import re
import spacy

class GermanNLPEngine:
    def __init__(self, model_name="de_core_news_sm"):
        """
        初始化 NLP 引擎，加载 spaCy 模型并设置初始黑名单
        """
        try:
            # 禁用不需要的管道组件（如命名实体识别 NER）以极大提升运行速度并降低内存占用
            self.nlp = spacy.load(model_name, disable=["ner", "lemmatizer", "textcat"])
        except OSError:
            raise OSError(f"未找到 spaCy 模型 '{model_name}'。请先在终端运行: python -m spacy download {model_name}")
        
        # 内置的常见德语缩写黑名单
        self.blacklist = [
            "z.B.", "bzw.", "Dr.", "Prof.", "ca.", "usw.", 
            "d.h.", "vgl.", "u.a.", "inkl.", "ggf.", "z.T."
        ]
        # 用于替换句号的绝对安全的掩码
        self.mask_token = "<MASK_DOT>"
        self.ignore_case = False

    def update_blacklist(self, custom_words, ignore_case=False):
        """
        更新/追加自定义黑名单
        """
        self.ignore_case = ignore_case
        if not custom_words:
            return
            
        # 合并系统词库与用户词库，去重
        combined = list(set(self.blacklist + custom_words))
        # 【关键防呆设计】：按字符串长度降序排序。
        # 确保 "GmbH & Co." 优先于 "Co." 被匹配，防止短词破坏长词结构
        self.blacklist = sorted(combined, key=len, reverse=True)

    def _mask_text(self, text):
        """
        第一阶段（戴面具）：保护黑名单词汇中的句号
        """
        masked_text = text
        flags = re.IGNORECASE if self.ignore_case else 0

        for word in self.blacklist:
            if "." not in word:
                continue # 没有句号的缩写不会引起断句误判，直接跳过
            
            # 【词边界防御设计】：左侧不能是德文字母，防止类似于 "in." 匹配到 "Termin." 的结尾
            pattern = r'(?<![a-zA-ZäöüßÄÖÜ])' + re.escape(word)
            
            # 替换函数：动态把匹配到的原词中的 "." 替换为掩码
            # 这样做的好处是，在 ignore_case=True 时，依然保留原文的大小写格式
            def repl(match):
                return match.group(0).replace(".", self.mask_token)

            masked_text = re.sub(pattern, repl, masked_text, flags=flags)
            
        return masked_text

    def _unmask_text(self, text):
        """
        第三阶段（卸面具）：将掩码还原为真实的句号
        """
        return text.replace(self.mask_token, ".")

    def split_sentences(self, text):
        """
        主入口：执行完整的德语分句流程
        """
        if not text or not str(text).strip():
            return []

        # 1. 预处理：给黑名单词汇戴上面具
        masked_text = self._mask_text(str(text))

        # 2. 核心切分：交给 spaCy 引擎处理
        # 此时 spaCy 看不到黑名单里的句号，绝对不会误切
        doc = self.nlp(masked_text)
        
        sentences = []
        for sent in doc.sents:
            # 3. 后处理：逐句还原真实句号，并清理两端多余的空格或换行
            clean_sent = self._unmask_text(sent.text).strip()
            if clean_sent:
                sentences.append(clean_sent)

        return sentences