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
        核心处理流：读取 Excel、分句、导出新 Excel
        """
        if not output_path:
            base, ext = os.path.splitext(input_path)
            output_path = f"{base}_split.xlsx"

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
            # 提取目标列文本，处理空值 (NaN)
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

            # 3. 构造空白折叠长表格式
            for s_idx, sentence in enumerate(sentences, 1):
                if s_idx == 1:
                    output_data.append([original_text, s_idx, sentence])
                else:
                    output_data.append(["", s_idx, sentence])

            processed_rows += 1
            
            # 触发进度条更新
            if progress_callback:
                progress_callback(processed_rows, total_rows)

        # 4. 将处理后的数据转为 DataFrame 并导出为新的 Excel
        out_df = pd.DataFrame(output_data, columns=["原始文本", "句子序号", "分句结果"])
        
        try:
            # 强制禁用索引导出，确保排版干净
            out_df.to_excel(output_path, index=False)
        except PermissionError:
            raise PermissionError("导出失败！请检查是否在其他程序中打开了同名的输出文件。")

        return output_path