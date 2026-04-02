from typing import List, Dict, Optional
import time

class FilterUtils:
    """筛选工具类，处理文件筛选功能"""
    
    @staticmethod
    def filter_by_size(files: List[Dict], min_size: Optional[int] = None, max_size: Optional[int] = None) -> List[Dict]:
        """按文件大小筛选"""
        filtered_files = []
        
        for file_info in files:
            file_size = file_info.get('size', 0)
            
            # 检查最小大小
            if min_size is not None and file_size < min_size:
                continue
            
            # 检查最大大小
            if max_size is not None and file_size > max_size:
                continue
            
            filtered_files.append(file_info)
        
        return filtered_files
    
    @staticmethod
    def filter_by_time(files: List[Dict], start_time: Optional[float] = None, end_time: Optional[float] = None) -> List[Dict]:
        """按修改时间筛选"""
        filtered_files = []
        
        for file_info in files:
            file_mtime = file_info.get('mtime', 0)
            
            # 检查开始时间
            if start_time is not None and file_mtime < start_time:
                continue
            
            # 检查结束时间
            if end_time is not None and file_mtime > end_time:
                continue
            
            filtered_files.append(file_info)
        
        return filtered_files
    
    @staticmethod
    def filter_by_name(files: List[Dict], keyword: str) -> List[Dict]:
        """按文件名筛选"""
        if not keyword:
            return files
        
        filtered_files = []
        keyword = keyword.lower()
        
        for file_info in files:
            file_name = file_info.get('name', '').lower()
            if keyword in file_name:
                filtered_files.append(file_info)
        
        return filtered_files
    
    @staticmethod
    def filter_by_extension(files: List[Dict], extensions: List[str]) -> List[Dict]:
        """按文件扩展名筛选"""
        if not extensions:
            return files
        
        filtered_files = []
        extensions = [ext.lower() for ext in extensions]
        
        for file_info in files:
            file_name = file_info.get('name', '')
            ext = file_name.split('.')[-1].lower() if '.' in file_name else ''
            if ext in extensions:
                filtered_files.append(file_info)
        
        return filtered_files
    
    @staticmethod
    def filter_by_type(files: List[Dict], file_type: str) -> List[Dict]:
        """按文件类型筛选"""
        if not file_type or file_type == 'all':
            return files
        
        filtered_files = []
        
        for file_info in files:
            # 根据文件扩展名判断类型
            file_name = file_info.get('name', '')
            ext = file_name.split('.')[-1].lower() if '.' in file_name else ''
            
            if file_type == 'image':
                if ext in ['jpg', 'jpeg', 'png', 'gif', 'bmp', 'tiff', 'webp', 'raw', 'heic', 'psd', 'ai']:
                    filtered_files.append(file_info)
            elif file_type == 'video':
                if ext in ['mp4', 'avi', 'mov', 'wmv', 'flv', 'mkv', 'webm', 'm4v', 'ts', 'rmvb']:
                    filtered_files.append(file_info)
        
        return filtered_files
    
    @staticmethod
    def combine_filters(files: List[Dict], filters: Dict) -> List[Dict]:
        """组合多个筛选条件"""
        filtered_files = files.copy()
        
        # 按大小筛选
        min_size = filters.get('min_size')
        max_size = filters.get('max_size')
        if min_size is not None or max_size is not None:
            filtered_files = FilterUtils.filter_by_size(filtered_files, min_size, max_size)
        
        # 按时间筛选
        start_time = filters.get('start_time')
        end_time = filters.get('end_time')
        if start_time is not None or end_time is not None:
            filtered_files = FilterUtils.filter_by_time(filtered_files, start_time, end_time)
        
        # 按名称筛选
        keyword = filters.get('keyword', '')
        if keyword:
            filtered_files = FilterUtils.filter_by_name(filtered_files, keyword)
        
        # 按扩展名筛选
        extensions = filters.get('extensions', [])
        if extensions:
            filtered_files = FilterUtils.filter_by_extension(filtered_files, extensions)
        
        # 按类型筛选
        file_type = filters.get('file_type', 'all')
        if file_type != 'all':
            filtered_files = FilterUtils.filter_by_type(filtered_files, file_type)
        
        return filtered_files
    
    @staticmethod
    def sort_files(files: List[Dict], sort_by: str = 'name', reverse: bool = False) -> List[Dict]:
        """排序文件"""
        if sort_by == 'name':
            return sorted(files, key=lambda x: x.get('name', ''), reverse=reverse)
        elif sort_by == 'size':
            return sorted(files, key=lambda x: x.get('size', 0), reverse=reverse)
        elif sort_by == 'mtime':
            return sorted(files, key=lambda x: x.get('mtime', 0), reverse=reverse)
        else:
            return files
    
    @staticmethod
    def get_time_range(days: int) -> tuple:
        """获取时间范围"""
        end_time = time.time()
        start_time = end_time - (days * 24 * 60 * 60)
        return start_time, end_time
    
    @staticmethod
    def format_size(size: int) -> str:
        """格式化文件大小"""
        units = ['B', 'KB', 'MB', 'GB', 'TB']
        unit_index = 0
        current_size = size
        
        while current_size >= 1024 and unit_index < len(units) - 1:
            current_size /= 1024
            unit_index += 1
        
        return f"{current_size:.2f} {units[unit_index]}"
    
    @staticmethod
    def format_time(timestamp: float) -> str:
        """格式化时间"""
        return time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(timestamp))
