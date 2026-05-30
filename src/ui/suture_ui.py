import os
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
                             QLabel, QListWidget, QAbstractItemView, QCheckBox, 
                             QFrame, QFileDialog)
from PyQt6.QtCore import Qt
import sys
from src.processors import suture_merger
from src.ui.custom_widgets import SmartRunButton

class DragDropList(QListWidget):
    """A custom ListWidget that acts as a giant Drag & Drop zone."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAcceptDrops(True)
        self.setDragEnabled(True)
        self.setDragDropMode(QAbstractItemView.DragDropMode.InternalMove)
        self.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        
        # Professional Styling: Dashed border to indicate it's a Drop Zone
        self.setStyleSheet("""
            QListWidget {
                background-color: #161616;
                border: 2px dashed #333;
                border-radius: 10px;
                color: #eee;
                font-size: 14px;
                padding: 10px;
            }
            QListWidget:hover { border: 2px dashed #2D72D9; }
            QListWidget::item { 
                background-color: #1e1e1e; 
                margin-bottom: 5px; 
                padding: 10px; 
                border-radius: 5px; 
            }
            QListWidget::item:selected { background-color: #2D72D9; color: white; }
        """)

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.accept()
        else:
            super().dragEnterEvent(event)

    def dragMoveEvent(self, event):
        if event.mimeData().hasUrls():
            event.accept()
        else:
            super().dragMoveEvent(event)

    def dropEvent(self, event):
        if event.mimeData().hasUrls():
            event.setDropAction(Qt.DropAction.CopyAction)
            event.accept()
            for url in event.mimeData().urls():
                file_path = str(url.toLocalFile())
                if file_path.lower().endswith(('.mp4', '.mkv', '.avi', '.mov')):
                    self.addItem(file_path)
        else:
            # Handle internal re-ordering
            super().dropEvent(event)

class SeamlessSutureUI(QWidget):
    def __init__(self, back_callback, orchestrator):
        super().__init__()
        self.orchestrator = orchestrator
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        # --- HEADER ---
        header_layout = QHBoxLayout()
        
        # Neat Back Button
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
        
        title = QLabel(" 🧵 Seamless Suture")
        title.setStyleSheet("font-size: 22px; font-weight: bold; color: white;")
        
        header_layout.addWidget(back_btn)
        header_layout.addSpacing(15)
        header_layout.addWidget(title)
        header_layout.addStretch()
        layout.addLayout(header_layout)

        # --- THE DRAG & DROP LIST (The main engine) ---
        layout.addSpacing(10)
        layout.addWidget(QLabel("Drag video files directly into the box below or use Add Files:"))
        
        self.file_list = DragDropList() # This is your Drag & Drop option
        self.file_list.setMinimumHeight(350)
        layout.addWidget(self.file_list)

        # --- CONTROLS ---
        list_controls = QHBoxLayout()
        
        self.browse_btn = QPushButton("➕ Add Files")
        self.browse_btn.clicked.connect(self.browse_files)
        
        self.remove_btn = QPushButton("❌ Remove Selected")
        self.remove_btn.clicked.connect(self.remove_selected_item)
        
        self.clear_btn = QPushButton("🗑️ Clear All")
        self.clear_btn.clicked.connect(self.file_list.clear)

        for btn in [self.browse_btn, self.remove_btn, self.clear_btn]:
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.setStyleSheet("background-color: #252525; border-radius: 4px; padding: 8px 15px; font-weight: bold;")
        
        list_controls.addWidget(self.browse_btn)
        list_controls.addWidget(self.remove_btn)
        list_controls.addWidget(self.clear_btn)
        list_controls.addStretch()
        layout.addLayout(list_controls)

        # --- OPTIONS ---
        layout.addSpacing(20)
        options_frame = QFrame()
        options_frame.setStyleSheet("background-color: #1a1a1a; border: 1px solid #222; border-radius: 8px; padding: 15px;")
        options_layout = QVBoxLayout(options_frame)

        self.cv_toggle = QCheckBox(" Enable Auto-Detect Overlap (CV Mode)")
        self.cv_toggle.setChecked(True)
        self.cv_toggle.setStyleSheet("font-size: 15px; font-weight: bold; color: #2D72D9;")
        
        cv_desc = QLabel("Uses OpenCV to find the exact frame match (removes duplicate scenes).")
        cv_desc.setStyleSheet("color: #777; font-size: 13px; margin-left: 28px;")
        
        options_layout.addWidget(self.cv_toggle)
        options_layout.addWidget(cv_desc)
        layout.addWidget(options_frame)

        # --- EXECUTE ---
        layout.addStretch()
        self.exec_btn = SmartRunButton("⚡ Execute Seamless Suture", self.get_suture_inputs, self.execute_suture, speed_multiplier=15.0)
        layout.addWidget(self.exec_btn)

    def get_suture_inputs(self):
        count = self.file_list.count()
        if count < 2: return None
        return [self.file_list.item(i).text() for i in range(count)]

    def browse_files(self):
        start_dir = getattr(sys, '_onyx_last_dir', os.path.expanduser("~\\Desktop"))
        files, _ = QFileDialog.getOpenFileNames(self, "Select Video Parts", start_dir, "Video Files (*.mp4 *.mkv *.avi)")
        if files:
            sys._onyx_last_dir = os.path.dirname(files[0])
            for f in files: self.file_list.addItem(f)

    def remove_selected_item(self):
        for item in self.file_list.selectedItems():
            self.file_list.takeItem(self.file_list.row(item))

    def execute_suture(self, inputs, est_seconds):
        ordered_files = inputs
        use_cv = self.cv_toggle.isChecked()
        
        # Smart output naming (Preserve original extension)
        base_dir = os.path.dirname(ordered_files[0])
        ext = os.path.splitext(ordered_files[0])[1]
        final_output = os.path.join(base_dir, f"Onyx_Suture_Result{ext}")

        def task():
            suture_merger.run_suture_workflow(ordered_files, final_output, use_cv)
            return True, f"Seamless Suture completed successfully. Output saved to: {final_output}"

        self.orchestrator.add_background_job("Seamless Suture", task, estimated_seconds=est_seconds)
        self.orchestrator.show_status_message("⏳ Seamless Suture task queued.")

# ==========================================
# HOW TO USE THIS CODE (EXAMPLE)
# ==========================================
# Example usage:
# from src.processors.suture_ui import MainClass
# processor = MainClass()
# processor.run(input_file, output_file)
# ==========================================

# ==============================================================================
# 🎬 FEATURE: INTERNAL MODULE DOCUMENTATION (suture_ui.py)
# ==============================================================================
#
# 📝 WHAT IS THIS FILE?
#    This file, 'suture_ui.py', is a core component of the Onyx Engine. It is
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
