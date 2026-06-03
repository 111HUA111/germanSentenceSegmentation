import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import threading
import os
import pandas as pd
import json
import ctypes

# 导入核心逻辑
from nlp_engine import GermanNLPEngine
from data_processor import ExcelDataProcessor  # 类名变了！

#开启 Windows 高 DPI 感知，彻底解决字体模糊
# ==========================================
try:
    # 优先尝试 Windows 8.1 及以上版本的 API
    ctypes.windll.shcore.SetProcessDpiAwareness(1)
except Exception:
    try:
        # 如果失败，降级尝试 Windows Vista / 7 的 API
        ctypes.windll.user32.SetProcessDPIAware()
    except Exception:
        # 如果不是 Windows 系统或者调用失败，直接忽略，不影响核心功能
        pass
# ==========================================



# --- 现代扁平化UI设计常量配置 ---
FONT_FAMILY = "Times New Roman, Simsong"  # 统一使用标准的微软雅黑字体
FONT_TITLE = (FONT_FAMILY, 11, "bold")
FONT_MAIN = (FONT_FAMILY, 10)
FONT_SMALL = (FONT_FAMILY, 9)

COLOR_BG = "#F3F4F6"         # 页面大背景（轻量浅灰，极具现代质感）
COLOR_CARD = "#FFFFFF"       # 组件卡片背景（纯白）
COLOR_PRIMARY = "#0095d7"    # 科技蓝（主动作按钮）
COLOR_PRIMARY_HOVER = "#00a6b7" 
COLOR_SUCCESS = "#10B981"    # 翡翠绿（就绪/运行成功）
COLOR_DANGER = "#EF4444"     # 珊瑚红（删除/失败）
COLOR_TEXT_MAIN = "#1F2937"  # 主文字颜色（深炭黑）
COLOR_TEXT_MUTED = "#6B7280" # 次要提示文字颜色（灰）

