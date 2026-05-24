from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QLineEdit, QSlider, QStyle, QFrame
from PyQt6.QtCore import Qt, QUrl
from PyQt6.QtMultimedia import QMediaPlayer, QAudioOutput
from PyQt6.QtMultimediaWidgets import QVideoWidget
from src.ui.custom_widgets import DropZone
from src.processors import scene_sniper
import os

class SceneSniperUI(QWidget):
    """The Engine Room for Feature 12: Scene Sniper with Integrated Playback"""
    def __init__(self, back_callback):
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        # Header
        header_layout = QHBoxLayout()
        back_btn = QPushButton("⬅ Back to Dashboard")
        back_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        back_btn.setStyleSheet("padding: 8px; font-weight: bold; border-radius: 5px;")
        back_btn.clicked.connect(back_callback)
        
        title = QLabel(" 🎯 Scene Sniper")
        title.setStyleSheet("font-size: 22px; font-weight: bold;")
        
        header_layout.addWidget(back_btn)
        header_layout.addWidget(title)
        header_layout.addStretch()
        layout.addLayout(header_layout)
        
        # Drop Zone
        self.drop_zone = DropZone(self)
        self.drop_zone.file_input.textChanged.connect(self.load_video)
        layout.addWidget(self.drop_zone)

        # Integrated Video Player
        self.video_widget = QVideoWidget()
        self.video_widget.setMinimumHeight(400)
        self.video_widget.setStyleSheet("background-color: #000000; border-top-left-radius: 8px; border-top-right-radius: 8px;")
        layout.addWidget(self.video_widget)

        self.media_player = QMediaPlayer()
        self.audio_output = QAudioOutput()
        self.media_player.setAudioOutput(self.audio_output)
        self.media_player.setVideoOutput(self.video_widget)

        # VLC-Style Playback Bar
        player_bar = QFrame()
        player_bar.setStyleSheet("background-color: #1e1e1e; border-bottom-left-radius: 8px; border-bottom-right-radius: 8px; padding: 5px;")
        bar_layout = QVBoxLayout(player_bar)
        bar_layout.setContentsMargins(10, 5, 10, 10)

        self.timeline_slider = QSlider(Qt.Orientation.Horizontal)
        self.timeline_slider.setRange(0, 0)
        self.timeline_slider.setCursor(Qt.CursorShape.PointingHandCursor)
        self.timeline_slider.sliderMoved.connect(self.set_position)
        bar_layout.addWidget(self.timeline_slider)

        controls_layout = QHBoxLayout()
        self.rewind_btn = QPushButton("⏪ 10s")
        self.rewind_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.rewind_btn.setStyleSheet("background-color: transparent; font-weight: bold; padding: 5px;")
        self.rewind_btn.clicked.connect(self.skip_backward)
        
        self.play_btn = QPushButton()
        self.play_btn.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_MediaPlay))
        self.play_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.play_btn.setStyleSheet("background-color: transparent; padding: 5px;")
        self.play_btn.clicked.connect(self.toggle_playback)
        
        self.forward_btn = QPushButton("10s ⏩")
        self.forward_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.forward_btn.setStyleSheet("background-color: transparent; font-weight: bold; padding: 5px;")
        self.forward_btn.clicked.connect(self.skip_forward)

        self.time_label = QLabel("00:00:00 / 00:00:00")
        self.time_label.setStyleSheet("font-family: monospace; font-size: 14px; color: #aaaaaa;")

        controls_layout.addWidget(self.rewind_btn)
        controls_layout.addWidget(self.play_btn)
        controls_layout.addWidget(self.forward_btn)
        controls_layout.addStretch()
        controls_layout.addWidget(self.time_label)
        
        bar_layout.addLayout(controls_layout)
        layout.addWidget(player_bar)

        self.media_player.positionChanged.connect(self.position_changed)
        self.media_player.durationChanged.connect(self.duration_changed)
        layout.addSpacing(15)

        # Timing Controls
        time_layout = QHBoxLayout()
        self.start_input = QLineEdit()
        self.start_input.setPlaceholderText("Start Time")
        self.start_btn = QPushButton("📍 Set In")
        self.start_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.start_btn.clicked.connect(self.set_in_point)
        
        self.end_input = QLineEdit()
        self.end_input.setPlaceholderText("End Time")
        self.end_btn = QPushButton("📍 Set Out")
        self.end_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.end_btn.clicked.connect(self.set_out_point)

        time_layout.addWidget(self.start_input)
        time_layout.addWidget(self.start_btn)
        time_layout.addSpacing(20)
        time_layout.addWidget(self.end_input)
        time_layout.addWidget(self.end_btn)
        
        layout.addLayout(time_layout)
        layout.addSpacing(20)

        # Execution Button
        self.exec_btn = QPushButton("⚡ Extract Scene Natively")
        self.exec_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.exec_btn.setMinimumHeight(50)
        self.exec_btn.setStyleSheet("QPushButton { font-size: 16px; font-weight: bold; background-color: #2D72D9; color: white; border-radius: 8px; } QPushButton:hover { background-color: #3a82ef; }")
        self.exec_btn.clicked.connect(self.execute_sniper)
        layout.addWidget(self.exec_btn)

    # --- VIDEO PLAYER LOGIC ---
    def load_video(self, file_path):
        if file_path:
            self.media_player.setSource(QUrl.fromLocalFile(file_path))
            self.media_player.play()
            self.play_btn.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_MediaPause))

    def toggle_playback(self):
        if self.media_player.playbackState() == QMediaPlayer.PlaybackState.PlayingState:
            self.media_player.pause()
            self.play_btn.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_MediaPlay))
        else:
            self.media_player.play()
            self.play_btn.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_MediaPause))

    def skip_backward(self):
        new_pos = max(0, self.media_player.position() - 10000)
        self.media_player.setPosition(new_pos)

    def skip_forward(self):
        new_pos = min(self.media_player.duration(), self.media_player.position() + 10000)
        self.media_player.setPosition(new_pos)

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

    def execute_sniper(self):
        # 1. Grab inputs
        file_path = self.drop_zone.file_input.text().strip()
        start = self.start_input.text().strip()
        end = self.end_input.text().strip()
        
        # 2. Validation: Ensure we have all three requirements
        if not file_path or not start or not end:
            print("[UI Warning] Missing input! Need File, Start Time, and End Time.")
            # Optional: You could show a QMessageBox here for better UX
            return

        # 3. Create a smart output path (Saves in the same folder as the original)
        base_dir = os.path.dirname(file_path)
        file_name = os.path.basename(file_path)
        name_only, ext = os.path.splitext(file_name)
        
        # Format: OriginalName_Snipe_00-01-05.mp4
        output_name = f"{name_only}_Snipe_{start.replace(':', '-')}{ext}"
        final_output = os.path.join(base_dir, output_name)

        print(f"--- Sniper Initialized ---")
        print(f"Target: {file_name} | Range: {start} -> {end}")

        # 4. Call the Backend Processor
        # Assuming you have: from src.processors import scene_sniper
        success = scene_sniper.extract_scene(file_path, start, end, final_output)

        if success:
            print(f"[SUCCESS] Clip saved to: {final_output}")
        else:
            print(f"[ERROR] Sniper failed to extract clip.")