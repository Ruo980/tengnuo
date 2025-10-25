#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
PSM双资源池部署分析工具
用于查找可以从第一个资源池腾挪资源并在第二个资源池补充实例的PSM服务
"""

import pandas as pd
import sys
from typing import Tuple, List, Optional


def load_excel_data(file_path: str) -> pd.DataFrame:
    """加载Excel数据"""
    try:
        df = pd.read_excel(file_path)
        return df
    except Exception as e:
        print(f"加载Excel文件失败: {e}")
        sys.exit(1)


def filter_by_idc(df: pd.DataFrame, idc_list: Optional[List[str]]) -> pd.DataFrame:
    """按机房过滤数据"""
    if not idc_list:
        return df.copy()

    return df[df["idc"].isin(idc_list)].copy()


def filter_default_clusters(df: pd.DataFrame) -> pd.DataFrame:
    """过滤出cluster_name为default的数据"""
    return df[df["cluster_name"] == "default"].copy()


def find_psm_in_both_pools(
    df: pd.DataFrame, pool1: Tuple[str, str], pool2: Tuple[str, str]
) -> pd.DataFrame:
    """
    找到同时部署在两个资源池中的psm服务

    Args:
        df: 过滤后的DataFrame
        pool1: (physical_cluster, iaas_cluster) 第一个资源池（需要借出资源的集群）
        pool2: (physical_cluster, iaas_cluster) 第二个资源池（可以补充资源的集群）

    Returns:
        包含同时部署在两个资源池的psm的DataFrame
    """

    # 创建资源池标识符
    def create_pool_key(row):
        return f"{row['physical_cluster']}/{row['iaas_cluster']}"

    df["pool_key"] = df.apply(create_pool_key, axis=1)

    # 定义两个资源池的key
    pool1_key = f"{pool1[0]}/{pool1[1]}"
    pool2_key = f"{pool2[0]}/{pool2[1]}"

    # 按psm分组，检查每个psm是否同时存在于两个资源池
    psm_groups = df.groupby("psm")

    valid_psms = []
    for psm, group in psm_groups:
        pools = set(group["pool_key"].unique())
        if pool1_key in pools and pool2_key in pools:
            valid_psms.append(psm)

    # 只保留在指定两个资源池中的数据
    result_df = df[
        df["psm"].isin(valid_psms)
        & ((df["pool_key"] == pool1_key) | (df["pool_key"] == pool2_key))
    ].copy()

    # 添加资源池标识列
    result_df["pool_identifier"] = result_df["pool_key"]

    return result_df


def analyze_deployment(
    file_path: str,
    pool1: str,
    pool2: str,
    idc_list: Optional[List[str]] = None,
    output_file: str = "dual_deployment_psm.xlsx",
) -> None:
    """主分析函数"""
    # 1. 加载数据
    df = load_excel_data(file_path)

    # 2. 按机房过滤
    if idc_list:
        df = filter_by_idc(df, idc_list)

    # 3. 过滤default集群
    filtered_df = filter_default_clusters(df)

    # 4. 解析资源池
    try:
        pool1_physical, pool1_iaas = pool1.split("/")
        pool2_physical, pool2_iaas = pool2.split("/")
    except ValueError:
        print("资源池格式错误，请使用'Physical Cluster/IaaS Cluster'格式")
        return

    pool1_tuple = (pool1_physical, pool1_iaas)
    pool2_tuple = (pool2_physical, pool2_iaas)

    # 5. 查找同时部署的psm
    result_df = find_psm_in_both_pools(filtered_df, pool1_tuple, pool2_tuple)

    if len(result_df) == 0:
        print("没有找到同时部署在两个资源池的psm")
        return

    # 输出找到的符合条件的PSM数量
    psm_count = len(result_df["psm"].unique())
    print(f"找到{psm_count}个同时部署在两个资源池的PSM服务")

    # 6. 准备输出数据
    output_columns = [
        "psm",
        "pool_identifier",
        "physical_cluster",
        "iaas_cluster",
        "instance_num",
        "cpu_limit",
        "mem_limit",
        "cluster_name",
        "dept_level1",
        "dept_level2",
        "host_type",
        "idc",
    ]

    # 检查是否有package字段，且不为空
    if (
        "package" in result_df.columns
        and result_df["package"].notna().any()
        and (result_df["package"] != "").any()
    ):
        output_columns.insert(2, "package")  # 在pool_identifier后面添加package字段

    # 确保所有需要的列都存在
    available_columns = [col for col in output_columns if col in result_df.columns]
    output_df = result_df[available_columns].copy()

    # 确保instance_num是数值类型
    try:
        output_df["instance_num"] = pd.to_numeric(
            output_df["instance_num"], errors="coerce"
        )
        output_df["instance_num"] = output_df["instance_num"].fillna(0).astype(int)
    except Exception as e:
        print(f"警告: 转换instance_num为数值类型时出错: {e}")
        print("将使用原始值进行排序，可能影响排序结果")

    # 7. 按照第一个资源池的instance_num排序并将同一服务在两个资源池的数据相邻排列
    # 创建一个临时DataFrame来存储第一个资源池的instance_num信息
    pool1_key = f"{pool1_tuple[0]}/{pool1_tuple[1]}"
    pool1_df = output_df[output_df["pool_identifier"] == pool1_key].copy()

    # 创建一个psm到instance_num的映射
    psm_to_instance = {}
    for _, row in pool1_df.iterrows():
        # 确保使用数值进行排序
        try:
            instance_num = int(row["instance_num"])
        except (ValueError, TypeError):
            instance_num = 0
        psm_to_instance[row["psm"]] = instance_num

    # 为所有行添加排序列
    def get_sort_key(row):
        return psm_to_instance.get(row["psm"], 0)

    output_df["sort_key"] = output_df.apply(get_sort_key, axis=1)

    # 按psm和pool_identifier排序，确保同一服务在两个资源池的数据相邻
    # 先按sort_key（第一个资源池的instance_num）降序排序，再按psm排序，最后按pool_identifier排序
    sorted_df = output_df.sort_values(
        by=["sort_key", "psm", "pool_identifier"], ascending=[False, True, True]
    )

    # 删除临时排序列
    sorted_df = sorted_df.drop(columns=["sort_key"])

    # 8. 添加汇总信息
    # 确保汇总前转换为数值类型
    summary_columns = ["instance_num", "cpu_limit", "mem_limit"]
    result_df_for_summary = result_df.copy()

    for col in summary_columns:
        if col in result_df_for_summary.columns:
            try:
                result_df_for_summary[col] = pd.to_numeric(
                    result_df_for_summary[col], errors="coerce"
                )
                result_df_for_summary[col] = result_df_for_summary[col].fillna(0)
            except Exception:
                print(f"警告: 转换{col}为数值类型时出错，汇总结果可能不准确")

    # 定义汇总列
    group_columns = ["psm", "pool_identifier"]
    agg_dict = {"instance_num": "sum", "cpu_limit": "sum", "mem_limit": "sum"}

    # 如果package字段存在且有值，添加到汇总列
    if (
        "package" in result_df_for_summary.columns
        and result_df_for_summary["package"].notna().any()
        and (result_df_for_summary["package"] != "").any()
    ):
        group_columns.append("package")

    summary_df = (
        result_df_for_summary.groupby(group_columns).agg(agg_dict).reset_index()
    )

    # 对汇总信息也进行排序
    summary_df["sort_key"] = summary_df.apply(
        lambda row: psm_to_instance.get(row["psm"], 0), axis=1
    )

    sorted_summary_df = summary_df.sort_values(
        by=["sort_key", "psm", "pool_identifier"], ascending=[False, True, True]
    ).drop(columns=["sort_key"])

    # 9. 保存到Excel
    with pd.ExcelWriter(output_file, engine="openpyxl") as writer:
        # 按照要求的顺序输出：先资源汇总，再详细数据
        # 汇总数据
        sorted_summary_df.to_excel(writer, sheet_name="资源汇总", index=False)

        # 详细数据
        sorted_df.to_excel(writer, sheet_name="详细数据", index=False)

    print(f"结果已保存到: {output_file}")
    print(
        f"提示: 结果按第一个资源池(需借出)的实例数从大到小排序，可以快速找到可腾挪资源的服务"
    )


def main():
    """主函数 - 用户交互界面"""
    # 配置参数
    EXCEL_FILE = "/Applications/code_repoistory/tengnuo/all.xlsx"
    OUTPUT_FILE = "dual_deployment_analysis.xlsx"

    print("PSM双资源池部署分析工具 - 资源腾挪分析")
    print("说明: 第一个资源池是需要借出资源的集群，第二个资源池是可以补充资源的集群")
    print("      结果将按第一个资源池的实例数从大到小排序，方便找到可腾挪资源的服务")
    print("-" * 80)

    # 用户输入机房信息
    idc_input = input(
        "请输入要过滤的机房名称（多个机房用逗号分隔，留空表示不过滤）: "
    ).strip()
    idc_list = [idc.strip() for idc in idc_input.split(",")] if idc_input else None

    # 用户输入资源池信息（使用Physical Cluster/IaaS Cluster格式）
    pool1 = input(
        "第一个资源池(需借出) (格式: Physical Cluster/IaaS Cluster): "
    ).strip()
    pool2 = input(
        "第二个资源池(可补充) (格式: Physical Cluster/IaaS Cluster): "
    ).strip()

    # 确认输出文件名
    output_file = input(f"输出文件名 (默认: {OUTPUT_FILE}): ").strip()
    if not output_file:
        output_file = OUTPUT_FILE
    if not output_file.endswith(".xlsx"):
        output_file += ".xlsx"

    try:
        # 执行分析
        analyze_deployment(
            file_path=EXCEL_FILE,
            pool1=pool1,
            pool2=pool2,
            idc_list=idc_list,
            output_file=output_file,
        )

    except Exception as e:
        print(f"分析过程中出现错误: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    main()
