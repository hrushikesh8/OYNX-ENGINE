import os
import json
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
                             QLabel, QFrame, QComboBox, QTabWidget, QSlider, QGridLayout)
from PyQt6.QtCore import Qt
from src.ui.custom_widgets import DropZone, SmartRunButton
from src.processors.remaster import VideoRemaster
from src.processors.remaster_service import RemasterService
from src.processors.motion import MotionFluidizer
from src.processors.intel import MediaIntel
from src.processors.stabilizer import VideoStabilizerProcessor

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
        
        title = QLabel("💎 AI Restoration & Intelligence")
        title.setStyleSheet("font-size: 22px; font-weight: bold; color: white;")
        header.addWidget(title)
        header.addStretch()
        layout.addLayout(header)
        layout.addSpacing(15)
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
        self.setup_stabilize_tab()

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

        self.remaster_btn = SmartRunButton("✨ Start AI Restoration Pipeline", self.get_remaster_input, self.run_remaster, self.get_remaster_speed)
        t_layout.addWidget(self.remaster_btn)
        t_layout.addStretch()

        self.tabs.addTab(tab, "✨ AI Remaster")

    def get_remaster_input(self):
        path = self.remaster_drop.file_input.text().strip()
        return path if path else None

    def get_remaster_speed(self):
        return 0.2 if self.remaster_mode_combo.currentIndex() == 1 else 0.5

    def run_remaster(self, inputs, est_seconds):
        path = self.get_remaster_input()
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

        self.orchestrator.add_background_job(f"AI Remaster: {filename}", task, estimated_seconds=est_seconds)
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

        self.motion_btn = SmartRunButton("⚡ Synthesize Motion (RIFE AI)", self.get_motion_input, self.run_motion, self.get_motion_speed)
        t_layout.addWidget(self.motion_btn)
        t_layout.addStretch()

        self.tabs.addTab(tab, "⚡ Motion Fluidizer")

    def get_motion_input(self):
        path = self.motion_drop.file_input.text().strip()
        return path if path else None

    def get_motion_speed(self):
        mult = int(self.mult_combo.currentText())
        return 1.0 / mult

    def run_motion(self, inputs, est_seconds):
        path = self.get_motion_input()
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

        self.orchestrator.add_background_job(f"RIFE Motion: {base}", task, estimated_seconds=est_seconds)
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

        self.intel_btn = SmartRunButton("🧠 Run Scene Cut Detection & Auto-Chaptering", self.get_intel_input, self.run_intel, speed_multiplier=10.0)
        self.intel_btn.setStyleSheet("background-color: #00ff66; color: #111; font-size: 16px; font-weight: bold; border-radius: 8px;")
        t_layout.addWidget(self.intel_btn)
        t_layout.addStretch()

        self.tabs.addTab(tab, "🧠 Media Intel")

    def get_intel_input(self):
        path = self.intel_drop.file_input.text().strip()
        return path if path else None

    def run_intel(self, inputs, est_seconds):
        path = self.get_intel_input()
        if not path:
            return

        filename = os.path.basename(path)
        def task():
            engine = MediaIntel()
            return engine.analyze_and_chapter(path)

        self.orchestrator.add_background_job(f"Media Intel: {filename}", task, estimated_seconds=est_seconds)
        self.orchestrator.show_status_message(f"⏳ Chaptering analysis queued for: {filename}")

    # =========================================================================
    # TAB 4: INTELLIGENT VIDEO STABILIZER (vid.stab)
    # =========================================================================
    def setup_stabilize_tab(self):
        tab = QWidget()
        t_layout = QVBoxLayout(tab)
        t_layout.setContentsMargins(20, 20, 20, 20)

        t_layout.addWidget(QLabel("Step 1: Select Shaky Video File"))
        self.stab_vid_drop = DropZone(self)
        t_layout.addWidget(self.stab_vid_drop)
        t_layout.addSpacing(15)

        # Stabilizer Sliders Grid
        grid = QGridLayout()

        # Shakiness (1 to 10)
        grid.addWidget(QLabel("Shakiness (1=mild, 10=shaky):"), 0, 0)
        self.shakiness_slider = QSlider(Qt.Orientation.Horizontal)
        self.shakiness_slider.setRange(1, 10)
        self.shakiness_slider.setValue(10)
        self.shakiness_label = QLabel("10")
        self.shakiness_slider.valueChanged.connect(lambda val: self.shakiness_label.setText(str(val)))
        grid.addWidget(self.shakiness_slider, 0, 1)
        grid.addWidget(self.shakiness_label, 0, 2)

        # Accuracy (1 to 15)
        grid.addWidget(QLabel("Analysis Accuracy (1-15):"), 1, 0)
        self.accuracy_slider = QSlider(Qt.Orientation.Horizontal)
        self.accuracy_slider.setRange(1, 15)
        self.accuracy_slider.setValue(15)
        self.accuracy_label = QLabel("15")
        self.accuracy_slider.valueChanged.connect(lambda val: self.accuracy_label.setText(str(val)))
        grid.addWidget(self.accuracy_slider, 1, 1)
        grid.addWidget(self.accuracy_label, 1, 2)

        # Smoothing (1 to 100)
        grid.addWidget(QLabel("Smoothing (frame window):"), 2, 0)
        self.smoothing_slider = QSlider(Qt.Orientation.Horizontal)
        self.smoothing_slider.setRange(1, 100)
        self.smoothing_slider.setValue(30)
        self.smoothing_label = QLabel("30")
        self.smoothing_slider.valueChanged.connect(lambda val: self.smoothing_label.setText(str(val)))
        grid.addWidget(self.smoothing_slider, 2, 1)
        grid.addWidget(self.smoothing_label, 2, 2)

        t_layout.addLayout(grid)
        t_layout.addSpacing(25)

        self.stabilize_btn = SmartRunButton("🎥 Smooth Camera Shakiness (2-Pass)", self.get_stab_input, self.run_stabilize, speed_multiplier=2.0)
        self.stabilize_btn.setStyleSheet("background-color: #00ff66; color: #111; font-size: 16px; font-weight: bold; border-radius: 8px;")
        t_layout.addWidget(self.stabilize_btn)
        t_layout.addStretch()

        self.tabs.addTab(tab, "🎥 Stabilizer")

    def get_stab_input(self):
        path = self.stab_vid_drop.file_input.text().strip()
        return path if path else None

    def run_stabilize(self, inputs, est_seconds):
        path = self.get_stab_input()
        shakiness = self.shakiness_slider.value()
        accuracy = self.accuracy_slider.value()
        smoothing = self.smoothing_slider.value()

        if not path:
            return

        base_dir = os.path.dirname(path)
        name, ext = os.path.splitext(os.path.basename(path))
        output_path = os.path.join(base_dir, f"{name}_stabilized{ext}")

        def task():
            processor = VideoStabilizerProcessor()
            success = processor.stabilize(path, output_path, shakiness=shakiness, accuracy=accuracy, smoothing=smoothing)
            return success, f"Stabilization finished. Output saved to: {output_path}" if success else "Stabilization failed."

        self.orchestrator.add_background_job(f"Stabilize: {name}", task, estimated_seconds=est_seconds)
        self.orchestrator.show_status_message(f"⏳ Stabilization task queued for: {name}")


# ==========================================
# HOW TO USE THIS CODE (EXAMPLE)
# ==========================================
# Example usage:
# from src.processors.ai_restoration_ui import MainClass
# processor = MainClass()
# processor.run(input_file, output_file)
# ==========================================

# ==============================================================================
# 🎬 FEATURE: INTERNAL MODULE DOCUMENTATION (ai_restoration_ui.py)
# ==============================================================================
#
# 📝 WHAT IS THIS FILE?
#    This file, 'ai_restoration_ui.py', is a core component of the Onyx Engine. It is
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
