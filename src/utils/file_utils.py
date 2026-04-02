import os
import platform
import subprocess
from typing import Optional

class FileUtils:
    @staticmethod
    def open_file(file_path: str) -> bool:
        """使用系统默认程序打开文件"""
        try:
            if platform.system() == "Windows":
                os.startfile(file_path)
            elif platform.system() == "Darwin":  # macOS
                subprocess.run(["open", file_path], check=True)
            else:  # Linux
                subprocess.run(["xdg-open", file_path], check=True)
            return True
        except Exception as e:
            print(f"打开文件失败: {e}")
            return False
    
    @staticmethod
    def locate_file(file_path: str) -> bool:
        """在文件管理器中定位文件"""
        try:
            folder = os.path.dirname(file_path)
            
            if platform.system() == "Windows":
                # Windows资源管理器，选中文件
                # 确保路径使用正确的Windows路径格式
                file_path = file_path.replace('/', '\\')  # 确保使用反斜杠
                folder = folder.replace('/', '\\')  # 确保文件夹路径也使用反斜杠
                
                # 首先尝试使用/select参数选中文件
                # 使用shell=True来正确处理路径中的空格和特殊字符
                import shlex
                cmd = f'explorer /select,"{file_path}"'
                result = subprocess.run(cmd, shell=True, check=False, capture_output=True)
                
                # 如果explorer命令成功执行（返回码为0或1都算成功，因为1通常表示窗口已打开）
                if result.returncode in [0, 1]:
                    return True
                else:
                    # 如果失败，尝试只打开文件夹
                    cmd2 = f'explorer "{folder}"'
                    result2 = subprocess.run(cmd2, shell=True, check=False, capture_output=True)
                    return result2.returncode in [0, 1]
            elif platform.system() == "Darwin":  # macOS
                # Finder，选中文件
                subprocess.run(["open", "-R", file_path], check=True)
                return True
            else:  # Linux
                # 大多数Linux文件管理器支持通过路径打开
                subprocess.run(["xdg-open", folder], check=True)
                return True
        except Exception as e:
            print(f"定位文件失败: {e}")
            return False
    
    @staticmethod
    def copy_file_path(file_path: str) -> bool:
        """复制文件路径到剪贴板"""
        try:
            if platform.system() == "Windows":
                # Windows剪贴板
                subprocess.run(["clip"], input=file_path.encode(), check=True)
            elif platform.system() == "Darwin":  # macOS
                # macOS剪贴板
                subprocess.run(["pbcopy"], input=file_path.encode(), check=True)
            else:  # Linux
                # Linux剪贴板（需要xclip或xsel）
                try:
                    subprocess.run(["xclip", "-selection", "clipboard"], input=file_path.encode(), check=True)
                except FileNotFoundError:
                    try:
                        subprocess.run(["xsel", "--clipboard", "--input"], input=file_path.encode(), check=True)
                    except FileNotFoundError:
                        print("复制失败：系统缺少xclip或xsel工具")
                        return False
            return True
        except Exception as e:
            print(f"复制路径失败: {e}")
            return False
    
    @staticmethod
    def get_file_size(file_path: str) -> Optional[int]:
        """获取文件大小（字节）"""
        try:
            return os.path.getsize(file_path)
        except Exception as e:
            print(f"获取文件大小失败: {e}")
            return None
    
    @staticmethod
    def get_file_modification_time(file_path: str) -> Optional[float]:
        """获取文件修改时间"""
        try:
            return os.path.getmtime(file_path)
        except Exception as e:
            print(f"获取文件修改时间失败: {e}")
            return None
    
    @staticmethod
    def get_file_extension(file_path: str) -> str:
        """获取文件扩展名"""
        return os.path.splitext(file_path)[1].lower()
    
    @staticmethod
    def is_image_file(file_path: str) -> bool:
        """判断是否为图片文件"""
        image_extensions = ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.webp', '.raw', '.heic', '.psd', '.ai']
        ext = FileUtils.get_file_extension(file_path)
        return ext in image_extensions
    
    @staticmethod
    def is_video_file(file_path: str) -> bool:
        """判断是否为视频文件"""
        video_extensions = ['.mp4', '.mkv', '.mov', '.avi', '.flv', '.wmv', '.rmvb', '.webm', '.m4v', '.ts']
        ext = FileUtils.get_file_extension(file_path)
        return ext in video_extensions
    
    @staticmethod
    def get_file_name(file_path: str) -> str:
        """获取文件名（不含路径）"""
        return os.path.basename(file_path)
    
    @staticmethod
    def get_file_directory(file_path: str) -> str:
        """获取文件所在目录"""
        return os.path.dirname(file_path)
    
    @staticmethod
    def join_paths(*paths) -> str:
        """拼接路径"""
        return os.path.join(*paths)
    
    @staticmethod
    def is_path_valid(path: str) -> bool:
        """判断路径是否有效"""
        try:
            return os.path.exists(path)
        except Exception:
            return False
    
    @staticmethod
    def get_home_directory() -> str:
        """获取用户主目录"""
        return os.path.expanduser("~")
    
    @staticmethod
    def get_desktop_directory() -> str:
        """获取桌面目录"""
        return os.path.join(FileUtils.get_home_directory(), "Desktop")
    
    @staticmethod
    def get_documents_directory() -> str:
        """获取文档目录"""
        return os.path.join(FileUtils.get_home_directory(), "Documents")
    
    @staticmethod
    def get_pictures_directory() -> str:
        """获取图片目录"""
        return os.path.join(FileUtils.get_home_directory(), "Pictures")
    
    @staticmethod
    def get_videos_directory() -> str:
        """获取视频目录"""
        return os.path.join(FileUtils.get_home_directory(), "Videos")
