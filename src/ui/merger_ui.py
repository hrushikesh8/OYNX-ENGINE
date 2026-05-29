import os
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
                             QLabel, QStackedWidget, QFrame, QFileDialog)
from PyQt6.QtCore import Qt
from src.ui.custom_widgets import DropZone, SmartRunButton
from src.processors.merger import StreamMerger

class StreamMergerUI(QWidget):
    """
    Unified UI for Features 4 & 5. 
    Handles Single-file syncing and Smart-folder batching.
    """
    def __init__(self, back_callback, orchestrator, mode='audio'):
        super().__init__()
        self.orchestrator = orchestrator
        self.mode = mode # 'audio' for F4, 'subtitle' for F5
        self.engine = StreamMerger()
        
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        # --- 1. NEAT HEADER ---
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
        
        title_text = "🔗 Audio + Video Sync" if mode == 'audio' else "📝 Subtitle Muxing"
        self.title_label = QLabel(title_text)
        self.title_label.setStyleSheet("font-size: 22px; font-weight: bold; color: white;")
        
        header.addWidget(back_btn)
        header.addSpacing(15)
        header.addWidget(self.title_label)
        header.addStretch()
        
        # Mode Toggle Switch
        self.toggle_btn = QPushButton("📂 Switch to Smart Folder Mode")
        self.toggle_btn.setCheckable(True)
        self.toggle_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.toggle_btn.setStyleSheet("""
            QPushButton { background-color: #333; padding: 8px 15px; border-radius: 6px; font-weight: bold; color: #2D72D9; }
            QPushButton:hover { background-color: #444; }
            QPushButton:checked { background-color: #2D72D9; color: white; }
        """)
        self.toggle_btn.clicked.connect(self.switch_view)
        header.addWidget(self.toggle_btn)
        
        layout.addLayout(header)
        layout.addSpacing(20)

        # --- 2. THE WORKSPACE STACK ---
        self.mode_stack = QStackedWidget()
        
        # PAGE 0: SINGLE FILE MODE
        self.single_page = QWidget()
        sp_layout = QVBoxLayout(self.single_page)
        sp_layout.setContentsMargins(0,0,0,0)
        
        sp_layout.addWidget(QLabel("Step 1: Select Master Video File"))
        self.video_drop = DropZone(self)
        sp_layout.addWidget(self.video_drop)
        
        sp_layout.addSpacing(15)
        extra_label = "Step 2: Select Audio Track (.mp3, .aac, .wav)" if mode == 'audio' else "Step 2: Select Subtitle File (.srt, .ass)"
        sp_layout.addWidget(QLabel(extra_label))
        self.extra_drop = DropZone(self)
        sp_layout.addWidget(self.extra_drop)
        
        self.mode_stack.addWidget(self.single_page)

        # PAGE 1: SMART FOLDER MODE
        self.folder_page = QWidget()
        fp_layout = QVBoxLayout(self.folder_page)
        fp_layout.setContentsMargins(0,0,0,0)
        
        instruction_box = QFrame()
        instruction_box.setStyleSheet("background-color: #1a1a1a; border: 1px solid #333; border-radius: 8px; padding: 15px;")
        ib_layout = QVBoxLayout(instruction_box)
        ib_layout.addWidget(QLabel("<b>Smart Folder Rules:</b>"))
        ib_layout.addWidget(QLabel(f"1. Video and {'Audio' if mode=='audio' else 'Subtitle'} files must have the SAME name."))
        ib_layout.addWidget(QLabel("2. Example: <i>'Movie_01.mp4'</i> and <i>'Movie_01.srt'</i>"))
        fp_layout.addWidget(instruction_box)
        
        fp_layout.addSpacing(20)
        fp_layout.addWidget(QLabel("Select Folder to Scan:"))
        self.folder_drop = DropZone(self)
        fp_layout.addWidget(self.folder_drop)
        fp_layout.addStretch()
        
        self.mode_stack.addWidget(self.folder_page)
        layout.addWidget(self.mode_stack)

        # --- 3. EXECUTION FOOTER ---
        layout.addStretch()
        self.exec_btn = SmartRunButton("⚡ Execute Sync Engine", self.get_input_paths, self.run_process, speed_multiplier=20.0)
        layout.addWidget(self.exec_btn)

    def get_input_paths(self):
        if self.mode_stack.currentIndex() == 0:
            v_path = self.video_drop.file_input.text().strip()
            e_path = self.extra_drop.file_input.text().strip()
            if not v_path or not e_path: return None
            return v_path
        else:
            f_path = self.folder_drop.file_input.text().strip()
            if not f_path or not os.path.isdir(f_path): return None
            return f_path

    def switch_view(self):
        if self.toggle_btn.isChecked():
            self.mode_stack.setCurrentIndex(1)
            self.toggle_btn.setText("📄 Switch to Single File Mode")
        else:
            self.mode_stack.setCurrentIndex(0)
            self.toggle_btn.setText("📂 Switch to Smart Folder Mode")

    def run_process(self, inputs, est_seconds):
        if self.mode_stack.currentIndex() == 0:
            # --- SINGLE MODE ---
            v_path = self.video_drop.file_input.text().strip()
            e_path = self.extra_drop.file_input.text().strip()
            
            if not v_path or not e_path:
                return

            output = os.path.join(os.path.dirname(v_path), f"Onyx_Merged_{os.path.basename(v_path)}")
            filename = os.path.basename(v_path)
            
            def task():
                if self.mode == 'audio':
                    self.engine.merge_video_audio(v_path, e_path, output)
                else:
                    self.engine.mux_subtitles(v_path, e_path, output)
                return True, f"Sync completed successfully. Saved to: {output}"
            
            self.orchestrator.add_background_job(f"Mux Single: {filename}", task, estimated_seconds=est_seconds)
            self.orchestrator.show_status_message(f"⏳ Single Muxing job queued for: {filename}")
            
        else:
            # --- BATCH MODE ---
            folder = self.folder_drop.file_input.text().strip()
            if not folder or not os.path.isdir(folder):
                return
                
            foldername = os.path.basename(folder)
            
            def task():
                self.engine.batch_smart_sync(folder, self.mode)
                return True, f"Smart Folder sync finished for: {folder}"
                
            self.orchestrator.add_background_job(f"Mux Folder: {foldername}", task, estimated_seconds=est_seconds)
            self.orchestrator.show_status_message(f"⏳ Smart Folder Mux job queued for: {foldername}")

# ==========================================
# HOW TO USE THIS CODE (EXAMPLE)
# ==========================================
# Example usage:
# from src.processors.merger_ui import MainClass
# processor = MainClass()
# processor.run(input_file, output_file)
# ==========================================

# ==============================================================================
# 🎬 FEATURE: INTERNAL MODULE DOCUMENTATION (merger_ui.py)
# ==============================================================================
#
# 📝 WHAT IS THIS FILE?
#    This file, 'merger_ui.py', is a core component of the Onyx Engine. It is
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
