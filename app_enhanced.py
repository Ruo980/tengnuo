from flask import Flask, render_template, request, redirect, url_for, send_file, jsonify
import pandas as pd
import numpy as np
import os
import uuid
import json
import resource_manager as rm
from datetime import datetime

app = Flask(__name__)

# 确保uploads目录存在
UPLOAD_FOLDER = 'uploads'
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

@app.route('/')
def index():
    return render_template('index_complete.html')

@app.route('/migration')
def migration():
    return render_template('migration.html')

@app.route('/recommend')
def recommend():
    return render_template('recommend.html')

@app.route('/migratable')
def migratable():
    return render_template('migratable.html')

@app.route('/migration', methods=['GET', 'POST'])
def analyze_migration():
    """资源腾挪分析功能"""
    if request.method == 'GET':
        return render_template('migration.html', has_results=False)
    
    try:
        # 获取用户输入
        idc_input = request.form.get('idc', '').strip()
        pool1 = request.form.get('pool1', '').strip()
        pool2 = request.form.get('pool2', '').strip()
        
        # 获取上传的文件或使用默认文件
        data_file = request.form.get('data_file', 'all.xlsx')
        file_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), data_file)
        
        # 构建idc列表
        idc_list = [idc.strip() for idc in idc_input.split(',')] if idc_input else None
        
        # 使用resource_manager模块进行分析
        analysis_result = rm.analyze_resource_migration(file_path, pool1, pool2, idc_list)
        
        # 检查分析结果状态
        if analysis_result['status'] != 'success':
            return render_template('migration.html', 
                                 error=analysis_result.get('message', '分析失败'),
                                 idc=idc_input, 
                                 pool1=pool1, 
                                 pool2=pool2,
                                 has_results=False)
        
        # 获取详细数据和汇总数据
        sorted_df = analysis_result['data']['detail']
        sorted_summary_df = analysis_result['data']['summary']
        stats_df = analysis_result['data']['stats']
        
        # 生成统计表格HTML
        stats_table = stats_df.to_html(classes="table table-striped table-bordered", index=False)
        
        # 生成唯一的输出文件名
        output_filename = f"resource_migration_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
        output_path = os.path.join(UPLOAD_FOLDER, output_filename)
        
        # 保存到Excel
        with pd.ExcelWriter(output_path, engine="openpyxl") as writer:
            sorted_summary_df.to_excel(writer, sheet_name="资源汇总", index=False)
            sorted_df.to_excel(writer, sheet_name="详细数据", index=False)
            stats_df.to_excel(writer, sheet_name="统计信息", index=False)
        
        # 将DataFrame转换为字典列表以供模板使用
        detail_data = sorted_df.to_dict(orient="records")
        summary_data = sorted_summary_df.to_dict(orient="records")
        
        # 获取列名用于表头
        detail_columns = sorted_df.columns.tolist()
        summary_columns = sorted_summary_df.columns.tolist()
        
        # 计算统计数据
        psm_count = len(stats_df) if len(stats_df) > 0 else 0
        
        # 返回migration.html模板，包含查询结果
        return render_template(
            "migration.html",
            idc=idc_input,
            pool1=pool1,
            pool2=pool2,
            data_file=data_file,
            detail_data=detail_data,
            summary_data=summary_data,
            detail_columns=detail_columns,
            summary_columns=summary_columns,
            stats_table=stats_table,
            excel_file=output_filename,
            has_results=True,
            psm_count=psm_count
        )
    except Exception as e:
        import traceback
        error_msg = traceback.format_exc()
        print(f"分析过程中出现错误: {error_msg}")
        return render_template('migration.html', 
                             error=f'分析过程中出现错误: {str(e)}',
                             has_results=False)

@app.route('/analyze_recommend', methods=['POST'])
def analyze_recommend():
    idc = request.form.get('idc', '').strip()
    pool = request.form.get('pool', '').strip()
    min_save_cores = request.form.get('min_save_cores', '0')
    data_file = request.form.get('data_file', 'all.xlsx')
    
    # 验证必填参数
    if not idc or not pool:
        return render_template('recommend.html', error='请填写所有必填字段', has_results=False)
    
    # 转换min_save_cores为整数
    try:
        min_save_cores = int(min_save_cores)
    except ValueError:
        min_save_cores = 0
    
    # 构建数据文件的完整路径
    file_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), data_file)
    
    # 检查文件是否存在
    if not os.path.exists(file_path):
        return render_template('recommend.html', error=f'数据文件 {data_file} 不存在', has_results=False)
    
    try:
        # 使用resource_manager模块进行分析
        results = rm.analyze_recommended_scaling(file_path, idc, pool, min_save_cores)
        
        # 计算统计信息
        total_cpu = sum(row.get('save_cores', 0) for row in results)
        total_clusters = len(results)
        
        # 不需要生成Excel文件
        return render_template('recommend.html', results=results, idc=idc, pool=pool,
                             total_cpu=total_cpu, total_clusters=total_clusters,
                             has_results=True)
    except Exception as e:
        import traceback
        print(f"分析过程中出现错误: {traceback.format_exc()}")
        return render_template('recommend.html', error=f'分析过程中出现错误: {str(e)}',
                             has_results=False)

