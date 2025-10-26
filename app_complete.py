#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
PSM资源管理系统 - Web版
包含三个主要功能：
1. 资源腾挪：查找可从第一个资源池腾挪到第二个资源池的服务
2. 推荐缩容：查找利用率低的集群进行缩容
3. 可腾挪集群查询：查询包含特定资源池的PSM及其在其他资源池的分布
"""

from flask import Flask, render_template, request, send_file, jsonify, redirect, url_for
import pandas as pd
import os
import uuid
import json
from resource_manager import (
    analyze_resource_migration,
    analyze_recommended_scaling,
    analyze_migratable_clusters
)

app = Flask(__name__)

# 配置参数 - 注意：这里需要根据实际环境修改Excel文件路径
# 在Windows环境中，使用绝对路径时要注意格式
EXCEL_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "all.xlsx")
OUTPUT_DIR = "outputs"

# 确保输出目录存在
os.makedirs(OUTPUT_DIR, exist_ok=True)

# 确保Excel文件存在
if not os.path.exists(EXCEL_FILE):
    # 尝试使用测试文件
    test_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "all-test.xlsx")
    if os.path.exists(test_file):
        EXCEL_FILE = test_file
    else:
        print(f"警告: 找不到Excel数据文件: {EXCEL_FILE} 和 {test_file}")


@app.route("/")
def index():
    """首页 - 显示功能选择界面"""
    return render_template("index_complete.html")


@app.route("/migration", methods=["GET", "POST"])
def migration():
    """资源腾挪分析功能"""
    if request.method == "GET":
        return render_template("migration.html")
    
    # 处理POST请求
    try:
        # 获取用户输入
        idc_input = request.form.get("idc", "").strip()
        pool1 = request.form.get("pool1", "").strip()
        pool2 = request.form.get("pool2", "").strip()
        
        # 验证输入
        if not pool1 or not pool2:
            return render_template("migration.html", error="请输入两个资源池信息")
        
        # 处理机房列表
        idc_list = [idc.strip() for idc in idc_input.split(",")] if idc_input else None
        
        # 执行分析
        result = analyze_resource_migration(EXCEL_FILE, pool1, pool2, idc_list)
        
        if result["status"] == "empty":
            return render_template("migration.html", error=result["message"])
        elif result["status"] == "error":
            return render_template("migration.html", error=result["message"])
        
        # 准备数据
        detail_data = result["data"]["detail"].to_dict(orient="records")
        summary_data = result["data"]["summary"].to_dict(orient="records")
        stats_data = result["data"]["stats"].to_dict(orient="records")
        
        detail_columns = result["data"]["detail"].columns.tolist()
        summary_columns = result["data"]["summary"].columns.tolist()
        
        # 生成唯一的输出文件名
        output_filename = f"migration_{uuid.uuid4().hex}.xlsx"
        output_path = os.path.join(OUTPUT_DIR, output_filename)
        
        # 保存到Excel
        with pd.ExcelWriter(output_path, engine="openpyxl") as writer:
            result["data"]["summary"].to_excel(writer, sheet_name="资源汇总", index=False)
            result["data"]["detail"].to_excel(writer, sheet_name="详细数据", index=False)
            result["data"]["stats"].to_excel(writer, sheet_name="统计信息", index=False)
        
        return render_template(
            "results_migration.html",
            idc_list=idc_input,
            pool1=pool1,
            pool2=pool2,
            detail_data=json.dumps(detail_data),
            summary_data=json.dumps(summary_data),
            stats_data=json.dumps(stats_data),
            detail_columns=detail_columns,
            summary_columns=summary_columns,
            excel_file=output_filename
        )
        
    except Exception as e:
        return render_template("migration.html", error=str(e))


@app.route("/recommend", methods=["GET", "POST"])
def recommend_scaling():
    """推荐缩容分析功能"""
    if request.method == "GET":
        return render_template("recommend_scaling.html")
    
    # 处理POST请求
    try:
        # 获取用户输入
        idc = request.form.get("idc", "").strip()
        physical_cluster = request.form.get("physical_cluster", "").strip()
        
        # 验证输入
        if not idc or not physical_cluster:
            return render_template("recommend_scaling.html", error="请输入机房和资源池信息")
        
        # 执行分析
        result = analyze_recommended_scaling(EXCEL_FILE, idc, physical_cluster)
        
        if result["status"] == "empty":
            return render_template("recommend_scaling.html", error=result["message"])
        elif result["status"] == "error":
            return render_template("recommend_scaling.html", error=result["message"])
        
        # 准备数据
        detail_data = result["data"]["detail"].to_dict(orient="records")
        stats_data = result["data"]["stats"].to_dict(orient="records")
        detail_columns = result["data"]["detail"].columns.tolist()
        
        # 生成唯一的输出文件名
        output_filename = f"recommend_{uuid.uuid4().hex}.xlsx"
        output_path = os.path.join(OUTPUT_DIR, output_filename)
        
        # 保存到Excel
        with pd.ExcelWriter(output_path, engine="openpyxl") as writer:
            result["data"]["detail"].to_excel(writer, sheet_name="推荐缩容列表", index=False)
            result["data"]["stats"].to_excel(writer, sheet_name="统计信息", index=False)
        
        return render_template(
            "results_recommend.html",
            idc=idc,
            physical_cluster=physical_cluster,
            detail_data=json.dumps(detail_data),
            stats_data=json.dumps(stats_data),
            detail_columns=detail_columns,
            excel_file=output_filename
        )
        
    except Exception as e:
        return render_template("recommend_scaling.html", error=str(e))


@app.route("/migratable", methods=["GET", "POST"])
def migratable_clusters():
    """可腾挪集群查询功能"""
    if request.method == "GET":
        return render_template("migratable_clusters.html")
    
    # 处理POST请求
    try:
        # 获取用户输入
        idc = request.form.get("idc", "").strip()
        physical_cluster = request.form.get("physical_cluster", "").strip()
        
        # 验证输入
        if not idc or not physical_cluster:
            return render_template("migratable_clusters.html", error="请输入机房和资源池信息")
        
        # 执行分析
        result = analyze_migratable_clusters(EXCEL_FILE, idc, physical_cluster)
        
        if result["status"] == "empty":
            return render_template("migratable_clusters.html", error=result["message"])
        elif result["status"] == "error":
            return render_template("migratable_clusters.html", error=result["message"])
        
        # 准备数据
        detail_data = result["data"]["detail"].to_dict(orient="records")
        stats_data = result["data"]["stats"].to_dict(orient="records")
        detail_columns = result["data"]["detail"].columns.tolist()
        
        # 生成唯一的输出文件名
        output_filename = f"migratable_{uuid.uuid4().hex}.xlsx"
        output_path = os.path.join(OUTPUT_DIR, output_filename)
        
        # 保存到Excel
        with pd.ExcelWriter(output_path, engine="openpyxl") as writer:
            result["data"]["detail"].to_excel(writer, sheet_name="可腾挪集群", index=False)
            result["data"]["stats"].to_excel(writer, sheet_name="统计信息", index=False)
        
        return render_template(
            "results_migratable.html",
            idc=idc,
            physical_cluster=physical_cluster,
            detail_data=json.dumps(detail_data),
            stats_data=json.dumps(stats_data),
            detail_columns=detail_columns,
            excel_file=output_filename
        )
        
    except Exception as e:
        return render_template("migratable_clusters.html", error=str(e))


@app.route("/download/<filename>")
def download_file(filename):
    """下载Excel文件"""
    file_path = os.path.join(OUTPUT_DIR, filename)
    if os.path.exists(file_path):
        return send_file(file_path, as_attachment=True)
    else:
        return render_template("error_complete.html", error="文件不存在")


@app.route("/api/migration", methods=["POST"])
def api_migration():
    """资源腾挪API接口"""
    try:
        data = request.get_json()
        idc_input = data.get("idc", "").strip()
        pool1 = data.get("pool1", "").strip()
        pool2 = data.get("pool2", "").strip()
        
        idc_list = [idc.strip() for idc in idc_input.split(",")] if idc_input else None
        
        result = analyze_resource_migration(EXCEL_FILE, pool1, pool2, idc_list)
        
        if result["status"] == "success":
            return jsonify({
                "status": "success",
                "data": {
                    "detail": result["data"]["detail"].to_dict(orient="records"),
                    "summary": result["data"]["summary"].to_dict(orient="records"),
                    "stats": result["data"]["stats"].to_dict(orient="records")
                }
            })
        else:
            return jsonify({"status": result["status"], "message": result["message"]}), 400
            
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 400


@app.route("/api/recommend", methods=["POST"])
def api_recommend():
    """推荐缩容API接口"""
    try:
        data = request.get_json()
        idc = data.get("idc", "").strip()
        physical_cluster = data.get("physical_cluster", "").strip()
        
        result = analyze_recommended_scaling(EXCEL_FILE, idc, physical_cluster)
        
        if result["status"] == "success":
            return jsonify({
                "status": "success",
                "data": {
                    "detail": result["data"]["detail"].to_dict(orient="records"),
                    "stats": result["data"]["stats"].to_dict(orient="records")
                }
            })
        else:
            return jsonify({"status": result["status"], "message": result["message"]}), 400
            
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 400


@app.route("/api/migratable", methods=["POST"])
def api_migratable():
    """可腾挪集群查询API接口"""
    try:
        data = request.get_json()
        idc = data.get("idc", "").strip()
        physical_cluster = data.get("physical_cluster", "").strip()
        
        result = analyze_migratable_clusters(EXCEL_FILE, idc, physical_cluster)
        
        if result["status"] == "success":
            return jsonify({
                "status": "success",
                "data": {
                    "detail": result["data"]["detail"].to_dict(orient="records"),
                    "stats": result["data"]["stats"].to_dict(orient="records")
                }
            })
        else:
            return jsonify({"status": result["status"], "message": result["message"]}), 400
            
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 400


if __name__ == "__main__":
    # 在生产环境中，应该使用专门的WSGI服务器
    # 这里使用Flask自带的开发服务器进行演示
    app.run(debug=False, host="0.0.0.0", port=8888)