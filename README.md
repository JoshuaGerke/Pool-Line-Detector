# 🎱 Pool Line Detector

**Computer Vision Experiment for Line Detection**

![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)
![OpenCV](https://img.shields.io/badge/OpenCV-4.8+-green.svg)
![License](https://img.shields.io/badge/License-CC%20BY--NC--SA%204.0-lightgrey.svg)

---

## ⚠️ IMPORTANT DISCLAIMER

> **This project is a PROOF OF CONCEPT and EDUCATIONAL EXPERIMENT only!**
>
> - ❌ **DO NOT** use this to gain any advantage in online/multiplayer games
> - ❌ **DO NOT** use this to cheat or violate any game's Terms of Service
> - ✅ This was developed and tested **ONLY in single-player mode**
> - ✅ Purpose: Learning computer vision, line detection, and overlay techniques

**Using this tool in multiplayer games may result in account bans and violates fair play principles.**

---

## 📖 About

This is a computer vision experiment that:
1. Captures the screen
2. Detects white lines using OpenCV
3. Extends detected lines and displays them as a transparent overlay

The project demonstrates:
- Screen capturing with `mss`
- Color-based line detection
- Contour analysis with OpenCV
- Transparent click-through overlays on Windows

---

## 🧪 Testing Environment

This project was developed and tested **exclusively** in single-player mode at:

🔗 https://www.crazygames.com/game/8-ball-pool-billiards-multiplayer

**No multiplayer testing was performed.**

---

## 🛠️ Installation

```bash
# Clone the repository
git clone https://github.com/YOUR_USERNAME/pool-line-detector.git
cd pool-line-detector

# Install dependencies
pip install -r requirements.txt
```

## 📦 Requirements

- Python 3.10+
- Windows OS (for click-through overlay)
- Dependencies: `opencv-python`, `mss`, `numpy`, `Pillow`, `pywin32`

---

## 🚀 Usage

```bash
# Run the line detector (single scan, saves debug images)
python line_finder.py

# Run the overlay (continuous detection)
python main.py
```

**Controls:**
- `ESC` - Exit the overlay

---

## 📁 Project Structure

```
pool-line-detector/
├── main.py           # Overlay application
├── line_finder.py    # Line detection testing script
├── requirements.txt  # Python dependencies
└── README.md         # This file
```

---

## 🤝 Contributing

Contributions are welcome! Please ensure any contributions:
1. Maintain the educational/experimental nature of the project
2. Do not encourage or enable cheating in any games
3. Follow the code style of the project

---

## 📄 License

**CC BY-NC-SA 4.0** (Creative Commons Attribution-NonCommercial-ShareAlike)

- ✅ Use, modify, and share freely
- ✅ Contributions welcome
- ❌ **No commercial use or selling**

See [LICENSE](LICENSE) for details.

---

## 🙏 Acknowledgments

- OpenCV community for excellent documentation
- This project is purely for learning computer vision techniques

---

**Remember: Play fair, learn responsibly! 🎮**
