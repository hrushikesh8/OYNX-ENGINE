import sys
import os
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QPushButton, QLabel, QStackedWidget, 
                             QFrame, QGridLayout, QStatusBar)
from PyQt6.QtCore import Qt

# --- FEATURE CORE & WORKER IMPORTS ---
from src.ui.custom_widgets import TaskWorker
from src.ui.dashboard_ui import DashboardUI
from src.ui.divider_ui import DividerUI
from src.ui.audio_extractor_ui import AudioExtractorUI
from src.ui.ai_restoration_ui import AIRestorationUI
from src.ui.branding_ui import BrandingUI
from src.ui.logistics_ui import LogisticsUI
from src.ui.ladder_ui import StreamLadderUI

# --- EXISTING UI IMPORTS ---
from src.ui.formats_ui import FormatConverterUI
from src.ui.tracks_ui import TrackCleanerUI
from src.ui.suture_ui import SeamlessSutureUI
from src.ui.scene_sniper_ui import SceneSniperUI
from src.ui.merger_ui import StreamMergerUI
from src.ui.stitcher_ui import VideoStitcherUI

class MasterOrchestrator(QMainWindow):
    """
    The Central Brain of Onyx Engine.
    Manages global navigation, workspace hubs, high-end styling, 
    and an asynchronous render job queue.
    """
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Onyx Engine v3.0 | Professional Production Suite")
        self.resize(1300, 850)
        self.setMinimumSize(1100, 750)

        # Job Queue System
        self.job_queue = []
        self.max_concurrent_jobs = 1

        # Central Layout Container
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        self.main_layout = QHBoxLayout(central_widget)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)

        # 1. Define stacked workspace
        self.workspace = QStackedWidget()
        self.workspace.setStyleSheet("background-color: #121212;")

        # 2. Populate all UI views
        self.init_views()

        # 3. Setup Navigation Sidebar
        self.setup_sidebar()

        # 4. Add components to window layout
        self.main_layout.addWidget(self.workspace)

        # 5. Add status bar
        self.status_bar = QStatusBar()
        self.status_bar.setStyleSheet("background-color: #181818; color: #888; border-top: 1px solid #282828;")
        self.setStatusBar(self.status_bar)
        self.show_status_message("System Ready.")

    # =========================================================================
    # SIDEBAR NAVIGATION
    # =========================================================================

    def setup_sidebar(self):
        """Builds the left-hand navigation panel with animated buttons."""
        sidebar = QFrame()
        sidebar.setFixedWidth(260)
        sidebar.setStyleSheet("background-color: #1a1a1a; border-right: 1px solid #282828;")
        sidebar_layout = QVBoxLayout(sidebar)
        sidebar_layout.setContentsMargins(15, 25, 15, 25)

        # Brand Identity
        brand_container = QVBoxLayout()
        brand_label = QLabel("ONYX ENGINE")
        brand_label.setStyleSheet("font-size: 22px; font-weight: 900; color: white; letter-spacing: 3px;")
        brand_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        version_label = QLabel("v3.0 Production Build")
        version_label.setStyleSheet("font-size: 11px; color: #555; font-weight: bold;")
        version_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        brand_container.addWidget(brand_label)
        brand_container.addWidget(version_label)
        sidebar_layout.addLayout(brand_container)
        sidebar_layout.addSpacing(30)

        # Create Navigation Buttons
        self.btn_dash = self.create_nav_button("📊", "Dashboard")
        self.btn_format = self.create_nav_button("🔄", "Format & Container")
        self.btn_edit = self.create_nav_button("🎬", "Edit & Cut")
        self.btn_audio = self.create_nav_button("🎵", "Audio & Subtitles")
        self.btn_ai = self.create_nav_button("💎", "AI & VFX")
        self.btn_logistics = self.create_nav_button("📦", "Logistics & Archive")

        self.nav_buttons = [self.btn_dash, self.btn_format, self.btn_edit, self.btn_audio, self.btn_ai, self.btn_logistics]

        for btn in self.nav_buttons:
            sidebar_layout.addWidget(btn)
        
        sidebar_layout.addStretch()
        self.main_layout.insertWidget(0, sidebar)

        # Connect Navigation Logic
        self.btn_dash.clicked.connect(lambda: self.update_nav_selection(self.btn_dash, 0))
        self.btn_format.clicked.connect(lambda: self.update_nav_selection(self.btn_format, 1))
        self.btn_edit.clicked.connect(lambda: self.update_nav_selection(self.btn_edit, 2))
        self.btn_audio.clicked.connect(lambda: self.update_nav_selection(self.btn_audio, 3))
        self.btn_ai.clicked.connect(lambda: self.update_nav_selection(self.btn_ai, 4))
        self.btn_logistics.clicked.connect(lambda: self.update_nav_selection(self.btn_logistics, 5))

        # Initial selection
        self.btn_dash.setChecked(True)
        self.update_nav_selection(self.btn_dash, 0)

    def create_nav_button(self, icon_char, text):
        btn = QPushButton()
        btn.setCheckable(True)
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        btn.setMinimumHeight(55)
        
        layout = QHBoxLayout(btn)
        layout.setContentsMargins(15, 0, 15, 0)
        layout.setSpacing(15)
        
        icon_label = QLabel(icon_char)
        icon_label.setStyleSheet("font-size: 16px; color: #888; background: transparent;")
        
        text_label = QLabel(text)
        text_label.setStyleSheet("font-size: 13px; font-weight: bold; color: #aaa; background: transparent;")
        
        layout.addWidget(icon_label)
        layout.addWidget(text_label)
        layout.addStretch()

        btn.setStyleSheet("""
            QPushButton { background: transparent; border: none; border-radius: 8px; }
            QPushButton:hover { background-color: rgba(255, 255, 255, 5); }
            QPushButton:checked { background-color: rgba(45, 114, 217, 15); border-left: 4px solid #2D72D9; }
        """)

        def on_enter(event):
            icon_label.setStyleSheet("font-size: 16px; color: #2D72D9; background: transparent;")
            text_label.setStyleSheet("font-size: 13px; font-weight: bold; color: white; background: transparent;")
            super(QPushButton, btn).enterEvent(event)

        def on_leave(event):
            if not btn.isChecked():
                icon_label.setStyleSheet("font-size: 16px; color: #888; background: transparent;")
                text_label.setStyleSheet("font-size: 13px; font-weight: bold; color: #aaa; background: transparent;")
            super(QPushButton, btn).leaveEvent(event)

        btn.enterEvent = on_enter
        btn.leaveEvent = on_leave
        btn.icon_label = icon_label
        btn.text_label = text_label

        return btn

    def update_nav_selection(self, selected_btn, target_index):
        for btn in self.nav_buttons:
            is_active = (btn == selected_btn)
            btn.setChecked(is_active)
            color = "#2D72D9" if is_active else "#888"
            txt_color = "white" if is_active else "#aaa"
            btn.icon_label.setStyleSheet(f"font-size: 16px; color: {color}; background: transparent;")
            btn.text_label.setStyleSheet(f"font-size: 13px; font-weight: bold; color: {txt_color}; background: transparent;")
            
        self.workspace.setCurrentIndex(target_index)

    # =========================================================================
    # WORKSPACE HUBS & CARDS
    # =========================================================================

    def create_tool_card(self, title, desc, target_index):
        card = QFrame()
        card.setCursor(Qt.CursorShape.PointingHandCursor)
        card.setMinimumSize(280, 160)
        
        layout = QVBoxLayout(card)
        layout.setContentsMargins(20, 20, 20, 20)

        t_label = QLabel(title)
        t_label.setStyleSheet("font-size: 16px; font-weight: bold; color: #eee; background: transparent; border: none;")
        
        d_label = QLabel(desc)
        d_label.setStyleSheet("font-size: 12px; color: #777; background: transparent; border: none;")
        d_label.setWordWrap(True)

        layout.addWidget(t_label)
        layout.addWidget(d_label)
        layout.addStretch()

        def set_style(hover=False):
            bg = "#222" if hover else "#1a1a1a"
            border = "#2D72D9" if hover else "#282828"
            txt = "#2D72D9" if hover else "#eee"
            card.setStyleSheet(f"QFrame {{ background-color: {bg}; border: 2px solid {border}; border-radius: 12px; }}")
            t_label.setStyleSheet(f"font-size: 16px; font-weight: bold; color: {txt}; background: transparent; border: none;")

        set_style(False)
        card.enterEvent = lambda e: set_style(True)
        card.leaveEvent = lambda e: set_style(False)
        card.mousePressEvent = lambda e: self.workspace.setCurrentIndex(target_index)

        return card

    def init_views(self):
        """Orchestrates stacked layouts and back routing references."""

        # --- INDEX 0: DASHBOARD & SETTINGS ---
        self.dashboard_ui = DashboardUI(self)
        self.workspace.addWidget(self.dashboard_ui)

        # --- INDEX 1: FORMAT & CONTAINER HUB ---
        fmt_hub = QWidget()
        fmt_layout = QVBoxLayout(fmt_hub)
        fmt_layout.setContentsMargins(40, 40, 40, 40)
        fmt_title = QLabel("Format & Container Hub")
        fmt_title.setStyleSheet("font-size: 24px; font-weight: bold; color: white; margin-bottom: 20px;")
        fmt_layout.addWidget(fmt_title)
        
        grid_fmt = QGridLayout()
        grid_fmt.setSpacing(25)
        grid_fmt.addWidget(self.create_tool_card("🔄 Format Converter", "Convert containers losslessly or re-encode video.", 6), 0, 0)
        grid_fmt.addWidget(self.create_tool_card("📶 ABR Stream Ladder / Compare", "Create ABR ladder profiles or compare quality.", 7), 0, 1)
        fmt_layout.addLayout(grid_fmt)
        fmt_layout.addStretch()
        self.workspace.addWidget(fmt_hub)

        # --- INDEX 2: EDIT & DIVIDE HUB ---
        edit_hub = QWidget()
        edit_layout = QVBoxLayout(edit_hub)
        edit_layout.setContentsMargins(40, 40, 40, 40)
        edit_title = QLabel("Edit & Divide Hub")
        edit_title.setStyleSheet("font-size: 24px; font-weight: bold; color: white; margin-bottom: 20px;")
        edit_layout.addWidget(edit_title)
        
        grid_edit = QGridLayout()
        grid_edit.setSpacing(25)
        grid_edit.addWidget(self.create_tool_card("🎯 Scene Sniper", "Extract pristine clips with frame accuracy.", 8), 0, 0)
        grid_edit.addWidget(self.create_tool_card("🧵 Seamless Suture", "AI-Powered merging of split movie parts.", 9), 0, 1)
        grid_edit.addWidget(self.create_tool_card("🎬 Video Stitcher", "Concat multiple clips instantly.", 10), 1, 0)
        grid_edit.addWidget(self.create_tool_card("✂️ Edit, Divide & Auto-Trim", "Intermission split, chunks, and silence removal.", 11), 1, 1)
        edit_layout.addLayout(grid_edit)
        edit_layout.addStretch()
        self.workspace.addWidget(edit_hub)

        # --- INDEX 3: AUDIO & SUBS HUB ---
        audio_hub = QWidget()
        audio_layout = QVBoxLayout(audio_hub)
        audio_layout.setContentsMargins(40, 40, 40, 40)
        audio_title = QLabel("Audio & Subtitle Workspace")
        audio_title.setStyleSheet("font-size: 24px; font-weight: bold; color: white; margin-bottom: 20px;")
        audio_layout.addWidget(audio_title)
        
        grid_audio = QGridLayout()
        grid_audio.setSpacing(25)
        grid_audio.addWidget(self.create_tool_card("🎙️ Audio Extractor & Harvester", "Extract single tracks or run folder mass ripping.", 12), 0, 0)
        grid_audio.addWidget(self.create_tool_card("🎵 Audio Track Cleaner", "Purge language dubs from files.", 13), 0, 1)
        grid_audio.addWidget(self.create_tool_card("📝 Subtitle Track Cleaner", "Remove extra subtitle streams.", 14), 1, 0)
        grid_audio.addWidget(self.create_tool_card("🔗 Stream Merger (Audio Sync)", "Mux audio with video timeline.", 15), 1, 1)
        grid_audio.addWidget(self.create_tool_card("📝 Subtitle Muxer", "Softcode external subtitles into container.", 20, 0), 2, 0)
        audio_layout.addLayout(grid_audio)
        audio_layout.addStretch()
        self.workspace.addWidget(audio_hub)

        # --- INDEX 4: AI & VFX HUB ---
        ai_hub = QWidget()
        ai_layout = QVBoxLayout(ai_hub)
        ai_layout.setContentsMargins(40, 40, 40, 40)
        ai_title = QLabel("AI Restoration & VFX Hub")
        ai_title.setStyleSheet("font-size: 24px; font-weight: bold; color: white; margin-bottom: 20px;")
        ai_layout.addWidget(ai_title)
        
        grid_ai = QGridLayout()
        grid_ai.setSpacing(25)
        grid_ai.addWidget(self.create_tool_card("💎 AI Remaster & Motion", "Real-ESRGAN upscaling, RIFE 60FPS, and chaptering.", 17), 0, 0)
        grid_ai.addWidget(self.create_tool_card("🎨 VFX, Branding & GIFs", "Overlay watermarks, delogo eraser, and HD GIFs.", 18), 0, 1)
        ai_layout.addLayout(grid_ai)
        ai_layout.addStretch()
        self.workspace.addWidget(ai_hub)

        # --- INDEX 5: LOGISTICS & ARCHIVE VIEW DIRECT ---
        self.logistics_ui = LogisticsUI(back_callback=lambda: self.update_nav_selection(self.btn_dash, 0), orchestrator=self)
        self.workspace.addWidget(self.logistics_ui)

        # --- DETAILED TOOL VIEWS (INDEX 6-18) ---

        # 6: Format Converter
        self.format_ui = FormatConverterUI(back_callback=lambda: self.workspace.setCurrentIndex(1))
        self.workspace.addWidget(self.format_ui)

        # 7: Stream Ladder & Comparer
        self.ladder_ui = StreamLadderUI(back_callback=lambda: self.workspace.setCurrentIndex(1), orchestrator=self)
        self.workspace.addWidget(self.ladder_ui)

        # 8: Scene Sniper
        self.sniper_ui = SceneSniperUI(back_callback=lambda: self.workspace.setCurrentIndex(2))
        self.workspace.addWidget(self.sniper_ui)

        # 9: Seamless Suture
        self.suture_ui = SeamlessSutureUI(back_callback=lambda: self.workspace.setCurrentIndex(2))
        self.workspace.addWidget(self.suture_ui)

        # 10: Video Stitcher
        self.stitcher_ui = VideoStitcherUI(back_callback=lambda: self.workspace.setCurrentIndex(2))
        self.workspace.addWidget(self.stitcher_ui)

        # 11: DividerUI (Intermission/Chunks/Shorts/Silence Remover)
        self.divider_ui = DividerUI(back_callback=lambda: self.workspace.setCurrentIndex(2), orchestrator=self)
        self.workspace.addWidget(self.divider_ui)

        # 12: Audio Extractor (Single & Harvester)
        self.audio_extract_ui = AudioExtractorUI(back_callback=lambda: self.workspace.setCurrentIndex(3), orchestrator=self)
        self.workspace.addWidget(self.audio_extract_ui)

        # 13: Audio Track Cleaner
        self.audio_cleaner_ui = TrackCleanerUI(back_callback=lambda: self.workspace.setCurrentIndex(3), mode='a')
        self.workspace.addWidget(self.audio_cleaner_ui)

        # 14: Subtitle Track Cleaner
        self.sub_cleaner_ui = TrackCleanerUI(back_callback=lambda: self.workspace.setCurrentIndex(3), mode='s')
        self.workspace.addWidget(self.sub_cleaner_ui)

        # 15: Stream Merger (Audio Sync)
        self.merger_audio_ui = StreamMergerUI(back_callback=lambda: self.workspace.setCurrentIndex(3), mode='audio')
        self.workspace.addWidget(self.merger_audio_ui)

        # 16: Subtitle Muxer
        self.merger_sub_ui = StreamMergerUI(back_callback=lambda: self.workspace.setCurrentIndex(3), mode='subtitle')
        self.workspace.addWidget(self.merger_sub_ui)

        # 17: AI Restoration (Real-ESRGAN / RIFE / Intel)
        self.ai_rest_ui = AIRestorationUI(back_callback=lambda: self.workspace.setCurrentIndex(4), orchestrator=self)
        self.workspace.addWidget(self.ai_rest_ui)

        # 18: VFX Branding (Watermark/Delogo/GIF)
        self.branding_ui = BrandingUI(back_callback=lambda: self.workspace.setCurrentIndex(4), orchestrator=self)
        self.workspace.addWidget(self.branding_ui)

    # =========================================================================
    # CENTRAL BACKGROUND JOB QUEUE SYSTEM
    # =========================================================================

    def add_background_job(self, name, func_or_cmd):
        """Queues a task or command list for execution in background thread."""
        job = {
            "name": name,
            "status": "Queued",
            "func_or_cmd": func_or_cmd,
            "worker": None
        }
        self.job_queue.append(job)
        self.append_log(f"📥 [Queue] Task added: {name}\n")
        self.process_next_job()

    def process_next_job(self):
        """Scans queue and runs the next queued job up to max concurrency."""
        running = sum(1 for j in self.job_queue if j["status"] == "Running")
        if running >= self.max_concurrent_jobs:
            return

        for idx, job in enumerate(self.job_queue):
            if job["status"] == "Queued":
                job["status"] = "Running"
                self.show_status_message(f"Running: {job['name']}")
                self.append_log(f"🎬 [Engine] Initializing task thread for: {job['name']}\n")
                
                # Instantiate and hook worker thread
                worker = TaskWorker(job["func_or_cmd"])
                job["worker"] = worker
                
                # Use default arguments via lambda with index lock
                worker.log_signal.connect(self.handle_job_log)
                worker.finished_signal.connect(lambda success, msg, index=idx: self.handle_job_finished(success, msg, index))
                
                worker.start()
                break

    def handle_job_log(self, text):
        self.dashboard_ui.append_log(text)

    def handle_job_finished(self, success, msg, index):
        if index < len(self.job_queue):
            job = self.job_queue[index]
            job["status"] = "Completed" if success else "Failed"
            status_symbol = "✅" if success else "❌"
            self.append_log(f"\n{status_symbol} [Finished] {job['name']} - Result: {msg}\n\n")
            self.show_status_message(f"Task Finished: {job['name']}")
            
            # Stop & cleanup thread safely
            if job["worker"]:
                job["worker"].wait()
                job["worker"] = None
                
        self.process_next_job()

    def cancel_or_remove_job(self, idx):
        if idx < len(self.job_queue):
            job = self.job_queue[idx]
            if job["status"] == "Running":
                self.append_log(f"⚠️ [User] Terminating active thread: {job['name']}...\n")
                if job["worker"]:
                    job["worker"].requestInterruption()
                    job["worker"].terminate()
                    job["worker"].wait()
                    job["worker"] = None
                job["status"] = "Failed"
                self.append_log("🔴 [Engine] Task terminated.\n")
                self.process_next_job()
            else:
                self.job_queue.pop(idx)
                self.append_log(f"🗑️ [User] Removed task from queue: {job['name']}\n")

    def show_status_message(self, message):
        self.status_bar.showMessage(message)

    def append_log(self, text):
        self.dashboard_ui.append_log(text)

# --- BOOTSTRAP ---
if __name__ == "__main__":
    import qdarktheme
    app = QApplication(sys.argv)
    qdarktheme.setup_theme("dark", custom_colors={"primary": "#2D72D9"})
    window = MasterOrchestrator()
    window.show()
    sys.exit(app.exec())