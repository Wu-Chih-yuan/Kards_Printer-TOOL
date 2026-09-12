import os
import json
import shutil
import ctypes
import tkinter as tk
from tkinter import filedialog, ttk

# ==================== 🛠️ 默认参数配置 (可在此处修改，优先使用相对路径) ====================
DEFAULT_SOURCE_DIR = "./card"
DEFAULT_JSON_PATH = "./Cards_v51.json"
DEFAULT_OUTPUT_DIR = "./卡组"
DEFAULT_DECK_CODE = ""
# =======================================================================

# 适配高分屏 (HiDPI)
try:
    ctypes.windll.shcore.SetProcessDpiAwareness(2)
except Exception:
    try:
        ctypes.windll.user32.SetProcessDPIAware()
    except Exception:
        pass

CONFIG_FILE = "gui_config.json"

class DeckPickerGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("KARDS卡组卡牌图片拾取器")
        self.root.geometry("780x640")
        self.root.minsize(650, 500)

        # 获取程序根目录，用于相对路径转换与基准判断
        self.base_dir = os.path.dirname(os.path.abspath(__file__))

        # 全局字体适配
        self.default_font = ("Microsoft YaHei UI", 9)
        self.root.option_add("*Font", self.default_font)

        self.config = self.load_config()
        self.setup_ui()

    def get_initial_dir(self, input_path):
        """
        根据要求的逻辑计算文件资源管理器的起始目录：
        1. 若为相对路径：从原路径的上一级文件夹开始浏览。
        2. 若为绝对路径：尝试定位，若路径不存在则退回 .\ (程序根目录)。
        """
        input_path = input_path.strip() if input_path else ""
        if not input_path:
            return self.base_dir

        if os.path.isabs(input_path):
            # 绝对路径逻辑
            if os.path.exists(input_path):
                return input_path if os.path.isdir(input_path) else os.path.dirname(input_path)
            else:
                return self.base_dir
        else:
            # 相对路径逻辑：转换为绝对路径后取上一级目录
            abs_path = os.path.abspath(os.path.join(self.base_dir, input_path))
            parent_dir = os.path.dirname(abs_path)
            return parent_dir if os.path.exists(parent_dir) else self.base_dir

    def to_relative_path(self, absolute_path):
        """尝试将绝对路径转换为相对路径，若不在同一驱动盘或转换失败则保留原样"""
        if not absolute_path:
            return absolute_path
        try:
            rel_path = os.path.relpath(absolute_path, self.base_dir)
            if not rel_path.startswith(".."):
                return "./" + rel_path.replace("\\", "/")
            return rel_path.replace("\\", "/")
        except Exception:
            return absolute_path

    def to_absolute_path(self, path_str):
        """将路径转为绝对路径（以程序所在目录为基准）"""
        if not path_str:
            return path_str
        if os.path.isabs(path_str):
            return os.path.abspath(path_str)
        return os.path.abspath(os.path.join(self.base_dir, path_str))

    def load_config(self):
        """加载本地配置，无配置则使用顶部默认参数"""
        default_cfg = {
            "source_dir": DEFAULT_SOURCE_DIR,
            "json_path": DEFAULT_JSON_PATH,
            "output_dir": DEFAULT_OUTPUT_DIR,
            "deck_code": DEFAULT_DECK_CODE
        }
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                    user_cfg = json.load(f)
                    default_cfg.update(user_cfg)
            except Exception:
                pass
        return default_cfg

    def save_config(self):
        """保存配置 (保存 UI 中的路径设置)"""
        self.config["source_dir"] = self.entry_source.get().strip()
        self.config["json_path"] = self.entry_json.get().strip()
        self.config["output_dir"] = self.entry_output.get().strip()
        self.config["deck_code"] = self.text_code.get("1.0", tk.END).strip()

        try:
            with open(CONFIG_FILE, "w", encoding="utf-8") as f:
                json.dump(self.config, f, ensure_ascii=False, indent=4)
        except Exception as e:
            print(f"保存配置失败: {e}")

    def setup_ui(self):
        self.root.rowconfigure(3, weight=1)
        self.root.columnconfigure(0, weight=1)

        # 1. 路径设置区域
        frame_paths = ttk.LabelFrame(self.root, text=" 路径设置 ", padding=12)
        frame_paths.grid(row=0, column=0, sticky="ew", padx=15, pady=8)
        frame_paths.columnconfigure(1, weight=1)

        # 图片源目录
        ttk.Label(frame_paths, text="图片源目录:").grid(row=0, column=0, sticky="w", pady=4)
        self.entry_source = ttk.Entry(frame_paths)
        self.entry_source.insert(0, self.config["source_dir"])
        self.entry_source.grid(row=0, column=1, sticky="ew", padx=8, pady=4)
        ttk.Button(frame_paths, text="浏览...", command=self.browse_source).grid(row=0, column=2, pady=4)

        # 数据库 JSON 路径
        ttk.Label(frame_paths, text="数据库文件:").grid(row=1, column=0, sticky="w", pady=4)
        self.entry_json = ttk.Entry(frame_paths)
        self.entry_json.insert(0, self.config["json_path"])
        self.entry_json.grid(row=1, column=1, sticky="ew", padx=8, pady=4)
        ttk.Button(frame_paths, text="浏览...", command=self.browse_json).grid(row=1, column=2, pady=4)

        # 输出保存目录
        ttk.Label(frame_paths, text="图片保存目录:").grid(row=2, column=0, sticky="w", pady=4)
        self.entry_output = ttk.Entry(frame_paths)
        self.entry_output.insert(0, self.config["output_dir"])
        self.entry_output.grid(row=2, column=1, sticky="ew", padx=8, pady=4)
        ttk.Button(frame_paths, text="浏览...", command=self.browse_output).grid(row=2, column=2, pady=4)

        # 2. 卡组代码输入区域
        frame_input = ttk.LabelFrame(self.root, text=" 卡组代码输入 ", padding=12)
        frame_input.grid(row=1, column=0, sticky="ew", padx=15, pady=5)
        frame_input.columnconfigure(0, weight=1)

        self.text_code = tk.Text(frame_input, height=3, font=("Consolas", 10))
        self.text_code.grid(row=0, column=0, sticky="ew", pady=2)
        self.text_code.insert("1.0", self.config["deck_code"])

        # 3. 运行按钮
        btn_run = ttk.Button(self.root, text="🚀 开始解析并拾取图片", command=self.process_deck)
        btn_run.grid(row=2, column=0, pady=8)

        # 4. 运行日志区域
        frame_log = ttk.LabelFrame(self.root, text=" 运行日志 ", padding=10)
        frame_log.grid(row=3, column=0, sticky="nsew", padx=15, pady=(5, 15))
        frame_log.rowconfigure(0, weight=1)
        frame_log.columnconfigure(0, weight=1)

        self.log_box = tk.Text(frame_log, state="disabled", wrap="word", font=("Consolas", 10))
        self.log_box.grid(row=0, column=0, sticky="nsew")

        scrollbar = ttk.Scrollbar(frame_log, command=self.log_box.yview)
        scrollbar.grid(row=0, column=1, sticky="ns")
        self.log_box['yscrollcommand'] = scrollbar.set

    def log(self, message):
        self.log_box.config(state="normal")
        self.log_box.insert("end", message + "\n")
        self.log_box.see("end")
        self.log_box.config(state="disabled")

    def browse_source(self):
        curr_val = self.entry_source.get()
        initial_dir = self.get_initial_dir(curr_val)
        path = filedialog.askdirectory(title="选择 kards 图片库文件夹", initialdir=initial_dir)
        if path:
            rel_path = self.to_relative_path(path)
            self.entry_source.delete(0, tk.END)
            self.entry_source.insert(0, rel_path)

    def browse_json(self):
        curr_val = self.entry_json.get()
        initial_dir = self.get_initial_dir(curr_val)
        path = filedialog.askopenfilename(
            title="选择 Cards_v51.json 文件", 
            initialdir=initial_dir, 
            filetypes=[("JSON Files", "*.json")]
        )
        if path:
            rel_path = self.to_relative_path(path)
            self.entry_json.delete(0, tk.END)
            self.entry_json.insert(0, rel_path)

    def browse_output(self):
        curr_val = self.entry_output.get()
        initial_dir = self.get_initial_dir(curr_val)
        path = filedialog.askdirectory(title="选择图片保存文件夹", initialdir=initial_dir)
        if path:
            rel_path = self.to_relative_path(path)
            self.entry_output.delete(0, tk.END)
            self.entry_output.insert(0, rel_path)

    def load_mapping(self, json_path):
        if not os.path.exists(json_path):
            self.log(f"❌ 错误: 找不到 JSON 文件 -> {json_path}")
            return None

        try:
            with open(json_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                cards_list = data
                if isinstance(data, dict):
                    cards_list = data.get("cards") or data.get("items") or list(data.values())

                mapping = {}
                for card in cards_list:
                    if isinstance(card, dict):
                        imp_id = card.get("importId")
                        card_code = card.get("cardId") or (card.get("json") and card.get("json").get("id"))
                        if imp_id and card_code:
                            card_code_clean = str(card_code).split('.')[0].lower()
                            mapping[imp_id] = card_code_clean
                return mapping
        except Exception as e:
            self.log(f"❌ 错误: 解析 JSON 失败: {e}")
            return None

    def parse_deck_with_count(self, code):
        if "%%" not in code or "|" not in code:
            return None

        try:
            cards_section = code.split("|")[1]
            for i, char in enumerate(cards_section):
                if char not in "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789;":
                    cards_section = cards_section[:i]
                    break

            codes_str = cards_section + ";"
            card_counts = {}
            temp_import_codes = []
            c_str = ""
            card_count = 0

            for char in codes_str:
                if char == ';':
                    card_count += 1
                    for imp_code in temp_import_codes:
                        card_counts[imp_code] = card_counts.get(imp_code, 0) + card_count
                    temp_import_codes = []
                else:
                    if len(c_str) == 1:
                        c_str += char
                        temp_import_codes.append(c_str)
                        c_str = ""
                    else:
                        c_str += char

            return card_counts
        except Exception as e:
            self.log(f"❌ 错误: 卡组代码解析失败: {e}")
            return None

    def process_deck(self):
        self.save_config()

        raw_source = self.entry_source.get().strip()
        raw_json = self.entry_json.get().strip()
        raw_output = self.entry_output.get().strip()
        deck_code = self.text_code.get("1.0", tk.END).strip()

        source_dir = self.to_absolute_path(raw_source)
        json_path = self.to_absolute_path(raw_json)
        output_dir = self.to_absolute_path(raw_output)

        self.log_box.config(state="normal")
        self.log_box.delete("1.0", tk.END)
        self.log_box.config(state="disabled")

        if not os.path.exists(source_dir):
            self.log(f"❌ 错误: 指定的图片源目录不存在 -> {source_dir}")
            return

        mapping = self.load_mapping(json_path)
        if not mapping:
            self.log("❌ 错误: 无法加载数据库映射！")
            return

        card_counts = self.parse_deck_with_count(deck_code)
        if not card_counts:
            self.log("❌ 错误: 卡组代码格式不正确，必须包含 %% 和 |")
            return

        if not os.path.exists(output_dir):
            try:
                os.makedirs(output_dir)
            except Exception as e:
                self.log(f"❌ 错误: 无法创建输出目录 [{output_dir}]: {e}")
                return

        self.log("正在读取本地图片列表...")
        try:
            local_files = os.listdir(source_dir)
        except Exception as e:
            self.log(f"❌ 错误: 读取图片源目录失败: {e}")
            return

        local_file_map = {}
        for f in local_files:
            name_without_ext = os.path.splitext(f)[0].lower()
            local_file_map[name_without_ext.strip()] = f

        success_files = 0
        total_cards_count = sum(card_counts.values())
        self.log(f"卡组解析成功: 包含 {len(card_counts)} 种卡牌，共 {total_cards_count} 张卡牌。")
        self.log(f"保存路径: {output_dir}\n")

        for imp_id, count in card_counts.items():
            card_code = mapping.get(imp_id)
            if not card_code:
                self.log(f"⚠️ 警告: 未知的卡牌 importId [{imp_id}]")
                continue

            matched_filename = local_file_map.get(card_code)
            if matched_filename:
                src_path = os.path.join(source_dir, matched_filename)
                base_name, ext = os.path.splitext(matched_filename)

                for i in range(1, count + 1):
                    new_filename = f"{base_name}_{i}{ext}" if count > 1 else matched_filename
                    dst_path = os.path.join(output_dir, new_filename)
                    try:
                        shutil.copy(src_path, dst_path)
                        success_files += 1
                    except Exception as e:
                        self.log(f"❌ 复制文件失败 [{new_filename}]: {e}")

                self.log(f"✅ 成功导出 ({count}张): {matched_filename}")
            else:
                self.log(f"❌ 失败: 本地缺少卡牌图片 [{card_code}]")

        self.log(f"\n🎉 处理完毕！成功导出 {success_files}/{total_cards_count} 张图片到目录:\n{output_dir}")

if __name__ == "__main__":
    root = tk.Tk()
    app = DeckPickerGUI(root)
    root.protocol("WM_DELETE_WINDOW", lambda: (app.save_config(), root.destroy()))
    root.mainloop()
