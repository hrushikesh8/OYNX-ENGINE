from PyQt6.QtWidgets import QFrame, QHBoxLayout, QLineEdit, QPushButton, QFileDialog
from PyQt6.QtCore import Qt

class DropZone(QFrame):
    """A custom Triple-Threat file input zone: Drag/Drop, Browse, or Paste."""
    def __init__(self, parent_ui):
        super().__init__()
        self.parent_ui = parent_ui 
        self.setAcceptDrops(True)  
        
        self.default_style = "QFrame { border: 2px dashed #555555; border-radius: 8px; background-color: #1e1e1e; }"
        self.active_style = "QFrame { border: 2px dashed #2D72D9; border-radius: 8px; background-color: #253347; }"
        self.setStyleSheet(self.default_style)
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)

        self.file_input = QLineEdit()
        self.file_input.setPlaceholderText("Drag & Drop a video file here, paste a path, or click Browse...")
        self.file_input.setStyleSheet("border: none; background: transparent; font-size: 14px; color: #ffffff;")
        self.file_input.setMinimumHeight(35)
        
        browse_btn = QPushButton("📁 Browse")
        browse_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        browse_btn.setStyleSheet("QPushButton { background-color: #3a3a3a; border-radius: 5px; padding: 8px 15px; font-weight: bold; } QPushButton:hover { background-color: #4a4a4a; }")
        browse_btn.clicked.connect(self.browse_file)
        
        layout.addWidget(self.file_input)
        layout.addWidget(browse_btn)

    def browse_file(self):
        file_name, _ = QFileDialog.getOpenFileName(self, "Select Movie File", "", "Video Files (*.mp4 *.mkv)")
        if file_name:
            self.file_input.setText(file_name)

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.accept()
            self.setStyleSheet(self.active_style) 
        else:
            event.ignore()

    def dragLeaveEvent(self, event):
        self.setStyleSheet(self.default_style)

    def dropEvent(self, event):
        self.setStyleSheet(self.default_style) 
        files = [u.toLocalFile() for u in event.mimeData().urls()]
        if files:
            self.file_input.setText(files[0])