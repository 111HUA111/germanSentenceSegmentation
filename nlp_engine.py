import re
import spacy

class GermanNLPEngine:
    def __init__(self, model_name="de_core_news_sm"):
        try:
            self.nlp = spacy.load(model_name, disable=["ner", "lemmatizer", "textcat"])
        except OSError:
            raise OSError(f"未找到 spaCy 模型 '{model_name}'。请先在终端运行: python -m spacy download {model_name}")
        
        # 1. 缩写白名单（防句号被切）
        self.blacklist = [
            "z.B.", "bzw.", "Dr.", "Prof.", "ca.", "usw.", 
            "d.h.", "vgl.", "u.a.", "inkl.", "ggf.", "z.T."
        ]
        
        # 2. 强制绑定的短语白名单（防空格被切断）
        self.protected_phrases = [
            "Poly Rattan Rahmen",
            "Poly Rattan",
            # 你可以在这里继续添加你们行业里常被卖家写错、容易被切断的专有名词
        ]
        
        self.mask_dot = "XXXDOTXXX"       
        self.mask_space = "XXXSPACEXXX"  # 新增：用于保护短语内空格的掩码
        self.ignore_case = False

    def update_blacklist(self, custom_words, ignore_case=False):
        """更新自定义白名单（这里简化逻辑，直接全加进缩写库，你可以在 UI 独立分开）"""
        self.ignore_case = ignore_case
        if not custom_words:
            return
        combined = list(set(self.blacklist + custom_words))
        self.blacklist = sorted(combined, key=len, reverse=True)

    def _mask_text(self, text):
        masked_text = text
        flags = re.IGNORECASE if self.ignore_case else 0

        # --- 阶段 A：保护强制绑定的短语（用掩码替换它们内部的空格） ---
        for phrase in sorted(self.protected_phrases, key=len, reverse=True):
            if " " not in phrase:
                continue
                
            # 匹配整个词组
            pattern = r'\b' + re.escape(phrase) + r'\b'
            
            # 将匹配到的词组内的空格，替换为 mask_space
            def space_repl(match):
                return match.group(0).replace(" ", self.mask_space)

            masked_text = re.sub(pattern, space_repl, masked_text, flags=flags)

        # --- 阶段 B：保护白名单词汇中的句号 ---
        for word in self.blacklist:
            if "." not in word:
                continue 
            
            pattern = r'(?<![a-zA-ZäöüßÄÖÜ])' + re.escape(word)
            def dot_repl(match):
                return match.group(0).replace(".", self.mask_dot)

            masked_text = re.sub(pattern, dot_repl, masked_text, flags=flags)
            
        return masked_text

    def _unmask_text(self, text):
        """还原句号和空格"""
        text = text.replace(self.mask_dot, ".")
        text = text.replace(self.mask_space, " ")
        return text

    def split_sentences(self, text):
        if not text or not str(text).strip():
            return []

        # 1. 预处理掩码
        masked_text = self._mask_text(str(text))
        
        # 2. AI 切分
        doc = self.nlp(masked_text)
        
        raw_sents = []
        for sent in doc.sents:
            clean_sent = self._unmask_text(sent.text).strip()
            if clean_sent:
                raw_sents.append(clean_sent)

        # 3. 冒号强力胶后处理
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