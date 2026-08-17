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
        
        # Mode Buttons Navigation
        self.mode_btn_layout = QHBoxLayout()
        self.mode_btns = []
        
        btn_configs = [
            ("📄 Single File", 0),
            ("📂 1:1 Smart Folder", 1)
        ]
        if self.mode == 'subtitle':
            btn_configs.append(("📚 Multi-Subtitle Folder", 2))

        for text, idx in btn_configs:
            btn = QPushButton(text)
            btn.setCheckable(True)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.setStyleSheet("""
                QPushButton {
                    background-color: #222222;
                    border: 1px solid #333333;
                    padding: 8px 15px;
                    border-radius: 6px;
                    font-weight: bold;
                    color: #bbbbbb;
                }
                QPushButton:hover {
                    background-color: #333333;
                    color: #ffffff;
                }
                QPushButton:checked {
                    background-color: #2D72D9;
                    border-color: #2D72D9;
                    color: #ffffff;
                }
            """)
            btn.clicked.connect(lambda checked, i=idx: self.set_active_mode(i))
            self.mode_btn_layout.addWidget(btn)
            self.mode_btns.append(btn)

        header.addLayout(self.mode_btn_layout)
        
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
        self.folder_drop = DropZone(self, mode='dir')
        fp_layout.addWidget(self.folder_drop)
        fp_layout.addStretch()
        
        self.mode_stack.addWidget(self.folder_page)

        # PAGE 2: MULTI-SUBTITLE FOLDER MODE (Subtitle Mode Only)
        if self.mode == 'subtitle':
            self.multi_sub_page = QWidget()
            msp_layout = QVBoxLayout(self.multi_sub_page)
            msp_layout.setContentsMargins(0,0,0,0)

            ms_instruction_box = QFrame()
            ms_instruction_box.setStyleSheet("background-color: #1a1a1a; border: 1px solid #333; border-radius: 8px; padding: 15px;")
            ms_ib_layout = QVBoxLayout(ms_instruction_box)
            ms_ib_layout.addWidget(QLabel("<b>Multi-Subtitle Folder Mode Rules:</b>"))
            ms_ib_layout.addWidget(QLabel("1. Place 1 Video file and ALL Subtitle files (.srt, .ass, .vtt) in a single folder."))
            ms_ib_layout.addWidget(QLabel("2. Onyx Engine will embed ALL subtitle tracks into the video file simultaneously."))
            ms_ib_layout.addWidget(QLabel("3. Subtitle track labels in media players will be derived automatically from their filenames!"))
            msp_layout.addWidget(ms_instruction_box)

            msp_layout.addSpacing(15)
            msp_layout.addWidget(QLabel("Master Video File (Optional - leave empty to auto-detect video in folder):"))
            self.multi_sub_video_drop = DropZone(self)
            msp_layout.addWidget(self.multi_sub_video_drop)

            msp_layout.addSpacing(15)
            msp_layout.addWidget(QLabel("Select Folder Containing Subtitle Files (.srt, .ass, .vtt):"))
            self.multi_sub_folder_drop = DropZone(self, mode='dir')
            msp_layout.addWidget(self.multi_sub_folder_drop)
            msp_layout.addStretch()

            self.mode_stack.addWidget(self.multi_sub_page)

        layout.addWidget(self.mode_stack)

        # Set default selection
        self.set_active_mode(0)

        # --- 3. EXECUTION FOOTER ---
        layout.addStretch()
        self.exec_btn = SmartRunButton("⚡ Execute Sync Engine", self.get_input_paths, self.run_process, speed_multiplier=20.0)
        layout.addWidget(self.exec_btn)

    def set_active_mode(self, index: int):
        self.mode_stack.setCurrentIndex(index)
        for idx, btn in enumerate(self.mode_btns):
            btn.setChecked(idx == index)

    def get_input_paths(self):
        curr_idx = self.mode_stack.currentIndex()
        if curr_idx == 0:
            v_path = self.video_drop.file_input.text().strip()
            e_path = self.extra_drop.file_input.text().strip()
            if not v_path or not e_path: return None
            return v_path
        elif curr_idx == 1:
            f_path = self.folder_drop.file_input.text().strip()
            if not f_path: return None
            if os.path.isfile(f_path):
                f_path = os.path.dirname(f_path)
            if not os.path.isdir(f_path): return None
            return f_path
        elif curr_idx == 2:
            f_path = self.multi_sub_folder_drop.file_input.text().strip()
            v_path = self.multi_sub_video_drop.file_input.text().strip()
            if v_path and os.path.isfile(v_path):
                return v_path
            if f_path:
                if os.path.isfile(f_path):
                    f_path = os.path.dirname(f_path)
                if os.path.isdir(f_path):
                    return f_path
            return None

    def run_process(self, inputs, est_seconds):
        curr_idx = self.mode_stack.currentIndex()
        if curr_idx == 0:
            # --- SINGLE MODE ---
            v_path = self.video_drop.file_input.text().strip()
            e_path = self.extra_drop.file_input.text().strip()
            
            if not v_path or not e_path:
                return

            base_name, ext = os.path.splitext(os.path.basename(v_path))
            if self.mode == 'subtitle':
                output = os.path.join(os.path.dirname(v_path), f"{base_name}_subs_added{ext}")
            else:
                output = os.path.join(os.path.dirname(v_path), f"Onyx_Merged_{base_name}{ext}")
            filename = os.path.basename(v_path)
            
            def task():
                if self.mode == 'audio':
                    ok = self.engine.merge_video_audio(v_path, e_path, output)
                else:
                    ok = self.engine.mux_subtitles(v_path, e_path, output)
                if ok:
                    return True, f"Sync completed successfully. Saved to: {output}"
                else:
                    return False, f"Sync failed for: {filename}"
            
            self.orchestrator.add_background_job(f"Mux Single: {filename}", task, estimated_seconds=est_seconds, local_widget=self.exec_btn)
            self.orchestrator.show_status_message(f"⏳ Single Muxing job queued for: {filename}")
            
        elif curr_idx == 1:
            # --- BATCH 1:1 MODE ---
            folder = self.folder_drop.file_input.text().strip()
            if os.path.isfile(folder):
                folder = os.path.dirname(folder)
            if not folder or not os.path.isdir(folder):
                return
                
            foldername = os.path.basename(folder)
            
            def task():
                res = self.engine.batch_process_folder(folder, self.mode)
                if isinstance(res, tuple):
                    return res[0], res[1]
                return bool(res), f"Smart Folder sync finished for: {folder}"
                
            self.orchestrator.add_background_job(f"Mux Folder: {foldername}", task, estimated_seconds=est_seconds, local_widget=self.exec_btn)
            self.orchestrator.show_status_message(f"⏳ Smart Folder Mux job queued for: {foldername}")

        elif curr_idx == 2:
            # --- MULTI-SUBTITLE FOLDER MODE ---
            folder = self.multi_sub_folder_drop.file_input.text().strip()
            v_path = self.multi_sub_video_drop.file_input.text().strip()

            if folder and os.path.isfile(folder):
                folder = os.path.dirname(folder)
            if not folder or not os.path.isdir(folder):
                if v_path and os.path.isfile(v_path):
                    folder = os.path.dirname(v_path)
                else:
                    return

            foldername = os.path.basename(folder)

            def task():
                if v_path and os.path.isfile(v_path):
                    # Master video explicitly specified
                    sub_files = [
                        os.path.join(folder, f) for f in sorted(os.listdir(folder))
                        if f.lower().endswith(self.engine.sub_exts) and not (
                            f.startswith("Onyx_Merged_") or "_subs_added" in f or "_all_subs" in f
                        )
                    ]
                    if not sub_files:
                        return False, "No subtitle files found in specified folder."

                    base_name, ext = os.path.splitext(os.path.basename(v_path))
                    output_path = os.path.join(os.path.dirname(v_path), f"{base_name}_all_subs{ext}")
                    success = self.engine.mux_multiple_subtitles(v_path, sub_files, output_path)
                    return success, f"Multi-Subtitle muxing complete: {output_path}" if success else "Failed to mux subtitles."
                else:
                    res = self.engine.batch_process_multi_subtitles_folder(folder)
                    if isinstance(res, tuple):
                        return res[0], res[1]
                    return bool(res), f"Multi-Subtitle Folder batch finished for: {folder}"

            self.orchestrator.add_background_job(f"Multi-Sub Mux: {foldername}", task, estimated_seconds=est_seconds, local_widget=self.exec_btn)
            self.orchestrator.show_status_message(f"⏳ Multi-Subtitle Mux job queued for: {foldername}")

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
