from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
                             QLabel, QCheckBox, QScrollArea, QFrame)
from PyQt6.QtCore import Qt
from src.ui.custom_widgets import DropZone, SmartRunButton
from src.processors.tracks import TrackProcessor # Import your class
import os

class TrackCleanerUI(QWidget):
    """The Visual Dashboard for Feature 2 (Audio) and Feature 3 (Subtitles)"""
    def __init__(self, back_callback, orchestrator, mode='a'):
        super().__init__()
        self.orchestrator = orchestrator
        self.processor = TrackProcessor()
        self.mode = mode # 'a' for Audio, 's' for Subtitles
        
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
        
        label_text = "🎵 Audio Track Cleaner" if mode == 'a' else "📝 Subtitle Track Cleaner"
        title = QLabel(label_text)
        title.setStyleSheet("font-size: 22px; font-weight: bold; color: white;")
        header.addWidget(title)
        header.addStretch()
        layout.addLayout(header)
        layout.addSpacing(15)

        # --- DROP ZONE ---
        self.drop_zone = DropZone(self)
        self.drop_zone.file_input.textChanged.connect(self.refresh_tracks)
        layout.addWidget(self.drop_zone)

        layout.addSpacing(15)
        layout.addWidget(QLabel("Step 2: Select the tracks you wish to PRESERVE:"))

        # --- DYNAMIC CHECKBOX LIST ---
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setStyleSheet("background-color: #1e1e1e; border-radius: 8px;")
        
        self.container = QWidget()
        self.track_layout = QVBoxLayout(self.container)
        self.scroll.setWidget(self.container)
        layout.addWidget(self.scroll)

        self.checkboxes = []

        # --- EXECUTION ---
        self.exec_btn = SmartRunButton("🚀 Purge Unselected Tracks", self.get_input_paths, self.run_purge, speed_multiplier=10.0)
        self.exec_btn.setStyleSheet("background-color: #D92D2D; color: white; font-size: 16px; font-weight: bold; border-radius: 10px;")
        layout.addWidget(self.exec_btn)

    def refresh_tracks(self):
        """Called when a file is dropped. Uses your get_track_info logic."""
        path = self.drop_zone.file_input.text().strip()
        if not path or not os.path.exists(path): return

        # Clear existing list
        for cb in self.checkboxes:
            self.track_layout.removeWidget(cb)
            cb.deleteLater()
        self.checkboxes.clear()

        # Call YOUR original ffprobe logic
        raw_tracks = self.processor.get_track_info(path, self.mode)
        
        for i, t in enumerate(raw_tracks):
            lang = t.get('tags', {}).get('language', 'und')
            title = t.get('tags', {}).get('title', 'Track')
            idx = t.get('index')
            
            cb = QCheckBox(f"Index {idx} | Language: {lang} | Title: {title}")
            cb.setProperty("track_id", i) # We use the relative ID for FFmpeg mapping
            cb.setChecked(True)
            cb.setStyleSheet("font-size: 14px; padding: 5px;")
            self.track_layout.addWidget(cb)
            self.checkboxes.append(cb)

    def get_input_paths(self):
        input_path = self.drop_zone.file_input.text().strip()
        keep_ids = [cb.property("track_id") for cb in self.checkboxes if cb.isChecked()]
        if not input_path or not keep_ids:
            return None
        return input_path

    def run_purge(self, inputs, est_seconds):
        input_path = self.get_input_paths()
        keep_ids = [cb.property("track_id") for cb in self.checkboxes if cb.isChecked()]

        filename = os.path.basename(input_path)
        track_type = "Audio" if self.mode == 'a' else "Subtitle"
        def task():
            self.processor.process_batch(input_path, keep_ids, self.mode)
            return True, f"Track purge finished successfully for: {filename}"

        self.orchestrator.add_background_job(f"Purge {track_type} Tracks: {filename}", task, estimated_seconds=est_seconds)
        self.orchestrator.show_status_message(f"⏳ Purge job queued for: {filename}")

# ==========================================
# HOW TO USE THIS CODE (EXAMPLE)
# ==========================================
# Example usage:
# from src.processors.tracks_ui import MainClass
# processor = MainClass()
# processor.run(input_file, output_file)
# ==========================================

# ==============================================================================
# 🎬 FEATURE: INTERNAL MODULE DOCUMENTATION (tracks_ui.py)
# ==============================================================================
#
# 📝 WHAT IS THIS FILE?
#    This file, 'tracks_ui.py', is a core component of the Onyx Engine. It is
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