@app.route('/analyze_migratable', methods=['POST'])
def analyze_migratable():
    print("收到可腾挪集群查询请求...")
    
    # 检查请求参数
    idc = request.form.get('idc')
    pool = request.form.get('pool')
    data_file = request.form.get('data_file', 'all.xlsx')
    
    print(f"请求参数: idc={idc}, pool={pool}, data_file={data_file}")
    
    # 验证必填参数
    if not idc or not pool:
        error_msg = "请填写所有必填字段"
        print(f"参数错误: {error_msg}")
        return render_template('migratable.html', error=error_msg)
    
    # 构建数据文件的完整路径
    file_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), data_file)
    
    # 检查文件是否存在
    if not os.path.exists(file_path):
        error_msg = f'数据文件 {data_file} 不存在'
        print(f"文件错误: {error_msg}")
        return render_template('migratable.html', error=error_msg)
    
    try:
        print(f"开始分析数据文件: {file_path}")
        
        # 使用resource_manager模块进行分析
        results = rm.analyze_migratable_clusters(file_path, idc, pool)
        
        print(f"分析完成，结果数量: {len(results)}")
        
        # 计算统计信息
        total_psm = len(results)
        migratable_psm = sum(1 for row in results if row.get('deployment_status') == '多资源池')
        
        print(f"统计信息: total_psm={total_psm}, migratable_psm={migratable_psm}")
        
        # 收集所有可用的其他资源池
        available_pools = set()
        for row in results:
            available_pools.update(row.get('other_pools', []))
        available_pools = sorted(list(available_pools))
        
        # 为了避免请求超时，限制结果数量
        max_results = 500  # 设置一个合理的上限
        if len(results) > max_results:
            print(f"结果数量过多({len(results)}), 限制为{max_results}")
            results = results[:max_results]
        
        # 准备响应数据，移除excel_filename相关内容
        response_data = {
            'results': results,
            'idc': idc,
            'pool': pool,
            'total_psm': total_psm,
            'migratable_psm': migratable_psm,
            'available_pools': available_pools
        }
        
        print("准备渲染模板...")
        return render_template('migratable.html', **response_data)
        
    except Exception as e:
        import traceback
        error_msg = f'分析过程中出现错误: {str(e)}'
        print(f"错误: {error_msg}")
        print(f"错误详情: {traceback.format_exc()}")
        return render_template('migratable.html', error=error_msg)

def generate_migration_excel(results, idc, pool1, pool2):
    # 创建文件名
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f'migration_{idc}_{pool1}_to_{pool2}_{timestamp}.xlsx'
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    
    # 创建DataFrame
    df = pd.DataFrame(results)
    
    # 创建Excel写入器
    with pd.ExcelWriter(filepath, engine='openpyxl') as writer:
        # 写入详细数据
        df.to_excel(writer, sheet_name='腾挪详情', index=False)
        
        # 添加统计信息
        stats_df = pd.DataFrame({
            '统计项': ['总可腾挪CPU(核)', '总可腾挪内存(GB)', '可腾挪服务数量'],
            '数值': [
                sum(row.get('migratable_cpu', 0) for row in results),
                sum(row.get('migratable_mem', 0) for row in results),
                len(results)
            ]
        })
        stats_df.to_excel(writer, sheet_name='统计信息', index=False)
        
        # 添加说明
        info_df = pd.DataFrame({
            '说明': [
                f'分析时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}',
                f'机房: {idc}',
                f'源资源池: {pool1}',
                f'目标资源池: {pool2}',
                '腾挪建议: 先扩容目标资源池集群，确认服务稳定后缩容源资源池集群'
            ]
        })
        info_df.to_excel(writer, sheet_name='分析说明', index=False)
    
    return filename

def generate_recommend_excel(results, idc, pool):
    # 创建文件名
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f'recommend_scale_down_{idc}_{pool}_{timestamp}.xlsx'
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    
    # 创建DataFrame
    df = pd.DataFrame(results)
    
    # 创建Excel写入器
    with pd.ExcelWriter(filepath, engine='openpyxl') as writer:
        # 写入详细数据
        df.to_excel(writer, sheet_name='缩容建议', index=False)
        
        # 添加统计信息
        stats_df = pd.DataFrame({
            '统计项': ['预计可释放CPU(核)', '符合条件的集群数量', '建议缩容核数大于10的集群数'],
            '数值': [
                sum(row.get('save_cores', 0) for row in results),
                len(results),
                sum(1 for row in results if row.get('save_cores', 0) > 10)
            ]
        })
        stats_df.to_excel(writer, sheet_name='统计信息', index=False)
        
        # 添加说明
        info_df = pd.DataFrame({
            '说明': [
                f'分析时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}',
                f'机房: {idc}',
                f'资源池: {pool}',
                '缩容建议: 优先考虑缩容建议核数较大的集群，缩容前请确认服务实际运行情况'
            ]
        })
        info_df.to_excel(writer, sheet_name='分析说明', index=False)
    
    return filename

