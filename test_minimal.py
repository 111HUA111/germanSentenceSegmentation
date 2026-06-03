import spacy
import re

print("⏳ 正在加载德语 AI 模型...")
# 1. 加载模型
try:
    nlp = spacy.load("de_core_news_sm")
    print("✅ 模型加载成功！\n")
except Exception as e:
    print(f"❌ 模型加载失败，请确认是否运行过 python -m spacy download de_core_news_sm\n错误信息: {e}")
    exit()

# 2. 构造极端测试用例（模拟包含“幽灵换行符”的脏数据）
# 注意 "aus" 和 "Poly" 之间有一个隐藏的 \n
dirty_text = "Diese robuste Truhe aus \n Poly Rattan ist sowohl eine praktische als auch eine dekorative Ergänzung."

print("--- 处理前 ---")
print(f"带脏数据的原文: {repr(dirty_text)}\n")

# 3. 核心清洗逻辑
def clean_text(text):
    # 将换行、回车、制表符全部替换为空格
    text = text.replace("\n", " ").replace("\r", " ").replace("\t", " ")
    # 将连续的多个空格压缩为一个
    text = re.sub(r'\s+', ' ', text).strip()
    return text

cleaned_text = clean_text(dirty_text)
print("--- 处理后 ---")
print(f"清洗后的纯净文本: {repr(cleaned_text)}\n")

# 4. 执行 AI 分句
doc = nlp(cleaned_text)

print("--- 最终分句结果 ---")
for i, sent in enumerate(doc.sents, 1):
    print(f"[{i}] {sent.text}")