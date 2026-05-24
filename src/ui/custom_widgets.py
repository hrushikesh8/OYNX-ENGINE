import os
import subprocess
from PyQt6.QtWidgets import QFrame, QHBoxLayout, QLineEdit, QPushButton, QFileDialog, QTextEdit
from PyQt6.QtCore import Qt, QThread, pyqtSignal

class TaskWorker(QThread):
    """
    Asynchronous Worker Thread that executes FFmpeg commands or Python functions 
    in the background, preventing the UI from freezing.
    """
    log_signal = pyqtSignal(str)
    progress_signal = pyqtSignal(int)
    finished_signal = pyqtSignal(bool, str)

    def __init__(self, func_or_cmd, *args, **kwargs):
        super().__init__()
        self.func_or_cmd = func_or_cmd
        self.args = args
        self.kwargs = kwargs
        # Detect if it's a list of arguments for subprocess, or a Python callable
        self.is_command = isinstance(func_or_cmd, list)

    def run(self):
        if self.is_command:
            try:
                # Stringify arguments for displaying
                cmd_str = " ".join(str(x) for x in self.func_or_cmd)
                self.log_signal.emit(f"⚡ [Onyx Exec] Starting: {cmd_str}\n\n")
                
                # Make sure all elements in the command are stringified
                cmd_list = [str(x) for x in self.func_or_cmd]
                
                # Start subprocess with no console window on Windows to keep it neat
                startupinfo = None
                if os.name == 'nt':
                    startupinfo = subprocess.STARTUPINFO()
                    startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
                    startupinfo.wShowWindow = subprocess.SW_HIDE

                process = subprocess.Popen(
                    cmd_list,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True,
                    bufsize=1,
                    startupinfo=startupinfo,
                    encoding='utf-8',
                    errors='replace'
                )

                while True:
                    line = process.stdout.readline()
                    if not line and process.poll() is not None:
                        break
                    if line:
                        self.log_signal.emit(line)
                        
                return_code = process.wait()
                if return_code == 0:
                    self.finished_signal.emit(True, "Process completed successfully.")
                else:
                    self.finished_signal.emit(False, f"Process exited with code {return_code}.")
            except Exception as e:
                self.finished_signal.emit(False, f"Subprocess Error: {str(e)}")
        else:
            try:
                self.log_signal.emit("⚡ [Onyx Task] Starting Python script worker...\n")
                # Redirect stdout for Python callables if possible or execute directly
                result = self.func_or_cmd(*self.args, **self.kwargs)
                if isinstance(result, tuple) and len(result) > 0:
                    success = result[0]
                    msg = result[1] if len(result) > 1 else "Task finished."
                    self.finished_signal.emit(bool(success), str(msg))
                else:
                    success = result if isinstance(result, bool) else True
                    self.finished_signal.emit(success, "Task finished.")
            except Exception as e:
                self.finished_signal.emit(False, f"Python Task Error: {str(e)}")

class ConsoleLogger(QTextEdit):
    """A premium styled terminal console emulator for output logs."""
    def __init__(self):
        super().__init__()
        self.setReadOnly(True)
        self.setStyleSheet("""
            QTextEdit {
                background-color: #0b0b0b;
                color: #00ff66;
                font-family: 'Consolas', 'Monaco', 'Courier New', monospace;
                font-size: 13px;
                border: 1px solid #282828;
                border-radius: 6px;
                padding: 10px;
            }
        """)

    def append_log(self, text):
        self.insertPlainText(text)
        self.ensureCursorVisible()

class DropZone(QFrame):
    """A custom file/folder input zone that supports Drag/Drop, Browsing, and Pasting."""
    def __init__(self, parent_ui, mode='file'):
        super().__init__()
        self.parent_ui = parent_ui 
        self.mode = mode  # 'file' or 'dir'
        self.setAcceptDrops(True)  
        
        self.default_style = "QFrame { border: 2px dashed #3a3a3a; border-radius: 8px; background-color: #161616; }"
        self.active_style = "QFrame { border: 2px dashed #2D72D9; border-radius: 8px; background-color: #172436; }"
        self.setStyleSheet(self.default_style)
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)

        self.file_input = QLineEdit()
        placeholder = "Drag & Drop a video file here, paste path, or click Browse..." if mode == 'file' else "Drag & Drop a folder here, paste path, or click Browse..."
        self.file_input.setPlaceholderText(placeholder)
        self.file_input.setStyleSheet("border: none; background: transparent; font-size: 14px; color: #ffffff;")
        self.file_input.setMinimumHeight(35)
        
        browse_btn = QPushButton("📁 Browse")
        browse_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        browse_btn.setStyleSheet("""
            QPushButton { background-color: #2b2b2b; border: 1px solid #3c3c3c; border-radius: 5px; padding: 8px 15px; font-weight: bold; color: #eee; } 
            QPushButton:hover { background-color: #3a3a3a; border-color: #555; }
        """)
        browse_btn.clicked.connect(self.browse_path)
        
        layout.addWidget(self.file_input)
        layout.addWidget(browse_btn)

    def browse_path(self):
        if self.mode == 'dir':
            folder_name = QFileDialog.getExistingDirectory(self, "Select Folder", "")
            if folder_name:
                self.file_input.setText(folder_name)
        else:
            file_name, _ = QFileDialog.getOpenFileName(self, "Select File", "", "Video/Audio Files (*.mp4 *.mkv *.avi *.mov *.mp3 *.wav *.srt *.ass *.zip);;All Files (*)")
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
            target_path = files[0]
            # Ensure path matching mode
            if self.mode == 'dir' and not os.path.isdir(target_path):
                target_path = os.path.dirname(target_path)
            self.file_input.setText(target_path)