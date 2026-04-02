import sqlite3
import json
import os
from typing import List, Dict, Optional
import time

class DataStorage:
    def __init__(self, db_path: str = None):
        if db_path is None:
            # 默认数据库路径
            self.db_path = os.path.join(os.path.expanduser("~"), ".mediafinder.db")
        else:
            self.db_path = db_path
        
        self._init_database()
    
    def _init_database(self):
        """初始化数据库"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # 创建媒体文件表
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS media_files (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            file_id TEXT UNIQUE,
            file_name TEXT,
            file_path TEXT,
            file_type TEXT,
            file_ext TEXT,
            file_size INTEGER,
            modify_time REAL,
            is_collected INTEGER DEFAULT 0,
            scan_id INTEGER,
            FOREIGN KEY (scan_id) REFERENCES scan_records(id)
        )
        ''')
        
        # 创建扫描记录表
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS scan_records (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            scan_time REAL,
            scan_path TEXT,
            file_total INTEGER,
            scan_duration TEXT,
            scan_status TEXT
        )
        ''')
        
        # 创建格式配置表
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS format_configs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            format_type TEXT,
            format_ext TEXT,
            is_enabled INTEGER DEFAULT 1,
            is_custom INTEGER DEFAULT 0,
            UNIQUE(format_type, format_ext)
        )
        ''')
        
        # 创建用户配置表
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS user_configs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            config_key TEXT UNIQUE,
            config_value TEXT,
            config_group TEXT
        )
        ''')
        
        # 创建收藏夹表
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS collections (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE,
            description TEXT,
            create_time REAL
        )
        ''')
        
        # 创建收藏文件关联表
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS collection_files (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            collection_id INTEGER,
            file_id TEXT,
            add_time REAL,
            FOREIGN KEY (collection_id) REFERENCES collections(id),
            FOREIGN KEY (file_id) REFERENCES media_files(file_id),
            UNIQUE(collection_id, file_id)
        )
        ''')
        
        conn.commit()
        conn.close()
        
        # 初始化默认格式配置
        self._init_default_formats()
    
    def _init_default_formats(self):
        """初始化默认格式配置"""
        default_formats = [
            # 图片格式
            ("image", ".jpg", 1, 0),
            ("image", ".jpeg", 1, 0),
            ("image", ".png", 1, 0),
            ("image", ".gif", 1, 0),
            ("image", ".bmp", 1, 0),
            ("image", ".tiff", 1, 0),
            ("image", ".webp", 1, 0),
            ("image", ".raw", 1, 0),
            ("image", ".heic", 1, 0),
            ("image", ".psd", 1, 0),
            ("image", ".ai", 1, 0),
            # 视频格式
            ("video", ".mp4", 1, 0),
            ("video", ".mkv", 1, 0),
            ("video", ".mov", 1, 0),
            ("video", ".avi", 1, 0),
            ("video", ".flv", 1, 0),
            ("video", ".wmv", 1, 0),
            ("video", ".rmvb", 1, 0),
            ("video", ".webm", 1, 0),
            ("video", ".m4v", 1, 0),
            ("video", ".ts", 1, 0),
        ]
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        for fmt_type, fmt_ext, is_enabled, is_custom in default_formats:
            try:
                cursor.execute(
                    "INSERT OR IGNORE INTO format_configs (format_type, format_ext, is_enabled, is_custom) VALUES (?, ?, ?, ?)",
                    (fmt_type, fmt_ext, is_enabled, is_custom)
                )
            except Exception as e:
                print(f"添加默认格式失败: {e}")
        
        conn.commit()
        conn.close()
    
    def save_scan_record(self, scan_path: str, file_total: int, scan_duration: str, scan_status: str) -> int:
        """保存扫描记录"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute(
            "INSERT INTO scan_records (scan_time, scan_path, file_total, scan_duration, scan_status) VALUES (?, ?, ?, ?, ?)",
            (time.time(), scan_path, file_total, scan_duration, scan_status)
        )
        
        scan_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        return scan_id
    
    def save_media_files(self, files: List[Dict], scan_id: int):
        """保存媒体文件信息"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        for file_info in files:
            try:
                # 生成file_id（使用文件路径的MD5）
                import hashlib
                file_id = hashlib.md5(file_info['path'].encode()).hexdigest()
                
                # 确定文件类型和扩展名
                file_ext = os.path.splitext(file_info['name'])[1].lower()
                file_type = "image" if file_ext in ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.webp', '.raw', '.heic', '.psd', '.ai'] else "video"
                
                cursor.execute(
                    "INSERT OR REPLACE INTO media_files (file_id, file_name, file_path, file_type, file_ext, file_size, modify_time, is_collected, scan_id) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                    (file_id, file_info['name'], file_info['path'], file_type, file_ext, file_info['size'], file_info['mtime'], 0, scan_id)
                )
            except Exception as e:
                print(f"保存文件信息失败: {e}")
        
        conn.commit()
        conn.close()
    
    def get_scan_records(self) -> List[Dict]:
        """获取扫描记录"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM scan_records ORDER BY scan_time DESC")
        records = cursor.fetchall()
        
        result = []
        for record in records:
            result.append({
                'id': record[0],
                'scan_time': record[1],
                'scan_path': record[2],
                'file_total': record[3],
                'scan_duration': record[4],
                'scan_status': record[5]
            })
        
        conn.close()
        return result
    
    def get_media_files_by_scan_id(self, scan_id: int) -> List[Dict]:
        """根据扫描ID获取媒体文件"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM media_files WHERE scan_id = ?", (scan_id,))
        files = cursor.fetchall()
        
        result = []
        for file in files:
            result.append({
                'id': file[0],
                'file_id': file[1],
                'name': file[2],
                'path': file[3],
                'type': file[4],
                'ext': file[5],
                'size': file[6],
                'mtime': file[7],
                'is_collected': file[8],
                'scan_id': file[9]
            })
        
        conn.close()
        return result
    
    def get_enabled_formats(self) -> List[str]:
        """获取启用的格式"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("SELECT format_ext FROM format_configs WHERE is_enabled = 1")
        formats = cursor.fetchall()
        
        result = [fmt[0] for fmt in formats]
        conn.close()
        return result
    
    def update_format_status(self, format_ext: str, is_enabled: int):
        """更新格式状态"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute(
            "UPDATE format_configs SET is_enabled = ? WHERE format_ext = ?",
            (is_enabled, format_ext)
        )
        
        conn.commit()
        conn.close()
    
    def add_custom_format(self, format_type: str, format_ext: str):
        """添加自定义格式"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute(
                "INSERT OR IGNORE INTO format_configs (format_type, format_ext, is_enabled, is_custom) VALUES (?, ?, 1, 1)",
                (format_type, format_ext)
            )
            conn.commit()
        except Exception as e:
            print(f"添加自定义格式失败: {e}")
            conn.rollback()
        finally:
            conn.close()
    
    def create_collection(self, name: str, description: str = "") -> int:
        """创建收藏夹"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute(
                "INSERT INTO collections (name, description, create_time) VALUES (?, ?, ?)",
                (name, description, time.time())
            )
            collection_id = cursor.lastrowid
            conn.commit()
            return collection_id
        except Exception as e:
            print(f"创建收藏夹失败: {e}")
            conn.rollback()
            return -1
        finally:
            conn.close()
    
    def get_collections(self) -> List[Dict]:
        """获取所有收藏夹"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute("SELECT * FROM collections ORDER BY create_time DESC")
            collections = cursor.fetchall()
            
            result = []
            for collection in collections:
                result.append({
                    'id': collection[0],
                    'name': collection[1],
                    'description': collection[2],
                    'create_time': collection[3]
                })
            return result
        except Exception as e:
            print(f"获取收藏夹失败: {e}")
            return []
        finally:
            conn.close()
    
    def get_collection_files(self, collection_id: int) -> List[Dict]:
        """获取收藏夹中的文件"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute(
                "SELECT mf.* FROM media_files mf JOIN collection_files cf ON mf.file_id = cf.file_id WHERE cf.collection_id = ?",
                (collection_id,)
            )
            files = cursor.fetchall()
            
            result = []
            for file in files:
                # 确保文件路径使用正斜杠，避免反斜杠被转义
                file_path = file[3].replace('\\', '/')
                result.append({
                    'id': file[0],
                    'file_id': file[1],
                    'name': file[2],
                    'path': file_path,
                    'type': file[4],
                    'ext': file[5],
                    'size': file[6],
                    'mtime': file[7],
                    'is_collected': file[8],
                    'scan_id': file[9]
                })
            return result
        except Exception as e:
            print(f"获取收藏夹文件失败: {e}")
            return []
        finally:
            conn.close()
    
    def add_file_to_collection(self, collection_id: int, file_id: str) -> bool:
        """添加文件到收藏夹"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute(
                "INSERT OR IGNORE INTO collection_files (collection_id, file_id, add_time) VALUES (?, ?, ?)",
                (collection_id, file_id, time.time())
            )
            conn.commit()
            return True
        except Exception as e:
            print(f"添加文件到收藏夹失败: {e}")
            conn.rollback()
            return False
        finally:
            conn.close()
    
    def remove_file_from_collection(self, collection_id: int, file_id: str) -> bool:
        """从收藏夹中删除文件"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute(
                "DELETE FROM collection_files WHERE collection_id = ? AND file_id = ?",
                (collection_id, file_id)
            )
            conn.commit()
            return True
        except Exception as e:
            print(f"从收藏夹中删除文件失败: {e}")
            conn.rollback()
            return False
        finally:
            conn.close()
    
    def delete_collection(self, collection_id: int) -> bool:
        """删除收藏夹"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            # 先删除收藏夹中的文件关联
            cursor.execute("DELETE FROM collection_files WHERE collection_id = ?", (collection_id,))
            # 再删除收藏夹
            cursor.execute("DELETE FROM collections WHERE id = ?", (collection_id,))
            conn.commit()
            return True
        except Exception as e:
            print(f"删除收藏夹失败: {e}")
            conn.rollback()
            return False
        finally:
            conn.close()
    
    def save_user_config(self, config_key: str, config_value: str, config_group: str):
        """保存用户配置"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute(
            "INSERT OR REPLACE INTO user_configs (config_key, config_value, config_group) VALUES (?, ?, ?)",
            (config_key, config_value, config_group)
        )
        
        conn.commit()
        conn.close()
    
    def get_user_config(self, config_key: str) -> Optional[str]:
        """获取用户配置"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("SELECT config_value FROM user_configs WHERE config_key = ?", (config_key,))
        result = cursor.fetchone()
        
        conn.close()
        return result[0] if result else None
    
    def get_all_user_configs(self) -> Dict:
        """获取所有用户配置"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("SELECT config_key, config_value, config_group FROM user_configs")
        configs = cursor.fetchall()
        
        result = {}
        for config in configs:
            result[config[0]] = {
                'value': config[1],
                'group': config[2]
            }
        
        conn.close()
        return result
    
    def toggle_collection(self, file_id: str, is_collected: int):
        """切换文件收藏状态"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute(
            "UPDATE media_files SET is_collected = ? WHERE file_id = ?",
            (is_collected, file_id)
        )
        
        conn.commit()
        conn.close()
    
    def get_collected_files(self) -> List[Dict]:
        """获取收藏的文件"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM media_files WHERE is_collected = 1")
        files = cursor.fetchall()
        
        result = []
        for file in files:
            result.append({
                'id': file[0],
                'file_id': file[1],
                'name': file[2],
                'path': file[3],
                'type': file[4],
                'ext': file[5],
                'size': file[6],
                'mtime': file[7],
                'is_collected': file[8],
                'scan_id': file[9]
            })
        
        conn.close()
        return result
    
    def delete_scan_record(self, scan_id: int):
        """删除扫描记录及相关文件"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # 删除相关文件
        cursor.execute("DELETE FROM media_files WHERE scan_id = ?", (scan_id,))
        # 删除扫描记录
        cursor.execute("DELETE FROM scan_records WHERE id = ?", (scan_id,))
        
        conn.commit()
        conn.close()
