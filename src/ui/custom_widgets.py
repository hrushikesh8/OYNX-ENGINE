import os
import subprocess
import threading
import re
from PyQt6.QtWidgets import QFrame, QHBoxLayout, QLineEdit, QPushButton, QFileDialog, QTextEdit, QMessageBox, QWidget, QVBoxLayout, QLabel, QSizePolicy, QProgressBar
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QPointF, QRectF
from PyQt6.QtGui import QPainter, QColor, QPolygonF, QBrush

# Monkeypatch subprocess.run to parse progress for any command launched in background threads
original_subprocess_run = subprocess.run

def custom_subprocess_run(cmd, *args, **kwargs):
    current_t = threading.current_thread()
    if isinstance(current_t, TaskWorker):
        return current_t.execute_subprocess_with_progress(cmd, *args, **kwargs)
    else:
        return original_subprocess_run(cmd, *args, **kwargs)

subprocess.run = custom_subprocess_run


class TaskWorker(QThread):
    """
    Asynchronous Worker Thread that executes FFmpeg commands or Python functions 
    in the background, preventing the UI from freezing.
    """
    log_signal = pyqtSignal(str)
    progress_signal = pyqtSignal(int)
    progress_update = pyqtSignal(int, str)
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
                
                # Run with progress tracking
                self.execute_subprocess_with_progress(cmd_list, check=True)
                self.finished_signal.emit(True, "Process completed successfully.")
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

    def execute_subprocess_with_progress(self, cmd, *args, **kwargs):
        """
        Executes a subprocess, reads its stdout line-by-line in real-time,
        and parses FFmpeg logs for duration and current progress to calculate
        remaining time (countdown/estimates).
        """
        cmd_list = [str(x) for x in cmd]
        
        # Setup startupinfo to hide CMD window on Windows
        startupinfo = None
        if os.name == 'nt':
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            startupinfo.wShowWindow = subprocess.SW_HIDE
            
        self.process = subprocess.Popen(
            cmd_list,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
            startupinfo=startupinfo,
            encoding='utf-8',
            errors='replace'
        )
        
        stdout_lines = []
        
        # Regex parsers for FFmpeg progress logs
        duration_sec = None
        duration_regex = re.compile(r"Duration:\s*(\d{2}):(\d{2}):(\d{2})\.(\d{2})")
        time_regex = re.compile(r"time=\s*(\d{2}):(\d{2}):(\d{2})\.(\d{2})")
        speed_regex = re.compile(r"speed=\s*([\d\.]+)x")
        
        while True:
            line = self.process.stdout.readline()
            if not line and self.process.poll() is not None:
                break
            if line:
                stdout_lines.append(line)
                self.log_signal.emit(line)
                
                # 1. Parse total video duration
                if duration_sec is None:
                    dur_match = duration_regex.search(line)
                    if dur_match:
                        h, m, s, ms = map(int, dur_match.groups())
                        duration_sec = h * 3600 + m * 60 + s + ms / 100.0
                
                # 2. Parse current elapsed encode time and processing speed
                if duration_sec:
                    time_match = time_regex.search(line)
                    if time_match:
                        h, m, s, ms = map(int, time_match.groups())
                        current_sec = h * 3600 + m * 60 + s + ms / 100.0
                        
                        # Calculate progress percentage
                        pct = int((current_sec / duration_sec) * 100)
                        pct = min(100, max(0, pct))
                        
                        # Parse speed to calculate remaining time countdown
                        speed = 1.0
                        speed_match = speed_regex.search(line)
                        if speed_match:
                            try:
                                speed = float(speed_match.group(1))
                            except ValueError:
                                speed = 1.0
                                
                        if speed > 0.01:
                            remaining_sec = (duration_sec - current_sec) / speed
                        else:
                            remaining_sec = duration_sec - current_sec
                        
                        remaining_sec = max(0, remaining_sec)
                        
                        # Format countdown display text
                        if remaining_sec > 3600:
                            rem_h = int(remaining_sec // 3600)
                            rem_m = int((remaining_sec % 3600) // 60)
                            rem_txt = f"{rem_h}h {rem_m}m left"
                        elif remaining_sec > 60:
                            rem_m = int(remaining_sec // 60)
                            rem_s = int(remaining_sec % 60)
                            rem_txt = f"{rem_m}m {rem_s}s left"
                        else:
                            rem_txt = f"{int(remaining_sec)}s left"
                            
                        status_str = f"Running ({pct}% | {rem_txt})"
                        self.progress_update.emit(pct, status_str)
                        self.progress_signal.emit(pct)

        return_code = self.process.wait()
        stdout_bytes = "".join(stdout_lines).encode('utf-8', errors='replace')
        
        if kwargs.get('check', False) and return_code != 0:
            raise subprocess.CalledProcessError(return_code, cmd_list, output=stdout_bytes, stderr=None)
            
        return subprocess.CompletedProcess(cmd_list, return_code, stdout_bytes, None)

    def cancel(self):
        """Immediately kill the underlying subprocess if it exists."""
        if hasattr(self, 'process') and self.process and self.process.poll() is None:
            try:
                if os.name == 'nt':
                    subprocess.run(['taskkill', '/F', '/T', '/PID', str(self.process.pid)], capture_output=True)
                else:
                    self.process.terminate()
            except Exception as e:
                print(f"Error killing process: {e}")
            self.finished_signal.emit(False, "Task was explicitly canceled by the user.")

class EstimateWorker(QThread):
    estimation_done = pyqtSignal(str, int)
    
    def __init__(self, input_paths, speed_multiplier=1.0):
        super().__init__()
        if isinstance(input_paths, str):
            self.input_paths = [input_paths]
        else:
            self.input_paths = input_paths
        self.speed_multiplier = speed_multiplier
        
    def run(self):
        import glob
        files_to_probe = []
        for path in self.input_paths:
            if not path:
                continue
            if os.path.isdir(path):
                extensions = ('*.mp4', '*.mkv', '*.avi', '*.mov', '*.flv', '*.wmv', '*.mpg', '*.mpeg', '*.webm')
                for ext in extensions:
                    files_to_probe.extend(glob.glob(os.path.join(path, '**', ext), recursive=True))
            elif os.path.isfile(path):
                files_to_probe.append(path)
            
        if not files_to_probe:
            self.estimation_done.emit("Error: No media found", 0)
            return

        total_seconds = 0
        for file_path in files_to_probe:
            cmd = ['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'default=noprint_wrappers=1:nokey=1', file_path]
            try:
                startupinfo = None
                if os.name == 'nt':
                    startupinfo = subprocess.STARTUPINFO()
                    startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
                    startupinfo.wShowWindow = subprocess.SW_HIDE
                result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, startupinfo=startupinfo, timeout=5)
                if result.stdout.strip():
                    total_seconds += float(result.stdout.strip())
            except Exception:
                continue

        if total_seconds == 0:
            self.estimation_done.emit("Unable to estimate", 0)
            return

        estimated_seconds = total_seconds / self.speed_multiplier
        
        if estimated_seconds > 3600:
            rem_h = int(estimated_seconds // 3600)
            rem_m = int((estimated_seconds % 3600) // 60)
            est_str = f"~{rem_h}h {rem_m}m"
        elif estimated_seconds > 60:
            rem_m = int(estimated_seconds // 60)
            rem_s = int(estimated_seconds % 60)
            est_str = f"~{rem_m}m {rem_s}s"
        else:
            est_str = f"~{int(estimated_seconds)}s"

        self.estimation_done.emit(est_str, int(estimated_seconds))

class SmartRunButton(QPushButton):
    """
    A universal 2-stage run button that natively calculates estimated job duration
    before allowing the user to confirm.
    """
    def __init__(self, text, get_input_paths_callback, on_confirm_callback, speed_multiplier=1.0):
        super().__init__(text)
        self.original_text = text
        self.get_input_paths_callback = get_input_paths_callback
        self.on_confirm_callback = on_confirm_callback
        self.speed_multiplier = speed_multiplier
        self.est_seconds = 0
        
        self.setMinimumHeight(60)
        self.setStyleSheet("""
            QPushButton { background-color: #2D72D9; color: white; font-size: 18px; font-weight: bold; border-radius: 8px; }
            QPushButton:hover { background-color: #3a82ef; }
        """)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.clicked.connect(self.handle_click)

    def handle_click(self):
        if self.text() == self.original_text:
            paths = self.get_input_paths_callback()
            if not paths:
                return # Validation failed or handled by parent UI
            
            self.current_inputs = paths
                
            self.setText("⏳ Estimating...")
            self.setEnabled(False)
            
            multiplier = self.speed_multiplier() if callable(self.speed_multiplier) else self.speed_multiplier
            self.worker = EstimateWorker(paths, multiplier)
            self.worker.estimation_done.connect(self.on_est_done)
            self.worker.start()
            
        elif self.text().startswith("✅ Confirm"):
            self.setText(self.original_text)
            self.setStyleSheet("""
                QPushButton { background-color: #2D72D9; color: white; font-size: 18px; font-weight: bold; border-radius: 8px; }
                QPushButton:hover { background-color: #3a82ef; }
            """)
            self.on_confirm_callback(self.current_inputs, self.est_seconds)
            
    def on_est_done(self, est_str, est_seconds):
        self.setEnabled(True)
        self.est_seconds = est_seconds
        if est_str.startswith("Error"):
            self.setText(self.original_text)
        else:
            self.setText(f"✅ Confirm Run (Est. {est_str})")
            self.setStyleSheet("""
                QPushButton { background-color: #28a745; color: white; font-size: 18px; font-weight: bold; border-radius: 8px; }
                QPushButton:hover { background-color: #218838; }
            """)

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
        self.setMinimumHeight(60)
        
        self.default_style = """
            QFrame { 
                border: 2px dashed #444; 
                border-radius: 10px; 
                background-color: #1a1a1a; 
            }
            QFrame:hover {
                border: 2px dashed #555;
                background-color: #1e1e1e;
            }
        """
        self.active_style = """
            QFrame { 
                border: 2px dashed #2D72D9; 
                border-radius: 10px; 
                background-color: rgba(45, 114, 217, 0.1); 
            }
        """
        self.setStyleSheet(self.default_style)
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(15, 10, 15, 10)
        layout.setSpacing(10)

        self.file_input = QLineEdit()
        placeholder = "⏬ Drag & Drop a video file here, paste path, or click Browse..." if mode == 'file' else "⏬ Drag & Drop a folder here, paste path, or click Browse..."
        self.file_input.setPlaceholderText(placeholder)
        self.file_input.setStyleSheet("border: none; background: transparent; font-size: 14px; font-weight: bold; color: #ffffff;")
        self.file_input.setMinimumHeight(40)
        
        layout.addWidget(self.file_input)
        
        if self.mode == 'both':
            browse_file_btn = QPushButton("📄 File")
            browse_dir_btn = QPushButton("📁 Folder")
            for btn in [browse_file_btn, browse_dir_btn]:
                btn.setCursor(Qt.CursorShape.PointingHandCursor)
                btn.setFixedHeight(35)
                btn.setStyleSheet("""
                    QPushButton { background-color: #2b2b2b; border: 1px solid #444; border-radius: 5px; padding: 0 15px; font-weight: bold; color: #eee; } 
                    QPushButton:hover { background-color: #3D72D9; border-color: #2D72D9; color: white; }
                """)
            browse_file_btn.clicked.connect(lambda: self.browse_path('file'))
            browse_dir_btn.clicked.connect(lambda: self.browse_path('dir'))
            layout.addWidget(browse_file_btn)
            layout.addWidget(browse_dir_btn)
        else:
            browse_btn = QPushButton("📁 Browse")
            browse_btn.setCursor(Qt.CursorShape.PointingHandCursor)
            browse_btn.setFixedHeight(35)
            browse_btn.setStyleSheet("""
                QPushButton { background-color: #2b2b2b; border: 1px solid #444; border-radius: 5px; padding: 0 15px; font-weight: bold; color: #eee; } 
                QPushButton:hover { background-color: #3D72D9; border-color: #2D72D9; color: white; }
            """)
            browse_btn.clicked.connect(lambda: self.browse_path(self.mode))
            layout.addWidget(browse_btn)

    def browse_path(self, override_mode=None):
        from PyQt6.QtCore import QTimer
        # Defer the dialog opening by 10ms to let the button click event finish.
        # This prevents a legendary Windows COM OLE deadlock that happens when 
        # a native dialog is launched directly from a widget with setAcceptDrops(True).
        QTimer.singleShot(10, lambda: self._execute_dialog(override_mode))

    def _execute_dialog(self, override_mode):
        import os
        import sys
        from PyQt6.QtWidgets import QFileDialog
        
        mode_to_use = override_mode if override_mode else self.mode
        start_dir = getattr(sys, '_onyx_last_dir', os.path.expanduser("~\\Desktop"))
        
        # Temporarily disable drops to guarantee no OLE conflicts
        self.setAcceptDrops(False)
        sys._onyx_dialog_active = True  # Tell background timers to pause
        try:
            if mode_to_use == 'dir':
                folder_name = QFileDialog.getExistingDirectory(self.window(), "Select Folder", start_dir)
                if folder_name:
                    sys._onyx_last_dir = folder_name
                    self.file_input.setText(folder_name)
            else:
                file_name, _ = QFileDialog.getOpenFileName(self.window(), "Select File", start_dir, "Video/Audio Files (*.mp4 *.mkv *.avi *.mov *.mp3 *.wav *.srt *.ass *.zip);;All Files (*)")
                if file_name:
                    sys._onyx_last_dir = os.path.dirname(file_name)
                    self.file_input.setText(file_name)
        finally:
            self.setAcceptDrops(True)
            sys._onyx_dialog_active = False

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

class VLCVolumeSlider(QWidget):
    """
    Custom widget that precisely mimics the VLC media player volume wedge.
    """
    valueChanged = pyqtSignal(int)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumSize(100, 20)
        self.setMaximumSize(140, 25)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self._value = 100
        
    def value(self):
        return self._value
        
    def setValue(self, val):
        val = max(0, min(200, val))
        if self._value != val:
            self._value = val
            self.valueChanged.emit(self._value)
            self.update()
            
    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._update_value_from_pos(event.position().x())
        
    def mouseMoveEvent(self, event):
        if event.buttons() & Qt.MouseButton.LeftButton:
            self._update_value_from_pos(event.position().x())
        
    def _update_value_from_pos(self, x):
        offset_x = 35
        wedge_w = self.width() - offset_x
        if wedge_w <= 0: return
        x_in_wedge = x - offset_x
        pct = x_in_wedge / wedge_w
        self.setValue(int(pct * 200))
        
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        w = self.width()
        h = self.height()
        offset_x = 35
        wedge_w = w - offset_x
        
        # Draw text on the left
        painter.setPen(QColor(200, 200, 200))
        text = f"{self._value}%"
        font = painter.font()
        font.setPointSize(9)
        painter.setFont(font)
        painter.drawText(0, 0, 30, h, Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter, text)
        
        if wedge_w <= 0: return
        
        # The wedge polygon (triangle)
        poly = QPolygonF([
            QPointF(offset_x, h),
            QPointF(w, h),
            QPointF(w, 0)
        ])
        
        # Draw background wedge
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QBrush(QColor(60, 60, 60)))
        painter.drawPolygon(poly)
        
        # Draw filled wedge
        fill_w = wedge_w * (self._value / 200.0)
        painter.setClipRect(QRectF(offset_x, 0, fill_w, h))
        painter.setBrush(QBrush(QColor(0, 200, 0))) # VLC green
        painter.drawPolygon(poly)

# ==========================================
# HOW TO USE THIS CODE (EXAMPLE)
# ==========================================
# Example usage:
# from src.processors.custom_widgets import MainClass
# processor = MainClass()
# processor.run(input_file, output_file)
# ==========================================

# ==============================================================================
# 🎬 FEATURE: INTERNAL MODULE DOCUMENTATION (custom_widgets.py)
# ==============================================================================
#
# 📝 WHAT IS THIS FILE?
#    This file, 'custom_widgets.py', is a core component of the Onyx Engine. It is
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
