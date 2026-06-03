import re
import spacy

class GermanNLPEngine:
    def __init__(self, model_name="de_core_news_sm"):
        try:
            # 禁用不必要的组件以极大提升处理速度
            self.nlp = spacy.load(model_name, disable=["ner", "lemmatizer", "textcat"])
        except OSError:
            raise OSError(f"未找到 spaCy 模型 '{model_name}'。请先在终端运行: python -m spacy download {model_name}")
        
        # 缩写白名单（防句号被切）
        self.blacklist = [
            "z.B.", "bzw.", "Dr.", "Prof.", "ca.", "usw.", 
            "d.h.", "vgl.", "u.a.", "inkl.", "ggf.", "z.T."
        ]
        
        self.mask_dot = "XXXDOTXXX"       
        self.ignore_case = False

    def update_blacklist(self, custom_words, ignore_case=False):
        """更新自定义白名单"""
        self.ignore_case = ignore_case
        if not custom_words:
            return
        combined = list(set(self.blacklist + custom_words))
        # 按长度降序排列，防止短词错误遮挡长词
        self.blacklist = sorted(combined, key=len, reverse=True)

    def _mask_text(self, text):
        """将白名单里的句号替换为掩码"""
        masked_text = text
        flags = re.IGNORECASE if self.ignore_case else 0
        
        for word in self.blacklist:
            if "." not in word:
                continue 
            
            # 使用正则匹配，防止错误匹配单词的一部分
            pattern = r'(?<![a-zA-ZäöüßÄÖÜ])' + re.escape(word)
            def dot_repl(match):
                return match.group(0).replace(".", self.mask_dot)

            masked_text = re.sub(pattern, dot_repl, masked_text, flags=flags)
            
        return masked_text

    def _unmask_text(self, text):
        """还原句号"""
        return text.replace(self.mask_dot, ".")

    def split_sentences(self, text):
        """核心分句逻辑"""
        if not text or not str(text).strip():
            return []

        # ==========================================
        # 🛡️ 步骤 1：防弹预清洗逻辑（消灭幽灵换行符）
        # ==========================================
        text = str(text)
        # 把所有换行符 (\n), 回车符 (\r), 制表符 (\t) 强制替换为空格
        text = text.replace("\n", " ").replace("\r", " ").replace("\t", " ")
        # 把多个连续的空格合并成一个标准空格
        text = re.sub(r'\s+', ' ', text).strip()

        # ==========================================
        # 🛡️ 步骤 2：预处理掩码 (保护黑名单词汇中的句号)
        # ==========================================
        masked_text = self._mask_text(text)
        
        # ==========================================
        # 🧠 步骤 3：AI 切分
        # ==========================================
        doc = self.nlp(masked_text)
        
        raw_sents = []
        for sent in doc.sents:
            # 还原掩码并去除首尾空白
            clean_sent = self._unmask_text(sent.text).strip()
            if clean_sent:
                raw_sents.append(clean_sent)

        # ==========================================
        # 🔗 步骤 4：冒号强力胶后处理
        # ==========================================
        merged_sentences = []
        buffer = ""
        
        for s in raw_sents:
            if buffer:
                buffer += " " + s
            else:
                buffer = s
                
            if not buffer.endswith(":"):
                merged_sentences.append(buffer)
                buffer = ""
                
        if buffer:
            merged_sentences.append(buffer)

        return merged_sentences

# ==========================================
# 本地极速测试代码
# ==========================================
if __name__ == "__main__":
    print("⏳ 正在加载引擎...")
    engine = GermanNLPEngine()
    
    # 构造刚才报错的极端测试用例
    dirty_text = "Diese robuste Truhe aus\nPoly Rattan ist sowohl eine praktische als auch eine dekorative Ergänzung."
    
    print("\n--- 待处理的脏数据 ---")
    print(repr(dirty_text))
    
    sentences = engine.split_sentences(dirty_text)
    
    print("\n--- 最终输出 ---")
    for i, s in enumerate(sentences, 1):
        print(f"[{i}] {s}")