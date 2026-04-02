import sys
import os
import time
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QPushButton, QLineEdit, QComboBox, QListWidget, QTreeWidget, QTreeWidgetItem,
    QLabel, QSplitter, QMenu, QFileDialog, QProgressBar, QStatusBar,
    QTabWidget, QCheckBox, QGroupBox, QRadioButton, QButtonGroup, QScrollArea,
    QSizePolicy
)
from PyQt6.QtGui import QIcon, QPixmap, QImage, QTransform, QAction
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QSize, QUrl, QMetaObject, Q_ARG, QObject
from PyQt6.QtMultimedia import QMediaPlayer, QAudioOutput
from PyQt6.QtMultimediaWidgets import QVideoWidget
from src.ui.format_settings import FormatSettingsDialog
from src.ui.history_dialog import HistoryDialog
from src.ui.settings_dialog import SettingsDialog
from src.ui.collection_dialog import CollectionDialog
from src.core.scanner import MultiThreadedMediaScanner
from src.core.video_processor import VideoProcessor
from src.data.storage import DataStorage
from src.utils.file_utils import FileUtils

class MediaScanner(QThread):
    progress_updated = pyqtSignal(int, int, str)  # 进度, 已找到文件数, 耗时
    file_found = pyqtSignal(dict)  # 找到的文件信息
    scan_finished = pyqtSignal()
    scan_stopped = pyqtSignal()
    
    def __init__(self, path, file_types):
        super().__init__()
        self.path = path
        self.file_types = file_types
        self.running = True
        
    def run(self):
        start_time = time.time()
        found_files = 0
        total_files = 0
        
        # 先计算总文件数
        for root, dirs, files in os.walk(self.path):
            if not self.running:
                self.scan_stopped.emit()
                return
            for file in files:
                if any(file.lower().endswith(ext) for ext in self.file_types):
                    total_files += 1
        
        # 再次遍历并处理文件
        for root, dirs, files in os.walk(self.path):
            if not self.running:
                self.scan_stopped.emit()
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
                    self.file_found.emit(file_info)
                    
                    # 更新进度
                    elapsed = time.time() - start_time
                    progress = int((found_files / total_files) * 100) if total_files > 0 else 0
                    self.progress_updated.emit(progress, found_files, f"{elapsed:.2f}s")
        
        self.scan_finished.emit()
    
    def stop(self):
        self.running = False

