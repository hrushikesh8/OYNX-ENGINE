# Onyx Engine: Architecture & Processes Documentation

This document provides a comprehensive explanation of the internal workings, processes, and architecture of the **Onyx Engine**. The application combines a responsive Python/PyQt6 graphical interface with the sheer processing power of FFmpeg via asynchronous subprocess execution.

## 🏗️ System Architecture Overview

The Onyx Engine follows a decoupled architecture, separating the **Frontend (UI)** from the **Backend (Processors)**.

1.  **Frontend (`gui_main.py` & `src/ui/`)**: Built using PyQt6. It handles all user interactions, file drag-and-drops, configuration selections, and visual feedback (Progress Bars, ETAs). It manages a `QStackedWidget` to seamlessly switch between different tool screens.
2.  **Backend (`src/processors/`)**: A collection of isolated Python modules. Each module is responsible for constructing precise, complex FFmpeg/FFprobe commands based on the parameters passed from the UI.
3.  **The Execution Layer**: UI components spawn backend processor commands asynchronously using `subprocess.Popen` or `QProcess`. The standard output/error streams are parsed in real-time to extract timecodes and progress, feeding this data back to the UI to update progress bars and ETAs.

---

## 🧠 Core Processing Modules

### 1. Multi-Track Timeline Composer (`timeline_composer.py`)
This is the most advanced module in the engine, replicating a non-linear video editor (NLE). 
*   **Process**: It receives a JSON payload or structured list containing video clips (with trim-in, trim-out, color grading metrics, and speeds), multiple audio tracks (with volume and delay offset), and global settings (target resolution/aspect ratio).
*   **Media Analysis**: Uses `ffprobe` to determine the original resolutions and framerates of all input clips.
*   **Filter Graph Generation (`-filter_complex`)**: 
    *   **Video Chain**: Each video clip is independently trimmed (`trim`), scaled and center-cropped (`scale` and `crop` to match 16:9, 9:16, or 1:1), color-graded (`eq` for brightness, contrast, saturation), and speed-adjusted (`setpts`). All clips are then concatenated (`concat`).
    *   **Audio Chain**: The background audio tracks are delayed to start at user-specified timestamps (`adelay`), adjusted for volume (`volume`), and mixed together (`amix`). The mixed background audio is then mapped alongside the concatenated video.
*   **Output**: A highly produced, single continuous MP4 file suitable for social media or cinematic viewing.

### 2. Auto-Shorts Editor (`editor.py`)
*   **Process**: Converts horizontal (16:9) video into vertical (9:16) format.
*   **Filter Graph**: It duplicates the video stream into two paths. 
    1.  *Background Path*: Scaled to fill the vertical frame, heavily blurred (`boxblur`), and darkened.
    2.  *Foreground Path*: Scaled to fit horizontally, maintaining aspect ratio.
    The foreground is overlaid onto the blurred background.

### 3. Scene Sniper / Division (`division.py`)
*   **Process**: Splitting massive files cleanly without quality loss (where possible).
*   **Mechanism**: Uses FFmpeg's `-ss` (start time) and `-t` (duration) flags. When combined with `-c copy`, this performs stream copying, instantly slicing the file along keyframes without re-encoding.

### 4. Media Remastering (`remaster.py`)
*   **Process**: Upgrading vintage or low-quality video.
*   **Mechanism**: Applies a complex filter chain: `hqdn3d` (high-quality 3D denoise), `unsharp` (sharpening), `scale` (Lanczos upscaling to 1080p), and `colorlevels` or `eq` to correct faded colors. Requires heavy re-encoding (`libx264`).

### 5. Chronicle Organizer (`omni_sorter.py`, `file_manager.py`)
*   **Process**: Automates media library logistics by taking a messy dump folder of videos and organizing them into standard Plex/Jellyfin structured hierarchies.
*   **Mechanism**: Uses advanced regex (`re`) to parse TV show titles, seasons, and episode numbers. It connects to the internet via the `requests` library to ping the TMDB API, resolving show IDs and scraping real episode titles. Finally, it uses `shutil` and `os` commands to safely move and rename massive files without data loss.

### 6. Seamless Suture & Stream Ladder (`seamless_suture.py`, `ladder.py`)
*   **Process**: Advanced video compositing and stitching. Suture creates dynamic multi-clip compilations, while Ladder aligns videos side-by-side (like a stream ladder).
*   **Mechanism**: Heavily utilizes FFmpeg's `-filter_complex` with `hstack`, `vstack`, and `pad` filters. It synchronizes multiple audio tracks and provides the user with independent VLC-style visual volume controls on the frontend.

### 7. Extraction & Tracks (`extractor.py`, `tracks.py`)
*   **Process**: Ripping audio or isolating specific streams (audio/subtitles).
*   **Mechanism**: Uses `ffprobe` to map all streams. FFmpeg's `-map` flag is then heavily utilized to select specific streams (e.g., `-map 0:a:1` to select the second audio track). For extraction, it encodes to requested formats (MP3 `libmp3lame`, FLAC `flac`). For stripping, it uses `-c copy` to repackage the container without the unwanted streams.

### 8. Seamless Stitcher (`stitcher.py`)
*   **Process**: Joining multiple clips sequentially without re-encoding.
*   **Mechanism**: Employs FFmpeg's "concat demuxer". It generates a temporary `mylist.txt` file listing the file paths in order. FFmpeg then reads this file (`-f concat -i mylist.txt`) and stream copies (`-c copy`) them into a single file. This only works if all clips have identical codecs, resolutions, and framerates.

---

## ⚡ UI/UX and Asynchronous Workflow

### Real-time Progress and ETAs
When a long-running FFmpeg task is launched, the UI cannot freeze. 
1.  The UI launches the FFmpeg command using `QProcess` or a `QThread`.
2.  FFmpeg outputs text like `time=00:01:23.45` to stderr.
3.  A regular expression in the Python code parses this timecode and converts it to seconds.
4.  By comparing the processed seconds to the total known duration of the video, a completion percentage is calculated.
5.  A timer tracks how long the process has been running, calculating the processing speed (seconds of video processed per second of real-time) to estimate the Remaining Time (ETA).

### Task Cancellation
The UI features a prominent "Cancel" button during processing. Clicking this sends a termination signal (`SIGTERM` or Windows `taskkill`) to the underlying FFmpeg subprocess. The temporary or half-finished output files are then gracefully handled or deleted, returning the user to the starting state immediately.

### Custom Video Player Preview
Instead of relying on external players, the Timeline UI integrates `QMediaPlayer` and `QVideoWidget`. When a user selects a clip in their timeline table, the UI loads that specific file into the preview monitor, allowing them to visually find the exact "Trim In" and "Trim Out" timestamps, enhancing the precision of the editing workflow.

---
*This documentation reflects Onyx Engine v3.0, incorporating the Multi-Track Timeline update.*
