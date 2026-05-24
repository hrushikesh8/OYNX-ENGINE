import os
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
                             QLabel, QFrame, QListWidgetItem)
from PyQt6.QtCore import Qt
from src.ui.suture_ui import DragDropList  # Reusing your professional list logic
from src.processors.stitcher import VideoStitcher

class VideoStitcherUI(QWidget):
    """
    UI for Feature 6: Video Stitcher.
    Allows users to drag, drop, and re-order clips for instant concatenation.
    """
    def __init__(self, back_callback):
        super().__init__()
        self.stitcher_engine = VideoStitcher()
        
        # Main Layout
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        layout.setContentsMargins(30, 30, 30, 30)

        # --- 1. HEADER SECTION ---
        header = QHBoxLayout()
        
        self.back_btn = QPushButton(" ←  Back")
        self.back_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.back_btn.setStyleSheet("""
            QPushButton { background-color: #252525; border: 1px solid #333; border-radius: 6px; 
                          color: #bbb; padding: 8px 15px; font-weight: bold; }
            QPushButton:hover { background-color: #333; color: white; }
        """)
        self.back_btn.clicked.connect(back_callback)
        
        title = QLabel("🎬 Video Stitcher (Concat)")
        title.setStyleSheet("font-size: 24px; font-weight: bold; color: white;")
        
        header.addWidget(self.back_btn)
        header.addSpacing(20)
        header.addWidget(title)
        header.addStretch()
        layout.addLayout(header)
        
        layout.addSpacing(10)
        subtitle = QLabel("Instantly join multiple clips into one file without quality loss.")
        subtitle.setStyleSheet("color: #777; font-size: 14px;")
        layout.addWidget(subtitle)

        # --- 2. THE TIMELINE (DRAG & DROP LIST) ---
        layout.addSpacing(25)
        layout.addWidget(QLabel("<b>TIMELINE:</b> Drag clips to change their order in the final video"))
        
        self.file_list = DragDropList()
        self.file_list.setMinimumHeight(400)
        # Adding a tool tip for better UX
        self.file_list.setToolTip("Drop video files here and drag them up/down to re-order.")
        layout.addWidget(self.file_list)

        # --- 3. LIST CONTROLS ---
        controls = QHBoxLayout()
        
        self.remove_btn = QPushButton("❌ Remove Selected")
        self.remove_btn.clicked.connect(self.remove_item)
        
        self.clear_btn = QPushButton("🗑️ Clear Timeline")
        self.clear_btn.clicked.connect(self.file_list.clear)

        for btn in [self.remove_btn, self.clear_btn]:
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.setStyleSheet("""
                QPushButton { background-color: #1e1e1e; border: 1px solid #333; border-radius: 4px; 
                              padding: 6px 12px; color: #888; font-weight: bold; }
                QPushButton:hover { background-color: #252525; color: #eee; border: 1px solid #444; }
            """)
        
        controls.addWidget(self.remove_btn)
        controls.addWidget(self.clear_btn)
        controls.addStretch()
        layout.addLayout(controls)

        # --- 4. EXECUTION AREA ---
        layout.addStretch()
        
        info_frame = QFrame()
        info_frame.setStyleSheet("background-color: #1a1a1a; border: 1px solid #282828; border-radius: 8px; padding: 10px;")
        info_layout = QHBoxLayout(info_frame)
        info_icon = QLabel("ℹ️")
        info_text = QLabel("All clips must have the same resolution and codec for a successful stitch.")
        info_text.setStyleSheet("color: #aaa; font-size: 12px;")
        info_layout.addWidget(info_icon)
        info_layout.addWidget(info_text)
        info_layout.addStretch()
        layout.addWidget(info_frame)
        
        layout.addSpacing(15)

        self.exec_btn = QPushButton("⚡ Execute Stitching")
        self.exec_btn.setMinimumHeight(65)
        self.exec_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.exec_btn.setStyleSheet("""
            QPushButton { 
                font-size: 18px; font-weight: bold; background-color: #2D72D9; 
                color: white; border-radius: 12px; 
            }
            QPushButton:hover { background-color: #3a82ef; }
            QPushButton:disabled { background-color: #1a3a63; color: #555; }
        """)
        self.exec_btn.clicked.connect(self.start_stitching)
        layout.addWidget(self.exec_btn)

    def remove_item(self):
        """Removes the highlighted item from the list."""
        for item in self.file_list.selectedItems():
            self.file_list.takeItem(self.file_list.row(item))

    def start_stitching(self):
        """Prepares the file list and triggers the backend engine."""
        count = self.file_list.count()
        if count < 2:
            print("[UI Warning] At least 2 clips are required to stitch.")
            return
        
        # 1. Collect ordered paths
        video_paths = [self.file_list.item(i).text() for i in range(count)]
        
        # 2. Determine output path (Saves in the same folder as the first clip)
        base_dir = os.path.dirname(video_paths[0])
        output_file = os.path.join(base_dir, "Onyx_Stitch_Result.mp4")
        
        # 3. Update Button State
        self.exec_btn.setEnabled(False)
        self.exec_btn.setText("Stitching Files (Instant Copy)...")
        
        # 4. Call your original VideoStitcher Engine
        success = self.stitcher_engine.concat_videos(video_paths, output_file)
        
        # 5. UI Feedback
        self.exec_btn.setEnabled(True)
        self.exec_btn.setText("⚡ Execute Stitching")
        
        if success:
            print(f"[SUCCESS] Merged file created: {output_file}")
            # Optional: You could add a QMessagebox here to notify the user
        else:
            print("[ERROR] Stitching failed. Check logs for details.")