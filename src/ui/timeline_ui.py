import os
import json
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
                             QLabel, QFrame, QFileDialog, QTableWidget, 
                             QTableWidgetItem, QComboBox, QLineEdit, QSpinBox,
                             QAbstractItemView, QHeaderView, QSlider, QScrollArea, QStyle, QProgressBar)
from PyQt6.QtCore import Qt, pyqtSignal, QRectF, QUrl
from PyQt6.QtGui import QPainter, QColor, QPen, QBrush, QFont, QLinearGradient
from PyQt6.QtMultimedia import QMediaPlayer, QAudioOutput
from PyQt6.QtMultimediaWidgets import QVideoWidget
from src.ui.video_player import ClickableVideoWidget, PlayerContainer

from src.ui.custom_widgets import DropZone, SmartRunButton, VLCVolumeSlider
from src.processors.timeline_composer import TimelineComposer, get_media_properties

# Standard time converters
def seconds_to_timecode(seconds: float) -> str:
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = int(seconds % 60)
    ms = int(round((seconds - int(seconds)) * 1000))
    if ms >= 1000:
        s += 1
        ms -= 1000
    return f"{h:02d}:{m:02d}:{s:02d}.{ms:03d}"

def timecode_to_seconds(timecode: str) -> float:
    try:
        timecode = timecode.strip()
        if ':' in timecode:
            parts = timecode.split(':')
            if len(parts) == 3:
                h, m, s = parts
                return int(h) * 3600 + int(m) * 60 + float(s)
            elif len(parts) == 2:
                m, s = parts
                return int(m) * 60 + float(s)
        return float(timecode)
    except Exception:
        return 0.0


class DragDropTable(QTableWidget):
    """Custom TableWidget that receives media file drag & drop events."""
    files_dropped = pyqtSignal(list)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAcceptDrops(True)
        self.setDragEnabled(True)
        self.setDropIndicatorShown(True)

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.accept()
        else:
            super().dragEnterEvent(event)

    def dragMoveEvent(self, event):
        if event.mimeData().hasUrls():
            event.accept()
        else:
            super().dragMoveEvent(event)

    def dropEvent(self, event):
        if event.mimeData().hasUrls():
            event.setDropAction(Qt.DropAction.CopyAction)
            event.accept()
            paths = []
            for url in event.mimeData().urls():
                file_path = str(url.toLocalFile())
                ext = file_path.lower()
                if ext.endswith(('.mp4', '.mkv', '.avi', '.mov', '.m4v', '.webm', '.png', '.jpg', '.jpeg', '.webp', '.bmp', '.mp3', '.wav', '.m4a', '.aac')):
                    paths.append(file_path)
            if paths:
                self.files_dropped.emit(paths)
        else:
            super().dropEvent(event)


