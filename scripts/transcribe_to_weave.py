#!/usr/bin/env python3
"""
transcribe_to_weave.py - General, automated utility for Weave users.
Extracts audio from a video, transcribes it locally using OpenAI Whisper (with word-level timestamps),
OR parses an existing SRT/WebVTT subtitle file to generate a fully-compliant, styled `.weave` project.

Usage:
    python3 scripts/transcribe_to_weave.py <path_to_video> [output_dir] [--srt <path_to_srt>] [--vtt <path_to_vtt>]
"""

import sys
import os
import subprocess
import json
import argparse

def run_command(cmd, shell=False):
    try:
        result = subprocess.run(cmd, shell=shell, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        print(f"Error running command: {' '.join(cmd) if isinstance(cmd, list) else cmd}")
        print(f"Stderr: {e.stderr}")
        sys.exit(1)

def check_base_dependencies():
    # Check ffmpeg / ffprobe
    try:
        subprocess.run(["ffmpeg", "-version"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        subprocess.run(["ffprobe", "-version"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    except FileNotFoundError:
        print("ERROR: ffmpeg and ffprobe are required but not found in PATH.")
        print("Install them via Homebrew: brew install ffmpeg")
        sys.exit(1)

def check_whisper_dependency():
    # Check whisper
    try:
        import whisper
    except ImportError:
        print("ERROR: 'openai-whisper' python package is required for auto-transcription.")
        print("Please install it by running:")
        print("  pip install openai-whisper")
        print("\nAlternatively, bypass Whisper entirely by providing an existing subtitle file:")
        print("  python3 scripts/transcribe_to_weave.py <path_to_video> --srt <path_to_srt>")
        print("  python3 scripts/transcribe_to_weave.py <path_to_video> --vtt <path_to_vtt>")
        sys.exit(1)

def parse_time_srt(time_str):
    # Format can be HH:MM:SS,mmm or HH:MM:SS.mmm or MM:SS.mmm
    time_str = time_str.strip().replace(",", ".")
    parts = time_str.split(":")
    if len(parts) == 2:
        minutes = float(parts[0])
        seconds = float(parts[1])
        return minutes * 60 + seconds
    elif len(parts) == 3:
        hours = float(parts[0])
        minutes = float(parts[1])
        seconds = float(parts[2])
        return hours * 3600 + minutes * 60 + seconds
    else:
        try:
            return float(time_str)
        except ValueError:
            return 0.0

def parse_srt(file_path):
    cues = []
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read().replace("\r\n", "\n")
        
    # Split by double newlines to separate blocks
    blocks = content.strip().split("\n\n")
    for block in blocks:
        lines = [l.strip() for l in block.strip().split("\n") if l.strip()]
        if len(lines) < 2:
            continue
        
        # Check where '-->' timing arrow resides
        time_line = ""
        text_lines = []
        if "-->" in lines[0]:
            time_line = lines[0]
            text_lines = lines[1:]
        elif len(lines) > 1 and "-->" in lines[1]:
            time_line = lines[1]
            text_lines = lines[2:]
            
        if not time_line:
            continue
            
        try:
            start_str, end_str = time_line.split("-->")
            start = parse_time_srt(start_str)
            end = parse_time_srt(end_str)
            text = " ".join(text_lines).strip()
            if text:
                cues.append({
                    "start": start,
                    "end": end,
                    "text": text
                })
        except Exception:
            continue
    return cues

def parse_vtt(file_path):
    cues = []
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read().replace("\r\n", "\n")
        
    lines = content.strip().split("\n")
    if not lines:
        return []
    
    idx = 0
    if lines[0].startswith("WEBVTT"):
        idx = 1
        # Skip headers / style metadata until first blank line
        while idx < len(lines) and lines[idx].strip() != "":
            idx += 1
            
    current_block = []
    for line in lines[idx:]:
        line_stripped = line.strip()
        if line_stripped == "":
            if current_block:
                cue = parse_vtt_block(current_block)
                if cue:
                    cues.append(cue)
                current_block = []
        else:
            current_block.append(line)
            
    if current_block:
        cue = parse_vtt_block(current_block)
        if cue:
            cues.append(cue)
            
    return cues

def parse_vtt_block(lines):
    time_line = ""
    text_lines = []
    if "-->" in lines[0]:
        time_line = lines[0]
        text_lines = lines[1:]
    elif len(lines) > 1 and "-->" in lines[1]:
        time_line = lines[1]
        text_lines = lines[2:]
        
    if not time_line:
        return None
        
    try:
        start_str, end_str = time_line.split("-->")
        start = parse_time_srt(start_str)
        end = parse_time_srt(end_str)
        text = " ".join(text_lines).strip()
        if text:
            return {
                "start": start,
                "end": end,
                "text": text
            }
    except Exception:
        pass
    return None

def get_video_metadata(video_path):
    cmd = [
        "ffprobe", "-v", "error", 
        "-select_streams", "v:0", 
        "-show_entries", "stream=width,height,duration,r_frame_rate", 
        "-of", "json", 
        video_path
    ]
    meta = json.loads(run_command(cmd))
    stream = meta.get("streams", [{}])[0]
    
    width = int(stream.get("width", 1280))
    height = int(stream.get("height", 720))
    duration = float(stream.get("duration", 10.0))
    
    # Calculate FPS
    fps_raw = stream.get("r_frame_rate", "24/1")
    if "/" in fps_raw:
        num, den = fps_raw.split("/")
        fps = int(round(float(num) / float(den)))
    else:
        fps = int(round(float(fps_raw)))
        
    return width, height, duration, fps

def main():
    parser = argparse.ArgumentParser(description="Auto-generate formatted subtitle templates for Weave.")
    parser.add_argument("video_path", help="Path to video file")
    parser.add_argument("output_dir", nargs="?", default=None, help="Output directory (defaults to outputs/<video_name>)")
    parser.add_argument("--srt", help="Path to pre-existing SRT file (bypasses Whisper dependency)")
    parser.add_argument("--vtt", help="Path to pre-existing WebVTT file (bypasses Whisper dependency)")
    args = parser.parse_args()

    video_path = args.video_path
    if not os.path.exists(video_path):
        print(f"Error: Video file not found at '{video_path}'")
        sys.exit(1)

    # Output directory defaults to outputs/<video_basename_without_ext>
    video_basename = os.path.basename(video_path)
    video_name_no_ext, _ = os.path.splitext(video_basename)
    
    if args.output_dir:
        output_dir = args.output_dir
    else:
        output_dir = os.path.join("outputs", video_name_no_ext)

    check_base_dependencies()
    
    print(f"Probing video metadata for '{video_path}'...")
    width, height, duration, fps = get_video_metadata(video_path)
    print(f"  Dimensions: {width}x{height}")
    print(f"  Duration:   {duration}s")
    print(f"  FPS:        {fps}")

    os.makedirs(output_dir, exist_ok=True)
    segments = []

    if args.srt or args.vtt:
        subtitle_path = args.srt if args.srt else args.vtt
        if not os.path.exists(subtitle_path):
            print(f"Error: Subtitle file not found at '{subtitle_path}'")
            sys.exit(1)
            
        print(f"Parsing subtitle file '{subtitle_path}'...")
        if args.srt:
            cues = parse_srt(subtitle_path)
        else:
            cues = parse_vtt(subtitle_path)
            
        if not cues:
            print("Error: No valid subtitle cues could be parsed from the file.")
            sys.exit(1)
            
        print(f"Loaded {len(cues)} subtitle cues. Distributing word timings evenly...")
        for cue in cues:
            words = cue["text"].split()
            seg_dur = cue["end"] - cue["start"]
            word_dur = seg_dur / max(1, len(words))
            word_list = []
            for i, w in enumerate(words):
                w_start = cue["start"] + i * word_dur
                w_end = w_start + word_dur
                word_list.append({
                    "word": w,
                    "start": w_start,
                    "end": w_end
                })
            segments.append({
                "start": cue["start"],
                "end": cue["end"],
                "words": word_list
            })
    else:
        # Bypassed only if subtitle input is given
        check_whisper_dependency()
        temp_wav = os.path.join(output_dir, "temp_audio.wav")
        
        print("Extracting audio track...")
        # Extract mono 16kHz WAV (best for Whisper)
        run_command([
            "ffmpeg", "-y", "-i", video_path, 
            "-vn", "-acodec", "pcm_s16le", 
            "-ar", "16000", "-ac", "1", 
            temp_wav
        ])

        print("Loading local OpenAI Whisper model ('base')...")
        import whisper
        # Loads model onto MPS on Apple Silicon if available
        model = whisper.load_model("base")

        print("Transcribing and extracting word-level timestamps...")
        result = model.transcribe(temp_wav, word_timestamps=True, language="en")

        # Clean up temp WAV
        if os.path.exists(temp_wav):
            os.remove(temp_wav)

        raw_segments = result.get("segments", [])
        if not raw_segments:
            print("Warning: No speech segments were detected in the video.")
            sys.exit(1)
            
        for seg in raw_segments:
            word_list = []
            for w in seg.get("words", []):
                word_list.append({
                    "word": w["word"].strip(),
                    "start": w["start"],
                    "end": w["end"]
                })
            segments.append({
                "start": seg["start"],
                "end": seg["end"],
                "words": word_list
            })

    print(f"Detected {len(segments)} phrase segments. Structuring cues...")

    # Build the HTML template content
    html_cues = []
    
    # Calculate relative paths from output_dir to video
    abs_video_path = os.path.abspath(video_path)
    abs_output_dir = os.path.abspath(output_dir)
    rel_video_path = os.path.relpath(abs_video_path, abs_output_dir)

    for seg in segments:
        seg_start = seg["start"]
        seg_end = seg["end"]
        seg_dur = seg_end - seg_start
        
        words_html = []
        for word_info in seg.get("words", []):
            word_text = word_info["word"].strip()
            word_start = word_info["start"]
            word_end = word_info["end"]
            word_dur = word_end - word_start
            
            # Escape HTML characters if any
            word_text = word_text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
            
            words_html.append(
                f'    <span class="w" style="animation-delay: {word_start:.3f}s; animation-duration: {word_dur:.3f}s;">{word_text}</span>'
            )
            
        words_joined = "\n".join(words_html)
        html_cues.append(f"""  <!-- Phrase Segment ({seg_start:.3f}s - {seg_end:.3f}s) -->
  <div class="cue" style="animation-delay: {seg_start:.3f}s; animation-duration: {seg_dur:.3f}s;">
{words_joined}
  </div>""")

    cues_body = "\n\n".join(html_cues)

    # 1. Write manifest.json
    manifest_data = {
        "render": {
            "width": width,
            "height": height,
            "fps": fps,
            "duration": duration
        }
    }
    manifest_path = os.path.join(output_dir, "manifest.json")
    with open(manifest_path, "w") as f:
        json.dump(manifest_data, f, indent=2)

    # 2. Write template.weave
    template_content = f"""<!DOCTYPE html><html><head><style>
/* 
   Auto-generated Karaoke-Highlight Subtitle Template
   Dimensions: {width}x{height}
   Target Video: {rel_video_path}
 */
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@800&display=swap');

html, body {{
  margin: 0;
  padding: 0;
  width: {width}px;
  height: {height}px;
  background: #000;
  position: relative;
  overflow: hidden;
  font-family: 'Inter', sans-serif;
  -webkit-font-smoothing: antialiased;
}}

video {{
  position: absolute;
  inset: 0;
  width: {width}px;
  height: {height}px;
  object-fit: cover;
}}

/* Base cue wrapper style */
.cue {{
  position: absolute;
  left: {int(width * 0.08)}px;
  width: {int(width * 0.84)}px;
  top: 76%;
  text-align: center;
  font-size: {int(height * 0.075)}px;
  font-weight: 800;
  line-height: 1.3;
  text-transform: uppercase;
  letter-spacing: -1px;
  
  opacity: 0;
  animation-name: cueshow;
  animation-timing-function: linear;
  animation-fill-mode: forwards;
}}

@keyframes cueshow {{
  0%, 99.99% {{ opacity: 1; }}
  100% {{ opacity: 0; }}
}}

/* Individual word styling for Karaoke Highlight */
.w {{
  display: inline-block;
  color: rgba(255, 255, 255, 0.35); /* Subdued state for upcoming words */
  margin: 0 {int(width * 0.008)}px;
  animation-name: speak;
  animation-timing-function: step-end;
  animation-fill-mode: forwards;
}}

@keyframes speak {{
  from {{
    color: #FFDE00; /* Active state when spoken */
  }}
  to {{
    color: #FFFFFF; /* Past state */
  }}
}}
</style></head><body>
  <video src="{rel_video_path}" muted></video>
  
{cues_body}
</body></html>
"""

    template_path = os.path.join(output_dir, "template.weave")
    with open(template_path, "w") as f:
        f.write(template_content)

    print("\nSUCCESS! Generated fully aligned `.weave` project.")
    print(f"  Project Location: {output_dir}/")
    print(f"  Files created:")
    print(f"    - {output_dir}/template.weave  (Karaoke-highlight subtitles)")
    print(f"    - {output_dir}/manifest.json    ({width}x{height}, {duration}s, {fps}fps)")
    print(f"\nNext steps:")
    print(f"  1. Preview in browser or render silent MP4:")
    print(f"     weave-viewer-cli {output_dir} --record {output_dir}/silent_render.mp4")
    print(f"  2. Re-mux audio:")
    print(f"     ffmpeg -y -i {output_dir}/silent_render.mp4 -i {video_path} -map 0:v -map 1:a -c:v copy -c:a copy -shortest {output_dir}/final_subtitled.mp4")

if __name__ == "__main__":
    main()
