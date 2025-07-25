
# 🎙️ SRT to Speech Converter (Windows GUI)

A Windows-based GUI tool that converts `.srt` subtitle files into audio using Persian text-to-speech API (PartAI). Supports accurate timing and speaker control. Built with Python and Tkinter.

---

## 🚀 Features

- 🧠 Parses `.srt` subtitle files accurately.
- 🗣️ Sends each subtitle to the **PartAI** TTS API for speech synthesis.
- 🎚️ Automatically adjusts speaking speed based on subtitle duration and length.
- 🎧 Creates individual audio clips and a combined `.wav` file matching subtitle timings.
- 👤 Choose from multiple speaker voices.
- 🖥️ Simple and clean **Tkinter GUI**.
- 🔊 Supports audio merging (e.g., merge `.mp3` and `.wav` files into one).
- 🔐 Uses `config.py` to load your API token securely.

---

## 📦 Installation

### Requirements

- Python 3.7+
- [ffmpeg](https://ffmpeg.org/download.html) (required for audio processing)
- Install required libraries:

```bash
pip install pydub requests
```

---

## 🔧 Setup

1. Clone the repository:

```bash
git clone https://github.com/yourusername/srt-to-speech.git
cd srt-to-speech
```

2. Add a `config.py` file in the same directory:

```python
main_token = "your_api_token_here"
```

3. Make sure `ffmpeg.exe` and `ffprobe.exe` are either:
   - In your system PATH, or
   - Located next to your `python.exe` in the virtual environment.

---

## 🖱️ Usage

### Graphical Interface (recommended)

```bash
python your_script_name.py
```

Then, in the GUI:

1. Select your `.srt` subtitle file.
2. Choose the output path for the combined `.wav` file.
3. Pick a speaker voice (1, 2, or 3).
4. Click **Start Conversion**.

You’ll get:
- A full synchronized audio track.
- A folder with individual audio files per subtitle.

You can also:
- Merge multiple audio files into one using the **Merge Audio Files** button.

### CLI Mode (optional)

```bash
python your_script_name.py input.srt output.wav 3
```

---

## 🎤 API Info

This app uses the **PartAI Text-to-Speech API** (https://partai.gw.isahab.ir). You need an access token (`main_token`) to use it.

---

## 📁 Output

- `output.wav` — the final full-length audio.
- `output_individual_audios/` — folder of per-subtitle audio files (`.mp3`).
- `output2.wav` — optional merged audio from selected clips.

---

## 📷 Screenshots

> *(Add GUI screenshots here)*

---

## 💬 Language Support

- ✅ Persian (Farsi)
- ❌ English subtitles not officially supported (may work)

---

## 📜 License

MIT License. Feel free to fork, improve, and share.

---

## 🤝 Contributing

Pull requests and feedback are welcome!

---

## ✨ Author

Made with ❤️ by Ali
GitHub: [aliiih03](https://github.com/yourusername)
