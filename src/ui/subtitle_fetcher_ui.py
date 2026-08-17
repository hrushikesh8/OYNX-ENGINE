import os
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
    QListWidget, QListWidgetItem, QFileDialog, QMessageBox,
    QProgressBar, QTabWidget, QLineEdit, QComboBox
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont
from src.processors.subtitle_processor import SubtitleProcessor, parse_title_year
from src.ui.custom_widgets import DropZone, SmartRunButton

class SubtitleFetcherUI(QWidget):
    def __init__(self, back_callback=None, orchestrator=None):
        super().__init__()
        self.processor = SubtitleProcessor()
        self.back_callback = back_callback
        self.orchestrator = orchestrator
        self.current_video_path = None
        self.current_subtitles = []
        self.selected_subtitle = None
        
        self.setup_ui()
        self.setup_connections()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        layout.setContentsMargins(30, 30, 30, 30)
        
        # Top Bar with Back Button
        top_layout = QHBoxLayout()
        if self.back_callback:
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
            top_layout.addWidget(back_btn)
            top_layout.addSpacing(15)
        
        title = QLabel("📝 Subtitle Studio")
        title.setStyleSheet("font-size: 22px; font-weight: bold; color: white;")
        top_layout.addWidget(title)
        top_layout.addStretch()
        layout.addLayout(top_layout)
        layout.addSpacing(15)
        
        self.tabs = QTabWidget()
        self.tabs.setStyleSheet("""
            QTabWidget::pane { border: 1px solid #282828; background: #121212; border-radius: 8px; }
            QTabBar::tab { background: #1a1a1a; padding: 10px 20px; font-weight: bold; border-top-left-radius: 6px; border-top-right-radius: 6px; margin-right: 5px; color: #888; }
            QTabBar::tab:selected { background: #2D72D9; color: white; }
            QTabBar::tab:hover { background: #252525; }
        """)
        layout.addWidget(self.tabs)
        
        self.setup_download_tab()
        self.setup_extract_tab()
        
    def setup_download_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Video Selection
        vid_layout = QHBoxLayout()
        self.vid_label = QLabel("No video selected.")
        vid_btn = QPushButton("Browse Video")
        vid_btn.clicked.connect(self.browse_video)
        vid_layout.addWidget(self.vid_label, stretch=1)
        vid_layout.addWidget(vid_btn)
        layout.addLayout(vid_layout)
        
        # Search Fields
        search_fields_layout = QHBoxLayout()
        
        v_title = QVBoxLayout()
        v_title.addWidget(QLabel("Movie Title:"))
        self.title_input = QLineEdit()
        self.title_input.setStyleSheet("background-color: #222; border: 1px solid #333; color: white; padding: 5px; border-radius: 4px;")
        v_title.addWidget(self.title_input)
        search_fields_layout.addLayout(v_title, stretch=3)
        
        v_year = QVBoxLayout()
        v_year.addWidget(QLabel("Year:"))
        self.year_input = QLineEdit()
        self.year_input.setStyleSheet("background-color: #222; border: 1px solid #333; color: white; padding: 5px; border-radius: 4px;")
        v_year.addWidget(self.year_input)
        search_fields_layout.addLayout(v_year, stretch=1)
        
        layout.addLayout(search_fields_layout)
        
        # Search Button
        self.search_btn = QPushButton("Search Subtitles")
        self.search_btn.setEnabled(False)
        self.search_btn.clicked.connect(self.search_subtitles)
        layout.addWidget(self.search_btn)
        
        # List of options
        self.subs_list = QListWidget()
        self.subs_list.itemSelectionChanged.connect(self.on_selection_changed)
        layout.addWidget(self.subs_list)
        
        # Progress Bar
        self.progress = QProgressBar()
        self.progress.setRange(0, 0)
        self.progress.hide()
        layout.addWidget(self.progress)
        
        # Status Label
        self.status_label = QLabel("")
        layout.addWidget(self.status_label)
        
        # Download & Merge Button
        self.merge_btn = QPushButton("Download & Merge Selected Subtitle")
        self.merge_btn.setEnabled(False)
        self.merge_btn.clicked.connect(self.download_and_merge)
        layout.addWidget(self.merge_btn)
        
        self.tabs.addTab(tab, "📥 Download Subtitles")

    def setup_extract_tab(self):
        tab = QWidget()
        t_layout = QVBoxLayout(tab)
        t_layout.setContentsMargins(20, 20, 20, 20)

        t_layout.addWidget(QLabel("Step 1: Select Video with Embedded Subtitles"))
        self.extract_drop = DropZone(self)
        t_layout.addWidget(self.extract_drop)
        t_layout.addSpacing(15)

        # Format and Track options
        opts_layout = QHBoxLayout()
        
        v_layout1 = QVBoxLayout()
        v_layout1.addWidget(QLabel("Output Format:"))
        self.extract_format_combo = QComboBox()
        self.extract_format_combo.addItems(["srt", "ass", "vtt"])
        self.extract_format_combo.setMinimumHeight(40)
        v_layout1.addWidget(self.extract_format_combo)
        opts_layout.addLayout(v_layout1)

        v_layout2 = QVBoxLayout()
        v_layout2.addWidget(QLabel("Subtitle Track ID (0 = First, 1 = Second, etc.):"))
        self.extract_track_id_input = QLineEdit("0")
        self.extract_track_id_input.setMinimumHeight(40)
        self.extract_track_id_input.setStyleSheet("background-color: #222; border: 1px solid #333; color: white; padding: 5px; border-radius: 4px;")
        v_layout2.addWidget(self.extract_track_id_input)
        opts_layout.addLayout(v_layout2)

        t_layout.addLayout(opts_layout)
        t_layout.addSpacing(25)

        self.exec_extract_btn = SmartRunButton("🚀 Extract Subtitle Stream", self.get_extract_input, self.run_extraction, speed_multiplier=20.0)
        t_layout.addWidget(self.exec_extract_btn)
        t_layout.addStretch()

        self.tabs.addTab(tab, "✂️ Extract Subtitles")

    def setup_connections(self):
        self.processor.signals.search_finished.connect(self.on_search_finished)
        self.processor.signals.download_finished.connect(self.on_download_finished)
        self.processor.signals.merge_finished.connect(self.on_merge_finished)
        self.processor.signals.extract_finished.connect(self.on_extract_finished)
        self.processor.signals.error.connect(self.on_error)
        
        # Enable search button based on inputs
        self.title_input.textChanged.connect(self.check_search_ready)

    def check_search_ready(self):
        self.search_btn.setEnabled(bool(self.title_input.text().strip()))

    def browse_video(self):
        file_name, _ = QFileDialog.getOpenFileName(
            self, "Select Video", "", "Video Files (*.mp4 *.mkv *.avi)"
        )
        if file_name:
            self.current_video_path = file_name
            self.vid_label.setText(os.path.basename(file_name))
            
            # Auto-populate title and year
            title, year = parse_title_year(file_name)
            self.title_input.setText(title)
            self.year_input.setText(year)
            
            self.search_btn.setEnabled(True)
            self.subs_list.clear()
            self.status_label.setText("Video loaded.")

    def search_subtitles(self):
        title = self.title_input.text().strip()
        year = self.year_input.text().strip()
        
        if not title:
            return
            
        self.subs_list.clear()
        self.current_subtitles.clear()
        self.search_btn.setEnabled(False)
        self.progress.show()
        self.status_label.setText("Searching...")
        self.processor.search_subtitles(title, year)

    def on_search_finished(self, subtitles):
        self.progress.hide()
        self.search_btn.setEnabled(True)
        self.current_subtitles = subtitles
        
        if not subtitles:
            self.status_label.setText("No subtitles found.")
            return
            
        self.status_label.setText(f"Found {len(subtitles)} subtitles.")
        
        for sub in subtitles:
            provider = sub.provider_name.capitalize()
            lang = sub.language.name
            downloads = sub.downloads
            trusted = "✅ Trusted Source" if sub.trusted else "⚠️ Unverified Source"
            
            display_text = f"[{provider}] {lang} - {trusted} | {downloads} Downloads"
            if hasattr(sub, 'filename') and sub.filename:
                display_text += f"\nFile: {sub.filename}"
                
            item = QListWidgetItem(display_text)
            item.setData(Qt.ItemDataRole.UserRole, sub)
            self.subs_list.addItem(item)

    def on_selection_changed(self):
        selected_items = self.subs_list.selectedItems()
        self.merge_btn.setEnabled(len(selected_items) > 0)

    def download_and_merge(self):
        selected_items = self.subs_list.selectedItems()
        if not selected_items:
            return
            
        self.selected_subtitle = selected_items[0].data(Qt.ItemDataRole.UserRole)
        self.merge_btn.setEnabled(False)
        self.subs_list.setEnabled(False)
        self.progress.show()
        self.status_label.setText("Downloading subtitle...")
        
        # We need video path to merge
        if not self.current_video_path:
            self.status_label.setText("Please select a video file first.")
            self.progress.hide()
            return
            
        self.processor.download_subtitle(self.selected_subtitle, self.current_video_path)

    def on_download_finished(self, srt_path):
        self.status_label.setText(f"Downloaded SRT. Merging...")
        
        base_dir, ext = os.path.splitext(self.current_video_path)
        output_path = f"{base_dir}_subbed{ext}"
        
        self.processor.merge_subtitle(self.current_video_path, srt_path, output_path)

    def on_merge_finished(self, output_path):
        self.progress.hide()
        self.subs_list.setEnabled(True)
        self.status_label.setText(f"Success! Saved to:\n{os.path.basename(output_path)}")
        QMessageBox.information(self, "Success", f"Video merged with subtitle successfully!\n\nSaved at: {output_path}")

    def on_extract_finished(self, output_path):
        if self.orchestrator:
            self.orchestrator.show_status_message(f"✅ Extraction Complete: {os.path.basename(output_path)}")

    def on_error(self, err_msg):
        self.progress.hide()
        self.search_btn.setEnabled(True)
        self.subs_list.setEnabled(True)
        self.status_label.setText("Error occurred.")
        QMessageBox.critical(self, "Error", err_msg)

    # Extraction Logic
    def get_extract_input(self):
        path = self.extract_drop.file_input.text().strip()
        return path if path else None

    def run_extraction(self, inputs, est_seconds):
        path = self.get_extract_input()
        fmt = self.extract_format_combo.currentText()
        try:
            track_id = int(self.extract_track_id_input.text().strip())
        except ValueError:
            track_id = 0

        if not path:
            return

        filename = os.path.basename(path)
        def task():
            try:
                base_dir, fname = os.path.split(path)
                name, _ = os.path.splitext(fname)
                suffix = f"_SubTrack{track_id}" if track_id > 0 else ""
                output_path = os.path.join(base_dir, f"{name}{suffix}.{fmt}")
                
                cmd = [
                    'ffmpeg', '-y', '-i', path,
                    '-map', f'0:s:{track_id}',
                    output_path
                ]
                import subprocess
                subprocess.run(cmd, check=True, capture_output=True)
                return True, f"Subtitle saved to: {output_path}"
            except subprocess.CalledProcessError as e:
                return False, f"FFmpeg Error: {e.stderr.decode('utf-8', errors='ignore')}"
            except Exception as e:
                return False, f"Error: {e}"

        if self.orchestrator:
            self.orchestrator.add_background_job(f"Subtitle Extract: {filename}", task, estimated_seconds=est_seconds, local_widget=self.exec_extract_btn)
            self.orchestrator.show_status_message(f"⏳ Extraction task queued for: {filename}")
