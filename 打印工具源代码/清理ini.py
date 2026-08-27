# 放在根目录，强制删除目录内所有desktop.ini。
# 警告：不要乱移动或复制！特别是不要放到桌面去运行！
import os
import stat

def remove_desktop_ini():
    # 获取程序当前所在的文件夹路径
    current_dir = os.path.dirname(os.path.abspath(__file__))
    deleted_count = 0

    print(f"开始扫描目录: {current_dir}\n")

    # 递归遍历当前目录及所有子目录
    for root, dirs, files in os.walk(current_dir):
        for file_name in files:
            if file_name.lower() == "desktop.ini":
                file_path = os.path.join(root, file_name)
                try:
                    # 解除隐藏、系统、只读等文件属性限制
                    os.chmod(file_path, stat.S_IWRITE)
                    # 删除文件
                    os.remove(file_path)
                    deleted_count += 1
                    print(f"[已删除]: {file_path}")
                except Exception as e:
                    print(f"[删除失败]: {file_path}，原因: {e}")

    print(f"\n清理完成！共删除了 {deleted_count} 个 desktop.ini 文件。")

if __name__ == "__main__":
    remove_desktop_ini()
    os.system('pause')
