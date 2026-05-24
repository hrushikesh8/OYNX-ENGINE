import os
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
                             QLabel, QFrame, QLineEdit, QComboBox, QTabWidget)
from PyQt6.QtCore import Qt
from src.ui.custom_widgets import DropZone
from src.processors.extractor import AudioExtractor

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
        back_btn = QPushButton("⬅ Back to Dashboard")
        back_btn.clicked.connect(back_callback)
        header.addWidget(back_btn)
        
        title = QLabel("🎵 Audio Extractor & Mass Harvester")
        title.setStyleSheet("font-size: 22px; font-weight: bold;")
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

        self.exec_single_btn = QPushButton("🚀 Extract Audio Stream")
        self.exec_single_btn.setMinimumHeight(60)
        self.exec_single_btn.setStyleSheet("background-color: #2D72D9; color: white; font-size: 16px; font-weight: bold; border-radius: 8px;")
        self.exec_single_btn.clicked.connect(self.run_single_extraction)
        t_layout.addWidget(self.exec_single_btn)
        t_layout.addStretch()

        self.tabs.addTab(tab, "📄 Single Extractor")

    def run_single_extraction(self):
        path = self.single_drop.file_input.text().strip()
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

        self.orchestrator.add_background_job(f"Audio Extract: {filename}", task)
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

        self.exec_batch_btn = QPushButton("🌾 Run Mass Audio Harvester")
        self.exec_batch_btn.setMinimumHeight(60)
        self.exec_batch_btn.setStyleSheet("background-color: #00ff66; color: #111; font-size: 16px; font-weight: bold; border-radius: 8px;")
        self.exec_batch_btn.clicked.connect(self.run_batch_extraction)
        t_layout.addWidget(self.exec_batch_btn)
        t_layout.addStretch()

        self.tabs.addTab(tab, "📂 Mass Harvester")

    def run_batch_extraction(self):
        folder = self.batch_drop.file_input.text().strip()
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

        self.orchestrator.add_background_job(f"Mass Harvester: {foldername}", task)
        self.orchestrator.show_status_message(f"⏳ Mass Harvester task queued for folder: {foldername}")
