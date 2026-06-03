import spacy

print("⏳ 1. 正在加载 spaCy 德语模型 (首次加载可能需要两三秒)...")

try:
    # 尝试加载刚刚下载的德语模型
    nlp = spacy.load("de_core_news_sm")
    print("✅ 模型加载成功！\n")

    # 准备一句包含德语缩写陷阱的测试文本
    text = "Hallo! Ich kenne Dr. Müller. Er mag z.B. Äpfel."
    print(f"📝 2. 开始测试分句引擎。")
    print(f"   原文: {text}\n")

    # 执行分句
    doc = nlp(text)
    
    print("🎯 分句结果:")
    for i, sent in enumerate(doc.sents, 1):
        print(f"   第 {i} 句: {sent.text}")

    print("\n🎉 恭喜！你的核心分句环境已完全配置成功！")

except Exception as e:
    print(f"\n❌ 发生错误，环境可能还有问题:\n{e}")