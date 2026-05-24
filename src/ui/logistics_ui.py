import os
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
                             QLabel, QFrame, QLineEdit, QComboBox, QCheckBox, QTabWidget)
from PyQt6.QtCore import Qt, QThread
from src.ui.custom_widgets import DropZone
from src.processors.archiver import FolderArchiver
from src.processors.unarchiver import EnterpriseUnarchiver
from src.processors.compressor import VideoCompressor
import time

class WatcherThread(QThread):
    """Background thread to monitor directories and auto-compress new media files."""
    log_signal = QThread.pyqtSignal(str)

    def __init__(self, watch_folder, output_folder):
        super().__init__()
        self.watch_folder = watch_folder
        self.output_folder = output_folder
        self.compressor = VideoCompressor()

    def run(self):
        self.log_signal.emit(f"👀 Watcher ONLINE: Monitoring '{self.watch_folder}'...\n")
        while not self.isInterruptionRequested():
            try:
                if not os.path.exists(self.watch_folder):
                    self.msleep(1000)
                    continue

                files = [f for f in os.listdir(self.watch_folder) if f.lower().endswith(('.mp4', '.mkv', '.mov'))]
                for f in files:
                    if self.isInterruptionRequested():
                        break
                    
                    input_path = os.path.join(self.watch_folder, f)
                    output_path = os.path.join(self.output_folder, f)
                    
                    # Wait for copy to complete safely
                    time.sleep(1)
                    self.log_signal.emit(f"⚡ Watcher Event: Found new file '{f}'. Processing...\n")
                    
                    if self.compressor.compress_audio_maintain_video(input_path, output_path):
                        self.log_signal.emit(f"✅ Watcher Success: Compressed '{f}' and moved to destination.\n")
                        try:
                            os.remove(input_path)
                        except Exception:
                            pass
                    else:
                        self.log_signal.emit(f"❌ Watcher Failure: Compression failed for '{f}'.\n")

                self.msleep(2000) # Poll every 2 seconds
            except Exception as e:
                self.log_signal.emit(f"⚠️ Watcher Error: {str(e)}\n")
                self.msleep(5000)

