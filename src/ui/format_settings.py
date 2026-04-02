from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QGroupBox, QCheckBox, QPushButton,
    QTabWidget, QWidget, QLabel, QGridLayout
)
from PyQt6.QtCore import Qt

class FormatSettingsDialog(QDialog):
    def __init__(self, parent=None, image_formats=None, video_formats=None):
        super().__init__(parent)
        self.setWindowTitle("格式设置")
        self.setGeometry(300, 200, 400, 300)
        
        # 存储当前格式设置
        self.image_formats = image_formats or ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.webp']
        self.video_formats = video_formats or ['.mp4', '.avi', '.mov', '.wmv', '.flv', '.mkv', '.webm']
        
        # 所有支持的格式
        self.all_image_formats = ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.webp']
        self.all_video_formats = ['.mp4', '.avi', '.mov', '.wmv', '.flv', '.mkv', '.webm']
        
        # 初始化UI
        self.init_ui()
    
    def init_ui(self):
        layout = QVBoxLayout(self)
        
        # 标签页
        self.tab_widget = QTabWidget()
        
        # 图片格式标签页
        image_tab = QWidget()
        image_layout = QVBoxLayout(image_tab)
        
        image_group = QGroupBox("图片格式")
        image_grid = QGridLayout()
        
        self.image_checkboxes = {}
        row = 0
        col = 0
        for fmt in self.all_image_formats:
            checkbox = QCheckBox(fmt)
            checkbox.setChecked(fmt in self.image_formats)
            self.image_checkboxes[fmt] = checkbox
            image_grid.addWidget(checkbox, row, col)
            col += 1
            if col >= 3:
                col = 0
                row += 1
        
        image_group.setLayout(image_grid)
        image_layout.addWidget(image_group)
        
        # 视频格式标签页
        video_tab = QWidget()
        video_layout = QVBoxLayout(video_tab)
        
        video_group = QGroupBox("视频格式")
        video_grid = QGridLayout()
        
        self.video_checkboxes = {}
        row = 0
        col = 0
        for fmt in self.all_video_formats:
            checkbox = QCheckBox(fmt)
            checkbox.setChecked(fmt in self.video_formats)
            self.video_checkboxes[fmt] = checkbox
            video_grid.addWidget(checkbox, row, col)
            col += 1
            if col >= 3:
                col = 0
                row += 1
        
        video_group.setLayout(video_grid)
        video_layout.addWidget(video_group)
        
        # 添加标签页
        self.tab_widget.addTab(image_tab, "图片")
        self.tab_widget.addTab(video_tab, "视频")
        layout.addWidget(self.tab_widget)
        
        # 按钮
        button_layout = QHBoxLayout()
        
        apply_btn = QPushButton("应用")
        apply_btn.clicked.connect(self.apply_settings)
        button_layout.addWidget(apply_btn)
        
        cancel_btn = QPushButton("取消")
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)
        
        default_btn = QPushButton("默认")
        default_btn.clicked.connect(self.set_default)
        button_layout.addWidget(default_btn)
        
        layout.addLayout(button_layout)
    
    def apply_settings(self):
        # 保存当前设置
        self.image_formats = [fmt for fmt, checkbox in self.image_checkboxes.items() if checkbox.isChecked()]
        self.video_formats = [fmt for fmt, checkbox in self.video_checkboxes.items() if checkbox.isChecked()]
        self.accept()
    
    def set_default(self):
        # 恢复默认设置
        default_image_formats = ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.webp']
        default_video_formats = ['.mp4', '.avi', '.mov', '.wmv', '.flv', '.mkv', '.webm']
        
        for fmt, checkbox in self.image_checkboxes.items():
            checkbox.setChecked(fmt in default_image_formats)
        
        for fmt, checkbox in self.video_checkboxes.items():
            checkbox.setChecked(fmt in default_video_formats)
    
    def get_settings(self):
        return self.image_formats, self.video_formats
