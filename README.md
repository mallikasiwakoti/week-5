# Faceless Video Factory

A beginner-friendly Python tool that turns a topic and voiceover script into a vertical MP4 for YouTube Shorts and Instagram Reels.

## What it does
- Tries a local Ollama model for script drafting (no cloud API key).
- Lets you paste your own script if local AI is unavailable.
- Creates narration with Edge TTS.
- Downloads portrait stock video from Pexels if you provide an API key.
- Otherwise uses a clean branded background with subtitles.
- Exports a 1080 x 1920 MP4 in the output folder.

This is a local video maker, not a fully autonomous publishing bot. You review and upload each video yourself.

## Requirements
Windows 10/11, Python 3.10+, FFmpeg on PATH, and internet for Edge TTS. Pexels and Ollama are optional.

## Install
1. Install Python from https://www.python.org/downloads/ and tick **Add Python to PATH**.
2. Install FFmpeg and add its bin folder to Windows PATH.
3. Open PowerShell in this folder and run:

   ```powershell
   py -m venv .venv
   .\.venv\Scripts\Activate.ps1
   pip install -r requirements.txt
   ```

## Optional local AI scripts
Install Ollama from https://ollama.com/download, then run:

```powershell
ollama pull qwen2.5:3b
```

Keep Ollama running. The factory tries it first; if unavailable, paste your own script. Speed depends on your laptop hardware and available memory.

## Optional stock footage
Create an API key at https://www.pexels.com/api/ and set it for this PowerShell session:

```powershell
$env:PEXELS_API_KEY="your-key"
```

Check Pexels' current API and media licence terms before publishing. Without a key, the tool uses a plain branded background.

## Make a video
Interactive:

```powershell
python main.py
```

Topic:

```powershell
python main.py --topic "5 surprising facts about the ocean"
```

Script file:

```powershell
python main.py --topic "Ocean facts" --script script.txt
```

Default voice is en-GB-SoniaNeural. Try en-GB-RyanNeural with --voice. Voice availability and service terms can change; check commercial-use rights.

## Publishing checklist
- Verify every factual claim.
- Listen to the full narration and check subtitles.
- Confirm rights for every video, image, sound and music track.
- Add original research and editing; avoid repetitive mass-produced uploads.
- Upload separately to YouTube and Instagram; auto-posting is not included.

## Cost and limitations
The code and FFmpeg are free. Ollama runs on your laptop. Edge TTS and Pexels have service terms and limits; do not assume unlimited commercial use. This tool does not guarantee views or income.
