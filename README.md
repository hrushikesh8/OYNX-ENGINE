# 🎬 Onyx Engine (formerly VidFlow)

**Onyx Engine** is an advanced, comprehensive video engineering application and microservice designed to automate, simplify, and elevate complex media workflows. Featuring a fully integrated **PyQt6 graphical interface**, it serves as a bridge between raw FFmpeg processing power and professional non-linear editing. 

Whether you need to remaster legacy footage, create highly-produced social media shorts, seamlessly stitch video clips, perform color grading, or manage complex multi-track timelines, Onyx Engine handles it all through an intuitive, premium dark-mode interface.

---

## ✨ Comprehensive Feature Breakdown

### 1. The Core NLE Suite
The backbone of Onyx Engine revolves around giving you precise, non-linear control over your media without the bloat of traditional editors.
* **Multi-Track Timeline Composer (Major Update):** A full-fledged non-linear editing interface. Mix multiple video clips and audio tracks, apply custom scaling (16:9, 9:16, 1:1), color grade on the fly, set precise trim in/out points, and adjust speeds for cinematic slow-motion or hyper-lapses.
* **Stream Ladder:** A high-end broadcast tool for combining clips side-by-side or stacking multiple clips into a single video file dynamically. Features independent, VLC-style UI volume wedges for each stream and granular mute controls.
* **Seamless Suture:** Perfect for compiling highlight reels. Add unlimited clips to a drag-and-drop list and have the engine multiplex them together seamlessly with unified background audio tracks.
* **Precision Division (Scene Sniper):** Structurally edit and split massive video files into exact chunks (e.g., 30 seconds for WhatsApp statuses) or slice media exactly in half. Now features a live preview QMediaPlayer!

### 2. The Social Media Engine
Designed for content creators and marketers who need rapid deployment across TikTok, Reels, and YouTube Shorts.
* **Intelligent Auto-Shorts Editor:** Automatically convert horizontal (landscape) videos into vertical (portrait) 9:16 formats. The engine dynamically creates an aesthetically pleasing blurred background using the original footage, ensuring no black bars are visible.
* **HD GIF Maker:** Generate crystal-clear, high-definition GIFs using a robust 2-pass palette generation algorithm, ensuring accurate colors and smooth, low-filesize playback.
* **Watermark Injection & Branding:** Burn branding, logo images, or text overlays directly onto your video at any specified position with custom opacity controls.

### 3. Media Logistics & AI Management
Stop organizing your downloaded shows by hand. Let the engine do the heavy lifting.
* **Chronicle Organizer (NEW):** A massive AI-driven media logistics engine. Point it at a messy download folder, and it connects to the TMDB API to scrape metadata, automatically sort episodes, rename them to Plex/Jellyfin standards, and intelligently structure entire messy libraries of movies and TV shows.
* **Automated Subtitle Merger:** Automatically scans directories to find and embed matching `.srt` subtitle files into their corresponding video containers.
* **Track Management (Multiplexer):** Surgical control over file streams. Inspect all embedded audio and subtitle tracks, and safely extract or strip specific channels without re-encoding.
* **Smart Format Conversion:** Wrap video streams into new containers (MP4, MKV, AVI, MOV) seamlessly via stream copying—zero quality loss, instant completion.

### 4. Audio Processing Suite
Unparalleled control over sound.
* **Silence Remover:** Detects and automatically trims out silent, dead-air gaps in your audio or video files. Perfect for fast-paced podcast edits or vlog jump-cuts.
* **Audiophile Extraction:** Rip audio tracks from video files in high-fidelity formats, supporting 320kbps MP3, 24-bit WAV, and Lossless FLAC.
* **Volume Normalization & Mixing:** Use the custom VLC-style volume sliders across the UI to set perfect mixing levels before rendering.

### 5. AI Restoration & Enhancement
Breathe new life into old, noisy footage.
* **Media Remastering:** Applies complex FFmpeg filter chains including `hqdn3d` (high-quality 3D denoise), `unsharp` (sharpening), and `scale` (Lanczos upscaling) to modernize vintage clips.
* **Color Studio:** Deep color grading. Adjust brightness, contrast, saturation, and gamma.
* **Lossless Video Compressor:** Shrink massive file sizes by intelligently optimizing audio bitrates and re-encoding video tracks using modern codecs while aiming to maintain original visual quality.

---

## 🏗️ Architectural Overview

The Onyx Engine utilizes a highly decoupled, asynchronous architecture.
* **Frontend (PyQt6):** Found in `src/ui/`. A totally custom-built dark-mode UI utilizing custom widgets, floating flashes, and advanced PyQt6 layouts to provide a premium feel.
* **Backend Processors:** Found in `src/processors/`. These are the engines. They intercept UI signals, calculate complex FFmpeg command arrays, and execute them in isolated `subprocess` environments.
* **Global Asynchronous Tracking:** Tasks are never run on the main UI thread. Long-running FFmpeg processes calculate ETA, Processing Speed, and Completion % by scraping `stderr` outputs in real-time, allowing users to safely cancel tasks at any moment.

---

## 🚀 Installation & Setup

### 1. Clone the Repository
Start by downloading the codebase to your computer:
```bash
git clone https://github.com/hrushikesh8/Onyx-Engine.git
cd Onyx-Engine
```

### 2. FFmpeg Setup (Critical Requirement)
Onyx Engine utilizes **FFmpeg** and **FFprobe** under the hood. If this is not set up correctly, the application will not work.
1. Download the build release for your OS from [ffmpeg.org/download](https://ffmpeg.org/download.html).
2. Extract the folder to a permanent location (e.g., `C:\ffmpeg`).
3. Add the `bin` folder (e.g., `C:\ffmpeg\bin`) to your system's `PATH` environment variable.
4. Restart your computer or terminal for the changes to take effect.

### 3. Install Python Dependencies
Ensure you have Python 3.9+ installed, then run:
```bash
python -m venv venv
.\venv\Scripts\activate  # On Windows
pip install -r requirements.txt
```
*Required packages include `PyQt6`, `requests`, `pyqtdarktheme`, `opencv-python`, etc.*

---

## 🎮 How to Use

Simply launch the GUI application from your terminal:
```bash
python gui_main.py
```
You will be greeted by the **Onyx Engine Dashboard**. From here, navigate the sidebar to access the Timeline Composer, Editor, AI VFX tools, Chronicle Logistics, and more. 

---

## 📚 Documentation
For a deep dive into the architecture, FFmpeg command generation logic, and detailed module breakdowns, please refer to:
- [DOCUMENTATION.md](DOCUMENTATION.md) - For deep-dive logic and FFmpeg mechanisms.
- [ARCHITECTURE.md](ARCHITECTURE.md) - For developers looking to extend the Python codebase.

---

**Built with 💻 & ☕ by Hrushikesh Bunni**