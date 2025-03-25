import sys
import os
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                            QLabel, QPushButton, QFileDialog, QSpinBox, QComboBox, 
                            QProgressBar, QTextEdit, QLineEdit, QTabWidget, QCheckBox,
                            QGroupBox, QFormLayout, QMessageBox, QSplitter, QFrame,
                            QScrollArea, QToolButton, QAction, QMenu, QStyle)
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QSettings, QSize, QEvent
from PyQt5.QtGui import QIcon, QFont, QPalette, QColor, QPixmap, QCursor, QFontDatabase

from pdf_processor import PDFProcessor
from settings import SettingsDialog

class ThemeColors:
    """Theme colors for the application"""
    PRIMARY = QColor(52, 152, 219)  # Blue
    SECONDARY = QColor(41, 128, 185)
    ACCENT = QColor(243, 156, 18)  # Orange
    BACKGROUND = QColor(248, 249, 250)
    CARD_BG = QColor(255, 255, 255)
    TEXT = QColor(44, 62, 80)
    LIGHT_TEXT = QColor(127, 140, 141)
    SUCCESS = QColor(46, 204, 113)
    WARNING = QColor(241, 196, 15)
    ERROR = QColor(231, 76, 60)

class StyledButton(QPushButton):
    """Custom styled button with hover effects"""
    
    def __init__(self, text, parent=None, primary=True):
        super().__init__(text, parent)
        self.primary = primary
        self.setFixedHeight(36)
        self.setCursor(QCursor(Qt.PointingHandCursor))
        self.updateStyle()
    
    def updateStyle(self):
        if self.primary:
            bg_color = ThemeColors.PRIMARY.name()
            hover_color = ThemeColors.SECONDARY.name()
            text_color = "white"
        else:
            bg_color = "white"
            hover_color = "#f8f9fa"
            text_color = ThemeColors.TEXT.name()
        
        self.setStyleSheet(f"""
            QPushButton {{
                background-color: {bg_color};
                color: {text_color};
                border: none;
                border-radius: 4px;
                padding: 8px 16px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: {hover_color};
            }}
            QPushButton:pressed {{
                padding-left: 18px;
                padding-top: 10px;
            }}
            QPushButton:disabled {{
                background-color: #cccccc;
                color: #666666;
            }}
        """)

class StyledProgressBar(QProgressBar):
    """Custom styled progress bar"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(12)
        self.setTextVisible(False)
        self.setStyleSheet(f"""
            QProgressBar {{
                border: none;
                border-radius: 6px;
                background-color: #f0f0f0;
                text-align: center;
            }}
            QProgressBar::chunk {{
                background-color: {ThemeColors.PRIMARY.name()};
                border-radius: 6px;
            }}
        """)

class CardFrame(QFrame):
    """Card-like frame with shadow effect"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFrameShape(QFrame.StyledPanel)
        self.setAutoFillBackground(True)
        palette = self.palette()
        palette.setColor(QPalette.Window, ThemeColors.CARD_BG)
        self.setPalette(palette)
        self.setStyleSheet("""
            CardFrame {
                border-radius: 8px;
                background-color: white;
                border: 1px solid #e0e0e0;
            }
        """)

