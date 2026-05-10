from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
                             QLabel, QCheckBox, QScrollArea, QFrame)
from PyQt6.QtCore import Qt
from src.ui.custom_widgets import DropZone
from src.processors.tracks import TrackProcessor # Import your class
import os

class TrackCleanerUI(QWidget):
    """The Visual Dashboard for Feature 2 (Audio) and Feature 3 (Subtitles)"""
    def __init__(self, back_callback, mode='a'):
        super().__init__()
        self.processor = TrackProcessor()
        self.mode = mode # 'a' for Audio, 's' for Subtitles
        
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        # --- HEADER ---
        header = QHBoxLayout()
        back_btn = QPushButton("⬅ Back to Dashboard")
        back_btn.clicked.connect(back_callback)
        header.addWidget(back_btn)
        
        label_text = "🎵 Audio Track Cleaner" if mode == 'a' else "📝 Subtitle Track Cleaner"
        title = QLabel(label_text)
        title.setStyleSheet("font-size: 22px; font-weight: bold;")
        header.addWidget(title)
        header.addStretch()
        layout.addLayout(header)

        # --- DROP ZONE ---
        self.drop_zone = DropZone(self)
        self.drop_zone.file_input.textChanged.connect(self.refresh_tracks)
        layout.addWidget(self.drop_zone)

        layout.addSpacing(15)
        layout.addWidget(QLabel("Step 2: Select the tracks you wish to PRESERVE:"))

        # --- DYNAMIC CHECKBOX LIST ---
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setStyleSheet("background-color: #1e1e1e; border-radius: 8px;")
        
        self.container = QWidget()
        self.track_layout = QVBoxLayout(self.container)
        self.scroll.setWidget(self.container)
        layout.addWidget(self.scroll)

        self.checkboxes = []

        # --- EXECUTION ---
        self.exec_btn = QPushButton("🚀 Purge Unselected Tracks")
        self.exec_btn.setMinimumHeight(60)
        self.exec_btn.setStyleSheet("background-color: #D92D2D; color: white; font-size: 16px; font-weight: bold; border-radius: 10px;")
        self.exec_btn.clicked.connect(self.run_purge)
        layout.addWidget(self.exec_btn)

    def refresh_tracks(self):
        """Called when a file is dropped. Uses your get_track_info logic."""
        path = self.drop_zone.file_input.text().strip()
        if not path or not os.path.exists(path): return

        # Clear existing list
        for cb in self.checkboxes:
            self.track_layout.removeWidget(cb)
            cb.deleteLater()
        self.checkboxes.clear()

        # Call YOUR original ffprobe logic
        raw_tracks = self.processor.get_track_info(path, self.mode)
        
        for i, t in enumerate(raw_tracks):
            lang = t.get('tags', {}).get('language', 'und')
            title = t.get('tags', {}).get('title', 'Track')
            idx = t.get('index')
            
            cb = QCheckBox(f"Index {idx} | Language: {lang} | Title: {title}")
            cb.setProperty("track_id", i) # We use the relative ID for FFmpeg mapping
            cb.setChecked(True)
            cb.setStyleSheet("font-size: 14px; padding: 5px;")
            self.track_layout.addWidget(cb)
            self.checkboxes.append(cb)

    def run_purge(self):
        input_path = self.drop_zone.file_input.text().strip()
        # Collect IDs from checked boxes
        keep_ids = [cb.property("track_id") for cb in self.checkboxes if cb.isChecked()]

        if not input_path or not keep_ids:
            return

        self.exec_btn.setText("Processing Batch...")
        self.exec_btn.setEnabled(False)

        # Call YOUR original process_batch logic
        self.processor.process_batch(input_path, keep_ids, self.mode)

        self.exec_btn.setText("🚀 Purge Unselected Tracks")
        self.exec_btn.setEnabled(True)