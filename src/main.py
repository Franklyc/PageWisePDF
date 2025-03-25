import sys
import os
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                            QLabel, QPushButton, QFileDialog, QSpinBox, QComboBox, 
                            QProgressBar, QTextEdit, QLineEdit, QTabWidget, QCheckBox,
                            QGroupBox, QFormLayout, QMessageBox, QSplitter)
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QSettings
from PyQt5.QtGui import QIcon, QFont

from pdf_processor import PDFProcessor
from settings import SettingsDialog

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("PageWisePDF - PDF OCR and Processing Tool")
        self.setMinimumSize(800, 600)
        
        # Initialize settings
        self.settings = QSettings("PageWisePDF", "PageWisePDF")
        self.load_settings()
        
        # Initialize UI
        self.init_ui()
        
        # Initialize PDF processor
        self.pdf_processor = None
        self.processing_thread = None
        
        # Set default output directory
        self.set_default_output_dir()
    
    def load_settings(self):
        # Default settings
        self.api_key = self.settings.value("api_key", "")
        self.api_endpoint = self.settings.value("api_endpoint", "https://api.openai.com/v1/chat/completions")
        self.model_name = self.settings.value("model_name", "gpt-4-vision-preview")
        self.concurrent_calls = int(self.settings.value("concurrent_calls", 1))
        self.pages_per_call = int(self.settings.value("pages_per_call", 1))
        self.language = self.settings.value("language", "English")
        self.api_call_interval = float(self.settings.value("api_call_interval", 0.0))
    
    def save_settings(self):
        self.settings.setValue("api_key", self.api_key)
        self.settings.setValue("api_endpoint", self.api_endpoint)
        self.settings.setValue("model_name", self.model_name)
        self.settings.setValue("concurrent_calls", self.concurrent_calls)
        self.settings.setValue("pages_per_call", self.pages_per_call)
        self.settings.setValue("language", self.language)
        self.settings.setValue("api_call_interval", self.api_call_interval)
    
    def set_default_output_dir(self):
        # Set default output directory to project folder/output
        project_dir = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))
        default_output_dir = os.path.join(project_dir, "output")
        
        # Create the directory if it doesn't exist
        if not os.path.exists(default_output_dir):
            try:
                os.makedirs(default_output_dir)
                self.log(self.tr("Created default output directory") if self.language == "English" else "已创建默认输出目录")
            except Exception as e:
                self.log(self.tr(f"Failed to create output directory: {str(e)}") 
                       if self.language == "English" 
                       else f"创建输出目录失败：{str(e)}")
        
        # Set as default in the UI when init_ui is called
        self.default_output_dir = default_output_dir
    
    def init_ui(self):
        # Main widget and layout
        main_widget = QWidget()
        main_layout = QVBoxLayout(main_widget)
        
        # Create file selection section
        file_group = QGroupBox(self.tr("PDF Selection") if self.language == "English" else "PDF 选择")
        file_layout = QHBoxLayout()
        
        self.file_path_edit = QLineEdit()
        self.file_path_edit.setReadOnly(True)
        self.file_path_edit.setPlaceholderText(self.tr("Select a PDF file...") if self.language == "English" else "选择 PDF 文件...")
        
        browse_button = QPushButton(self.tr("Browse") if self.language == "English" else "浏览")
        browse_button.clicked.connect(self.browse_pdf)
        
        file_layout.addWidget(self.file_path_edit, 7)
        file_layout.addWidget(browse_button, 1)
        file_group.setLayout(file_layout)
        
        # Create output directory selection
        output_group = QGroupBox(self.tr("Output Directory") if self.language == "English" else "输出目录")
        output_layout = QHBoxLayout()
        
        self.output_path_edit = QLineEdit()
        self.output_path_edit.setReadOnly(True)
        
        # Set default output directory text
        if hasattr(self, 'default_output_dir') and self.default_output_dir:
            self.output_path_edit.setText(self.default_output_dir)
        else:
            self.output_path_edit.setPlaceholderText(self.tr("Select output directory...") if self.language == "English" else "选择输出目录...")
        
        output_button = QPushButton(self.tr("Browse") if self.language == "English" else "浏览")
        output_button.clicked.connect(self.browse_output_dir)
        
        output_layout.addWidget(self.output_path_edit, 7)
        output_layout.addWidget(output_button, 1)
        output_group.setLayout(output_layout)
        
        # Create processing options
        options_group = QGroupBox(self.tr("Processing Options") if self.language == "English" else "处理选项")
        options_layout = QFormLayout()
        
        # Processing mode
        self.mode_combo = QComboBox()
        extraction_mode = self.tr("Full Text Extraction") if self.language == "English" else "完整文本提取"
        summary_mode = self.tr("Summary Mode") if self.language == "English" else "摘要模式"
        self.mode_combo.addItems([extraction_mode, summary_mode])
        options_layout.addRow(self.tr("Mode:") if self.language == "English" else "模式:", self.mode_combo)
        
        # Page range
        page_range_layout = QHBoxLayout()
        self.process_all_pages = QCheckBox(self.tr("Process all pages") if self.language == "English" else "处理所有页面")
        self.process_all_pages.setChecked(True)
        self.process_all_pages.stateChanged.connect(self.toggle_page_range)
        
        self.start_page_spin = QSpinBox()
        self.start_page_spin.setMinimum(1)
        self.start_page_spin.setEnabled(False)
        self.end_page_spin = QSpinBox()
        self.end_page_spin.setMinimum(1)
        self.end_page_spin.setEnabled(False)
        
        page_range_layout.addWidget(self.process_all_pages)
        page_range_layout.addWidget(QLabel(self.tr("From:") if self.language == "English" else "从:"))
        page_range_layout.addWidget(self.start_page_spin)
        page_range_layout.addWidget(QLabel(self.tr("To:") if self.language == "English" else "到:"))
        page_range_layout.addWidget(self.end_page_spin)
        
        options_layout.addRow("", QWidget())  # Spacer
        options_layout.addRow(self.tr("Page Range:") if self.language == "English" else "页面范围:", page_range_layout)
        
        # Settings button
        settings_button = QPushButton(self.tr("API Settings") if self.language == "English" else "API 设置")
        settings_button.clicked.connect(self.open_settings)
        options_layout.addRow("", settings_button)
        
        options_group.setLayout(options_layout)
        
        # Create progress section
        progress_group = QGroupBox(self.tr("Progress") if self.language == "English" else "进度")
        progress_layout = QVBoxLayout()
        
        self.status_label = QLabel(self.tr("Ready") if self.language == "English" else "就绪")
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        
        progress_layout.addWidget(self.status_label)
        progress_layout.addWidget(self.progress_bar)
        progress_group.setLayout(progress_layout)
        
        # Create log section
        log_group = QGroupBox(self.tr("Log") if self.language == "English" else "日志")
        log_layout = QVBoxLayout()
        
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        
        log_layout.addWidget(self.log_text)
        log_group.setLayout(log_layout)
        
        # Create buttons
        button_layout = QHBoxLayout()
        
        self.start_button = QPushButton(self.tr("Start Processing") if self.language == "English" else "开始处理")
        self.start_button.setEnabled(False)
        self.start_button.clicked.connect(self.start_processing)
        
        self.cancel_button = QPushButton(self.tr("Cancel") if self.language == "English" else "取消")
        self.cancel_button.setEnabled(False)
        self.cancel_button.clicked.connect(self.cancel_processing)
        
        language_button = QPushButton(self.tr("Switch to Chinese") if self.language == "English" else "切换到英文")
        language_button.clicked.connect(self.toggle_language)
        
        button_layout.addWidget(self.start_button)
        button_layout.addWidget(self.cancel_button)
        button_layout.addWidget(language_button)
        
        # Add all components to main layout
        main_layout.addWidget(file_group)
        main_layout.addWidget(output_group)
        main_layout.addWidget(options_group)
        main_layout.addWidget(progress_group)
        main_layout.addWidget(log_group, 1)  # Give log more space
        main_layout.addLayout(button_layout)
        
        self.setCentralWidget(main_widget)
    
    def toggle_language(self):
        if self.language == "English":
            self.language = "Chinese"
        else:
            self.language = "English"
        
        self.save_settings()
        QMessageBox.information(
            self, 
            self.tr("Language Changed") if self.language == "English" else "语言已更改",
            self.tr("Please restart the application for the language change to take effect.") 
            if self.language == "English" 
            else "请重启应用程序以使语言更改生效。"
        )
    
    def toggle_page_range(self, state):
        self.start_page_spin.setEnabled(not state)
        self.end_page_spin.setEnabled(not state)
    
    def browse_pdf(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, 
            self.tr("Select PDF File") if self.language == "English" else "选择 PDF 文件", 
            "", 
            self.tr("PDF Files (*.pdf)") if self.language == "English" else "PDF 文件 (*.pdf)"
        )
        
        if file_path:
            self.file_path_edit.setText(file_path)
            self.update_start_button()
    
    def browse_output_dir(self):
        dir_path = QFileDialog.getExistingDirectory(
            self, 
            self.tr("Select Output Directory") if self.language == "English" else "选择输出目录"
        )
        
        if dir_path:
            self.output_path_edit.setText(dir_path)
            self.update_start_button()
    
    def update_start_button(self):
        self.start_button.setEnabled(
            bool(self.file_path_edit.text()) and 
            bool(self.output_path_edit.text())
        )
    
    def open_settings(self):
        settings_dialog = SettingsDialog(self)
        if settings_dialog.exec_():
            # Update settings if dialog was accepted
            self.api_key = settings_dialog.api_key_edit.text()
            self.api_endpoint = settings_dialog.endpoint_edit.text()
            self.model_name = settings_dialog.model_combo.currentText()
            self.concurrent_calls = settings_dialog.concurrent_spin.value()
            self.pages_per_call = settings_dialog.pages_per_call_spin.value()
            self.api_call_interval = settings_dialog.interval_spin.value()
            self.save_settings()
    
    def start_processing(self):
        if not self.api_key:
            QMessageBox.warning(
                self, 
                self.tr("API Key Required") if self.language == "English" else "需要 API 密钥",
                self.tr("Please set your OpenAI API key in the settings.") 
                if self.language == "English" 
                else "请在设置中设置您的 OpenAI API 密钥。"
            )
            return
        
        # Get processing parameters
        pdf_path = self.file_path_edit.text()
        output_dir = self.output_path_edit.text()
        is_summary_mode = self.mode_combo.currentIndex() == 1
        
        # Get page range
        if self.process_all_pages.isChecked():
            start_page = None
            end_page = None
        else:
            start_page = self.start_page_spin.value()
            end_page = self.end_page_spin.value()
        
        # Create PDF processor
        self.pdf_processor = PDFProcessor(
            pdf_path=pdf_path,
            output_dir=output_dir,
            api_key=self.api_key,
            api_endpoint=self.api_endpoint,
            model_name=self.model_name,
            is_summary_mode=is_summary_mode,
            start_page=start_page,
            end_page=end_page,
            concurrent_calls=self.concurrent_calls,
            pages_per_call=self.pages_per_call,
            language=self.language,
            api_call_interval=self.api_call_interval
        )
        
        # Create and start processing thread
        self.processing_thread = ProcessingThread(self.pdf_processor)
        self.processing_thread.status_update.connect(self.update_status)
        self.processing_thread.progress_update.connect(self.update_progress)
        self.processing_thread.log_update.connect(self.update_log)
        self.processing_thread.finished.connect(self.processing_finished)
        
        # Update UI
        self.start_button.setEnabled(False)
        self.cancel_button.setEnabled(True)
        self.progress_bar.setValue(0)
        
        # Start processing
        self.processing_thread.start()
        
        self.log(self.tr("Processing started...") if self.language == "English" else "处理已开始...")
    
    def cancel_processing(self):
        if self.processing_thread and self.processing_thread.isRunning():
            self.pdf_processor.cancel()
            self.log(self.tr("Cancelling...") if self.language == "English" else "正在取消...")
            self.cancel_button.setEnabled(False)
    
    def update_status(self, status):
        self.status_label.setText(status)
    
    def update_progress(self, value):
        self.progress_bar.setValue(value)
    
    def update_log(self, message):
        self.log(message)
    
    def log(self, message):
        self.log_text.append(message)
        # Scroll to bottom
        self.log_text.verticalScrollBar().setValue(self.log_text.verticalScrollBar().maximum())
    
    def processing_finished(self):
        self.start_button.setEnabled(True)
        self.cancel_button.setEnabled(False)
        self.log(self.tr("Processing completed.") if self.language == "English" else "处理完成。")
        
        # Show completed dialog
        QMessageBox.information(
            self, 
            self.tr("Processing Complete") if self.language == "English" else "处理完成",
            self.tr("PDF processing has been completed.") if self.language == "English" else "PDF 处理已完成。"
        )


class ProcessingThread(QThread):
    status_update = pyqtSignal(str)
    progress_update = pyqtSignal(int)
    log_update = pyqtSignal(str)
    
    def __init__(self, pdf_processor):
        super().__init__()
        self.pdf_processor = pdf_processor
        
        # Connect signals from processor
        self.pdf_processor.status_update.connect(self.on_status_update)
        self.pdf_processor.progress_update.connect(self.on_progress_update)
        self.pdf_processor.log_update.connect(self.on_log_update)
    
    def run(self):
        try:
            self.pdf_processor.process()
        except Exception as e:
            self.log_update.emit(f"Error: {str(e)}")
    
    def on_status_update(self, status):
        self.status_update.emit(status)
    
    def on_progress_update(self, value):
        self.progress_update.emit(value)
    
    def on_log_update(self, message):
        self.log_update.emit(message)


def main():
    app = QApplication(sys.argv)
    app.setStyle('Fusion')  # Use Fusion style for consistent look
    
    window = MainWindow()
    window.show()
    
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()