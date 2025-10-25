# -*- coding: utf-8 -*-
"""
Excel文件处理脚本
功能：读取Excel文件，在每行后插入指定数量的空行，然后导出新文件
"""

import pandas as pd
import os

# 配置参数
# 以下是Excel文件处理的相关参数设置
# 可根据需要调整输入输出文件路径和空行数量
INPUT_FILE = "2.xlsx"  # 输入文件名
OUTPUT_FILE = "2_with_empty_rows.xlsx"  # 输出文件名
EMPTY_ROWS_BETWEEN = 2  # 每行后插入的空行数量，可在此修改


def insert_empty_rows(input_file, output_file, empty_rows=1):
    """
    在Excel文件的每行数据后插入指定数量的空行
    
    参数:
    input_file: 输入Excel文件路径
    output_file: 输出Excel文件路径
    empty_rows: 每行后插入的空行数量
    """
    try:
        # 检查输入文件是否存在
        if not os.path.exists(input_file):
            print(f"错误: 找不到输入文件 '{input_file}'")
            return
        
        # 读取Excel文件
        print(f"正在读取文件: {input_file}")
        df = pd.read_excel(input_file)
        
        print(f"原始数据行数: {len(df)}")
        
        # 创建新的DataFrame用于存储结果
        result_rows = []
        
        # 遍历原始数据的每一行
        for _, row in df.iterrows():
            # 添加原始行
            result_rows.append(row)
            # 添加空行
            for _ in range(empty_rows):
                # 创建一个空行，保持与原始数据相同的列
                empty_row = pd.Series([None] * len(df.columns), index=df.columns)
                result_rows.append(empty_row)
        
        # 创建结果DataFrame
        result_df = pd.DataFrame(result_rows)
        
        print(f"处理后数据行数: {len(result_df)}")
        
        # 保存到新文件
        result_df.to_excel(output_file, index=False)
        print(f"文件已保存到: {output_file}")
        
    except Exception as e:
        print(f"处理过程中出现错误: {str(e)}")


if __name__ == "__main__":
    print("开始处理Excel文件...")
    insert_empty_rows(INPUT_FILE, OUTPUT_FILE, EMPTY_ROWS_BETWEEN)
    print("处理完成！")