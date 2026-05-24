import os
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
                             QLabel, QFrame, QComboBox, QLineEdit, QTabWidget)
from PyQt6.QtCore import Qt
from src.ui.custom_widgets import DropZone
from src.processors.watermark import Watermarker
from src.processors.watermark_remover import get_watermark_coords
from src.processors.gif_maker import GifMaker

class BrandingUI(QWidget):
    """
    Workspace for VFX, Branding, and GIF creation.
    Tab 1: Watermark Burner (overlaying custom PNG/JPG logos onto video).
    Tab 2: Watermark Remover (interactive Region of Interest delogo brush).
    Tab 3: HD GIF Maker (custom start time, duration, and Lanczos palette scaling).
    """
    def __init__(self, back_callback, orchestrator):
        super().__init__()
        self.orchestrator = orchestrator
        self.watermarker = Watermarker()
        self.gif_maker = GifMaker()

        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        layout.setContentsMargins(30, 30, 30, 30)

        # --- HEADER ---
        header = QHBoxLayout()
        back_btn = QPushButton("⬅ Back to Dashboard")
        back_btn.clicked.connect(back_callback)
        header.addWidget(back_btn)
        
        title = QLabel("🎨 VFX, Branding & GIF Maker")
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

        self.setup_burner_tab()
        self.setup_remover_tab()
        self.setup_gif_tab()

    # =========================================================================
    # TAB 1: WATERMARK BURNER
    # =========================================================================
    def setup_burner_tab(self):
        tab = QWidget()
        t_layout = QVBoxLayout(tab)
        t_layout.setContentsMargins(20, 20, 20, 20)

        t_layout.addWidget(QLabel("Step 1: Select Video File"))
        self.burn_vid_drop = DropZone(self)
        t_layout.addWidget(self.burn_vid_drop)
        t_layout.addSpacing(15)

        t_layout.addWidget(QLabel("Step 2: Select Logo Image (PNG / JPG)"))
        self.burn_img_drop = DropZone(self)
        t_layout.addWidget(self.burn_img_drop)
        t_layout.addSpacing(15)

        t_layout.addWidget(QLabel("Step 3: Choose Logo Position Corner:"))
        self.pos_combo = QComboBox()
        self.pos_combo.addItems(["Bottom-Right (Recommended)", "Bottom-Left", "Top-Right", "Top-Left", "Center"])
        self.pos_combo.setMinimumHeight(40)
        t_layout.addWidget(self.pos_combo)
        t_layout.addSpacing(25)

        self.burn_btn = QPushButton("🚀 Burn Logo Overlay (Re-encode)")
        self.burn_btn.setMinimumHeight(60)
        self.burn_btn.setStyleSheet("background-color: #2D72D9; color: white; font-size: 16px; font-weight: bold; border-radius: 8px;")
        self.burn_btn.clicked.connect(self.run_burner)
        t_layout.addWidget(self.burn_btn)
        t_layout.addStretch()

        self.tabs.addTab(tab, "💧 Watermark Burner")

    def run_burner(self):
        vid = self.burn_vid_drop.file_input.text().strip()
        img = self.burn_img_drop.file_input.text().strip()
        pos_idx = self.pos_combo.currentIndex()
        pos_keys = ["br", "bl", "tr", "tl", "center"]
        pos = pos_keys[pos_idx]

        if not vid or not img:
            return

        base_dir = os.path.dirname(vid)
        name, ext = os.path.splitext(os.path.basename(vid))
        output_path = os.path.join(base_dir, f"{name}_branded{ext}")

        def task():
            return self.watermarker.add_image_watermark(vid, img, output_path, position=pos)

        self.orchestrator.add_background_job(f"Burn Watermark: {name}", task)
        self.orchestrator.show_status_message(f"⏳ Branding task queued for: {name}")

    # =========================================================================
    # TAB 2: WATERMARK REMOVER (Delogo)
    # =========================================================================
    def setup_remover_tab(self):
        tab = QWidget()
        t_layout = QVBoxLayout(tab)
        t_layout.setContentsMargins(20, 20, 20, 20)

        t_layout.addWidget(QLabel("Step 1: Select Target Video File containing Watermark"))
        self.rem_drop = DropZone(self)
        t_layout.addWidget(self.rem_drop)
        t_layout.addSpacing(20)

        info_box = QFrame()
        info_box.setStyleSheet("background-color: #1a1a1a; border: 1px solid #333; border-radius: 8px; padding: 15px;")
        ib_layout = QVBoxLayout(info_box)
        ib_layout.addWidget(QLabel("<b>Interactive Bounding Box workflow:</b>"))
        ib_layout.addWidget(QLabel("1. Click the button below to launch the video frame viewer."))
        ib_layout.addWidget(QLabel("2. Drag a rectangular selection box over the watermark logo using your mouse."))
        ib_layout.addWidget(QLabel("3. Press <b>ENTER</b> or <b>SPACE</b> to confirm, or <b>C</b> to cancel."))
        ib_layout.addWidget(QLabel("4. The engine will run a background in-painting delogo blur filter losslessly."))
        t_layout.addWidget(info_box)
        t_layout.addSpacing(25)

        self.rem_btn = QPushButton("🧹 Select Watermark & Erase")
        self.rem_btn.setMinimumHeight(60)
        self.rem_btn.setStyleSheet("background-color: #ff3333; color: white; font-size: 16px; font-weight: bold; border-radius: 8px;")
        self.rem_btn.clicked.connect(self.run_remover)
        t_layout.addWidget(self.rem_btn)
        t_layout.addStretch()

        self.tabs.addTab(tab, "🧹 Watermark Remover")

    def run_remover(self):
        path = self.rem_drop.file_input.text().strip()
        if not path or not os.path.exists(path):
            return

        # Step 1: Open ROI selector window on main thread (OpenCV GUI must run on main thread)
        coords = get_watermark_coords(path)
        if not coords:
            return

        x, y, w, h = coords
        filename = os.path.basename(path)
        base_dir = os.path.dirname(path)
        name, ext = os.path.splitext(filename)
        output_path = os.path.join(base_dir, f"{name}_clean_logo{ext}")

        # Step 2: Build delogo command and run in background thread
        cmd = [
            'ffmpeg', '-y',
            '-i', path,
            '-vf', f"delogo=x={x}:y={y}:w={w}:h={h}",
            '-c:a', 'copy',
            '-ignore_unknown',
            output_path
        ]

        self.orchestrator.add_background_job(f"Delogo: {name}", cmd)
        self.orchestrator.show_status_message(f"⏳ Delogo task queued for: {filename}")

    # =========================================================================
    # TAB 3: GIF GENERATOR
    # =========================================================================
    def setup_gif_tab(self):
        tab = QWidget()
        t_layout = QVBoxLayout(tab)
        t_layout.setContentsMargins(20, 20, 20, 20)

        t_layout.addWidget(QLabel("Step 1: Select Input Video File"))
        self.gif_drop = DropZone(self)
        t_layout.addWidget(self.gif_drop)
        t_layout.addSpacing(15)

        # Settings
        grid = QGridLayout()
        grid.addWidget(QLabel("Start Timestamp (HH:MM:SS):"), 0, 0)
        self.gif_start = QLineEdit("00:00:00")
        self.gif_start.setStyleSheet("background-color: #222; border: 1px solid #333; color: white; padding: 5px; border-radius: 4px;")
        grid.addWidget(self.gif_start, 0, 1)

        grid.addWidget(QLabel("Duration (seconds):"), 1, 0)
        self.gif_dur = QLineEdit("5")
        self.gif_dur.setStyleSheet("background-color: #222; border: 1px solid #333; color: white; padding: 5px; border-radius: 4px;")
        grid.addWidget(self.gif_dur, 1, 1)

        grid.addWidget(QLabel("Width Scale (px, height auto):"), 2, 0)
        self.gif_scale = QLineEdit("480")
        self.gif_scale.setStyleSheet("background-color: #222; border: 1px solid #333; color: white; padding: 5px; border-radius: 4px;")
        grid.addWidget(self.gif_scale, 2, 1)

        grid.addWidget(QLabel("Speed Preset:"), 3, 0)
        self.gif_preset = QComboBox()
        self.gif_preset.addItems(["fast", "ultrafast", "medium"])
        self.gif_preset.setMinimumHeight(40)
        grid.addWidget(self.gif_preset, 3, 1)

        t_layout.addLayout(grid)
        t_layout.addSpacing(25)

        self.gif_btn = QPushButton("🎨 Generate High-Quality GIF (Lanczos)")
        self.gif_btn.setMinimumHeight(60)
        self.gif_btn.setStyleSheet("background-color: #00ff66; color: #111; font-size: 16px; font-weight: bold; border-radius: 8px;")
        self.gif_btn.clicked.connect(self.run_gif)
        t_layout.addWidget(self.gif_btn)
        t_layout.addStretch()

        self.tabs.addTab(tab, "🎨 GIF Maker")

    def run_gif(self):
        path = self.gif_drop.file_input.text().strip()
        start = self.gif_start.text().strip()
        dur = self.gif_dur.text().strip()
        scale = self.gif_scale.text().strip()
        preset = self.gif_preset.currentText()

        if not path:
            return

        base_dir = os.path.dirname(path)
        name, _ = os.path.splitext(os.path.basename(path))
        output_path = os.path.join(base_dir, f"{name}_clip.gif")

        def task():
            return self.gif_maker.create_gif(path, output_path, start_time=start, duration=dur, scale=scale, preset=preset)

        self.orchestrator.add_background_job(f"GIF Gen: {name}", task)
        self.orchestrator.show_status_message(f"⏳ GIF creation queued for: {name}")
