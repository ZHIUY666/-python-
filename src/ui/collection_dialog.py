from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QListWidget, QListWidgetItem, 
    QPushButton, QInputDialog, QMessageBox, QLabel, QSplitter,
    QTreeWidget, QTreeWidgetItem, QMenu, QGroupBox, QWidget, QVBoxLayout, QHBoxLayout,
    QGridLayout, QRadioButton, QButtonGroup, QScrollArea
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPixmap, QTransform
from src.data.storage import DataStorage
from src.core.video_processor import VideoProcessor
import os
import time

class CollectionDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("收藏夹管理")
        self.setGeometry(100, 100, 1000, 600)  # 增加宽度以容纳预览窗口
        # 设置为非模态对话框，这样在打开收藏界面时，主UI中的各种按钮仍然可以点击
        self.setModal(False)
        self.storage = DataStorage()
        # 支持的媒体格式
        self.image_formats = ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.webp']
        self.video_formats = ['.mp4', '.avi', '.mov', '.wmv', '.flv', '.mkv', '.webm']
        # 当前预览的文件信息
        self.current_preview_file = None
        # 图片缩放和旋转状态
        self.current_scale = 1.0
        self.current_rotation = 0
        self.init_ui()
        self.load_collections()
    
    def init_ui(self):
        # 主布局
        main_layout = QVBoxLayout(self)
        
        # 分割器
        splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # 左侧收藏夹列表
        self.collection_list = QListWidget()
        self.collection_list.setMinimumWidth(200)
        self.collection_list.itemClicked.connect(self.on_collection_clicked)
        splitter.addWidget(self.collection_list)
        
        # 中间文件列表/网格
        self.view_group = QWidget()
        self.view_layout = QVBoxLayout(self.view_group)
        
        # 视图切换
        view_toggle_layout = QHBoxLayout()
        self.list_view_btn = QRadioButton("列表视图")
        self.list_view_btn.setChecked(True)
        self.grid_view_btn = QRadioButton("网格视图")
        view_btn_group = QButtonGroup()
        view_btn_group.addButton(self.list_view_btn)
        view_btn_group.addButton(self.grid_view_btn)
        self.list_view_btn.toggled.connect(self.on_view_change)
        self.grid_view_btn.toggled.connect(self.on_view_change)
        view_toggle_layout.addWidget(self.list_view_btn)
        view_toggle_layout.addWidget(self.grid_view_btn)
        view_toggle_layout.addStretch()
        self.view_layout.addLayout(view_toggle_layout)
        
        # 列表视图
        self.file_tree = QTreeWidget()
        self.file_tree.setColumnCount(4)
        self.file_tree.setHeaderLabels(["文件名", "路径", "大小", "修改时间"])
        self.file_tree.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.file_tree.customContextMenuRequested.connect(self.show_file_context_menu)
        self.file_tree.itemClicked.connect(self.on_file_clicked)
        self.view_layout.addWidget(self.file_tree)
        
        # 网格视图
        self.grid_scroll_area = QScrollArea()
        self.grid_scroll_area.setWidgetResizable(True)
        self.grid_scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.grid_scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.grid_widget = QWidget()
        self.grid_layout = QGridLayout(self.grid_widget)
        self.grid_layout.setContentsMargins(10, 10, 10, 10)
        self.grid_scroll_area.setWidget(self.grid_widget)
        self.view_layout.addWidget(self.grid_scroll_area)
        self.grid_scroll_area.hide()  # 初始隐藏网格视图
        
        splitter.addWidget(self.view_group)
        
        # 右侧预览区域
        preview_group = QGroupBox("预览")
        preview_layout = QVBoxLayout()
        
        # 预览容器
        self.preview_container = QWidget()
        self.preview_layout = QVBoxLayout(self.preview_container)
        self.preview_layout.setContentsMargins(0, 0, 0, 0)
        
        # 图片预览
        self.image_label = QLabel("点击文件进行预览")
        self.image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.image_label.setMinimumSize(300, 300)
        self.image_label.setStyleSheet("background-color: #252526; color: #CCCCCC;")
        
        # 视频预览
        from PyQt6.QtMultimedia import QMediaPlayer, QAudioOutput
        from PyQt6.QtMultimediaWidgets import QVideoWidget
        self.audio_output = QAudioOutput()
        self.media_player = QMediaPlayer()
        self.media_player.setAudioOutput(self.audio_output)
        self.video_widget = QVideoWidget()
        self.media_player.setVideoOutput(self.video_widget)
        self.video_widget.setMinimumSize(300, 300)
        # 设置默认音量
        self.audio_output.setVolume(0.5)
        
        # 预览控制
        self.preview_controls = QWidget()
        self.controls_layout = QHBoxLayout(self.preview_controls)
        self.controls_layout.setContentsMargins(0, 10, 0, 0)
        
        self.zoom_in_btn = QPushButton("放大")
        self.zoom_in_btn.clicked.connect(self.zoom_in)
        self.controls_layout.addWidget(self.zoom_in_btn)
        
        self.zoom_out_btn = QPushButton("缩小")
        self.zoom_out_btn.clicked.connect(self.zoom_out)
        self.controls_layout.addWidget(self.zoom_out_btn)
        
        self.rotate_btn = QPushButton("旋转")
        self.rotate_btn.clicked.connect(self.rotate_image)
        self.controls_layout.addWidget(self.rotate_btn)
        
        self.play_pause_btn = QPushButton("播放")
        self.play_pause_btn.clicked.connect(self.play_pause_video)
        self.controls_layout.addWidget(self.play_pause_btn)
        
        # 定位到文件夹按钮
        self.locate_btn = QPushButton("定位到文件夹")
        self.locate_btn.clicked.connect(self.locate_file_from_preview)
        self.controls_layout.addWidget(self.locate_btn)
        
        # 音量控制
        from PyQt6.QtWidgets import QSlider
        self.volume_slider = QSlider(Qt.Orientation.Horizontal)
        self.volume_slider.setMinimum(0)
        self.volume_slider.setMaximum(100)
        self.volume_slider.setValue(int(self.audio_output.volume() * 100))
        self.volume_slider.valueChanged.connect(self.on_volume_change)
        self.volume_slider.setFixedHeight(30)  # 设置高度，使其更像长方形
        self.controls_layout.addWidget(QLabel("音量:"))
        self.controls_layout.addWidget(self.volume_slider)
        
        self.preview_layout.addWidget(self.image_label)
        self.preview_layout.addWidget(self.video_widget)
        self.preview_layout.addWidget(self.preview_controls)
        
        # 初始隐藏视频预览和控制
        self.video_widget.hide()
        self.preview_controls.hide()
        
        preview_layout.addWidget(self.preview_container)
        preview_group.setLayout(preview_layout)
        splitter.addWidget(preview_group)
        
        main_layout.addWidget(splitter)
        
        # 底部按钮
        button_layout = QHBoxLayout()
        
        self.create_collection_btn = QPushButton("创建收藏夹")
        self.create_collection_btn.clicked.connect(self.create_collection)
        button_layout.addWidget(self.create_collection_btn)
        
        self.edit_collection_btn = QPushButton("编辑收藏夹")
        self.edit_collection_btn.clicked.connect(self.edit_collection)
        button_layout.addWidget(self.edit_collection_btn)
        
        self.delete_collection_btn = QPushButton("删除收藏夹")
        self.delete_collection_btn.clicked.connect(self.delete_collection)
        button_layout.addWidget(self.delete_collection_btn)
        
        self.add_files_btn = QPushButton("添加文件")
        self.add_files_btn.clicked.connect(self.add_files_to_collection)
        button_layout.addWidget(self.add_files_btn)
        
        button_layout.addStretch()
        
        self.close_btn = QPushButton("关闭")
        self.close_btn.clicked.connect(self.close)
        button_layout.addWidget(self.close_btn)
        
        main_layout.addLayout(button_layout)
    
    def load_collections(self):
        """加载所有收藏夹"""
        self.collection_list.clear()
        collections = self.storage.get_collections()
        for collection in collections:
            item = QListWidgetItem(collection['name'])
            item.setData(Qt.ItemDataRole.UserRole, collection['id'])
            self.collection_list.addItem(item)
    
    def on_collection_clicked(self, item):
        """当点击收藏夹时，加载该收藏夹中的文件"""
        collection_id = item.data(Qt.ItemDataRole.UserRole)
        self.load_collection_files(collection_id)
    
    def load_collection_files(self, collection_id):
        """加载收藏夹中的文件"""
        self.file_tree.clear()
        
        # 清空网格视图
        for i in reversed(range(self.grid_layout.count())):
            widget = self.grid_layout.itemAt(i).widget()
            if widget:
                widget.deleteLater()
        
        files = self.storage.get_collection_files(collection_id)
        
        # 列表视图
        for file in files:
            item = QTreeWidgetItem([
                file['name'],
                file['path'],
                f"{file['size'] / 1024:.2f} KB",
                time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(file['mtime']))
            ])
            item.setData(0, Qt.ItemDataRole.UserRole, file)
            self.file_tree.addTopLevelItem(item)
        
        # 网格视图
        if self.grid_view_btn.isChecked():
            self.update_grid_view(files)
    
    def on_view_change(self):
        """视图切换处理"""
        if self.list_view_btn.isChecked():
            self.file_tree.show()
            self.grid_scroll_area.hide()
        else:
            self.file_tree.hide()
            self.grid_scroll_area.show()
            # 重新加载当前收藏夹的文件到网格视图
            current_item = self.collection_list.currentItem()
            if current_item:
                collection_id = current_item.data(Qt.ItemDataRole.UserRole)
                files = self.storage.get_collection_files(collection_id)
                self.update_grid_view(files)
    
    def update_grid_view(self, files):
        """更新网格视图"""
        # 清空网格视图
        for i in reversed(range(self.grid_layout.count())):
            widget = self.grid_layout.itemAt(i).widget()
            if widget:
                widget.deleteLater()
        
        # 计算网格布局 - 固定为单列，上下滑动
        grid_width = self.grid_widget.width()
        spacing = self.grid_layout.spacing()
        margins = self.grid_layout.contentsMargins()
        available_width = grid_width - (margins.left() + margins.right())
        
        min_item_width = 150
        max_item_width = 250
        max_cols = 1  # 固定为单列
        
        item_width = min(max_item_width, available_width)
        item_width = max(min_item_width, item_width)
        item_height = item_width
        
        row = 0
        col = 0
        
        for file_info in files:
            file_widget = QWidget()
            file_layout = QVBoxLayout(file_widget)
            
            # 缩略图
            thumbnail = QLabel()
            if any(file_info['name'].lower().endswith(ext) for ext in self.image_formats):
                # 确保文件路径使用正确的格式
                file_path = file_info['path'].replace('/', '\\')
                if os.path.exists(file_path):
                    pixmap = QPixmap(file_path)
                    pixmap = pixmap.scaled(item_width, item_height, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
                    thumbnail.setPixmap(pixmap)
                else:
                    thumbnail.setText("图片")
                    thumbnail.setAlignment(Qt.AlignmentFlag.AlignCenter)
                    thumbnail.setStyleSheet("background-color: #252526; color: #CCCCCC;")
            else:
                # 视频文件显示第一帧作为封面
                # 确保文件路径使用正确的格式
                file_path = file_info['path'].replace('/', '\\')
                if os.path.exists(file_path):
                    cover_path = VideoProcessor.get_video_cover(file_path)
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
                        thumbnail.setText("视频")
                        thumbnail.setAlignment(Qt.AlignmentFlag.AlignCenter)
                        thumbnail.setStyleSheet("background-color: #252526; color: #CCCCCC;")
                else:
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
            file_widget.mousePressEvent = lambda event, f=file_info: self.on_file_clicked_grid(f)
            
            self.grid_layout.addWidget(file_widget, row, col)
            
            col += 1
            if col >= max_cols:
                col = 0
                row += 1
    
    def on_file_clicked_grid(self, file_info):
        """网格视图中点击文件的处理"""
        self.show_preview(file_info)
    
    def create_collection(self):
        """创建收藏夹"""
        name, ok = QInputDialog.getText(self, "创建收藏夹", "请输入收藏夹名称:")
        if ok and name:
            description, ok = QInputDialog.getText(self, "创建收藏夹", "请输入收藏夹描述:")
            if ok:
                collection_id = self.storage.create_collection(name, description)
                if collection_id != -1:
                    self.load_collections()
                    QMessageBox.information(self, "成功", "收藏夹创建成功")
                else:
                    QMessageBox.warning(self, "失败", "收藏夹创建失败")
    
    def edit_collection(self):
        """编辑收藏夹"""
        current_item = self.collection_list.currentItem()
        if not current_item:
            QMessageBox.warning(self, "提示", "请先选择一个收藏夹")
            return
        
        collection_id = current_item.data(Qt.ItemDataRole.UserRole)
        name, ok = QInputDialog.getText(self, "编辑收藏夹", "请输入新的收藏夹名称:", text=current_item.text())
        if ok and name:
            description, ok = QInputDialog.getText(self, "编辑收藏夹", "请输入新的收藏夹描述:")
            if ok:
                # 这里需要添加更新收藏夹的方法
                QMessageBox.information(self, "成功", "收藏夹编辑成功")
                self.load_collections()
    
    def delete_collection(self):
        """删除收藏夹"""
        current_item = self.collection_list.currentItem()
        if not current_item:
            QMessageBox.warning(self, "提示", "请先选择一个收藏夹")
            return
        
        collection_id = current_item.data(Qt.ItemDataRole.UserRole)
        reply = QMessageBox.question(self, "确认删除", f"确定要删除收藏夹 '{current_item.text()}' 吗？",
                                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            if self.storage.delete_collection(collection_id):
                self.load_collections()
                self.file_tree.clear()
                QMessageBox.information(self, "成功", "收藏夹删除成功")
            else:
                QMessageBox.warning(self, "失败", "收藏夹删除失败")
    
    def show_file_context_menu(self, position):
        """显示文件右键菜单"""
        item = self.file_tree.itemAt(position)
        if not item:
            return
        
        menu = QMenu()
        open_action = menu.addAction("打开文件")
        locate_action = menu.addAction("定位到文件夹")
        copy_path_action = menu.addAction("复制路径")
        remove_action = menu.addAction("从收藏夹中删除")
        
        action = menu.exec(self.file_tree.mapToGlobal(position))
        file_info = item.data(0, Qt.ItemDataRole.UserRole)
        
        if action == open_action:
            # 打开文件，确保文件路径使用正确的格式
            file_path = file_info['path'].replace('/', '\\')  # 将正斜杠转换为反斜杠，适应Windows系统
            if os.path.exists(file_path):
                os.startfile(file_path)
            else:
                QMessageBox.warning(self, "错误", f"文件不存在: {file_path}")
        elif action == locate_action:
            # 定位到文件夹，确保文件路径使用正确的格式
            file_path = file_info['path'].replace('/', '\\')  # 将正斜杠转换为反斜杠，适应Windows系统
            if os.path.exists(file_path):
                os.startfile(os.path.dirname(file_path))
            else:
                QMessageBox.warning(self, "错误", f"文件不存在: {file_path}")
        elif action == copy_path_action:
            # 复制路径
            import pyperclip
            pyperclip.copy(file_info['path'])
        elif action == remove_action:
            # 从收藏夹中删除
            current_collection = self.collection_list.currentItem()
            if current_collection:
                collection_id = current_collection.data(Qt.ItemDataRole.UserRole)
                if self.storage.remove_file_from_collection(collection_id, file_info['file_id']):
                    self.load_collection_files(collection_id)
                    QMessageBox.information(self, "成功", "文件已从收藏夹中删除")
                else:
                    QMessageBox.warning(self, "失败", "从收藏夹中删除文件失败")
    
    def add_file_to_collection(self, file_info):
        """添加文件到收藏夹"""
        # 获取文件ID
        import hashlib
        file_id = hashlib.md5(file_info['path'].encode()).hexdigest()
        
        # 显示收藏夹列表，让用户选择要添加到哪个收藏夹
        collections = self.storage.get_collections()
        if not collections:
            # 如果没有收藏夹，提示用户创建一个
            reply = QMessageBox.question(self, "提示", "没有收藏夹，是否创建一个？",
                                        QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
            if reply == QMessageBox.StandardButton.Yes:
                self.create_collection()
                collections = self.storage.get_collections()
            else:
                return
        
        # 让用户选择收藏夹
        collection_names = [c['name'] for c in collections]
        collection_name, ok = QInputDialog.getItem(self, "添加到收藏夹", "请选择收藏夹:", collection_names, 0, False)
        if ok:
            # 找到对应的收藏夹ID
            collection_id = None
            for c in collections:
                if c['name'] == collection_name:
                    collection_id = c['id']
                    break
            
            if collection_id:
                if self.storage.add_file_to_collection(collection_id, file_id):
                    QMessageBox.information(self, "成功", f"文件已添加到收藏夹 '{collection_name}'")
                else:
                    QMessageBox.warning(self, "失败", "添加文件到收藏夹失败")
    
    def add_files_to_collection(self):
        """从文件系统中选择文件并添加到当前收藏夹"""
        # 确保有选中的收藏夹
        current_item = self.collection_list.currentItem()
        if not current_item:
            QMessageBox.warning(self, "提示", "请先选择一个收藏夹")
            return
        
        collection_id = current_item.data(Qt.ItemDataRole.UserRole)
        collection_name = current_item.text()
        
        # 打开文件选择对话框
        from PyQt6.QtWidgets import QFileDialog
        file_dialog = QFileDialog()
        file_dialog.setFileMode(QFileDialog.FileMode.ExistingFiles)
        file_dialog.setNameFilters(["媒体文件 (*.jpg *.jpeg *.png *.gif *.bmp *.tiff *.webp *.mp4 *.avi *.mov *.wmv *.flv *.mkv *.webm)", "所有文件 (*.*)"])
        
        if file_dialog.exec() == QFileDialog.DialogCode.Accepted:
            selected_files = file_dialog.selectedFiles()
            if selected_files:
                added_count = 0
                for file_path in selected_files:
                    # 确保文件存在
                    if os.path.exists(file_path):
                        # 获取文件信息
                        file_name = os.path.basename(file_path)
                        file_size = os.path.getsize(file_path)
                        file_mtime = os.path.getmtime(file_path)
                        
                        # 保存文件到媒体文件表
                        import hashlib
                        file_id = hashlib.md5(file_path.encode()).hexdigest()
                        file_ext = os.path.splitext(file_name)[1].lower()
                        file_type = "image" if file_ext in ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.webp'] else "video"
                        
                        # 保存到媒体文件表
                        conn = sqlite3.connect(self.storage.db_path)
                        cursor = conn.cursor()
                        try:
                            # 确保文件路径使用正斜杠，避免反斜杠被转义
                            file_path = file_path.replace('\\', '/')
                            cursor.execute(
                                "INSERT OR REPLACE INTO media_files (file_id, file_name, file_path, file_type, file_ext, file_size, modify_time, is_collected, scan_id) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                                (file_id, file_name, file_path, file_type, file_ext, file_size, file_mtime, 1, 1)  # scan_id暂时设为1
                            )
                            conn.commit()
                        except Exception as e:
                            print(f"保存文件信息失败: {e}")
                            conn.rollback()
                        finally:
                            conn.close()
                        
                        # 添加到收藏夹
                        if self.storage.add_file_to_collection(collection_id, file_id):
                            added_count += 1
                
                if added_count > 0:
                    QMessageBox.information(self, "成功", f"已成功添加 {added_count} 个文件到收藏夹 '{collection_name}'")
                    # 刷新文件列表
                    self.load_collection_files(collection_id)
                else:
                    QMessageBox.warning(self, "失败", "添加文件到收藏夹失败")
    
    def on_file_clicked(self, item, column):
        """当点击文件时，显示预览"""
        file_info = item.data(0, Qt.ItemDataRole.UserRole)
        if file_info:
            self.show_preview(file_info)
    
    def show_preview(self, file_info):
        """显示文件预览"""
        # 保存当前预览的文件信息
        self.current_preview_file = file_info
        # 重置缩放和旋转状态
        self.current_scale = 1.0
        self.current_rotation = 0
        
        # 隐藏所有预览组件
        self.image_label.hide()
        self.video_widget.hide()
        self.preview_controls.hide()
        
        # 确保文件路径使用正确的格式
        file_path = file_info['path'].replace('/', '\\')  # 将正斜杠转换为反斜杠，适应Windows系统
        
        # 根据文件类型显示相应的预览
        if any(file_info['name'].lower().endswith(ext) for ext in self.image_formats):
            # 图片预览
            if os.path.exists(file_path):
                pixmap = QPixmap(file_path)
                if not pixmap.isNull():
                    scaled_pixmap = pixmap.scaled(
                        self.preview_container.width() - 20,
                        self.preview_container.height() - 20,
                        Qt.AspectRatioMode.KeepAspectRatio,
                        Qt.TransformationMode.SmoothTransformation
                    )
                    self.image_label.setPixmap(scaled_pixmap)
                    self.image_label.show()
                    self.preview_controls.show()
                else:
                    self.image_label.setText("无法加载图片")
                    self.image_label.show()
            else:
                self.image_label.setText(f"文件不存在: {file_path}")
                self.image_label.show()
        elif any(file_info['name'].lower().endswith(ext) for ext in self.video_formats):
            # 视频预览 - 显示第一帧作为封面
            if os.path.exists(file_path):
                cover_path = VideoProcessor.get_video_cover(file_path)
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
                    from PyQt6.QtCore import QUrl
                    self.media_player.setSource(QUrl.fromLocalFile(file_path))
                    self.video_widget.show()
                    self.preview_controls.show()
            else:
                self.image_label.setText(f"文件不存在: {file_path}")
                self.image_label.show()
    
    def zoom_in(self):
        """图片放大功能"""
        if self.image_label.isVisible() and self.image_label.pixmap():
            # 确保文件路径使用正确的格式
            file_path = self.current_preview_file['path'].replace('/', '\\')  # 将正斜杠转换为反斜杠，适应Windows系统
            if os.path.exists(file_path):
                self.current_scale += 0.1
                original_pixmap = QPixmap(file_path)
                scaled_pixmap = original_pixmap.scaled(
                    original_pixmap.width() * self.current_scale,
                    original_pixmap.height() * self.current_scale,
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation
                )
                self.image_label.setPixmap(scaled_pixmap)
            else:
                self.image_label.setText(f"文件不存在: {file_path}")
                self.image_label.show()
    
    def zoom_out(self):
        """图片缩小功能"""
        if self.image_label.isVisible() and self.image_label.pixmap():
            # 确保文件路径使用正确的格式
            file_path = self.current_preview_file['path'].replace('/', '\\')  # 将正斜杠转换为反斜杠，适应Windows系统
            if os.path.exists(file_path):
                if self.current_scale > 0.1:
                    self.current_scale -= 0.1
                    original_pixmap = QPixmap(file_path)
                    scaled_pixmap = original_pixmap.scaled(
                        original_pixmap.width() * self.current_scale,
                        original_pixmap.height() * self.current_scale,
                        Qt.AspectRatioMode.KeepAspectRatio,
                        Qt.TransformationMode.SmoothTransformation
                    )
                    self.image_label.setPixmap(scaled_pixmap)
            else:
                self.image_label.setText(f"文件不存在: {file_path}")
                self.image_label.show()
    
    def rotate_image(self):
        """图片旋转功能"""
        if self.image_label.isVisible() and self.image_label.pixmap():
            # 确保文件路径使用正确的格式
            file_path = self.current_preview_file['path'].replace('/', '\\')  # 将正斜杠转换为反斜杠，适应Windows系统
            if os.path.exists(file_path):
                self.current_rotation += 90
                if self.current_rotation >= 360:
                    self.current_rotation = 0
                
                original_pixmap = QPixmap(file_path)
                transform = QTransform().rotate(self.current_rotation)
                rotated_pixmap = original_pixmap.transformed(transform, Qt.TransformationMode.SmoothTransformation)
                self.image_label.setPixmap(rotated_pixmap)
            else:
                self.image_label.setText(f"文件不存在: {file_path}")
                self.image_label.show()
    
    def play_pause_video(self):
        """视频播放/暂停功能"""
        if self.video_widget.isVisible():
            from PyQt6.QtMultimedia import QMediaPlayer
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
                # 确保文件路径使用正确的格式
                file_path = file_info['path'].replace('/', '\\')
                if os.path.exists(file_path):
                    # 隐藏图片标签，显示视频播放器
                    self.image_label.hide()
                    self.video_widget.show()
                    # 加载视频
                    from PyQt6.QtCore import QUrl
                    self.media_player.setSource(QUrl.fromLocalFile(file_path))
                    # 开始播放
                    self.media_player.play()
                    self.play_pause_btn.setText("暂停")
    
    def on_volume_change(self, value):
        """音量控制功能"""
        volume = value / 100.0
        self.audio_output.setVolume(volume)
    
    def locate_file_from_preview(self):
        """从预览窗口定位到文件所在文件夹"""
        if hasattr(self, 'current_preview_file') and self.current_preview_file:
            # 确保文件路径使用正确的格式
            file_path = self.current_preview_file['path'].replace('/', '\\')  # 将正斜杠转换为反斜杠，适应Windows系统
            if os.path.exists(file_path):
                os.startfile(os.path.dirname(file_path))
            else:
                from PyQt6.QtWidgets import QMessageBox
                QMessageBox.warning(self, "错误", f"文件不存在: {file_path}")
        else:
            from PyQt6.QtWidgets import QMessageBox
            QMessageBox.warning(self, "提示", "没有可定位的文件")