class StyledComboBox(QComboBox):
    """Custom styled combobox with modern look"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet("""
            QComboBox {
                border: 1px solid #ccc;
                border-radius: 4px;
                padding: 5px 10px;
                min-height: 28px;
                background-color: white;
            }
            QComboBox:hover {
                border: 1px solid #aaa;
            }
            QComboBox:focus {
                border: 1px solid #3498db;
            }
            QComboBox::drop-down {
                subcontrol-origin: padding;
                subcontrol-position: top right;
                width: 20px;
                border-left: none;
            }
        """)

class StyledLineEdit(QLineEdit):
    """Custom styled line edit with modern look"""
    
    def __init__(self, parent=None, read_only=False):
        super().__init__(parent)
        self.setStyleSheet("""
            QLineEdit {
                border: 1px solid #ccc;
                border-radius: 4px;
                padding: 5px 10px;
                background-color: white;
                min-height: 28px;
            }
            QLineEdit:hover {
                border: 1px solid #aaa;
            }
            QLineEdit:focus {
                border: 1px solid #3498db;
            }
            QLineEdit:disabled {
                background-color: #f5f5f5;
                color: #888;
            }
        """)
        
        if read_only:
            self.setReadOnly(True)
            
class StyledSpinBox(QSpinBox):
    """Custom styled spin box with modern look"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet("""
            QSpinBox {
                border: 1px solid #ccc;
                border-radius: 4px;
                padding: 5px 10px;
                background-color: white;
                min-height: 28px;
            }
            QSpinBox:hover {
                border: 1px solid #aaa;
            }
            QSpinBox:focus {
                border: 1px solid #3498db;
            }
            QSpinBox::up-button, QSpinBox::down-button {
                subcontrol-origin: padding;
                width: 20px;
                border-radius: 2px;
                background-color: #f5f5f5;
            }
            QSpinBox::up-button:hover, QSpinBox::down-button:hover {
                background-color: #e0e0e0;
            }
        """)

class StyledGroupBox(QGroupBox):
    """Custom styled group box with modern look"""
    
    def __init__(self, title, parent=None):
        super().__init__(title, parent)
        self.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                border: 1px solid #ccc;
                border-radius: 5px;
                margin-top: 1.5ex;
                padding-top: 10px;
                background-color: white;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                subcontrol-position: top left;
                padding: 0 5px;
                color: #2c3e50;
            }
        """)

