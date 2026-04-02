from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem, 
    QPushButton, QLabel, QHeaderView, QCheckBox, QMessageBox
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QAction
import json
import os
import time

class HistoryDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("扫描历史记录")
        self.setGeometry(300, 200, 800, 500)
        
        # 历史记录文件路径
        self.history_file = os.path.join(os.path.expanduser("~"), ".mediafinder_history.json")
        
        # 加载历史记录
        self.history_records = self.load_history()
        
        # 初始化UI
        self.init_ui()
    
    def init_ui(self):
        # 设置对话框样式
        self.setStyleSheet("""
            QDialog {
                background-color: #1E1E1E;
                color: #FFFFFF;
            }
            QLabel {
                color: #CCCCCC;
            }
            QTableWidget {
                background-color: #1E1E1E;
                color: #FFFFFF;
                border: 1px solid #3E3E42;
            }
            QTableWidget::item {
                padding: 4px;
            }
            QTableWidget::item:selected {
                background-color: #0E639C;
            }
            QTableWidget::header {
                background-color: #252526;
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
        """)
        
        layout = QVBoxLayout(self)
        
        # 标题
        title_label = QLabel("扫描历史记录")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_label.setStyleSheet("font-size: 16px; font-weight: bold;")
        layout.addWidget(title_label)
        
        # 历史记录表格
        self.history_table = QTableWidget()
        self.history_table.setColumnCount(5)
        self.history_table.setHorizontalHeaderLabels(["选择", "扫描时间", "扫描路径", "状态", "文件数"])
        
        # 设置表格列宽
        header = self.history_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        
        # 填充表格数据
        self.populate_table()
        
        layout.addWidget(self.history_table)
        
        # 按钮
        button_layout = QHBoxLayout()
        button_layout.setContentsMargins(10, 10, 10, 10)
        button_layout.setSpacing(10)
        
        rescan_btn = QPushButton("重新扫描")
        rescan_btn.clicked.connect(self.rescan_selected)
        button_layout.addWidget(rescan_btn)
        
        delete_btn = QPushButton("删除记录")
        delete_btn.clicked.connect(self.delete_selected)
        button_layout.addWidget(delete_btn)
        
        export_btn = QPushButton("导出报告")
        export_btn.clicked.connect(self.export_report)
        button_layout.addWidget(export_btn)
        
        button_layout.addStretch()
        
        close_btn = QPushButton("关闭")
        close_btn.clicked.connect(self.accept)
        button_layout.addWidget(close_btn)
        
        layout.addLayout(button_layout)
    
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
        self.populate_table()
    
    def populate_table(self):
        """填充表格数据"""
        self.history_table.setRowCount(0)
        
        for i, record in enumerate(self.history_records):
            row = self.history_table.rowCount()
            self.history_table.insertRow(row)
            
            # 选择框
            checkbox = QCheckBox()
            self.history_table.setCellWidget(row, 0, checkbox)
            
            # 扫描时间
            timestamp = record.get("timestamp", 0)
            time_str = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(timestamp))
            self.history_table.setItem(row, 1, QTableWidgetItem(time_str))
            
            # 扫描路径
            path = record.get("path", "")
            self.history_table.setItem(row, 2, QTableWidgetItem(path))
            
            # 状态
            status = record.get("status", "")
            self.history_table.setItem(row, 3, QTableWidgetItem(status))
            
            # 文件数
            file_count = record.get("file_count", 0)
            self.history_table.setItem(row, 4, QTableWidgetItem(str(file_count)))
    
    def get_selected_records(self):
        """获取选中的记录"""
        selected = []
        for row in range(self.history_table.rowCount()):
            checkbox = self.history_table.cellWidget(row, 0)
            if checkbox and checkbox.isChecked():
                selected.append(self.history_records[row])
        return selected
    
    def rescan_selected(self):
        """重新扫描选中的记录"""
        selected = self.get_selected_records()
        if not selected:
            QMessageBox.information(self, "提示", "请选择要重新扫描的记录")
            return
        
        # 这里应该触发重新扫描的逻辑
        # 为了演示，我们只是显示一个消息
        for record in selected:
            path = record.get("path", "")
            QMessageBox.information(self, "重新扫描", f"将重新扫描路径: {path}")
    
    def delete_selected(self):
        """删除选中的记录"""
        selected_rows = []
        for row in range(self.history_table.rowCount()):
            checkbox = self.history_table.cellWidget(row, 0)
            if checkbox and checkbox.isChecked():
                selected_rows.append(row)
        
        if not selected_rows:
            QMessageBox.information(self, "提示", "请选择要删除的记录")
            return
        
        # 按行号从大到小删除，避免索引变化
        for row in sorted(selected_rows, reverse=True):
            del self.history_records[row]
        
        self.save_history()
        self.populate_table()
        QMessageBox.information(self, "成功", f"已删除 {len(selected_rows)} 条记录")
    
    def export_report(self):
        """导出历史记录报告"""
        selected = self.get_selected_records()
        if not selected:
            QMessageBox.information(self, "提示", "请选择要导出的记录")
            return
        
        # 生成报告内容
        report = "扫描历史记录报告\n"
        report += "=" * 80 + "\n"
        
        for record in selected:
            timestamp = record.get("timestamp", 0)
            time_str = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(timestamp))
            path = record.get("path", "")
            status = record.get("status", "")
            file_count = record.get("file_count", 0)
            elapsed = record.get("elapsed", "0s")
            
            report += f"时间: {time_str}\n"
            report += f"路径: {path}\n"
            report += f"状态: {status}\n"
            report += f"文件数: {file_count}\n"
            report += f"耗时: {elapsed}\n"
            report += "-" * 80 + "\n"
        
        # 保存报告文件
        report_file = os.path.join(os.path.expanduser("~"), f"scan_history_report_{int(time.time())}.txt")
        try:
            with open(report_file, 'w', encoding='utf-8') as f:
                f.write(report)
            QMessageBox.information(self, "成功", f"报告已导出到: {report_file}")
        except Exception as e:
            QMessageBox.critical(self, "错误", f"导出报告失败: {e}")
