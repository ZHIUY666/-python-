import os
import platform
import ctypes
from typing import Optional, List

class SystemAdaptor:
    """系统适配类，处理跨平台系统调用和路径处理"""
    
    @staticmethod
    def get_system() -> str:
        """获取当前系统类型"""
        return platform.system()
    
    @staticmethod
    def is_windows() -> bool:
        """判断是否为Windows系统"""
        return SystemAdaptor.get_system() == "Windows"
    
    @staticmethod
    def is_macos() -> bool:
        """判断是否为macOS系统"""
        return SystemAdaptor.get_system() == "Darwin"
    
    @staticmethod
    def is_linux() -> bool:
        """判断是否为Linux系统"""
        return SystemAdaptor.get_system() == "Linux"
    
    @staticmethod
    def get_home_directory() -> str:
        """获取用户主目录"""
        return os.path.expanduser("~")
    
    @staticmethod
    def get_desktop_directory() -> str:
        """获取桌面目录"""
        if SystemAdaptor.is_windows():
            # Windows特殊处理，使用CSIDL_DESKTOP获取桌面路径
            import ctypes.wintypes
            CSIDL_DESKTOP = 0x0000
            buf = ctypes.create_unicode_buffer(260)
            ctypes.windll.shell32.SHGetSpecialFolderPathW(None, buf, CSIDL_DESKTOP, False)
            return buf.value
        else:
            return os.path.join(SystemAdaptor.get_home_directory(), "Desktop")
    
    @staticmethod
    def get_pictures_directory() -> str:
        """获取图片目录"""
        if SystemAdaptor.is_windows():
            # Windows特殊处理，使用CSIDL_MYPICTURES获取图片路径
            import ctypes.wintypes
            CSIDL_MYPICTURES = 0x0027
            buf = ctypes.create_unicode_buffer(260)
            ctypes.windll.shell32.SHGetSpecialFolderPathW(None, buf, CSIDL_MYPICTURES, False)
            return buf.value
        else:
            return os.path.join(SystemAdaptor.get_home_directory(), "Pictures")
    
    @staticmethod
    def get_videos_directory() -> str:
        """获取视频目录"""
        if SystemAdaptor.is_windows():
            # Windows特殊处理，使用CSIDL_MYVIDEO获取视频路径
            import ctypes.wintypes
            CSIDL_MYVIDEO = 0x0035
            buf = ctypes.create_unicode_buffer(260)
            ctypes.windll.shell32.SHGetSpecialFolderPathW(None, buf, CSIDL_MYVIDEO, False)
            return buf.value
        else:
            return os.path.join(SystemAdaptor.get_home_directory(), "Videos")
    
    @staticmethod
    def get_documents_directory() -> str:
        """获取文档目录"""
        if SystemAdaptor.is_windows():
            # Windows特殊处理，使用CSIDL_MYDOCUMENTS获取文档路径
            import ctypes.wintypes
            CSIDL_MYDOCUMENTS = 0x0005
            buf = ctypes.create_unicode_buffer(260)
            ctypes.windll.shell32.SHGetSpecialFolderPathW(None, buf, CSIDL_MYDOCUMENTS, False)
            return buf.value
        else:
            return os.path.join(SystemAdaptor.get_home_directory(), "Documents")
    
    @staticmethod
    def get_downloads_directory() -> str:
        """获取下载目录"""
        if SystemAdaptor.is_windows():
            # Windows特殊处理，使用CSIDL_DOWNLOADS获取下载路径
            import ctypes.wintypes
            CSIDL_DOWNLOADS = 0x0019
            buf = ctypes.create_unicode_buffer(260)
            ctypes.windll.shell32.SHGetSpecialFolderPathW(None, buf, CSIDL_DOWNLOADS, False)
            return buf.value
        else:
            return os.path.join(SystemAdaptor.get_home_directory(), "Downloads")
    
    @staticmethod
    def get_common_directories() -> List[str]:
        """获取常用目录列表"""
        return [
            SystemAdaptor.get_desktop_directory(),
            SystemAdaptor.get_pictures_directory(),
            SystemAdaptor.get_videos_directory(),
            SystemAdaptor.get_documents_directory(),
            SystemAdaptor.get_downloads_directory()
        ]
    
    @staticmethod
    def path_exists(path: str) -> bool:
        """判断路径是否存在"""
        try:
            return os.path.exists(path)
        except Exception:
            return False
    
    @staticmethod
    def is_directory(path: str) -> bool:
        """判断是否为目录"""
        try:
            return os.path.isdir(path)
        except Exception:
            return False
    
    @staticmethod
    def is_file(path: str) -> bool:
        """判断是否为文件"""
        try:
            return os.path.isfile(path)
        except Exception:
            return False
    
    @staticmethod
    def get_file_size(path: str) -> Optional[int]:
        """获取文件大小"""
        try:
            return os.path.getsize(path)
        except Exception:
            return None
    
    @staticmethod
    def get_file_mtime(path: str) -> Optional[float]:
        """获取文件修改时间"""
        try:
            return os.path.getmtime(path)
        except Exception:
            return None
    
    @staticmethod
    def join_paths(*paths) -> str:
        """拼接路径"""
        return os.path.join(*paths)
    
    @staticmethod
    def normalize_path(path: str) -> str:
        """规范化路径"""
        try:
            return os.path.normpath(path)
        except Exception:
            return path
    
    @staticmethod
    def get_absolute_path(path: str) -> str:
        """获取绝对路径"""
        try:
            return os.path.abspath(path)
        except Exception:
            return path
    
    @staticmethod
    def get_path_basename(path: str) -> str:
        """获取路径的basename"""
        try:
            return os.path.basename(path)
        except Exception:
            return path
    
    @staticmethod
    def get_path_dirname(path: str) -> str:
        """获取路径的dirname"""
        try:
            return os.path.dirname(path)
        except Exception:
            return path
    
    @staticmethod
    def get_path_extension(path: str) -> str:
        """获取路径的扩展名"""
        try:
            return os.path.splitext(path)[1].lower()
        except Exception:
            return ""
    
    @staticmethod
    def has_permission(path: str) -> bool:
        """判断是否有访问权限"""
        try:
            if os.path.isdir(path):
                # 尝试列出目录内容
                os.listdir(path)
            else:
                # 尝试打开文件
                with open(path, 'r') as f:
                    pass
            return True
        except Exception:
            return False
    
    @staticmethod
    def get_drives() -> List[str]:
        """获取所有驱动器（Windows）"""
        drives = []
        if SystemAdaptor.is_windows():
            # Windows获取所有驱动器
            import ctypes
            import string
            drives = []
            bitmask = ctypes.windll.kernel32.GetLogicalDrives()
            for letter in string.ascii_uppercase:
                if bitmask & 1:
                    drives.append(f"{letter}:\\")
                bitmask >>= 1
        return drives
    
    @staticmethod
    def get_system_directories() -> List[str]:
        """获取系统目录"""
        if SystemAdaptor.is_windows():
            return [
                os.environ.get("WINDIR", "C:\\Windows"),
                os.environ.get("PROGRAMFILES", "C:\\Program Files"),
                os.environ.get("PROGRAMFILES(X86)", "C:\\Program Files (x86)")
            ]
        return []
    
    @staticmethod
    def should_skip_directory(path: str) -> bool:
        """判断是否应该跳过目录"""
        # 跳过系统目录
        system_dirs = SystemAdaptor.get_system_directories()
        for system_dir in system_dirs:
            if path.startswith(system_dir):
                return True
        
        # 跳过隐藏目录
        try:
            if SystemAdaptor.is_windows():
                # Windows隐藏目录
                import ctypes
                attrs = ctypes.windll.kernel32.GetFileAttributesW(path)
                if attrs != -1 and (attrs & 0x02):  # FILE_ATTRIBUTE_HIDDEN
                    return True
            else:
                # Unix-like隐藏目录
                if os.path.basename(path).startswith('.'):
                    return True
        except Exception:
            pass
        
        return False
