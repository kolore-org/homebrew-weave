#!/usr/bin/env python3
"""
transcribe_to_weave.py - Extract transcript words with word-level timings.
Extracts audio from a video/audio file and transcribes it locally using OpenAI Whisper (with word-level timestamps),
OR parses an existing SRT/WebVTT subtitle file to distribute word timings.
Outputs a clean JSON list of words with precise timestamps.

Usage:
    python3 scripts/transcribe_to_weave.py <path_to_input> [output_json] [--srt <path_to_srt>] [--vtt <path_to_vtt>]
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

def check_ffmpeg():
    try:
        subprocess.run(["ffmpeg", "-version"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    except FileNotFoundError:
        print("ERROR: ffmpeg is required but not found in PATH.")
        print("Install it via Homebrew: brew install ffmpeg")
        sys.exit(1)

def check_whisper_dependency():
    try:
        import whisper
    except ImportError:
        print("ERROR: 'openai-whisper' python package is required for auto-transcription.")
        print("Please install it by running:")
        print("  pip install openai-whisper")
        print("\nAlternatively, bypass Whisper entirely by providing an existing subtitle file:")
        print("  python3 scripts/transcribe_to_weave.py <path_to_input> --srt <path_to_srt>")
        print("  python3 scripts/transcribe_to_weave.py <path_to_input> --vtt <path_to_vtt>")
        sys.exit(1)

def parse_time_srt(time_str):
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
        
    blocks = content.strip().split("\n\n")
    for block in blocks:
        lines = [l.strip() for l in block.strip().split("\n") if l.strip()]
        if len(lines) < 2:
            continue
        
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

def main():
    parser = argparse.ArgumentParser(description="Extract word-level transcript with precise timings from video/audio or subtitles.")
    parser.add_argument("input_path", help="Path to video or audio file")
    parser.add_argument("output_json", nargs="?", default=None, help="Output JSON file path (defaults to <input_name>_transcript.json)")
    parser.add_argument("--srt", help="Path to pre-existing SRT file (bypasses Whisper dependency)")
    parser.add_argument("--vtt", help="Path to pre-existing WebVTT file (bypasses Whisper dependency)")
    args = parser.parse_args()

    input_path = args.input_path
    if not os.path.exists(input_path):
        print(f"Error: Input file not found at '{input_path}'")
        sys.exit(1)

    # Resolve output path
    if args.output_json:
        output_json = args.output_json
    else:
        base, _ = os.path.splitext(input_path)
        output_json = f"{base}_transcript.json"

    words_list = []

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
            for i, w in enumerate(words):
                w_start = cue["start"] + i * word_dur
                w_end = w_start + word_dur
                words_list.append({
                    "word": w,
                    "start": round(w_start, 3),
                    "end": round(w_end, 3)
                })
    else:
        check_ffmpeg()
        check_whisper_dependency()
        
        # We need a temp wav file for Whisper
        temp_dir = os.path.dirname(os.path.abspath(output_json))
        if temp_dir:
            os.makedirs(temp_dir, exist_ok=True)
        temp_wav = os.path.join(temp_dir if temp_dir else ".", "temp_audio.wav")
        
        print("Extracting audio track...")
        # Extract mono 16kHz WAV (best for Whisper)
        run_command([
            "ffmpeg", "-y", "-i", input_path, 
            "-vn", "-acodec", "pcm_s16le", 
            "-ar", "16000", "-ac", "1", 
            temp_wav
        ])

        try:
            print("Loading local OpenAI Whisper model ('base')...")
            import whisper
            model = whisper.load_model("base")

            print("Transcribing and extracting word-level timestamps...")
            result = model.transcribe(temp_wav, word_timestamps=True, language="en")
        finally:
            # Clean up temp WAV
            if os.path.exists(temp_wav):
                os.remove(temp_wav)

        raw_segments = result.get("segments", [])
        if not raw_segments:
            print("Warning: No speech segments were detected in the video/audio.")
            sys.exit(1)
            
        for seg in raw_segments:
            for w in seg.get("words", []):
                words_list.append({
                    "word": w["word"].strip(),
                    "start": round(w["start"], 3),
                    "end": round(w["end"], 3)
                })

    # Save to JSON
    with open(output_json, "w", encoding="utf-8") as f:
        json.dump(words_list, f, indent=2, ensure_ascii=False)

    print(f"\nSUCCESS! Extracted {len(words_list)} words with timings.")
    print(f"Saved transcript to: {output_json}")

if __name__ == "__main__":
    main()