def generate_migratable_excel(results, idc, pool):
    # 创建文件名
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f'migratable_clusters_{idc}_{pool}_{timestamp}.xlsx'
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    
    # 创建DataFrame，需要处理列表类型的字段
    df = pd.DataFrame(results)
    # 将列表字段转换为字符串
    if 'other_pools' in df.columns:
        df['other_pools'] = df['other_pools'].apply(lambda x: ', '.join(x) if isinstance(x, list) else x)
    
    # 创建Excel写入器
    with pd.ExcelWriter(filepath, engine='openpyxl') as writer:
        # 写入详细数据
        df.to_excel(writer, sheet_name='可腾挪集群', index=False)
        
        # 添加统计信息
        migratable_count = sum(1 for row in results if row.get('deployment_status') == '多资源池')
        stats_df = pd.DataFrame({
            '统计项': ['总查询PSM数量', '可跨资源池腾挪的PSM数量', '总集群数量'],
            '数值': [
                len(results),
                migratable_count,
                sum(row.get('other_pool_cluster_count', 0) for row in results) + len(results)
            ]
        })
        stats_df.to_excel(writer, sheet_name='统计信息', index=False)
        
        # 添加说明
        info_df = pd.DataFrame({
            '说明': [
                f'分析时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}',
                f'机房: {idc}',
                f'查询资源池: {pool}',
                '使用建议: 选择可腾挪状态的PSM，结合其他可用资源池信息进行资源规划'
            ]
        })
        info_df.to_excel(writer, sheet_name='分析说明', index=False)
    
    return filename

@app.route('/download/<filename>')
def download_file(filename):
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    if os.path.exists(filepath):
        return send_file(filepath, as_attachment=True)
    else:
        return "文件不存在", 404

# API接口支持
@app.route('/api/migration', methods=['POST'])
def api_migration():
    try:
        data = request.get_json()
        idc = data.get('idc')
        pool1 = data.get('pool1')
        pool2 = data.get('pool2')
        data_file = data.get('data_file', 'all.xlsx')
        
        if not all([idc, pool1, pool2]):
            return jsonify({'error': '缺少必要参数'}), 400
        
        file_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), data_file)
        if not os.path.exists(file_path):
            return jsonify({'error': f'数据文件 {data_file} 不存在'}), 404
        
        results = rm.analyze_resource_migration(file_path, idc, pool1, pool2)
        total_cpu = sum(row.get('migratable_cpu', 0) for row in results)
        total_memory = sum(row.get('migratable_mem', 0) for row in results)
        
        return jsonify({
            'success': True,
            'results': results,
            'summary': {
                'total_cpu': total_cpu,
                'total_memory': total_memory,
                'service_count': len(results),
                'idc': idc,
                'source_pool': pool1,
                'target_pool': pool2
            }
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/recommend', methods=['POST'])
def api_recommend():
    try:
        data = request.get_json()
        idc = data.get('idc')
        pool = data.get('pool')
        min_save_cores = data.get('min_save_cores', 0)
        data_file = data.get('data_file', 'all.xlsx')
        
        if not all([idc, pool]):
            return jsonify({'error': '缺少必要参数'}), 400
        
        file_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), data_file)
        if not os.path.exists(file_path):
            return jsonify({'error': f'数据文件 {data_file} 不存在'}), 404
        
        results = rm.analyze_recommended_scaling(file_path, idc, pool, min_save_cores)
        total_cpu = sum(row.get('save_cores', 0) for row in results)
        total_clusters = len(results)
        
        return jsonify({
            'success': True,
            'results': results,
            'summary': {
                'total_cpu': total_cpu,
                'total_clusters': total_clusters,
                'idc': idc,
                'pool': pool
            }
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/migratable', methods=['POST'])
def api_migratable():
    try:
        data = request.get_json()
        idc = data.get('idc')
        pool = data.get('pool')
        data_file = data.get('data_file', 'all.xlsx')
        
        if not all([idc, pool]):
            return jsonify({'error': '缺少必要参数'}), 400
        
        file_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), data_file)
        if not os.path.exists(file_path):
            return jsonify({'error': f'数据文件 {data_file} 不存在'}), 404
        
        results = rm.analyze_migratable_clusters(file_path, idc, pool)
        total_psm = len(results)
        migratable_psm = sum(1 for row in results if row.get('deployment_status') == '多资源池')
        
        # 收集所有可用的其他资源池
        available_pools = set()
        for row in results:
            available_pools.update(row.get('other_pools', []))
        available_pools = sorted(list(available_pools))
        
        return jsonify({
            'success': True,
            'results': results,
            'summary': {
                'total_psm': total_psm,
                'migratable_psm': migratable_psm,
                'available_pools': available_pools,
                'idc': idc,
                'pool': pool
            }
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    # 设置host为0.0.0.0以允许从其他机器访问
    app.run(host='0.0.0.0', port=8888, debug=True)