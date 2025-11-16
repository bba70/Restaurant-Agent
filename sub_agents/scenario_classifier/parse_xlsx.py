import pandas as pd
import json
import os
from collections import defaultdict

def create_poi_taxonomy(file_path: str):
    """
    读取高德POI Excel文件，筛选"餐饮服务"大类，
    并将其中的层级数据（中类-小类）转换为简化的映射表。

    :param file_path: 输入的 .xlsx 文件完整路径。
    """
    if not os.path.exists(file_path):
        print(f"错误：文件未找到，请检查路径：{file_path}")
        return

    # 1. 配置常量
    TARGET_COLUMN = '大类'
    TARGET_VALUE = '餐饮服务'
    LEVELS = ['大类', '中类', '小类', 'NEW_TYPE']
    
    try:
        print(f"正在读取文件：{file_path}...")
        # 尝试读取 Excel，默认使用第一个工作表
        df = pd.read_excel(file_path)
        
        # 检查关键列是否存在
        for col in LEVELS:
            if col not in df.columns:
                print(f"错误：文件中缺少关键列 '{col}'。请检查列名是否正确。")
                return

        # 2. 筛选数据：只保留"餐饮服务"
        print(f"正在筛选数据：'{TARGET_COLUMN}' 等于 '{TARGET_VALUE}'...")
        # 清理列数据并进行不区分大小写的筛选，提高鲁棒性
        filtered_df = df[
            df[TARGET_COLUMN].astype(str).str.strip().str.lower() == TARGET_VALUE.lower()
        ].copy() # 使用 .copy() 避免 SettingWithCopyWarning
        
        # 检查筛选结果
        if filtered_df.empty:
            print(f"筛选结果为空，没有找到 {TARGET_VALUE} 的数据。")
            return

        # 3. 数据预处理
        # 填充 NaN/None 值，方便后续分组
        for col in LEVELS:
            filtered_df[col] = filtered_df[col].fillna('').astype(str).str.strip()

        print(f"筛选完成，共找到 {len(filtered_df)} 条 {TARGET_VALUE} 数据。")
        
        # 4. 构建简化的映射表：中类/小类 -> NEW_TYPE
        taxonomy_map = {}
        
        # 遍历所有数据行，构建映射关系
        for index, row in filtered_df.iterrows():
            z = row['中类']  # 中类
            x = row['小类']  # 小类
            t = row['NEW_TYPE']  # 高德API的type值
            
            if not z or not t:
                continue
            
            # 创建复合键：中类-小类
            key = f"{z}-{x}" if x else z
            
            # 如果该键还不存在，添加到映射表
            if key not in taxonomy_map:
                taxonomy_map[key] = {
                    "medium_category": z,
                    "small_category": x if x else None,
                    "type": t
                }

        print(f"构建完成，共有 {len(taxonomy_map)} 个映射关系。")
        
        # 5. 构建输出文件路径（保存到当前脚本所在目录）
        current_dir = os.path.dirname(os.path.abspath(__file__))
        output_file_path = os.path.join(current_dir, "restaurant_taxonomy.json")

        # 6. 保存 JSON 结构到文件
        print(f"正在保存结果到：{output_file_path}...")
        with open(output_file_path, 'w', encoding='utf-8') as f:
            # indent=2 使 JSON 格式化，方便阅读
            json.dump(taxonomy_map, f, ensure_ascii=False, indent=2) 
        
        print("\n✅ 脚本执行成功！")
        print(f"结果已保存至：{output_file_path}")
        print(f"共生成 {len(taxonomy_map)} 个映射关系。")
        print("请检查 JSON 文件内容，供您的 Agent 使用。")

    except Exception as e:
        print(f"处理文件时发生错误：{e}")
        print("请确保 Excel 文件格式正确且没有被占用。")


# --- 配置区域 ---
if __name__ == "__main__":
    # TODO: 请将下面的路径替换为你实际的文件路径
    input_file = "C:\\Users\\Lenovo\\Desktop\\ruler.xlsx"
    
    # 调取函数执行
    create_poi_taxonomy(input_file)