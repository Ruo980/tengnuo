#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
PSM双资源池部署分析工具 - Web版
用于查找可以从第一个资源池腾挪资源并在第二个资源池补充实例的PSM服务
"""

from flask import Flask, render_template, request, send_file, jsonify, redirect, url_for
import pandas as pd
import os
import uuid
import json
from main import (
    load_excel_data,
    filter_by_idc,
    filter_default_clusters,
    find_psm_in_both_pools,
)

app = Flask(__name__)

# 配置参数
EXCEL_FILE = "/Applications/code_repoistory/tengnuo/all.xlsx"
OUTPUT_DIR = "outputs"

# 确保输出目录存在
os.makedirs(OUTPUT_DIR, exist_ok=True)


@app.route("/")
def index():
    """首页 - 显示输入表单"""
    return render_template("index.html")


@app.route("/analyze", methods=["POST"])
def analyze():
    """处理分析请求"""
    # 获取用户输入
    idc_input = request.form.get("idc", "").strip()
    pool1 = request.form.get("pool1", "").strip()
    pool2 = request.form.get("pool2", "").strip()

    # 处理机房列表
    idc_list = [idc.strip() for idc in idc_input.split(",")] if idc_input else None

    # 生成唯一的输出文件名
    output_filename = f"{uuid.uuid4().hex}.xlsx"
    output_path = os.path.join(OUTPUT_DIR, output_filename)

    # 执行分析
    try:
        # 1. 加载数据
        df = load_excel_data(EXCEL_FILE)

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
            return render_template(
                "error.html",
                error="资源池格式错误，请使用'Physical Cluster/IaaS Cluster'格式",
            )

        pool1_tuple = (pool1_physical, pool1_iaas)
        pool2_tuple = (pool2_physical, pool2_iaas)

        # 5. 查找同时部署的psm
        result_df = find_psm_in_both_pools(filtered_df, pool1_tuple, pool2_tuple)

        if len(result_df) == 0:
            return render_template(
                "error.html", error="没有找到同时部署在两个资源池的psm"
            )

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

        # 确保所有需要的列都存在
        available_columns = [col for col in output_columns if col in result_df.columns]
        output_df = result_df[available_columns].copy()

        # 确保instance_num是数值类型
        output_df["instance_num"] = pd.to_numeric(
            output_df["instance_num"], errors="coerce"
        )
        output_df["instance_num"] = output_df["instance_num"].fillna(0).astype(int)

        # 7. 按照第一个资源池的instance_num排序并将同一服务在两个资源池的数据相邻排列
        # 创建一个临时DataFrame来存储第一个资源池的instance_num信息
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

        # 按psm和pool_identifier排序，确保同一服务在两个资源池的数据相邻
        sorted_df = output_df.sort_values(
            by=["sort_key", "psm", "pool_identifier"], ascending=[False, True, True]
        )

        # 删除临时排序列
        sorted_df = sorted_df.drop(columns=["sort_key"])

        # 8. 添加汇总信息
        # 确保汇总前转换为数值类型
        summary_columns = ["instance_num", "cpu_limit", "mem_limit"]
        result_df_for_summary = result_df.copy()

        # 检查是否存在非空的package字段
        has_package = False
        if "package" in result_df_for_summary.columns:
            if not result_df_for_summary["package"].isna().all():
                has_package = True
                summary_columns.append("package")

        for col in summary_columns:
            if col in result_df_for_summary.columns and col != "package":
                result_df_for_summary[col] = pd.to_numeric(
                    result_df_for_summary[col], errors="coerce"
                )
                result_df_for_summary[col] = result_df_for_summary[col].fillna(0)

        # 根据是否有package字段决定分组字段
        group_columns = ["psm", "pool_identifier"]
        if has_package:
            group_columns.append("package")

        # 根据是否有package字段决定聚合方式
        agg_dict = {"instance_num": "sum", "cpu_limit": "sum", "mem_limit": "sum"}

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

        # 统计信息 - 减少不必要的输出
        stats_data = {
            "资源池1(需借出)": [pool1],
            "资源池2(可补充)": [pool2],
            "PSM数量": [len(result_df["psm"].unique())],
        }
        stats_df = pd.DataFrame(stats_data)

        # 10. 准备Web显示数据
        # 将DataFrame转换为HTML表格
        detail_table = sorted_df.to_html(
            classes="table table-striped table-bordered", index=False
        )
        summary_table = sorted_summary_df.to_html(
            classes="table table-striped table-bordered", index=False
        )
        stats_table = stats_df.to_html(
            classes="table table-striped table-bordered", index=False
        )

        # 9. 保存到Excel
        with pd.ExcelWriter(output_path, engine="openpyxl") as writer:
            # 汇总数据 - 放在详细数据上方
            sorted_summary_df.to_excel(writer, sheet_name="资源汇总", index=False)

            # 详细数据
            sorted_df.to_excel(writer, sheet_name="详细数据", index=False)

            # 统计信息
            stats_df.to_excel(writer, sheet_name="统计信息", index=False)

        # 将DataFrame转换为JSON以供DataTables使用
        detail_data = sorted_df.to_dict(orient="records")
        summary_data = sorted_summary_df.to_dict(orient="records")

        # 获取列名用于表头
        detail_columns = sorted_df.columns.tolist()
        summary_columns = sorted_summary_df.columns.tolist()

        return render_template(
            "results.html",
            idc_list=idc_input,
            pool1=pool1,
            pool2=pool2,
            detail_data=json.dumps(detail_data),
            summary_data=json.dumps(summary_data),
            detail_columns=detail_columns,
            summary_columns=summary_columns,
            stats_table=stats_table,
            excel_file=output_filename,
        )

    except Exception as e:
        import traceback

        error_msg = traceback.format_exc()
        return render_template("error.html", error=str(e), details=error_msg)


@app.route("/download/<filename>")
def download_file(filename):
    """下载Excel文件"""
    file_path = os.path.join(OUTPUT_DIR, filename)
    if os.path.exists(file_path):
        return send_file(file_path, as_attachment=True)
    else:
        return render_template("error.html", error="文件不存在")


@app.route("/api/data", methods=["POST"])
def api_analyze():
    """API接口 - 返回JSON格式的分析结果"""
    try:
        # 获取JSON请求数据
        data = request.get_json()
        idc_input = data.get("idc", "").strip()
        pool1 = data.get("pool1", "").strip()
        pool2 = data.get("pool2", "").strip()

        # 处理机房列表
        idc_list = [idc.strip() for idc in idc_input.split(",")] if idc_input else None

        # 执行与Web界面相同的分析逻辑
        # 1. 加载数据
        df = load_excel_data(EXCEL_FILE)

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
            return jsonify({"status": "error", "message": "资源池格式错误，请使用'Physical Cluster/IaaS Cluster'格式"}), 400

        pool1_tuple = (pool1_physical, pool1_iaas)
        pool2_tuple = (pool2_physical, pool2_iaas)

        # 5. 查找同时部署的psm
        result_df = find_psm_in_both_pools(filtered_df, pool1_tuple, pool2_tuple)

        if len(result_df) == 0:
            return jsonify({"status": "error", "message": "没有找到同时部署在两个资源池的psm"}), 400

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

        # 确保所有需要的列都存在
        available_columns = [col for col in output_columns if col in result_df.columns]
        output_df = result_df[available_columns].copy()

        # 确保instance_num是数值类型
        output_df["instance_num"] = pd.to_numeric(
            output_df["instance_num"], errors="coerce"
        )
        output_df["instance_num"] = output_df["instance_num"].fillna(0).astype(int)

        # 7. 按照第一个资源池的instance_num排序并将同一服务在两个资源池的数据相邻排列
        # 创建一个临时DataFrame来存储第一个资源池的instance_num信息
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

        # 按psm和pool_identifier排序，确保同一服务在两个资源池的数据相邻
        sorted_df = output_df.sort_values(
            by=["sort_key", "psm", "pool_identifier"], ascending=[False, True, True]
        )

        # 删除临时排序列
        sorted_df = sorted_df.drop(columns=["sort_key"])

        # 8. 添加汇总信息
        # 确保汇总前转换为数值类型
        summary_columns = ["instance_num", "cpu_limit", "mem_limit"]
        result_df_for_summary = result_df.copy()

        # 检查是否存在非空的package字段
        has_package = False
        if "package" in result_df_for_summary.columns:
            if not result_df_for_summary["package"].isna().all():
                has_package = True
                summary_columns.append("package")

        for col in summary_columns:
            if col in result_df_for_summary.columns and col != "package":
                result_df_for_summary[col] = pd.to_numeric(
                    result_df_for_summary[col], errors="coerce"
                )
                result_df_for_summary[col] = result_df_for_summary[col].fillna(0)

        # 根据是否有package字段决定分组字段
        group_columns = ["psm", "pool_identifier"]
        if has_package:
            group_columns.append("package")

        # 根据是否有package字段决定聚合方式
        agg_dict = {"instance_num": "sum", "cpu_limit": "sum", "mem_limit": "sum"}

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

        # 统计信息
        stats_data = {
            "资源池1(需借出)": [pool1],
            "资源池2(可补充)": [pool2],
            "PSM数量": [len(result_df["psm"].unique())],
        }
        stats_df = pd.DataFrame(stats_data)

        # 将DataFrame转换为JSON
        detail_data = sorted_df.to_dict(orient="records")
        summary_data = sorted_summary_df.to_dict(orient="records")

        # 返回JSON格式的结果
        return jsonify(
            {
                "status": "success",
                "data": {
                    "detail": detail_data,
                    "summary": summary_data,
                    "stats": stats_df.to_dict(orient="records"),
                },
            }
        )

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 400


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=8888)
