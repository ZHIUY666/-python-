import os
import shutil
from typing import List, Optional
from src.adaptor.exception_handler import ExceptionHandler

class BatchOperations:
    """批量操作类，处理批量文件操作"""
    
    @staticmethod
    def batch_copy(files: List[str], destination: str) -> List[str]:
        """批量复制文件到目标目录"""
        success_files = []
        failed_files = []
        
        # 确保目标目录存在
        if not ExceptionHandler.safe_os_path_exists(destination):
            try:
                os.makedirs(destination, exist_ok=True)
            except Exception as e:
                ExceptionHandler.log_exception(e)
                return failed_files
        
        for file_path in files:
            try:
                # 安全检查文件是否存在
                if not ExceptionHandler.safe_os_path_exists(file_path):
                    failed_files.append(file_path)
                    continue
                
                # 构建目标文件路径
                file_name = os.path.basename(file_path)
                dest_path = os.path.join(destination, file_name)
                
                # 处理文件名冲突
                counter = 1
                while ExceptionHandler.safe_os_path_exists(dest_path):
                    name, ext = os.path.splitext(file_name)
                    dest_path = os.path.join(destination, f"{name}_{counter}{ext}")
                    counter += 1
                
                # 复制文件
                shutil.copy2(file_path, dest_path)
                success_files.append(file_path)
            except Exception as e:
                ExceptionHandler.log_exception(e)
                failed_files.append(file_path)
        
        return success_files
    
    @staticmethod
    def batch_move(files: List[str], destination: str) -> List[str]:
        """批量移动文件到目标目录"""
        success_files = []
        failed_files = []
        
        # 确保目标目录存在
        if not ExceptionHandler.safe_os_path_exists(destination):
            try:
                os.makedirs(destination, exist_ok=True)
            except Exception as e:
                ExceptionHandler.log_exception(e)
                return failed_files
        
        for file_path in files:
            try:
                # 安全检查文件是否存在
                if not ExceptionHandler.safe_os_path_exists(file_path):
                    failed_files.append(file_path)
                    continue
                
                # 构建目标文件路径
                file_name = os.path.basename(file_path)
                dest_path = os.path.join(destination, file_name)
                
                # 处理文件名冲突
                counter = 1
                while ExceptionHandler.safe_os_path_exists(dest_path):
                    name, ext = os.path.splitext(file_name)
                    dest_path = os.path.join(destination, f"{name}_{counter}{ext}")
                    counter += 1
                
                # 移动文件
                shutil.move(file_path, dest_path)
                success_files.append(file_path)
            except Exception as e:
                ExceptionHandler.log_exception(e)
                failed_files.append(file_path)
        
        return success_files
    
    @staticmethod
    def batch_delete(files: List[str]) -> List[str]:
        """批量删除文件"""
        success_files = []
        failed_files = []
        
        for file_path in files:
            try:
                # 安全检查文件是否存在
                if not ExceptionHandler.safe_os_path_exists(file_path):
                    failed_files.append(file_path)
                    continue
                
                # 删除文件
                os.remove(file_path)
                success_files.append(file_path)
            except Exception as e:
                ExceptionHandler.log_exception(e)
                failed_files.append(file_path)
        
        return success_files
    
    @staticmethod
    def batch_copy_path(files: List[str]) -> List[str]:
        """批量复制文件路径到剪贴板"""
        import pyperclip
        
        try:
            paths = '\n'.join(files)
            pyperclip.copy(paths)
            return files
        except Exception as e:
            ExceptionHandler.log_exception(e)
            return []
    
    @staticmethod
    def batch_rename(files: List[str], prefix: str = "", suffix: str = "") -> List[str]:
        """批量重命名文件"""
        success_files = []
        failed_files = []
        
        for file_path in files:
            try:
                # 安全检查文件是否存在
                if not ExceptionHandler.safe_os_path_exists(file_path):
                    failed_files.append(file_path)
                    continue
                
                # 构建新文件名
                directory = os.path.dirname(file_path)
                file_name = os.path.basename(file_path)
                name, ext = os.path.splitext(file_name)
                new_name = f"{prefix}{name}{suffix}{ext}"
                new_path = os.path.join(directory, new_name)
                
                # 处理文件名冲突
                counter = 1
                while ExceptionHandler.safe_os_path_exists(new_path):
                    new_name = f"{prefix}{name}{suffix}_{counter}{ext}"
                    new_path = os.path.join(directory, new_name)
                    counter += 1
                
                # 重命名文件
                os.rename(file_path, new_path)
                success_files.append(file_path)
            except Exception as e:
                ExceptionHandler.log_exception(e)
                failed_files.append(file_path)
        
        return success_files
    
    @staticmethod
    def batch_open(files: List[str]) -> List[str]:
        """批量打开文件"""
        success_files = []
        failed_files = []
        
        for file_path in files:
            try:
                # 安全检查文件是否存在
                if not ExceptionHandler.safe_os_path_exists(file_path):
                    failed_files.append(file_path)
                    continue
                
                # 打开文件
                import subprocess
                if os.name == 'nt':  # Windows
                    os.startfile(file_path)
                elif os.name == 'posix':  # macOS, Linux
                    subprocess.run(['open' if os.uname().sysname == 'Darwin' else 'xdg-open', file_path])
                success_files.append(file_path)
            except Exception as e:
                ExceptionHandler.log_exception(e)
                failed_files.append(file_path)
        
        return success_files
    
    @staticmethod
    def batch_locate(files: List[str]) -> List[str]:
        """批量定位文件"""
        success_files = []
        failed_files = []
        
        for file_path in files:
            try:
                # 安全检查文件是否存在
                if not ExceptionHandler.safe_os_path_exists(file_path):
                    failed_files.append(file_path)
                    continue
                
                # 定位文件
                directory = os.path.dirname(file_path)
                import subprocess
                if os.name == 'nt':  # Windows
                    subprocess.run(['explorer', '/select,', file_path])
                elif os.name == 'posix':  # macOS, Linux
                    if os.uname().sysname == 'Darwin':  # macOS
                        subprocess.run(['open', '-R', file_path])
                    else:  # Linux
                        subprocess.run(['xdg-open', directory])
                success_files.append(file_path)
            except Exception as e:
                ExceptionHandler.log_exception(e)
                failed_files.append(file_path)
        
        return success_files
