import os
from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, 
                           QPushButton, QFormLayout, QSpinBox, QComboBox, QGroupBox,
                           QDialogButtonBox, QCheckBox, QMessageBox, QDoubleSpinBox,
                           QTabWidget, QWidget, QFrame, QScrollArea, QSizePolicy)
from PyQt5.QtCore import Qt, QSettings, QSize
from PyQt5.QtGui import QColor, QPalette, QFont, QIcon, QPixmap

class SettingsDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self.parent = parent
        
        # Determine language
        self.language = "English"
        if parent and hasattr(parent, 'language'):
            self.language = parent.language
        
        # Set dialog properties
        self.setWindowTitle(self.tr("API Settings") if self.language == "English" else "API 设置")
        self.setModal(True)
        self.resize(550, 500)  # Made larger for additional settings
        
        # Create settings form
        self.init_ui()
        
        # Load settings
        self.load_settings()

    def init_ui(self):
        main_layout = QVBoxLayout(self)
        
        # Create tab widget for better organization
        self.tab_widget = QTabWidget()
        
        # Tab 1: API Settings
        api_tab = QWidget()
        api_layout = QVBoxLayout(api_tab)
        
        # Create API settings group
        api_group = QGroupBox(self.tr("OpenAI API Configuration") if self.language == "English" else "OpenAI API 配置")
        form_layout = QFormLayout()
        
        # API Key
        self.api_key_edit = QLineEdit()
        self.api_key_edit.setEchoMode(QLineEdit.Password)
        form_layout.addRow(self.tr("API Key:") if self.language == "English" else "API 密钥:", self.api_key_edit)
        
        # Add security warning for API key
        security_label = QLabel(
            self.tr("⚠️ Warning: Your API key is stored locally and not part of your code. "
                   "Do not share sensitive configuration files.") 
            if self.language == "English" 
            else "⚠️ 警告：您的API密钥存储在本地，不是代码的一部分。请不要共享敏感的配置文件。"
        )
        security_label.setWordWrap(True)
        
        # Set a highlighted background for the warning
        palette = security_label.palette()
        palette.setColor(QPalette.Window, QColor(255, 255, 200))  # Light yellow background
        palette.setColor(QPalette.WindowText, QColor(180, 0, 0))  # Dark red text
        security_label.setPalette(palette)
        security_label.setAutoFillBackground(True)
        security_label.setStyleSheet("padding: 8px; border-radius: 4px;")
        
        form_layout.addRow("", security_label)
        
        # API Endpoint
        self.endpoint_edit = QLineEdit()
        self.endpoint_edit.setPlaceholderText("https://api.openai.com/v1/chat/completions")
        form_layout.addRow(self.tr("API Endpoint:") if self.language == "English" else "API 端点:", self.endpoint_edit)
        
        # API endpoint help text
        endpoint_help = QLabel(
            self.tr("Special rules for endpoint URLs:\n"
                   "- Ending with / means don't append /v1/chat/completions\n"
                   "- Ending with # means use exactly as is")
            if self.language == "English"
            else "端点URL的特殊规则：\n"
                 "- 以/结尾表示不追加/v1/chat/completions\n"
                 "- 以#结尾表示原样使用"
        )
        endpoint_help.setStyleSheet("color: #777; font-size: 10pt; padding-left: 4px;")
        endpoint_help.setWordWrap(True)
        form_layout.addRow("", endpoint_help)
        
        # Model selection - made editable to support custom model names
        self.model_combo = QComboBox()
        self.model_combo.setEditable(True)
        self.model_combo.addItems([
            "gpt-4-vision-preview", 
            "gpt-4o", 
            "gpt-4-turbo",
            "gpt-4o-mini"
        ])
        model_label = self.tr("Model (editable):") if self.language == "English" else "模型 (可编辑):"
        form_layout.addRow(model_label, self.model_combo)
        
        # Add model hint
        model_hint = QLabel(
            self.tr("You can type any model name supported by your API endpoint") 
            if self.language == "English" 
            else "您可以输入您的API端点支持的任何模型名称"
        )
        model_hint.setStyleSheet("color: #777; font-size: 10pt; padding-left: 4px;")
        model_hint.setWordWrap(True)
        form_layout.addRow("", model_hint)
        
        # API Call Interval (in seconds)
        interval_layout = QHBoxLayout()
        self.interval_spin = QDoubleSpinBox()
        self.interval_spin.setMinimum(0.0)
        self.interval_spin.setMaximum(10.0)  # Maximum 10 seconds interval
        self.interval_spin.setSingleStep(0.1)  # Allow fine-grained control
        self.interval_spin.setDecimals(1)  # Show one decimal place
        self.interval_spin.setValue(0.0)  # Default to no delay
        
        interval_help_btn = QPushButton("?")
        interval_help_btn.setFixedSize(24, 24)
        interval_help_btn.setToolTip(
            self.tr("Adds a delay between API calls to avoid rate limits") 
            if self.language == "English" 
            else "在API调用之间添加延迟以避免速率限制"
        )
        interval_help_btn.clicked.connect(lambda: self.show_help_message(
            self.tr("API Call Interval") if self.language == "English" else "API 调用间隔",
            (self.tr("Setting a delay between API calls can help avoid rate limiting issues with the OpenAI API. "
                "If you're experiencing 'too many requests' errors, try setting this to 0.5 or higher.") 
            if self.language == "English" 
            else "在API调用之间设置延迟可以帮助避免OpenAI API的速率限制问题。如果您遇到'请求过多'错误，请尝试将其设置为0.5或更高。")
        ))
        
        interval_layout.addWidget(self.interval_spin)
        interval_layout.addWidget(interval_help_btn)
        
        form_layout.addRow(
            self.tr("API Call Interval (seconds):") if self.language == "English" else "API 调用间隔（秒）:", 
            interval_layout
        )
        
        api_group.setLayout(form_layout)
        api_layout.addWidget(api_group)
        
        # Tab 2: Processing Settings
        processing_tab = QWidget()
        processing_layout = QVBoxLayout(processing_tab)
        
        # Create processing settings group
        proc_group = QGroupBox(self.tr("Processing Configuration") if self.language == "English" else "处理配置")
        proc_layout = QFormLayout()
        
        # Concurrent API calls
        concurrent_layout = QHBoxLayout()
        self.concurrent_spin = QSpinBox()
        self.concurrent_spin.setMinimum(1)
        self.concurrent_spin.setMaximum(10)  # Set a reasonable max to avoid API rate limits
        
        concurrent_help_btn = QPushButton("?")
        concurrent_help_btn.setFixedSize(24, 24)
        concurrent_help_btn.setToolTip(
            self.tr("Number of concurrent API calls (higher values process faster but may hit rate limits)") 
            if self.language == "English" 
            else "并发API调用数量（较高的值处理速度更快，但可能达到速率限制）"
        )
        concurrent_help_btn.clicked.connect(lambda: self.show_help_message(
            self.tr("Concurrent API Calls") if self.language == "English" else "并发 API 调用",
            (self.tr("This setting controls how many API calls are made simultaneously. "
                   "Higher values can speed up processing but may trigger OpenAI's rate limits. "
                   "Recommended values: 1-3 for free tier accounts, 3-5 for paid accounts.") 
            if self.language == "English" 
            else "此设置控制同时进行的API调用数量。较高的值可以加快处理速度，但可能触发OpenAI的速率限制。"
                 "推荐值：免费账户为1-3，付费账户为3-5。")
        ))
        
        concurrent_layout.addWidget(self.concurrent_spin)
        concurrent_layout.addWidget(concurrent_help_btn)
        
        proc_layout.addRow(
            self.tr("Concurrent API Calls:") if self.language == "English" else "并发 API 调用:", 
            concurrent_layout
        )
        
        # Pages per API call
        pages_layout = QHBoxLayout()
        self.pages_per_call_spin = QSpinBox()
        self.pages_per_call_spin.setMinimum(1)
        self.pages_per_call_spin.setMaximum(4)  # OpenAI has limits on number of images per request
        
        pages_help_btn = QPushButton("?")
        pages_help_btn.setFixedSize(24, 24)
        pages_help_btn.setToolTip(
            self.tr("Number of PDF pages to include in a single API call") 
            if self.language == "English" 
            else "单个API调用中包含的PDF页数"
        )
        pages_help_btn.clicked.connect(lambda: self.show_help_message(
            self.tr("Pages Per API Call") if self.language == "English" else "每个 API 调用的页数",
            (self.tr("This setting determines how many PDF pages are sent in a single API call. "
                   "Higher values can reduce the total number of API calls but may produce less accurate results "
                   "for complex documents. Most vision models support up to 4 images per call.") 
            if self.language == "English" 
            else "此设置决定在单个API调用中发送多少PDF页。较高的值可以减少API调用的总数，"
                 "但对于复杂文档可能会产生不太准确的结果。大多数视觉模型每次调用最多支持4张图像。")
        ))
        
        pages_layout.addWidget(self.pages_per_call_spin)
        pages_layout.addWidget(pages_help_btn)
        
        proc_layout.addRow(
            self.tr("Pages Per API Call:") if self.language == "English" else "每个 API 调用的页数:", 
            pages_layout
        )
        
        # Advanced settings section
        advanced_group = QGroupBox(self.tr("Advanced Settings") if self.language == "English" else "高级设置")
        advanced_layout = QFormLayout()
        
        # Image quality/resolution setting (placeholder for future implementation)
        self.image_quality_combo = QComboBox()
        self.image_quality_combo.addItems([
            self.tr("Standard (300 DPI)") if self.language == "English" else "标准 (300 DPI)",
            self.tr("High (600 DPI)") if self.language == "English" else "高 (600 DPI)"
        ])
        # Temporarily disable this control as it's not yet implemented
        self.image_quality_combo.setEnabled(False)
        
        advanced_layout.addRow(
            self.tr("Image Quality:") if self.language == "English" else "图像质量:", 
            self.image_quality_combo
        )
        
        advanced_group.setLayout(advanced_layout)
        
        proc_group.setLayout(proc_layout)
        processing_layout.addWidget(proc_group)
        processing_layout.addWidget(advanced_group)
        processing_layout.addStretch()
        
        # Add tabs to tab widget
        self.tab_widget.addTab(api_tab, self.tr("API Settings") if self.language == "English" else "API 设置")
        self.tab_widget.addTab(processing_tab, self.tr("Processing") if self.language == "English" else "处理")
        
        # About section at the bottom
        about_frame = QFrame()
        about_frame.setFrameShape(QFrame.StyledPanel)
        about_frame.setStyleSheet("background-color: #f8f9fa; border-radius: 4px; padding: 8px;")
        about_layout = QHBoxLayout(about_frame)
        
        app_info = QLabel("PageWisePDF v1.0")
        app_info.setStyleSheet("color: #666; font-size: 10pt;")
        
        about_layout.addWidget(app_info)
        about_layout.addStretch()
        
        # Add buttons
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        
        # Add components to main layout
        main_layout.addWidget(self.tab_widget)
        main_layout.addWidget(about_frame)
        main_layout.addWidget(button_box)
    
    def show_help_message(self, title, message):
        """Display a help message dialog"""
        QMessageBox.information(self, title, message)
    
    def load_settings(self):
        if not self.parent:
            return
        
        # Load settings from parent
        self.api_key_edit.setText(self.parent.api_key)
        self.endpoint_edit.setText(self.parent.api_endpoint)
        
        # For editable combo box, directly set the text
        self.model_combo.setCurrentText(self.parent.model_name)
        
        # Set processing values
        self.concurrent_spin.setValue(self.parent.concurrent_calls)
        self.pages_per_call_spin.setValue(self.parent.pages_per_call)
        
        # Set API call interval
        self.interval_spin.setValue(self.parent.api_call_interval)
    
    def tr(self, text):
        """Simple translation helper function"""
        # In a real app, this would use proper translation mechanisms
        return text