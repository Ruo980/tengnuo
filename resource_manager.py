#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
PSM资源管理系统 - 核心逻辑模块
包含三个主要功能：
1. 资源腾挪：查找可从第一个资源池腾挪到第二个资源池的服务
2. 推荐缩容：查找利用率低的集群进行缩容
3. 可腾挪集群查询：查询包含特定资源池的PSM及其在其他资源池的分布
"""

import pandas as pd
from typing import Tuple, List, Optional, Dict, Any


def load_excel_data(file_path: str) -> pd.DataFrame:
    """加载Excel数据"""
    try:
        df = pd.read_excel(file_path)
        return df
    except Exception as e:
        raise Exception(f"加载Excel文件失败: {e}")


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


def analyze_resource_migration(
    file_path: str,
    pool1: str,
    pool2: str,
    idc_list: Optional[List[str]] = None
) -> Dict[str, Any]:
    """
    功能1: 资源腾挪分析
    查找可从第一个资源池腾挪到第二个资源池的服务
    """
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
        raise Exception("资源池格式错误，请使用'Physical Cluster/IaaS Cluster'格式")
    
    pool1_tuple = (pool1_physical, pool1_iaas)
    pool2_tuple = (pool2_physical, pool2_iaas)
    
    # 5. 查找同时部署的psm
    result_df = find_psm_in_both_pools(filtered_df, pool1_tuple, pool2_tuple)
    
    if len(result_df) == 0:
        return {
            "status": "empty",
            "message": "没有找到同时部署在两个资源池的psm",
            "data": None
        }
    
    # 准备输出数据
    output_columns = [
        "psm", "pool_identifier", "physical_cluster", "iaas_cluster",
        "instance_num", "cpu_limit", "mem_limit", "cluster_name",
        "dept_level1", "dept_level2", "host_type", "idc"
    ]
    
    # 检查是否有package字段，且不为空
    if (
        "package" in result_df.columns
        and result_df["package"].notna().any()
        and (result_df["package"] != "").any()
    ):
        output_columns.insert(2, "package")
    
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
    
    # 按照第一个资源池的instance_num排序并将同一服务在两个资源池的数据相邻排列
    pool1_key = f"{pool1_tuple[0]}/{pool1_tuple[1]}"
    pool1_df = output_df[output_df["pool_identifier"] == pool1_key].copy()
    
    # 创建一个psm到instance_num的映射
    psm_to_instance = {}
    for _, row in pool1_df.iterrows():
        try:
            instance_num = int(row["instance_num"])
        except (ValueError, TypeError):
            instance_num = 0
        psm_to_instance[row["psm"]] = instance_num
    
    # 为所有行添加排序列
    def get_sort_key(row):
        return psm_to_instance.get(row["psm"], 0)
    
    output_df["sort_key"] = output_df.apply(get_sort_key, axis=1)
    
    # 排序
    sorted_df = output_df.sort_values(
        by=["sort_key", "psm", "pool_identifier"], ascending=[False, True, True]
    ).drop(columns=["sort_key"])
    
    # 生成汇总信息
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
                print(f"警告: 转换{col}为数值类型时出错")
    
    # 定义汇总列
    group_columns = ["psm", "pool_identifier"]
    if (
        "package" in result_df_for_summary.columns
        and result_df_for_summary["package"].notna().any()
        and (result_df_for_summary["package"] != "").any()
    ):
        group_columns.append("package")
    
    agg_dict = {"instance_num": "sum", "cpu_limit": "sum", "mem_limit": "sum"}
    summary_df = (
        result_df_for_summary.groupby(group_columns).agg(agg_dict).reset_index()
    )
    
    # 对汇总信息排序
    summary_df["sort_key"] = summary_df.apply(
        lambda row: psm_to_instance.get(row["psm"], 0), axis=1
    )
    
    sorted_summary_df = summary_df.sort_values(
        by=["sort_key", "psm", "pool_identifier"], ascending=[False, True, True]
    ).drop(columns=["sort_key"])
    
    # 统计信息
    stats_data = {
        "资源池1(需借出)": [pool1],
        "资源池2(可补充)": [pool2],
        "PSM数量": [len(result_df["psm"].unique())],
    }
    stats_df = pd.DataFrame(stats_data)
    
    return {
        "status": "success",
        "data": {
            "detail": sorted_df,
            "summary": sorted_summary_df,
            "stats": stats_df
        }
    }


def analyze_recommended_scaling(
    file_path: str,
    idc: str,
    physical_cluster: str,
    min_save_cores: int = 0
) -> List[Dict[str, Any]]:
    """
    功能2: 推荐缩容分析
    查找指定机房和资源池中可缩容的default集群
    """
    # 1. 加载数据
    df = load_excel_data(file_path)
    
    # 2. 按机房过滤
    df = df[df["idc"] == idc].copy() if idc else df.copy()
    
    # 3. 解析物理集群和IaaS集群
    try:
        physical, iaas = physical_cluster.split("/")
    except ValueError:
        # 如果格式不正确，尝试只按物理集群过滤
        physical = physical_cluster
        iaas = "default"
    
    # 4. 按物理集群和IaaS集群过滤
    filtered_df = df[
        (df["physical_cluster"] == physical) & 
        (df["iaas_cluster"] == iaas)
    ].copy()
    
    # 5. 过滤有效数据
    if len(filtered_df) == 0:
        raise Exception(f"没有找到{idc}机房{physical_cluster}资源池中的数据")
    
    # 6. 处理save_cores字段
    if "save_cores" not in filtered_df.columns:
        # 如果没有save_cores字段，尝试从其他相关字段计算
        if all(col in filtered_df.columns for col in ["cpu_limit", "cpu_request"]):
            filtered_df["save_cores"] = filtered_df["cpu_limit"] - filtered_df["cpu_request"]
        else:
            raise Exception("数据中没有save_cores字段，也无法从其他字段计算")
    
    # 7. 转换save_cores为数值类型
    try:
        # 处理可能的字符串值
        filtered_df["save_cores"] = filtered_df["save_cores"].astype(str)
        filtered_df["save_cores"] = filtered_df["save_cores"].str.strip()
        filtered_df = filtered_df[filtered_df["save_cores"] != ""].copy()
        filtered_df["save_cores"] = pd.to_numeric(filtered_df["save_cores"], errors="coerce")
        filtered_df = filtered_df.dropna(subset=["save_cores"]).copy()
        filtered_df["save_cores"] = filtered_df["save_cores"].astype(int)
    except Exception as e:
        raise Exception(f"处理save_cores字段时出错: {str(e)}")
    
    # 8. 过滤出建议缩容的集群（save_cores >= min_save_cores）
    recommended_df = filtered_df[filtered_df["save_cores"] >= min_save_cores].copy()
    
    if len(recommended_df) == 0:
        return []
    
    # 9. 按save_cores降序排序
    recommended_df = recommended_df.sort_values(by="save_cores", ascending=False)
    
    # 10. 准备返回数据，确保包含前端模板需要的字段
    results = []
    for _, row in recommended_df.iterrows():
        # 为缺失的字段提供默认值
        result_row = {
            "psm": row.get("psm", "未知"),
            "cluster_id": row.get("cluster_id", row.get("cluster_name", "未知")),
            "package": row.get("package", ""),
            "cpu_limit": row.get("cpu_limit", 0),
            "mem_limit": row.get("mem_limit", 0),
            "save_cores": row.get("save_cores", 0),
            # 添加新的利用率字段
            "cpu_util_max_1days": row.get("cpu_util_max_1days", ""),
            "cpu_util_max_7days": row.get("cpu_util_max_7days", ""),
            "mem_util_max_7days": row.get("mem_util_max_7days", ""),
            "business_line": row.get("dept_level1", "") + "/" + row.get("dept_level2", "").strip("/")
        }
        results.append(result_row)
    
    return results


def analyze_migratable_clusters(
    file_path: str,
    idc: str,
    pool: str
) -> List[Dict[str, Any]]:
    """
    功能3: 可腾挪集群查询
    查询包含特定资源池的PSM及其在其他资源池的分布
    
    Args:
        file_path: Excel数据文件路径
        idc: 机房名称
        pool: 资源池字符串，格式为'physical_cluster/iaas_cluster'
        
    Returns:
        包含PSM信息的字典列表
    """
    # 1. 解析资源池
    try:
        physical_cluster, iaas_cluster = pool.split("/")
    except ValueError:
        # 如果解析失败，尝试直接使用传入的值作为物理集群名
        physical_cluster = pool
        iaas_cluster = None
    
    # 2. 加载数据
    df = load_excel_data(file_path)
    
    # 3. 按机房过滤
    df = df[df["idc"] == idc].copy() if idc else df.copy()
    
    # 4. 过滤default集群
    filtered_df = filter_default_clusters(df)
    
    # 5. 找出包含目标物理集群的PSM
    target_psms = filtered_df[filtered_df["physical_cluster"] == physical_cluster]["psm"].unique()
    
    if len(target_psms) == 0:
        # 返回空列表，而不是状态字典，以匹配应用程序的期望格式
        return []
    
    # 6. 获取这些PSM在所有资源池的分布
    result_df = filtered_df[filtered_df["psm"].isin(target_psms)].copy()
    
    # 7. 转换为应用程序期望的格式
    results = []
    for psm in target_psms:
        psm_data = result_df[result_df["psm"] == psm]
        
        # 查找主资源池（查询的资源池）中的记录
        main_pool_data = psm_data[psm_data["physical_cluster"] == physical_cluster]
        
        # 如果指定了iaas_cluster，进一步过滤
        if iaas_cluster and not main_pool_data.empty:
            main_pool_data = main_pool_data[main_pool_data["iaas_cluster"] == iaas_cluster]
        
        # 获取其他资源池信息（包含iaas_cluster）
        other_pools_data = psm_data[psm_data["physical_cluster"] != physical_cluster]
        other_pools = []
        for _, row in other_pools_data.iterrows():
            # 构建完整的资源池标识：physical_cluster/iaas_cluster
            iaas = row.get("iaas_cluster", "default")
            pool_identifier = f"{row['physical_cluster']}/{iaas}"
            if pool_identifier not in other_pools:
                other_pools.append(pool_identifier)
        
        # 确定部署状态
        deployment_status = "多资源池" if len(other_pools) > 0 else "单资源池"
        
        # 构建返回记录
        record = {
            "psm": psm,
            "deployment_status": deployment_status,
            "other_pools": other_pools,
            "other_pool_cluster_count": len(other_pools_data),
            "idc": idc,
            "pool": pool
        }
        
        # 如果主资源池中有数据，添加实例和资源信息
        if not main_pool_data.empty:
            first_record = main_pool_data.iloc[0]
            for col in ["instance_num", "cpu_limit", "mem_limit", "dept_level1", "dept_level2", "package", "cluster_id"]:
                if col in first_record.index:
                    record[col] = first_record[col]
        
        results.append(record)
    
    return results


def parse_pool_string(pool_str: str) -> Tuple[str, str]:
    """解析资源池字符串"""
    try:
        physical_cluster, iaas_cluster = pool_str.split("/")
        return physical_cluster.strip(), iaas_cluster.strip()
    except ValueError:
        raise ValueError("资源池格式错误，请使用'Physical Cluster/IaaS Cluster'格式")