import os
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
                             QLabel, QListWidget, QAbstractItemView, QCheckBox, 
                             QFrame, QFileDialog)
from PyQt6.QtCore import Qt
from src.processors import suture_merger

class DragDropList(QListWidget):
    """A custom ListWidget that acts as a giant Drag & Drop zone."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAcceptDrops(True)
        self.setDragEnabled(True)
        self.setDragDropMode(QAbstractItemView.DragDropMode.InternalMove)
        self.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        
        # Professional Styling: Dashed border to indicate it's a Drop Zone
        self.setStyleSheet("""
            QListWidget {
                background-color: #161616;
                border: 2px dashed #333;
                border-radius: 10px;
                color: #eee;
                font-size: 14px;
                padding: 10px;
            }
            QListWidget:hover { border: 2px dashed #2D72D9; }
            QListWidget::item { 
                background-color: #1e1e1e; 
                margin-bottom: 5px; 
                padding: 10px; 
                border-radius: 5px; 
            }
            QListWidget::item:selected { background-color: #2D72D9; color: white; }
        """)

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.accept()
        else:
            super().dragEnterEvent(event)

    def dragMoveEvent(self, event):
        if event.mimeData().hasUrls():
            event.accept()
        else:
            super().dragMoveEvent(event)

    def dropEvent(self, event):
        if event.mimeData().hasUrls():
            event.setDropAction(Qt.DropAction.CopyAction)
            event.accept()
            for url in event.mimeData().urls():
                file_path = str(url.toLocalFile())
                if file_path.lower().endswith(('.mp4', '.mkv', '.avi', '.mov')):
                    self.addItem(file_path)
        else:
            # Handle internal re-ordering
            super().dropEvent(event)

class SeamlessSutureUI(QWidget):
    def __init__(self, back_callback):
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        # --- HEADER ---
        header_layout = QHBoxLayout()
        
        # Neat Back Button
        back_btn = QPushButton(" ←  Back")
        back_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        back_btn.setStyleSheet("""
            QPushButton { background-color: #252525; border: 1px solid #333; border-radius: 6px; 
                          color: #bbb; padding: 6px 12px; font-weight: bold; }
            QPushButton:hover { background-color: #333; color: white; }
        """)
        back_btn.clicked.connect(back_callback)
        
        title = QLabel(" 🧵 Seamless Suture")
        title.setStyleSheet("font-size: 22px; font-weight: bold; color: white;")
        
        header_layout.addWidget(back_btn)
        header_layout.addSpacing(15)
        header_layout.addWidget(title)
        header_layout.addStretch()
        layout.addLayout(header_layout)

        # --- THE DRAG & DROP LIST (The main engine) ---
        layout.addSpacing(10)
        layout.addWidget(QLabel("Drag video files directly into the box below or use Add Files:"))
        
        self.file_list = DragDropList() # This is your Drag & Drop option
        self.file_list.setMinimumHeight(350)
        layout.addWidget(self.file_list)

        # --- CONTROLS ---
        list_controls = QHBoxLayout()
        
        self.browse_btn = QPushButton("➕ Add Files")
        self.browse_btn.clicked.connect(self.browse_files)
        
        self.remove_btn = QPushButton("❌ Remove Selected")
        self.remove_btn.clicked.connect(self.remove_selected_item)
        
        self.clear_btn = QPushButton("🗑️ Clear All")
        self.clear_btn.clicked.connect(self.file_list.clear)

        for btn in [self.browse_btn, self.remove_btn, self.clear_btn]:
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.setStyleSheet("background-color: #252525; border-radius: 4px; padding: 8px 15px; font-weight: bold;")
        
        list_controls.addWidget(self.browse_btn)
        list_controls.addWidget(self.remove_btn)
        list_controls.addWidget(self.clear_btn)
        list_controls.addStretch()
        layout.addLayout(list_controls)

        # --- OPTIONS ---
        layout.addSpacing(20)
        options_frame = QFrame()
        options_frame.setStyleSheet("background-color: #1a1a1a; border: 1px solid #222; border-radius: 8px; padding: 15px;")
        options_layout = QVBoxLayout(options_frame)

        self.cv_toggle = QCheckBox(" Enable Auto-Detect Overlap (CV Mode)")
        self.cv_toggle.setChecked(True)
        self.cv_toggle.setStyleSheet("font-size: 15px; font-weight: bold; color: #2D72D9;")
        
        cv_desc = QLabel("Uses OpenCV to find the exact frame match (removes duplicate scenes).")
        cv_desc.setStyleSheet("color: #777; font-size: 13px; margin-left: 28px;")
        
        options_layout.addWidget(self.cv_toggle)
        options_layout.addWidget(cv_desc)
        layout.addWidget(options_frame)

        # --- EXECUTE ---
        layout.addStretch()
        self.exec_btn = QPushButton("⚡ Execute Seamless Suture")
        self.exec_btn.setMinimumHeight(60)
        self.exec_btn.setStyleSheet("""
            QPushButton { font-size: 18px; font-weight: bold; background-color: #2D72D9; color: white; border-radius: 10px; }
            QPushButton:hover { background-color: #3a82ef; }
        """)
        self.exec_btn.clicked.connect(self.execute_suture)
        layout.addWidget(self.exec_btn)

    def browse_files(self):
        files, _ = QFileDialog.getOpenFileNames(self, "Select Video Parts", "", "Video Files (*.mp4 *.mkv *.avi)")
        if files:
            for f in files: self.file_list.addItem(f)

    def remove_selected_item(self):
        for item in self.file_list.selectedItems():
            self.file_list.takeItem(self.file_list.row(item))

    def execute_suture(self):
        count = self.file_list.count()
        if count < 2: return
        
        ordered_files = [self.file_list.item(i).text() for i in range(count)]
        use_cv = self.cv_toggle.isChecked()
        
        # Smart output naming
        base_dir = os.path.dirname(ordered_files[0])
        final_output = os.path.join(base_dir, "Onyx_Suture_Result.mp4")

        # Remember: Check if your processor function is 'run_suture_workflow' or 'execute_suture'
        suture_merger.run_suture_workflow(ordered_files, final_output, use_cv)