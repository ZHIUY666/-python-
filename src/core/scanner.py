import os
import time
import threading
import queue
from typing import List, Dict, Optional
from src.adaptor.system_adaptor import SystemAdaptor
from src.adaptor.exception_handler import ExceptionHandler
from src.adaptor.format_adaptor import FormatAdaptor

class MediaScanner:
    def __init__(self, path: str, file_types: List[str], blacklist: List[str] = None, resume_scan: bool = False, last_scan_time: float = 0):
        self.path = path
        self.file_types = file_types
        self.blacklist = blacklist or []
        self.running = True
        self.results = []
        self.total_files = 0
        self.found_files = 0
        self.start_time = 0
        self.progress_callback = None
        self.file_found_callback = None
        self.resume_scan = resume_scan
        self.last_scan_time = last_scan_time
        self.scanned_files = set()  # 用于断点续扫和增量扫描
    
    def set_callbacks(self, progress_callback=None, file_found_callback=None):
        """设置回调函数"""
        self.progress_callback = progress_callback
        self.file_found_callback = file_found_callback
    
    def scan(self) -> List[Dict]:
        """开始扫描"""
        self.start_time = time.time()
        self.results = []
        self.total_files = 0
        self.found_files = 0
        
        # 先计算总文件数
        self._count_files()
        
        # 开始扫描
        self._scan_directory(self.path)
        
        return self.results
    
    def _count_files(self):
        """计算总文件数"""
        # 使用安全的目录遍历
        for root, dirs, files in ExceptionHandler.safe_os_walk(self.path):
            if not self.running:
                return
            
            # 跳过黑名单目录
            dirs[:] = [d for d in dirs if os.path.join(root, d) not in self.blacklist]
            
            # 跳过系统目录和隐藏目录
            dirs[:] = [d for d in dirs if not SystemAdaptor.should_skip_directory(os.path.join(root, d))]
            
            for file in files:
                if any(file.lower().endswith(ext) for ext in self.file_types):
                    self.total_files += 1
    
    def _scan_directory(self, directory: str):
        """扫描目录"""
        try:
            # 使用安全的目录遍历
            for root, dirs, files in ExceptionHandler.safe_os_walk(directory):
                if not self.running:
                    return
                
                # 跳过黑名单目录
                dirs[:] = [d for d in dirs if os.path.join(root, d) not in self.blacklist]
                
                # 跳过系统目录和隐藏目录
                dirs[:] = [d for d in dirs if not SystemAdaptor.should_skip_directory(os.path.join(root, d))]
                
                for file in files:
                    if not self.running:
                        return
                    
                    if any(file.lower().endswith(ext) for ext in self.file_types):
                        file_path = os.path.join(root, file)
                        
                        # 断点续扫：跳过已经扫描过的文件
                        if self.resume_scan and file_path in self.scanned_files:
                            continue
                        
                        # 安全获取文件信息
                        file_size = ExceptionHandler.safe_file_size(file_path)
                        file_mtime = ExceptionHandler.safe_file_mtime(file_path)
                        
                        if file_size is not None and file_mtime is not None:
                            # 增量扫描：只扫描修改时间大于last_scan_time的文件
                            if self.last_scan_time > 0 and file_mtime <= self.last_scan_time:
                                continue
                            
                            file_info = {
                                'name': file,
                                'path': file_path,
                                'size': file_size,
                                'mtime': file_mtime
                            }
                            self.results.append(file_info)
                            self.found_files += 1
                            self.scanned_files.add(file_path)  # 记录已扫描的文件
                            
                            # 调用回调函数
                            if self.file_found_callback:
                                self.file_found_callback(file_info)
                            
                            # 更新进度
                            if self.progress_callback:
                                elapsed = time.time() - self.start_time
                                progress = int((self.found_files / self.total_files) * 100) if self.total_files > 0 else 0
                                self.progress_callback(progress, self.found_files, f"{elapsed:.2f}s")
        except Exception as e:
            ExceptionHandler.log_exception(e)
    
    def stop(self):
        """停止扫描"""
        self.running = False