class LogisticsUI(QWidget):
    """
    Workspace for Storage, Archives, and Automation.
    Tab 1: Folder Archiver (packages subfolders to ZIPs).
    Tab 2: High-Speed Un-archiver (decompresses ZIPs using C++ 7z).
    Tab 3: Video Compressor (audio compression & video CRF pass-through).
    Tab 4: Folder Watcher (watches folders and runs auto-compression).
    """
    def __init__(self, back_callback, orchestrator):
        super().__init__()
        self.orchestrator = orchestrator
        self.archiver = FolderArchiver()
        self.unarchiver = EnterpriseUnarchiver()
        self.compressor = VideoCompressor()
        self.watcher_thread = None

        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        layout.setContentsMargins(30, 30, 30, 30)

        # --- HEADER ---
        header = QHBoxLayout()
        back_btn = QPushButton("⬅ Back to Dashboard")
        back_btn.clicked.connect(back_callback)
        header.addWidget(back_btn)
        
        title = QLabel("📦 Logistics, Compression & Archiver")
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

        self.setup_archiver_tab()
        self.setup_unarchiver_tab()
        self.setup_compressor_tab()
        self.setup_watcher_tab()

    # =========================================================================
    # TAB 1: FOLDER ARCHIVER
    # =========================================================================
    def setup_archiver_tab(self):
        tab = QWidget()
        t_layout = QVBoxLayout(tab)
        t_layout.setContentsMargins(20, 20, 20, 20)

        t_layout.addWidget(QLabel("Step 1: Select Parent Directory containing folders to ZIP"))
        self.arc_drop = DropZone(self, mode='dir')
        t_layout.addWidget(self.arc_drop)
        t_layout.addSpacing(15)

        self.zip_mode = QCheckBox(" Enable high compression (Deflate mode). Default: Fast packing.")
        self.zip_mode.setStyleSheet("font-size: 14px; color: #aaa;")
        t_layout.addWidget(self.zip_mode)
        t_layout.addSpacing(25)

        self.arc_btn = QPushButton("🚀 Run Batch Folder Archiver")
        self.arc_btn.setMinimumHeight(60)
        self.arc_btn.setStyleSheet("background-color: #2D72D9; color: white; font-size: 16px; font-weight: bold; border-radius: 8px;")
        self.arc_btn.clicked.connect(self.run_archiver)
        t_layout.addWidget(self.arc_btn)
        t_layout.addStretch()

        self.tabs.addTab(tab, "📦 Folder Archiver")

    def run_archiver(self):
        parent_dir = self.arc_drop.file_input.text().strip()
        compress = self.zip_mode.isChecked()

        if not parent_dir or not os.path.exists(parent_dir):
            return

        foldername = os.path.basename(parent_dir)
        def task():
            return self.archiver.batch_zip_folders(parent_dir, compress=compress)

        self.orchestrator.add_background_job(f"Archive Folders: {foldername}", task)
        self.orchestrator.show_status_message(f"⏳ Archiving task queued for: {foldername}")

    # =========================================================================
    # TAB 2: HIGH-SPEED UN-ARCHIVER
    # =========================================================================
    def setup_unarchiver_tab(self):
        tab = QWidget()
        t_layout = QVBoxLayout(tab)
        t_layout.setContentsMargins(20, 20, 20, 20)

        t_layout.addWidget(QLabel("Step 1: Select ZIP Archive File"))
        self.unarc_drop = DropZone(self)
        t_layout.addWidget(self.unarc_drop)
        t_layout.addSpacing(15)

        t_layout.addWidget(QLabel("Step 2: Select Extract Destination Folder (Optional, defaults next to zip)"))
        self.unarc_dest = DropZone(self, mode='dir')
        t_layout.addWidget(self.unarc_dest)
        t_layout.addSpacing(25)

        self.unarc_btn = QPushButton("🔓 Extract with 7-Zip Engine")
        self.unarc_btn.setMinimumHeight(60)
        self.unarc_btn.setStyleSheet("background-color: #2D72D9; color: white; font-size: 16px; font-weight: bold; border-radius: 8px;")
        self.unarc_btn.clicked.connect(self.run_unarchiver)
        t_layout.addWidget(self.unarc_btn)
        t_layout.addStretch()

        self.tabs.addTab(tab, "🔓 High-Speed Extract")

    def run_unarchiver(self):
        zip_path = self.unarc_drop.file_input.text().strip()
        dest = self.unarc_dest.file_input.text().strip()

        if not zip_path or not os.path.exists(zip_path):
            return

        # Read 7za path dynamically from settings
        # unarchiver.py hardcodes engine_path to src/tools/7za.exe, but we update constructor settings if available
        if os.path.exists("onyx_settings.json"):
            try:
                with open("onyx_settings.json", "r") as f:
                    settings = json.load(f)
                    zip_exe = settings.get("seven_zip", "")
                    if zip_exe:
                        self.unarchiver.engine_path = os.path.abspath(zip_exe)
            except Exception:
                pass

        filename = os.path.basename(zip_path)
        dest_folder = dest if dest else None

        def task():
            return self.unarchiver.extract_archive(zip_path, dest_folder)

        self.orchestrator.add_background_job(f"Extract ZIP: {filename}", task)
        self.orchestrator.show_status_message(f"⏳ Extraction task queued for: {filename}")

    # =========================================================================
    # TAB 3: VIDEO COMPRESSOR
    # =========================================================================
    def setup_compressor_tab(self):
        tab = QWidget()
        t_layout = QVBoxLayout(tab)
        t_layout.setContentsMargins(20, 20, 20, 20)

        t_layout.addWidget(QLabel("Step 1: Select Video to Compress"))
        self.comp_drop = DropZone(self)
        t_layout.addWidget(self.comp_drop)
        t_layout.addSpacing(15)

        t_layout.addWidget(QLabel("Step 2: Choose Target Audio Bitrate (lower saves more space):"))
        self.bitrate_combo = QComboBox()
        self.bitrate_combo.addItems(["384k", "320k", "256k", "192k", "128k", "96k", "64k"])
        self.bitrate_combo.setCurrentText("128k")
        self.bitrate_combo.setMinimumHeight(40)
        t_layout.addWidget(self.bitrate_combo)
        t_layout.addSpacing(25)

        self.comp_btn = QPushButton("🗜️ Execute Media Compression")
        self.comp_btn.setMinimumHeight(60)
        self.comp_btn.setStyleSheet("background-color: #2D72D9; color: white; font-size: 16px; font-weight: bold; border-radius: 8px;")
        self.comp_btn.clicked.connect(self.run_compressor)
        t_layout.addWidget(self.comp_btn)
        t_layout.addStretch()

        self.tabs.addTab(tab, "🗜️ Video Compressor")

    def run_compressor(self):
        path = self.comp_drop.file_input.text().strip()
        bitrate = self.bitrate_combo.currentText()

        if not path or not os.path.exists(path):
            return

        base_dir = os.path.dirname(path)
        name, ext = os.path.splitext(os.path.basename(path))
        output_path = os.path.join(base_dir, f"{name}_compressed{ext}")

        def task():
            return self.compressor.compress_audio_maintain_video(path, output_path, bitrate=bitrate)

        self.orchestrator.add_background_job(f"Compress Video: {name}", task)
        self.orchestrator.show_status_message(f"⏳ Compression task queued for: {name}")

    # =========================================================================
    # TAB 4: SMART FOLDER WATCHER
    # =========================================================================
    def setup_watcher_tab(self):
        tab = QWidget()
        t_layout = QVBoxLayout(tab)
        t_layout.setContentsMargins(20, 20, 20, 20)

        t_layout.addWidget(QLabel("Step 1: Select Watch Directory"))
        self.watch_drop = DropZone(self, mode='dir')
        t_layout.addWidget(self.watch_drop)
        t_layout.addSpacing(15)

        t_layout.addWidget(QLabel("Step 2: Select Compression Output Destination Directory"))
        self.dest_drop = DropZone(self, mode='dir')
        t_layout.addWidget(self.dest_drop)
        t_layout.addSpacing(20)

        self.watcher_status = QLabel("Watcher Status: OFFLINE")
        self.watcher_status.setStyleSheet("color: #ff3333; font-weight: bold;")
        t_layout.addWidget(self.watcher_status)
        t_layout.addSpacing(15)

        self.watch_btn = QPushButton("👁️ Start Smart Directory Watcher")
        self.watch_btn.setMinimumHeight(60)
        self.watch_btn.setStyleSheet("background-color: #00ff66; color: #111; font-size: 16px; font-weight: bold; border-radius: 8px;")
        self.watch_btn.clicked.connect(self.toggle_watcher)
        t_layout.addWidget(self.watch_btn)
        t_layout.addStretch()

        self.tabs.addTab(tab, "👁️ Folder Watcher")

    def toggle_watcher(self):
        if self.watcher_thread and self.watcher_thread.isRunning():
            # Stop watcher
            self.watcher_thread.requestInterruption()
            self.watcher_thread.wait()
            self.watcher_thread = None
            
            self.watcher_status.setText("Watcher Status: OFFLINE")
            self.watcher_status.setStyleSheet("color: #ff3333; font-weight: bold;")
            self.watch_btn.setText("👁️ Start Smart Directory Watcher")
            self.watch_btn.setStyleSheet("background-color: #00ff66; color: #111; font-size: 16px; font-weight: bold; border-radius: 8px;")
            self.orchestrator.append_log("🔴 Folder Watcher turned OFFLINE.\n")
        else:
            # Start watcher
            watch_dir = self.watch_drop.file_input.text().strip()
            dest_dir = self.dest_drop.file_input.text().strip()
            
            if not watch_dir or not dest_dir:
                return

            self.watcher_thread = WatcherThread(watch_dir, dest_dir)
            self.watcher_thread.log_signal.connect(self.orchestrator.append_log)
            self.watcher_thread.start()
            
            self.watcher_status.setText(f"Watcher Status: ACTIVE (Monitoring {os.path.basename(watch_dir)})")
            self.watcher_status.setStyleSheet("color: #00ff66; font-weight: bold;")
            self.watch_btn.setText("🛑 Stop Directory Watcher")
            self.watch_btn.setStyleSheet("background-color: #ff3333; color: white; font-size: 16px; font-weight: bold; border-radius: 8px;")
            self.orchestrator.append_log("🟢 Folder Watcher activated successfully.\n")

    def closeEvent(self, event):
        if self.watcher_thread and self.watcher_thread.isRunning():
            self.watcher_thread.requestInterruption()
            self.watcher_thread.wait()
        super().closeEvent(event)
