# GermanSplitter - 德语分句工具

![Version](https://img.shields.io/badge/version-1.0.0-blue.svg)
![Python](https://img.shields.io/badge/python-3.8%2B-green.svg)
![spaCy](https://img.shields.io/badge/spaCy-NLP-orange.svg)
![Pandas](https://img.shields.io/badge/Pandas-Data-yellow.svg)

## 项目简介 (Introduction)

**GermanSplitter** 是一款轻量级桌面端软件。

在业务场景中，经常遇到排版混乱的德语语料（例如：句号后缺失空格、换行符丢失、特殊缩写词滥用、德语特有的复合词拆分错误等）。传统的基于正则表达式或简单标点符号的分句脚本可能产生大量碎句和乱码。

本工具引入基于深度学习的 **spaCy (NLP)** 引擎，依靠**德语依存句法树**理解文本上下文。结合白名单自定义功能，能够应对几乎所有恶劣排版的德语长文本，并支持 Excel 宽表导出。

---

##  核心特性 (Key Features)

*  **AI 句法级驱动**：底层采用 `de_core_news_sm` 深度学习模型，不依赖单纯的标点符号，即使原文本没有句号和回车（“字符墙”），也能剥离小标题与正文。
*  **动态缩写保护（白名单持久化）**：自带悬浮配置面板，支持业务人员自定义行业缩写库（如`GmbH & Co. KG`, `bzw.`）。配置自动持久化为本地 `JSON`，下次启动自动读取，防止句号误切。
*  **智能冒号强力胶**：针对电商文案中高频出现的“标题: 描述”结构，强制缝合并保护冒号前后的完整语境，杜绝描述断裂。
*  **Excel 原生宽表转化**：彻底告别 CSV 导出导致的 `ä, ö, ü, ß` 乱码问题！原生支持读取 `.xlsx`，并将分句结果动态展平为**宽表（多列平铺）**，降低标注员排版成本。

---

##  快速上手 (Quick Start)

### 方案一：免安装开箱即用（推荐业务人员使用）
1. 下载最新版本的打包文件 `GermanSplitter_v1.0.zip`。
2. 解压到任意非中文路径的文件夹。
3. 进入文件夹，双击运行 **`GermanSplitter.exe`** 即可开启图形界面，无需配置任何 Python 环境。

### 方案二：开发者源码运行
如果您希望基于源码进行二次开发，请确保本地已安装 Python 3.8+。

**1. 克隆项目 & 安装依赖库：**
```bash
git clone https://github.com/111HUA111/germanSentenceSegmentation.git
cd GermanSplitter
pip install -r requirements.txt
