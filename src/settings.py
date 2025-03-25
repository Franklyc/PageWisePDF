import os
from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, 
                           QPushButton, QFormLayout, QSpinBox, QComboBox, QGroupBox,
                           QDialogButtonBox, QCheckBox, QMessageBox, QDoubleSpinBox)
from PyQt5.QtCore import Qt, QSettings
from PyQt5.QtGui import QColor, QPalette

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
        self.resize(500, 400)  # Made taller for additional settings
        
        # Create settings form
        self.init_ui()
        
        # Load settings
        self.load_settings()
    
    def init_ui(self):
        main_layout = QVBoxLayout(self)
        
        # Create API settings group
        api_group = QGroupBox(self.tr("OpenAI API Settings") if self.language == "English" else "OpenAI API 设置")
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
        
        form_layout.addRow("", security_label)
        
        # API Endpoint
        self.endpoint_edit = QLineEdit()
        self.endpoint_edit.setPlaceholderText("https://api.openai.com/v1/chat/completions")
        form_layout.addRow(self.tr("API Endpoint:") if self.language == "English" else "API 端点:", self.endpoint_edit)
        
        # Model selection - made editable to support custom model names
        self.model_combo = QComboBox()
        self.model_combo.setEditable(True)
        self.model_combo.addItems(["gpt-4-vision-preview", "gpt-4o", "gpt-4-turbo"])
        model_label = self.tr("Model (editable):") if self.language == "English" else "模型 (可编辑):"
        form_layout.addRow(model_label, self.model_combo)
        
        # Add model hint
        model_hint = QLabel(
            self.tr("You can type any model name supported by your API endpoint") 
            if self.language == "English" 
            else "您可以输入您的API端点支持的任何模型名称"
        )
        model_hint.setWordWrap(True)
        form_layout.addRow("", model_hint)
        
        # API Call Interval (in seconds)
        self.interval_spin = QDoubleSpinBox()
        self.interval_spin.setMinimum(0.0)
        self.interval_spin.setMaximum(10.0)  # Maximum 10 seconds interval
        self.interval_spin.setSingleStep(0.1)  # Allow fine-grained control
        self.interval_spin.setDecimals(1)  # Show one decimal place
        self.interval_spin.setValue(0.0)  # Default to no delay
        form_layout.addRow(
            self.tr("API Call Interval (seconds):") if self.language == "English" else "API 调用间隔（秒）:", 
            self.interval_spin
        )
        
        api_group.setLayout(form_layout)
        
        # Create processing settings group
        proc_group = QGroupBox(self.tr("Processing Settings") if self.language == "English" else "处理设置")
        proc_layout = QFormLayout()
        
        # Concurrent API calls
        self.concurrent_spin = QSpinBox()
        self.concurrent_spin.setMinimum(1)
        self.concurrent_spin.setMaximum(10)  # Set a reasonable max to avoid API rate limits
        proc_layout.addRow(self.tr("Concurrent API Calls:") if self.language == "English" else "并发 API 调用:", self.concurrent_spin)
        
        # Pages per API call
        self.pages_per_call_spin = QSpinBox()
        self.pages_per_call_spin.setMinimum(1)
        self.pages_per_call_spin.setMaximum(4)  # OpenAI has limits on number of images per request
        proc_layout.addRow(self.tr("Pages Per API Call:") if self.language == "English" else "每个 API 调用的页数:", self.pages_per_call_spin)
        
        proc_group.setLayout(proc_layout)
        
        # Add groups to main layout
        main_layout.addWidget(api_group)
        main_layout.addWidget(proc_group)
        
        # Add buttons
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        main_layout.addWidget(button_box)
    
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