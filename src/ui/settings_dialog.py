from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QTabWidget, QWidget, QGroupBox,
    QLabel, QComboBox, QPushButton, QSlider, QCheckBox, QSpinBox,
    QLineEdit, QColorDialog
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor
import json
import os

class SettingsDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("设置")
        self.setGeometry(300, 200, 600, 400)
        
        # 设置文件路径
        self.settings_file = os.path.join(os.path.expanduser("~"), ".mediafinder_settings.json")
        
        # 加载设置
        self.settings = self.load_settings()
        
        # 初始化UI
        self.init_ui()
    
    def init_ui(self):
        # 设置对话框样式
        self.setStyleSheet("""
            QDialog {
                background-color: #1E1E1E;
                color: #FFFFFF;
            }
            QGroupBox {
                background-color: #252526;
                border: 1px solid #3E3E42;
                border-radius: 4px;
                margin-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 3px 0 3px;
                color: #CCCCCC;
            }
            QLabel {
                color: #CCCCCC;
            }
            QComboBox {
                background-color: #3C3C3C;
                color: #FFFFFF;
                border: 1px solid #3E3E42;
                padding: 6px;
                border-radius: 4px;
            }
            QPushButton {
                background-color: #0E639C;
                color: #FFFFFF;
                border: none;
                padding: 6px 12px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #1177BB;
            }
            QPushButton:disabled {
                background-color: #3E3E42;
                color: #888888;
            }
            QSpinBox {
                background-color: #3C3C3C;
                color: #FFFFFF;
                border: 1px solid #3E3E42;
                padding: 6px;
                border-radius: 4px;
            }
            QSlider {
                background-color: #3C3C3C;
                border-radius: 4px;
            }
            QSlider::handle {
                background-color: #0E639C;
                width: 16px;
                height: 16px;
                border-radius: 8px;
            }
            QSlider::groove {
                background-color: #252526;
                height: 6px;
                border-radius: 3px;
            }
            QCheckBox {
                color: #CCCCCC;
            }
            QTabWidget::tab-bar {
                alignment: left;
            }
            QTabWidget::tab {
                background-color: #252526;
                color: #CCCCCC;
                padding: 8px 16px;
                border: 1px solid #3E3E42;
                border-bottom: none;
                border-top-left-radius: 4px;
                border-top-right-radius: 4px;
            }
            QTabWidget::tab:selected {
                background-color: #0E639C;
                color: #FFFFFF;
            }
            QTabWidget::pane {
                background-color: #1E1E1E;
                border: 1px solid #3E3E42;
                border-top: none;
            }
        """)
        
        layout = QVBoxLayout(self)
        
        # 标签页
        self.tab_widget = QTabWidget()
        
        # 界面设置
        interface_tab = QWidget()
        interface_layout = QVBoxLayout(interface_tab)
        interface_layout.setContentsMargins(10, 10, 10, 10)
        interface_layout.setSpacing(10)
        
        # 主题设置
        theme_group = QGroupBox("主题设置")
        theme_layout = QHBoxLayout()
        theme_layout.setContentsMargins(10, 10, 10, 10)
        
        theme_label = QLabel("主题:")
        theme_layout.addWidget(theme_label)
        
        self.theme_combo = QComboBox()
        self.theme_combo.addItems(["浅色", "深色", "系统默认"])
        self.theme_combo.setCurrentText(self.settings.get("theme", "浅色"))
        theme_layout.addWidget(self.theme_combo)
        
        theme_group.setLayout(theme_layout)
        interface_layout.addWidget(theme_group)
        
        # 界面颜色
        color_group = QGroupBox("界面颜色")
        color_layout = QHBoxLayout()
        color_layout.setContentsMargins(10, 10, 10, 10)
        
        self.bg_color_btn = QPushButton("背景颜色")
        self.bg_color_btn.setStyleSheet(f"background-color: {self.settings.get('bg_color', '#FFFFFF')}")
        self.bg_color_btn.clicked.connect(self.select_bg_color)
        color_layout.addWidget(self.bg_color_btn)
        
        self.text_color_btn = QPushButton("文本颜色")
        self.text_color_btn.setStyleSheet(f"background-color: {self.settings.get('text_color', '#000000')}")
        self.text_color_btn.clicked.connect(self.select_text_color)
        color_layout.addWidget(self.text_color_btn)
        
        color_group.setLayout(color_layout)
        interface_layout.addWidget(color_group)
        
        # 字体大小
        font_group = QGroupBox("字体设置")
        font_layout = QHBoxLayout()
        font_layout.setContentsMargins(10, 10, 10, 10)
        
        font_size_label = QLabel("字体大小:")
        font_layout.addWidget(font_size_label)
        
        self.font_size_spin = QSpinBox()
        self.font_size_spin.setRange(8, 24)
        self.font_size_spin.setValue(self.settings.get("font_size", 12))
        font_layout.addWidget(self.font_size_spin)
        
        font_group.setLayout(font_layout)
        interface_layout.addWidget(font_group)
        
        # 扫描设置
        scan_tab = QWidget()
        scan_layout = QVBoxLayout(scan_tab)
        scan_layout.setContentsMargins(10, 10, 10, 10)
        scan_layout.setSpacing(10)
        
        # 扫描深度
        depth_group = QGroupBox("扫描设置")
        depth_layout = QHBoxLayout()
        depth_layout.setContentsMargins(10, 10, 10, 10)
        
        depth_label = QLabel("扫描深度:")
        depth_layout.addWidget(depth_label)
        
        self.depth_spin = QSpinBox()
        self.depth_spin.setRange(1, 10)
        self.depth_spin.setValue(self.settings.get("scan_depth", 3))
        depth_layout.addWidget(self.depth_spin)
        
        depth_group.setLayout(depth_layout)
        scan_layout.addWidget(depth_group)
        
        # 线程数
        thread_group = QGroupBox("性能设置")
        thread_layout = QHBoxLayout()
        thread_layout.setContentsMargins(10, 10, 10, 10)
        
        thread_label = QLabel("扫描线程数:")
        thread_layout.addWidget(thread_label)
        
        self.thread_spin = QSpinBox()
        self.thread_spin.setRange(1, 8)
        self.thread_spin.setValue(self.settings.get("scan_threads", 2))
        thread_layout.addWidget(self.thread_spin)
        
        thread_group.setLayout(thread_layout)
        scan_layout.addWidget(thread_group)
        
        # 缓存设置
        cache_group = QGroupBox("缓存设置")
        cache_layout = QHBoxLayout()
        cache_layout.setContentsMargins(10, 10, 10, 10)
        
        cache_label = QLabel("缓存大小 (MB):")
        cache_layout.addWidget(cache_label)
        
        self.cache_spin = QSpinBox()
        self.cache_spin.setRange(100, 1000)
        self.cache_spin.setValue(self.settings.get("cache_size", 500))
        cache_layout.addWidget(self.cache_spin)
        
        cache_group.setLayout(cache_layout)
        scan_layout.addWidget(cache_group)
        
        # 播放设置
        play_tab = QWidget()
        play_layout = QVBoxLayout(play_tab)
        play_layout.setContentsMargins(10, 10, 10, 10)
        play_layout.setSpacing(10)
        
        # 视频设置
        video_group = QGroupBox("视频设置")
        video_layout = QVBoxLayout()
        video_layout.setContentsMargins(10, 10, 10, 10)
        
        # 自动播放
        self.auto_play_check = QCheckBox("自动播放视频")
        self.auto_play_check.setChecked(self.settings.get("auto_play", False))
        video_layout.addWidget(self.auto_play_check)
        
        # 音量
        volume_layout = QHBoxLayout()
        volume_label = QLabel("默认音量:")
        volume_layout.addWidget(volume_label)
        
        self.volume_slider = QSlider(Qt.Orientation.Horizontal)
        self.volume_slider.setRange(0, 100)
        self.volume_slider.setValue(self.settings.get("default_volume", 50))
        volume_layout.addWidget(self.volume_slider)
        
        video_layout.addLayout(volume_layout)
        video_group.setLayout(video_layout)
        play_layout.addWidget(video_group)
        
        # 图片设置
        image_group = QGroupBox("图片设置")
        image_layout = QVBoxLayout()
        image_layout.setContentsMargins(10, 10, 10, 10)
        
        # 缩略图大小
        thumb_layout = QHBoxLayout()
        thumb_label = QLabel("缩略图大小:")
        thumb_layout.addWidget(thumb_label)
        
        self.thumb_spin = QSpinBox()
        self.thumb_spin.setRange(80, 200)
        self.thumb_spin.setValue(self.settings.get("thumbnail_size", 120))
        thumb_layout.addWidget(self.thumb_spin)
        
        image_layout.addLayout(thumb_layout)
        image_group.setLayout(image_layout)
        play_layout.addWidget(image_group)
        
        # 添加标签页
        self.tab_widget.addTab(interface_tab, "界面设置")
        self.tab_widget.addTab(scan_tab, "扫描设置")
        self.tab_widget.addTab(play_tab, "播放设置")
        layout.addWidget(self.tab_widget)
        
        # 按钮
        button_layout = QHBoxLayout()
        button_layout.setContentsMargins(10, 10, 10, 10)
        button_layout.setSpacing(10)
        
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
    
    def load_settings(self):
        """加载设置"""
        default_settings = {
            "theme": "浅色",
            "bg_color": "#FFFFFF",
            "text_color": "#000000",
            "font_size": 12,
            "scan_depth": 3,
            "scan_threads": 2,
            "cache_size": 500,
            "auto_play": False,
            "default_volume": 50,
            "thumbnail_size": 120
        }
        
        try:
            if os.path.exists(self.settings_file):
                with open(self.settings_file, 'r', encoding='utf-8') as f:
                    settings = json.load(f)
                    # 合并默认设置和用户设置
                    for key, value in default_settings.items():
                        if key not in settings:
                            settings[key] = value
                    return settings
        except Exception as e:
            print(f"加载设置失败: {e}")
        
        return default_settings
    
    def save_settings(self):
        """保存设置"""
        try:
            with open(self.settings_file, 'w', encoding='utf-8') as f:
                json.dump(self.settings, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"保存设置失败: {e}")
    
    def apply_settings(self):
        """应用设置"""
        self.settings["theme"] = self.theme_combo.currentText()
        self.settings["font_size"] = self.font_size_spin.value()
        self.settings["scan_depth"] = self.depth_spin.value()
        self.settings["scan_threads"] = self.thread_spin.value()
        self.settings["cache_size"] = self.cache_spin.value()
        self.settings["auto_play"] = self.auto_play_check.isChecked()
        self.settings["default_volume"] = self.volume_slider.value()
        self.settings["thumbnail_size"] = self.thumb_spin.value()
        
        self.save_settings()
        self.accept()
    
    def set_default(self):
        """恢复默认设置"""
        default_settings = {
            "theme": "浅色",
            "bg_color": "#FFFFFF",
            "text_color": "#000000",
            "font_size": 12,
            "scan_depth": 3,
            "scan_threads": 2,
            "cache_size": 500,
            "auto_play": False,
            "default_volume": 50,
            "thumbnail_size": 120
        }
        
        self.theme_combo.setCurrentText(default_settings["theme"])
        self.bg_color_btn.setStyleSheet(f"background-color: {default_settings['bg_color']}")
        self.text_color_btn.setStyleSheet(f"background-color: {default_settings['text_color']}")
        self.font_size_spin.setValue(default_settings["font_size"])
        self.depth_spin.setValue(default_settings["scan_depth"])
        self.thread_spin.setValue(default_settings["scan_threads"])
        self.cache_spin.setValue(default_settings["cache_size"])
        self.auto_play_check.setChecked(default_settings["auto_play"])
        self.volume_slider.setValue(default_settings["default_volume"])
        self.thumb_spin.setValue(default_settings["thumbnail_size"])
        
        self.settings = default_settings
    
    def select_bg_color(self):
        """选择背景颜色"""
        color = QColorDialog.getColor(QColor(self.settings.get("bg_color", "#FFFFFF")), self, "选择背景颜色")
        if color.isValid():
            self.settings["bg_color"] = color.name()
            self.bg_color_btn.setStyleSheet(f"background-color: {color.name()}")
    
    def select_text_color(self):
        """选择文本颜色"""
        color = QColorDialog.getColor(QColor(self.settings.get("text_color", "#000000")), self, "选择文本颜色")
        if color.isValid():
            self.settings["text_color"] = color.name()
            self.text_color_btn.setStyleSheet(f"background-color: {color.name()}")
    
    def get_settings(self):
        """获取设置"""
        return self.settings
