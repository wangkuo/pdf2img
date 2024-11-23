import sys
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                            QHBoxLayout, QPushButton, QLabel, QFileDialog, 
                            QListWidget, QComboBox, QProgressBar, QScrollArea)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtGui import QPixmap, QImage
from pdf2image import convert_from_path
import fitz  # PyMuPDF
from PIL import Image
import io
import os

class PDFConverter(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("PDF转图片工具")
        self.setMinimumSize(800, 600)
        
        # 初始化变量
        self.current_pdf = None
        self.current_page = 0
        self.total_pages = 0
        
        # 创建主窗口部件
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        layout = QHBoxLayout(main_widget)
        
        # 左侧面板
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        
        # 文件列表
        self.file_list = QListWidget()
        left_layout.addWidget(QLabel("待转换文件列表："))
        left_layout.addWidget(self.file_list)
        
        # 按钮区域
        button_layout = QHBoxLayout()
        self.add_file_btn = QPushButton("添加文件")
        self.add_files_btn = QPushButton("批量添加")
        self.remove_file_btn = QPushButton("删除所选")
        button_layout.addWidget(self.add_file_btn)
        button_layout.addWidget(self.add_files_btn)
        button_layout.addWidget(self.remove_file_btn)
        left_layout.addLayout(button_layout)
        
        # 格式选择
        format_layout = QHBoxLayout()
        format_layout.addWidget(QLabel("输出格式："))
        self.format_combo = QComboBox()
        self.format_combo.addItems(["PNG", "JPG"])
        format_layout.addWidget(self.format_combo)
        left_layout.addLayout(format_layout)
        
        # 转换按钮和进度条
        self.convert_btn = QPushButton("开始转换")
        self.progress_bar = QProgressBar()
        left_layout.addWidget(self.convert_btn)
        left_layout.addWidget(self.progress_bar)
        
        # 右侧预览区
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        
        # 预览控制按钮
        preview_controls = QHBoxLayout()
        self.prev_btn = QPushButton("上一页")
        self.next_btn = QPushButton("下一页")
        self.page_label = QLabel("0/0")
        preview_controls.addWidget(self.prev_btn)
        preview_controls.addWidget(self.page_label)
        preview_controls.addWidget(self.next_btn)
        right_layout.addLayout(preview_controls)
        
        # 滚动预览区
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setMinimumHeight(400)
        self.preview_label = QLabel("PDF预览区")
        self.preview_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        scroll_area.setWidget(self.preview_label)
        right_layout.addWidget(scroll_area)
        
        # 添加左右面板到主布局
        layout.addWidget(left_panel, 1)
        layout.addWidget(right_panel, 2)
        
        # 连接信号
        self.add_file_btn.clicked.connect(self.add_file)
        self.add_files_btn.clicked.connect(self.add_files)
        self.remove_file_btn.clicked.connect(self.remove_file)
        self.convert_btn.clicked.connect(self.start_conversion)
        self.prev_btn.clicked.connect(self.prev_page)
        self.next_btn.clicked.connect(self.next_page)
        self.file_list.itemClicked.connect(self.preview_pdf)
        
        # 初始化按钮状态
        self.prev_btn.setEnabled(False)
        self.next_btn.setEnabled(False)
        
    def add_file(self):
        file_name, _ = QFileDialog.getOpenFileName(
            self, "选择PDF文件", "", "PDF文件 (*.pdf)")
        if file_name:
            self.file_list.addItem(file_name)
            # 自动预览第一个添加的文件
            if self.file_list.count() == 1:
                self.preview_pdf(self.file_list.item(0))
            
    def add_files(self):
        file_names, _ = QFileDialog.getOpenFileNames(
            self, "选择PDF文件", "", "PDF文件 (*.pdf)")
        for file_name in file_names:
            self.file_list.addItem(file_name)
            
    def remove_file(self):
        for item in self.file_list.selectedItems():
            self.file_list.takeItem(self.file_list.row(item))
            
    def preview_pdf(self, item):
        try:
            pdf_path = item.text()
            self.current_pdf = fitz.open(pdf_path)
            self.total_pages = len(self.current_pdf)
            self.current_page = 0
            self.update_preview()
            
            # 更新页面控制按钮状态
            self.prev_btn.setEnabled(False)
            self.next_btn.setEnabled(self.total_pages > 1)
            self.page_label.setText(f"1/{self.total_pages}")
        except Exception as e:
            self.preview_label.setText(f"预览失败: {str(e)}")
            
    def update_preview(self):
        if self.current_pdf is None:
            return
            
        # 获取当前页面
        page = self.current_pdf[self.current_page]
        
        # 将页面渲染为图像
        pix = page.get_pixmap(matrix=fitz.Matrix(1.5, 1.5))
        
        # 转换为QImage
        img = QImage(pix.samples, pix.width, pix.height, pix.stride, QImage.Format.Format_RGB888)
        
        # 创建QPixmap并设置到预览标签
        pixmap = QPixmap.fromImage(img)
        
        # 调整图像大小以适应预览区域
        scaled_pixmap = pixmap.scaled(self.preview_label.size(), 
                                    Qt.AspectRatioMode.KeepAspectRatio, 
                                    Qt.TransformationMode.SmoothTransformation)
        
        self.preview_label.setPixmap(scaled_pixmap)
        self.page_label.setText(f"{self.current_page + 1}/{self.total_pages}")
        
    def prev_page(self):
        if self.current_page > 0:
            self.current_page -= 1
            self.update_preview()
            self.next_btn.setEnabled(True)
            self.prev_btn.setEnabled(self.current_page > 0)
            
    def next_page(self):
        if self.current_page < self.total_pages - 1:
            self.current_page += 1
            self.update_preview()
            self.prev_btn.setEnabled(True)
            self.next_btn.setEnabled(self.current_page < self.total_pages - 1)
            
    def resizeEvent(self, event):
        super().resizeEvent(event)
        if hasattr(self, 'current_pdf') and self.current_pdf:
            self.update_preview()
            
    def start_conversion(self):
        # 这里将实现转换功能
        self.convert_btn.setEnabled(False)
        self.progress_bar.setMaximum(self.file_list.count())
        self.progress_bar.setValue(0)
        
        for i in range(self.file_list.count()):
            pdf_path = self.file_list.item(i).text()
            output_format = self.format_combo.currentText().lower()
            self.convert_pdf(pdf_path, output_format)
            self.progress_bar.setValue(i + 1)
            
        self.convert_btn.setEnabled(True)
        
    def convert_pdf(self, pdf_path, output_format):
        try:
            images = convert_from_path(pdf_path)
            base_name = os.path.splitext(pdf_path)[0]
            
            for i, image in enumerate(images):
                if len(images) == 1:
                    output_path = f"{base_name}.{output_format}"
                else:
                    output_path = f"{base_name}_{i+1}.{output_format}"
                image.save(output_path, output_format.upper())
        except Exception as e:
            print(f"转换错误: {str(e)}")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = PDFConverter()
    window.show()
    sys.exit(app.exec()) 