class AppHeader(QFrame):
    """App header with logo, title and theme toggle"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(80)
        self.setStyleSheet("""
            AppHeader {
                background-color: #2c3e50;
                border-bottom: 1px solid #34495e;
            }
        """)
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(20, 10, 20, 10)
        
        # App title and subtitle
        title_layout = QVBoxLayout()
        app_title = QLabel("PageWisePDF")
        app_title.setStyleSheet("color: white; font-size: 24px; font-weight: bold;")
        
        # Store subtitle label as instance variable
        self.app_subtitle = QLabel("AI-Powered PDF Processing")
        self.app_subtitle.setStyleSheet("color: #bdc3c7; font-size: 14px;")
        
        title_layout.addWidget(app_title)
        title_layout.addWidget(self.app_subtitle)
        
        # Add version on the right
        version_label = QLabel("v1.0")
        version_label.setStyleSheet("color: #7f8c8d; font-size: 12px;")
        version_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        
        layout.addLayout(title_layout)
        layout.addStretch(1)
        layout.addWidget(version_label)
    
    def set_language(self, language):
        """Update header text based on language"""
        self.app_subtitle.setText("AI驱动的PDF处理工具" if language == "Chinese" else "AI-Powered PDF Processing")

class FooterStatusBar(QFrame):
    """Custom footer status bar"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(30)
        self.setStyleSheet("""
            FooterStatusBar {
                background-color: #f5f5f5;
                border-top: 1px solid #dcdcdc;
            }
        """)
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 0, 10, 0)
        
        self.status_label = QLabel("Ready")
        self.status_label.setStyleSheet("color: #555;")
        
        layout.addWidget(self.status_label)
        layout.addStretch(1)
        
    def update_status(self, text):
        self.status_label.setText(text)

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("PageWisePDF - PDF OCR and Processing Tool")
        self.setMinimumSize(950, 750)
        
        # Set application style and font
        self.setup_app_style()
        
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
    
    def setup_app_style(self):
        """Setup application style with custom fonts and colors"""
        # Set application palette
        palette = QPalette()
        palette.setColor(QPalette.Window, ThemeColors.BACKGROUND)
        palette.setColor(QPalette.WindowText, ThemeColors.TEXT)
        palette.setColor(QPalette.Base, QColor(255, 255, 255))
        palette.setColor(QPalette.Text, ThemeColors.TEXT)
        palette.setColor(QPalette.Button, ThemeColors.CARD_BG)
        palette.setColor(QPalette.ButtonText, ThemeColors.TEXT)
        palette.setColor(QPalette.Highlight, ThemeColors.PRIMARY)
        palette.setColor(QPalette.HighlightedText, QColor(255, 255, 255))
        self.setPalette(palette)
        
        # Set font
        default_font = QFont()
        default_font.setPointSize(10)
        self.setFont(default_font)
        
        # Set application stylesheet
        self.setStyleSheet("""
            QMainWindow {
                background-color: #f8f9fa;
            }
            QScrollBar:vertical {
                border: none;
                background: #f0f0f0;
                width: 10px;
                margin: 0px;
            }
            QScrollBar::handle:vertical {
                background: #c0c0c0;
                min-height: 20px;
                border-radius: 5px;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0px;
            }
            QScrollBar:horizontal {
                border: none;
                background: #f0f0f0;
                height: 10px;
                margin: 0px;
            }
            QScrollBar::handle:horizontal {
                background: #c0c0c0;
                min-width: 20px;
                border-radius: 5px;
            }
            QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {
                width: 0px;
            }
            QToolTip {
                border: 1px solid #ccc;
                background-color: #f8f9fa;
                color: #333;
                padding: 5px;
            }
        """)
    
    def load_settings(self):
        # Default settings
        self.api_key = self.settings.value("api_key", "")
        self.api_endpoint = self.settings.value("api_endpoint", "https://api.openai.com/v1/chat/completions")
        self.model_name = self.settings.value("model_name", "gpt-4-vision-preview")
        self.concurrent_calls = int(self.settings.value("concurrent_calls", 1))
        self.pages_per_call = int(self.settings.value("pages_per_call", 1))
        self.language = self.settings.value("language", "English")
        self.api_call_interval = float(self.settings.value("api_call_interval", 0.0))
    
    def init_ui(self):
        # Create central widget with vertical layout
        central_widget = QWidget()
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # Create app header
        self.header = AppHeader()
        
        # Create main content widget
        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)
        content_layout.setContentsMargins(20, 20, 20, 20)
        content_layout.setSpacing(15)
        
        # Create a scroll area for the form content
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setFrameShape(QFrame.NoFrame)
        
        # Content container (used inside scroll area)
        form_container = QWidget()
        form_layout = QVBoxLayout(form_container)
        form_layout.setContentsMargins(5, 5, 5, 15)
        form_layout.setSpacing(15)
        
        # Create file selection section
        file_group = StyledGroupBox(self.tr("PDF Selection") if self.language == "English" else "PDF 选择")
        file_layout = QHBoxLayout()
        
        self.file_path_edit = StyledLineEdit(read_only=True)
        self.file_path_edit.setPlaceholderText(self.tr("Select a PDF file...") if self.language == "English" else "选择 PDF 文件...")
        
        browse_button = StyledButton(self.tr("Browse") if self.language == "English" else "浏览", primary=False)
        browse_button.clicked.connect(self.browse_pdf)
        browse_button.setIcon(self.style().standardIcon(QStyle.SP_DialogOpenButton))
        
        file_layout.addWidget(self.file_path_edit, 7)
        file_layout.addWidget(browse_button, 1)
        file_group.setLayout(file_layout)
        
        # Create output directory selection
        output_group = StyledGroupBox(self.tr("Output Directory") if self.language == "English" else "输出目录")
        output_layout = QHBoxLayout()
        
        self.output_path_edit = StyledLineEdit(read_only=True)
        
        # Set default output directory text
        if hasattr(self, 'default_output_dir') and self.default_output_dir:
            self.output_path_edit.setText(self.default_output_dir)
        else:
            self.output_path_edit.setPlaceholderText(self.tr("Select output directory...") if self.language == "English" else "选择输出目录...")
        
        output_button = StyledButton(self.tr("Browse") if self.language == "English" else "浏览", primary=False)
        output_button.clicked.connect(self.browse_output_dir)
        output_button.setIcon(self.style().standardIcon(QStyle.SP_DialogOpenButton))
        
        output_layout.addWidget(self.output_path_edit, 7)
        output_layout.addWidget(output_button, 1)
        output_group.setLayout(output_layout)
        
        # Create processing options card
        options_card = CardFrame()
        options_card_layout = QVBoxLayout(options_card)
        
        options_title = QLabel(self.tr("Processing Options") if self.language == "English" else "处理选项")
        options_title.setStyleSheet("font-weight: bold; font-size: 14px; color: #2c3e50; margin-bottom: 5px;")
        
        options_grid = QFormLayout()
        options_grid.setContentsMargins(10, 10, 10, 10)
        options_grid.setSpacing(15)
        
        # Processing mode
        self.mode_combo = StyledComboBox()
        extraction_mode = self.tr("Full Text Extraction") if self.language == "English" else "完整文本提取"
        summary_mode = self.tr("Summary Mode") if self.language == "English" else "摘要模式"
        self.mode_combo.addItems([extraction_mode, summary_mode])
        options_grid.addRow(self.tr("Mode:") if self.language == "English" else "模式:", self.mode_combo)
        
        # Language selection
        self.language_combo = StyledComboBox()
        self.language_combo.addItems(["English", "中文"])
        self.language_combo.setCurrentIndex(0 if self.language == "English" else 1)
        self.language_combo.currentIndexChanged.connect(self.on_language_change)
        options_grid.addRow(self.tr("Output Language:") if self.language == "English" else "输出语言:", self.language_combo)
        
        # Page range
        page_range_widget = QWidget()
        page_range_layout = QHBoxLayout(page_range_widget)
        page_range_layout.setContentsMargins(0, 0, 0, 0)
        
        self.process_all_pages = QCheckBox(self.tr("Process all pages") if self.language == "English" else "处理所有页面")
        self.process_all_pages.setChecked(True)
        self.process_all_pages.stateChanged.connect(self.toggle_page_range)
        
        self.start_page_spin = StyledSpinBox()
        self.start_page_spin.setMinimum(1)
        self.start_page_spin.setEnabled(False)
        
        self.end_page_spin = StyledSpinBox()
        self.end_page_spin.setMinimum(1)
        self.end_page_spin.setEnabled(False)
        
        page_range_layout.addWidget(self.process_all_pages)
        page_range_layout.addWidget(QLabel(self.tr("From:") if self.language == "English" else "从:"))
        page_range_layout.addWidget(self.start_page_spin)
        page_range_layout.addWidget(QLabel(self.tr("To:") if self.language == "English" else "到:"))
        page_range_layout.addWidget(self.end_page_spin)
        page_range_layout.addStretch()
        
        options_grid.addRow(self.tr("Page Range:") if self.language == "English" else "页面范围:", page_range_widget)
        
        # Settings button
        settings_button = StyledButton(self.tr("API Settings") if self.language == "English" else "API 设置", primary=False)
        settings_button.setIcon(self.style().standardIcon(QStyle.SP_FileDialogDetailedView))
        settings_button.clicked.connect(self.open_settings)
        
        # Add all options to card
        options_card_layout.addWidget(options_title)
        options_card_layout.addLayout(options_grid)
        options_card_layout.addSpacing(5)
        options_card_layout.addWidget(settings_button)
        
        # Create progress section
        progress_group = StyledGroupBox(self.tr("Progress") if self.language == "English" else "进度")
        progress_layout = QVBoxLayout()
        
        self.status_label = QLabel(self.tr("Ready") if self.language == "English" else "就绪")
        self.progress_bar = StyledProgressBar()
        
        progress_layout.addWidget(self.status_label)
        progress_layout.addWidget(self.progress_bar)
        progress_group.setLayout(progress_layout)
        
        # Create log section
        log_group = StyledGroupBox(self.tr("Log") if self.language == "English" else "日志")
        log_layout = QVBoxLayout()
        
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setStyleSheet("""
            QTextEdit {
                border: 1px solid #ccc;
                border-radius: 4px;
                background-color: white;
                padding: 5px;
                font-family: monospace;
            }
        """)
        
        # Add clear log button
        clear_log_button = QPushButton(self.tr("Clear Log") if self.language == "English" else "清除日志")
        clear_log_button.clicked.connect(self.clear_log)
        clear_log_button.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                border: none;
                color: #3498db;
                text-decoration: underline;
                text-align: right;
            }
            QPushButton:hover {
                color: #2980b9;
            }
        """)
        
        log_layout.addWidget(self.log_text)
        log_layout.addWidget(clear_log_button, 0, Qt.AlignRight)
        log_group.setLayout(log_layout)
        
        # Create buttons
        button_layout = QHBoxLayout()
        button_layout.setContentsMargins(0, 10, 0, 0)
        
        self.start_button = StyledButton(self.tr("Start Processing") if self.language == "English" else "开始处理")
        self.start_button.setEnabled(False)
        self.start_button.clicked.connect(self.start_processing)
        self.start_button.setIcon(self.style().standardIcon(QStyle.SP_MediaPlay))
        
        self.cancel_button = StyledButton(self.tr("Cancel") if self.language == "English" else "取消", primary=False)
        self.cancel_button.setEnabled(False)
        self.cancel_button.clicked.connect(self.cancel_processing)
        self.cancel_button.setIcon(self.style().standardIcon(QStyle.SP_MediaStop))
        
        button_layout.addStretch(1)
        button_layout.addWidget(self.start_button)
        button_layout.addWidget(self.cancel_button)
        
        # Add all components to form layout
        form_layout.addWidget(file_group)
        form_layout.addWidget(output_group)
        form_layout.addWidget(options_card)
        form_layout.addWidget(progress_group)
        form_layout.addWidget(log_group, 1)  # Give log more space
        form_layout.addLayout(button_layout)
        
        # Set up the scroll area
        scroll_area.setWidget(form_container)
        content_layout.addWidget(scroll_area)
        
        # Create footer status bar
        self.footer = FooterStatusBar()
        self.footer.update_status(self.tr("Ready") if self.language == "English" else "就绪")
        
        # Add all main sections to main layout
        main_layout.addWidget(self.header)
        main_layout.addWidget(content_widget, 1)  # 1 = stretch factor
        main_layout.addWidget(self.footer)
        
        self.setCentralWidget(central_widget)
        
        # Apply initial language
        self.update_ui_language()
    
    def on_language_change(self, index):
        """Handle language combobox changes"""
        language = "English" if index == 0 else "Chinese"
        if language != self.language:
            self.language = language
            self.save_settings()
            self.update_ui_language()
    
    def update_ui_language(self):
        """Update UI elements based on selected language"""
        # Update header
        self.header.set_language(self.language)
        
        # Update labels
        self.setWindowTitle("PageWisePDF - PDF OCR and Processing Tool" if self.language == "English" else "PageWisePDF - PDF OCR 和处理工具")
        
        # Will update other elements as needed
        
        # Update footer
        self.footer.update_status(self.tr("Ready") if self.language == "English" else "就绪")
        
        # Log the language change
        self.log(self.tr("Language changed to English") if self.language == "English" else "语言已更改为中文")
    
    def clear_log(self):
        """Clear the log text box"""
        self.log_text.clear()
        self.log(self.tr("Log cleared") if self.language == "English" else "日志已清除")
    
    def toggle_page_range(self, state):
        """Enable/disable page range spinners based on 'process all pages' checkbox"""
        self.start_page_spin.setEnabled(not state)
        self.end_page_spin.setEnabled(not state)
    
    def set_default_output_dir(self):
        """Set default output directory to a folder inside the user's documents folder"""
        if hasattr(self, 'default_output_dir') and self.default_output_dir:
            return
            
        # Try to use the same directory as the PDF file first, if already selected
        if hasattr(self, 'file_path_edit') and self.file_path_edit.text():
            pdf_dir = os.path.dirname(self.file_path_edit.text())
            if os.path.isdir(pdf_dir):
                self.default_output_dir = pdf_dir
                return
        
        # Otherwise use the user's documents folder
        home_dir = os.path.expanduser("~")
        docs_dir = os.path.join(home_dir, "Documents")
        
        # Create the PageWisePDF folder inside documents if it doesn't exist
        output_dir = os.path.join(docs_dir, "PageWisePDF_Output")
        try:
            if not os.path.exists(output_dir):
                os.makedirs(output_dir)
            self.default_output_dir = output_dir
        except Exception:
            # If we can't create the directory, just use the home directory
            self.default_output_dir = home_dir
        
        # Update UI if already initialized
        if hasattr(self, 'output_path_edit'):
            self.output_path_edit.setText(self.default_output_dir)
    
    def browse_pdf(self):
        """Open a file dialog to select a PDF file"""
        options = QFileDialog.Options()
        file_filter = self.tr("PDF Files (*.pdf)") if self.language == "English" else "PDF 文件 (*.pdf)"
        file_path, _ = QFileDialog.getOpenFileName(
            self, 
            self.tr("Select PDF File") if self.language == "English" else "选择 PDF 文件",
            "", 
            file_filter,
            options=options
        )
        
        if file_path:
            self.file_path_edit.setText(file_path)
            self.check_input_validity()
            
            # Log the selection
            filename = os.path.basename(file_path)
            self.log(self.tr(f"Selected file: {filename}") if self.language == "English" else f"已选择文件: {filename}")
            
            # If no output directory is set, use the PDF's directory
            if not self.output_path_edit.text():
                output_dir = os.path.dirname(file_path)
                self.output_path_edit.setText(output_dir)
            
            # Try to detect page count to set max value for spinners
            try:
                from pypdf import PdfReader
                reader = PdfReader(file_path)
                total_pages = len(reader.pages)
                
                # Update max values for page range spinners
                self.start_page_spin.setMaximum(total_pages)
                self.end_page_spin.setMaximum(total_pages)
                self.end_page_spin.setValue(total_pages)
                
                # Log page count
                self.log(self.tr(f"PDF has {total_pages} pages") if self.language == "English" else f"PDF 有 {total_pages} 页")
            except Exception as e:
                self.log(self.tr(f"Error reading PDF: {str(e)}") if self.language == "English" else f"读取 PDF 时出错: {str(e)}")
    
    def browse_output_dir(self):
        """Open a directory dialog to select output directory"""
        options = QFileDialog.Options() | QFileDialog.ShowDirsOnly
        dir_path = QFileDialog.getExistingDirectory(
            self, 
            self.tr("Select Output Directory") if self.language == "English" else "选择输出目录",
            self.default_output_dir if hasattr(self, 'default_output_dir') else "",
            options=options
        )
        
        if dir_path:
            self.output_path_edit.setText(dir_path)
            self.check_input_validity()
            
            # Log the selection
            self.log(self.tr(f"Output directory: {dir_path}") if self.language == "English" else f"输出目录: {dir_path}")
    
    def check_input_validity(self):
        """Check if all required inputs are valid and enable/disable start button accordingly"""
        has_pdf = bool(self.file_path_edit.text() and os.path.isfile(self.file_path_edit.text()))
        has_output = bool(self.output_path_edit.text() and os.path.isdir(self.output_path_edit.text()))
        
        self.start_button.setEnabled(has_pdf and has_output)
    
    def open_settings(self):
        """Open the settings dialog"""
        dialog = SettingsDialog(self)
        if dialog.exec_():
            # Get settings from dialog
            self.api_key = dialog.api_key_edit.text()
            self.api_endpoint = dialog.endpoint_edit.text()
            self.model_name = dialog.model_combo.currentText()
            self.concurrent_calls = dialog.concurrent_spin.value()
            self.pages_per_call = dialog.pages_per_call_spin.value()
            self.api_call_interval = dialog.interval_spin.value()
            
            # Save settings
            self.save_settings()
            
            # Log settings change
            self.log(self.tr("Settings updated") if self.language == "English" else "设置已更新")
    
    def save_settings(self):
        """Save settings to QSettings"""
        self.settings.setValue("api_key", self.api_key)
        self.settings.setValue("api_endpoint", self.api_endpoint)
        self.settings.setValue("model_name", self.model_name)
        self.settings.setValue("concurrent_calls", self.concurrent_calls)
        self.settings.setValue("pages_per_call", self.pages_per_call)
        self.settings.setValue("language", self.language)
        self.settings.setValue("api_call_interval", self.api_call_interval)
    
    def log(self, message):
        """Add a message to the log text box"""
        from datetime import datetime
        
        # Add timestamp
        timestamp = datetime.now().strftime("%H:%M:%S")
        timestamped_message = f"[{timestamp}] {message}"
        
        # Append to log
        self.log_text.append(timestamped_message)
        
        # Auto-scroll to bottom
        cursor = self.log_text.textCursor()
        cursor.movePosition(cursor.End)
        self.log_text.setTextCursor(cursor)
    
    def start_processing(self):
        """Start PDF processing"""
        # Validate PDF file
        pdf_path = self.file_path_edit.text()
        if not os.path.isfile(pdf_path):
            QMessageBox.warning(
                self,
                self.tr("Invalid PDF") if self.language == "English" else "无效的 PDF",
                self.tr("Please select a valid PDF file.") if self.language == "English" else "请选择有效的 PDF 文件。"
            )
            return
        
        # Validate output directory
        output_dir = self.output_path_edit.text()
        if not os.path.isdir(output_dir):
            QMessageBox.warning(
                self,
                self.tr("Invalid Output Directory") if self.language == "English" else "无效的输出目录",
                self.tr("Please select a valid output directory.") if self.language == "English" else "请选择有效的输出目录。"
            )
            return
        
        # Validate API key
        if not self.api_key:
            QMessageBox.warning(
                self,
                self.tr("API Key Required") if self.language == "English" else "需要 API 密钥",
                self.tr("Please enter your OpenAI API key in settings.") if self.language == "English" else "请在设置中输入您的 OpenAI API 密钥。"
            )
            self.open_settings()
            return
        
        # Set up processing thread
        self.setup_processing_thread(pdf_path, output_dir)
    
    def setup_processing_thread(self, pdf_path, output_dir):
        """Set up and start the PDF processing thread"""
        # Disable UI controls during processing
        self.start_button.setEnabled(False)
        self.cancel_button.setEnabled(True)
        
        # Reset progress bar
        self.progress_bar.setValue(0)
        
        # Determine processing parameters
        is_summary_mode = self.mode_combo.currentIndex() == 1  # Index 1 = Summary mode
        output_language = "English" if self.language_combo.currentIndex() == 0 else "Chinese"
        
        # Page range
        start_page = None
        end_page = None
        if not self.process_all_pages.isChecked():
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
            language=output_language,
            api_call_interval=self.api_call_interval
        )
        
        # Set up signal connections
        self.pdf_processor.status_update.connect(self.update_status)
        self.pdf_processor.progress_update.connect(self.update_progress)
        self.pdf_processor.log_update.connect(self.log)
        
        # Create processing thread
        self.processing_thread = PDFProcessorThread(self.pdf_processor)
        self.processing_thread.finished.connect(self.on_processing_finished)
        
        # Start processing
        mode_text = self.tr("summary") if is_summary_mode else self.tr("OCR")
        self.log(self.tr(f"Starting {mode_text} processing with {self.model_name}...")
                if self.language == "English"
                else f"开始使用 {self.model_name} 进行{mode_text}处理...")
        
        # Update status
        status_text = self.tr("Processing PDF...") if self.language == "English" else "正在处理 PDF..."
        self.update_status(status_text)
        self.footer.update_status(status_text)
        
        # Start thread
        self.processing_thread.start()
    
    def cancel_processing(self):
        """Cancel the PDF processing"""
        if self.pdf_processor and self.processing_thread and self.processing_thread.isRunning():
            # Log cancellation
            self.log(self.tr("Cancelling processing...") if self.language == "English" else "正在取消处理...")
            
            # Tell the processor to cancel
            self.pdf_processor.cancel()
            
            # Update status
            cancel_text = self.tr("Cancelling...") if self.language == "English" else "正在取消..."
            self.update_status(cancel_text)
            self.footer.update_status(cancel_text)
            
            # Disable cancel button to prevent multiple clicks
            self.cancel_button.setEnabled(False)
    
    def update_status(self, status):
        """Update the status label"""
        self.status_label.setText(status)
        self.footer.update_status(status)
    
    def update_progress(self, value):
        """Update the progress bar"""
        self.progress_bar.setValue(value)
    
    def on_processing_finished(self):
        """Handle the completion of PDF processing"""
        # Re-enable UI controls
        self.check_input_validity()  # This will properly enable/disable the start button
        self.cancel_button.setEnabled(False)
        
        # Check if processing was cancelled
        if self.pdf_processor and self.pdf_processor.is_cancelled():
            status_text = self.tr("Processing cancelled") if self.language == "English" else "处理已取消"
            self.update_status(status_text)
            self.log(status_text)
        else:
            status_text = self.tr("Processing completed") if self.language == "English" else "处理完成"
            self.update_status(status_text)
            self.log(status_text)
            
            # Show completion message with output path
            output_dir = self.output_path_edit.text()
            filename = os.path.basename(self.file_path_edit.text()).split('.')[0]
            md_path = os.path.join(output_dir, f"{filename}_consolidated.md")
            
            if os.path.exists(md_path):
                # Offer to open the output file
                message_box = QMessageBox(self)
                message_box.setWindowTitle(self.tr("Processing Complete") if self.language == "English" else "处理完成")
                message_box.setText(self.tr(f"PDF processing completed successfully!\nOutput saved to: {md_path}")
                                   if self.language == "English"
                                   else f"PDF 处理成功完成！\n输出已保存到: {md_path}")
                
                # Add open folder button
                open_folder_button = message_box.addButton(
                    self.tr("Open Folder") if self.language == "English" else "打开文件夹",
                    QMessageBox.ActionRole
                )
                
                # Add close button
                close_button = message_box.addButton(QMessageBox.Close)
                
                message_box.exec_()
                
                # Handle button click
                if message_box.clickedButton() == open_folder_button:
                    self.open_output_folder()
        
        # Clean up
        self.pdf_processor = None
        self.processing_thread = None
    
    def open_output_folder(self):
        """Open the output folder in the system file explorer"""
        output_dir = self.output_path_edit.text()
        if os.path.isdir(output_dir):
            # Platform-specific code to open folder
            if sys.platform == 'win32':
                os.startfile(output_dir)
            elif sys.platform == 'darwin':  # macOS
                import subprocess
                subprocess.call(['open', output_dir])
            else:  # Linux
                import subprocess
                subprocess.call(['xdg-open', output_dir])

class PDFProcessorThread(QThread):
    """Thread for PDF processing to keep the UI responsive"""
    
    def __init__(self, pdf_processor):
        super().__init__()
        self.pdf_processor = pdf_processor
    
    def run(self):
        """Run the PDF processor"""
        try:
            self.pdf_processor.process()
        except Exception as e:
            # Log and report any unhandled exceptions
            self.pdf_processor.log(f"Error: {str(e)}")
            self.pdf_processor.status_update.emit(str(e))

# Application entry point
def main():
    app = QApplication(sys.argv)
    
    # Set application info
    app.setApplicationName("PageWisePDF")
    app.setOrganizationName("PageWisePDF")
    app.setOrganizationDomain("pagewisepdf.com")
    
    # Create and show the main window
    window = MainWindow()
    window.show()
    
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()