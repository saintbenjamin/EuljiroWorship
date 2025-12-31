# 📖 EuljiroWorship

## Overview

**EuljiroWorship** is a real-time worship slide control system designed for live church services.  
It enables operators to manage worship slides, Bible verses, hymns, responsive readings, and emergency captions seamlessly during worship, while broadcasting the selected slide content to overlay displays (e.g. OBS, beam projectors, sanctuary screens) via WebSocket.

The project is actively used in a Korean church environment and is currently optimized for **Korean language workflows**.  
However, its architecture is intentionally modular, and the system is designed with **future global / multilingual expansion** in mind.

---

## Key Features

### 🎛 Slide Controller (GUI)

- Central slide controller built with **PySide6**
- Keyboard-driven slide navigation (arrow keys, spacebar)
- Page jump and direct slide selection via table
- Real-time preview of slide caption and content
- Designed to be stable during rapid slide switching

---

### 📡 Real-Time WebSocket Broadcasting

- Slides are sent as JSON objects over WebSocket
- Overlay clients update instantly upon slide changes
- Lightweight, synchronous WebSocket manager
- Designed to work reliably with OBS browser sources or custom overlays

---

### 🚨 Emergency Caption System

- One-click activation of emergency captions
- Modal dialog for:
  - Bible reference input (e.g. `요 3:16`)
  - Keyword-based Bible search
  - Manual emergency messages
- Automatic generation of emergency slides
- Emergency mode cleanly restores the previous slide state after clearance

---

### 📖 Bible Integration

- Supports multiple Bible versions stored as JSON
- Flexible Bible reference parser with alias support
- Keyword search across entire Bible text
  - AND-based search
  - Compact (whitespace-removed) search
- Highlighted keyword results with custom Qt delegates

---

### 🧾 Hymns & Responsive Readings

- Automatic loading of:
  - Hymns by number
  - Responsive readings by number
- Intelligent slide splitting for long text
- Consistent formatting optimized for live projection

---

### 👀 File-Based Watchers for Reliability

- Slide file watcher detects:
  - Slide updates
  - Slide clears (used for emergency exit)
- Verse interruptor watcher monitors emergency verse file
- Designed to recover gracefully from unexpected states

---

### 🧠 State Safety & Restoration

- Automatic backup of slide state before emergency mode
- Restores previous slides when emergency captions are cleared
- Prevents accidental loss of worship flow during live services

---

## Project Structure (Simplified)

```
EuljiroWorship/
├─ controller/
│  ├─ slide_controller.py
│  ├─ ui/
│  │  ├─ slide_controller_ui_builder.py
│  │  └─ emergency_caption_dialog.py
│  └─ utils/
│     ├─ emergency_caption_handler.py
│     ├─ emergency_slide_factory.py
│     ├─ interruptor_watcher.py
│     ├─ slide_file_watcher.py
│     ├─ slide_controller_data_manager.py
│     └─ slide_websocket_manager.py
├─ core/
│  ├─ utils/
│  │  ├─ bible_parser.py
│  │  ├─ bible_keyword_searcher.py
│  │  └─ …
│  └─ config/
│     └─ paths.py
```
---

## Design Philosophy

- **Stability over complexity**  
  Worship software must not fail during live services.

- **Explicit state transitions**  
  Emergency mode, restoration, and slide changes are all clearly separated.

- **Human-operated first**  
  Optimized for real worship operators, not automation gimmicks.

- **Expandable, not locked-in**  
  Korean-centric today, global-ready tomorrow.

---

## Future Plans

- Multilingual UI and Bible datasets
- Internationalized slide templates
- Optional async WebSocket backend
- Extended sanctuary-specific display modes

---

## License

MIT License with Attribution Requirement  
© 2025 The Eulji-ro Presbyterian Church