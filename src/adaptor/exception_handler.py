import traceback
import sys
from typing import Optional, Callable, Any
import os
import logging

class ExceptionHandler:
    """异常处理类，处理权限和异常兼容"""
    
    # 初始化日志
    @staticmethod
    def init_logging():
        """初始化日志"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            filename=os.path.join(os.path.expanduser("~"), ".mediafinder.log"),
            filemode='a'
        )
    
    @staticmethod
    def handle_exception(func: Callable) -> Callable:
        """异常处理装饰器"""
        def wrapper(*args, **kwargs) -> Optional[Any]:
            try:
                return func(*args, **kwargs)
            except Exception as e:
                ExceptionHandler.log_exception(e)
                return None
        return wrapper
    
    @staticmethod
    def log_exception(e: Exception):
        """记录异常"""
        logger = logging.getLogger("MediaFinder")
        logger.error(f"异常类型: {type(e).__name__}")
        logger.error(f"异常信息: {str(e)}")
        logger.error(f"堆栈信息: {traceback.format_exc()}")
    
    @staticmethod
    def handle_permission_error(path: str, log_error: bool = False) -> bool:
        """处理权限错误"""
        try:
            # 尝试获取路径权限
            if os.path.isdir(path):
                # 尝试列出目录内容
                os.listdir(path)
            else:
                # 尝试打开文件
                with open(path, 'r') as f:
                    pass
            return True
        except Exception as e:
            if log_error:
                ExceptionHandler.log_exception(e)
            return False
    
    @staticmethod
    def handle_long_path(path: str) -> Optional[str]:
        """处理超长路径"""
        try:
            # Windows最长路径限制为260个字符
            if len(path) >= 260:
                # 使用UNC路径格式
                unc_prefix = r'\\?\\'
                if not path.startswith(unc_prefix):
                    if os.path.isabs(path):
                        # 构建UNC路径
                        path = unc_prefix + path
                    else:
                        # 构建绝对UNC路径
                        path = unc_prefix + os.path.abspath(path)
            return path
        except Exception as e:
            ExceptionHandler.log_exception(e)
            return None
    
    @staticmethod
    def handle_corrupted_file(file_path: str) -> bool:
        """处理损坏的文件"""
        try:
            # 尝试获取文件大小
            if os.path.getsize(file_path) == 0:
                return False
            
            # 尝试打开文件，但不要读取内容
            # 有些系统文件可能无法读取，但我们仍然想扫描它们
            with open(file_path, 'rb') as f:
                pass
            
            return True
        except Exception as e:
            # 不记录这些错误，因为它们是预期的
            return False
    
    @staticmethod
    def handle_network_path(path: str) -> bool:
        """处理网络路径"""
        try:
            # 检查是否为网络路径
            if path.startswith('\\') or path.startswith('//'):
                # 尝试访问网络路径
                if os.path.exists(path):
                    return True
                else:
                    return False
            return True
        except Exception as e:
            ExceptionHandler.log_exception(e)
            return False
    
    @staticmethod
    def safe_os_walk(top: str, topdown: bool = True, onerror: Callable = None, followlinks: bool = False):
        """安全的os.walk包装器"""
        try:
            # 处理初始路径的超长路径问题
            safe_top = ExceptionHandler.handle_long_path(top)
            if not safe_top:
                return
            
            for root, dirs, files in os.walk(safe_top, topdown=topdown, onerror=onerror, followlinks=followlinks):
                # 处理超长路径
                safe_root = ExceptionHandler.handle_long_path(root)
                if not safe_root:
                    continue
                
                # 处理权限错误
                if not ExceptionHandler.handle_permission_error(safe_root):
                    continue
                
                # 处理网络路径
                if not ExceptionHandler.handle_network_path(safe_root):
                    continue
                
                # 处理目录列表
                safe_dirs = []
                for d in dirs:
                    dir_path = os.path.join(safe_root, d)
                    # 处理超长路径
                    safe_dir_path = ExceptionHandler.handle_long_path(dir_path)
                    if safe_dir_path and ExceptionHandler.handle_permission_error(safe_dir_path):
                        safe_dirs.append(d)
                
                # 处理文件列表 - 不移除任何文件，因为我们只是要扫描文件，不需要打开它们
                safe_files = files
                
                yield (safe_root, safe_dirs, safe_files)
        except Exception as e:
            ExceptionHandler.log_exception(e)
            return
    
    @staticmethod
    def safe_file_size(path: str) -> Optional[int]:
        """安全获取文件大小"""
        try:
            # 处理超长路径
            safe_path = ExceptionHandler.handle_long_path(path)
            if not safe_path:
                return None
            
            # 处理权限错误
            if not ExceptionHandler.handle_permission_error(safe_path):
                return None
            
            # 处理损坏的文件
            if not ExceptionHandler.handle_corrupted_file(safe_path):
                return None
            
            return os.path.getsize(safe_path)
        except Exception as e:
            ExceptionHandler.log_exception(e)
            return None
    
    @staticmethod
    def safe_file_mtime(path: str) -> Optional[float]:
        """安全获取文件修改时间"""
        try:
            # 处理超长路径
            safe_path = ExceptionHandler.handle_long_path(path)
            if not safe_path:
                return None
            
            # 处理权限错误
            if not ExceptionHandler.handle_permission_error(safe_path):
                return None
            
            # 处理损坏的文件
            if not ExceptionHandler.handle_corrupted_file(safe_path):
                return None
            
            return os.path.getmtime(safe_path)
        except Exception as e:
            ExceptionHandler.log_exception(e)
            return None
    
    @staticmethod
    def safe_file_open(path: str, mode: str = 'r') -> Optional[Any]:
        """安全打开文件"""
        try:
            # 处理超长路径
            safe_path = ExceptionHandler.handle_long_path(path)
            if not safe_path:
                return None
            
            # 处理权限错误
            if not ExceptionHandler.handle_permission_error(safe_path):
                return None
            
            # 处理损坏的文件
            if mode == 'r' and not ExceptionHandler.handle_corrupted_file(safe_path):
                return None
            
            return open(safe_path, mode)
        except Exception as e:
            ExceptionHandler.log_exception(e)
            return None
    
    @staticmethod
    def safe_os_listdir(path: str) -> Optional[list]:
        """安全列出目录内容"""
        try:
            # 处理超长路径
            safe_path = ExceptionHandler.handle_long_path(path)
            if not safe_path:
                return None
            
            # 处理权限错误
            if not ExceptionHandler.handle_permission_error(safe_path):
                return None
            
            return os.listdir(safe_path)
        except Exception as e:
            ExceptionHandler.log_exception(e)
            return None
    
    @staticmethod
    def safe_os_path_exists(path: str) -> bool:
        """安全判断路径是否存在"""
        try:
            # 处理超长路径
            safe_path = ExceptionHandler.handle_long_path(path)
            if not safe_path:
                return False
            
            return os.path.exists(safe_path)
        except Exception as e:
            ExceptionHandler.log_exception(e)
            return False
    
    @staticmethod
    def safe_os_path_isdir(path: str) -> bool:
        """安全判断是否为目录"""
        try:
            # 处理超长路径
            safe_path = ExceptionHandler.handle_long_path(path)
            if not safe_path:
                return False
            
            return os.path.isdir(safe_path)
        except Exception as e:
            ExceptionHandler.log_exception(e)
            return False
    
    @staticmethod
    def safe_os_path_isfile(path: str) -> bool:
        """安全判断是否为文件"""
        try:
            # 处理超长路径
            safe_path = ExceptionHandler.handle_long_path(path)
            if not safe_path:
                return False
            
            return os.path.isfile(safe_path)
        except Exception as e:
            ExceptionHandler.log_exception(e)
            return False