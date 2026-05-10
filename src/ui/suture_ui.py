from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
                             QLabel, QListWidget, QAbstractItemView)
from PyQt6.QtCore import Qt

# ==========================================
# CUSTOM WIDGET: REORDERABLE DRAG & DROP LIST
# ==========================================
class DragDropList(QListWidget):
    """A custom list that accepts dropped files and allows the user to reorder them."""
    def __init__(self):
        super().__init__()
        self.setAcceptDrops(True)
        # This magical setting allows the user to drag items up and down to reorder them!
        self.setDragDropMode(QAbstractItemView.DragDropMode.InternalMove)
        self.setStyleSheet("""
            QListWidget {
                background-color: #1e1e1e;
                border: 2px dashed #555555;
                border-radius: 8px;
                padding: 10px;
                font-size: 14px;
                color: #ffffff;
            }
            QListWidget::item { padding: 8px; border-bottom: 1px solid #333; }
            QListWidget::item:selected { background-color: #2D72D9; border-radius: 4px; }
        """)

    # 1. When a file hovers over the list
    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.accept()
        else:
            super().dragEnterEvent(event)

    # 2. When the file is moving around inside the list
    def dragMoveEvent(self, event):
        if event.mimeData().hasUrls():
            event.setDropAction(Qt.DropAction.CopyAction)
            event.accept()
        else:
            super().dragMoveEvent(event)

    # 3. When the user drops the file!
    def dropEvent(self, event):
        if event.mimeData().hasUrls():
            event.setDropAction(Qt.DropAction.CopyAction)
            event.accept()
            # Loop through all dropped files and add them to the list
            for url in event.mimeData().urls():
                if url.isLocalFile():
                    self.addItem(url.toLocalFile())
        else:
            super().dropEvent(event)


# ==========================================
# MAIN UI: SEAMLESS SUTURE SCREEN
# ==========================================
class SeamlessSutureUI(QWidget):
    """The Engine Room for Feature 7: Intelligent Movie Suture"""
    def __init__(self, back_callback):
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        # --- HEADER ---
        header_layout = QHBoxLayout()
        back_btn = QPushButton("⬅ Back to Dashboard")
        back_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        back_btn.setStyleSheet("padding: 8px; font-weight: bold; border-radius: 5px;")
        back_btn.clicked.connect(back_callback)
        
        title = QLabel(" 🧵 Seamless Suture")
        title.setStyleSheet("font-size: 22px; font-weight: bold;")
        
        header_layout.addWidget(back_btn)
        header_layout.addWidget(title)
        header_layout.addStretch()
        layout.addLayout(header_layout)
        layout.addSpacing(10)

        # --- MULTI-FILE LIST ---
        instruction = QLabel("Order your movie parts chronologically (Part 1, Part 2, etc.):")
        instruction.setStyleSheet("color: #aaaaaa; font-style: italic; margin-bottom: 5px;")
        layout.addWidget(instruction)

        self.file_list = DragDropList()
        self.file_list.setMinimumHeight(300)
        layout.addWidget(self.file_list)

        # --- LIST CONTROLS ---
        list_controls = QHBoxLayout()
        self.remove_btn = QPushButton("❌ Remove Selected")
        self.remove_btn.clicked.connect(self.remove_selected_item)
        self.clear_btn = QPushButton("🗑️ Clear All")
        self.clear_btn.clicked.connect(self.file_list.clear)

        list_controls.addWidget(self.remove_btn)
        list_controls.addWidget(self.clear_btn)
        list_controls.addStretch()
        layout.addLayout(list_controls)
        
        layout.addSpacing(20)

        # --- INTELLIGENT OPTIONS BOX ---
        options_frame = QFrame()
        options_frame.setStyleSheet("background-color: #1e1e1e; border-radius: 8px; padding: 10px;")
        options_layout = QVBoxLayout(options_frame)

        self.cv_toggle = QCheckBox(" Enable Auto-Detect Overlap (CV Mode)")
        self.cv_toggle.setChecked(True) # Enabled by default for intelligence
        self.cv_toggle.setStyleSheet("font-size: 14px; font-weight: bold; color: #2D72D9;")
        
        cv_desc = QLabel("Uses OpenCV to find the exact frame match between parts (prevents double scenes).")
        cv_desc.setStyleSheet("color: #888888; font-size: 12px; margin-left: 25px;")
        
        options_layout.addWidget(self.cv_toggle)
        options_layout.addWidget(cv_desc)
        layout.addWidget(options_frame)

        layout.addSpacing(30)

        # --- EXECUTION BUTTON ---
        self.exec_btn = QPushButton("⚡ Execute Seamless Suture")
        self.exec_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.exec_btn.setMinimumHeight(60)
        self.exec_btn.setStyleSheet("""
            QPushButton { font-size: 18px; font-weight: bold; background-color: #2D72D9; color: white; border-radius: 10px; }
            QPushButton:hover { background-color: #3a82ef; }
        """)
        self.exec_btn.clicked.connect(self.execute_suture)
        layout.addWidget(self.exec_btn)

    def remove_selected_item(self):
        for item in self.file_list.selectedItems():
            self.file_list.takeItem(self.file_list.row(item))

    def execute_suture(self):
        """Prepares the order and fires the backend processor."""
        count = self.file_list.count()
        if count < 2:
            print("[UI Warning] Suture requires at least 2 files.")
            return

        # 1. Gather files in UI order
        ordered_files = [self.file_list.item(i).text() for i in range(count)]
        
        # 2. Check the state of the CV toggle
        use_cv = self.cv_toggle.isChecked()

        # 3. Define the output path (Saves in the same folder as Part 1)
        base_dir = os.path.dirname(ordered_files[0])
        final_output = os.path.join(base_dir, "Onyx_Suture_Result.mp4")

        print(f"[UI] Sending {count} files to Suture Engine (CV Mode: {use_cv})")
        suture_merger.run_suture_workflow(ordered_files, final_output, use_cv)
            
        # TODO: Wire this to src.processors.seamless_suture.py next!