import os
import time
import argparse
import json

class MediaScanner:
    def __init__(self, path, file_types):
        self.path = path
        self.file_types = file_types
        self.results = []
        self.running = True
    
    def scan(self):
        start_time = time.time()
        found_files = 0
        total_files = 0
        
        # 先计算总文件数
        for root, dirs, files in os.walk(self.path):
            if not self.running:
                return
            for file in files:
                if any(file.lower().endswith(ext) for ext in self.file_types):
                    total_files += 1
        
        # 再次遍历并处理文件
        for root, dirs, files in os.walk(self.path):
            if not self.running:
                return
            for file in files:
                if any(file.lower().endswith(ext) for ext in self.file_types):
                    found_files += 1
                    file_path = os.path.join(root, file)
                    file_info = {
                        'name': file,
                        'path': file_path,
                        'size': os.path.getsize(file_path),
                        'mtime': os.path.getmtime(file_path)
                    }
                    self.results.append(file_info)
                    
                    # 每找到10个文件显示一次进度
                    if found_files % 10 == 0:
                        elapsed = time.time() - start_time
                        progress = int((found_files / total_files) * 100) if total_files > 0 else 0
                        print(f"扫描中... {progress}% - 已找到 {found_files} 个文件 - 耗时: {elapsed:.2f}s")
        
        elapsed = time.time() - start_time
        print(f"扫描完成 - 共找到 {found_files} 个文件 - 耗时: {elapsed:.2f}s")
        return self.results
    
    def stop(self):
        self.running = False

class MediaManager:
    def __init__(self):
        # 支持的媒体格式
        self.image_formats = ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.webp']
        self.video_formats = ['.mp4', '.avi', '.mov', '.wmv', '.flv', '.mkv', '.webm']
        self.all_formats = self.image_formats + self.video_formats
        
        # 历史记录文件路径
        self.history_file = os.path.join(os.path.expanduser("~"), ".mediafinder_history.json")
        
        # 加载历史记录
        self.history_records = self.load_history()
    
    def load_history(self):
        """加载历史记录"""
        try:
            if os.path.exists(self.history_file):
                with open(self.history_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except Exception as e:
            print(f"加载历史记录失败: {e}")
        return []
    
    def save_history(self):
        """保存历史记录"""
        try:
            with open(self.history_file, 'w', encoding='utf-8') as f:
                json.dump(self.history_records, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"保存历史记录失败: {e}")
    
    def add_history_record(self, path, status, file_count, elapsed):
        """添加历史记录"""
        record = {
            "timestamp": time.time(),
            "path": path,
            "status": status,
            "file_count": file_count,
            "elapsed": elapsed
        }
        self.history_records.insert(0, record)  # 添加到开头
        # 只保留最近100条记录
        if len(self.history_records) > 100:
            self.history_records = self.history_records[:100]
        self.save_history()
    
    def scan(self, path, file_type="all"):
        """扫描媒体文件"""
        # 根据选择的文件类型确定要扫描的格式
        if file_type == "all":
            file_types = self.all_formats
        elif file_type == "image":
            file_types = self.image_formats
        else:
            file_types = self.video_formats
        
        start_time = time.time()
        print(f"开始扫描路径: {path}")
        print(f"扫描类型: {file_type}")
        
        # 创建并启动扫描器
        scanner = MediaScanner(path, file_types)
        results = scanner.scan()
        
        # 添加到历史记录
        elapsed = time.time() - start_time
        self.add_history_record(path, "完成", len(results), f"{elapsed:.2f}s")
        
        return results
    
    def list_results(self, results, sort_by="name"):
        """列出扫描结果"""
        if not results:
            print("没有找到媒体文件")
            return
        
        # 排序
        if sort_by == "name":
            results.sort(key=lambda x: x['name'].lower())
        elif sort_by == "size":
            results.sort(key=lambda x: x['size'], reverse=True)
        elif sort_by == "mtime":
            results.sort(key=lambda x: x['mtime'], reverse=True)
        
        print("\n扫描结果:")
        print("-" * 80)
        for i, file_info in enumerate(results, 1):
            size = f"{file_info['size'] / 1024:.2f} KB"
            mtime = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(file_info['mtime']))
            print(f"{i}. {file_info['name']}")
            print(f"   路径: {file_info['path']}")
            print(f"   大小: {size}")
            print(f"   修改时间: {mtime}")
            print("-" * 80)
    
    def show_history(self):
        """显示历史记录"""
        if not self.history_records:
            print("没有历史记录")
            return
        
        print("\n扫描历史记录:")
        print("-" * 80)
        for i, record in enumerate(self.history_records, 1):
            timestamp = record.get("timestamp", 0)
            time_str = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(timestamp))
            path = record.get("path", "")
            status = record.get("status", "")
            file_count = record.get("file_count", 0)
            elapsed = record.get("elapsed", "0s")
            
            print(f"{i}. 时间: {time_str}")
            print(f"   路径: {path}")
            print(f"   状态: {status}")
            print(f"   文件数: {file_count}")
            print(f"   耗时: {elapsed}")
            print("-" * 80)

def main():
    parser = argparse.ArgumentParser(description="媒体文件管理器")
    parser.add_argument("--scan", metavar="PATH", help="扫描指定路径")
    parser.add_argument("--type", choices=["all", "image", "video"], default="all", help="扫描类型")
    parser.add_argument("--sort", choices=["name", "size", "mtime"], default="name", help="排序方式")
    parser.add_argument("--history", action="store_true", help="显示历史记录")
    
    args = parser.parse_args()
    
    manager = MediaManager()
    
    if args.history:
        manager.show_history()
    elif args.scan:
        path = args.scan
        if not os.path.exists(path):
            print(f"路径不存在: {path}")
            return
        
        results = manager.scan(path, args.type)
        manager.list_results(results, args.sort)
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
