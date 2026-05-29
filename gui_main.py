import sys
import os
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QPushButton, QLabel, QStackedWidget, 
                             QFrame, QGridLayout, QStatusBar, QProgressBar)
from PyQt6.QtCore import Qt, QTimer

# --- FEATURE CORE & WORKER IMPORTS ---
from src.ui.custom_widgets import TaskWorker
from src.ui.dashboard_ui import DashboardUI
from src.ui.divider_ui import DividerUI
from src.ui.audio_extractor_ui import AudioExtractorUI
from src.ui.ai_restoration_ui import AIRestorationUI
from src.ui.branding_ui import BrandingUI
from src.ui.logistics_ui import LogisticsUI
from src.ui.ladder_ui import StreamLadderUI
from src.ui.settings_ui import SettingsUI
from src.ui.chronicle_ui import ChronicleUI

# --- EXISTING UI IMPORTS ---
from src.ui.formats_ui import FormatConverterUI
from src.ui.tracks_ui import TrackCleanerUI
from src.ui.suture_ui import SeamlessSutureUI
from src.ui.scene_sniper_ui import SceneSniperUI
from src.ui.merger_ui import StreamMergerUI
from src.ui.stitcher_ui import VideoStitcherUI
from src.ui.timeline_ui import TimelineComposerUI

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
        self.setMinimumSize(800, 600)

        # Job Queue & Thread Registry System
        self.job_queue = []
        self.active_workers = set()
        self.max_concurrent_jobs = 1
        self.sidebar_collapsed = False
        self.load_general_settings()

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
        
        # Add a settings cog icon to the right side of status bar (DaVinci Resolve style)
        self.status_cog = QPushButton("⚙")
        self.status_cog.setFixedSize(24, 24)
        self.status_cog.setCursor(Qt.CursorShape.PointingHandCursor)
        self.status_cog.setStyleSheet("""
            QPushButton {
                background: transparent;
                border: none;
                color: #888888;
                font-size: 16px;
                font-weight: bold;
            }
            QPushButton:hover {
                color: #2D72D9;
            }
        """)
        self.status_cog.clicked.connect(self.open_settings_dialog)
        self.status_bar.addPermanentWidget(self.status_cog)
        
        # --- GLOBAL PROGRESS PANEL ---
        self.global_progress_panel = QWidget()
        progress_layout = QHBoxLayout(self.global_progress_panel)
        progress_layout.setContentsMargins(0, 0, 15, 0)
        
        self.global_eta_label = QLabel()
        self.global_eta_label.setStyleSheet("color: #aaa; font-size: 11px; font-weight: bold;")
        self.global_eta_label.hide()
        
        self.global_progress_bar = QProgressBar()
        self.global_progress_bar.setFixedWidth(150)
        self.global_progress_bar.setFixedHeight(12)
        self.global_progress_bar.setTextVisible(False)
        self.global_progress_bar.setStyleSheet("""
            QProgressBar { border-radius: 6px; background-color: #2b2b2b; }
            QProgressBar::chunk { background-color: #2D72D9; border-radius: 6px; }
        """)
        self.global_progress_bar.hide()
        
        self.global_cancel_btn = QPushButton("🚫 Cancel")
        self.global_cancel_btn.setFixedSize(70, 22)
        self.global_cancel_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.global_cancel_btn.setStyleSheet("""
            QPushButton { background-color: #d92d2d; color: white; border-radius: 4px; font-weight: bold; font-size: 11px; }
            QPushButton:hover { background-color: #f03e3e; }
        """)
        self.global_cancel_btn.hide()
        self.global_cancel_btn.clicked.connect(self.cancel_active_job_from_ui)
        
        progress_layout.addWidget(self.global_eta_label)
        progress_layout.addWidget(self.global_progress_bar)
        progress_layout.addWidget(self.global_cancel_btn)
        
        self.status_bar.addPermanentWidget(self.global_progress_panel)
        self.setStatusBar(self.status_bar)
        
        # Countdown Timer for smooth visual countdowns
        self.countdown_timer = QTimer(self)
        self.countdown_timer.timeout.connect(self.tick_countdown)
        self.current_job_seconds_left = 0
        
        self.show_status_message("System Ready.")

    def load_general_settings(self):
        import json
        if os.path.exists("onyx_settings.json"):
            try:
                with open("onyx_settings.json", "r") as f:
                    settings = json.load(f)
                    self.max_concurrent_jobs = settings.get("max_concurrent_jobs", 1)
                    accent = settings.get("accent_color", "#2D72D9")
                    theme_mode = settings.get("theme_mode", "dark")
                    import qdarktheme
                    qdarktheme.setup_theme(theme_mode, custom_colors={"primary": accent})
            except Exception:
                pass

    # =========================================================================
    # SIDEBAR NAVIGATION
    # =========================================================================

    def setup_sidebar(self):
        """Builds the left-hand navigation panel with animated buttons."""
        self.sidebar = QFrame()
        self.sidebar.setFixedWidth(260)
        self.sidebar.setStyleSheet("background-color: #101010; border-right: 1px solid #1b1b1f;")
        sidebar_layout = QVBoxLayout(self.sidebar)
        sidebar_layout.setContentsMargins(15, 20, 15, 20)

        # Brand Identity & Toggle Row
        brand_row = QHBoxLayout()
        self.brand_label = QLabel("ONYX ENGINE")
        self.brand_label.setStyleSheet("font-size: 18px; font-weight: 900; color: white; letter-spacing: 2px;")
        
        self.btn_toggle = QPushButton("☰")
        self.btn_toggle.setFixedSize(32, 32)
        self.btn_toggle.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_toggle.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                border: none;
                color: #888888;
                font-size: 16px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: rgba(255, 255, 255, 0.05);
                color: white;
                border-radius: 6px;
            }
        """)
        self.btn_toggle.clicked.connect(self.toggle_sidebar)
        
        brand_row.addWidget(self.brand_label)
        brand_row.addStretch()
        brand_row.addWidget(self.btn_toggle)
        sidebar_layout.addLayout(brand_row)
        
        self.version_label = QLabel("v3.0 Production Build")
        self.version_label.setStyleSheet("font-size: 10px; color: #444; font-weight: bold; margin-bottom: 20px;")
        sidebar_layout.addWidget(self.version_label)

        # Create Navigation Buttons
        self.btn_dash = self.create_nav_button("📊", "Dashboard", True)
        self.btn_format = self.create_nav_button("🔄", "Format & Container", True)
        self.btn_edit = self.create_nav_button("🎬", "Edit & Cut", True)
        self.btn_audio = self.create_nav_button("🎵", "Audio & Subtitles", True)
        self.btn_ai = self.create_nav_button("💎", "AI & VFX", True)
        self.btn_logistics = self.create_nav_button("📦", "Logistics & Archive", True)
        self.btn_chronicle = self.create_nav_button("🎬", "Chronicle Organizer", True)

        self.nav_buttons = [self.btn_dash, self.btn_format, self.btn_edit, self.btn_audio, self.btn_ai, self.btn_logistics, self.btn_chronicle]

        for btn in self.nav_buttons:
            sidebar_layout.addWidget(btn)
        
        sidebar_layout.addStretch()

        # Premium separator line before settings
        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.HLine)
        separator.setStyleSheet("background-color: #202020; margin: 10px 0px;")
        sidebar_layout.addWidget(separator)

        # Settings button anchored at bottom (Non-checkable modal dialog trigger)
        self.btn_settings = self.create_nav_button("⚙️", "Settings", False)
        sidebar_layout.addWidget(self.btn_settings)

        self.main_layout.insertWidget(0, self.sidebar)

        # Connect Navigation Logic
        self.btn_dash.clicked.connect(lambda: self.update_nav_selection(self.btn_dash, 0))
        self.btn_format.clicked.connect(lambda: self.update_nav_selection(self.btn_format, 1))
        self.btn_edit.clicked.connect(lambda: self.update_nav_selection(self.btn_edit, 2))
        self.btn_audio.clicked.connect(lambda: self.update_nav_selection(self.btn_audio, 3))
        self.btn_ai.clicked.connect(lambda: self.update_nav_selection(self.btn_ai, 4))
        self.btn_logistics.clicked.connect(lambda: self.update_nav_selection(self.btn_logistics, 5))
        self.btn_chronicle.clicked.connect(lambda: self.update_nav_selection(self.btn_chronicle, 20))
        self.btn_settings.clicked.connect(self.open_settings_dialog)

        # Initial selection
        self.btn_dash.setChecked(True)
        self.update_nav_selection(self.btn_dash, 0)

    def create_nav_button(self, icon_char, text, checkable=True):
        btn = QPushButton()
        btn.icon_char = icon_char
        btn.text_label = text
        btn.setText(f"  {icon_char}    {text}")
        btn.setCheckable(checkable)
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        btn.setMinimumHeight(46)
        btn.setToolTip(text)
        btn.setStyleSheet("""
            QPushButton { 
                background-color: transparent; 
                border: none; 
                border-radius: 6px; 
                color: #aaaaaa; 
                text-align: left; 
                padding-left: 20px; 
                font-size: 13px; 
                font-weight: bold; 
            }
            QPushButton:hover { 
                background-color: rgba(255, 255, 255, 0.05); 
                color: #ffffff; 
            }
            QPushButton:checked { 
                background-color: rgba(45, 114, 217, 0.12); 
                color: #2D72D9; 
                border-left: 4px solid #2D72D9; 
                border-radius: 0px; 
                border-top-right-radius: 6px; 
                border-bottom-right-radius: 6px; 
                padding-left: 16px; 
            }
        """)
        return btn

    def toggle_sidebar(self):
        self.sidebar_collapsed = not self.sidebar_collapsed
        if self.sidebar_collapsed:
            self.sidebar.setFixedWidth(68)
            self.brand_label.hide()
            self.version_label.hide()
            for btn in self.nav_buttons + [self.btn_settings]:
                btn.setText(btn.icon_char)
                btn.setStyleSheet("""
                    QPushButton { 
                        background-color: transparent; 
                        border: none; 
                        border-radius: 6px; 
                        color: #aaaaaa; 
                        text-align: center; 
                        padding-left: 0px; 
                        font-size: 16px; 
                    }
                    QPushButton:hover { 
                        background-color: rgba(255, 255, 255, 0.05); 
                        color: #ffffff; 
                    }
                    QPushButton:checked { 
                        background-color: rgba(45, 114, 217, 0.12); 
                        color: #2D72D9; 
                        border-left: 4px solid #2D72D9; 
                        border-radius: 0px; 
                        border-top-right-radius: 6px; 
                        border-bottom-right-radius: 6px; 
                        padding-left: 0px; 
                    }
                """)
        else:
            self.sidebar.setFixedWidth(260)
            self.brand_label.show()
            self.version_label.show()
            for btn in self.nav_buttons + [self.btn_settings]:
                btn.setText(f"  {btn.icon_char}    {btn.text_label}")
                btn.setStyleSheet("""
                    QPushButton { 
                        background-color: transparent; 
                        border: none; 
                        border-radius: 6px; 
                        color: #aaaaaa; 
                        text-align: left; 
                        padding-left: 20px; 
                        font-size: 13px; 
                        font-weight: bold; 
                    }
                    QPushButton:hover { 
                        background-color: rgba(255, 255, 255, 0.05); 
                        color: #ffffff; 
                    }
                    QPushButton:checked { 
                        background-color: rgba(45, 114, 217, 0.12); 
                        color: #2D72D9; 
                        border-left: 4px solid #2D72D9; 
                        border-radius: 0px; 
                        border-top-right-radius: 6px; 
                        border-bottom-right-radius: 6px; 
                        padding-left: 16px; 
                    }
                """)

    def open_settings_dialog(self):
        from src.ui.settings_ui import SettingsUI
        dialog = SettingsUI(self)
        dialog.exec()

    def update_nav_selection(self, selected_btn, target_index):
        for btn in self.nav_buttons:
            btn.setChecked(btn == selected_btn)
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
        grid_edit.addWidget(self.create_tool_card("🎬 Multi-Track Timeline Composer", "Overlay multiple B-rolls over background audio with speed & canvas settings.", 19), 2, 0, 1, 2)
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
        grid_audio.addWidget(self.create_tool_card("📝 Subtitle Muxer", "Softcode external subtitles into container.", 16), 2, 0)
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
        self.format_ui = FormatConverterUI(back_callback=lambda: self.workspace.setCurrentIndex(1), orchestrator=self)
        self.workspace.addWidget(self.format_ui)

        # 7: Stream Ladder & Comparer
        self.ladder_ui = StreamLadderUI(back_callback=lambda: self.workspace.setCurrentIndex(1), orchestrator=self)
        self.workspace.addWidget(self.ladder_ui)

        # 8: Scene Sniper
        self.sniper_ui = SceneSniperUI(back_callback=lambda: self.workspace.setCurrentIndex(2), orchestrator=self)
        self.workspace.addWidget(self.sniper_ui)

        # 9: Seamless Suture
        self.suture_ui = SeamlessSutureUI(back_callback=lambda: self.workspace.setCurrentIndex(2), orchestrator=self)
        self.workspace.addWidget(self.suture_ui)

        # 10: Video Stitcher
        self.stitcher_ui = VideoStitcherUI(back_callback=lambda: self.workspace.setCurrentIndex(2), orchestrator=self)
        self.workspace.addWidget(self.stitcher_ui)

        # 11: DividerUI (Intermission/Chunks/Shorts/Silence Remover)
        self.divider_ui = DividerUI(back_callback=lambda: self.workspace.setCurrentIndex(2), orchestrator=self)
        self.workspace.addWidget(self.divider_ui)

        # 12: Audio Extractor (Single & Harvester)
        self.audio_extract_ui = AudioExtractorUI(back_callback=lambda: self.workspace.setCurrentIndex(3), orchestrator=self)
        self.workspace.addWidget(self.audio_extract_ui)

        # 13: Audio Track Cleaner
        self.audio_cleaner_ui = TrackCleanerUI(back_callback=lambda: self.workspace.setCurrentIndex(3), orchestrator=self, mode='a')
        self.workspace.addWidget(self.audio_cleaner_ui)

        # 14: Subtitle Track Cleaner
        self.sub_cleaner_ui = TrackCleanerUI(back_callback=lambda: self.workspace.setCurrentIndex(3), orchestrator=self, mode='s')
        self.workspace.addWidget(self.sub_cleaner_ui)

        # 15: Stream Merger (Audio Sync)
        self.merger_audio_ui = StreamMergerUI(back_callback=lambda: self.workspace.setCurrentIndex(3), orchestrator=self, mode='audio')
        self.workspace.addWidget(self.merger_audio_ui)

        # 16: Subtitle Muxer
        self.merger_sub_ui = StreamMergerUI(back_callback=lambda: self.workspace.setCurrentIndex(3), orchestrator=self, mode='subtitle')
        self.workspace.addWidget(self.merger_sub_ui)

        # 17: AI Restoration (Real-ESRGAN / RIFE / Intel)
        self.ai_rest_ui = AIRestorationUI(back_callback=lambda: self.workspace.setCurrentIndex(4), orchestrator=self)
        self.workspace.addWidget(self.ai_rest_ui)

        # 18: VFX Branding (Watermark/Delogo/GIF)
        self.branding_ui = BrandingUI(back_callback=lambda: self.workspace.setCurrentIndex(4), orchestrator=self)
        self.workspace.addWidget(self.branding_ui)

        # 19: Multi-Track Timeline Composer
        self.timeline_ui = TimelineComposerUI(back_callback=lambda: self.workspace.setCurrentIndex(2), orchestrator=self)
        self.workspace.addWidget(self.timeline_ui)

        # 20: Chronicle Organizer
        self.chronicle_ui = ChronicleUI(orchestrator=self)
        self.workspace.addWidget(self.chronicle_ui)

        # (SettingsUI is now a modal dialog, not added to stacked widget)

    # =========================================================================
    # CENTRAL BACKGROUND JOB QUEUE SYSTEM
    # =========================================================================

    def add_background_job(self, name, func_or_cmd, estimated_seconds=0):
        """Queues a task or command list for execution in background thread."""
        job = {
            "name": name,
            "status": "Queued",
            "func_or_cmd": func_or_cmd,
            "worker": None,
            "est_seconds": estimated_seconds
        }
        self.job_queue.append(job)
        self.append_log(f"📥 [Queue] Task added: {name}\n")
        self.process_next_job()

    def process_next_job(self):
        """Scans queue and runs the next queued job up to max concurrency."""
        running = sum(1 for j in self.job_queue if j["status"] == "Running")
        if running >= self.max_concurrent_jobs:
            return

        for job in self.job_queue:
            if job["status"] == "Queued":
                job["status"] = "Running"
                self.show_status_message(f"Running: {job['name']}")
                self.append_log(f"🎬 [Engine] Initializing task thread for: {job['name']}\n")
                
                # Show UI Immediately for instant Cancel availability
                self.global_progress_bar.setValue(0)
                self.global_progress_bar.show()
                self.global_cancel_btn.show()
                
                if job.get("est_seconds", 0) > 0:
                    self.current_job_seconds_left = job["est_seconds"]
                    self.global_eta_label.setText(f"Starting... (~{int(self.current_job_seconds_left)}s left)")
                    self.global_eta_label.show()
                    self.countdown_timer.start(1000)
                else:
                    self.current_job_seconds_left = 0
                    self.global_eta_label.setText("Starting...")
                    self.global_eta_label.show()
                    self.countdown_timer.start(1000)
                
                # Instantiate and hook worker thread
                worker = TaskWorker(job["func_or_cmd"])
                job["worker"] = worker
                
                # Connect slots using worker matching to avoid index-shift race conditions
                worker.log_signal.connect(self.handle_job_log)
                worker.finished_signal.connect(lambda success, msg, w=worker: self.handle_job_finished(success, msg, w))
                worker.progress_update.connect(lambda pct, txt, w=worker: self.handle_job_progress(pct, txt, w))
                
                # Keep strong reference in main window to prevent early Python garbage collection
                if not hasattr(self, 'active_workers'):
                    self.active_workers = set()
                self.active_workers.add(worker)
                
                # Safe cleanup on actual thread finish
                worker.finished.connect(lambda w=worker: self.cleanup_worker(w))
                
                worker.start()
                break

    def handle_job_log(self, text):
        self.dashboard_ui.append_log(text)

    def handle_job_progress(self, pct, txt, worker):
        for job in self.job_queue:
            if job["worker"] == worker:
                job["status"] = txt
                # We update the progress bar, but let QTimer handle the ETA text if est_seconds > 0
                if self.current_job_seconds_left <= 0:
                    self.global_eta_label.setText(txt)
                
                self.global_eta_label.show()
                self.global_progress_bar.setValue(pct)
                self.global_progress_bar.show()
                self.global_cancel_btn.show()
                break
        current_w = self.workspace.currentWidget()
        if hasattr(current_w, "on_job_progress"):
            current_w.on_job_progress(worker, pct, txt)

    def tick_countdown(self):
        if self.current_job_seconds_left > 0:
            self.current_job_seconds_left -= 1
            rem = self.current_job_seconds_left
            if rem > 3600:
                txt = f"~{int(rem//3600)}h {int((rem%3600)//60)}m left"
            elif rem > 60:
                txt = f"~{int(rem//60)}m {int(rem%60)}s left"
            else:
                txt = f"~{int(rem)}s left"
            
            # Extract percentage from job status if possible
            pct_str = "Running"
            for job in self.job_queue:
                if job["status"] == "Running":
                    pass # Not easily extractable, rely on progress bar value
            
            self.global_eta_label.setText(f"Running ({self.global_progress_bar.value()}% | {txt})")

    def handle_job_finished(self, success, msg, worker):
        self.countdown_timer.stop()
        self.global_eta_label.hide()
        self.global_progress_bar.hide()
        self.global_cancel_btn.hide()
        
        for job in self.job_queue:
            if job["worker"] == worker:
                job["status"] = "Completed" if success else "Failed"
                status_symbol = "✅" if success else "❌"
                self.append_log(f"\n{status_symbol} [Finished] {job['name']} - Result: {msg}\n\n")
                self.show_status_message(f"Task Finished: {job['name']}")
                break
        current_w = self.workspace.currentWidget()
        if hasattr(current_w, "on_job_finished"):
            current_w.on_job_finished(worker, success, msg)
        self.process_next_job()

    def cleanup_worker(self, worker):
        if hasattr(self, 'active_workers') and worker in self.active_workers:
            self.active_workers.discard(worker)
        # Safely schedules object deletion inside main thread event loop
        worker.deleteLater()

    def cancel_active_job_from_ui(self):
        for idx, job in enumerate(self.job_queue):
            if job["status"] == "Running":
                self.cancel_or_remove_job(idx)
                break

    def cancel_or_remove_job(self, idx):
        if idx < len(self.job_queue):
            job = self.job_queue[idx]
            if job["status"] == "Running":
                self.append_log(f"⚠️ [User] Terminating active thread: {job['name']}...\n")
                if job["worker"]:
                    job["worker"].requestInterruption()
                    if hasattr(job["worker"], "cancel"):
                        job["worker"].cancel()
                    else:
                        job["worker"].terminate()
                    job["worker"].wait(2000) # Short wait timeout
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
    import json
    
    app = QApplication(sys.argv)
    
    # Load settings early to apply global theme
    settings = {}
    if os.path.exists("onyx_settings.json"):
        try:
            with open("onyx_settings.json", "r") as f:
                settings = json.load(f)
        except Exception:
            pass
            
    accent = settings.get("accent_color", "#2D72D9")
    theme_mode = settings.get("theme_mode", "dark")
    
    qdarktheme.setup_theme(theme_mode, custom_colors={"primary": accent})
    
    window = MasterOrchestrator()
    window.show()
    sys.exit(app.exec())

# ==========================================
# HOW TO USE THIS CODE (EXAMPLE)
# ==========================================
# Example usage:
# from src.processors.gui_main import MainClass
# processor = MainClass()
# processor.run(input_file, output_file)
# ==========================================

# ==============================================================================
# 🎬 FEATURE: INTERNAL MODULE DOCUMENTATION (gui_main.py)
# ==============================================================================
#
# 📝 WHAT IS THIS FILE?
#    This file, 'gui_main.py', is a core component of the Onyx Engine. It is
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
