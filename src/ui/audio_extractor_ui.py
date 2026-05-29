import os
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
                             QLabel, QFrame, QLineEdit, QComboBox, QTabWidget)
from PyQt6.QtCore import Qt
from src.ui.custom_widgets import DropZone, SmartRunButton
from src.processors.extractor import AudioExtractor
from src.processors.transcription import AudioTranscriber

class AudioExtractorUI(QWidget):
    """
    Workspace for Audio Extraction.
    Tab 1: Single Video Extractor (extracts specific track to audio formats).
    Tab 2: Folder Mass Harvester (recursively rips audio from all videos in a folder).
    """
    def __init__(self, back_callback, orchestrator):
        super().__init__()
        self.orchestrator = orchestrator
        self.extractor = AudioExtractor()

        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        layout.setContentsMargins(30, 30, 30, 30)

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
        
        title = QLabel("🎵 Audio Extractor & Mass Harvester")
        title.setStyleSheet("font-size: 22px; font-weight: bold; color: white;")
        header.addWidget(title)
        header.addStretch()
        layout.addLayout(header)
        layout.addSpacing(15)

        # --- TABS WORKSPACE ---
        self.tabs = QTabWidget()
        self.tabs.setStyleSheet("""
            QTabWidget::pane { border: 1px solid #282828; background: #121212; border-radius: 8px; }
            QTabBar::tab { background: #1a1a1a; padding: 10px 20px; font-weight: bold; border-top-left-radius: 6px; border-top-right-radius: 6px; margin-right: 5px; color: #888; }
            QTabBar::tab:selected { background: #2D72D9; color: white; }
            QTabBar::tab:hover { background: #252525; }
        """)
        layout.addWidget(self.tabs)

        self.setup_single_tab()
        self.setup_batch_tab()
        self.setup_transcribe_tab()

    # =========================================================================
    # TAB 1: SINGLE EXTRACTION
    # =========================================================================
    def setup_single_tab(self):
        tab = QWidget()
        t_layout = QVBoxLayout(tab)
        t_layout.setContentsMargins(20, 20, 20, 20)

        t_layout.addWidget(QLabel("Step 1: Select Master Video File"))
        self.single_drop = DropZone(self)
        t_layout.addWidget(self.single_drop)
        t_layout.addSpacing(15)

        # Format and Track options
        opts_layout = QHBoxLayout()
        
        v_layout1 = QVBoxLayout()
        v_layout1.addWidget(QLabel("Output Audio Format:"))
        self.format_combo = QComboBox()
        self.format_combo.addItems(["mp3", "wav", "original", "aac"])
        self.format_combo.setMinimumHeight(40)
        v_layout1.addWidget(self.format_combo)
        opts_layout.addLayout(v_layout1)

        v_layout2 = QVBoxLayout()
        v_layout2.addWidget(QLabel("Track ID to Extract (0 = Main, 1 = Dub, etc.):"))
        self.track_id_input = QLineEdit("0")
        self.track_id_input.setMinimumHeight(40)
        self.track_id_input.setStyleSheet("background-color: #222; border: 1px solid #333; color: white; padding: 5px; border-radius: 4px;")
        v_layout2.addWidget(self.track_id_input)
        opts_layout.addLayout(v_layout2)

        t_layout.addLayout(opts_layout)
        t_layout.addSpacing(25)

        self.exec_single_btn = SmartRunButton("🚀 Extract Audio Stream", self.get_single_input, self.run_single_extraction, speed_multiplier=10.0)
        t_layout.addWidget(self.exec_single_btn)
        t_layout.addStretch()

        self.tabs.addTab(tab, "📄 Single Extractor")

    def get_single_input(self):
        path = self.single_drop.file_input.text().strip()
        return path if path else None

    def run_single_extraction(self, inputs, est_seconds):
        path = self.get_single_input()
        fmt = self.format_combo.currentText()
        try:
            track_id = int(self.track_id_input.text().strip())
        except ValueError:
            track_id = 0

        if not path:
            return

        filename = os.path.basename(path)
        def task():
            success, out = self.extractor.extract_audio(path, output_format=fmt, track_id=track_id)
            return success, f"Audio saved to: {out}" if success else "Audio extraction failed."

        self.orchestrator.add_background_job(f"Audio Extract: {filename}", task, estimated_seconds=est_seconds)
        self.orchestrator.show_status_message(f"⏳ Extraction task queued for: {filename}")

    # =========================================================================
    # TAB 2: BATCH FOLDER HARVESTER
    # =========================================================================
    def setup_batch_tab(self):
        tab = QWidget()
        t_layout = QVBoxLayout(tab)
        t_layout.setContentsMargins(20, 20, 20, 20)

        t_layout.addWidget(QLabel("Step 1: Select Source Folder to Scan"))
        self.batch_drop = DropZone(self, mode='dir')
        t_layout.addWidget(self.batch_drop)
        t_layout.addSpacing(15)

        # Format and Track options for batch
        opts_layout = QHBoxLayout()
        
        v_layout1 = QVBoxLayout()
        v_layout1.addWidget(QLabel("Output Audio Format:"))
        self.batch_format_combo = QComboBox()
        self.batch_format_combo.addItems(["mp3", "wav", "original", "aac"])
        self.batch_format_combo.setMinimumHeight(40)
        v_layout1.addWidget(self.batch_format_combo)
        opts_layout.addLayout(v_layout1)

        v_layout2 = QVBoxLayout()
        v_layout2.addWidget(QLabel("Track ID to Extract (applied globally):"))
        self.batch_track_id_input = QLineEdit("0")
        self.batch_track_id_input.setMinimumHeight(40)
        self.batch_track_id_input.setStyleSheet("background-color: #222; border: 1px solid #333; color: white; padding: 5px; border-radius: 4px;")
        v_layout2.addWidget(self.batch_track_id_input)
        opts_layout.addLayout(v_layout2)

        t_layout.addLayout(opts_layout)
        t_layout.addSpacing(25)

        self.exec_batch_btn = SmartRunButton("🌾 Run Mass Audio Harvester", self.get_batch_input, self.run_batch_extraction, speed_multiplier=10.0)
        t_layout.addWidget(self.exec_batch_btn)
        t_layout.addStretch()

        self.tabs.addTab(tab, "📂 Mass Harvester")

    def get_batch_input(self):
        folder = self.batch_drop.file_input.text().strip()
        if not folder or not os.path.isdir(folder):
            return None
        return folder

    def run_batch_extraction(self, inputs, est_seconds):
        folder = self.get_batch_input()
        fmt = self.batch_format_combo.currentText()
        try:
            track_id = int(self.batch_track_id_input.text().strip())
        except ValueError:
            track_id = 0

        if not folder or not os.path.isdir(folder):
            return

        foldername = os.path.basename(folder)
        def task():
            return self.extractor.extract_folder(folder, output_format=fmt, track_id=track_id)

        self.orchestrator.add_background_job(f"Mass Harvester: {foldername}", task, estimated_seconds=est_seconds)
        self.orchestrator.show_status_message(f"⏳ Mass Harvester task queued for folder: {foldername}")

    # =========================================================================
    # TAB 3: AI SUBTITLE TRANSCRIBER (Speech-to-Text)
    # =========================================================================
    def setup_transcribe_tab(self):
        tab = QWidget()
        t_layout = QVBoxLayout(tab)
        t_layout.setContentsMargins(20, 20, 20, 20)

        t_layout.addWidget(QLabel("Step 1: Select Video File for Auto-Transcription"))
        self.trans_vid_drop = DropZone(self)
        t_layout.addWidget(self.trans_vid_drop)
        t_layout.addSpacing(15)

        opts_layout = QHBoxLayout()
        v_layout1 = QVBoxLayout()
        v_layout1.addWidget(QLabel("Whisper AI Model (smaller is faster):"))
        self.trans_model_combo = QComboBox()
        self.trans_model_combo.addItems(["tiny", "base", "small", "medium"])
        self.trans_model_combo.setMinimumHeight(40)
        v_layout1.addWidget(self.trans_model_combo)
        opts_layout.addLayout(v_layout1)

        v_layout2 = QVBoxLayout()
        v_layout2.addWidget(QLabel("Language Code (e.g. 'en', 'es', blank for auto):"))
        self.trans_lang_input = QLineEdit()
        self.trans_lang_input.setPlaceholderText("auto")
        self.trans_lang_input.setMinimumHeight(40)
        self.trans_lang_input.setStyleSheet("background-color: #222; border: 1px solid #333; color: white; padding: 5px; border-radius: 4px;")
        v_layout2.addWidget(self.trans_lang_input)
        opts_layout.addLayout(v_layout2)

        t_layout.addLayout(opts_layout)
        t_layout.addSpacing(25)

        self.exec_trans_btn = SmartRunButton("🎙️ Start Auto-Transcription (Speech-to-Text)", self.get_transcribe_input, self.run_transcription, speed_multiplier=self.get_transcribe_speed)
        t_layout.addWidget(self.exec_trans_btn)
        t_layout.addStretch()

        self.tabs.addTab(tab, "🎙️ AI Transcriber")

    def get_transcribe_input(self):
        video = self.trans_vid_drop.file_input.text().strip()
        return video if video else None

    def get_transcribe_speed(self):
        model = self.trans_model_combo.currentText()
        if model == "tiny": return 10.0
        if model == "base": return 5.0
        if model == "small": return 2.0
        return 1.0

    def run_transcription(self, inputs, est_seconds):
        video = self.get_transcribe_input()
        lang = self.trans_lang_input.text().strip() or None
        model = self.trans_model_combo.currentText()

        if not video:
            return

        base_dir = os.path.dirname(video)
        name, _ = os.path.splitext(os.path.basename(video))
        output_srt = os.path.join(base_dir, f"{name}.srt")

        def task():
            transcriber = AudioTranscriber()
            success = transcriber.transcribe(video, output_srt, language=lang, model_name=model)
            return success, f"Transcription completed. Subtitle saved at: {output_srt}" if success else "Transcription failed."

        self.orchestrator.add_background_job(f"Transcribe: {name}", task, estimated_seconds=est_seconds)
        self.orchestrator.show_status_message(f"⏳ Transcription queued for: {name}")


# ==========================================
# HOW TO USE THIS CODE (EXAMPLE)
# ==========================================
# Example usage:
# from src.processors.audio_extractor_ui import MainClass
# processor = MainClass()
# processor.run(input_file, output_file)
# ==========================================

# ==============================================================================
# 🎬 FEATURE: INTERNAL MODULE DOCUMENTATION (audio_extractor_ui.py)
# ==============================================================================
#
# 📝 WHAT IS THIS FILE?
#    This file, 'audio_extractor_ui.py', is a core component of the Onyx Engine. It is
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
