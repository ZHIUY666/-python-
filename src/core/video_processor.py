import os
import cv2
import tempfile
from typing import Optional, Dict

class VideoProcessor:
    """视频处理类，用于提取视频帧作为封面"""
    
    @staticmethod
    def extract_first_frame(video_path: str) -> Optional[str]:
        """提取视频的第一帧
        
        Args:
            video_path: 视频文件路径
            
        Returns:
            提取的帧的临时文件路径，如果失败则返回None
        """
        try:
            # 打开视频文件
            cap = cv2.VideoCapture(video_path)
            
            if not cap.isOpened():
                return None
            
            # 读取第一帧
            ret, frame = cap.read()
            cap.release()
            
            if not ret:
                return None
            
            # 创建临时文件
            with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as temp_file:
                temp_path = temp_file.name
            
            # 保存帧为JPG文件
            cv2.imwrite(temp_path, frame)
            
            return temp_path
        except Exception as e:
            print(f"提取视频帧失败: {e}")
            return None
    
    @staticmethod
    def get_video_cover(video_path: str) -> Optional[str]:
        """获取视频的封面（第一帧）
        
        Args:
            video_path: 视频文件路径
            
        Returns:
            封面图片路径，如果失败则返回None
        """
        return VideoProcessor.extract_first_frame(video_path)
