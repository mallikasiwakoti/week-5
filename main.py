"""Faceless Video Factory: turn a topic/script into a vertical narrated video."""
from __future__ import annotations
import argparse, asyncio, json, os, re, shutil, subprocess, urllib.parse, urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent
OUTPUT = ROOT / "output"
WIDTH, HEIGHT, FPS = 1080, 1920, 30

def run(command: list[str]) -> None:
    print("Rendering video...")
    subprocess.run(command, check=True)

def check_tools() -> None:
    if not shutil.which("ffmpeg"):
        raise SystemExit("FFmpeg was not found. Install it and add it to Windows PATH.")

def draft_with_ollama(topic: str, seconds: int) -> str | None:
    model = os.getenv("OLLAMA_MODEL", "qwen2.5:3b")
    prompt = (f"Write a compelling, accurate voiceover script for a {seconds}-second "
              f"faceless social video about: {topic}. Start with a strong hook. "
              "Use short natural sentences, no headings, camera directions or hashtags. "
              "Avoid unsupported claims. Aim for about 2.2 words per second.")
    payload = json.dumps({"model": model, "prompt": prompt, "stream": False}).encode()
    req = urllib.request.Request("http://localhost:11434/api/generate", data=payload,
                                 headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=180) as response:
            return json.loads(response.read().decode()).get("response", "").strip() or None
    except Exception as exc:
        print(f"Local AI unavailable ({exc}). Paste a script instead.")
        return None

def get_script(topic: str, seconds: int) -> str:
    draft = draft_with_ollama(topic, seconds)
    if draft:
        print("\nAI draft:\n" + draft)
        if input("\nUse this script? [Y/n] ").strip().lower() in ("", "y", "yes"):
            return draft
    print("\nPaste your voiceover script. Finish with a line containing only END:")
    lines = []
    while True:
        line = input()
        if line.strip().upper() == "END":
            break
        lines.append(line)
    script = "\n".join(lines).strip()
    if not script:
        raise SystemExit("No script supplied.")
    return script

def stamp(seconds: float) -> str:
    ms = int(seconds * 1000)
    h, ms = divmod(ms, 3600000); m, ms = divmod(ms, 60000); s, ms = divmod(ms, 1000)
    return f"{h:02}:{m:02}:{s:02},{ms:03}"

def make_srt(script: str, duration: float, path: Path) -> None:
    words = re.findall(r"\S+", script)
    chunks, current = [], []
    for word in words:
        current.append(word)
        if len(current) >= 7 or re.search(r"[.!?]$", word):
            chunks.append(" ".join(current)); current = []
    if current: chunks.append(" ".join(current))
    total = sum(max(1, len(c.split())) for c in chunks)
    cursor, entries = 0.0, []
    for i, chunk in enumerate(chunks, 1):
        end = min(duration, cursor + duration * max(1, len(chunk.split())) / total)
        entries.append(f"{i}\n{stamp(cursor)} --> {stamp(end)}\n{chunk}\n")
        cursor = end
    path.write_text("\n".join(entries), encoding="utf-8")

def pexels_video(topic: str, destination: Path) -> bool:
    key = os.getenv("PEXELS_API_KEY", "").strip()
    if not key: return False
    query = urllib.parse.urlencode({"query": topic, "per_page": 10, "orientation": "portrait"})
    req = urllib.request.Request("https://api.pexels.com/videos/search?" + query,
                                 headers={"Authorization": key})
    try:
        with urllib.request.urlopen(req, timeout=30) as response:
            videos = json.loads(response.read().decode()).get("videos", [])
        for video in videos:
            files = [f for f in video.get("video_files", []) if f.get("file_type") == "video/mp4"]
            files.sort(key=lambda f: abs(f.get("width", 1) / max(1, f.get("height", 1)) - 0.5625))
            if files:
                with urllib.request.urlopen(files[0]["link"], timeout=90) as src, destination.open("wb") as out:
                    shutil.copyfileobj(src, out)
                return True
    except Exception as exc:
        print(f"Pexels footage unavailable: {exc}")
    return False

async def create_voice(script: str, path: Path, voice: str) -> None:
    try:
        import edge_tts
    except ImportError:
        raise SystemExit("Install dependencies with: pip install -r requirements.txt")
    await edge_tts.Communicate(script, voice).save(str(path))

def audio_duration(path: Path) -> float:
    result = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1", str(path)], capture_output=True,
        text=True, check=True)
    return max(1.0, float(result.stdout.strip()))

def render_video(topic: str, script: str, voice: str, output_name: str) -> Path:
    OUTPUT.mkdir(exist_ok=True); work = OUTPUT / "working"; work.mkdir(exist_ok=True)
    audio, bg, srt = work / "voice.mp3", work / "background.mp4", work / "captions.srt"
    final = OUTPUT / output_name
    asyncio.run(create_voice(script, audio, voice))
    duration = audio_duration(audio); make_srt(script, duration, srt)
    if pexels_video(topic, bg):
        video_input = ["-stream_loop", "-1", "-i", str(bg)]
        visual = f"scale={WIDTH}:{HEIGHT}:force_original_aspect_ratio=increase,crop={WIDTH}:{HEIGHT},fps={FPS},"
    else:
        video_input = ["-f", "lavfi", "-i", f"color=c=#101827:s={WIDTH}x{HEIGHT}:r={FPS}:d={duration}"]
        visual = f"fps={FPS},"
    srt_path = str(srt).replace("\\", "/").replace(":", r"\:")
    vf = visual + f"subtitles='{srt_path}':force_style='FontName=Arial,FontSize=18,PrimaryColour=&H00FFFFFF,OutlineColour=&H00101827,BorderStyle=1,Outline=3,Shadow=1,Alignment=2,MarginV=260,MarginL=90,MarginR=90'"
    cmd = ["ffmpeg", "-y", *video_input, "-i", str(audio), "-t", f"{duration:.2f}",
           "-vf", vf, "-map", "0:v:0", "-map", "1:a:0", "-c:v", "libx264",
           "-preset", "veryfast", "-crf", "23", "-pix_fmt", "yuv420p", "-r", str(FPS),
           "-c:a", "aac", "-b:a", "192k", "-shortest", "-movflags", "+faststart", str(final)]
    run(cmd); return final

def main() -> None:
    parser = argparse.ArgumentParser(description="Create a faceless vertical social video.")
    parser.add_argument("--topic"); parser.add_argument("--script")
    parser.add_argument("--seconds", type=int, default=45)
    parser.add_argument("--voice", default="en-GB-SoniaNeural")
    parser.add_argument("--output", default="faceless-short.mp4")
    args = parser.parse_args(); check_tools()
    topic = args.topic or input("Video topic: ").strip()
    if not topic: raise SystemExit("Please provide a topic.")
    script = Path(args.script).read_text(encoding="utf-8").strip() if args.script else get_script(topic, args.seconds)
    if not script: raise SystemExit("Script is empty.")
    result = render_video(topic, script, args.voice, args.output)
    print(f"\nFinished: {result}\nReview it before publishing.")

if __name__ == "__main__":
    main()
