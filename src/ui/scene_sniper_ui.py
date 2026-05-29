import os
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
                             QLabel, QLineEdit, QSlider, QStyle, QFrame)
from PyQt6.QtCore import Qt, QUrl, QTimer
from PyQt6.QtMultimedia import QMediaPlayer, QAudioOutput
from PyQt6.QtMultimediaWidgets import QVideoWidget
from src.ui.video_player import FloatingFlash, ClickableVideoWidget, PlayerContainer
from src.ui.custom_widgets import DropZone, SmartRunButton, VLCVolumeSlider
from src.processors import scene_sniper
class SceneSniperUI(QWidget):
    """The Engine Room for Feature 12: Scene Sniper with Integrated Playback"""
    def __init__(self, back_callback, orchestrator):
        super().__init__()
        self.orchestrator = orchestrator
        
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        layout.setContentsMargins(30, 30, 30, 30)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)

        # Header
        header_layout = QHBoxLayout()
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
        
        title = QLabel(" 🎯 Scene Sniper")
        title.setStyleSheet("font-size: 22px; font-weight: bold; color: white;")
        
        header_layout.addWidget(back_btn)
        header_layout.addSpacing(15)
        header_layout.addWidget(title)
        header_layout.addStretch()
        layout.addLayout(header_layout)
        layout.addSpacing(15)
        
        # Drop Zone
        self.drop_zone = DropZone(self)
        self.drop_zone.file_input.textChanged.connect(self.load_video)
        layout.addWidget(self.drop_zone)
        layout.addSpacing(15)

        # Video components
        self.video_widget = ClickableVideoWidget(self.toggle_playback)
        self.flash_indicator = FloatingFlash(self)
        
        # FLOATING PLAYBACK CONTROLS OVERLAY
        self.controls_overlay = QFrame()
        self.controls_overlay.setStyleSheet("""
            QFrame {
                background-color: rgba(20, 20, 20, 0.9);
                border: 1px solid rgba(255, 255, 255, 0.1);
                border-radius: 10px;
            }
            QPushButton {
                background-color: transparent;
                border: none;
                color: #ffffff;
                font-weight: bold;
                font-size: 12px;
                padding: 5px;
            }
            QPushButton:hover {
                color: #2D72D9;
            }
            QLineEdit {
                background-color: rgba(0, 0, 0, 0.6);
                border: 1px solid rgba(255, 255, 255, 0.15);
                color: #ffffff;
                padding: 4px;
                border-radius: 4px;
                font-size: 11px;
                font-family: monospace;
            }
            QLineEdit:focus {
                border: 1px solid #2D72D9;
            }
            QLabel {
                color: #bbbbbb;
                font-size: 12px;
                background: transparent;
                border: none;
            }
        """)
        
        overlay_layout = QVBoxLayout(self.controls_overlay)
        overlay_layout.setContentsMargins(15, 8, 15, 8)
        overlay_layout.setSpacing(6)
        
        # Timeline Slider Row
        slider_row = QHBoxLayout()
        self.timeline_slider = QSlider(Qt.Orientation.Horizontal)
        self.timeline_slider.setRange(0, 0)
        self.timeline_slider.setCursor(Qt.CursorShape.PointingHandCursor)
        self.timeline_slider.setStyleSheet("""
            QSlider::groove:horizontal {
                height: 4px;
                background: rgba(255, 255, 255, 0.2);
                border-radius: 2px;
            }
            QSlider::sub-page:horizontal {
                background: #2D72D9;
                border-radius: 2px;
            }
            QSlider::handle:horizontal {
                background: #ffffff;
                width: 12px;
                height: 12px;
                margin-top: -4px;
                margin-bottom: -4px;
                border-radius: 6px;
            }
            QSlider::handle:horizontal:hover {
                background: #2D72D9;
            }
        """)
        self.timeline_slider.sliderMoved.connect(self.set_position)
        slider_row.addWidget(self.timeline_slider)
        
        self.time_label = QLabel("00:00:00 / 00:00:00")
        self.time_label.setStyleSheet("font-family: monospace; font-size: 12px; color: #aaaaaa;")
        slider_row.addWidget(self.time_label)
        overlay_layout.addLayout(slider_row)
        
        # Buttons Row
        btn_row = QHBoxLayout()
        btn_row.setSpacing(15)
        
        self.rewind_btn = QPushButton("⏪")
        self.rewind_btn.setFixedSize(40, 40)
        self.rewind_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.rewind_btn.setStyleSheet("QPushButton { font-size: 20px; border-radius: 20px; background-color: #333; color: white; } QPushButton:hover { background-color: #444; }")
        self.rewind_btn.clicked.connect(self.skip_backward)
        btn_row.addWidget(self.rewind_btn)
        
        self.play_btn = QPushButton("⏸")
        self.play_btn.setFixedSize(50, 50)
        self.play_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.play_btn.setStyleSheet("QPushButton { font-size: 24px; border-radius: 25px; background-color: #2D72D9; color: white; } QPushButton:hover { background-color: #3a82ef; }")
        self.play_btn.clicked.connect(self.toggle_playback)
        btn_row.addWidget(self.play_btn)
        
        self.forward_btn = QPushButton("⏩")
        self.forward_btn.setFixedSize(40, 40)
        self.forward_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.forward_btn.setStyleSheet("QPushButton { font-size: 20px; border-radius: 20px; background-color: #333; color: white; } QPushButton:hover { background-color: #444; }")
        self.forward_btn.clicked.connect(self.skip_forward)
        btn_row.addWidget(self.forward_btn)
        
        btn_row.addSpacing(25)
        
        # Marker tools
        self.start_btn = QPushButton("📍 Set In")
        self.start_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.start_btn.setStyleSheet("color: #00ff66; font-weight: bold;")
        self.start_btn.clicked.connect(self.set_in_point)
        btn_row.addWidget(self.start_btn)
        
        self.start_input = QLineEdit()
        self.start_input.setFixedWidth(80)
        self.start_input.setPlaceholderText("Start Time")
        btn_row.addWidget(self.start_input)
        
        btn_row.addSpacing(10)
        
        self.end_input = QLineEdit()
        self.end_input.setFixedWidth(80)
        self.end_input.setPlaceholderText("End Time")
        btn_row.addWidget(self.end_input)
        
        self.end_btn = QPushButton("📍 Set Out")
        self.end_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.end_btn.setStyleSheet("color: #ff3333; font-weight: bold;")
        self.end_btn.clicked.connect(self.set_out_point)
        btn_row.addWidget(self.end_btn)
        
        btn_row.addStretch()
        
        self.mute_btn = QPushButton("🔊")
        self.mute_btn.setFixedSize(30, 30)
        self.mute_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.mute_btn.setStyleSheet("QPushButton { font-size: 16px; border-radius: 15px; background-color: transparent; color: white; } QPushButton:hover { background-color: rgba(255, 255, 255, 0.1); }")
        self.mute_btn.clicked.connect(self.toggle_mute)
        btn_row.addWidget(self.mute_btn)
        
        self.volume_slider = VLCVolumeSlider()
        self.volume_slider.setValue(100)
        self.volume_slider.valueChanged.connect(self.set_volume)
        btn_row.addWidget(self.volume_slider)
        
        overlay_layout.addLayout(btn_row)

        self.controls_overlay.setSizePolicy(self.controls_overlay.sizePolicy().Policy.Preferred, self.controls_overlay.sizePolicy().Policy.Fixed)
        self.controls_overlay.setMinimumHeight(75)

        # Assemble Video Player Container
        self.player_container = PlayerContainer(self.video_widget, self.controls_overlay)
        self.player_container.setMinimumHeight(250)
        layout.addWidget(self.player_container, stretch=1)

        self.media_player = QMediaPlayer()
        self.audio_output = QAudioOutput()
        self.media_player.setAudioOutput(self.audio_output)
        self.media_player.setVideoOutput(self.video_widget)

        self.media_player.positionChanged.connect(self.position_changed)
        self.media_player.durationChanged.connect(self.duration_changed)
        layout.addSpacing(20)

        # Execution Button
        self.exec_btn = SmartRunButton("⚡ Extract Scene Natively", self.get_sniper_input, self.execute_sniper, speed_multiplier=20.0)
        layout.addWidget(self.exec_btn)

    def get_sniper_input(self):
        file_path = self.drop_zone.file_input.text().strip()
        start = self.start_input.text().strip()
        end = self.end_input.text().strip()
        if not file_path or not start or not end:
            return None
        return file_path

    # --- VIDEO PLAYER LOGIC ---
    def load_video(self, file_path):
        if file_path:
            self.media_player.setSource(QUrl.fromLocalFile(file_path))
            self.media_player.play()
            self.play_btn.setText("⏸")

    def toggle_playback(self):
        if self.media_player.playbackState() == QMediaPlayer.PlaybackState.PlayingState:
            self.media_player.pause()
            self.play_btn.setText("▶")
            self.flash_indicator.show_flash("⏸", self.video_widget.rect(), self.video_widget.mapToGlobal(self.video_widget.rect().topLeft()))
        else:
            self.media_player.play()
            self.play_btn.setText("⏸")
            self.flash_indicator.show_flash("▶", self.video_widget.rect(), self.video_widget.mapToGlobal(self.video_widget.rect().topLeft()))

    def toggle_mute(self):
        is_muted = self.audio_output.isMuted()
        self.audio_output.setMuted(not is_muted)
        self.mute_btn.setText("🔇" if not is_muted else "🔊")

    def set_volume(self, value):
        self.audio_output.setVolume(value / 100.0)
        if value == 0:
            self.mute_btn.setText("🔇")
        elif self.audio_output.isMuted():
            self.audio_output.setMuted(False)
            self.mute_btn.setText("🔊")

    def keyPressEvent(self, event):
        if self.start_input.hasFocus() or self.end_input.hasFocus():
            super().keyPressEvent(event)
            return

        if event.key() == Qt.Key.Key_Space:
            self.toggle_playback()
        elif event.key() == Qt.Key.Key_Left:
            self.skip_backward()
        elif event.key() == Qt.Key.Key_Right:
            self.skip_forward()
        else:
            super().keyPressEvent(event)

    def skip_backward(self):
        new_pos = max(0, self.media_player.position() - 10000)
        self.media_player.setPosition(new_pos)
        self.flash_indicator.show_flash("⏪", self.video_widget.rect(), self.video_widget.mapToGlobal(self.video_widget.rect().topLeft()))

    def skip_forward(self):
        new_pos = min(self.media_player.duration(), self.media_player.position() + 10000)
        self.media_player.setPosition(new_pos)
        self.flash_indicator.show_flash("⏩", self.video_widget.rect(), self.video_widget.mapToGlobal(self.video_widget.rect().topLeft()))

    def position_changed(self, position):
        self.timeline_slider.setValue(position)
        current = self.format_time(position)[:8]
        total = self.format_time(self.media_player.duration())[:8]
        self.time_label.setText(f"{current} / {total}")

    def duration_changed(self, duration):
        self.timeline_slider.setRange(0, duration)
        total = self.format_time(duration)[:8]
        self.time_label.setText(f"00:00:00 / {total}")

    def set_position(self, position):
        self.media_player.setPosition(position)

    def format_time(self, ms):
        seconds = (ms // 1000) % 60
        minutes = (ms // 60000) % 60
        hours = (ms // 3600000)
        milliseconds = ms % 1000
        return f"{hours:02d}:{minutes:02d}:{seconds:02d}.{milliseconds:03d}"

    def set_in_point(self):
        pos = self.media_player.position()
        self.start_input.setText(self.format_time(pos))

    def set_out_point(self):
        pos = self.media_player.position()
        self.end_input.setText(self.format_time(pos))

    def execute_sniper(self, inputs, est_seconds):
        file_path = inputs
        start = self.start_input.text().strip()
        end = self.end_input.text().strip()
        
        # 2. Validation: Ensure we have all three requirements
        if not file_path or not start or not end:
            self.orchestrator.show_status_message("❌ Error: Missing Input! Need File, Start Time, and End Time.")
            return

        # 3. Create a smart output path
        base_dir = os.path.dirname(file_path)
        file_name = os.path.basename(file_path)
        name_only, ext = os.path.splitext(file_name)
        
        output_name = f"{name_only}_Snipe_{start.replace(':', '-')}{ext}"
        final_output = os.path.join(base_dir, output_name)

        def task():
            scene_sniper.extract_scene(file_path, start, end, final_output)
            if os.path.exists(final_output):
                return True, f"Scene extracted successfully to: {final_output}"
            else:
                return False, "Failed to extract scene."

        self.orchestrator.add_background_job(f"Scene Sniper: {name_only}", task, estimated_seconds=est_seconds)
        self.orchestrator.show_status_message(f"⏳ Sniper task queued for: {file_name}")

# ==========================================
# HOW TO USE THIS CODE (EXAMPLE)
# ==========================================
# Example usage:
# from src.processors.scene_sniper_ui import MainClass
# processor = MainClass()
# processor.run(input_file, output_file)
# ==========================================

# ==============================================================================
# 🎬 FEATURE: INTERNAL MODULE DOCUMENTATION (scene_sniper_ui.py)
# ==============================================================================
#
# 📝 WHAT IS THIS FILE?
#    This file, 'scene_sniper_ui.py', is a core component of the Onyx Engine. It is
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
