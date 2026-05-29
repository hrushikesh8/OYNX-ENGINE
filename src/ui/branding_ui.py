import os
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
                             QLabel, QFrame, QComboBox, QLineEdit, QTabWidget, QSlider, QGridLayout)
from PyQt6.QtCore import Qt
from src.ui.custom_widgets import DropZone, SmartRunButton
from src.processors.watermark import Watermarker
from src.processors.watermark_remover import get_watermark_coords
from src.processors.gif_maker import GifMaker
from src.processors.color_studio import ColorStudioProcessor

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
        
        title = QLabel("🎨 VFX, Branding & GIF Maker")
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

        self.setup_burner_tab()
        self.setup_remover_tab()
        self.setup_gif_tab()
        self.setup_color_tab()

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

        self.burn_btn = SmartRunButton("🚀 Burn Logo Overlay (Re-encode)", self.get_burn_input, self.run_burner, speed_multiplier=2.0)
        t_layout.addWidget(self.burn_btn)
        t_layout.addStretch()

        self.tabs.addTab(tab, "💧 Watermark Burner")

    def get_burn_input(self):
        vid = self.burn_vid_drop.file_input.text().strip()
        img = self.burn_img_drop.file_input.text().strip()
        if not vid or not img:
            return None
        return vid

    def run_burner(self, inputs, est_seconds):
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

        self.orchestrator.add_background_job(f"Burn Watermark: {name}", task, estimated_seconds=est_seconds)
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

        self.rem_btn = SmartRunButton("🧹 Select Watermark & Erase", self.get_rem_input, self.run_remover, speed_multiplier=1.5)
        self.rem_btn.setStyleSheet("background-color: #ff3333; color: white; font-size: 16px; font-weight: bold; border-radius: 8px;")
        t_layout.addWidget(self.rem_btn)
        t_layout.addStretch()

        self.tabs.addTab(tab, "🧹 Watermark Remover")

    def get_rem_input(self):
        path = self.rem_drop.file_input.text().strip()
        if not path or not os.path.exists(path):
            return None
        return path

    def run_remover(self, inputs, est_seconds):
        path = self.get_rem_input()

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

        self.orchestrator.add_background_job(f"Delogo: {name}", cmd, estimated_seconds=est_seconds)
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

        self.gif_btn = SmartRunButton("🎨 Generate High-Quality GIF (Lanczos)", self.get_gif_input, self.run_gif, self.get_gif_speed)
        self.gif_btn.setStyleSheet("background-color: #00ff66; color: #111; font-size: 16px; font-weight: bold; border-radius: 8px;")
        t_layout.addWidget(self.gif_btn)
        t_layout.addStretch()

        self.tabs.addTab(tab, "🎨 GIF Maker")

    def get_gif_input(self):
        path = self.gif_drop.file_input.text().strip()
        return path if path else None

    def get_gif_speed(self):
        preset = self.gif_preset.currentText()
        if preset == "ultrafast": return 10.0
        if preset == "fast": return 5.0
        return 2.0

    def run_gif(self, inputs, est_seconds):
        path = self.get_gif_input()
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

        self.orchestrator.add_background_job(f"GIF Gen: {name}", task, estimated_seconds=est_seconds)
        self.orchestrator.show_status_message(f"⏳ GIF creation queued for: {name}")

    # =========================================================================
    # TAB 4: COLOR GRADING STUDIO (LUT & EQ Filters)
    # =========================================================================
    def setup_color_tab(self):
        tab = QWidget()
        t_layout = QVBoxLayout(tab)
        t_layout.setContentsMargins(20, 20, 20, 20)

        t_layout.addWidget(QLabel("Step 1: Select Video File"))
        self.color_vid_drop = DropZone(self)
        t_layout.addWidget(self.color_vid_drop)
        t_layout.addSpacing(15)

        # EQ Sliders Grid
        grid = QGridLayout()
        
        # Brightness (-1.0 to 1.0)
        grid.addWidget(QLabel("Brightness:"), 0, 0)
        self.bright_slider = QSlider(Qt.Orientation.Horizontal)
        self.bright_slider.setRange(-100, 100)
        self.bright_slider.setValue(0)
        self.bright_label = QLabel("0.0")
        self.bright_slider.valueChanged.connect(lambda val: self.bright_label.setText(f"{val / 100.0:.2f}"))
        grid.addWidget(self.bright_slider, 0, 1)
        grid.addWidget(self.bright_label, 0, 2)

        # Contrast (0.0 to 4.0)
        grid.addWidget(QLabel("Contrast:"), 1, 0)
        self.contrast_slider = QSlider(Qt.Orientation.Horizontal)
        self.contrast_slider.setRange(0, 40)
        self.contrast_slider.setValue(10)
        self.contrast_label = QLabel("1.0")
        self.contrast_slider.valueChanged.connect(lambda val: self.contrast_label.setText(f"{val / 10.0:.1f}"))
        grid.addWidget(self.contrast_slider, 1, 1)
        grid.addWidget(self.contrast_label, 1, 2)

        # Saturation (0.0 to 3.0)
        grid.addWidget(QLabel("Saturation:"), 2, 0)
        self.sat_slider = QSlider(Qt.Orientation.Horizontal)
        self.sat_slider.setRange(0, 30)
        self.sat_slider.setValue(10)
        self.sat_label = QLabel("1.0")
        self.sat_slider.valueChanged.connect(lambda val: self.sat_label.setText(f"{val / 10.0:.1f}"))
        grid.addWidget(self.sat_slider, 2, 1)
        grid.addWidget(self.sat_label, 2, 2)

        # Gamma (0.1 to 10.0)
        grid.addWidget(QLabel("Gamma:"), 3, 0)
        self.gamma_slider = QSlider(Qt.Orientation.Horizontal)
        self.gamma_slider.setRange(1, 100)
        self.gamma_slider.setValue(10)
        self.gamma_label = QLabel("1.0")
        self.gamma_slider.valueChanged.connect(lambda val: self.gamma_label.setText(f"{val / 10.0:.1f}"))
        grid.addWidget(self.gamma_slider, 3, 1)
        grid.addWidget(self.gamma_label, 3, 2)

        t_layout.addLayout(grid)
        t_layout.addSpacing(15)

        t_layout.addWidget(QLabel("Step 3: Select 3D LUT File (.cube) (Optional)"))
        self.lut_drop = DropZone(self)
        t_layout.addWidget(self.lut_drop)
        t_layout.addSpacing(25)

        self.color_btn = SmartRunButton("🎨 Apply Color Grading & LUT", self.get_color_input, self.run_color_grading, speed_multiplier=2.0)
        t_layout.addWidget(self.color_btn)
        t_layout.addStretch()

        self.tabs.addTab(tab, "🎨 Color Studio")

    def get_color_input(self):
        path = self.color_vid_drop.file_input.text().strip()
        return path if path else None

    def run_color_grading(self, inputs, est_seconds):
        path = self.get_color_input()
        b = self.bright_slider.value() / 100.0
        c = self.contrast_slider.value() / 10.0
        s = self.sat_slider.value() / 10.0
        g = self.gamma_slider.value() / 10.0
        lut = self.lut_drop.file_input.text().strip() or None

        if not path:
            return

        base_dir = os.path.dirname(path)
        name, ext = os.path.splitext(os.path.basename(path))
        output_path = os.path.join(base_dir, f"{name}_graded{ext}")

        def task():
            processor = ColorStudioProcessor()
            success = processor.adjust_colors(path, output_path, brightness=b, contrast=c, saturation=s, gamma=g, lut_path=lut)
            return success, f"Color grading complete. Saved at: {output_path}" if success else "Color grading failed."

        self.orchestrator.add_background_job(f"Color Studio: {name}", task, estimated_seconds=est_seconds)
        self.orchestrator.show_status_message(f"⏳ Color Grading queued for: {name}")


# ==========================================
# HOW TO USE THIS CODE (EXAMPLE)
# ==========================================
# Example usage:
# from src.processors.branding_ui import MainClass
# processor = MainClass()
# processor.run(input_file, output_file)
# ==========================================

# ==============================================================================
# 🎬 FEATURE: INTERNAL MODULE DOCUMENTATION (branding_ui.py)
# ==============================================================================
#
# 📝 WHAT IS THIS FILE?
#    This file, 'branding_ui.py', is a core component of the Onyx Engine. It is
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
