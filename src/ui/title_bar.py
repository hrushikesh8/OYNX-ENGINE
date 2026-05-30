from PyQt6.QtWidgets import QWidget, QHBoxLayout, QLabel, QPushButton, QMenuBar, QMenu
from PyQt6.QtCore import Qt, QPoint

class CustomTitleBar(QWidget):
    """
    A custom frameless title bar with integrated menu bar and window controls,
    mimicking the professional look of VLC or VS Code.
    """
    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent
        self.layout = QHBoxLayout(self)
        self.layout.setContentsMargins(10, 0, 0, 0)
        self.layout.setSpacing(5)
        self.setFixedHeight(35)
        
        # Style the title bar background
        self.setStyleSheet("""
            QWidget {
                background-color: #1a1a1a;
                color: #ffffff;
            }
        """)

        # 1. Icon / Title
        self.icon_label = QLabel()
        import os, sys
        from PyQt6.QtGui import QPixmap
        base_path = getattr(sys, '_MEIPASS', os.path.abspath("."))
        logo_path = os.path.join(base_path, "assets", "onyx_logo.png")
        if os.path.exists(logo_path):
            pixmap = QPixmap(logo_path).scaled(22, 22, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
            self.icon_label.setPixmap(pixmap)
        else:
            self.icon_label.setText("💎")
        self.icon_label.setStyleSheet("margin-right: 5px;")
        
        self.title_label = QLabel("Onyx Engine v3.0")
        self.title_label.setStyleSheet("font-size: 12px; font-weight: bold; color: #aaaaaa;")

        # 2. Menu Bar
        self.menu_bar = QMenuBar(self)
        self.menu_bar.setStyleSheet("""
            QMenuBar {
                background-color: transparent;
                color: #eeeeee;
                font-size: 12px;
            }
            QMenuBar::item {
                background-color: transparent;
                padding: 4px 10px;
                border-radius: 4px;
            }
            QMenuBar::item:selected {
                background-color: rgba(255, 255, 255, 0.1);
            }
            QMenuBar::item:pressed {
                background-color: rgba(255, 255, 255, 0.2);
            }
            QMenu {
                background-color: #252525;
                color: white;
                border: 1px solid #333;
            }
            QMenu::item:selected {
                background-color: #2D72D9;
            }
        """)

        # --- FILE MENU ---
        file_menu = self.menu_bar.addMenu("File")
        file_menu.addAction("Dashboard", lambda: self.parent.update_nav_selection(getattr(self.parent, 'btn_dash', None), 0))
        file_menu.addAction("Settings", self.parent.open_settings_dialog)
        file_menu.addSeparator()
        file_menu.addAction("Exit", self.parent.close)

        # --- VIEW MENU ---
        view_menu = self.menu_bar.addMenu("View")
        view_menu.addAction("Toggle Sidebar", self.parent.toggle_sidebar)
        view_menu.addAction("Toggle Fullscreen", self.toggle_fullscreen)

        # --- TOOLS MENU ---
        tools_menu = self.menu_bar.addMenu("Tools")
        
        vid_menu = tools_menu.addMenu("Video & Formats")
        vid_menu.addAction("Format Converter", lambda: self.parent.update_nav_selection(None, 6))
        vid_menu.addAction("ABR Stream Ladder", lambda: self.parent.update_nav_selection(None, 7))
        
        edit_menu = tools_menu.addMenu("Editing & Splitting")
        edit_menu.addAction("Scene Sniper", lambda: self.parent.update_nav_selection(None, 8))
        edit_menu.addAction("Seamless Suture", lambda: self.parent.update_nav_selection(None, 9))
        edit_menu.addAction("Video Stitcher", lambda: self.parent.update_nav_selection(None, 10))
        edit_menu.addAction("Divider & Auto-Trim", lambda: self.parent.update_nav_selection(None, 11))
        edit_menu.addAction("Timeline Composer", lambda: self.parent.update_nav_selection(None, 19))
        
        audio_menu = tools_menu.addMenu("Audio & Subtitles")
        audio_menu.addAction("Audio Extractor", lambda: self.parent.update_nav_selection(None, 12))
        audio_menu.addAction("Audio Track Cleaner", lambda: self.parent.update_nav_selection(None, 13))
        audio_menu.addAction("Subtitle Track Cleaner", lambda: self.parent.update_nav_selection(None, 14))
        audio_menu.addAction("Stream Merger (Audio)", lambda: self.parent.update_nav_selection(None, 15))
        audio_menu.addAction("Subtitle Muxer", lambda: self.parent.update_nav_selection(None, 16))
        
        ai_menu = tools_menu.addMenu("AI & VFX")
        ai_menu.addAction("AI Remaster & Motion", lambda: self.parent.update_nav_selection(None, 17))
        ai_menu.addAction("VFX & Branding", lambda: self.parent.update_nav_selection(None, 18))
        
        log_menu = tools_menu.addMenu("Logistics")
        log_menu.addAction("Chronicle Organizer", lambda: self.parent.update_nav_selection(None, 20))
        log_menu.addAction("Logistics Hub", lambda: self.parent.update_nav_selection(getattr(self.parent, 'btn_logistics', None), 5))

        # --- QUEUE MENU ---
        queue_menu = self.menu_bar.addMenu("Queue")
        queue_menu.addAction("Cancel Active Job", self.parent.cancel_active_job_from_ui)

        # --- HELP MENU ---
        help_menu = self.menu_bar.addMenu("Help")
        help_menu.addAction("Read Documentation", self.open_docs)
        help_menu.addAction("About Onyx Engine", self.show_about)

        # 3. Window Controls (Minimize, Maximize, Close)
        self.btn_minimize = QPushButton("—")
        self.btn_maximize = QPushButton("◻")
        self.btn_close = QPushButton("✕")

        for btn in [self.btn_minimize, self.btn_maximize, self.btn_close]:
            btn.setFixedSize(45, 35)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            
        self.btn_minimize.setStyleSheet("QPushButton { background: transparent; border: none; font-size: 12px; } QPushButton:hover { background: rgba(255, 255, 255, 0.1); }")
        self.btn_maximize.setStyleSheet("QPushButton { background: transparent; border: none; font-size: 14px; } QPushButton:hover { background: rgba(255, 255, 255, 0.1); }")
        self.btn_close.setStyleSheet("QPushButton { background: transparent; border: none; font-size: 14px; } QPushButton:hover { background: #d92d2d; }")

        self.btn_minimize.clicked.connect(self.parent.showMinimized)
        self.btn_maximize.clicked.connect(self.toggle_maximize)
        self.btn_close.clicked.connect(self.parent.close)

        # Assemble Layout
        self.layout.addWidget(self.icon_label)
        self.layout.addWidget(self.title_label)
        self.layout.addSpacing(10)
        self.layout.addWidget(self.menu_bar)
        self.layout.addStretch()
        self.layout.addWidget(self.btn_minimize)
        self.layout.addWidget(self.btn_maximize)
        self.layout.addWidget(self.btn_close)

        # Variables for window dragging
        self.drag_position = QPoint()

    def toggle_maximize(self):
        if self.parent.isMaximized():
            self.parent.showNormal()
            self.btn_maximize.setText("◻")
        else:
            self.parent.showMaximized()
            self.btn_maximize.setText("❐")

    def toggle_fullscreen(self):
        if self.parent.isFullScreen():
            self.parent.showNormal()
            self.btn_maximize.setText("◻")
        else:
            self.parent.showFullScreen()
            self.btn_maximize.setText("❐")

    def open_docs(self):
        import os
        from PyQt6.QtGui import QDesktopServices
        from PyQt6.QtCore import QUrl
        doc_path = os.path.abspath("DOCUMENTATION.md")
        if os.path.exists(doc_path):
            QDesktopServices.openUrl(QUrl.fromLocalFile(doc_path))

    def show_about(self):
        from PyQt6.QtWidgets import QMessageBox
        from PyQt6.QtGui import QPixmap
        from PyQt6.QtCore import Qt
        import os
        msg = QMessageBox(self.parent)
        msg.setWindowTitle("About Onyx Engine")
        msg.setText("Onyx Engine v3.0\nProfessional Production Suite\n\nAdvanced tool for video, audio, and AI processing workflows.")
        msg.setStyleSheet("QMessageBox { background-color: #1e1e1e; color: white; } QLabel { color: white; } QPushButton { background-color: #333; color: white; padding: 5px 15px; }")
        
        import sys
        base_path = getattr(sys, '_MEIPASS', os.path.abspath("."))
        logo_path = os.path.join(base_path, "assets", "onyx_logo.png")
        if os.path.exists(logo_path):
            msg.setIconPixmap(QPixmap(logo_path).scaled(64, 64, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
        msg.exec()

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.drag_position = event.globalPosition().toPoint() - self.parent.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.MouseButton.LeftButton:
            self.parent.move(event.globalPosition().toPoint() - self.drag_position)
            event.accept()

    def mouseDoubleClickEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.toggle_maximize()
            event.accept()
