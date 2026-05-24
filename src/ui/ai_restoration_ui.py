import os
import json
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
                             QLabel, QFrame, QComboBox, QTabWidget)
from PyQt6.QtCore import Qt
from src.ui.custom_widgets import DropZone
from src.processors.remaster import VideoRemaster
from src.processors.remaster_service import RemasterService
from src.processors.motion import MotionFluidizer
from src.processors.intel import MediaIntel

class AIRestorationUI(QWidget):
    """
    Workspace for AI Restoration & Intelligence tools.
    Tab 1: AI Remastering (Real-ESRGAN upscaling & denoising).
    Tab 2: Motion Fluidizer (RIFE AI framerate interpolation).
    Tab 3: Media Intelligence (Automatic chapter markers & scene detection).
    """
    def __init__(self, back_callback, orchestrator):
        super().__init__()
        self.orchestrator = orchestrator
        
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        layout.setContentsMargins(30, 30, 30, 30)

        # --- HEADER ---
        header = QHBoxLayout()
        back_btn = QPushButton("⬅ Back to Dashboard")
        back_btn.clicked.connect(back_callback)
        header.addWidget(back_btn)
        
        title = QLabel("💎 AI Restoration & Intelligence")
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

        self.setup_remaster_tab()
        self.setup_motion_tab()
        self.setup_intel_tab()

    def get_bin_path(self, key, default):
        """Helper to get path settings dynamically from onyx_settings.json."""
        if os.path.exists("onyx_settings.json"):
            try:
                with open("onyx_settings.json", "r") as f:
                    settings = json.load(f)
                    return settings.get(key, default)
            except Exception:
                pass
        return default

    # =========================================================================
    # TAB 1: AI REMASTER (Real-ESRGAN)
    # =========================================================================
    def setup_remaster_tab(self):
        tab = QWidget()
        t_layout = QVBoxLayout(tab)
        t_layout.setContentsMargins(20, 20, 20, 20)

        t_layout.addWidget(QLabel("Step 1: Drop Blurry/Low-Resolution Video"))
        self.remaster_drop = DropZone(self)
        t_layout.addWidget(self.remaster_drop)
        t_layout.addSpacing(15)

        opts = QHBoxLayout()
        v1 = QVBoxLayout()
        v1.addWidget(QLabel("Upscale Scale Factor:"))
        self.scale_combo = QComboBox()
        self.scale_combo.addItems(["2", "4"])
        self.scale_combo.setMinimumHeight(40)
        v1.addWidget(self.scale_combo)
        opts.addLayout(v1)

        v2 = QVBoxLayout()
        v2.addWidget(QLabel("Remaster Execution Mode:"))
        self.remaster_mode_combo = QComboBox()
        self.remaster_mode_combo.addItems(["2-Minute Sample Check (Recommended)", "Full Movie Restoration (12-18 Hours)"])
        self.remaster_mode_combo.setMinimumHeight(40)
        v2.addWidget(self.remaster_mode_combo)
        opts.addLayout(v2)
        
        t_layout.addLayout(opts)
        t_layout.addSpacing(25)

        self.remaster_btn = QPushButton("✨ Start AI Restoration Pipeline")
        self.remaster_btn.setMinimumHeight(60)
        self.remaster_btn.setStyleSheet("background-color: #2D72D9; color: white; font-size: 16px; font-weight: bold; border-radius: 8px;")
        self.remaster_btn.clicked.connect(self.run_remaster)
        t_layout.addWidget(self.remaster_btn)
        t_layout.addStretch()

        self.tabs.addTab(tab, "✨ AI Remaster")

    def run_remaster(self):
        path = self.remaster_drop.file_input.text().strip()
        scale = int(self.scale_combo.currentText())
        mode = self.remaster_mode_combo.currentIndex() # 0 = Sample, 1 = Full

        if not path:
            return

        bin_path = self.get_bin_path("realesrgan", "bin/realesrgan-ncnn-vulkan.exe")
        filename = os.path.basename(path)

        def task():
            # If standard 2x/4x or theatrical
            if mode == 0:
                service = RemasterService(ai_engine_path=bin_path)
                sample_out = service.generate_sample(path)
                return True, f"Quality check complete. Sample saved to: {sample_out}"
            else:
                service = RemasterService(ai_engine_path=bin_path)
                full_out = service.start_full_remaster(path)
                return True, f"Full movie remaster complete. Output saved to: {full_out}"

        self.orchestrator.add_background_job(f"AI Remaster: {filename}", task)
        self.orchestrator.show_status_message(f"⏳ Remaster task queued for: {filename}")

    # =========================================================================
    # TAB 2: MOTION FLUIDIZER (RIFE)
    # =========================================================================
    def setup_motion_tab(self):
        tab = QWidget()
        t_layout = QVBoxLayout(tab)
        t_layout.setContentsMargins(20, 20, 20, 20)

        t_layout.addWidget(QLabel("Step 1: Drop Widescreen/Cinematic Video"))
        self.motion_drop = DropZone(self)
        t_layout.addWidget(self.motion_drop)
        t_layout.addSpacing(15)

        t_layout.addWidget(QLabel("Step 2: Choose Framerate Multiplier (2x turns 30fps to 60fps)"))
        self.mult_combo = QComboBox()
        self.mult_combo.addItems(["2", "4", "8"])
        self.mult_combo.setMinimumHeight(40)
        t_layout.addWidget(self.mult_combo)
        t_layout.addSpacing(25)

        self.motion_btn = QPushButton("⚡ Synthesize Motion (RIFE AI)")
        self.motion_btn.setMinimumHeight(60)
        self.motion_btn.setStyleSheet("background-color: #2D72D9; color: white; font-size: 16px; font-weight: bold; border-radius: 8px;")
        self.motion_btn.clicked.connect(self.run_motion)
        t_layout.addWidget(self.motion_btn)
        t_layout.addStretch()

        self.tabs.addTab(tab, "⚡ Motion Fluidizer")

    def run_motion(self):
        path = self.motion_drop.file_input.text().strip()
        mult = int(self.mult_combo.currentText())

        if not path:
            return

        bin_path = self.get_bin_path("rife", "bin/rife-ncnn-vulkan.exe")
        filename = os.path.basename(path)
        base, ext = os.path.splitext(filename)
        output_name = os.path.join(os.path.dirname(path), f"{base}_{mult}x_FPS{ext}")

        def task():
            engine = MotionFluidizer(bin_folder=bin_path)
            return engine.smooth_motion(path, output_name, multiplier=mult)

        self.orchestrator.add_background_job(f"RIFE Motion: {base}", task)
        self.orchestrator.show_status_message(f"⏳ Motion interpolation queued for: {filename}")

    # =========================================================================
    # TAB 3: MEDIA INTELLIGENCE (Scene Detect)
    # =========================================================================
    def setup_intel_tab(self):
        tab = QWidget()
        t_layout = QVBoxLayout(tab)
        t_layout.setContentsMargins(20, 20, 20, 20)

        t_layout.addWidget(QLabel("Step 1: Drop Video File for Scene Transition Analysis"))
        self.intel_drop = DropZone(self)
        t_layout.addWidget(self.intel_drop)
        t_layout.addSpacing(25)

        self.intel_btn = QPushButton("🧠 Run Scene Cut Detection & Auto-Chaptering")
        self.intel_btn.setMinimumHeight(60)
        self.intel_btn.setStyleSheet("background-color: #00ff66; color: #111; font-size: 16px; font-weight: bold; border-radius: 8px;")
        self.intel_btn.clicked.connect(self.run_intel)
        t_layout.addWidget(self.intel_btn)
        t_layout.addStretch()

        self.tabs.addTab(tab, "🧠 Media Intel")

    def run_intel(self):
        path = self.intel_drop.file_input.text().strip()
        if not path:
            return

        filename = os.path.basename(path)
        def task():
            engine = MediaIntel()
            return engine.analyze_and_chapter(path)

        self.orchestrator.add_background_job(f"Media Intel: {filename}", task)
        self.orchestrator.show_status_message(f"⏳ Chaptering analysis queued for: {filename}")
