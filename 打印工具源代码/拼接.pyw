# 改动或使用前务必仔细阅读“说明.TXT”，依法使用！
import os
import ctypes
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from PIL import Image

# 适配高分屏 (HiDPI)
try:
    ctypes.windll.shcore.SetProcessDpiAwareness(2)
except Exception:
    try:
        ctypes.windll.user32.SetProcessDPIAware()
    except Exception:
        pass

class ImageGridMergerGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("卡牌图片网格拼接工具")
        self.root.geometry("600x420")
        self.root.minsize(500, 380)

        # 获取程序当前所在目录，作为“浏览”的初始目录
        self.script_dir = os.path.dirname(os.path.abspath(__file__))

        # 全局字体统一
        self.root.option_add("*Font", ("Microsoft YaHei UI", 9))

        self.setup_ui()

    def setup_ui(self):
        self.root.columnconfigure(0, weight=1)

        # 1. 路径设置
        frame_paths = ttk.LabelFrame(self.root, text=" 路径设置 ", padding=12)
        frame_paths.grid(row=0, column=0, sticky="ew", padx=15, pady=10)
        frame_paths.columnconfigure(1, weight=1)

        ttk.Label(frame_paths, text="图片文件夹:").grid(row=0, column=0, sticky="w", pady=4)
        self.entry_dir = ttk.Entry(frame_paths)
        self.entry_dir.grid(row=0, column=1, sticky="ew", padx=8, pady=4)
        ttk.Button(frame_paths, text="浏览...", command=self.browse_dir).grid(row=0, column=2, pady=4)

        # 2. 参数设置
        frame_settings = ttk.LabelFrame(self.root, text=" 拼接参数设置 ", padding=12)
        frame_settings.grid(row=1, column=0, sticky="ew", padx=15, pady=5)
        frame_settings.columnconfigure(1, weight=1)

        ttk.Label(frame_settings, text="每排图片张数 (2-9):").grid(row=0, column=0, sticky="w", pady=4)

        # 设置滑动条范围 2-9
        self.cols_var = tk.IntVar(value=5)

        self.lbl_cols_val = ttk.Label(frame_settings, text="5 张/排", width=8)
        self.lbl_cols_val.grid(row=0, column=2, sticky="w", pady=4)

        self.slider_cols = ttk.Scale(
            frame_settings, 
            from_=2, 
            to=9, 
            orient="horizontal", 
            variable=self.cols_var, 
            command=self.on_slider_change
        )
        self.slider_cols.grid(row=0, column=1, sticky="ew", padx=8, pady=4)

        # 3. 运行按钮
        btn_run = ttk.Button(self.root, text="🧩 生成 PNG 大图", command=self.process_images)
        btn_run.grid(row=2, column=0, pady=12)

        # 4. 日志输出
        frame_log = ttk.LabelFrame(self.root, text=" 处理日志 ", padding=10)
        frame_log.grid(row=3, column=0, sticky="nsew", padx=15, pady=(5, 15))
        self.root.rowconfigure(3, weight=1)
        frame_log.rowconfigure(0, weight=1)
        frame_log.columnconfigure(0, weight=1)

        self.log_box = tk.Text(frame_log, state="disabled", wrap="word", font=("Consolas", 10))
        self.log_box.grid(row=0, column=0, sticky="nsew")

        scrollbar = ttk.Scrollbar(frame_log, command=self.log_box.yview)
        scrollbar.grid(row=0, column=1, sticky="ns")
        self.log_box['yscrollcommand'] = scrollbar.set

    def on_slider_change(self, val):
        cols = int(float(val))
        if hasattr(self, 'lbl_cols_val'):
            self.lbl_cols_val.config(text=f"{cols} 张/排")

    def log(self, message):
        self.log_box.config(state="normal")
        self.log_box.insert("end", message + "\n")
        self.log_box.see("end")
        self.log_box.config(state="disabled")

    def browse_dir(self):
        # 初始目录打开程序所在的文件夹
        path = filedialog.askdirectory(title="选择图片文件夹", initialdir=self.script_dir)
        if path:
            self.entry_dir.delete(0, tk.END)
            self.entry_dir.insert(0, path)

    def process_images(self):
        input_dir = self.entry_dir.get().strip()
        cols = int(self.slider_cols.get())

        self.log_box.config(state="normal")
        self.log_box.delete("1.0", tk.END)
        self.log_box.config(state="disabled")

        if not os.path.exists(input_dir):
            messagebox.showerror("错误", "请选择有效的文件夹路径！")
            return

        # 1. 扫描文件并校验格式与分辨率
        supported_exts = ('.png', '.avif')
        image_files = []

        self.log("正在扫描与校验图片...")
        for file_name in sorted(os.listdir(input_dir)):
            file_path = os.path.join(input_dir, file_name)
            if not os.path.isfile(file_path):
                continue

            ext = os.path.splitext(file_name)[1].lower()
            if ext not in supported_exts:
                err_msg = f"格式校验失败！包含非 PNG/AVIF 文件: {file_name}"
                self.log(f"❌ {err_msg}")
                messagebox.showerror("文件格式错误", err_msg)
                return

            try:
                with Image.open(file_path) as img:
                    if img.width != 500 or img.height != 702:
                        err_msg = f"分辨率校验失败！文件 [{file_name}] 尺寸为 {img.width}x{img.height}，必须为 500x702。"
                        self.log(f"❌ {err_msg}")
                        messagebox.showerror("尺寸不匹配错误", err_msg)
                        return
            except Exception as e:
                err_msg = f"无法读取图片 [{file_name}]: {e}"
                self.log(f"❌ {err_msg}")
                messagebox.showerror("读取错误", err_msg)
                return

            image_files.append(file_path)

        total_files = len(image_files)
        if total_files == 0:
            messagebox.showwarning("提示", "文件夹内未找到符合要求的 PNG/AVIF 图片！")
            return

        self.log(f"通过校验！共找到 {total_files} 张符合规格(500x702)的图片。")

        # 2. 计算网格与行数
        rows = (total_files + cols - 1) // cols
        max_capacity = rows * cols

        self.log(f"网格布局: {rows} 行 x {cols} 列 (当前容纳上限: {max_capacity} 张)")

        if total_files > max_capacity:
            err_msg = f"图片超出排列容量！现有 {total_files} 张，而 {rows}x{cols} 网格只能放入 {max_capacity} 张。"
            self.log(f"❌ {err_msg}")
            messagebox.showerror("图片超限错误", err_msg)
            return

        blank_count = max_capacity - total_files
        if blank_count > 0:
            self.log(f"自动补充: 空缺 {blank_count} 张图片，将填充透明空白格子。")

        # 3. 拼接图像（不缩放，单张 500x702）
        orig_w, orig_h = 500, 702
        canvas_w = cols * orig_w
        canvas_h = rows * orig_h

        self.log(f"正在生成原始尺寸大图，分辨率: {canvas_w} x {canvas_h}...")
        canvas = Image.new("RGBA", (canvas_w, canvas_h), (0, 0, 0, 0))

        for idx, file_path in enumerate(image_files):
            r = idx // cols
            c = idx % cols
            x = c * orig_w
            y = r * orig_h

            with Image.open(file_path) as img:
                img_rgba = img.convert("RGBA")
                canvas.paste(img_rgba, (x, y))

        # 4. 计算保存路径：原文件夹所在的同级目录，文件名与原文件夹同名
        abs_input_dir = os.path.abspath(input_dir)
        parent_dir = os.path.dirname(abs_input_dir)
        folder_name = os.path.basename(abs_input_dir)
        save_path = os.path.join(parent_dir, f"{folder_name}.png")

        try:
            canvas.save(save_path, "PNG")
            self.log(f"\n🎉 成功保存拼接完成大图至:\n{save_path}")
            messagebox.showinfo("完成", f"大图生成成功！\n分辨率: {canvas_w}x{canvas_h}\n保存路径: {save_path}")
        except Exception as e:
            err_msg = f"保存文件失败: {e}"
            self.log(f"❌ {err_msg}")
            messagebox.showerror("保存失败", err_msg)

if __name__ == "__main__":
    root = tk.Tk()
    app = ImageGridMergerGUI(root)
    root.mainloop()
