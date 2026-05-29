import os
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
                             QLabel, QFrame, QLineEdit, QTabWidget, QSlider)
from PyQt6.QtCore import Qt, QUrl
from PyQt6.QtMultimedia import QMediaPlayer, QAudioOutput
from src.ui.custom_widgets import DropZone, SmartRunButton, VLCVolumeSlider
from src.ui.video_player import FloatingFlash, ClickableVideoWidget, PlayerContainer
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
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)

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
        
        title = QLabel("🎬 Edit, Divide & Auto-Trim")
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
        self.int_drop.file_input.textChanged.connect(self.load_video)
        t_layout.addWidget(self.int_drop)
        t_layout.addSpacing(15)

        # --- VIDEO PLAYER INTEGRATION ---
        self.video_widget = ClickableVideoWidget(self.toggle_playback)
        self.flash_indicator = FloatingFlash(self)
        
        self.controls_overlay = QFrame()
        self.controls_overlay.setStyleSheet("""
            QFrame { background-color: rgba(20, 20, 20, 0.9); border: 1px solid rgba(255, 255, 255, 0.1); border-radius: 10px; }
            QPushButton { background-color: transparent; border: none; color: #ffffff; font-weight: bold; font-size: 12px; padding: 5px; }
            QPushButton:hover { color: #2D72D9; }
            QLabel { color: #bbbbbb; font-size: 12px; background: transparent; border: none; }
        """)
        overlay_layout = QVBoxLayout(self.controls_overlay)
        overlay_layout.setContentsMargins(15, 8, 15, 8)
        
        slider_row = QHBoxLayout()
        self.timeline_slider = QSlider(Qt.Orientation.Horizontal)
        self.timeline_slider.setRange(0, 0)
        self.timeline_slider.setCursor(Qt.CursorShape.PointingHandCursor)
        self.timeline_slider.setStyleSheet("""
            QSlider::groove:horizontal { height: 4px; background: rgba(255, 255, 255, 0.2); border-radius: 2px; }
            QSlider::sub-page:horizontal { background: #2D72D9; border-radius: 2px; }
            QSlider::handle:horizontal { background: #ffffff; width: 12px; height: 12px; margin-top: -4px; margin-bottom: -4px; border-radius: 6px; }
        """)
        self.timeline_slider.sliderMoved.connect(self.set_position)
        slider_row.addWidget(self.timeline_slider)
        
        self.time_label = QLabel("00:00:00 / 00:00:00")
        self.time_label.setStyleSheet("font-family: monospace; font-size: 12px; color: #aaaaaa;")
        slider_row.addWidget(self.time_label)
        overlay_layout.addLayout(slider_row)
        
        btn_row = QHBoxLayout()
        self.play_btn = QPushButton("⏸")
        self.play_btn.setFixedSize(40, 40)
        self.play_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.play_btn.setStyleSheet("QPushButton { font-size: 20px; border-radius: 20px; background-color: #2D72D9; color: white; } QPushButton:hover { background-color: #3a82ef; }")
        self.play_btn.clicked.connect(self.toggle_playback)
        btn_row.addWidget(self.play_btn)
        
        btn_row.addSpacing(25)
        self.set_int_btn = QPushButton("📍 Mark Intermission")
        self.set_int_btn.setStyleSheet("color: #00ff66; font-size: 14px;")
        self.set_int_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.set_int_btn.clicked.connect(self.set_intermission_point)
        btn_row.addWidget(self.set_int_btn)
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

        self.player_container = PlayerContainer(self.video_widget, self.controls_overlay)
        self.player_container.setMinimumHeight(250)
        t_layout.addWidget(self.player_container, stretch=1)
        
        self.media_player = QMediaPlayer()
        self.audio_output = QAudioOutput()
        self.media_player.setAudioOutput(self.audio_output)
        self.media_player.setVideoOutput(self.video_widget)
        self.media_player.positionChanged.connect(self.position_changed)
        self.media_player.durationChanged.connect(self.duration_changed)

        t_layout.addSpacing(15)

        t_layout.addWidget(QLabel("Step 2: Enter Timestamp to Cut (seconds or HH:MM:SS)"))
        self.int_time = QLineEdit("01:00:00")
        self.int_time.setStyleSheet("background-color: #222; border: 1px solid #333; color: white; padding: 10px; border-radius: 5px;")
        t_layout.addWidget(self.int_time)
        t_layout.addSpacing(25)

        self.int_btn = SmartRunButton("✂️ Split at Intermission (Lossless)", self.get_intermission_inputs, self.execute_intermission)
        t_layout.addWidget(self.int_btn)
        t_layout.addStretch()

        self.tabs.addTab(tab, "⏸️ Intermission Cut")

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
            self.set_intermission_point()
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

    def set_position(self, position):
        self.media_player.setPosition(position)

    def position_changed(self, position):
        self.timeline_slider.setValue(position)
        self.update_time_label()

    def duration_changed(self, duration):
        self.timeline_slider.setRange(0, duration)
        self.update_time_label()

    def update_time_label(self):
        pos = self.media_player.position()
        dur = self.media_player.duration()
        def format_time(ms):
            s = ms // 1000
            m, s = divmod(s, 60)
            h, m = divmod(m, 60)
            return f"{h:02d}:{m:02d}:{s:02d}"
        self.time_label.setText(f"{format_time(pos)} / {format_time(dur)}")

    def set_intermission_point(self):
        ms = self.media_player.position()
        s = ms / 1000.0
        m, s = divmod(s, 60)
        h, m = divmod(m, 60)
        formatted = f"{int(h):02d}:{int(m):02d}:{s:06.3f}"
        self.int_time.setText(formatted)

    def get_intermission_inputs(self):
        path = self.int_drop.file_input.text().strip()
        time_val = self.int_time.text().strip()
        if not path or not time_val:
            return None
        return path, time_val

    def execute_intermission(self, inputs, est_seconds):
        path, time_val = inputs
        print(f"\n--- Split Initiated at {time_val} ---")
        success, p1, p2 = self.divider.split_at_intermission(path, time_val)
        if success:
            print(f"\n[SUCCESS] Split completed!\nFirst Half: {p1}\nSecond Half: {p2}")
        else:
            print(f"\n[ERROR] Split failed.")

    def keyPressEvent(self, event):
        if self.tabs.currentIndex() == 0:  # Only if we are on the Intermission Cut tab
            if self.int_time.hasFocus():
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


# ==========================================
# HOW TO USE THIS CODE (EXAMPLE)
# ==========================================
# Example usage:
# from src.processors.divider_ui import MainClass
# processor = MainClass()
# processor.run(input_file, output_file)
# ==========================================

# ==============================================================================
# 🎬 FEATURE: INTERNAL MODULE DOCUMENTATION (divider_ui.py)
# ==============================================================================
#
# 📝 WHAT IS THIS FILE?
#    This file, 'divider_ui.py', is a core component of the Onyx Engine. It is
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
