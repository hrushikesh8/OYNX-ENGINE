import os
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
                             QLabel, QFrame, QGridLayout, QStyle, QSlider, QTabWidget)
from PyQt6.QtCore import Qt, QUrl
from PyQt6.QtMultimedia import QMediaPlayer, QAudioOutput
from PyQt6.QtMultimediaWidgets import QVideoWidget
from src.ui.custom_widgets import DropZone
from src.processors.ladder import StreamLadder

class StreamLadderUI(QWidget):
    """
    Workspace for ABR profiles and Video Quality comparison.
    Tab 1: ABR Streaming Profiles Ladder (Features adaptive resolution generation).
    Tab 2: Side-by-Side Quality Comparer (Dual players synchronized on playback & seek).
    """
    def __init__(self, back_callback, orchestrator):
        super().__init__()
        self.orchestrator = orchestrator
        self.ladder_engine = StreamLadder()
        
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        layout.setContentsMargins(30, 30, 30, 30)

        # --- HEADER ---
        header = QHBoxLayout()
        back_btn = QPushButton("⬅ Back to Dashboard")
        back_btn.clicked.connect(back_callback)
        header.addWidget(back_btn)
        
        title = QLabel("🔄 Format, Ladder & Compare")
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

        # BUILD THE TABS
        self.setup_ladder_tab()
        self.setup_comparer_tab()

    # =========================================================================
    # TAB 1: ADAPTIVE BITRATE LADDER
    # =========================================================================
    def setup_ladder_tab(self):
        tab = QWidget()
        t_layout = QVBoxLayout(tab)
        t_layout.setContentsMargins(20, 20, 20, 20)

        t_layout.addWidget(QLabel("Step 1: Select Master Video File"))
        self.master_drop = DropZone(self)
        t_layout.addWidget(self.master_drop)
        t_layout.addSpacing(15)

        t_layout.addWidget(QLabel("Step 2: Select Output Directory for Ladder Profiles"))
        self.output_drop = DropZone(self, mode='dir')
        t_layout.addWidget(self.output_drop)
        t_layout.addSpacing(20)

        info_box = QFrame()
        info_box.setStyleSheet("background-color: #1a1a1a; border: 1px solid #333; border-radius: 8px; padding: 15px;")
        ib_layout = QVBoxLayout(info_box)
        ib_layout.addWidget(QLabel("<b>Adaptive Bitrate (ABR) Output Profiles:</b>"))
        ib_layout.addWidget(QLabel("• <b>High-End (1080p):</b> Target bitrate 5.0 Mbps"))
        ib_layout.addWidget(QLabel("• <b>Mid-Range (720p):</b> Target bitrate 2.5 Mbps"))
        ib_layout.addWidget(QLabel("• <b>Low-End (480p):</b> Target bitrate 1.0 Mbps"))
        t_layout.addWidget(info_box)
        t_layout.addSpacing(25)

        self.run_btn = QPushButton("🚀 Run Adaptive Ladder Encoding")
        self.run_btn.setMinimumHeight(60)
        self.run_btn.setStyleSheet("""
            QPushButton { background-color: #2D72D9; color: white; font-size: 16px; font-weight: bold; border-radius: 8px; }
            QPushButton:hover { background-color: #3a82ef; }
        """)
        self.run_btn.clicked.connect(self.run_ladder)
        t_layout.addWidget(self.run_btn)
        t_layout.addStretch()

        self.tabs.addTab(tab, "📶 ABR Stream Ladder")

    def run_ladder(self):
        master = self.master_drop.file_input.text().strip()
        out_dir = self.output_drop.file_input.text().strip()

        if not master or not out_dir:
            return

        # Prepare outputs list for async logging
        filename = os.path.splitext(os.path.basename(master))[0]
        
        # Add to background job queue
        # Since ladder.py encodes each profile using FFmpeg, we can run them in background.
        # However, to let the user do it easily, we can add profile generation function as a task!
        # We define a helper that runs the profiles.
        def run_profile_task():
            return self.ladder_engine.generate_profiles(master, out_dir)

        self.orchestrator.add_background_job(f"ABR Ladder: {filename}", run_profile_task)
        self.orchestrator.show_status_message(f"⏳ ABR Ladder task queued for: {filename}")

    # =========================================================================
    # TAB 2: SIDE-BY-SIDE VIDEO COMPARER
    # =========================================================================
    def setup_comparer_tab(self):
        tab = QWidget()
        t_layout = QVBoxLayout(tab)
        t_layout.setContentsMargins(20, 20, 20, 20)

        # File Selectors Row
        selectors = QHBoxLayout()
        
        v1_layout = QVBoxLayout()
        v1_layout.addWidget(QLabel("👈 Master Original Video"))
        self.comp_drop_a = DropZone(self)
        self.comp_drop_a.file_input.textChanged.connect(self.load_video_a)
        v1_layout.addWidget(self.comp_drop_a)
        selectors.addLayout(v1_layout)
        
        v2_layout = QVBoxLayout()
        v2_layout.addWidget(QLabel("👉 Remastered / Compressed Video"))
        self.comp_drop_b = DropZone(self)
        self.comp_drop_b.file_input.textChanged.connect(self.load_video_b)
        v2_layout.addWidget(self.comp_drop_b)
        selectors.addLayout(v2_layout)
        
        t_layout.addLayout(selectors)
        t_layout.addSpacing(15)

        # Dual Player Viewports
        player_grid = QGridLayout()
        
        self.video_widget_a = QVideoWidget()
        self.video_widget_a.setStyleSheet("background-color: black; border: 1px solid #333; border-radius: 6px;")
        self.video_widget_a.setMinimumHeight(350)
        
        self.video_widget_b = QVideoWidget()
        self.video_widget_b.setStyleSheet("background-color: black; border: 1px solid #333; border-radius: 6px;")
        self.video_widget_b.setMinimumHeight(350)

        player_grid.addWidget(self.video_widget_a, 0, 0)
        player_grid.addWidget(self.video_widget_b, 0, 1)
        t_layout.addLayout(player_grid)

        # Synchronized Media Players Setup
        self.player_a = QMediaPlayer()
        self.audio_output_a = QAudioOutput()
        self.player_a.setAudioOutput(self.audio_output_a)
        self.player_a.setVideoOutput(self.video_widget_a)

        self.player_b = QMediaPlayer()
        self.audio_output_b = QAudioOutput()
        self.player_b.setAudioOutput(self.audio_output_b)
        # Mute Player B by default to prevent audio overlap/echo
        self.audio_output_b.setMuted(True)
        self.player_b.setVideoOutput(self.video_widget_b)

        # VLC-Style Synced Control Bar
        control_bar = QFrame()
        control_bar.setStyleSheet("background-color: #1a1a1a; border-radius: 8px; padding: 5px;")
        bar_layout = QVBoxLayout(control_bar)

        self.timeline_slider = QSlider(Qt.Orientation.Horizontal)
        self.timeline_slider.setRange(0, 0)
        self.timeline_slider.setCursor(Qt.CursorShape.PointingHandCursor)
        self.timeline_slider.sliderMoved.connect(self.set_sync_position)
        bar_layout.addWidget(self.timeline_slider)

        controls = QHBoxLayout()
        self.play_btn = QPushButton()
        self.play_btn.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_MediaPlay))
        self.play_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.play_btn.clicked.connect(self.toggle_sync_playback)
        
        self.mute_a_btn = QPushButton("🔊 Mute Left")
        self.mute_a_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.mute_a_btn.setStyleSheet("background-color: #333; border: 1px solid #444; border-radius: 4px; padding: 5px;")
        self.mute_a_btn.clicked.connect(self.toggle_mute_a)
        
        self.mute_b_btn = QPushButton("🔇 Mute Right (Synced)")
        self.mute_b_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.mute_b_btn.setStyleSheet("background-color: #333; border: 1px solid #444; border-radius: 4px; padding: 5px;")
        self.mute_b_btn.clicked.connect(self.toggle_mute_b)

        self.time_label = QLabel("00:00:00 / 00:00:00")
        self.time_label.setStyleSheet("font-family: monospace; font-size: 14px; color: #888;")

        controls.addWidget(self.play_btn)
        controls.addSpacing(15)
        controls.addWidget(self.mute_a_btn)
        controls.addWidget(self.mute_b_btn)
        controls.addStretch()
        controls.addWidget(self.time_label)
        bar_layout.addLayout(controls)

        t_layout.addWidget(control_bar)

        # Hook position signals
        self.player_a.positionChanged.connect(self.sync_position_changed)
        self.player_a.durationChanged.connect(self.sync_duration_changed)

        self.tabs.addTab(tab, "🎞️ Video Quality Comparer")

    # --- SYNCHRONIZED PLAYER ACTIONS ---
    def load_video_a(self, path):
        if path and os.path.exists(path):
            self.player_a.setSource(QUrl.fromLocalFile(path))

    def load_video_b(self, path):
        if path and os.path.exists(path):
            self.player_b.setSource(QUrl.fromLocalFile(path))

    def toggle_sync_playback(self):
        if self.player_a.playbackState() == QMediaPlayer.PlaybackState.PlayingState:
            self.player_a.pause()
            self.player_b.pause()
            self.play_btn.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_MediaPlay))
        else:
            self.player_a.play()
            self.player_b.play()
            self.play_btn.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_MediaPause))

    def set_sync_position(self, pos):
        self.player_a.setPosition(pos)
        self.player_b.setPosition(pos)

    def sync_position_changed(self, position):
        self.timeline_slider.setValue(position)
        # Check alignment: if they drift by > 150ms, force resync
        if abs(self.player_a.position() - self.player_b.position()) > 150:
            self.player_b.setPosition(position)
        
        current = self.format_time(position)[:8]
        total = self.format_time(self.player_a.duration())[:8]
        self.time_label.setText(f"{current} / {total}")

    def sync_duration_changed(self, duration):
        self.timeline_slider.setRange(0, duration)

    def toggle_mute_a(self):
        is_muted = self.audio_output_a.isMuted()
        self.audio_output_a.setMuted(not is_muted)
        self.mute_a_btn.setText("🔇 Muted Left" if not is_muted else "🔊 Mute Left")

    def toggle_mute_b(self):
        is_muted = self.audio_output_b.isMuted()
        self.audio_output_b.setMuted(not is_muted)
        self.mute_b_btn.setText("🔊 Unmute Right" if not is_muted else "🔇 Mute Right (Synced)")

    def format_time(self, ms):
        seconds = (ms // 1000) % 60
        minutes = (ms // 60000) % 60
        hours = (ms // 3600000)
        return f"{hours:02d}:{minutes:02d}:{seconds:02d}"

    def closeEvent(self, event):
        # Prevent leaking player audio/video loops
        self.player_a.stop()
        self.player_b.stop()
        super().closeEvent(event)