class MainWindow(QMainWindow):
    # 定义信号用于线程间通信
    progress_updated = pyqtSignal(int, int, str)
    file_found = pyqtSignal(dict)
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("MediaFinder")
        self.setGeometry(100, 100, 1200, 800)
        
        # 支持的媒体格式
        self.image_formats = ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.webp', '.raw', '.heic', '.psd', '.ai']
        self.video_formats = ['.mp4', '.mkv', '.mov', '.avi', '.flv', '.wmv', '.rmvb', '.webm', '.m4v', '.ts']
        self.all_formats = self.image_formats + self.video_formats
        
        # 当前扫描设置
        self.current_path = os.path.expanduser("~")
        self.current_file_type = "all"  # all, image, video
        self.current_view = "grid"  # grid, list
        self.current_sort = "name"  # name, size, mtime
        
        # 扫描结果
        self.scan_results = []
        
        # 网格视图缩放因子（用于Ctrl+滚轮调整图片大小）
        self.grid_scale_factor = 1.0
        self.min_scale_factor = 0.5  # 最小缩放比例
        self.max_scale_factor = 2.0  # 最大缩放比例
        
        # 初始化数据存储
        self.storage = DataStorage()
        
        # 初始化历史记录、设置和收藏夹
        self.history_dialog = HistoryDialog(self)
        self.settings_dialog = SettingsDialog(self)
        self.collection_dialog = CollectionDialog(self)
        
        # 连接信号到槽函数
        self.progress_updated.connect(self._update_progress)
        self.file_found.connect(self._add_file_result)
        
        # 初始化媒体播放器
        self.audio_output = QAudioOutput()
        self.media_player = QMediaPlayer()
        self.media_player.setAudioOutput(self.audio_output)
        self.video_widget = QVideoWidget()
        self.media_player.setVideoOutput(self.video_widget)
        # 设置默认音量
        self.audio_output.setVolume(0.5)
        
        # 初始化UI
        self.init_ui()
        
        # 加载最近的扫描结果
        self.load_recent_scan_results()
    
    def init_ui(self):
        # 设置窗口样式
        self.setStyleSheet("""
            QMainWindow {
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
            QLineEdit {
                background-color: #3C3C3C;
                color: #FFFFFF;
                border: 1px solid #3E3E42;
                padding: 6px;
                border-radius: 4px;
            }
            QComboBox {
                background-color: #3C3C3C;
                color: #FFFFFF;
                border: 1px solid #3E3E42;
                padding: 6px;
                border-radius: 4px;
            }
            QTreeWidget {
                background-color: #1E1E1E;
                color: #FFFFFF;
                border: 1px solid #3E3E42;
            }
            QTreeWidget::item {
                padding: 4px;
            }
            QTreeWidget::item:selected {
                background-color: #0E639C;
            }
            QTreeWidget::header {
                background-color: #252526;
                color: #CCCCCC;
            }
            QStatusBar {
                background-color: #252526;
                color: #CCCCCC;
            }
            QLabel {
                color: #CCCCCC;
            }
            QRadioButton {
                color: #CCCCCC;
            }
        """)
        
        # 主布局
        central_widget = QWidget()
        main_layout = QVBoxLayout(central_widget)
        
        # 顶部核心操作区
        top_layout = QHBoxLayout()
        top_layout.setContentsMargins(10, 10, 10, 10)
        top_layout.setSpacing(10)
        
        # 扫描路径选择
        path_group = QGroupBox("扫描路径")
        path_layout = QHBoxLayout()
        path_layout.setContentsMargins(10, 10, 10, 10)
        self.path_combo = QComboBox()
        self.path_combo.addItems(["常用目录", "全盘扫描", "自定义目录"])
        self.path_combo.currentIndexChanged.connect(self.on_path_change)
        path_layout.addWidget(self.path_combo)
        
        self.path_edit = QLineEdit(self.current_path)
        self.path_edit.setMinimumWidth(300)
        self.path_edit.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        path_layout.addWidget(self.path_edit)
        
        browse_btn = QPushButton("浏览")
        browse_btn.clicked.connect(self.browse_path)
        path_layout.addWidget(browse_btn)
        
        path_group.setLayout(path_layout)
        top_layout.addWidget(path_group, 2)
        
        # 扫描控制
        scan_group = QGroupBox("扫描控制")
        scan_layout = QHBoxLayout()
        scan_layout.setContentsMargins(10, 10, 10, 10)
        self.start_scan_btn = QPushButton("开始扫描")
        self.start_scan_btn.clicked.connect(self.start_scan)
        scan_layout.addWidget(self.start_scan_btn)
        
        self.stop_scan_btn = QPushButton("停止扫描")
        self.stop_scan_btn.clicked.connect(self.stop_scan)
        self.stop_scan_btn.setEnabled(False)
        scan_layout.addWidget(self.stop_scan_btn)
        
        scan_group.setLayout(scan_layout)
        top_layout.addWidget(scan_group, 1)
        
        # 核心筛选
        filter_group = QGroupBox("筛选")
        filter_layout = QHBoxLayout()
        filter_layout.setContentsMargins(10, 10, 10, 10)
        self.format_combo = QComboBox()
        self.format_combo.addItems(["全部", "仅图片", "仅视频"])
        self.format_combo.currentIndexChanged.connect(self.on_format_change)
        filter_layout.addWidget(self.format_combo)
        
        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("关键词搜索")
        self.search_edit.textChanged.connect(self.filter_results)
        self.search_edit.setMinimumWidth(200)
        self.search_edit.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        filter_layout.addWidget(self.search_edit)
        
        filter_group.setLayout(filter_layout)
        top_layout.addWidget(filter_group, 1)
        
        # 功能入口
        action_group = QGroupBox("功能")
        action_layout = QHBoxLayout()
        action_layout.setContentsMargins(10, 10, 10, 10)
        format_setting_btn = QPushButton("格式设置")
        format_setting_btn.clicked.connect(self.open_format_settings)
        action_layout.addWidget(format_setting_btn)
        
        history_btn = QPushButton("历史记录")
        history_btn.clicked.connect(self.open_history)
        action_layout.addWidget(history_btn)
        
        collection_btn = QPushButton("收藏夹")
        collection_btn.clicked.connect(self.open_collection)
        action_layout.addWidget(collection_btn)
        
        setting_btn = QPushButton("设置")
        setting_btn.clicked.connect(self.open_settings)
        action_layout.addWidget(setting_btn)
        
        action_group.setLayout(action_layout)
        top_layout.addWidget(action_group, 1)
        
        main_layout.addLayout(top_layout)
        
        # 中部结果展示区和右侧预览区
        middle_layout = QHBoxLayout()
        middle_layout.setContentsMargins(10, 0, 10, 10)
        middle_layout.setSpacing(10)
        
        # 结果展示区
        result_group = QGroupBox("文件结果")
        result_layout = QVBoxLayout()
        result_layout.setContentsMargins(10, 10, 10, 10)
        
        # 视图切换和排序
        view_sort_layout = QHBoxLayout()
        view_group = QButtonGroup()
        self.grid_view_btn = QRadioButton("网格视图")
        self.grid_view_btn.setChecked(True)
        self.grid_view_btn.toggled.connect(self.on_view_change)
        view_group.addButton(self.grid_view_btn)
        view_sort_layout.addWidget(self.grid_view_btn)
        
        self.list_view_btn = QRadioButton("列表视图")
        self.list_view_btn.toggled.connect(self.on_view_change)
        view_group.addButton(self.list_view_btn)
        view_sort_layout.addWidget(self.list_view_btn)
        
        view_sort_layout.addStretch()
        
        self.sort_combo = QComboBox()
        self.sort_combo.addItems(["按名称", "按大小", "按修改时间"])
        self.sort_combo.currentIndexChanged.connect(self.on_sort_change)
        view_sort_layout.addWidget(self.sort_combo)
        
        result_layout.addLayout(view_sort_layout)
        
        # 结果展示
        # 为网格视图添加滚动功能
        self.grid_scroll_area = QScrollArea()
        self.grid_scroll_area.setWidgetResizable(True)
        # 设置滚动条策略，水平和垂直方向都根据需要显示滚动条
        self.grid_scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.grid_scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        
        # 网格视图
        self.grid_widget = QWidget()
        self.grid_layout = QGridLayout(self.grid_widget)
        self.grid_layout.setContentsMargins(10, 10, 10, 10)
        self.grid_layout.setSpacing(10)
        
        self.grid_scroll_area.setWidget(self.grid_widget)
        
        # 为网格视图安装事件过滤器，用于捕获Ctrl+滚轮事件
        self.grid_scroll_area.viewport().installEventFilter(self)
        
        # 列表视图
        self.list_widget = QTreeWidget()
        self.list_widget.setColumnCount(4)
        self.list_widget.setHeaderLabels(["文件名", "路径", "大小", "修改时间"])
        self.list_widget.itemClicked.connect(self.on_item_clicked)
        self.list_widget.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.list_widget.customContextMenuRequested.connect(self.show_context_menu)
        
        # 创建一个新的splitter，包含滚动区域和列表视图
        self.splitter = QSplitter(Qt.Orientation.Vertical)
        self.splitter.addWidget(self.grid_scroll_area)
        self.splitter.addWidget(self.list_widget)
        self.splitter.setSizes([800, 0])  # 默认显示网格视图
        # 设置splitter的拉伸因子，确保在窗口大小改变时保持比例
        self.splitter.setStretchFactor(0, 1)
        self.splitter.setStretchFactor(1, 1)
        
        # 监听窗口大小变化
        self.resizeEvent = self.on_resize
        
        result_layout.addWidget(self.splitter)
        result_group.setLayout(result_layout)
        middle_layout.addWidget(result_group, 1)
        
        # 右侧内置预览区
        preview_group = QGroupBox("预览")
        preview_layout = QVBoxLayout()
        preview_layout.setContentsMargins(10, 10, 10, 10)
        
        # 预览容器
        self.preview_container = QWidget()
        self.preview_layout = QVBoxLayout(self.preview_container)
        self.preview_layout.setContentsMargins(0, 0, 0, 0)
        self.preview_container.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        
        # 图片预览
        self.image_label = QLabel("点击文件进行预览")
        self.image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.image_label.setMinimumSize(300, 300)
        self.image_label.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.image_label.setStyleSheet("background-color: #252526;")
        
        # 视频预览
        self.video_widget.setMinimumSize(300, 300)
        self.video_widget.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        
        # 预览控制
        self.preview_controls = QWidget()
        self.controls_layout = QVBoxLayout(self.preview_controls)
        self.controls_layout.setContentsMargins(0, 10, 0, 0)
        
        # 按钮布局
        buttons_layout = QHBoxLayout()
        self.zoom_in_btn = QPushButton("放大")
        self.zoom_in_btn.clicked.connect(self.zoom_in)
        buttons_layout.addWidget(self.zoom_in_btn)
        
        self.zoom_out_btn = QPushButton("缩小")
        self.zoom_out_btn.clicked.connect(self.zoom_out)
        buttons_layout.addWidget(self.zoom_out_btn)
        
        self.rotate_btn = QPushButton("旋转")
        self.rotate_btn.clicked.connect(self.rotate_image)
        buttons_layout.addWidget(self.rotate_btn)
        
        self.play_pause_btn = QPushButton("播放")
        self.play_pause_btn.clicked.connect(self.play_pause_video)
        buttons_layout.addWidget(self.play_pause_btn)
        
        # 收藏按钮
        self.favorite_btn = QPushButton("收藏")
        self.favorite_btn.clicked.connect(self.add_to_collection_from_preview)
        buttons_layout.addWidget(self.favorite_btn)
        
        # 定位到文件夹按钮
        self.locate_btn = QPushButton("定位到文件夹")
        self.locate_btn.clicked.connect(self.locate_file_from_preview)
        buttons_layout.addWidget(self.locate_btn)
        
        # 添加按钮布局到主控制布局
        self.controls_layout.addLayout(buttons_layout)
        
        # 音量控制布局
        volume_layout = QHBoxLayout()
        from PyQt6.QtWidgets import QSlider
        self.volume_slider = QSlider(Qt.Orientation.Horizontal)
        self.volume_slider.setMinimum(0)
        self.volume_slider.setMaximum(100)
        self.volume_slider.setValue(int(self.audio_output.volume() * 100))
        self.volume_slider.valueChanged.connect(self.on_volume_change)
        self.volume_slider.setFixedHeight(30)  # 设置高度，使其更像长方形
        volume_layout.addWidget(QLabel("音量:"))
        volume_layout.addWidget(self.volume_slider)
        
        # 添加音量布局到主控制布局
        self.controls_layout.addLayout(volume_layout)
        
        self.preview_layout.addWidget(self.image_label)
        self.preview_layout.addWidget(self.video_widget)
        self.preview_layout.addWidget(self.preview_controls)
        
        # 初始隐藏视频预览和控制
        self.video_widget.hide()
        self.preview_controls.hide()
        
        preview_layout.addWidget(self.preview_container)
        preview_group.setLayout(preview_layout)
        middle_layout.addWidget(preview_group, 1)
        
        main_layout.addLayout(middle_layout)
        
        # 底部状态栏
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        
        self.progress_label = QLabel("就绪")
        self.status_bar.addWidget(self.progress_label)
        
        self.file_count_label = QLabel("文件数: 0")
        self.status_bar.addWidget(self.file_count_label)
        
        self.time_label = QLabel("耗时: 0s")
        self.status_bar.addWidget(self.time_label)
        
        self.setCentralWidget(central_widget)
    
    def on_path_change(self, index):
        if index == 0:  # 常用目录
            self.current_path = os.path.expanduser("~")
        elif index == 1:  # 全盘扫描
            self.current_path = "/"
        else:  # 自定义目录
            self.browse_path()
        self.path_edit.setText(self.current_path)
    
    def browse_path(self):
        path = QFileDialog.getExistingDirectory(self, "选择目录", self.current_path)
        if path:
            self.current_path = path
            self.path_edit.setText(path)
    
    def on_format_change(self, index):
        if index == 0:  # 全部
            self.current_file_type = "all"
        elif index == 1:  # 仅图片
            self.current_file_type = "image"
        else:  # 仅视频
            self.current_file_type = "video"
        self.filter_results()
    
    def on_view_change(self):
        if self.grid_view_btn.isChecked():
            self.current_view = "grid"
            self.splitter.setSizes([800, 0])
        else:
            self.current_view = "list"
            self.splitter.setSizes([0, 800])
        self.update_results_display()
    
    def on_sort_change(self, index):
        if index == 0:  # 按名称
            self.current_sort = "name"
        elif index == 1:  # 按大小
            self.current_sort = "size"
        else:  # 按修改时间
            self.current_sort = "mtime"
        self.sort_results()
        self.update_results_display()
    
    def start_scan(self):
        # 打印调试信息
        print("点击了开始扫描按钮")
        # 获取当前设置
        path = self.path_edit.text()
        print(f"扫描路径: {path}")
        if not os.path.exists(path):
            self.status_bar.showMessage("路径不存在", 3000)
            print("路径不存在")
            return
        
        # 根据选择的文件类型确定要扫描的格式
        if self.current_file_type == "all":
            file_types = self.all_formats
        elif self.current_file_type == "image":
            file_types = self.image_formats
        else:
            file_types = self.video_formats
        
        # 开始扫描
        self.start_scan_btn.setEnabled(False)
        self.stop_scan_btn.setEnabled(True)
        
        # 清空之前的结果
        self.clear_results()
        
        # 打印调试信息
        print(f"扫描路径: {path}")
        print(f"当前文件类型筛选: {self.current_file_type}")
        print(f"文件类型列表: {file_types}")
        print(f"图片格式: {self.image_formats}")
        print(f"视频格式: {self.video_formats}")
        print(f"所有格式: {self.all_formats}")
        print(f"线程数: 4")
        
        # 直接在主线程中执行扫描，用于测试
        print("开始扫描...")
        # 创建扫描器
        scanner = MultiThreadedMediaScanner(
            path=path,
            file_types=file_types,
            thread_count=4
        )
        # 设置回调函数
        scanner.set_callbacks(
            progress_callback=self.update_progress,
            file_found_callback=self.add_file_result
        )
        # 执行扫描
        results = scanner.scan()
        # 打印扫描结果
        print(f"扫描完成，找到 {len(results)} 个文件")
        print(f"扫描结果: {results}")
        # 直接使用扫描器返回的结果，而不是依赖异步的信号处理
        self.scan_results = results
        # 调用scan_finished
        self.scan_finished()
    
    def stop_scan(self):
        print("停止扫描...")
        if hasattr(self, 'scanner'):
            print("调用scanner.stop()")
            self.scanner.stop()
        if hasattr(self, 'scan_thread') and self.scan_thread.isRunning():
            print("停止线程")
            # 强制终止线程
            self.scan_thread.requestInterruption()
            self.scan_thread.quit()
            # 等待线程结束，最多等待5秒
            if not self.scan_thread.wait(5000):
                print("线程强制终止")
        # 确保UI状态更新
        self.start_scan_btn.setEnabled(True)
        self.stop_scan_btn.setEnabled(False)
        self.progress_label.setText("扫描已停止")
        print("扫描已停止")
    
    def update_progress(self, progress, file_count, elapsed):
        # 发射信号，确保在主线程中处理
        self.progress_updated.emit(progress, file_count, elapsed)
    
    def _update_progress(self, progress, file_count, elapsed):
        """实际更新进度的方法，在主线程中执行"""
        self.progress_label.setText(f"扫描中... {progress}%")
        self.file_count_label.setText(f"文件数: {file_count}")
        self.time_label.setText(f"耗时: {elapsed}")
    
    def add_file_result(self, file_info):
        # 发射信号，确保在主线程中处理
        self.file_found.emit(file_info)
    
    def _add_file_result(self, file_info):
        """实际添加文件结果的方法，在主线程中执行"""
        # 检查是否是重复文件（基于文件路径）
        if not any(f['path'] == file_info['path'] for f in self.scan_results):
            self.scan_results.append(file_info)
            print(f"_add_file_result: 添加文件 {file_info['name']}, 当前共 {len(self.scan_results)} 个文件")
            # 每次添加文件都更新显示，确保用户能实时看到扫描结果
            self.sort_results()
            self.update_results_display()
    
    def scan_finished(self):
        self.start_scan_btn.setEnabled(True)
        self.stop_scan_btn.setEnabled(False)
        self.progress_label.setText("扫描完成")
        
        # 去重处理
        seen_paths = set()
        unique_results = []
        for file_info in self.scan_results:
            if file_info['path'] not in seen_paths:
                seen_paths.add(file_info['path'])
                unique_results.append(file_info)
        
        if len(unique_results) < len(self.scan_results):
            print(f"移除了 {len(self.scan_results) - len(unique_results)} 个重复文件")
            self.scan_results = unique_results
        
        self.sort_results()
        # 根据当前文件类型过滤并显示
        self.filter_results()
        
        # 保存扫描记录到数据库
        elapsed = self.time_label.text().replace("耗时: ", "")
        file_count = len(self.scan_results)
        
        # 调试信息：打印要保存的文件
        print(f"scan_finished: 准备保存 {file_count} 个文件到数据库")
        for f in self.scan_results:
            print(f"  - {f['name']}")
        
        scan_id = self.storage.save_scan_record(self.current_path, file_count, elapsed, "完成")
        self.storage.save_media_files(self.scan_results, scan_id)
        print(f"scan_finished: 已保存到数据库，scan_id={scan_id}")
        
        # 添加到历史记录
        self.history_dialog.add_history_record(self.current_path, "完成", file_count, elapsed)
    
    def on_resize(self, event):
        """窗口大小改变时的处理"""
        # 调用父类的resizeEvent
        super().resizeEvent(event)
        # 更新网格视图（如果当前是网格视图且有扫描结果）
        if self.grid_view_btn.isChecked() and self.scan_results:
            self.update_results_display()
        # 更新预览区大小
        if hasattr(self, 'current_preview_file') and self.current_preview_file:
            self.show_preview(self.current_preview_file)
    
    def scan_stopped(self):
        self.start_scan_btn.setEnabled(True)
        self.stop_scan_btn.setEnabled(False)
        self.progress_label.setText("扫描已停止")
        self.sort_results()
        # 根据当前文件类型过滤并显示
        self.filter_results()
        
        # 保存扫描记录到数据库
        elapsed = self.time_label.text().replace("耗时: ", "")
        file_count = len(self.scan_results)
        
        # 调试信息：打印要保存的文件
        print(f"scan_stopped: 准备保存 {file_count} 个文件到数据库")
        for f in self.scan_results:
            print(f"  - {f['name']}")
        
        scan_id = self.storage.save_scan_record(self.current_path, file_count, elapsed, "已停止")
        self.storage.save_media_files(self.scan_results, scan_id)
        print(f"scan_stopped: 已保存到数据库，scan_id={scan_id}")
        
        # 添加到历史记录
        self.history_dialog.add_history_record(self.current_path, "已停止", file_count, elapsed)
    
    def load_recent_scan_results(self):
        """加载最近的扫描结果"""
        try:
            # 获取最近的扫描记录
            scan_records = self.storage.get_scan_records()
            if scan_records:
                # 获取最近的扫描记录
                recent_record = scan_records[0]
                scan_id = recent_record['id']
                
                # 获取该扫描记录的媒体文件
                media_files = self.storage.get_media_files_by_scan_id(scan_id)
                
                # 调试信息：打印加载的文件数量和类型
                print(f"从数据库加载了 {len(media_files)} 个文件")
                for file in media_files:
                    print(f"  - {file['name']} (类型: {file.get('type', 'unknown')}, 扩展名: {file.get('ext', 'unknown')})")
                
                if media_files:
                    # 转换媒体文件格式
                    self.scan_results = []
                    for file in media_files:
                        file_info = {
                            'name': file['name'],
                            'path': file['path'],
                            'size': file['size'],
                            'mtime': file['mtime']
                        }
                        self.scan_results.append(file_info)
                    
                    # 排序并更新显示
                    self.sort_results()
                    # 根据当前文件类型过滤并显示
                    self.filter_results()
                    
                    # 更新状态信息
                    self.status_bar.showMessage(f"已加载最近的扫描结果，共 {len(self.scan_results)} 个文件", 3000)
                    self.progress_label.setText("已加载历史结果")
                    self.file_count_label.setText(f"文件数: {len(self.scan_results)}")
                    
                    # 更新当前路径
                    self.current_path = recent_record['scan_path']
                    self.path_edit.setText(self.current_path)
        except Exception as e:
            print(f"加载最近扫描结果失败: {e}")
    
    def sort_results(self):
        if self.current_sort == "name":
            self.scan_results.sort(key=lambda x: x['name'].lower())
        elif self.current_sort == "size":
            self.scan_results.sort(key=lambda x: x['size'], reverse=True)
        else:  # mtime
            self.scan_results.sort(key=lambda x: x['mtime'], reverse=True)
    
    def filter_results(self):
        keyword = self.search_edit.text().lower()
        filtered = [f for f in self.scan_results if keyword in f['name'].lower()]
        
        # 调试信息
        print(f"filter_results: 原始文件数={len(self.scan_results)}, 关键词过滤后={len(filtered)}, current_file_type={self.current_file_type}")
        
        # 根据文件类型过滤
        if self.current_file_type == "image":
            filtered = [f for f in filtered if any(f['name'].lower().endswith(ext) for ext in self.image_formats)]
            print(f"  图片过滤后={len(filtered)}")
        elif self.current_file_type == "video":
            filtered = [f for f in filtered if any(f['name'].lower().endswith(ext) for ext in self.video_formats)]
            print(f"  视频过滤后={len(filtered)}")
        else:
            print(f"  全部文件，不过滤")
        
        self.update_results_display(filtered)
    
    def clear_results(self):
        # 清空网格视图
        for i in reversed(range(self.grid_layout.count())):
            widget = self.grid_layout.itemAt(i).widget()
            if widget:
                widget.deleteLater()
        
        # 清空列表视图
        self.list_widget.clear()
    
    def update_results_display(self, results=None):
        if results is None:
            results = self.scan_results
        
        # 清空当前显示
        self.clear_results()
        
        if self.current_view == "grid":
            # 网格视图
            # 使用滚动区域的视口宽度来计算，确保内容不会超出范围
            grid_width = self.grid_scroll_area.viewport().width()
            spacing = self.grid_layout.spacing()
            margins = self.grid_layout.contentsMargins()
            available_width = grid_width - (margins.left() + margins.right())
            
            # 计算每行可以显示的文件数量
            min_item_width = int(100 * self.grid_scale_factor)  # 根据缩放因子调整最小宽度
            max_item_width = int(200 * self.grid_scale_factor)  # 根据缩放因子调整最大宽度
            
            # 计算每行显示的文件数量，确保不会超出可用宽度
            max_cols = max(1, available_width // (min_item_width + spacing))
            max_cols = min(8, max_cols)  # 最多显示8列
            
            # 计算每个文件项的大小，确保不会超出可用宽度
            if max_cols > 1:
                item_width = (available_width - (max_cols - 1) * spacing) // max_cols
            else:
                item_width = available_width - spacing
            item_width = max(min_item_width, min(max_item_width, item_width))
            item_height = item_width  # 保持正方形
            
            row = 0
            col = 0
            
            for file_info in results:
                file_widget = QWidget()
                file_layout = QVBoxLayout(file_widget)
                
                # 缩略图
                thumbnail = QLabel()
                if any(file_info['name'].lower().endswith(ext) for ext in self.image_formats):
                    pixmap = QPixmap(file_info['path'])
                    pixmap = pixmap.scaled(item_width, item_height, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
                    thumbnail.setPixmap(pixmap)
                else:
                    # 视频文件显示第一帧作为封面
                    cover_path = VideoProcessor.get_video_cover(file_info['path'])
                    if cover_path:
                        pixmap = QPixmap(cover_path)
                        pixmap = pixmap.scaled(item_width, item_height, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
                        thumbnail.setPixmap(pixmap)
                        # 清理临时文件
                        try:
                            os.remove(cover_path)
                        except:
                            pass
                    else:
                        # 视频文件显示默认图标
                        thumbnail.setText("视频")
                        thumbnail.setAlignment(Qt.AlignmentFlag.AlignCenter)
                        thumbnail.setStyleSheet("background-color: #252526; color: #CCCCCC;")
                
                thumbnail.setFixedSize(item_width, item_height)
                file_layout.addWidget(thumbnail)
                
                # 文件名
                name_label = QLabel(file_info['name'])
                name_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
                name_label.setWordWrap(True)
                name_label.setMaximumWidth(item_width)
                file_layout.addWidget(name_label)
                
                # 点击事件
                file_widget.mousePressEvent = lambda event, f=file_info: self.on_file_clicked(f)
                
                self.grid_layout.addWidget(file_widget, row, col)
                
                col += 1
                if col >= max_cols:
                    col = 0
                    row += 1
        else:
            # 列表视图
            for file_info in results:
                item = QTreeWidgetItem([
                    file_info['name'],
                    file_info['path'],
                    f"{file_info['size'] / 1024:.2f} KB",
                    time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(file_info['mtime']))
                ])
                item.setData(0, Qt.ItemDataRole.UserRole, file_info)
                self.list_widget.addTopLevelItem(item)
    
    def on_file_clicked(self, file_info):
        self.show_preview(file_info)
    
    def on_item_clicked(self, item, column):
        file_info = item.data(0, Qt.ItemDataRole.UserRole)
        if file_info:
            self.show_preview(file_info)
    
    def show_preview(self, file_info):
        # 保存当前预览的文件信息
        self.current_preview_file = file_info
        
        # 隐藏所有预览组件
        self.image_label.hide()
        self.video_widget.hide()
        self.preview_controls.hide()
        
        # 根据文件类型显示相应的预览
        if any(file_info['name'].lower().endswith(ext) for ext in self.image_formats):
            # 图片预览
            pixmap = QPixmap(file_info['path'])
            scaled_pixmap = pixmap.scaled(
                self.preview_container.width() - 20,
                self.preview_container.height() - 20,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation
            )
            self.image_label.setPixmap(scaled_pixmap)
            self.image_label.show()
            self.preview_controls.show()
        elif any(file_info['name'].lower().endswith(ext) for ext in self.video_formats):
            # 视频预览 - 显示第一帧作为封面
            cover_path = VideoProcessor.get_video_cover(file_info['path'])
            if cover_path:
                pixmap = QPixmap(cover_path)
                scaled_pixmap = pixmap.scaled(
                    self.preview_container.width() - 20,
                    self.preview_container.height() - 20,
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation
                )
                self.image_label.setPixmap(scaled_pixmap)
                self.image_label.show()
                self.preview_controls.show()
                # 清理临时文件
                try:
                    os.remove(cover_path)
                except:
                    pass
            else:
                # 如果无法提取封面，显示视频播放器
                self.media_player.setSource(QUrl.fromLocalFile(file_info['path']))
                self.video_widget.show()
                self.preview_controls.show()
            # 重置播放按钮状态
            self.play_pause_btn.setText("播放")
    
    def add_to_collection_from_preview(self):
        """从预览窗口添加文件到收藏夹"""
        if hasattr(self, 'current_preview_file') and self.current_preview_file:
            # 调用收藏夹对话框的add_file_to_collection方法
            self.collection_dialog.add_file_to_collection(self.current_preview_file)
        else:
            self.status_bar.showMessage("没有可收藏的文件", 3000)
    
    def locate_file_from_preview(self):
        """从预览窗口定位到文件所在文件夹"""
        if hasattr(self, 'current_preview_file') and self.current_preview_file:
            # 调用locate_file方法来定位到文件所在的文件夹
            self.locate_file(self.current_preview_file)
        else:
            self.status_bar.showMessage("没有可定位的文件", 3000)
    
    def zoom_in(self):
        # 图片放大功能
        if self.image_label.isVisible() and self.image_label.pixmap():
            current_pixmap = self.image_label.pixmap()
            new_size = current_pixmap.size() * 1.2
            scaled_pixmap = current_pixmap.scaled(new_size, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
            self.image_label.setPixmap(scaled_pixmap)
    
    def zoom_out(self):
        # 图片缩小功能
        if self.image_label.isVisible() and self.image_label.pixmap():
            current_pixmap = self.image_label.pixmap()
            new_size = current_pixmap.size() * 0.8
            scaled_pixmap = current_pixmap.scaled(new_size, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
            self.image_label.setPixmap(scaled_pixmap)
    
    def eventFilter(self, obj, event):
        """事件过滤器，用于处理Ctrl+滚轮调整网格视图图片大小"""
        if obj == self.grid_scroll_area.viewport() and event.type() == event.Type.Wheel:
            # 检查是否按下了Ctrl键
            if event.modifiers() == Qt.KeyboardModifier.ControlModifier:
                # 获取滚轮方向
                delta = event.angleDelta().y()
                if delta > 0:
                    # 向上滚动，放大
                    self.grid_scale_factor = min(self.grid_scale_factor + 0.1, self.max_scale_factor)
                else:
                    # 向下滚动，缩小
                    self.grid_scale_factor = max(self.grid_scale_factor - 0.1, self.min_scale_factor)
                
                # 更新网格视图显示
                if self.current_view == "grid" and self.scan_results:
                    self.update_results_display()
                
                return True  # 阻止事件继续传播
        
        return super().eventFilter(obj, event)
    
    def rotate_image(self):
        # 图片旋转功能
        if self.image_label.isVisible() and self.image_label.pixmap():
            current_pixmap = self.image_label.pixmap()
            rotated_pixmap = current_pixmap.transformed(QTransform().rotate(90))
            self.image_label.setPixmap(rotated_pixmap)
    
    def play_pause_video(self):
        # 视频播放/暂停功能
        if self.video_widget.isVisible():
            if self.media_player.playbackState() == QMediaPlayer.PlaybackState.PlayingState:
                self.media_player.pause()
                self.play_pause_btn.setText("播放")
            else:
                self.media_player.play()
                self.play_pause_btn.setText("暂停")
        elif self.image_label.isVisible() and hasattr(self, 'current_preview_file'):
            # 如果当前显示的是视频封面，切换到视频播放器
            file_info = self.current_preview_file
            if any(file_info['name'].lower().endswith(ext) for ext in self.video_formats):
                # 隐藏图片标签，显示视频播放器
                self.image_label.hide()
                self.video_widget.show()
                # 加载视频
                self.media_player.setSource(QUrl.fromLocalFile(file_info['path']))
                # 开始播放
                self.media_player.play()
                self.play_pause_btn.setText("暂停")
    
    def on_volume_change(self, value):
        # 音量控制功能
        volume = value / 100.0
        self.audio_output.setVolume(volume)
    
    def show_context_menu(self, position):
        # 显示右键菜单
        item = self.list_widget.itemAt(position)
        if not item:
            return
        
        file_info = item.data(0, Qt.ItemDataRole.UserRole)
        if not file_info:
            return
        
        menu = QMenu()
        
        preview_action = QAction("预览", self)
        preview_action.triggered.connect(lambda: self.show_preview(file_info))
        menu.addAction(preview_action)
        
        open_action = QAction("打开文件", self)
        open_action.triggered.connect(lambda: self.open_file(file_info))
        menu.addAction(open_action)
        
        locate_action = QAction("定位到文件夹", self)
        locate_action.triggered.connect(lambda: self.locate_file(file_info))
        menu.addAction(locate_action)
        
        copy_path_action = QAction("复制路径", self)
        copy_path_action.triggered.connect(lambda: self.copy_path(file_info))
        menu.addAction(copy_path_action)
        
        add_to_collection_action = QAction("添加到收藏夹", self)
        add_to_collection_action.triggered.connect(lambda: self.collection_dialog.add_file_to_collection(file_info))
        menu.addAction(add_to_collection_action)
        
        menu.exec(self.list_widget.mapToGlobal(position))
    
    def open_file(self, file_info):
        # 打开文件
        success = FileUtils.open_file(file_info['path'])
        if not success:
            self.status_bar.showMessage("打开文件失败", 3000)
    
    def locate_file(self, file_info):
        # 定位到文件夹
        success = FileUtils.locate_file(file_info['path'])
        if not success:
            self.status_bar.showMessage("定位文件失败", 3000)
    
    def copy_path(self, file_info):
        # 复制路径到剪贴板
        success = FileUtils.copy_file_path(file_info['path'])
        if success:
            self.status_bar.showMessage("路径已复制到剪贴板", 3000)
        else:
            self.status_bar.showMessage("复制路径失败", 3000)
    
    def favorite_file(self, file_info):
        # 收藏文件（这里只是示例，实际需要持久化存储）
        self.status_bar.showMessage(f"已收藏: {file_info['name']}", 3000)
    
    def open_format_settings(self):
        # 打开格式设置对话框
        dialog = FormatSettingsDialog(self, self.image_formats, self.video_formats)
        if dialog.exec() == dialog.accepted:
            self.image_formats, self.video_formats = dialog.get_settings()
            self.all_formats = self.image_formats + self.video_formats
            self.status_bar.showMessage("格式设置已更新", 2000)
    
    def open_history(self):
        # 打开历史记录对话框
        self.history_dialog.exec()
    
    def open_settings(self):
        # 打开设置对话框
        if self.settings_dialog.exec() == self.settings_dialog.accepted:
            self.status_bar.showMessage("设置已更新", 2000)
    
    def open_collection(self):
        # 打开收藏夹对话框（非模态）
        self.collection_dialog.show()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
