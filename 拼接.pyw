import os
import json
import ctypes
import tkinter as tk
from tkinter import filedialog, ttk
from PIL import Image

# 适配高分屏 (HiDPI)
try:
    ctypes.windll.shcore.SetProcessDpiAwareness(2)
except Exception:
    try:
        ctypes.windll.user32.SetProcessDPIAware()
    except Exception:
        pass

# 程序所在目录：所有相对路径与配置文件都以此为基准，与"当前工作目录"无关
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
# 拼接.pyw 与 解析.pyw 共享同一个 gui_config.json（各自只负责写自己的键）
CONFIG_FILE = os.path.join(BASE_DIR, "gui_config.json")
# 旧版本使用 gui_config_b.json，读取时会自动合并进来（首次运行完成迁移）
LEGACY_CONFIG_PATHS = (
    os.path.join(BASE_DIR, "gui_config_b.json"),
    os.path.abspath("gui_config_b.json"),
    os.path.abspath("gui_config.json"),
)


def config_file_candidates():
    """按优先级从低到高返回候选配置文件路径（越靠后优先级越高）"""
    seen, result = set(), []
    for path in tuple(LEGACY_CONFIG_PATHS) + (CONFIG_FILE,):
        key = os.path.normcase(os.path.normpath(path))
        if key not in seen:
            seen.add(key)
            result.append(path)
    return result


def read_config_file(path):
    """安全读取单个配置文件，失败返回空字典"""
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data if isinstance(data, dict) else {}
    except Exception:
        return {}


def load_shared_config(own_defaults):
    """读取共用配置：合并旧版本遗留文件，缺失项用本程序的默认值补齐"""
    merged = {}
    for path in config_file_candidates():
        if os.path.isfile(path):
            merged.update(read_config_file(path))
    for key, value in own_defaults.items():
        merged.setdefault(key, value)
    return merged


def save_shared_config(updates):
    """写入共用配置：只覆盖本程序负责的键，另一个程序的设置原样保留"""
    data = read_config_file(CONFIG_FILE)
    data.update(updates)
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)


class ImageGridMergerGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("卡牌图片网格拼接工具")
        self.root.geometry("600x450")
        self.root.minsize(500, 400)

        # 获取程序当前所在目录
        self.base_dir = BASE_DIR

        # 全局字体统一
        self.root.option_add("*Font", ("Microsoft YaHei UI", 9))

        self.config = self.load_config()
        self.setup_ui()

    def get_initial_dir(self, input_path):
        """
        计算文件资源管理器的起始目录：
        1. 目标已存在且是文件夹 -> 直接定位到该文件夹；
        2. 目标是文件 -> 定位到它所在的文件夹；
        3. 路径不存在 -> 逐级向上回溯到最近的已存在目录；
        4. 以上都失败 -> 退回程序所在目录。
        """
        input_path = self.clean_path(input_path)
        if not input_path:
            return self.base_dir

        abs_path = self.to_absolute_path(input_path)

        # 目标本身是文件夹 -> 直接定位
        if os.path.isdir(abs_path):
            return abs_path

        # 目标是文件 -> 定位到其所在文件夹；路径不存在 -> 逐级回溯到最近的已存在目录
        parent = os.path.dirname(abs_path)
        while parent and not os.path.isdir(parent):
            upper = os.path.dirname(parent)
            if upper == parent or not upper:
                break
            parent = upper
        return parent if parent and os.path.isdir(parent) else self.base_dir

    def clean_path(self, raw_path):
        """
        规范化用户输入的路径文本：
          - 去除首尾空白；
          - 去除成对的首尾引号（从资源管理器"复制为路径"会带引号）；
          - 展开 ~ 与环境变量；
          - 统一分隔符为正斜杠，避免 / 与 \\ 混用导致比较失败。
        """
        if raw_path is None:
            return ""
        text = str(raw_path).strip().strip("\ufeff").strip()
        while len(text) >= 2 and text[0] == text[-1] and text[0] in ("'", '"'):
            text = text[1:-1].strip()
        if not text:
            return ""
        try:
            text = os.path.expandvars(os.path.expanduser(text))
        except Exception:
            pass
        return text.replace("\\", "/").strip()

    def to_relative_path(self, absolute_path):
        """尝试将绝对路径转换为相对路径（以程序所在目录为基准，统一使用正斜杠）"""
        abs_path = self.to_absolute_path(absolute_path)
        if not abs_path:
            return ""
        try:
            rel_path = os.path.relpath(abs_path, self.base_dir)
        except ValueError:
            # 不同盘符 / UNC 路径，无法相对化，保留绝对路径
            return abs_path.replace("\\", "/")
        if rel_path == ".":
            return "."
        if rel_path.startswith(".."):
            return rel_path.replace("\\", "/")
        return "./" + rel_path.replace("\\", "/")

    def to_absolute_path(self, path_str):
        """将路径转为绝对路径（相对路径一律以程序所在目录为基准，而非当前工作目录）"""
        text = self.clean_path(path_str)
        if not text:
            return ""
        if not os.path.isabs(text):
            text = os.path.join(self.base_dir, text)
        return os.path.normpath(text)

    def load_config(self):
        """加载共用配置（与 解析.pyw 共享 gui_config.json），并兼容旧版本遗留文件"""
        default_cfg = {
            "input_dir": "./卡组",
            "cols": 5
        }
        config = load_shared_config(default_cfg)

        # 规范化路径写法（去引号 / 统一分隔符 / 去空白），避免历史配置中的脏数据
        cleaned_dir = self.clean_path(config.get("input_dir"))
        config["input_dir"] = cleaned_dir if cleaned_dir else default_cfg["input_dir"]

        # 列数兜底，避免配置损坏导致界面初始化异常
        try:
            cols = int(config.get("cols", 5))
        except Exception:
            cols = 5
        config["cols"] = min(9, max(2, cols))

        return config

    def save_config(self):
        """保存配置 (只写入本程序负责的键，不影响 解析.pyw 的设置)"""
        raw_dir = self.clean_path(self.entry_dir.get())
        input_dir = self.to_relative_path(raw_dir) if raw_dir else "./卡组"
        cols = int(self.slider_cols.get())

        self.config["input_dir"] = input_dir
        self.config["cols"] = cols

        try:
            save_shared_config({"input_dir": input_dir, "cols": cols})
        except Exception as e:
            self.log(f"⚠️ 保存配置失败: {e}")

    def setup_ui(self):
        self.root.columnconfigure(0, weight=1)

        # 1. 路径设置
        frame_paths = ttk.LabelFrame(self.root, text=" 路径设置 ", padding=12)
        frame_paths.grid(row=0, column=0, sticky="ew", padx=15, pady=10)
        frame_paths.columnconfigure(1, weight=1)

        ttk.Label(frame_paths, text="图片文件夹:").grid(row=0, column=0, sticky="w", pady=4)
        self.entry_dir = ttk.Entry(frame_paths)
        self.entry_dir.insert(0, self.config.get("input_dir", "./卡组"))
        self.entry_dir.grid(row=0, column=1, sticky="ew", padx=8, pady=4)
        ttk.Button(frame_paths, text="浏览...", command=self.browse_dir).grid(row=0, column=2, pady=4)

        # 2. 参数设置
        frame_settings = ttk.LabelFrame(self.root, text=" 拼接参数设置 ", padding=12)
        frame_settings.grid(row=1, column=0, sticky="ew", padx=15, pady=5)
        frame_settings.columnconfigure(1, weight=1)

        ttk.Label(frame_settings, text="每排图片张数 (2-9):").grid(row=0, column=0, sticky="w", pady=4)

        initial_cols = self.config.get("cols", 5)
        self.cols_var = tk.IntVar(value=initial_cols)

        self.lbl_cols_val = ttk.Label(frame_settings, text=f"{initial_cols} 张/排", width=8)
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
        curr_val = self.entry_dir.get()
        initial_dir = self.get_initial_dir(curr_val)
        path = filedialog.askdirectory(title="选择图片文件夹", initialdir=initial_dir)
        if path:
            rel_path = self.to_relative_path(path)
            self.entry_dir.delete(0, tk.END)
            self.entry_dir.insert(0, rel_path)
            self.log(f"已选择文件夹: {rel_path}")
            self.log(f"实际解析路径: {self.to_absolute_path(rel_path)}")

    def process_images(self):
        self.save_config()

        raw_input_dir = self.entry_dir.get()
        cols = int(self.slider_cols.get())
        input_dir = self.to_absolute_path(raw_input_dir)

        self.log_box.config(state="normal")
        self.log_box.delete("1.0", tk.END)
        self.log_box.config(state="disabled")

        self.log(f"图片文件夹: {self.to_relative_path(input_dir)}")
        self.log(f"解析为绝对路径: {input_dir}")
        self.log("")

        if not os.path.isdir(input_dir):
            self.log(f"❌ 错误: 请选择有效的文件夹路径！ -> {input_dir}")
            self.log("💡 提示: 相对路径以程序所在目录为基准；也可直接使用绝对路径（支持带引号粘贴）。")
            return

        supported_exts = ('.png', '.avif')
        image_files = []

        self.log("正在扫描与校验图片...")
        for file_name in sorted(os.listdir(input_dir)):
            # 忽略 desktop.ini 文件
            if file_name.lower() == "desktop.ini":
                self.log("ℹ️ 已跳过系统文件: desktop.ini")
                continue

            file_path = os.path.join(input_dir, file_name)
            if not os.path.isfile(file_path):
                continue

            ext = os.path.splitext(file_name)[1].lower()
            if ext not in supported_exts:
                self.log(f"❌ 格式校验失败！包含非 PNG/AVIF 文件: {file_name}")
                return

            try:
                with Image.open(file_path) as img:
                    w, h = img.width, img.height
                    
                    if w == 500 and h == 702:
                        image_files.append((file_path, False))  # 不需要缩放
                    else:
                        # 计算宽高比 (支持标准比例 4:3 ~ 3:2，即 1.333 ~ 1.5；也兼容纵向比例 3:4 ~ 2:3，即 0.666 ~ 0.75)
                        ratio_w_h = w / h
                        ratio_h_w = h / w

                        valid_ratio_1 = (4/3 <= ratio_w_h <= 3/2) or (3/4 <= ratio_w_h <= 2/3)
                        valid_ratio_2 = (4/3 <= ratio_h_w <= 3/2) or (3/4 <= ratio_h_w <= 2/3)

                        if valid_ratio_1 or valid_ratio_2:
                            self.log(f"⚠️ 图片 [{file_name}] 尺寸为 {w}x{h}，比例符合要求，将自动等比调整为 500x702。")
                            image_files.append((file_path, True))  # 需要缩放
                        else:
                            self.log(f"❌ 分辨率校验失败！文件 [{file_name}] 尺寸为 {w}x{h}，宽高比例不在 4:3 ~ 3:2 范围内。")
                            return
            except Exception as e:
                self.log(f"❌ 无法读取图片 [{file_name}]: {e}")
                return

        total_files = len(image_files)
        if total_files == 0:
            self.log("⚠️ 提示: 文件夹内未找到符合要求的 PNG/AVIF 图片！")
            return

        self.log(f"✅ 通过校验！共找到 {total_files} 张符合规格或适配比例的图片。")

        # 2. 计算网格布局
        rows = (total_files + cols - 1) // cols
        max_capacity = rows * cols

        self.log(f"网格布局: {rows} 行 x {cols} 列 (当前容纳上限: {max_capacity} 张)")

        blank_count = max_capacity - total_files
        if blank_count > 0:
            self.log(f"自动补充: 空缺 {blank_count} 张图片，将填充透明空白格子。")

        # 3. 拼接图像
        orig_w, orig_h = 500, 702
        canvas_w = cols * orig_w
        canvas_h = rows * orig_h

        self.log(f"正在生成拼接大图，目标分辨率: {canvas_w} x {canvas_h}...")
        canvas = Image.new("RGBA", (canvas_w, canvas_h), (0, 0, 0, 0))

        for idx, (file_path, need_resize) in enumerate(image_files):
            r = idx // cols
            c = idx % cols
            x = c * orig_w
            y = r * orig_h

            try:
                with Image.open(file_path) as img:
                    img_rgba = img.convert("RGBA")
                    if need_resize:
                        resample_method = getattr(Image, 'Resampling', Image).LANCZOS
                        img_rgba = img_rgba.resize((orig_w, orig_h), resample_method)
                    canvas.paste(img_rgba, (x, y))
            except Exception as e:
                self.log(f"❌ 处理图片 [{os.path.basename(file_path)}] 失败: {e}")
                return

        # 4. 保存输出到原文件夹同级目录下，并同名
        abs_input_dir = os.path.abspath(input_dir)
        parent_dir = os.path.dirname(abs_input_dir)
        folder_name = os.path.basename(abs_input_dir)
        save_path = os.path.join(parent_dir, f"{folder_name}.png")

        try:
            canvas.save(save_path, "PNG")
            self.log(f"\n🎉 拼接完成！大图已成功保存至:\n{save_path}")
        except Exception as e:
            self.log(f"❌ 保存文件失败: {e}")

if __name__ == "__main__":
    root = tk.Tk()
    app = ImageGridMergerGUI(root)
    root.protocol("WM_DELETE_WINDOW", lambda: (app.save_config(), root.destroy()))
    root.mainloop()