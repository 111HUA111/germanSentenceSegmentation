import csv
import os

class CSVDataProcessor:
    def __init__(self, nlp_engine):
        """
        初始化数据处理器，必须传入一个已经实例化的 NLP 分句引擎
        """
        self.nlp_engine = nlp_engine

    def process_file(self, input_path, target_col_name, output_path=None, progress_callback=None):
        """
        核心处理流：流式读取、分句、流式写入
        """
        # 如果未指定输出路径，自动在原文件名后加 "_split"
        if not output_path:
            base, ext = os.path.splitext(input_path)
            output_path = f"{base}_split.csv"

        # 检查文件是否存在
        if not os.path.exists(input_path):
            raise FileNotFoundError(f"找不到文件: {input_path}")

        # 第一遍：极速读取以获取总行数（用于在 UI 中显示精确的进度条）
        total_rows = 0
        with open(input_path, mode='r', encoding='utf-8-sig') as f:
            total_rows = sum(1 for _ in f) - 1  # 减去表头

        if total_rows <= 0:
            raise ValueError("CSV 文件中没有数据行。")

        # 第二遍：正式流式处理
        # 强制使用 utf-8-sig 写入，这是防止 Windows Excel 中文/德文乱码的终极护城河
        with open(input_path, mode='r', encoding='utf-8-sig') as infile, \
             open(output_path, mode='w', encoding='utf-8-sig', newline='') as outfile:
            
            reader = csv.reader(infile)
            writer = csv.writer(outfile)

            # --- 1. 处理表头 ---
            headers = next(reader, None)
            if not headers:
                raise ValueError("CSV 文件格式错误或为空。")
                
            if target_col_name not in headers:
                raise ValueError(f"在 CSV 中找不到列名: '{target_col_name}'。当前可用列: {headers}")
                
            target_col_idx = headers.index(target_col_name)

            # 写入固定三列的新表头（遵循 PRD 规范）
            writer.writerow(["原始文本", "句子序号", "分句结果"])

            # --- 2. 流式逐行处理数据 ---
            processed_rows = 0
            for row in reader:
                # 跳过空行
                if not row or len(row) <= target_col_idx:
                    continue

                original_text = row[target_col_idx].strip()
                
                # 如果这一行为空，跳过处理
                if not original_text:
                    continue

                # 调用 NLP 大脑进行切分
                sentences = self.nlp_engine.split_sentences(original_text)

                # 如果切分失败或返回空，原样保留
                if not sentences:
                    sentences = [original_text]

                # --- 3. 构造空白折叠长表 ---
                for idx, sentence in enumerate(sentences, 1):
                    if idx == 1:
                        # 第一句：展示原始文本
                        writer.writerow([original_text, idx, sentence])
                    else:
                        # 后续句子：原始文本留空，保持视觉清爽
                        writer.writerow(["", idx, sentence])

                processed_rows += 1
                
                # 如果绑定了进度回调函数（供后续 UI 使用），则触发更新
                if progress_callback:
                    progress_callback(processed_rows, total_rows)

        return output_path

# ==========================================
# QA 测试模块（脱离界面独立运行）
# ==========================================
if __name__ == "__main__":
    # 为了测试这个类，我们需要引入阶段一的引擎
    # （请确保同级目录下有你之前测试成功的 nlp_engine.py）
    from nlp_engine import GermanNLPEngine
    
    print("⏳ 1. 正在加载 NLP 引擎...")
    engine = GermanNLPEngine()
    
    # 手动添加一些黑名单用于测试
    engine.update_blacklist(["z.B.", "Dr."])

    processor = CSVDataProcessor(engine)

    # 创建一个测试用的 Dummy CSV 文件
    test_input = "test_input.csv"
    print(f"\n📝 2. 正在生成测试用 CSV 文件: {test_input}")
    with open(test_input, mode='w', encoding='utf-8-sig', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(["ID", "German_Text", "Status"])
        writer.writerow(["1", "Hallo! Ich kenne Dr. Müller. Er mag z.B. Äpfel.", "Done"])
        writer.writerow(["2", "Das ist ein Test.", "Pending"])
        writer.writerow(["3", "Wir gehen. Komm mit! Bis bald.", "Done"])

    print("\n🚀 3. 开始执行流水线处理...")
    
    # 模拟 UI 的进度回调
    def print_progress(current, total):
        print(f"   进度: {current}/{total} 行已处理...")

    try:
        # 执行处理，指定要切分的列是 'German_Text'
        output_file = processor.process_file(
            input_path=test_input, 
            target_col_name="German_Text", 
            progress_callback=print_progress
        )
        print(f"\n✅ 处理完成！请在当前目录下查看生成的文件: {output_file}")
        print("   (建议用 Excel 直接双击打开，检查是否乱码以及排版是否符合预期)")
    except Exception as e:
        print(f"❌ 处理出错: {e}")