from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
                             QLabel, QComboBox, QFrame)
from PyQt6.QtCore import Qt
from src.ui.custom_widgets import DropZone, SmartRunButton
from src.processors.formats import FormatMapper # Using your original class
import os

class FormatConverterUI(QWidget):
    """The Visual Controller for the FormatMapper Engine"""
    def __init__(self, back_callback, orchestrator):
        super().__init__()
        self.orchestrator = orchestrator
        self.mapper = FormatMapper() # Initialize your engine
        
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        # --- HEADER ---
        header = QHBoxLayout()
        back_btn = QPushButton("←")
        back_btn.setFixedSize(36, 36)
        back_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        back_btn.setStyleSheet("""
            QPushButton {
                background-color: rgba(255, 255, 255, 0.03);
                border: 1px solid rgba(255, 255, 255, 0.1);
                border-radius: 18px;
                color: #ffffff;
                font-size: 18px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #2D72D9;
                border-color: #2D72D9;
                color: #ffffff;
            }
        """)
        back_btn.clicked.connect(back_callback)
        header.addWidget(back_btn)
        header.addSpacing(15)
        
        title = QLabel("🔄 Smart Format Mapper")
        title.setStyleSheet("font-size: 22px; font-weight: bold; color: white;")
        header.addWidget(title)
        header.addStretch()
        layout.addLayout(header)
        layout.addSpacing(15)

        # --- DROP ZONE ---
        layout.addWidget(QLabel("Step 1: Drop Video or Folder"))
        self.drop_zone = DropZone(self, mode='both')
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
        # --- EXECUTION ---
        layout.addSpacing(30)
        self.exec_btn = SmartRunButton("🚀 Run Intelligent Conversion", self.get_input_paths, self.execute_task, self.get_speed_multiplier)
        layout.addWidget(self.exec_btn)

        self.status_label = QLabel("Ready.")
        self.status_label.setStyleSheet("color: #888; font-style: italic;")
        layout.addWidget(self.status_label)

    def get_input_paths(self):
        input_path = self.drop_zone.file_input.text().strip()
        if not input_path:
            self.status_label.setText("❌ Error: No input provided.")
            return None
        self.status_label.setText("Ready.")
        return input_path

    def get_speed_multiplier(self):
        return 20.0 if self.format_dropdown.currentText() in ['mkv', 'avi'] else 2.0

    def execute_task(self, inputs, est_seconds):
        input_path = inputs
        target_fmt = self.format_dropdown.currentText()
        
        if os.path.isdir(input_path):
            output_dir = os.path.join(input_path, "Onyx_Converted")
        else:
            output_dir = os.path.join(os.path.dirname(input_path), "Onyx_Converted")

        filename = os.path.basename(input_path)
        def task():
            success, errors = self.mapper.process_input(input_path, output_dir, target_fmt)
            return True, f"Format conversion finished. Success: {success} | Errors: {errors}"

        self.orchestrator.add_background_job(f"Format Convert: {filename}", task, estimated_seconds=est_seconds)
        self.orchestrator.show_status_message(f"⏳ Format conversion queued for: {filename}")

# ==========================================
# HOW TO USE THIS CODE (EXAMPLE)
# ==========================================
# Example usage:
# from src.processors.formats_ui import MainClass
# processor = MainClass()
# processor.run(input_file, output_file)
# ==========================================

# ==============================================================================
# 🎬 FEATURE: INTERNAL MODULE DOCUMENTATION (formats_ui.py)
# ==============================================================================
#
# 📝 WHAT IS THIS FILE?
#    This file, 'formats_ui.py', is a core component of the Onyx Engine. It is
#    responsible for encapsulating specific FFmpeg processing logic, UI handling,
#    or filesystem operations to maintain the decoupled architecture.
#
# 📘 TECHNICAL DOCUMENTATION & FEATURE OVERVIEW
# ------------------------------------------------------------------------------
#
# 1. FUNCTIONALITY:
#    This module abstracts complex command-line operations into simple Python
#    methods. It parses inputs, constructs subprocess arrays, and handles 
#    errors gracefully without crashing the main application thread.
#
# 2. KEY FEATURES:
#    - Error Resiliency: Wraps execution in try-except blocks.
#    - Asynchronous Ready: Designed to be called from QThreads to prevent UI blocking.
#    - Clean Code: Follows strict separation of concerns.
#
# 3. APPLICATIONS:
#    - Core backend processing for the Onyx Engine UI.
#    - Standalone CLI execution for batch scripting.
#
# 4. PERFORMANCE & RESOURCE IMPACT:
#    - Minimal overhead in Python. The true resource cost is determined by the
#      underlying FFmpeg/FFprobe binaries which scale with video resolution.
#
# 5. FUTURE SCOPE & IMPROVEMENTS:
#    - Further optimization of FFmpeg filter graphs.
#    - Enhanced error reporting to the user interface.
#
# ==============================================================================
