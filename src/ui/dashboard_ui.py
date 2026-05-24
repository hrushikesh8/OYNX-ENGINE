import os
import json
import sys
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
                             QLabel, QFrame, QLineEdit, QGridLayout, QTableWidget, 
                             QTableWidgetItem, QProgressBar, QTextEdit, QFileDialog, QHeaderView)
from PyQt6.QtCore import Qt, QTimer
from src.ui.custom_widgets import DropZone
from src.processors.metadata_editor import MetadataEditor

# Try importing psutil for real stats, otherwise mock it
try:
    import psutil
except ImportError:
    psutil = None

class DashboardUI(QWidget):
    """
    Landing Workspace of Onyx Engine.
    Exposes Live Stats, Preferences (Binary Paths), Active Render Queue, and a Metadata Editor.
    """
    def __init__(self, orchestrator):
        super().__init__()
        self.orchestrator = orchestrator # Reference to MasterOrchestrator
        self.meta_editor = MetadataEditor()
        self.settings_file = "onyx_settings.json"
        self.load_settings()

        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        layout.setContentsMargins(30, 30, 30, 30)

        # --- 1. SYSTEM STATS BAR ---
        stats_frame = QFrame()
        stats_frame.setStyleSheet("background-color: #1a1a1a; border: 1px solid #282828; border-radius: 10px; padding: 15px;")
        stats_layout = QHBoxLayout(stats_frame)
        
        self.cpu_label = QLabel("💻 CPU: --%")
        self.cpu_progress = QProgressBar()
        self.cpu_progress.setMaximumWidth(150)
        self.cpu_progress.setStyleSheet("QProgressBar { border: 1px solid #444; background: #111; border-radius: 4px; text-align: center; } QProgressBar::chunk { background: #2D72D9; }")
        
        self.ram_label = QLabel("🧠 RAM: --%")
        self.ram_progress = QProgressBar()
        self.ram_progress.setMaximumWidth(150)
        self.ram_progress.setStyleSheet("QProgressBar { border: 1px solid #444; background: #111; border-radius: 4px; text-align: center; } QProgressBar::chunk { background: #00ff66; }")
        
        self.ffmpeg_status = QLabel("🎬 FFmpeg: checking...")
        self.ffmpeg_status.setStyleSheet("font-weight: bold;")

        stats_layout.addWidget(self.cpu_label)
        stats_layout.addWidget(self.cpu_progress)
        stats_layout.addSpacing(30)
        stats_layout.addWidget(self.ram_label)
        stats_layout.addWidget(self.ram_progress)
        stats_layout.addStretch()
        stats_layout.addWidget(self.ffmpeg_status)
        
        layout.addWidget(stats_frame)
        layout.addSpacing(20)

        # --- 2. DOUBLE DECKER CONTENT (GRID) ---
        grid = QGridLayout()
        grid.setSpacing(20)

        # Left Column: Render Queue & Jobs list
        queue_box = QFrame()
        queue_box.setStyleSheet("background-color: #1a1a1a; border: 1px solid #282828; border-radius: 10px; padding: 20px;")
        qb_layout = QVBoxLayout(queue_box)
        qb_layout.addWidget(QLabel("<b>🎬 Active Render Queue / Task Monitor</b>"))
        
        self.job_table = QTableWidget(0, 3)
        self.job_table.setHorizontalHeaderLabels(["Task Name", "Progress / Status", "Actions"])
        self.job_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.job_table.setStyleSheet("""
            QTableWidget { background-color: #121212; border: 1px solid #333; gridline-color: #252525; color: #eee; }
            QHeaderView::section { background-color: #222; padding: 5px; color: #eee; border: 1px solid #333; }
        """)
        qb_layout.addWidget(self.job_table)

        # Unified Terminal Logger at bottom of Render Queue
        qb_layout.addWidget(QLabel("<b>📟 Real-Time Output Console</b>"))
        self.log_console = QTextEdit()
        self.log_console.setReadOnly(True)
        self.log_console.setMinimumHeight(150)
        self.log_console.setStyleSheet("""
            QTextEdit {
                background-color: #0b0b0b;
                color: #00ff66;
                font-family: Consolas, Monaco, monospace;
                font-size: 12px;
                border: 1px solid #333;
                border-radius: 6px;
                padding: 8px;
            }
        """)
        qb_layout.addWidget(self.log_console)
        grid.addWidget(queue_box, 0, 0, 2, 1)

        # Right Column top: Preferences & Binary Paths
        pref_box = QFrame()
        pref_box.setStyleSheet("background-color: #1a1a1a; border: 1px solid #282828; border-radius: 10px; padding: 20px;")
        pb_layout = QVBoxLayout(pref_box)
        pb_layout.addWidget(QLabel("<b>⚙️ Engine Paths & Preferences</b>"))
        
        self.path_inputs = {}
        for key, name in [("ffmpeg", "FFmpeg Binary"), ("seven_zip", "7-Zip (7za.exe)"), ("realesrgan", "Real-ESRGAN Binary"), ("rife", "RIFE Motion Binary")]:
            row = QHBoxLayout()
            row.addWidget(QLabel(f"{name}:"))
            input_field = QLineEdit(self.settings.get(key, ""))
            input_field.setStyleSheet("background-color: #222; border: 1px solid #333; color: white; padding: 5px; border-radius: 4px;")
            self.path_inputs[key] = input_field
            
            btn = QPushButton("📁")
            btn.setFixedWidth(35)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.setStyleSheet("background-color: #333; padding: 5px; border-radius: 4px;")
            # Connect browse action
            btn.clicked.connect(lambda checked, k=key: self.browse_pref(k))
            
            row.addWidget(input_field)
            row.addWidget(btn)
            pb_layout.addLayout(row)
        
        save_pref_btn = QPushButton("💾 Save Preferences")
        save_pref_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        save_pref_btn.setStyleSheet("background-color: #2D72D9; color: white; padding: 10px; font-weight: bold; border-radius: 5px;")
        save_pref_btn.clicked.connect(self.save_settings)
        pb_layout.addWidget(save_pref_btn)
        grid.addWidget(pref_box, 0, 1)

        # Right Column bottom: Metadata Editor
        meta_box = QFrame()
        meta_box.setStyleSheet("background-color: #1a1a1a; border: 1px solid #282828; border-radius: 10px; padding: 20px;")
        mb_layout = QVBoxLayout(meta_box)
        mb_layout.addWidget(QLabel("<b>🏷️ Lossless Metadata Editor</b>"))
        
        self.meta_drop = DropZone(self)
        self.meta_drop.file_input.textChanged.connect(self.load_metadata)
        mb_layout.addWidget(self.meta_drop)

        meta_grid = QGridLayout()
        self.meta_fields = {}
        for i, (key, label_name) in enumerate([("title", "Title"), ("artist", "Artist"), ("date", "Year"), ("genre", "Genre")]):
            meta_grid.addWidget(QLabel(f"{label_name}:"), i, 0)
            field = QLineEdit()
            field.setStyleSheet("background-color: #222; border: 1px solid #333; color: white; padding: 5px; border-radius: 4px;")
            meta_grid.addWidget(field, i, 1)
            self.meta_fields[key] = field
            
        mb_layout.addLayout(meta_grid)
        
        self.write_meta_btn = QPushButton("🏷️ Apply Metadata Tags")
        self.write_meta_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.write_meta_btn.setStyleSheet("background-color: #00ff66; color: #111; font-weight: bold; padding: 10px; border-radius: 5px;")
        self.write_meta_btn.clicked.connect(self.apply_metadata)
        mb_layout.addWidget(self.write_meta_btn)
        grid.addWidget(meta_box, 1, 1)

        layout.addLayout(grid)

        # --- 3. TIMERS FOR STATS & QUEUE REFRESH ---
        self.stats_timer = QTimer()
        self.stats_timer.timeout.connect(self.update_stats)
        self.stats_timer.start(2000) # Update stats every 2s

        self.queue_timer = QTimer()
        self.queue_timer.timeout.connect(self.refresh_queue)
        self.queue_timer.start(1000) # Update render queue table every 1s

    # --- PREFERENCES LOGIC ---
    def load_settings(self):
        default_settings = {
            "ffmpeg": "ffmpeg",
            "ffprobe": "ffprobe",
            "seven_zip": os.path.abspath(os.path.join("src", "tools", "7za.exe")),
            "realesrgan": os.path.abspath(os.path.join("bin", "realesrgan-ncnn-vulkan.exe")),
            "rife": os.path.abspath(os.path.join("bin", "rife-ncnn-vulkan.exe"))
        }
        if os.path.exists(self.settings_file):
            try:
                with open(self.settings_file, "r") as f:
                    self.settings = json.load(f)
            except Exception:
                self.settings = default_settings
        else:
            self.settings = default_settings
            self.save_settings()

    def save_settings(self):
        if hasattr(self, 'path_inputs'):
            for key in self.path_inputs:
                self.settings[key] = self.path_inputs[key].text().strip()
                
        try:
            with open(self.settings_file, "w") as f:
                json.dump(self.settings, f, indent=4)
            self.log_console.append("🎉 Preferences saved successfully.")
        except Exception as e:
            self.log_console.append(f"❌ Error saving preferences: {str(e)}")
            
        self.check_ffmpeg()

    def browse_pref(self, key):
        file_name, _ = QFileDialog.getOpenFileName(self, f"Select binary for {key}", "", "Executable Files (*.exe);;All Files (*)")
        if file_name:
            self.path_inputs[key].setText(file_name)

    def check_ffmpeg(self):
        import shutil
        ffmpeg_bin = self.settings.get("ffmpeg", "ffmpeg")
        if shutil.which(ffmpeg_bin) or os.path.exists(ffmpeg_bin):
            self.ffmpeg_status.setText("🎬 FFmpeg: ONLINE")
            self.ffmpeg_status.setStyleSheet("color: #00ff66; font-weight: bold;")
        else:
            self.ffmpeg_status.setText("🎬 FFmpeg: OFFLINE (Check path!)")
            self.ffmpeg_status.setStyleSheet("color: #ff3333; font-weight: bold;")

    # --- METADATA EDITOR LOGIC ---
    def load_metadata(self):
        path = self.meta_drop.file_input.text().strip()
        if not path or not os.path.exists(path):
            return
        
        tags = self.meta_editor.read_metadata(path)
        for key in self.meta_fields:
            self.meta_fields[key].setText(tags.get(key, ""))
            
        self.log_console.append(f"📁 Loaded metadata from: {os.path.basename(path)}")

    def apply_metadata(self):
        path = self.meta_drop.file_input.text().strip()
        if not path or not os.path.exists(path):
            self.log_console.append("❌ Error: Select a video file first.")
            return
            
        # Collect field updates
        tags = {}
        for key, field in self.meta_fields.items():
            if field.text().strip():
                tags[key] = field.text().strip()

        # Build output path
        base_dir = os.path.dirname(path)
        filename = os.path.basename(path)
        name, ext = os.path.splitext(filename)
        output_path = os.path.join(base_dir, f"{name}_tagged{ext}")

        # Run command asynchronously using orchestrator job queue
        cmd_list = self.meta_editor.write_metadata(path, output_path, tags)
        self.orchestrator.add_background_job(f"Tag Metadata: {name}", cmd_list)
        self.log_console.append(f"⏳ Queueing metadata updates for: {filename}")

    # --- LIVE RENDER QUEUE TABLE ---
    def refresh_queue(self):
        jobs = self.orchestrator.job_queue
        self.job_table.setRowCount(len(jobs))
        
        for idx, job in enumerate(jobs):
            name_item = QTableWidgetItem(job.get("name", "Unknown Job"))
            name_item.setFlags(name_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.job_table.setItem(idx, 0, name_item)
            
            # Status display
            status = job.get("status", "Queued")
            status_item = QTableWidgetItem(status)
            status_item.setFlags(status_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            if status == "Running":
                status_item.setStyleSheet("color: #00ff66; font-weight: bold;")
            elif status == "Completed":
                status_item.setStyleSheet("color: #aaa;")
            elif status == "Failed":
                status_item.setStyleSheet("color: #ff3333; font-weight: bold;")
            self.job_table.setItem(idx, 1, status_item)
            
            # Cancel/Remove action button
            act_btn = QPushButton("Cancel" if status == "Running" else "Remove")
            act_btn.setStyleSheet("background-color: #442222; color: #ff8888;" if status == "Running" else "background-color: #222; color: #888;")
            act_btn.setCursor(Qt.CursorShape.PointingHandCursor)
            act_btn.clicked.connect(lambda checked, index=idx: self.cancel_or_remove_job(index))
            
            self.job_table.setCellWidget(idx, 2, act_btn)

    def cancel_or_remove_job(self, idx):
        self.orchestrator.cancel_or_remove_job(idx)
        self.refresh_queue()

    # --- SYSTEM STATISTICS ---
    def update_stats(self):
        if psutil:
            try:
                cpu = psutil.cpu_percent()
                ram = psutil.virtual_memory().percent
                self.cpu_label.setText(f"💻 CPU: {cpu}%")
                self.cpu_progress.setValue(int(cpu))
                self.ram_label.setText(f"🧠 RAM: {ram}%")
                self.ram_progress.setValue(int(ram))
            except Exception:
                pass
        else:
            # Fallback mock values to prevent crashes
            import random
            cpu = random.randint(5, 15)
            ram = 42
            self.cpu_label.setText(f"💻 CPU: {cpu}% (psutil missing)")
            self.cpu_progress.setValue(cpu)
            self.ram_label.setText(f"🧠 RAM: {ram}%")
            self.ram_progress.setValue(ram)

    def append_log(self, text):
        self.log_console.append_log(text)
