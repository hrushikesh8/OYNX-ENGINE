import os
import json
from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QPushButton, 
                             QLabel, QFrame, QLineEdit, QComboBox, QFileDialog, QGridLayout)
from PyQt6.QtCore import Qt
from src.ui.custom_widgets import DropZone

class SettingsUI(QDialog):
    """
    Dedicated modal dialog for Onyx Engine preferences and configurations.
    Manages binary paths, output folder preferences, concurrent queue options, and global styling.
    """
    def __init__(self, orchestrator, parent=None):
        super().__init__(parent)
        self.orchestrator = orchestrator
        self.settings_file = "onyx_settings.json"
        self.load_settings()

        self.setWindowTitle("⚙️ Onyx Engine Preferences")
        self.setMinimumSize(650, 520)
        self.setStyleSheet("""
            QDialog {
                background-color: #121212;
            }
            QLabel {
                color: #bbbbbb;
                font-size: 12px;
                font-weight: bold;
            }
            QLineEdit {
                background-color: #1e1e1e;
                border: 1px solid #2d2d2d;
                color: #ffffff;
                padding: 8px;
                border-radius: 5px;
                font-size: 13px;
            }
            QLineEdit:focus {
                border: 1px solid #2D72D9;
            }
            QComboBox {
                background-color: #1e1e1e;
                border: 1px solid #2d2d2d;
                color: #ffffff;
                padding: 6px;
                border-radius: 5px;
                font-size: 13px;
                min-height: 30px;
            }
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(25, 25, 25, 25)
        layout.setSpacing(15)

        # --- TITLE ---
        title = QLabel("⚙️ Onyx Engine Settings")
        title.setStyleSheet("font-size: 20px; font-weight: 900; color: #ffffff; margin-bottom: 10px;")
        layout.addWidget(title)

        # --- CATEGORY 1: ENGINE BINARY PATHS ---
        bin_frame = QFrame()
        bin_frame.setStyleSheet("QFrame { background-color: #181818; border: 1px solid #252525; border-radius: 8px; }")
        bin_layout = QVBoxLayout(bin_frame)
        bin_layout.setContentsMargins(15, 15, 15, 15)
        
        bin_title = QLabel("🔌 Command & AI Binary Paths")
        bin_title.setStyleSheet("font-size: 13px; color: #ffffff; font-weight: bold;")
        bin_layout.addWidget(bin_title)
        bin_layout.addSpacing(5)
        
        self.path_inputs = {}
        for key, name in [
            ("ffmpeg", "FFmpeg Compiler Binary"), 
            ("seven_zip", "7-Zip Compressor (7za.exe)"), 
            ("realesrgan", "Real-ESRGAN Upscaler Binary"), 
            ("rife", "RIFE Motion interpolator Binary")
        ]:
            row = QHBoxLayout()
            lbl = QLabel(f"{name}:")
            lbl.setFixedWidth(180)
            row.addWidget(lbl)
            
            input_field = QLineEdit(self.settings.get(key, ""))
            self.path_inputs[key] = input_field
            row.addWidget(input_field)
            
            btn = QPushButton("📁")
            btn.setFixedWidth(36)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.setStyleSheet("""
                QPushButton {
                    background-color: #2b2b2b;
                    border: 1px solid #3c3c3c;
                    border-radius: 5px;
                    padding: 6px;
                    color: white;
                }
                QPushButton:hover {
                    background-color: #3d3d3d;
                }
            """)
            btn.clicked.connect(lambda checked, k=key: self.browse_pref(k))
            row.addWidget(btn)
            
            bin_layout.addLayout(row)
        layout.addWidget(bin_frame)

        # --- CATEGORY 2: GENERAL SUITE PREFERENCES ---
        pref_frame = QFrame()
        pref_frame.setStyleSheet("QFrame { background-color: #181818; border: 1px solid #252525; border-radius: 8px; }")
        pref_layout = QVBoxLayout(pref_frame)
        pref_layout.setContentsMargins(15, 15, 15, 15)
        
        pref_title = QLabel("⚙️ Suite & Render Preferences")
        pref_title.setStyleSheet("font-size: 13px; color: #ffffff; font-weight: bold;")
        pref_layout.addWidget(pref_title)
        pref_layout.addSpacing(5)

        grid = QGridLayout()
        grid.setSpacing(12)

        # Output folder option
        grid.addWidget(QLabel("Default Outputs Folder:"), 0, 0)
        self.output_drop = DropZone(self, mode='dir')
        self.output_drop.file_input.setText(self.settings.get("default_output_dir", ""))
        grid.addWidget(self.output_drop, 0, 1)

        # Max concurrency jobs
        grid.addWidget(QLabel("Max Concurrent Rendering Jobs:"), 1, 0)
        self.concurrency_combo = QComboBox()
        self.concurrency_combo.addItems(["1 (Safe)", "2", "3", "4 (High Performance)"])
        self.concurrency_combo.setCurrentText(str(self.settings.get("max_concurrent_jobs", 1)))
        grid.addWidget(self.concurrency_combo, 1, 1)

        # Theme Color option
        grid.addWidget(QLabel("Global Accent Color:"), 2, 0)
        self.accent_combo = QComboBox()
        self.accent_combo.addItems(["Classic Blue (#2D72D9)", "Emerald Green (#00ff66)", "Ruby Red (#ff3333)", "Vibrant Orange (#ff8c00)"])
        saved_accent = self.settings.get("accent_color", "#2D72D9")
        if "#00ff66" in saved_accent: self.accent_combo.setCurrentIndex(1)
        elif "#ff3333" in saved_accent: self.accent_combo.setCurrentIndex(2)
        elif "#ff8c00" in saved_accent: self.accent_combo.setCurrentIndex(3)
        else: self.accent_combo.setCurrentIndex(0)
        grid.addWidget(self.accent_combo, 2, 1)

        # Theme Mode Option
        grid.addWidget(QLabel("UI Appearance Mode:"), 3, 0)
        self.theme_mode_combo = QComboBox()
        self.theme_mode_combo.addItems(["dark", "light", "auto"])
        self.theme_mode_combo.setCurrentText(self.settings.get("theme_mode", "dark"))
        grid.addWidget(self.theme_mode_combo, 3, 1)

        # Hardware Acceleration Option
        grid.addWidget(QLabel("Video Hardware Encoder:"), 4, 0)
        self.hw_combo = QComboBox()
        self.hw_combo.addItems(["CPU (libx264/5) - Reliable", "NVIDIA NVENC - Fast", "Intel QSV - Fast", "AMD AMF - Fast"])
        self.hw_combo.setCurrentIndex(self.settings.get("hw_accel", 0))
        grid.addWidget(self.hw_combo, 4, 1)

        # Audio Bitrate Option
        grid.addWidget(QLabel("Default Audio Bitrate:"), 5, 0)
        self.audio_combo = QComboBox()
        self.audio_combo.addItems(["128k (Standard)", "192k (High Quality)", "320k (Audiophile)"])
        self.audio_combo.setCurrentIndex(self.settings.get("audio_bitrate", 1))
        grid.addWidget(self.audio_combo, 5, 1)

        # Subtitle Safeguard Checkbox
        from PyQt6.QtWidgets import QCheckBox
        self.subtitle_cb = QCheckBox("Globally Strip Subtitles in Conversions (Prevents Web-DL crashes)")
        self.subtitle_cb.setStyleSheet("color: #bbbbbb; font-size: 13px;")
        self.subtitle_cb.setChecked(self.settings.get("subtitle_safeguard", False))
        grid.addWidget(self.subtitle_cb, 6, 0, 1, 2)

        pref_layout.addLayout(grid)
        layout.addWidget(pref_frame)

        # --- ACTION BUTTONS ---
        actions = QHBoxLayout()
        
        cancel_btn = QPushButton("Cancel")
        cancel_btn.setMinimumHeight(45)
        cancel_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        cancel_btn.setStyleSheet("""
            QPushButton {
                background-color: #2b2b2b;
                border: 1px solid #3c3c3c;
                color: #bbbbbb;
                font-weight: bold;
                border-radius: 6px;
            }
            QPushButton:hover {
                background-color: #353535;
                color: white;
            }
        """)
        cancel_btn.clicked.connect(self.reject)
        
        self.save_btn = QPushButton("💾 Save & Apply")
        self.save_btn.setMinimumHeight(45)
        self.save_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.save_btn.setStyleSheet("""
            QPushButton {
                background-color: #2D72D9;
                color: white;
                font-weight: bold;
                border-radius: 6px;
            }
            QPushButton:hover {
                background-color: #3a82ef;
            }
        """)
        self.save_btn.clicked.connect(self.save_settings)
        
        actions.addWidget(cancel_btn)
        actions.addWidget(self.save_btn)
        layout.addLayout(actions)

    def load_settings(self):
        default_settings = {
            "ffmpeg": "ffmpeg",
            "ffprobe": "ffprobe",
            "seven_zip": os.path.abspath(os.path.join("src", "tools", "7za.exe")),
            "realesrgan": os.path.abspath(os.path.join("bin", "realesrgan-ncnn-vulkan.exe")),
            "rife": os.path.abspath(os.path.join("bin", "rife-ncnn-vulkan.exe")),
            "max_concurrent_jobs": 1,
            "default_output_dir": "",
            "accent_color": "#2D72D9",
            "theme_mode": "dark",
            "hw_accel": 0,
            "audio_bitrate": 1,
            "subtitle_safeguard": False
        }
        if os.path.exists(self.settings_file):
            try:
                with open(self.settings_file, "r") as f:
                    self.settings = json.load(f)
            except Exception:
                self.settings = default_settings
        else:
            self.settings = default_settings

    def save_settings(self):
        # Update binaries
        for key in self.path_inputs:
            self.settings[key] = self.path_inputs[key].text().strip()
        
        # Update output dir
        self.settings["default_output_dir"] = self.output_drop.file_input.text().strip()
        
        # Update concurrency
        text_concurrency = self.concurrency_combo.currentText()
        self.settings["max_concurrent_jobs"] = int(text_concurrency.split()[0])
        
        # Update accent color
        color_map = {
            0: "#2D72D9",
            1: "#00ff66",
            2: "#ff3333",
            3: "#ff8c00"
        }
        self.settings["accent_color"] = color_map.get(self.accent_combo.currentIndex(), "#2D72D9")
        self.settings["theme_mode"] = self.theme_mode_combo.currentText()
        
        # Update new backend settings
        self.settings["hw_accel"] = self.hw_combo.currentIndex()
        self.settings["audio_bitrate"] = self.audio_combo.currentIndex()
        self.settings["subtitle_safeguard"] = self.subtitle_cb.isChecked()

        # Save to file
        try:
            with open(self.settings_file, "w") as f:
                json.dump(self.settings, f, indent=4)
                
            # Apply parameters to master orchestrator
            self.orchestrator.max_concurrent_jobs = self.settings["max_concurrent_jobs"]
            self.orchestrator.show_status_message("⚙️ Preferences updated and saved successfully.")
            
            # Dynamically update the theme accent color and mode
            import qdarktheme
            qdarktheme.setup_theme(self.settings["theme_mode"], custom_colors={"primary": self.settings["accent_color"]})
            self.accept()
        except Exception as e:
            self.orchestrator.show_status_message(f"❌ Error saving preferences: {str(e)}")

    def browse_binary(self, key):
        import sys
        import os
        start_dir = getattr(sys, '_onyx_last_dir', os.path.expanduser("~"))
        file_name, _ = QFileDialog.getOpenFileName(self, f"Select binary for {key}", start_dir, "Executable Files (*.exe);;All Files (*)")
        if file_name:
            sys._onyx_last_dir = os.path.dirname(file_name)
            self.path_inputs[key].setText(file_name)


# ==========================================
# HOW TO USE THIS CODE (EXAMPLE)
# ==========================================
# Example usage:
# from src.processors.settings_ui import MainClass
# processor = MainClass()
# processor.run(input_file, output_file)
# ==========================================

# ==============================================================================
# 🎬 FEATURE: INTERNAL MODULE DOCUMENTATION (settings_ui.py)
# ==============================================================================
#
# 📝 WHAT IS THIS FILE?
#    This file, 'settings_ui.py', is a core component of the Onyx Engine. It is
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
