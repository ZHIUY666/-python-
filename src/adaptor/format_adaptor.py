from typing import Optional, Dict, List
import os
from PIL import Image, UnidentifiedImageError
import subprocess
import tempfile

class FormatAdaptor:
    """全格式解码适配类，处理图片和视频的解码和预览"""
    
    # 支持的图片格式
    SUPPORTED_IMAGE_FORMATS = [
        '.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.webp',
        '.raw', '.heic', '.psd', '.ai', '.svg', '.ico', '.cur',
        '.ppm', '.pgm', '.pbm', '.pnm', '.exr', '.hdr', '.tif'
    ]
    
    # 支持的视频格式
    SUPPORTED_VIDEO_FORMATS = [
        '.mp4', '.avi', '.mov', '.wmv', '.flv', '.mkv', '.webm',
        '.m4v', '.ts', '.rmvb', '.3gp', '.mpeg', '.mpg', '.vob',
        '.asf', '.mts', '.m2ts', '.divx', '.xvid', '.wmv', '.ogv'
    ]
    
    @staticmethod
    def is_image_file(file_path: str) -> bool:
        """判断是否为图片文件"""
        ext = os.path.splitext(file_path)[1].lower()
        return ext in FormatAdaptor.SUPPORTED_IMAGE_FORMATS
    
    @staticmethod
    def is_video_file(file_path: str) -> bool:
        """判断是否为视频文件"""
        ext = os.path.splitext(file_path)[1].lower()
        return ext in FormatAdaptor.SUPPORTED_VIDEO_FORMATS
    
    @staticmethod
    def get_file_type(file_path: str) -> str:
        """获取文件类型"""
        if FormatAdaptor.is_image_file(file_path):
            return "image"
        elif FormatAdaptor.is_video_file(file_path):
            return "video"
        return "unknown"
    
    @staticmethod
    def can_handle_file(file_path: str) -> bool:
        """判断是否能处理文件"""
        return FormatAdaptor.is_image_file(file_path) or FormatAdaptor.is_video_file(file_path)
    
    @staticmethod
    def get_image_size(file_path: str) -> Optional[tuple]:
        """获取图片尺寸"""
        try:
            with Image.open(file_path) as img:
                return img.size
        except Exception:
            return None
    
    @staticmethod
    def generate_thumbnail(file_path: str, size: tuple = (128, 128)) -> Optional[str]:
        """生成缩略图"""
        try:
            if FormatAdaptor.is_image_file(file_path):
                return FormatAdaptor._generate_image_thumbnail(file_path, size)
            elif FormatAdaptor.is_video_file(file_path):
                return FormatAdaptor._generate_video_thumbnail(file_path, size)
        except Exception:
            pass
        return None
    
    @staticmethod
    def _generate_image_thumbnail(file_path: str, size: tuple) -> Optional[str]:
        """生成图片缩略图"""
        try:
            with Image.open(file_path) as img:
                img.thumbnail(size, Image.LANCZOS)
                temp_file = tempfile.NamedTemporaryFile(suffix='.png', delete=False)
                img.save(temp_file.name, 'PNG')
                temp_file.close()
                return temp_file.name
        except Exception:
            return None
    
    @staticmethod
    def _generate_video_thumbnail(file_path: str, size: tuple) -> Optional[str]:
        """生成视频缩略图"""
        try:
            # 尝试使用ffmpeg生成视频缩略图
            temp_file = tempfile.NamedTemporaryFile(suffix='.png', delete=False)
            temp_file.close()
            
            # 构建ffmpeg命令
            cmd = [
                'ffmpeg', '-i', file_path, '-ss', '00:00:01',
                '-vframes', '1', '-s', f'{size[0]}x{size[1]}',
                '-f', 'image2', '-y', temp_file.name
            ]
            
            # 执行命令
            subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=10)
            
            # 检查文件是否生成
            if os.path.exists(temp_file.name) and os.path.getsize(temp_file.name) > 0:
                return temp_file.name
            else:
                os.unlink(temp_file.name)
                return None
        except Exception:
            return None
    
    @staticmethod
    def get_image_exif(file_path: str) -> Optional[Dict]:
        """获取图片EXIF信息"""
        try:
            from PIL.ExifTags import TAGS
            with Image.open(file_path) as img:
                exif_data = img.getexif()
                if exif_data:
                    exif = {}
                    for tag, value in exif_data.items():
                        tag_name = TAGS.get(tag, tag)
                        exif[tag_name] = value
                    return exif
        except Exception:
            pass
        return None
    
    @staticmethod
    def get_video_info(file_path: str) -> Optional[Dict]:
        """获取视频信息"""
        try:
            # 尝试使用ffprobe获取视频信息
            cmd = [
                'ffprobe', '-v', 'quiet', '-print_format', 'json',
                '-show_format', '-show_streams', file_path
            ]
            
            # 执行命令
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
            
            # 解析结果
            if result.returncode == 0:
                import json
                return json.loads(result.stdout)
        except Exception:
            pass
        return None
    
    @staticmethod
    def rotate_image(file_path: str, angle: int) -> Optional[str]:
        """旋转图片"""
        try:
            with Image.open(file_path) as img:
                rotated = img.rotate(angle, expand=True)
                temp_file = tempfile.NamedTemporaryFile(suffix='.png', delete=False)
                rotated.save(temp_file.name, 'PNG')
                temp_file.close()
                return temp_file.name
        except Exception:
            return None
    
    @staticmethod
    def resize_image(file_path: str, size: tuple) -> Optional[str]:
        """调整图片大小"""
        try:
            with Image.open(file_path) as img:
                resized = img.resize(size, Image.LANCZOS)
                temp_file = tempfile.NamedTemporaryFile(suffix='.png', delete=False)
                resized.save(temp_file.name, 'PNG')
                temp_file.close()
                return temp_file.name
        except Exception:
            return None
    
    @staticmethod
    def convert_image_format(file_path: str, output_format: str) -> Optional[str]:
        """转换图片格式"""
        try:
            with Image.open(file_path) as img:
                temp_file = tempfile.NamedTemporaryFile(suffix=f'.{output_format.lower()}', delete=False)
                img.save(temp_file.name, output_format.upper())
                temp_file.close()
                return temp_file.name
        except Exception:
            return None
    
    @staticmethod
    def get_supported_formats() -> Dict[str, List[str]]:
        """获取支持的格式列表"""
        return {
            "image": FormatAdaptor.SUPPORTED_IMAGE_FORMATS,
            "video": FormatAdaptor.SUPPORTED_VIDEO_FORMATS
        }
    
    @staticmethod
    def is_format_supported(file_path: str) -> bool:
        """判断格式是否支持"""
        ext = os.path.splitext(file_path)[1].lower()
        return ext in FormatAdaptor.SUPPORTED_IMAGE_FORMATS or ext in FormatAdaptor.SUPPORTED_VIDEO_FORMATS
    
    @staticmethod
    def get_format_description(file_ext: str) -> str:
        """获取格式描述"""
        format_descriptions = {
            # 图片格式
            '.jpg': 'JPEG Image',
            '.jpeg': 'JPEG Image',
            '.png': 'PNG Image',
            '.gif': 'GIF Image',
            '.bmp': 'Bitmap Image',
            '.tiff': 'TIFF Image',
            '.webp': 'WebP Image',
            '.raw': 'Raw Image',
            '.heic': 'HEIC Image',
            '.psd': 'Photoshop Document',
            '.ai': 'Adobe Illustrator Document',
            '.svg': 'SVG Vector Image',
            '.ico': 'Icon File',
            '.cur': 'Cursor File',
            '.ppm': 'PPM Image',
            '.pgm': 'PGM Image',
            '.pbm': 'PBM Image',
            '.pnm': 'PNM Image',
            '.exr': 'EXR Image',
            '.hdr': 'HDR Image',
            '.tif': 'TIFF Image',
            # 视频格式
            '.mp4': 'MP4 Video',
            '.avi': 'AVI Video',
            '.mov': 'MOV Video',
            '.wmv': 'WMV Video',
            '.flv': 'FLV Video',
            '.mkv': 'MKV Video',
            '.webm': 'WebM Video',
            '.m4v': 'M4V Video',
            '.ts': 'TS Video',
            '.rmvb': 'RMVB Video',
            '.3gp': '3GP Video',
            '.mpeg': 'MPEG Video',
            '.mpg': 'MPEG Video',
            '.vob': 'VOB Video',
            '.asf': 'ASF Video',
            '.mts': 'MTS Video',
            '.m2ts': 'M2TS Video',
            '.divx': 'DivX Video',
            '.xvid': 'XviD Video',
            '.ogv': 'OGV Video'
        }
        return format_descriptions.get(file_ext.lower(), 'Unknown Format')
