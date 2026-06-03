import os
import pandas as pd

class ExcelDataProcessor:
    def __init__(self, nlp_engine):
        """
        初始化数据处理器，必须传入一个已经实例化的 NLP 分句引擎
        """
        self.nlp_engine = nlp_engine

    def process_file(self, input_path, target_col_name, output_path=None, progress_callback=None):
        """
        核心处理流：读取 Excel、分句、按【列】平铺导出新 Excel
        """
        if not output_path:
            base, ext = os.path.splitext(input_path)
            # 文件名加个 _columns 区分一下
            output_path = f"{base}_columns.xlsx"

        if not os.path.exists(input_path):
            raise FileNotFoundError(f"找不到文件: {input_path}")

        # 1. 使用 pandas 读取 Excel 文件
        try:
            df = pd.read_excel(input_path)
        except Exception as e:
            raise RuntimeError(f"无法读取 Excel 文件，请确保文件未被占用或损坏。\n错误信息: {e}")

        if target_col_name not in df.columns:
            raise ValueError(f"在 Excel 中找不到列名: '{target_col_name}'。当前可用列: {list(df.columns)}")

        total_rows = len(df)
        if total_rows <= 0:
            raise ValueError("Excel 文件中没有数据行。")

        output_data = []
        processed_rows = 0

        # 2. 逐行处理数据
        for idx, row in df.iterrows():
            original_text = row[target_col_name]
            if pd.isna(original_text):
                original_text = ""
            else:
                original_text = str(original_text).strip()
            
            if not original_text:
                continue

            # 调用 NLP 大脑进行切分
            sentences = self.nlp_engine.split_sentences(original_text)

            if not sentences:
                sentences = [original_text]

            # --- 💡 核心逻辑更改：构建动态列字典 ---
            # 先把原始文本放进字典
            row_dict = {"原始文本": original_text}
            
            # 动态生成 "分句_1", "分句_2" 等列名，并赋值
            for s_idx, sentence in enumerate(sentences, 1):
                row_dict[f"分句_{s_idx}"] = sentence

            # 将这行字典存入总列表
            output_data.append(row_dict)

            processed_rows += 1
            if progress_callback:
                progress_callback(processed_rows, total_rows)

        # 3. 生成动态宽表 DataFrame
        # pandas 会自动扫描所有字典，把最多的分句数作为总列数，没有分句的地方会填入 NaN
        out_df = pd.DataFrame(output_data)
        
        # 将难看的 NaN (空值) 替换为空白字符串，保证 Excel 干净整洁
        out_df.fillna("", inplace=True)
        
        # 4. 导出为新的 Excel
        try:
            out_df.to_excel(output_path, index=False)
        except PermissionError:
            raise PermissionError("导出失败！请检查是否在其他程序中打开了同名的输出文件。")

        return output_path