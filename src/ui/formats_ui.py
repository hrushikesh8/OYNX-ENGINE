from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
                             QLabel, QComboBox, QFrame)
from PyQt6.QtCore import Qt
from src.ui.custom_widgets import DropZone
from src.processors.formats import FormatMapper # Using your original class
import os

class FormatConverterUI(QWidget):
    """The Visual Controller for the FormatMapper Engine"""
    def __init__(self, back_callback):
        super().__init__()
        self.mapper = FormatMapper() # Initialize your engine
        
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        # --- HEADER ---
        header = QHBoxLayout()
        back_btn = QPushButton("⬅ Back to Dashboard")
        back_btn.clicked.connect(back_callback)
        header.addWidget(back_btn)
        
        title = QLabel("🔄 Smart Format Mapper")
        title.setStyleSheet("font-size: 22px; font-weight: bold;")
        header.addWidget(title)
        header.addStretch()
        layout.addLayout(header)

        # --- DROP ZONE ---
        layout.addWidget(QLabel("Step 1: Drop Video or Folder"))
        self.drop_zone = DropZone(self)
        layout.addWidget(self.drop_zone)

        # --- FORMAT SELECTION ---
        layout.addSpacing(20)
        layout.addWidget(QLabel("Step 2: Choose Target Format"))
        
        # We pull the keys directly from your original FORMAT_RULES dictionary
        self.format_dropdown = QComboBox()
        self.format_dropdown.addItems(list(self.mapper.FORMAT_RULES.keys()))
        self.format_dropdown.setMinimumHeight(45)
        self.format_dropdown.setStyleSheet("font-size: 16px; font-weight: bold;")
        layout.addWidget(self.format_dropdown)

        # --- EXECUTION ---
        layout.addSpacing(30)
        self.exec_btn = QPushButton("🚀 Run Intelligent Conversion")
        self.exec_btn.setMinimumHeight(60)
        self.exec_btn.setStyleSheet("""
            QPushButton { background-color: #2D72D9; color: white; font-size: 18px; font-weight: bold; border-radius: 8px; }
            QPushButton:hover { background-color: #3a82ef; }
        """)
        self.exec_btn.clicked.connect(self.start_mapping)
        layout.addWidget(self.exec_btn)

        self.status_label = QLabel("Ready.")
        self.status_label.setStyleSheet("color: #888; font-style: italic;")
        layout.addWidget(self.status_label)

    def start_mapping(self):
        input_path = self.drop_zone.file_input.text().strip()
        target_fmt = self.format_dropdown.currentText()

        if not input_path:
            self.status_label.setText("❌ Error: No input provided.")
            return

        # Define Output Folder (Default to a 'Converted' folder in the source dir)
        if os.path.isdir(input_path):
            output_dir = os.path.join(input_path, "Onyx_Converted")
        else:
            output_dir = os.path.join(os.path.dirname(input_path), "Onyx_Converted")

        self.status_label.setText("⚡ Processing... See terminal for live logs.")
        self.exec_btn.setEnabled(False)

        # CALLING YOUR ORIGINAL process_input FUNCTION
        success, errors = self.mapper.process_input(input_path, output_dir, target_fmt)

        self.status_label.setText(f"🎉 Done! Success: {success} | Errors: {errors}")
        self.exec_btn.setEnabled(True)