class GermanSplitterApp:
    def __init__(self, root):
        self.root = root
        self.root.title("德语分句工具 v1.0")
        self.root.geometry("640x520")  # 稍微放宽，给UI充足的呼吸空间
        self.root.configure(bg=COLOR_BG)
        # self.root.resizable(False, False)
        self.root.minsize(600, 480)

        # 核心逻辑变量（保持完全一致）
        self.engine = None
        self.processor = None
        self.excel_filepath = ""
        self.excel_headers = []
        self.config_file = "custom_blacklist.json"
        self.custom_blacklist = self.load_blacklist()

        # 配置全局 TTK 样式
        self.setup_styles()
        # 构建美化版UI
        self.build_ui()
        # 异步加载 AI 引擎
        self.root.after(100, self.init_engine_async)

    def setup_styles(self):
        """配置 TTK 组件的主题样式树"""
        style = ttk.Style()
        style.theme_use('clam')  # 切换至可高度自定义的 clam 渲染引擎
        
        # 自定义 Notebook (Tab选项卡) 样式
        style.configure("TNotebook", background=COLOR_BG, borderwidth=0)
        style.configure("TNotebook.Tab", 
                        background="#E5E7EB", 
                        foreground=COLOR_TEXT_MUTED, 
                        padding=[20, 6], 
                        font=FONT_MAIN,
                        borderwidth=0)
        # 鼠标悬停及选中状态切换
        style.map("TNotebook.Tab", 
                  background=[("selected", COLOR_CARD), ("active", "#E5E7EB")], 
                  foreground=[("selected", COLOR_PRIMARY), ("active", COLOR_TEXT_MAIN)],
                  font=[("selected", (FONT_FAMILY, 10, "bold"))])
        
        # 自定义现代扁平化进度条
        style.configure("TProgressbar", 
                        thickness=8, 
                        troughcolor="#E5E7EB", 
                        background=COLOR_PRIMARY,
                        borderwidth=0)

    def load_blacklist(self):
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            except:
                return []
        return []

    def save_blacklist(self):
        try:
            with open(self.config_file, "w", encoding="utf-8") as f:
                json.dump(self.custom_blacklist, f, ensure_ascii=False)
        except Exception as e:
            messagebox.showerror("保存失败", f"无法保存白名单配置: {e}")

    def build_ui(self):
        """全新重构的高内聚、带有视觉卡片感的布局"""
        # --- 1. 顶部状态与控制栏 ---
        top_frame = tk.Frame(self.root, bg=COLOR_BG)
        top_frame.pack(fill=tk.X, padx=20, pady=(15, 10))
        
        self.lbl_status = tk.Label(top_frame, text="⏳ 正在加载 AI 模型，请稍候...", 
                                   fg="#D97706", bg=COLOR_BG, font=(FONT_FAMILY, 10, "bold"))
        self.lbl_status.pack(side=tk.LEFT)
        
        # 现代扁平化设置按钮
        btn_settings = tk.Button(top_frame, text="⚙️ 自定义白名单", command=self.open_settings_modal,
                                 font=FONT_SMALL, bg="#FFFFFF", fg=COLOR_TEXT_MAIN,
                                 activebackground="#F3F4F6", activeforeground=COLOR_PRIMARY,
                                 relief="solid", bd=1, cursor="hand2", padx=8, pady=2)
        btn_settings.pack(side=tk.RIGHT)
        
        # --- 2. 主体选项卡容器 ---
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=20, pady=(0, 20))

        # ====================================================
        # --- Tab 1: 文本速切 ---
        # ====================================================
        self.tab_text = tk.Frame(self.notebook, bg=COLOR_CARD)
        self.notebook.add(self.tab_text, text="  📝 文本速切测试  ")
        
        # 输入区布局
        tk.Label(self.tab_text, text="输入德语原文：", font=FONT_TITLE, fg=COLOR_TEXT_MAIN, bg=COLOR_CARD).pack(anchor=tk.W, pady=(15, 5), padx=15)
        
        self.text_input = tk.Text(self.tab_text, height=5, font=FONT_MAIN, fg=COLOR_TEXT_MAIN,
                                  bg="#F9FAFB", relief="solid", bd=1, highlightthickness=0, wrap=tk.WORD)
        self.text_input.pack(fill=tk.X, padx=15, pady=5)
        
        # 一键分句大按钮
        self.btn_split_text = tk.Button(self.tab_text, text="一键分句", command=self.do_split_text,
                                        font=(FONT_FAMILY, 11, "bold"), bg=COLOR_PRIMARY, fg="white",
                                        activebackground=COLOR_PRIMARY_HOVER, activeforeground="white",
                                        relief="flat", bd=0, cursor="hand2", pady=5)
        self.btn_split_text.pack(fill=tk.X, padx=15, pady=10)
        
        # 输出区布局
        tk.Label(self.tab_text, text="分句结果展示：", font=FONT_TITLE, fg=COLOR_TEXT_MAIN, bg=COLOR_CARD).pack(anchor=tk.W, padx=15, pady=(5, 0))
        self.text_output = tk.Text(self.tab_text, height=7, font=FONT_MAIN, fg=COLOR_TEXT_MAIN,
                                   bg="#F3F4F6", relief="solid", bd=1, highlightthickness=0, wrap=tk.WORD)
        self.text_output.pack(fill=tk.BOTH, expand=True, padx=15, pady=(5, 15))

        # ====================================================
        # --- Tab 2: Excel 批量处理 ---
        # ====================================================
        self.tab_excel = tk.Frame(self.notebook, bg=COLOR_CARD)
        self.notebook.add(self.tab_excel, text="  📊 Excel 批量处理  ")
        
        # 步骤 1：文件上传区卡片化布局
        tk.Label(self.tab_excel, text="第一步：上传需要切分的 Excel 文件", font=FONT_TITLE, fg=COLOR_TEXT_MAIN, bg=COLOR_CARD).pack(anchor=tk.W, padx=20, pady=(20, 5))
        frame_file = tk.Frame(self.tab_excel, bg=COLOR_CARD)
        frame_file.pack(fill=tk.X, padx=20, pady=5)
        
        self.lbl_filename = tk.Label(frame_file, text="请选择或拖入一个有效的 Excel 文件路径...", fg=COLOR_TEXT_MUTED, 
                                     bg="#F9FAFB", anchor="w", relief="solid", bd=1, font=FONT_MAIN, padx=10, pady=5)
        self.lbl_filename.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10))
        
        btn_browse = tk.Button(frame_file, text="浏览文件", command=self.select_file, font=FONT_MAIN,
                               bg="#E5E7EB", fg=COLOR_TEXT_MAIN, activebackground="#D1D5DB",
                               relief="flat", bd=0, cursor="hand2", padx=15)
        btn_browse.pack(side=tk.RIGHT, fill=tk.Y)

        # 步骤 2：下拉列表选择
        tk.Label(self.tab_excel, text="第二步：指定【德语语料】所在的列名", font=FONT_TITLE, fg=COLOR_TEXT_MAIN, bg=COLOR_CARD).pack(anchor=tk.W, padx=20, pady=(15, 5))
        
        # 覆写 Combobox 样式使其符合扁平化视觉
        self.combo_columns = ttk.Combobox(self.tab_excel, state="disabled", font=FONT_MAIN)
        self.combo_columns.pack(fill=tk.X, padx=20, pady=5)

        # 底部动作与进度渲染区
        frame_bottom = tk.Frame(self.tab_excel, bg=COLOR_CARD)
        frame_bottom.pack(fill=tk.BOTH, expand=True, padx=20, pady=(25, 15))
        
        self.btn_run_excel = tk.Button(frame_bottom, text="▶ 开始流式处理并导出长表", command=self.start_excel_processing, 
                                     state="disabled", bg=COLOR_PRIMARY, fg="white", font=(FONT_FAMILY, 12, "bold"),
                                     activebackground=COLOR_PRIMARY_HOVER, activeforeground="white",
                                     relief="flat", bd=0, cursor="hand2", pady=8)
        self.btn_run_excel.pack(fill=tk.X, pady=(0, 15))
        
        # 进度指示器
        self.progress_bar = ttk.Progressbar(frame_bottom, orient="horizontal", mode="determinate")
        self.progress_bar.pack(fill=tk.X)
        
        self.lbl_progress_text = tk.Label(frame_bottom, text="就绪。等待任务加载...", fg=COLOR_TEXT_MUTED, bg=COLOR_CARD, font=FONT_SMALL)
        self.lbl_progress_text.pack(pady=5)

    def init_engine_async(self):
        def load_task():
            try:
                self.engine = GermanNLPEngine()
                self.engine.update_blacklist(self.custom_blacklist) 
                self.processor = ExcelDataProcessor(self.engine)
                self.root.after(0, lambda: self.lbl_status.config(text="✅ SpaCy离线引擎已完全就绪", fg=COLOR_SUCCESS))
            except Exception as e:
                self.root.after(0, lambda: messagebox.showerror("引擎加载失败", str(e)))
        threading.Thread(target=load_task, daemon=True).start()

    def do_split_text(self):
        if not self.engine:
            messagebox.showwarning("警告", "SpaCy 引擎仍在加载，请稍候。")
            return
        raw_text = self.text_input.get("1.0", tk.END).strip()
        if not raw_text:
            return
        sentences = self.engine.split_sentences(raw_text)
        self.text_output.delete("1.0", tk.END)
        for i, s in enumerate(sentences, 1):
            self.text_output.insert(tk.END, f"[{i}] {s}\n\n")

    def select_file(self):
        # 1. 限制只能选择 xlsx 文件
        filepath = filedialog.askopenfilename(filetypes=[("Excel 文件", "*.xlsx"), ("旧版 Excel", "*.xls")])
        if not filepath:
            return
            
        self.excel_filepath = filepath
        self.lbl_filename.config(text=os.path.basename(filepath), fg="#1F2937")
        
        # 2. 尝试用 pandas 读取表头
        try:
            df = pd.read_excel(filepath, nrows=0) # 极速读取，只读表头
            self.excel_headers = list(df.columns)
            
            self.combo_columns.config(values=self.excel_headers, state="readonly")
            if self.excel_headers:
                self.combo_columns.current(0)
                
            self.btn_run_excel.config(state="normal")
            self.lbl_progress_text.config(text="解析 Excel 表头成功，请选择对应的目标列后开启任务。")
        except Exception as e:
            messagebox.showerror("读取失败", f"无法读取该 Excel。\n详细信息: {e}")

    def start_excel_processing(self):
        target_col = self.combo_columns.get()
        if not target_col:
            return
        self.btn_run_excel.config(state="disabled", text="⚡ 后台流式计算中...", bg="#9CA3AF")
        self.combo_columns.config(state="disabled")
        self.progress_bar["value"] = 0
        threading.Thread(target=self._process_excel_thread, args=(target_col,), daemon=True).start()

    def _process_excel_thread(self, target_col):
        try:
            def update_progress(current, total):
                pct = (current / total) * 100
                self.root.after(0, self._set_progress_ui, pct, f"已流式写入: {current} / {total} 行 records...")

            output_file = self.processor.process_file(
                input_path=self.excel_filepath,
                target_col_name=target_col,
                progress_callback=update_progress
            )
            self.root.after(0, self._processing_done, True, output_file)
        except Exception as e:
            self.root.after(0, self._processing_done, False, str(e))

    def _set_progress_ui(self, pct, text):
        self.progress_bar["value"] = pct
        self.lbl_progress_text.config(text=text, fg=COLOR_TEXT_MAIN)

    def _processing_done(self, success, message):
        self.btn_run_excel.config(state="normal", text="▶ 开始流式处理并导出长表", bg=COLOR_PRIMARY)
        self.combo_columns.config(state="readonly")
        if success:
            self.lbl_progress_text.config(text="🎉 任务圆满完成！目标大表已被完全重写。", fg=COLOR_SUCCESS)
            if messagebox.askyesno("处理成功", f"格式重写完成，数据已完美落盘至：\n{message}\n\n是否立即查看输出文件夹？"):
                os.startfile(os.path.dirname(message))
        else:
            self.lbl_progress_text.config(text="❌ 任务中断", fg=COLOR_DANGER)
            messagebox.showerror("处理失败", f"队列处理发生致命异常:\n{message}")

    # ====================================================
    # --- 悬浮设置窗（美化版） ---
    # ====================================================
    def open_settings_modal(self):
        if not self.engine:
            return

        modal = tk.Toplevel(self.root)
        modal.title("自定义规则词库面板")
        modal.geometry("500x420")
        modal.configure(bg=COLOR_CARD)
        # modal.resizable(False, False)
        self.root.minsize(600, 480)
        modal.transient(self.root)
        modal.grab_set()

        tk.Label(modal, text="添加不希望被切断的缩写词 (需带句号)：", 
                 font=FONT_TITLE, fg=COLOR_TEXT_MAIN, bg=COLOR_CARD).pack(pady=(15, 5), padx=15, anchor=tk.W)

        # 扁平化规则输入区
        frame_input = tk.Frame(modal, bg=COLOR_CARD)
        frame_input.pack(fill=tk.X, padx=15, pady=5)
        
        entry_new_word = tk.Entry(frame_input, font=FONT_MAIN, fg=COLOR_TEXT_MAIN, bg="#F3F4F6", relief="solid", bd=1)
        entry_new_word.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=(0, 10), ipady=3)
        
        # 极简树状展示区
        tk.Label(modal, text="当前本地常驻拦截词库：", font=FONT_SMALL, fg=COLOR_TEXT_MUTED, bg=COLOR_CARD).pack(anchor=tk.W, padx=15, pady=(10, 2))
        
        frame_list = tk.Frame(modal, bg=COLOR_CARD)
        frame_list.pack(fill=tk.BOTH, expand=True, padx=15, pady=(0, 10))
        
        listbox = tk.Listbox(frame_list, font=FONT_MAIN, fg=COLOR_TEXT_MAIN, bg="#F9FAFB", 
                             relief="solid", bd=1, highlightthickness=0, selectbackground=COLOR_PRIMARY)
        listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        scrollbar = ttk.Scrollbar(frame_list, orient="vertical", command=listbox.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        listbox.config(yscrollcommand=scrollbar.set)

        for w in self.custom_blacklist:
            listbox.insert(tk.END, w)

        def add_word():
            word = entry_new_word.get().strip()
            if not word: return
            if word in self.custom_blacklist:
                messagebox.showinfo("提示", "规则库中已存在该字段。", parent=modal)
                return
            self.custom_blacklist.append(word)
            self.save_blacklist()
            self.engine.update_blacklist(self.custom_blacklist)
            listbox.insert(tk.END, word)
            entry_new_word.delete(0, tk.END)

        def delete_word():
            selected = listbox.curselection()
            if not selected: return
            word = listbox.get(selected[0])
            self.custom_blacklist.remove(word)
            self.save_blacklist()
            self.engine.update_blacklist(self.custom_blacklist)
            listbox.delete(selected[0])

        tk.Button(frame_input, text="添加规则", command=add_word, font=FONT_SMALL, bg=COLOR_PRIMARY, fg="white",
                  activebackground=COLOR_PRIMARY_HOVER, activeforeground="white", relief="flat", bd=0, cursor="hand2", padx=12).pack(side=tk.RIGHT)

        tk.Button(modal, text=" 🗑️ 移除选中规则 ", command=delete_word, font=FONT_SMALL, bg="#FEF2F2", fg=COLOR_DANGER,
                  activebackground="#FEE2E2", activeforeground=COLOR_DANGER, relief="solid", bd=1, cursor="hand2", pady=4).pack(fill=tk.X, padx=15, pady=(0, 15))

if __name__ == "__main__":
    root = tk.Tk()
    app = GermanSplitterApp(root)
    root.mainloop()