class MultiThreadedMediaScanner:
    def __init__(self, path: str, file_types: List[str], blacklist: List[str] = None, thread_count: int = 4, resume_scan: bool = False, last_scan_time: float = 0):
        self.path = path
        self.file_types = file_types
        self.blacklist = blacklist or []
        self.thread_count = thread_count
        self.running = True
        self.results = []
        self.total_files = 0
        self.found_files = 0
        self.start_time = 0
        self.progress_callback = None
        self.file_found_callback = None
        self.file_queue = queue.Queue(maxsize=1000)  # 限制队列大小，防止内存溢出
        self.resume_scan = resume_scan
        self.last_scan_time = last_scan_time
        self.scanned_files = set()  # 用于断点续扫和增量扫描
        self.lock = threading.Lock()  # 用于线程安全操作
    
    def set_callbacks(self, progress_callback=None, file_found_callback=None):
        """设置回调函数"""
        self.progress_callback = progress_callback
        self.file_found_callback = file_found_callback
    
    def scan(self) -> List[Dict]:
        """开始扫描"""
        self.start_time = time.time()
        self.results = []
        self.total_files = 0
        self.found_files = 0
        
        # 创建并启动线程
        threads = []
        
        # 创建一个线程用于填充队列
        producer_thread = threading.Thread(target=self._fill_file_queue)
        producer_thread.daemon = True
        producer_thread.start()
        
        # 创建工作线程
        for _ in range(self.thread_count):
            thread = threading.Thread(target=self._scan_worker)
            thread.daemon = True
            thread.start()
            threads.append(thread)
        
        # 等待生产者线程完成
        producer_thread.join()
        
        # 等待所有工作线程完成
        for thread in threads:
            thread.join()
        
        return self.results
    
    def _count_files(self):
        """计算总文件数"""
        # 使用安全的目录遍历
        for root, dirs, files in ExceptionHandler.safe_os_walk(self.path):
            if not self.running:
                return
            
            # 跳过黑名单目录
            dirs[:] = [d for d in dirs if os.path.join(root, d) not in self.blacklist]
            
            # 跳过系统目录和隐藏目录
            dirs[:] = [d for d in dirs if not SystemAdaptor.should_skip_directory(os.path.join(root, d))]
            
            for file in files:
                if any(file.lower().endswith(ext) for ext in self.file_types):
                    self.total_files += 1
    
    def _fill_file_queue(self):
        """填充文件队列"""
        try:
            # 使用安全的目录遍历
            for root, dirs, files in ExceptionHandler.safe_os_walk(self.path):
                if not self.running:
                    break
                
                # 跳过黑名单目录
                dirs[:] = [d for d in dirs if os.path.join(root, d) not in self.blacklist]
                
                # 跳过系统目录和隐藏目录
                dirs[:] = [d for d in dirs if not SystemAdaptor.should_skip_directory(os.path.join(root, d))]
                
                for file in files:
                    if not self.running:
                        break
                    
                    if any(file.lower().endswith(ext) for ext in self.file_types):
                        file_path = os.path.join(root, file)
                        # 非阻塞方式放入队列，防止队列满时阻塞
                        try:
                            self.file_queue.put(file_path, block=False)
                        except queue.Full:
                            # 队列已满，短暂睡眠后重试
                            time.sleep(0.1)
                            try:
                                self.file_queue.put(file_path, block=True, timeout=1)
                            except queue.Full:
                                # 仍然满，跳过这个文件
                                continue
            
            # 为每个线程添加结束标志
            for _ in range(self.thread_count):
                while self.running:
                    try:
                        self.file_queue.put(None, block=False)
                        break
                    except queue.Full:
                        time.sleep(0.1)
        except Exception as e:
            ExceptionHandler.log_exception(e)
    
    def _scan_worker(self):
        """扫描工作线程"""
        while self.running:
            try:
                # 使用超时获取，以便能够及时响应停止信号
                try:
                    file_path = self.file_queue.get(timeout=0.1)
                except queue.Empty:
                    continue
                
                if file_path is None:
                    break
                
                # 断点续扫：跳过已经扫描过的文件
                if self.resume_scan and file_path in self.scanned_files:
                    continue
                
                # 安全获取文件信息
                file_size = ExceptionHandler.safe_file_size(file_path)
                file_mtime = ExceptionHandler.safe_file_mtime(file_path)
                
                if file_size is not None and file_mtime is not None:
                    # 增量扫描：只扫描修改时间大于last_scan_time的文件
                    if self.last_scan_time > 0 and file_mtime <= self.last_scan_time:
                        continue
                    
                    file_info = {
                        'name': os.path.basename(file_path),
                        'path': file_path,
                        'size': file_size,
                        'mtime': file_mtime
                    }
                    
                    with self.lock:
                        self.results.append(file_info)
                        self.found_files += 1
                        self.scanned_files.add(file_path)  # 记录已扫描的文件
                    
                    # 调用回调函数
                    if self.file_found_callback:
                        self.file_found_callback(file_info)
                    
                    # 更新进度
                    if self.progress_callback:
                        elapsed = time.time() - self.start_time
                        # 由于我们移除了文件计数步骤，使用已找到的文件数作为进度指标
                        progress = min(99, self.found_files // 100)  # 简单的进度估算
                        self.progress_callback(progress, self.found_files, f"{elapsed:.2f}s")
            except Exception as e:
                ExceptionHandler.log_exception(e)
    
    def stop(self):
        """停止扫描"""
        self.running = False
        # 清空文件队列，让所有线程能够退出循环
        while not self.file_queue.empty():
            try:
                self.file_queue.get_nowait()
            except queue.Empty:
                break
        # 向队列中添加足够的None值，确保所有线程都能退出循环
        for _ in range(self.thread_count):
            try:
                self.file_queue.put(None, block=False)
            except queue.Full:
                continue