class TimelineVisualizer(QWidget):
    """
    Timeline Visualizer Widget.
    Draws horizontal track boxes of video/image segments and multiple parallel audio overlays.
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumHeight(160)
        self.clips = []
        self.audio_overlays = []

    def set_data(self, clips, audio_overlays):
        self.clips = clips
        self.audio_overlays = audio_overlays
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        w = self.width()
        h = self.height()

        painter.fillRect(0, 0, w, h, QColor("#111111"))

        # Calculate durations
        video_dur = 0.0
        for clip in self.clips:
            if clip.get('is_image', False):
                video_dur += clip['duration']
            else:
                video_dur += clip['duration'] / clip['speed']

        max_audio_dur = 0.0
        for aud in self.audio_overlays:
            max_audio_dur = max(max_audio_dur, aud.get('offset', 0.0) + aud.get('duration', 0.0))

        total_dur = max(video_dur, max_audio_dur, 1.0)

        # Draw margins
        margin_left = 15
        margin_right = 15
        draw_width = w - margin_left - margin_right

        # Draw top tick ruler
        ruler_y = 25
        painter.setPen(QPen(QColor("#2d2d2d"), 1))
        painter.drawLine(margin_left, ruler_y, margin_left + draw_width, ruler_y)

        # Paint time ticks
        num_ticks = 10
        tick_interval = total_dur / num_ticks
        painter.setFont(QFont("Consolas", 8))
        for i in range(num_ticks + 1):
            t = i * tick_interval
            x = margin_left + int((t / total_dur) * draw_width)
            painter.setPen(QPen(QColor("#2d2d2d"), 1))
            painter.drawLine(x, ruler_y - 4, x, ruler_y)

            time_str = f"{t:.1f}s"
            painter.setPen(QPen(QColor("#666666"), 1))
            painter.drawText(x - 20, ruler_y - 18, 40, 12, Qt.AlignmentFlag.AlignCenter, time_str)

        # Video Track Box
        video_y = 35
        video_height = 42

        if not self.clips:
            rect = QRectF(margin_left, video_y, draw_width, video_height)
            painter.setBrush(QBrush(QColor("#161616")))
            painter.setPen(QPen(QColor("#262626"), 1, Qt.PenStyle.DashLine))
            painter.drawRoundedRect(rect, 6, 6)
            painter.setPen(QPen(QColor("#555555"), 1))
            painter.setFont(QFont("Segoe UI", 9, QFont.Weight.Bold))
            painter.drawText(rect, Qt.AlignmentFlag.AlignCenter, "➕ Drag & drop media clips onto the table to begin composition")
        else:
            current_x = margin_left
            for idx, clip in enumerate(self.clips):
                is_image = clip.get('is_image', False)
                clip_dur = clip['duration'] if is_image else (clip['duration'] / clip['speed'])
                clip_w = int((clip_dur / total_dur) * draw_width)
                clip_w = max(2, clip_w)

                rect = QRectF(current_x, video_y, clip_w, video_height)

                if is_image:
                    hue = (idx * 55 + 30) % 360
                    color_top = QColor.fromHsl(hue, 160, 100)
                    color_bot = QColor.fromHsl(hue, 160, 50)
                    color_border = QColor.fromHsl(hue, 180, 110)
                else:
                    hue = (idx * 55 + 210) % 360
                    color_top = QColor.fromHsl(hue, 150, 110)
                    color_bot = QColor.fromHsl(hue, 150, 60)
                    color_border = QColor.fromHsl(hue, 170, 120)

                grad = QLinearGradient(rect.topLeft(), rect.bottomLeft())
                grad.setColorAt(0.0, color_top)
                grad.setColorAt(1.0, color_bot)

                painter.setBrush(QBrush(grad))
                painter.setPen(QPen(color_border, 1))
                painter.drawRoundedRect(rect, 4, 4)

                if clip_w > 45:
                    painter.setPen(QPen(QColor("#ffffff"), 1))
                    painter.setFont(QFont("Segoe UI", 8, QFont.Weight.Bold))
                    
                    elided_name = painter.fontMetrics().elidedText(clip['name'], Qt.TextElideMode.ElideRight, int(clip_w - 12))
                    painter.drawText(rect.adjusted(6, 4, -6, -18), Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop, elided_name)

                    painter.setFont(QFont("Segoe UI", 7))
                    info_str = f"Slide | {clip_dur:.1f}s" if is_image else f"{clip['speed']}x | {clip_dur:.1f}s"
                    painter.drawText(rect.adjusted(6, 18, -6, -4), Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter, info_str)

                    painter.setFont(QFont("Segoe UI", 8, QFont.Weight.Bold))
                    badge_prefix = "🖼️" if is_image else "#"
                    painter.drawText(rect.adjusted(6, 4, -6, -18), Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignTop, f"{badge_prefix}{idx+1}")

                current_x += clip_w

        # Audio Track Indicator Row
        audio_y = 88
        audio_height = 14

        if self.audio_overlays:
            for idx, aud in enumerate(self.audio_overlays):
                offset = aud.get('offset', 0.0)
                dur = aud.get('duration', 5.0)
                
                start_x = margin_left + int((offset / total_dur) * draw_width)
                w_x = int((dur / total_dur) * draw_width)
                w_x = max(2, w_x)

                if start_x + w_x > margin_left + draw_width:
                    w_x = (margin_left + draw_width) - start_x

                rect = QRectF(start_x, audio_y + idx * 16, w_x, audio_height)

                grad = QLinearGradient(rect.topLeft(), rect.bottomLeft())
                grad.setColorAt(0.0, QColor("#104a27"))
                grad.setColorAt(1.0, QColor("#082c16"))

                painter.setBrush(QBrush(grad))
                painter.setPen(QPen(QColor("#00ff66"), 1))
                painter.drawRoundedRect(rect, 3, 3)

                if w_x > 40:
                    painter.setPen(QPen(QColor("#ffffff"), 1))
                    painter.setFont(QFont("Segoe UI", 7, QFont.Weight.Bold))
                    name_elided = painter.fontMetrics().elidedText(aud['name'], Qt.TextElideMode.ElideRight, int(w_x - 12))
                    painter.drawText(rect.adjusted(6, 0, -6, 0), Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft, name_elided)
        else:
            rect = QRectF(margin_left, audio_y, draw_width, audio_height)
            painter.setBrush(QBrush(QColor("#161616")))
            painter.setPen(QPen(QColor("#222222"), 1, Qt.PenStyle.DashLine))
            painter.drawRoundedRect(rect, 4, 4)
            painter.setPen(QPen(QColor("#666666"), 1))
            painter.setFont(QFont("Segoe UI", 8, QFont.Weight.Bold))
            painter.drawText(rect, Qt.AlignmentFlag.AlignCenter, "🔇 No background music overlays loaded")


class TimelineComposerUI(QWidget):
    """
    Frontend UI Workspace for Onyx Multi-Track Timeline Composer.
    Handles Audio Track DropZone, B-roll Drag-Drop Table, Global resolution presets,
    scaling conform, volume levels, visual segment track updating, and job queuing.
    """
    def __init__(self, back_callback, orchestrator):
        super().__init__()
        self.orchestrator = orchestrator
        self.back_callback = back_callback
        self.clips = []
        self.audio_overlays = []
        self.current_row = -1
        self.active_render_worker = None

        # Central layout
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        layout.setContentsMargins(30, 20, 30, 20)

        # ---------------------------------------------------------------------
        # 1. HEADER ROW
        # ---------------------------------------------------------------------
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
        back_btn.clicked.connect(self.back_callback)

        title = QLabel("🎬 Multi-Track Timeline Composer")
        title.setStyleSheet("font-size: 22px; font-weight: bold; color: white;")

        header.addWidget(back_btn)
        header.addSpacing(15)
        header.addWidget(title)
        header.addStretch()

        self.duration_counter = QLabel("Total Duration: 0.0s")
        self.duration_counter.setStyleSheet("font-size: 15px; font-weight: bold; color: #2D72D9; font-family: 'Consolas', monospace;")
        header.addWidget(self.duration_counter)
        header.addSpacing(25)

        add_clip_btn = QPushButton("➕ Add Media Clip")
        add_clip_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        add_clip_btn.setStyleSheet("""
            QPushButton {
                background-color: #1a1a1a;
                border: 1px solid #333;
                border-radius: 6px;
                color: #eee;
                font-weight: bold;
                padding: 8px 16px;
            }
            QPushButton:hover {
                background-color: #252525;
                border-color: #444;
            }
        """)
        add_clip_btn.clicked.connect(self.browse_media_clips)
        header.addWidget(add_clip_btn)

        layout.addLayout(header)
        layout.addSpacing(10)

        # ---------------------------------------------------------------------
        # 2. AUDIO DROP ZONE & LIST
        # ---------------------------------------------------------------------
        audio_section = QVBoxLayout()
        
        audio_header_row = QHBoxLayout()
        audio_header_row.addWidget(QLabel("<b>1. Multi-Track Background Audio Overlays</b>"))
        audio_header_row.addStretch()
        
        add_audio_btn = QPushButton("🎵 Add Background Music Track")
        add_audio_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        add_audio_btn.setStyleSheet("""
            QPushButton { background-color: #1e261e; border: 1px solid #2e3b2e; border-radius: 4px; padding: 4px 10px; font-weight: bold; color: #00ff66; }
            QPushButton:hover { background-color: #2e3b2e; }
        """)
        add_audio_btn.clicked.connect(self.browse_audio_overlay)
        audio_header_row.addWidget(add_audio_btn)
        audio_section.addLayout(audio_header_row)

        self.audio_table = QTableWidget(self)
        self.audio_table.setColumnCount(4)
        self.audio_table.setHorizontalHeaderLabels(["Music Track File Name", "Timeline Start Offset (s)", "Volume", "Actions"])
        self.audio_table.setMinimumHeight(100)
        self.audio_table.setMaximumHeight(130)
        self.audio_table.setStyleSheet("""
            QTableWidget { background-color: #121212; border: 1px solid #222; border-radius: 6px; color: #eee; }
            QHeaderView::section { background-color: #181818; color: #888; border-bottom: 1px solid #222; padding: 4px; }
        """)
        
        aud_header = self.audio_table.horizontalHeader()
        aud_header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        aud_header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        aud_header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        aud_header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        audio_section.addWidget(self.audio_table)
        
        layout.addLayout(audio_section)
        layout.addSpacing(10)

        # ---------------------------------------------------------------------
        # 3. SPLIT PANEL
        # ---------------------------------------------------------------------
        split_layout = QHBoxLayout()
        split_layout.setSpacing(20)

        # LEFT COLUMN
        left_column = QWidget()
        left_lay = QVBoxLayout(left_column)
        left_lay.setContentsMargins(0, 0, 0, 0)
        left_lay.setSpacing(10)

        left_lay.addWidget(QLabel("<b>2. Timeline Media Clips Track List</b> (Click a row to load clip monitor preview)"))
        
        self.table = DragDropTable(self)
        self.table.setColumnCount(7)
        self.table.setHorizontalHeaderLabels(["Reorder", "File Name", "Trim In", "Trim Out / Dur (s)", "Speed", "Volume", "Actions"])
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.table.files_dropped.connect(self.add_clips_by_paths)
        self.table.cellClicked.connect(self.on_table_cell_clicked)
        self.table.setStyleSheet("""
            QTableWidget {
                background-color: #141414;
                border: 1px solid #282828;
                border-radius: 8px;
                color: #eee;
            }
            QTableWidget::item {
                padding: 4px;
            }
            QHeaderView::section {
                background-color: #1a1a1a;
                color: #888;
                font-weight: bold;
                border: none;
                border-bottom: 1px solid #282828;
                padding: 6px;
            }
        """)
        
        header_view = self.table.horizontalHeader()
        header_view.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        header_view.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        header_view.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        header_view.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        header_view.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        header_view.setSectionResizeMode(5, QHeaderView.ResizeMode.ResizeToContents)
        header_view.setSectionResizeMode(6, QHeaderView.ResizeMode.ResizeToContents)

        left_lay.addWidget(self.table)
        split_layout.addWidget(left_column, 62)

        # RIGHT COLUMN
        right_column = QWidget()
        right_lay = QVBoxLayout(right_column)
        right_lay.setContentsMargins(0, 0, 0, 0)
        right_lay.setSpacing(10)

        right_lay.addWidget(QLabel("<b>3. Clip Monitor Preview</b>"))
        
        self.video_widget = QVideoWidget()
        
        self.controls_overlay = QFrame()
        self.controls_overlay.setStyleSheet("""
            QFrame { background-color: rgba(20, 20, 20, 0.9); border: 1px solid rgba(255, 255, 255, 0.1); border-radius: 8px; }
            QPushButton { background-color: transparent; border: none; color: #ffffff; font-weight: bold; font-size: 10px; padding: 3px; }
            QPushButton:hover { color: #2D72D9; }
            QLabel { color: #bbbbbb; font-size: 10px; background: transparent; border: none; }
        """)
        
        overlay_layout = QVBoxLayout(self.controls_overlay)
        overlay_layout.setContentsMargins(10, 4, 10, 4)
        overlay_layout.setSpacing(2)
        
        slider_row = QHBoxLayout()
        self.timeline_slider = QSlider(Qt.Orientation.Horizontal)
        self.timeline_slider.setRange(0, 0)
        self.timeline_slider.setCursor(Qt.CursorShape.PointingHandCursor)
        self.timeline_slider.setStyleSheet("""
            QSlider::groove:horizontal { height: 3px; background: rgba(255, 255, 255, 0.2); border-radius: 1px; }
            QSlider::sub-page:horizontal { background: #2D72D9; border-radius: 1px; }
            QSlider::handle:horizontal { background: #ffffff; width: 10px; height: 10px; margin-top: -3px; margin-bottom: -3px; border-radius: 5px; }
            QSlider::handle:horizontal:hover { background: #2D72D9; }
        """)
        self.timeline_slider.sliderMoved.connect(self.set_position)
        slider_row.addWidget(self.timeline_slider)
        
        self.time_label = QLabel("00:00:00 / 00:00:00")
        self.time_label.setStyleSheet("font-family: monospace; font-size: 10px; color: #aaaaaa;")
        slider_row.addWidget(self.time_label)
        overlay_layout.addLayout(slider_row)
        
        btn_row = QHBoxLayout()
        btn_row.setSpacing(6)
        
        self.rewind_btn = QPushButton("⏪ 10s")
        self.rewind_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.rewind_btn.clicked.connect(self.skip_backward)
        btn_row.addWidget(self.rewind_btn)
        
        self.play_btn = QPushButton()
        self.play_btn.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_MediaPlay))
        self.play_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.play_btn.clicked.connect(self.toggle_playback)
        btn_row.addWidget(self.play_btn)
        
        self.forward_btn = QPushButton("10s ⏩")
        self.forward_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.forward_btn.clicked.connect(self.skip_forward)
        btn_row.addWidget(self.forward_btn)
        
        btn_row.addSpacing(10)
        
        self.set_in_btn = QPushButton("📍 Set In")
        self.set_in_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.set_in_btn.setStyleSheet("color: #00ff66; font-weight: bold;")
        self.set_in_btn.clicked.connect(self.set_player_trim_in)
        btn_row.addWidget(self.set_in_btn)
        
        self.set_out_btn = QPushButton("📍 Set Out")
        self.set_out_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.set_out_btn.setStyleSheet("color: #ff3333; font-weight: bold;")
        self.set_out_btn.clicked.connect(self.set_player_trim_out)
        btn_row.addWidget(self.set_out_btn)
        
        btn_row.addStretch()
        
        self.mute_btn = QPushButton("🔊")
        self.mute_btn.setFixedSize(24, 24)
        self.mute_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.mute_btn.setStyleSheet("QPushButton { font-size: 14px; border-radius: 12px; background-color: transparent; color: white; } QPushButton:hover { background-color: rgba(255, 255, 255, 0.1); }")
        self.mute_btn.clicked.connect(self.toggle_mute)
        btn_row.addWidget(self.mute_btn)
        
        self.volume_slider = VLCVolumeSlider()
        self.volume_slider.setValue(100)
        self.volume_slider.valueChanged.connect(self.set_volume)
        btn_row.addWidget(self.volume_slider)
        
        overlay_layout.addLayout(btn_row)

        self.controls_overlay.setSizePolicy(self.controls_overlay.sizePolicy().Policy.Preferred, self.controls_overlay.sizePolicy().Policy.Fixed)
        self.controls_overlay.setMinimumHeight(75)

        self.controls_overlay.setSizePolicy(self.controls_overlay.sizePolicy().Policy.Preferred, self.controls_overlay.sizePolicy().Policy.Fixed)
        self.controls_overlay.setMinimumHeight(75)

        self.player_container = PlayerContainer(self.video_widget, self.controls_overlay)
        self.player_container.setMinimumHeight(200)
        right_lay.addWidget(self.player_container, stretch=1)

        self.media_player = QMediaPlayer()
        self.audio_output = QAudioOutput()
        self.media_player.setAudioOutput(self.audio_output)
        self.media_player.setVideoOutput(self.video_widget)
        self.media_player.positionChanged.connect(self.position_changed)
        self.media_player.durationChanged.connect(self.duration_changed)

        # Scroll wrapper for inspector parameters
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("""
            QScrollArea { border: none; background: transparent; }
            QScrollBar:vertical { width: 8px; background: #121212; }
            QScrollBar::handle:vertical { background: #262626; border-radius: 4px; }
        """)

        scroll_content = QWidget()
        scroll_layout = QVBoxLayout(scroll_content)
        scroll_layout.setContentsMargins(0, 0, 5, 0)
        scroll_layout.setSpacing(12)

        # Inspector Card Box
        self.settings_card = QFrame()
        self.settings_card.setStyleSheet("background-color: #181818; border: 1px solid #262626; border-radius: 8px; padding: 12px;")
        card_layout = QVBoxLayout(self.settings_card)
        card_layout.setSpacing(10)

        # Selected Clip Card
        self.clip_editor_frame = QFrame()
        self.clip_editor_frame.setStyleSheet("background-color: #1a1a24; border: 1px solid #2e2e42; border-radius: 6px; padding: 10px;")
        self.clip_editor_frame.setEnabled(False)
        clip_lay = QVBoxLayout(self.clip_editor_frame)
        clip_lay.setSpacing(8)

        self.selected_clip_label = QLabel("No clip selected (Select from table)")
        self.selected_clip_label.setStyleSheet("font-weight: bold; color: #ff9944; font-size: 13px;")
        clip_lay.addWidget(self.selected_clip_label)

        # Crop combo
        crop_lay = QHBoxLayout()
        crop_lay.addWidget(QLabel("Clip Crop aspect:"))
        self.clip_crop_combo = QComboBox()
        self.clip_crop_combo.addItems(["No Crop", "Square (1:1)", "Vertical (9:16)", "Widescreen (16:9)"])
        self.clip_crop_combo.currentIndexChanged.connect(self.on_clip_crop_changed)
        self.clip_crop_combo.setStyleSheet("QComboBox { background-color: #111; border: 1px solid #333; border-radius: 4px; color: white; padding: 4px; }")
        crop_lay.addWidget(self.clip_crop_combo)
        clip_lay.addLayout(crop_lay)

        # COLOR GRADING PARAMETERS
        clip_lay.addWidget(QLabel("<b>🎨 Color Grading & EQ Filters</b>"))
        
        # Brightness Slider
        bright_row = QHBoxLayout()
        self.bright_lbl = QLabel("Brightness: 0.0")
        bright_row.addWidget(self.bright_lbl)
        self.bright_slider = QSlider(Qt.Orientation.Horizontal)
        self.bright_slider.setRange(-100, 100)
        self.bright_slider.setValue(0)
        self.bright_slider.valueChanged.connect(self.on_color_slider_changed)
        bright_row.addWidget(self.bright_slider)
        clip_lay.addLayout(bright_row)

        # Contrast Slider
        contrast_row = QHBoxLayout()
        self.contrast_lbl = QLabel("Contrast: 1.0x")
        contrast_row.addWidget(self.contrast_lbl)
        self.contrast_slider = QSlider(Qt.Orientation.Horizontal)
        self.contrast_slider.setRange(0, 200)
        self.contrast_slider.setValue(100)
        self.contrast_slider.valueChanged.connect(self.on_color_slider_changed)
        contrast_row.addWidget(self.contrast_slider)
        clip_lay.addLayout(contrast_row)

        # Saturation Slider
        sat_row = QHBoxLayout()
        self.sat_lbl = QLabel("Saturation: 1.0x")
        sat_row.addWidget(self.sat_lbl)
        self.sat_slider = QSlider(Qt.Orientation.Horizontal)
        self.sat_slider.setRange(0, 200)
        self.sat_slider.setValue(100)
        self.sat_slider.valueChanged.connect(self.on_color_slider_changed)
        sat_row.addWidget(self.sat_slider)
        clip_lay.addLayout(sat_row)

        # Gamma Slider
        gamma_row = QHBoxLayout()
        self.gamma_lbl = QLabel("Gamma: 1.0x")
        gamma_row.addWidget(self.gamma_lbl)
        self.gamma_slider = QSlider(Qt.Orientation.Horizontal)
        self.gamma_slider.setRange(50, 200)
        self.gamma_slider.setValue(100)
        self.gamma_slider.valueChanged.connect(self.on_color_slider_changed)
        gamma_row.addWidget(self.gamma_slider)
        clip_lay.addLayout(gamma_row)

        card_layout.addWidget(self.clip_editor_frame)

        card_layout.addWidget(QLabel("<b>4. Global Output Parameters</b>"))

        # Aspect Ratio Selector
        card_layout.addWidget(QLabel("Aspect Ratio Preset:"))
        self.preset_combo = QComboBox()
        self.preset_combo.addItems([
            "YouTube Widescreen (16:9 - 1080p)",
            "Instagram Reel / TikTok (9:16 - 1080p)",
            "Instagram Square (1:1 - 1080p)",
            "4K Ultra HD (16:9 - 2160p)",
            "Custom Resolution"
        ])
        self.preset_combo.currentIndexChanged.connect(self.on_preset_changed)
        self.preset_combo.setStyleSheet("QComboBox { background-color: #111; border: 1px solid #333; border-radius: 4px; color: white; padding: 4px; }")
        card_layout.addWidget(self.preset_combo)

        # Custom sizes
        res_layout = QHBoxLayout()
        width_box = QVBoxLayout()
        width_box.addWidget(QLabel("Width:"))
        self.width_input = QSpinBox()
        self.width_input.setRange(120, 7680)
        self.width_input.setValue(1920)
        self.width_input.setEnabled(False)
        self.width_input.setStyleSheet("background-color: #111; color: white; border: 1px solid #333; padding: 3px;")
        width_box.addWidget(self.width_input)
        res_layout.addLayout(width_box)

        height_box = QVBoxLayout()
        height_box.addWidget(QLabel("Height:"))
        self.height_input = QSpinBox()
        self.height_input.setRange(120, 7680)
        self.height_input.setValue(1080)
        self.height_input.setEnabled(False)
        self.height_input.setStyleSheet("background-color: #111; color: white; border: 1px solid #333; padding: 3px;")
        height_box.addWidget(self.height_input)
        res_layout.addLayout(height_box)

        card_layout.addLayout(res_layout)

        # Scale fit/fill
        card_layout.addWidget(QLabel("Scaling conform Mode:"))
        self.scale_combo = QComboBox()
        self.scale_combo.addItems([
            "Fit (Letterbox with black background)",
            "Fill (Crop and Zoom to eliminate borders)"
        ])
        self.scale_combo.setStyleSheet("QComboBox { background-color: #111; border: 1px solid #333; border-radius: 4px; color: white; padding: 4px; }")
        card_layout.addWidget(self.scale_combo)

        # Audio Mix Mode
        card_layout.addWidget(QLabel("Audio Mix Mode:"))
        self.mix_combo = QComboBox()
        self.mix_combo.addItems([
            "Mix Video Audios + Background Music",
            "Keep Original Video Audios Only"
        ])
        self.mix_combo.setStyleSheet("QComboBox { background-color: #111; border: 1px solid #333; border-radius: 4px; color: white; padding: 4px; }")
        card_layout.addWidget(self.mix_combo)

        # Quick Clear list
        card_layout.addSpacing(5)
        self.clear_all_btn = QPushButton("🗑️ Clear Timeline Clips")
        self.clear_all_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.clear_all_btn.setStyleSheet("""
            QPushButton { background-color: #1e1e1e; border: 1px solid #333; border-radius: 5px; padding: 6px; color: #888; font-weight: bold; }
            QPushButton:hover { background-color: #262626; color: white; }
        """)
        self.clear_all_btn.clicked.connect(self.clear_all_clips)
        card_layout.addWidget(self.clear_all_btn)

        scroll_layout.addWidget(self.settings_card)
        scroll.setWidget(scroll_content)
        right_lay.addWidget(scroll)

        # LIVE PROGRESS & CANCEL AREA (Ancored at the bottom of Right Column)
        self.progress_frame = QFrame()
        self.progress_frame.setStyleSheet("background-color: #161622; border: 1px solid #2d2d44; border-radius: 8px; padding: 10px;")
        self.progress_frame.hide()
        
        prog_lay = QVBoxLayout(self.progress_frame)
        prog_lay.setSpacing(6)
        
        prog_status_row = QHBoxLayout()
        self.progress_label = QLabel("Rendering: 0% (estimating time...)")
        self.progress_label.setStyleSheet("color: #00ff66; font-size: 11px; font-weight: bold;")
        prog_status_row.addWidget(self.progress_label)
        
        self.cancel_render_btn = QPushButton("🚫 Cancel")
        self.cancel_render_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.cancel_render_btn.setStyleSheet("""
            QPushButton { background-color: #2a1414; border: 1px solid #ff3333; border-radius: 4px; color: #ff3333; font-weight: bold; font-size: 10px; padding: 3px 8px; }
            QPushButton:hover { background-color: #3a1a1a; }
        """)
        self.cancel_render_btn.clicked.connect(self.abort_render)
        prog_status_row.addWidget(self.cancel_render_btn)
        prog_lay.addLayout(prog_status_row)
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setStyleSheet("""
            QProgressBar { border: 1px solid #333; border-radius: 4px; height: 10px; background-color: #111; text-align: center; color: transparent; }
            QProgressBar::chunk { background-color: #2D72D9; border-radius: 3px; }
        """)
        prog_lay.addWidget(self.progress_bar)
        
        right_lay.addWidget(self.progress_frame)

        split_layout.addWidget(right_column, 38)
        layout.addLayout(split_layout)
        layout.addSpacing(10)

        # ---------------------------------------------------------------------
        # 4. TIMELINE VISUALIZER TRACK
        # ---------------------------------------------------------------------
        self.visualizer = TimelineVisualizer(self)
        layout.addWidget(self.visualizer)
        layout.addSpacing(10)

        # ---------------------------------------------------------------------
        # 5. RENDER TRIGGER BUTTON
        # ---------------------------------------------------------------------
        self.exec_btn = SmartRunButton("⚡ Compile & Render Timeline", self.get_timeline_inputs, self.trigger_render, speed_multiplier=10.0)
        layout.addWidget(self.exec_btn)

    def get_timeline_inputs(self):
        if not self.clips:
            self.orchestrator.show_status_message("❌ Error: No media clips loaded!")
            return None
        return [c['file'] for c in self.clips]

    # ---------------------------------------------------------------------
    # LOGIC COMPONENT HANDLERS
    # ---------------------------------------------------------------------

    def browse_media_clips(self):
        files, _ = QFileDialog.getOpenFileNames(
            self, "Select Video or Image B-Roll Clips", "", 
            "Media Files (*.mp4 *.mkv *.avi *.mov *.m4v *.webm *.png *.jpg *.jpeg *.webp *.bmp);;Video Files (*.mp4 *.mkv *.avi *.mov *.m4v *.webm);;Image Files (*.png *.jpg *.jpeg *.webp *.bmp)"
        )
        if files:
            self.add_clips_by_paths(files)

    def add_clips_by_paths(self, paths):
        for path in paths:
            is_image = path.lower().endswith(('.png', '.jpg', '.jpeg', '.webp', '.bmp'))
            if is_image:
                clip = {
                    'file': path,
                    'name': os.path.basename(path),
                    'is_image': True,
                    'duration': 3.0,
                    'speed': 1.0,
                    'volume': 0.0,
                    'crop_aspect': 'None',
                    'brightness': 0.0,
                    'contrast': 1.0,
                    'saturation': 1.0,
                    'gamma': 1.0
                }
            else:
                duration, _, _ = get_media_properties(path)
                clip = {
                    'file': path,
                    'name': os.path.basename(path),
                    'is_image': False,
                    'start': '00:00:00.000',
                    'end': seconds_to_timecode(duration),
                    'orig_duration': duration,
                    'duration': duration,
                    'speed': 1.0,
                    'volume': 1.0,
                    'crop_aspect': 'None',
                    'brightness': 0.0,
                    'contrast': 1.0,
                    'saturation': 1.0,
                    'gamma': 1.0
                }
            self.clips.append(clip)
        self.populate_table()
        self.update_visualizer()
        self.select_clip_row(len(self.clips) - 1)

    def browse_audio_overlay(self):
        import sys
        start_dir = getattr(sys, '_onyx_last_dir', os.path.expanduser("~"))
        files, _ = QFileDialog.getOpenFileNames(
            self, "Select Background Music Track Overlay", start_dir, 
            "Audio Files (*.mp3 *.wav *.m4a *.aac *.ogg);;All Files (*)"
        )
        if files:
            sys._onyx_last_dir = os.path.dirname(files[0])
            for path in files:
                duration, _, _ = get_media_properties(path)
                aud = {
                    'file': path,
                    'name': os.path.basename(path),
                    'offset': 0.0,
                    'volume': 1.0,
                    'duration': duration
                }
                self.audio_overlays.append(aud)
            self.populate_audio_table()
            self.update_visualizer()

    def populate_audio_table(self):
        self.audio_table.setRowCount(len(self.audio_overlays))
        for idx, aud in enumerate(self.audio_overlays):
            # Name
            self.audio_table.setCellWidget(idx, 0, QLabel(f"🎵 {aud['name']}"))
            
            # Offset input
            offset_edit = QLineEdit(f"{aud['offset']:.1f}")
            offset_edit.setFixedWidth(70)
            offset_edit.setAlignment(Qt.AlignmentFlag.AlignCenter)
            offset_edit.setStyleSheet("background-color: #1a1a1a; border: 1px solid #333; color: white; padding: 3px;")
            offset_edit.editingFinished.connect(lambda i=idx, edit=offset_edit: self.on_audio_offset_changed(i, edit))
            self.audio_table.setCellWidget(idx, 1, offset_edit)

            # Volume combo
            vol_combo = QComboBox()
            vol_combo.addItems(["Mute", "25%", "50%", "100%", "150%", "200%"])
            v_val = aud.get('volume', 1.0)
            if v_val == 0.0:
                vol_combo.setCurrentText("Mute")
            else:
                vol_combo.setCurrentText(f"{int(v_val * 100)}%")
            vol_combo.setFixedWidth(70)
            vol_combo.setStyleSheet("QComboBox { background-color: #1a1a1a; border: 1px solid #333; color: white; padding: 3px; }")
            vol_combo.currentIndexChanged.connect(lambda state, i=idx, combo=vol_combo: self.on_audio_volume_changed(i, combo))
            self.audio_table.setCellWidget(idx, 2, vol_combo)

            # Actions
            del_btn = QPushButton("🗑️ Remove")
            del_btn.setCursor(Qt.CursorShape.PointingHandCursor)
            del_btn.setStyleSheet("""
                QPushButton { background-color: #1a1414; border: 1px solid #3a1a1a; border-radius: 4px; color: #ff3333; font-size: 10px; padding: 4px; }
                QPushButton:hover { background-color: #3a1a1a; }
            """)
            del_btn.clicked.connect(lambda checked, i=idx: self.delete_audio_track(i))
            self.audio_table.setCellWidget(idx, 3, del_btn)

    def on_audio_offset_changed(self, row, edit):
        try:
            val = float(edit.text().strip())
            val = max(0.0, val)
            self.audio_overlays[row]['offset'] = val
        except ValueError:
            val = 0.0
            self.audio_overlays[row]['offset'] = val
        edit.setText(f"{val:.1f}")
        self.update_visualizer()

    def on_audio_volume_changed(self, row, combo):
        txt = combo.currentText()
        if txt == "Mute":
            vol = 0.0
        else:
            vol = float(txt.replace("%", "")) / 100.0
        self.audio_overlays[row]['volume'] = vol

    def delete_audio_track(self, row):
        if 0 <= row < len(self.audio_overlays):
            self.audio_overlays.pop(row)
            self.populate_audio_table()
            self.update_visualizer()

    def clear_all_clips(self):
        self.clips.clear()
        self.media_player.stop()
        self.select_clip_row(-1)
        self.populate_table()
        self.update_visualizer()

    def clear_audio_track(self):
        self.audio_drop.file_input.clear()
        self.master_audio_dur = 0.0
        self.update_visualizer()

    def on_audio_changed(self, text):
        path = text.strip()
        if path and os.path.exists(path):
            self.master_audio_dur, _, _ = get_media_properties(path)
        else:
            self.master_audio_dur = 0.0
        self.update_visualizer()

    def on_preset_changed(self, idx):
        if idx == 0:  # 16:9
            self.width_input.setValue(1920)
            self.height_input.setValue(1080)
            self.width_input.setEnabled(False)
            self.height_input.setEnabled(False)
        elif idx == 1:  # 9:16
            self.width_input.setValue(1080)
            self.height_input.setValue(1920)
            self.width_input.setEnabled(False)
            self.height_input.setEnabled(False)
        elif idx == 2:  # 1:1
            self.width_input.setValue(1080)
            self.height_input.setValue(1080)
            self.width_input.setEnabled(False)
            self.height_input.setEnabled(False)
        elif idx == 3:  # 4K UHD
            self.width_input.setValue(3840)
            self.height_input.setValue(2160)
            self.width_input.setEnabled(False)
            self.height_input.setEnabled(False)
        else:  # Custom
            self.width_input.setEnabled(True)
            self.height_input.setEnabled(True)

    def on_master_vol_changed(self, value):
        self.master_vol_label.setText(f"Background Music Volume: {value}%")

    def update_mix_mode_ui(self, idx):
        pass

    def calculate_total_duration(self) -> float:
        total = 0.0
        for c in self.clips:
            if c.get('is_image', False):
                total += c['duration']
            else:
                total += c['duration'] / c['speed']
        return total

    def update_visualizer(self):
        self.visualizer.set_data(self.clips, self.audio_overlays)
        total_dur = self.calculate_total_duration()
        self.duration_counter.setText(f"Total Duration: {total_dur:.1f}s")
        if total_dur > 60.1:
            self.duration_counter.setStyleSheet("font-size: 15px; font-weight: bold; color: #ff3333; font-family: 'Consolas', monospace;")
        else:
            self.duration_counter.setStyleSheet("font-size: 15px; font-weight: bold; color: #2D72D9; font-family: 'Consolas', monospace;")

    def on_table_cell_clicked(self, row, col):
        self.select_clip_row(row)

    def select_clip_row(self, row):
        if row < 0 or row >= len(self.clips):
            self.current_row = -1
            self.clip_editor_frame.setEnabled(False)
            self.selected_clip_label.setText("No clip selected (Select from table)")
            return

        self.current_row = row
        self.table.selectRow(row)
        clip = self.clips[row]
        
        self.clip_editor_frame.setEnabled(True)
        self.selected_clip_label.setText(f"Selected: {clip['name']}")
        
        # Block signals to prevent infinite value update loops
        self.clip_crop_combo.blockSignals(True)
        crop_val = clip.get('crop_aspect', 'None')
        if crop_val == 'None':
            self.clip_crop_combo.setCurrentText("No Crop")
        elif crop_val == '1:1':
            self.clip_crop_combo.setCurrentText("Square (1:1)")
        elif crop_val == '9:16':
            self.clip_crop_combo.setCurrentText("Vertical (9:16)")
        elif crop_val == '16:9':
            self.clip_crop_combo.setCurrentText("Widescreen (16:9)")
        self.clip_crop_combo.blockSignals(False)

        # Load color sliders
        self.bright_slider.blockSignals(True)
        self.contrast_slider.blockSignals(True)
        self.sat_slider.blockSignals(True)
        self.gamma_slider.blockSignals(True)

        self.bright_slider.setValue(int(clip.get('brightness', 0.0) * 100))
        self.contrast_slider.setValue(int(clip.get('contrast', 1.0) * 100))
        self.sat_slider.setValue(int(clip.get('saturation', 1.0) * 100))
        self.gamma_slider.setValue(int(clip.get('gamma', 1.0) * 100))

        self.bright_lbl.setText(f"Brightness: {clip.get('brightness', 0.0):.1f}")
        self.contrast_lbl.setText(f"Contrast: {clip.get('contrast', 1.0):.1f}x")
        self.sat_lbl.setText(f"Saturation: {clip.get('saturation', 1.0):.1f}x")
        self.gamma_lbl.setText(f"Gamma: {clip.get('gamma', 1.0):.1f}x")

        self.bright_slider.blockSignals(False)
        self.contrast_slider.blockSignals(False)
        self.sat_slider.blockSignals(False)
        self.gamma_slider.blockSignals(False)

        # Load file into preview media player
        if clip.get('is_image', False):
            self.media_player.stop()
            self.time_label.setText("00:00:00 / 00:00:00")
            self.timeline_slider.setRange(0, 0)
            self.play_btn.setEnabled(False)
            self.rewind_btn.setEnabled(False)
            self.forward_btn.setEnabled(False)
            self.set_in_btn.setEnabled(False)
            self.set_out_btn.setEnabled(False)
        else:
            self.play_btn.setEnabled(True)
            self.rewind_btn.setEnabled(True)
            self.forward_btn.setEnabled(True)
            self.set_in_btn.setEnabled(True)
            self.set_out_btn.setEnabled(True)
            self.load_video(clip['file'])

    def on_clip_crop_changed(self):
        if self.current_row < 0 or self.current_row >= len(self.clips):
            return
        txt = self.clip_crop_combo.currentText()
        if txt == "No Crop":
            aspect = "None"
        elif "1:1" in txt:
            aspect = "1:1"
        elif "9:16" in txt:
            aspect = "9:16"
        elif "16:9" in txt:
            aspect = "16:9"
        else:
            aspect = "None"
            
        self.clips[self.current_row]['crop_aspect'] = aspect
        self.update_visualizer()

    def on_color_slider_changed(self):
        if self.current_row < 0 or self.current_row >= len(self.clips):
            return
        b_val = self.bright_slider.value() / 100.0
        c_val = self.contrast_slider.value() / 100.0
        s_val = self.sat_slider.value() / 100.0
        g_val = self.gamma_slider.value() / 100.0

        clip = self.clips[self.current_row]
        clip['brightness'] = b_val
        clip['contrast'] = c_val
        clip['saturation'] = s_val
        clip['gamma'] = g_val

        self.bright_lbl.setText(f"Brightness: {b_val:.1f}")
        self.contrast_lbl.setText(f"Contrast: {c_val:.1f}x")
        self.sat_lbl.setText(f"Saturation: {s_val:.1f}x")
        self.gamma_lbl.setText(f"Gamma: {g_val:.1f}x")

    def populate_table(self):
        self.table.setRowCount(len(self.clips))
        
        for idx, clip in enumerate(self.clips):
            is_image = clip.get('is_image', False)

            # Column 0: Reorder Buttons
            reorder_widget = QWidget()
            reorder_layout = QHBoxLayout(reorder_widget)
            reorder_layout.setContentsMargins(0, 0, 0, 0)
            reorder_layout.setSpacing(4)
            reorder_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

            up_btn = QPushButton("▲")
            up_btn.setFixedSize(22, 22)
            up_btn.setCursor(Qt.CursorShape.PointingHandCursor)
            up_btn.setStyleSheet("""
                QPushButton { background-color: #222; border: 1px solid #333; border-radius: 3px; color: #aaa; font-size: 10px; }
                QPushButton:hover { background-color: #333; color: white; }
                QPushButton:disabled { background-color: transparent; border: none; color: #333; }
            """)
            up_btn.setEnabled(idx > 0)
            up_btn.clicked.connect(lambda checked, i=idx: self.move_clip(i, -1))
            
            down_btn = QPushButton("▼")
            down_btn.setFixedSize(22, 22)
            down_btn.setCursor(Qt.CursorShape.PointingHandCursor)
            down_btn.setStyleSheet("""
                QPushButton { background-color: #222; border: 1px solid #333; border-radius: 3px; color: #aaa; font-size: 10px; }
                QPushButton:hover { background-color: #333; color: white; }
                QPushButton:disabled { background-color: transparent; border: none; color: #333; }
            """)
            down_btn.setEnabled(idx < len(self.clips) - 1)
            down_btn.clicked.connect(lambda checked, i=idx: self.move_clip(i, 1))

            reorder_layout.addWidget(up_btn)
            reorder_layout.addWidget(down_btn)
            self.table.setCellWidget(idx, 0, reorder_widget)

            # Column 1: File Name
            label = QLabel(f"🖼️ {clip['name']}" if is_image else f"🎬 {clip['name']}")
            label.setToolTip(clip['file'])
            label.setAlignment(Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft)
            label.setStyleSheet("padding-left: 8px; color: #fff;")
            self.table.setCellWidget(idx, 1, label)

            # Column 2: Trim In
            if is_image:
                lbl_na = QLabel("-")
                lbl_na.setAlignment(Qt.AlignmentFlag.AlignCenter)
                lbl_na.setStyleSheet("color: #666;")
                self.table.setCellWidget(idx, 2, lbl_na)
            else:
                start_edit = QLineEdit(clip['start'])
                start_edit.setFixedWidth(80)
                start_edit.setAlignment(Qt.AlignmentFlag.AlignCenter)
                start_edit.setStyleSheet("""
                    QLineEdit { background-color: #1a1a1a; border: 1px solid #333; border-radius: 4px; color: white; font-family: 'Consolas', monospace; font-size: 12px; padding: 4px; }
                    QLineEdit:focus { border-color: #2D72D9; }
                """)
                start_edit.editingFinished.connect(lambda i=idx, edit=start_edit: self.on_trim_start_changed(i, edit))
                self.table.setCellWidget(idx, 2, start_edit)

            # Column 3: Trim Out / Dur (s)
            if is_image:
                dur_edit = QLineEdit(f"{clip['duration']:.2f}")
                dur_edit.setFixedWidth(80)
                dur_edit.setAlignment(Qt.AlignmentFlag.AlignCenter)
                dur_edit.setStyleSheet("""
                    QLineEdit { background-color: #1a1a1a; border: 1px solid #3a2211; border-radius: 4px; color: #ff9944; font-family: 'Consolas', monospace; font-size: 12px; font-weight: bold; padding: 4px; }
                    QLineEdit:focus { border-color: #ff9944; }
                """)
                dur_edit.editingFinished.connect(lambda i=idx, edit=dur_edit: self.on_image_duration_changed(i, edit))
                self.table.setCellWidget(idx, 3, dur_edit)
            else:
                end_edit = QLineEdit(clip['end'])
                end_edit.setFixedWidth(80)
                end_edit.setAlignment(Qt.AlignmentFlag.AlignCenter)
                end_edit.setStyleSheet("""
                    QLineEdit { background-color: #1a1a1a; border: 1px solid #333; border-radius: 4px; color: white; font-family: 'Consolas', monospace; font-size: 12px; padding: 4px; }
                    QLineEdit:focus { border-color: #2D72D9; }
                """)
                end_edit.editingFinished.connect(lambda i=idx, edit=end_edit: self.on_trim_end_changed(i, edit))
                self.table.setCellWidget(idx, 3, end_edit)

            # Column 4: Speed Combobox
            if is_image:
                lbl_na = QLabel("-")
                lbl_na.setAlignment(Qt.AlignmentFlag.AlignCenter)
                lbl_na.setStyleSheet("color: #666;")
                self.table.setCellWidget(idx, 4, lbl_na)
            else:
                speed_combo = QComboBox()
                speed_combo.addItems(["0.25x", "0.5x", "1.0x", "1.5x", "2.0x", "4.0x"])
                speed_combo.setCurrentText(f"{clip['speed']}x")
                speed_combo.setFixedWidth(70)
                speed_combo.setStyleSheet("""
                    QComboBox { background-color: #1a1a1a; border: 1px solid #333; border-radius: 4px; color: white; padding: 4px; font-size: 12px; }
                    QComboBox::drop-down { border: none; }
                """)
                speed_combo.currentIndexChanged.connect(lambda state, i=idx, combo=speed_combo: self.on_speed_changed(i, combo))
                self.table.setCellWidget(idx, 4, speed_combo)

            # Column 5: Volume Combobox
            vol_combo = QComboBox()
            vol_combo.addItems(["Mute", "25%", "50%", "100%", "150%", "200%"])
            
            v_val = clip.get('volume', 1.0)
            if v_val == 0.0:
                vol_combo.setCurrentText("Mute")
            else:
                vol_combo.setCurrentText(f"{int(v_val * 100)}%")

            vol_combo.setFixedWidth(70)
            border_col = "#3a1a1a" if v_val == 0.0 else "#333"
            vol_combo.setStyleSheet(f"""
                QComboBox {{ background-color: #1a1a1a; border: 1px solid {border_col}; border-radius: 4px; color: white; padding: 4px; font-size: 12px; }}
                QComboBox::drop-down {{ border: none; }}
            """)
            vol_combo.currentIndexChanged.connect(lambda state, i=idx, combo=vol_combo: self.on_volume_changed(i, combo))
            
            if is_image:
                vol_combo.setCurrentText("Mute")
                vol_combo.setEnabled(False)
                
            self.table.setCellWidget(idx, 5, vol_combo)

            # Column 6: Actions
            del_btn = QPushButton("🗑️ Delete")
            del_btn.setCursor(Qt.CursorShape.PointingHandCursor)
            del_btn.setStyleSheet("""
                QPushButton { background-color: #1e1e1e; border: 1px solid #3a1a1a; border-radius: 4px; color: #ff3333; font-size: 12px; font-weight: bold; padding: 4px 8px; }
                QPushButton:hover { background-color: #3a1a1a; border-color: #ff3333; }
            """)
            del_btn.clicked.connect(lambda checked, i=idx: self.delete_clip(i))
            self.table.setCellWidget(idx, 6, del_btn)

    def move_clip(self, row, direction):
        target = row + direction
        if 0 <= target < len(self.clips):
            self.clips[row], self.clips[target] = self.clips[target], self.clips[row]
            self.populate_table()
            self.update_visualizer()
            self.select_clip_row(target)

    def delete_clip(self, row):
        if 0 <= row < len(self.clips):
            self.clips.pop(row)
            if self.current_row == row:
                self.media_player.stop()
                self.select_clip_row(-1)
            elif self.current_row > row:
                self.select_clip_row(self.current_row - 1)
            self.populate_table()
            self.update_visualizer()

    def on_image_duration_changed(self, row, line_edit):
        try:
            val = float(line_edit.text().strip())
            if val < 0.1:
                val = 0.1
            self.clips[row]['duration'] = val
        except ValueError:
            val = 3.0
            self.clips[row]['duration'] = val

        line_edit.setText(f"{val:.2f}")
        self.update_visualizer()

    def on_trim_start_changed(self, row, line_edit):
        txt = line_edit.text().strip()
        secs = timecode_to_seconds(txt)
        secs = max(0.0, min(secs, self.clips[row]['orig_duration']))
        
        end_secs = timecode_to_seconds(self.clips[row]['end'])
        if secs > end_secs:
            secs = end_secs
            
        self.clips[row]['start'] = seconds_to_timecode(secs)
        self.clips[row]['duration'] = end_secs - secs
        
        line_edit.setText(self.clips[row]['start'])
        self.update_visualizer()

    def on_trim_end_changed(self, row, line_edit):
        txt = line_edit.text().strip()
        secs = timecode_to_seconds(txt)
        
        start_secs = timecode_to_seconds(self.clips[row]['start'])
        secs = max(start_secs, min(secs, self.clips[row]['orig_duration']))
        
        self.clips[row]['end'] = seconds_to_timecode(secs)
        self.clips[row]['duration'] = secs - start_secs
        
        line_edit.setText(self.clips[row]['end'])
        self.update_visualizer()

    def on_speed_changed(self, row, combobox):
        speed_val = float(combobox.currentText().replace("x", ""))
        self.clips[row]['speed'] = speed_val
        self.update_visualizer()

    def on_volume_changed(self, row, combobox):
        text = combobox.currentText()
        if text == "Mute":
            vol_val = 0.0
        else:
            vol_val = float(text.replace("%", "")) / 100.0
            
        self.clips[row]['volume'] = vol_val
        
        border_col = "#3a1a1a" if vol_val == 0.0 else "#333"
        combobox.setStyleSheet(f"""
            QComboBox {{ background-color: #1a1a1a; border: 1px solid {border_col}; border-radius: 4px; color: white; padding: 4px; font-size: 12px; }}
            QComboBox::drop-down {{ border: none; }}
        """)
        self.update_visualizer()

    # --- PREVIEW PLAYER LOGIC ---
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

    def set_player_trim_in(self):
        if self.current_row < 0 or self.current_row >= len(self.clips):
            return
        pos = self.media_player.position()
        timecode = self.format_time(pos)
        self.clips[self.current_row]['start'] = timecode
        
        end_secs = timecode_to_seconds(self.clips[self.current_row]['end'])
        start_secs = timecode_to_seconds(timecode)
        if start_secs > end_secs:
            end_secs = start_secs
            self.clips[self.current_row]['end'] = timecode
            
        self.clips[self.current_row]['duration'] = end_secs - start_secs
        self.populate_table()
        self.update_visualizer()
        self.orchestrator.show_status_message(f"Trim In set to {timecode}")

    def set_player_trim_out(self):
        if self.current_row < 0 or self.current_row >= len(self.clips):
            return
        pos = self.media_player.position()
        timecode = self.format_time(pos)
        self.clips[self.current_row]['end'] = timecode
        
        start_secs = timecode_to_seconds(self.clips[self.current_row]['start'])
        end_secs = timecode_to_seconds(timecode)
        if end_secs < start_secs:
            start_secs = end_secs
            self.clips[self.current_row]['start'] = timecode

        self.clips[self.current_row]['duration'] = end_secs - start_secs
        self.populate_table()
        self.update_visualizer()
        self.orchestrator.show_status_message(f"Trim Out set to {timecode}")

    # --- IN-WORKSPACE PROGRESS UPDATES ---
    def on_job_progress(self, worker, pct, txt):
        if worker == self.active_render_worker:
            self.progress_frame.show()
            self.progress_bar.setValue(pct)
            self.progress_label.setText(txt)

    def on_job_finished(self, worker, success, msg):
        if worker == self.active_render_worker:
            self.progress_frame.hide()
            self.exec_btn.setEnabled(True)
            self.active_render_worker = None
            if success:
                self.orchestrator.show_status_message("🎉 Timeline render completed successfully!")
            else:
                self.orchestrator.show_status_message(f"❌ Render failed: {msg}")

    def abort_render(self):
        if self.active_render_worker:
            for idx, job in enumerate(self.orchestrator.job_queue):
                if job.get('worker') == self.active_render_worker:
                    self.orchestrator.cancel_or_remove_job(idx)
                    break
            self.progress_frame.hide()
            self.exec_btn.setEnabled(True)
            self.active_render_worker = None
            self.orchestrator.show_status_message("🔴 Render aborted by user.")

    def trigger_render(self, inputs, est_seconds):
        import sys
        if not self.clips:
            self.orchestrator.show_status_message("❌ Error: No media clips loaded!")
            return

        start_dir = getattr(sys, '_onyx_last_dir', os.path.expanduser("~"))
        save_file, _ = QFileDialog.getSaveFileName(
            self, "Save Timeline Composition Video", start_dir, 
            "MPEG-4 Video (*.mp4)"
        )
        if not save_file:
            return
        
        sys._onyx_last_dir = os.path.dirname(save_file)

        width = self.width_input.value()
        height = self.height_input.value()
        resize_mode = 'fit' if "Fit" in self.scale_combo.currentText() else 'fill'
        
        idx = self.mix_combo.currentIndex()
        if idx == 0:
            audio_mix_mode = 'mix'
        else:
            audio_mix_mode = 'keep_only'
            
        # Snapshot overlays data
        overlays_data = []
        for aud in self.audio_overlays:
            overlays_data.append({
                'file': aud['file'],
                'offset': aud['offset'],
                'volume': aud['volume']
            })

        # Snapshot clips data
        clips_data = []
        for c in self.clips:
            is_image = c.get('is_image', False)
            clips_data.append({
                'file': c['file'],
                'is_image': is_image,
                'start': c.get('start', '00:00:00.000'),
                'end': c.get('end', '00:00:00.000'),
                'duration': c['duration'],
                'speed': c.get('speed', 1.0),
                'volume': c.get('volume', 0.0 if is_image else 1.0),
                'crop_aspect': c.get('crop_aspect', 'None'),
                'brightness': c.get('brightness', 0.0),
                'contrast': c.get('contrast', 1.0),
                'saturation': c.get('saturation', 1.0),
                'gamma': c.get('gamma', 1.0)
            })

        def render_job():
            composer = TimelineComposer()
            success = composer.compile_timeline(
                master_audio="",
                clips=clips_data,
                canvas_width=width,
                canvas_height=height,
                resize_mode=resize_mode,
                audio_mix_mode=audio_mix_mode,
                master_volume=1.0,
                output_path=save_file,
                audio_overlays=overlays_data
            )
            return success, f"Timeline compiled successfully. Saved to: {save_file}" if success else "Timeline compilation failed."

        # Disable render button and display progress block
        self.exec_btn.setEnabled(False)
        self.progress_frame.show()
        self.progress_bar.setValue(0)
        self.progress_label.setText("Starting compiler engine...")

        self.orchestrator.add_background_job("Timeline Render", render_job, estimated_seconds=est_seconds)
        
        # Link render worker
        job = self.orchestrator.job_queue[-1]
        self.active_render_worker = job.get('worker')


# ==========================================
# HOW TO USE THIS CODE (EXAMPLE)
# ==========================================
# Example usage:
# from src.processors.timeline_ui import MainClass
# processor = MainClass()
# processor.run(input_file, output_file)
# ==========================================

# ==============================================================================
# 🎬 FEATURE: INTERNAL MODULE DOCUMENTATION (timeline_ui.py)
# ==============================================================================
#
# 📝 WHAT IS THIS FILE?
#    This file, 'timeline_ui.py', is a core component of the Onyx Engine. It is
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
