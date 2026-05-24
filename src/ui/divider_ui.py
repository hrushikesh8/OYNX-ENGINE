import os
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
                             QLabel, QFrame, QLineEdit, QTabWidget, QSlider)
from PyQt6.QtCore import Qt
from src.ui.custom_widgets import DropZone
from src.processors.division import VideoDivider
from src.processors.editor import VideoEditor
from src.processors.silence_remover import SilenceRemover

class DividerUI(QWidget):
    """
    Workspace for dividing and trimming videos.
    Tab 1: Intermission Splitter (cuts movie exactly in half).
    Tab 2: Chunk Divider (splits into WhatsApp-friendly clips).
    Tab 3: Shorts Creator (converts to vertical 9:16 with blur background).
    Tab 4: Silence Remover (auto-trims dead space losslessly).
    """
    def __init__(self, back_callback, orchestrator):
        super().__init__()
        self.orchestrator = orchestrator
        self.divider = VideoDivider()
        self.editor = VideoEditor()
        self.silence_remover = SilenceRemover()

        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        layout.setContentsMargins(30, 30, 30, 30)

        # --- HEADER ---
        header = QHBoxLayout()
        back_btn = QPushButton("⬅ Back to Dashboard")
        back_btn.clicked.connect(back_callback)
        header.addWidget(back_btn)
        
        title = QLabel("🎬 Edit, Divide & Auto-Trim")
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

        self.setup_intermission_tab()
        self.setup_chunks_tab()
        self.setup_shorts_tab()
        self.setup_silence_tab()

    # =========================================================================
    # TAB 1: INTERMISSION SPLITTER
    # =========================================================================
    def setup_intermission_tab(self):
        tab = QWidget()
        t_layout = QVBoxLayout(tab)
        t_layout.setContentsMargins(20, 20, 20, 20)

        t_layout.addWidget(QLabel("Step 1: Drop Movie File"))
        self.int_drop = DropZone(self)
        t_layout.addWidget(self.int_drop)
        t_layout.addSpacing(15)

        t_layout.addWidget(QLabel("Step 2: Enter Timestamp to Cut (seconds or HH:MM:SS)"))
        self.int_time = QLineEdit("01:00:00")
        self.int_time.setStyleSheet("background-color: #222; border: 1px solid #333; color: white; padding: 10px; border-radius: 5px;")
        t_layout.addWidget(self.int_time)
        t_layout.addSpacing(25)

        self.int_btn = QPushButton("✂️ Split at Intermission (Lossless)")
        self.int_btn.setMinimumHeight(60)
        self.int_btn.setStyleSheet("background-color: #2D72D9; color: white; font-size: 16px; font-weight: bold; border-radius: 8px;")
        self.int_btn.clicked.connect(self.run_intermission)
        t_layout.addWidget(self.int_btn)
        t_layout.addStretch()

        self.tabs.addTab(tab, "⏸️ Intermission Cut")

    def run_intermission(self):
        path = self.int_drop.file_input.text().strip()
        time_val = self.int_time.text().strip()
        if not path or not time_val:
            return

        filename = os.path.basename(path)
        def task():
            success, p1, p2 = self.divider.split_at_intermission(path, time_val)
            return success, f"First Half: {p1}\nSecond Half: {p2}" if success else "Split failed."

        self.orchestrator.add_background_job(f"Intermission Cut: {filename}", task)
        self.orchestrator.show_status_message(f"⏳ Intermission Cut queued for: {filename}")

    # =========================================================================
    # TAB 2: CHUNK DIVIDER
    # =========================================================================
    def setup_chunks_tab(self):
        tab = QWidget()
        t_layout = QVBoxLayout(tab)
        t_layout.setContentsMargins(20, 20, 20, 20)

        t_layout.addWidget(QLabel("Step 1: Drop Video File"))
        self.chunk_drop = DropZone(self)
        t_layout.addWidget(self.chunk_drop)
        t_layout.addSpacing(15)

        t_layout.addWidget(QLabel("Step 2: Enter Chunk Segment Duration (seconds)"))
        self.chunk_time = QLineEdit("30")
        self.chunk_time.setStyleSheet("background-color: #222; border: 1px solid #333; color: white; padding: 10px; border-radius: 5px;")
        t_layout.addWidget(self.chunk_time)
        t_layout.addSpacing(25)

        self.chunk_btn = QPushButton("✂️ Divide into Chunks (Lossless)")
        self.chunk_btn.setMinimumHeight(60)
        self.chunk_btn.setStyleSheet("background-color: #2D72D9; color: white; font-size: 16px; font-weight: bold; border-radius: 8px;")
        self.chunk_btn.clicked.connect(self.run_chunks)
        t_layout.addWidget(self.chunk_btn)
        t_layout.addStretch()

        self.tabs.addTab(tab, "🧩 Chunk Divider")

    def run_chunks(self):
        path = self.chunk_drop.file_input.text().strip()
        time_val = self.chunk_time.text().strip()
        if not path or not time_val:
            return

        filename = os.path.basename(path)
        def task():
            return self.divider.split_by_chunks(path, time_val)

        self.orchestrator.add_background_job(f"Chunk Split: {filename}", task)
        self.orchestrator.show_status_message(f"⏳ Chunk Split queued for: {filename}")

    # =========================================================================
    # TAB 3: 9:16 SHORTS CREATOR
    # =========================================================================
    def setup_shorts_tab(self):
        tab = QWidget()
        t_layout = QVBoxLayout(tab)
        t_layout.setContentsMargins(20, 20, 20, 20)

        t_layout.addWidget(QLabel("Step 1: Drop Widescreen (Landscape) Video File"))
        self.shorts_drop = DropZone(self)
        t_layout.addWidget(self.shorts_drop)
        t_layout.addSpacing(25)

        self.shorts_btn = QPushButton("📱 Convert to Vertical 9:16 Short (Re-encode)")
        self.shorts_btn.setMinimumHeight(60)
        self.shorts_btn.setStyleSheet("background-color: #2D72D9; color: white; font-size: 16px; font-weight: bold; border-radius: 8px;")
        self.shorts_btn.clicked.connect(self.run_shorts)
        t_layout.addWidget(self.shorts_btn)
        t_layout.addStretch()

        self.tabs.addTab(tab, "📱 9:16 Shorts Creator")

    def run_shorts(self):
        path = self.shorts_drop.file_input.text().strip()
        if not path:
            return

        base_dir = os.path.dirname(path)
        filename = os.path.basename(path)
        name, ext = os.path.splitext(filename)
        output_path = os.path.join(base_dir, f"{name}_shorts{ext}")

        def task():
            return self.editor.convert_to_shorts_style(path, output_path)

        self.orchestrator.add_background_job(f"9:16 Short: {name}", task)
        self.orchestrator.show_status_message(f"⏳ Shorts Creator queued for: {filename}")

    # =========================================================================
    # TAB 4: SILENCE REMOVER (AUTO-TRIM)
    # =========================================================================
    def setup_silence_tab(self):
        tab = QWidget()
        t_layout = QVBoxLayout(tab)
        t_layout.setContentsMargins(20, 20, 20, 20)

        t_layout.addWidget(QLabel("Step 1: Drop Video/Audio File"))
        self.sil_drop = DropZone(self)
        t_layout.addWidget(self.sil_drop)
        t_layout.addSpacing(15)

        # Noise threshold slider
        t_layout.addWidget(QLabel("Step 2: Noise Threshold (dB) - Lower values detect only near-perfect silence"))
        self.threshold_slider = QSlider(Qt.Orientation.Horizontal)
        self.threshold_slider.setRange(-60, -10)
        self.threshold_slider.setValue(-35)
        
        self.th_val_label = QLabel("Current Threshold: -35 dB (Recommended)")
        self.th_val_label.setStyleSheet("color: #aaa; font-style: italic;")
        self.threshold_slider.valueChanged.connect(lambda val: self.th_val_label.setText(f"Current Threshold: {val} dB"))

        t_layout.addWidget(self.threshold_slider)
        t_layout.addWidget(self.th_val_label)
        t_layout.addSpacing(15)

        t_layout.addWidget(QLabel("Step 3: Minimum Silence Duration (seconds)"))
        self.sil_dur = QLineEdit("0.5")
        self.sil_dur.setStyleSheet("background-color: #222; border: 1px solid #333; color: white; padding: 10px; border-radius: 5px;")
        t_layout.addWidget(self.sil_dur)
        t_layout.addSpacing(25)

        self.sil_btn = QPushButton("🔇 Auto-Trim Silent Intervals (Lossless Concat)")
        self.sil_btn.setMinimumHeight(60)
        self.sil_btn.setStyleSheet("background-color: #00ff66; color: #111; font-size: 16px; font-weight: bold; border-radius: 8px;")
        self.sil_btn.clicked.connect(self.run_silence)
        t_layout.addWidget(self.sil_btn)
        t_layout.addStretch()

        self.tabs.addTab(tab, "🔇 Silence Remover")

    def run_silence(self):
        path = self.sil_drop.file_input.text().strip()
        noise = self.threshold_slider.value()
        try:
            dur = float(self.sil_dur.text().strip())
        except ValueError:
            dur = 0.5

        if not path:
            return

        base_dir = os.path.dirname(path)
        filename = os.path.basename(path)
        name, ext = os.path.splitext(filename)
        output_path = os.path.join(base_dir, f"{name}_trimmed{ext}")

        def task():
            return self.silence_remover.remove_silence(path, output_path, noise_db=noise, min_silence_len=dur)

        self.orchestrator.add_background_job(f"Auto-Trim: {name}", task)
        self.orchestrator.show_status_message(f"⏳ Silence Remover task queued for: {filename}")
