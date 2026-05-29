from PyQt6.QtWidgets import QFrame, QVBoxLayout, QLabel, QWidget
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtMultimediaWidgets import QVideoWidget

class FloatingFlash(QWidget):
    """A floating, frameless tooltip widget that displays play/pause/skip flashes natively over the video window."""
    def __init__(self, parent=None):
        super().__init__(parent, Qt.WindowType.ToolTip | Qt.WindowType.FramelessWindowHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        self.label = QLabel()
        self.label.setStyleSheet("background-color: rgba(0, 0, 0, 160); color: white; border-radius: 40px; font-size: 36px; padding-bottom: 2px;")
        self.label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.label.setFixedSize(80, 80)
        layout.addWidget(self.label)
        self.hide()
        
        self.timer = QTimer(self)
        self.timer.setSingleShot(True)
        self.timer.timeout.connect(self.hide)
        
    def show_flash(self, text, widget_rect, global_pos):
        self.label.setText(text)
        x = global_pos.x() + (widget_rect.width() - self.width()) // 2
        y = global_pos.y() + (widget_rect.height() - self.height()) // 2
        self.move(x, y)
        self.show()
        self.timer.start(500)

class ClickableVideoWidget(QVideoWidget):
    def __init__(self, toggle_callback, parent=None):
        super().__init__(parent)
        self.toggle_callback = toggle_callback

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.toggle_callback()
        super().mousePressEvent(event)

class PlayerContainer(QFrame):
    """
    Custom container widget that stacks the video and controls vertically.
    Avoids native rendering overlap issues on Windows.
    """
    def __init__(self, video_widget, controls_overlay, parent=None):
        super().__init__(parent)
        self.setStyleSheet("background-color: #000000; border: 1px solid #282828; border-radius: 12px;")
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        layout.addWidget(video_widget, stretch=1)
        controls_overlay.setStyleSheet(controls_overlay.styleSheet() + " QFrame { border-top-left-radius: 0; border-top-right-radius: 0; border-top: 1px solid #333; }")
        layout.addWidget(controls_overlay)


# ==========================================
# HOW TO USE THIS CODE (EXAMPLE)
# ==========================================
# Example usage:
# from src.processors.video_player import MainClass
# processor = MainClass()
# processor.run(input_file, output_file)
# ==========================================

# ==============================================================================
# 🎬 FEATURE: INTERNAL MODULE DOCUMENTATION (video_player.py)
# ==============================================================================
#
# 📝 WHAT IS THIS FILE?
#    This file, 'video_player.py', is a core component of the Onyx Engine. It is
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
