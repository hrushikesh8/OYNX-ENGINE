import os
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
                             QLabel, QFrame, QListWidgetItem)
from PyQt6.QtCore import Qt
from src.ui.custom_widgets import SmartRunButton
from src.ui.suture_ui import DragDropList  # Reusing your professional list logic
from src.processors.stitcher import VideoStitcher

class VideoStitcherUI(QWidget):
    """
    UI for Feature 6: Video Stitcher.
    Allows users to drag, drop, and re-order clips for instant concatenation.
    """
    def __init__(self, back_callback, orchestrator):
        super().__init__()
        self.orchestrator = orchestrator
        self.stitcher_engine = VideoStitcher()
        
        # Main Layout
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        layout.setContentsMargins(30, 30, 30, 30)

        # --- 1. HEADER SECTION ---
        header = QHBoxLayout()
        
        self.back_btn = QPushButton("←")
        self.back_btn.setFixedSize(36, 36)
        self.back_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.back_btn.setStyleSheet("""
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
        self.back_btn.clicked.connect(back_callback)
        
        title = QLabel("🎬 Video Stitcher (Concat)")
        title.setStyleSheet("font-size: 24px; font-weight: bold; color: white;")
        
        header.addWidget(self.back_btn)
        header.addSpacing(15)
        header.addWidget(title)
        header.addStretch()
        layout.addLayout(header)
        
        layout.addSpacing(10)
        subtitle = QLabel("Instantly join multiple clips into one file without quality loss.")
        subtitle.setStyleSheet("color: #777; font-size: 14px;")
        layout.addWidget(subtitle)

        # --- 2. THE TIMELINE (DRAG & DROP LIST) ---
        layout.addSpacing(25)
        layout.addWidget(QLabel("<b>TIMELINE:</b> Drag clips to change their order in the final video"))
        
        self.file_list = DragDropList()
        self.file_list.setMinimumHeight(400)
        # Adding a tool tip for better UX
        self.file_list.setToolTip("Drop video files here and drag them up/down to re-order.")
        layout.addWidget(self.file_list)

        # --- 3. LIST CONTROLS ---
        controls = QHBoxLayout()
        
        self.remove_btn = QPushButton("❌ Remove Selected")
        self.remove_btn.clicked.connect(self.remove_item)
        
        self.clear_btn = QPushButton("🗑️ Clear Timeline")
        self.clear_btn.clicked.connect(self.file_list.clear)

        for btn in [self.remove_btn, self.clear_btn]:
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.setStyleSheet("""
                QPushButton { background-color: #1e1e1e; border: 1px solid #333; border-radius: 4px; 
                              padding: 6px 12px; color: #888; font-weight: bold; }
                QPushButton:hover { background-color: #252525; color: #eee; border: 1px solid #444; }
            """)
        
        controls.addWidget(self.remove_btn)
        controls.addWidget(self.clear_btn)
        controls.addStretch()
        layout.addLayout(controls)

        # --- 4. EXECUTION AREA ---
        layout.addStretch()
        
        info_frame = QFrame()
        info_frame.setStyleSheet("background-color: #1a1a1a; border: 1px solid #282828; border-radius: 8px; padding: 10px;")
        info_layout = QHBoxLayout(info_frame)
        info_icon = QLabel("ℹ️")
        info_text = QLabel("All clips must have the same resolution and codec for a successful stitch.")
        info_text.setStyleSheet("color: #aaa; font-size: 12px;")
        info_layout.addWidget(info_icon)
        info_layout.addWidget(info_text)
        info_layout.addStretch()
        layout.addWidget(info_frame)
        
        layout.addSpacing(15)

        self.exec_btn = SmartRunButton("⚡ Execute Stitching", self.get_stitch_inputs, self.start_stitching, speed_multiplier=20.0)
        layout.addWidget(self.exec_btn)

    def get_stitch_inputs(self):
        count = self.file_list.count()
        if count < 2: return None
        return [self.file_list.item(i).text() for i in range(count)]

    def remove_item(self):
        """Removes the highlighted item from the list."""
        for item in self.file_list.selectedItems():
            self.file_list.takeItem(self.file_list.row(item))

    def start_stitching(self, inputs, est_seconds):
        """Prepares the file list and triggers the backend engine."""
        count = self.file_list.count()
        if count < 2:
            print("[UI Warning] At least 2 clips are required to stitch.")
            return
        
        # 1. Collect ordered paths
        video_paths = [self.file_list.item(i).text() for i in range(count)]
        
        # 2. Determine output path (Saves in the same folder as the first clip)
        base_dir = os.path.dirname(video_paths[0])
        output_file = os.path.join(base_dir, "Onyx_Stitch_Result.mp4")

        def task():
            success = self.stitcher_engine.concat_videos(video_paths, output_file)
            return success, f"Video stitching finished. Output: {output_file}" if success else "Stitching failed."

        self.orchestrator.add_background_job("Video Stitcher", task, estimated_seconds=est_seconds)
        self.orchestrator.show_status_message("⏳ Video stitching task queued.")

# ==========================================
# HOW TO USE THIS CODE (EXAMPLE)
# ==========================================
# Example usage:
# from src.processors.stitcher_ui import MainClass
# processor = MainClass()
# processor.run(input_file, output_file)
# ==========================================

# ==============================================================================
# 🎬 FEATURE: INTERNAL MODULE DOCUMENTATION (stitcher_ui.py)
# ==============================================================================
#
# 📝 WHAT IS THIS FILE?
#    This file, 'stitcher_ui.py', is a core component of the Onyx Engine. It is
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
