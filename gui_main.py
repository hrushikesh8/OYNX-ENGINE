import sys
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QPushButton, QLabel, QStackedWidget, 
                             QFrame, QGridLayout)
from PyQt6.QtCore import Qt
import qdarktheme
# Cleanly separated UI modules for each feature
# --- IMPORTING THE 5 CORE FEATURE UI MODULES ---
from src.ui.formats_ui import FormatConverterUI      # Feature 1
from src.ui.tracks_ui import TrackCleanerUI           # Feature 2 & 3
from src.ui.scene_sniper_ui import SceneSniperUI      # Feature 12
from src.ui.suture_ui import SeamlessSutureUI        # Feature 7

class MasterOrchestrator(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Onyx Engine v2.0") 
        self.resize(1200, 750)

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # 1. THE SIDEBAR
        sidebar = QFrame()
        sidebar.setFixedWidth(260)
        sidebar.setStyleSheet("background-color: #1e1e1e; border-right: 1px solid #333;")
        sidebar_layout = QVBoxLayout(sidebar)
        sidebar_layout.setContentsMargins(15, 20, 15, 20)

        brand_label = QLabel("ONYX ENGINE")
        brand_label.setStyleSheet("font-size: 24px; font-weight: 900; color: #ffffff; letter-spacing: 2px;")
        brand_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        sidebar_layout.addWidget(brand_label)
        sidebar_layout.addSpacing(30)

        self.btn_dashboard = self.create_nav_button("📊 Dashboard")
        self.btn_format = self.create_nav_button("🔄 Format & Map")
        self.btn_edit = self.create_nav_button("✂️ Edit & Divide")
        self.btn_audio = self.create_nav_button("🎵 Audio & Subs")
        self.btn_advanced = self.create_nav_button("⚙️ Advanced Intel")

        sidebar_layout.addWidget(self.btn_dashboard)
        sidebar_layout.addWidget(self.btn_format)
        sidebar_layout.addWidget(self.btn_edit)
        sidebar_layout.addWidget(self.btn_audio)
        sidebar_layout.addWidget(self.btn_advanced)
        sidebar_layout.addStretch()

        main_layout.addWidget(sidebar)

        # 2. THE WORKSPACE
        self.workspace = QStackedWidget()
        self.workspace.setStyleSheet("background-color: #121212;")
        main_layout.addWidget(self.workspace)

        # Initialize Views
        self.init_views()

        # Connect Navigation
        self.btn_dashboard.clicked.connect(lambda: self.workspace.setCurrentIndex(0))
        self.btn_edit.clicked.connect(lambda: self.workspace.setCurrentIndex(3))

    def create_nav_button(self, text):
        btn = QPushButton(text)
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        btn.setStyleSheet("""
            QPushButton {
                text-align: left; padding: 12px 15px; font-size: 15px; font-weight: bold; border-radius: 6px; color: #cccccc; background: transparent;
            }
            QPushButton:hover { background-color: #2a2a2a; color: #ffffff; }
        """)
        return btn

    def init_views(self):
        """
        Orchestrates the 'Deck of Cards' (The Workspace).
        Each index represents a unique screen in the Onyx Engine.
        """
        
        # --- INDEX 0: DASHBOARD ---
        dash_view = QLabel("Welcome to the Onyx Engine Dashboard.\nSelect a tool from the sidebar to begin.")
        dash_view.setAlignment(Qt.AlignmentFlag.AlignCenter)
        dash_view.setStyleSheet("font-size: 18px; color: #666;")
        self.workspace.addWidget(dash_view)

        # --- INDEX 1: FORMAT CONVERTER (FEATURE 1) ---
        self.format_ui = FormatConverterUI(back_callback=lambda: self.workspace.setCurrentIndex(0))
        self.workspace.addWidget(self.format_ui)

        # --- INDEX 2: EDIT & DIVIDE HUB (THE GRID) ---
        edit_menu = QWidget()
        edit_layout = QVBoxLayout(edit_menu)
        title_edit = QLabel("Edit & Divide Tools")
        title_edit.setStyleSheet("font-size: 28px; font-weight: bold; margin-bottom: 20px;")
        edit_layout.addWidget(title_edit)
        
        grid_edit = QGridLayout()
        # Card 12: Scene Sniper
        sniper_card = self.create_tool_card("🎯 Feature 12:\nScene Sniper", "Extract pristine clips.", 4)
        # Card 7: Seamless Suture
        suture_card = self.create_tool_card("🧵 Feature 7:\nSeamless Suture", "AI-Powered merging.", 5)
        
        grid_edit.addWidget(sniper_card, 0, 0)
        grid_edit.addWidget(suture_card, 0, 1)
        edit_layout.addLayout(grid_edit)
        edit_layout.addStretch()
        self.workspace.addWidget(edit_menu)

        # --- INDEX 3: AUDIO & SUBS HUB (THE GRID) ---
        audio_menu = QWidget()
        audio_layout = QVBoxLayout(audio_menu)
        title_audio = QLabel("Audio & Subtitle Tracks")
        title_audio.setStyleSheet("font-size: 28px; font-weight: bold; margin-bottom: 20px;")
        audio_layout.addWidget(title_audio)
        
        grid_audio = QGridLayout()
        # Card 2: Audio Cleaner
        audio_card = self.create_tool_card("🎵 Feature 2:\nAudio Cleaner", "Purge unwanted dubs.", 6)
        # Card 3: Subtitle Cleaner
        subs_card = self.create_tool_card("📝 Feature 3:\nSubtitle Cleaner", "Remove extra subs.", 7)
        
        grid_audio.addWidget(audio_card, 0, 0)
        grid_audio.addWidget(subs_card, 0, 1)
        audio_layout.addLayout(grid_audio)
        audio_layout.addStretch()
        self.workspace.addWidget(audio_menu)

        # --- THE TOOL SCREENS (REGISTERING THE MUSCLE) ---
        
        # Index 4: Scene Sniper
        self.sniper_ui = SceneSniperUI(back_callback=lambda: self.workspace.setCurrentIndex(2))
        self.workspace.addWidget(self.sniper_ui)

        # Index 5: Seamless Suture
        self.suture_ui = SeamlessSutureUI(back_callback=lambda: self.workspace.setCurrentIndex(2))
        self.workspace.addWidget(self.suture_ui)

        # Index 6: Audio Track Cleaner (Mode 'a')
        self.audio_ui = TrackCleanerUI(back_callback=lambda: self.workspace.setCurrentIndex(3), mode='a')
        self.workspace.addWidget(self.audio_ui)

        # Index 7: Subtitle Track Cleaner (Mode 's')
        self.subs_ui = TrackCleanerUI(back_callback=lambda: self.workspace.setCurrentIndex(3), mode='s')
        self.workspace.addWidget(self.subs_ui)

    def create_tool_card(self, title, desc, target_index):
        """Helper to create the big clickable buttons in the Hubs."""
        btn = QPushButton(f"{title}\n\n{desc}")
        btn.setMinimumSize(250, 150)
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        btn.setStyleSheet("""
            QPushButton { 
                background-color: #1e1e1e; border: 1px solid #333; border-radius: 12px; 
                font-size: 16px; font-weight: bold; padding: 15px; 
            }
            QPushButton:hover { border: 1px solid #2D72D9; background-color: #252525; }
        """)
        btn.clicked.connect(lambda: self.workspace.setCurrentIndex(target_index))
        return btn