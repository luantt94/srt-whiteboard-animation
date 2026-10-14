#!/usr/bin/env python3
"""
Hậu kỳ video trắng bảng: GHÉP ÂM THANH và/hoặc KHẮC PHỤ ĐỀ.

Renderer chính (`render_stream_whiteboard.py`) xuất MP4 im lặng, không chữ.
Script này thêm tiếng và/hoặc dải phụ đề bằng ffmpeg (cần ffmpeg trong PATH,
bản có libass để khắc phụ đề).

ÂM THANH — chọn tối đa một nguồn:
  --audio-file FILE               một file cho cả video
  --audio-clip "MS=FILE" [...]    đặt nhiều clip lên dòng thời gian theo mốc ms
                                  (mỗi cảnh một file: MS = startMs của cảnh)
  --tts-srt FILE --tts-voice V    dùng edge-tts đọc phụ đề, canh theo mốc SRT
       [--tts-group cue|scene]    đọc theo từng câu (mặc định) hay từng cảnh
       [--scenes scenes.json]     bắt buộc khi --tts-group scene

PHỤ ĐỀ:
  --burn-srt FILE                 khắc phụ đề (mốc thời gian tuyệt đối của cả
                                  video — dùng trên bản đã ghép ở tab 5)
  [--sub-fontsize 20] [--sub-margin-v 46] [--sub-font "Arial"]

Ví dụ:
  postprocess_video.py --video final.mp4 --output final-av.mp4 \\
    --tts-srt demo.srt --tts-voice vi-VN-HoaiMyNeural \\
    --tts-group scene --scenes scenes.json --burn-srt demo.srt

In dòng cuối: OUTPUT=<đường dẫn>
"""
from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parent
FFMPEG = shutil.which("ffmpeg")
FFPROBE = shutil.which("ffprobe")


def _run(cmd: list[str]) -> None:
    print("  $ " + subprocess.list2cmdline(cmd))
    res = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8",
                         errors="replace")
    if res.returncode != 0:
        raise RuntimeError((res.stderr or res.stdout or "ffmpeg lỗi").strip()[:800])


def _video_duration_sec(path: Path) -> float:
    if FFPROBE:
        res = subprocess.run(
            [FFPROBE, "-v", "error", "-show_entries", "format=duration",
             "-of", "default=nw=1:nk=1", str(path)],
            capture_output=True, text=True,
        )
        try:
            return float(res.stdout.strip())
        except ValueError:
            pass
    return 0.0


def _tts_units(srt: Path, group: str, scenes_json: Path | None) -> list[tuple[int, str]]:
    sys.path.insert(0, str(SCRIPTS))
    import parse_srt  # noqa: E402

    if group == "scene":
        if not scenes_json or not scenes_json.exists():
            raise SystemExit("[err] --tts-group scene cần --scenes scenes.json")
        data = json.loads(scenes_json.read_text(encoding="utf-8"))
        return [(int(s["startMs"]), s["text"]) for s in data["scenes"] if s.get("text")]
    cues = parse_srt.parse_srt(srt.read_text(encoding="utf-8-sig"))
    return [(int(c["startMs"]), c["text"]) for c in cues if c.get("text")]


def _run_edge_tts_cli(text: str, voice: str, out: Path) -> tuple[int, str]:
    """Gọi CLI edge-tts; trả về (returncode, thông báo lỗi nếu có)."""
    for base in ([sys.executable, "-m", "edge_tts"], ["edge-tts"]):
        try:
            res = subprocess.run(
                [*base, "--voice", voice, "--text", text, "--write-media", str(out)],
                capture_output=True, text=True, encoding="utf-8", errors="replace",
            )
        except FileNotFoundError:
            continue
        if res.returncode == 0 and out.exists() and out.stat().st_size > 0:
            return 0, ""
        return res.returncode, (res.stderr or res.stdout).strip()
    return -1, "Không gọi được edge-tts. Cài: pip install edge-tts"


def _edge_tts(text: str, voice: str, out: Path) -> None:
    rc, err = _run_edge_tts_cli(text, voice, out)
    if rc == 0:
        return
    # Lỗi 403 (WSServerHandshakeError) thường do bản edge-tts cũ không theo kịp
    # thay đổi xác thực phía Microsoft — tự nâng cấp rồi thử lại đúng 1 lần.
    if "403" in err or "WSServerHandshakeError" in err:
        upgrade = subprocess.run(
            [sys.executable, "-m", "pip", "install", "--quiet", "--upgrade", "edge-tts"],
            capture_output=True, text=True,
        )
        if upgrade.returncode == 0:
            rc, err = _run_edge_tts_cli(text, voice, out)
            if rc == 0:
                return
    raise RuntimeError(f"edge-tts lỗi: {err[:400]}")


def _assemble_timeline(clips: list[tuple[int, Path]], total_sec: float,
                       out: Path) -> None:
    """Đặt từng clip vào mốc ms của nó trên một dải im lặng dài total_sec."""
    inputs: list[str] = []
    for _, f in clips:
        inputs += ["-i", str(f)]
    parts, labels = [], []
    for i, (ms, _) in enumerate(clips):
        parts.append(f"[{i}:a]aresample=44100,adelay={ms}|{ms}[a{i}]")
        labels.append(f"[a{i}]")
    if len(clips) == 1:
        parts.append(f"{labels[0]}apad=whole_dur={total_sec:.3f}[a]")
    else:
        parts.append("".join(labels) +
                     f"amix=inputs={len(clips)}:normalize=0:dropout_transition=0[m]")
        parts.append(f"[m]apad=whole_dur={total_sec:.3f}[a]")
    _run([FFMPEG, "-y", "-loglevel", "error", *inputs,
          "-filter_complex", ";".join(parts), "-map", "[a]",
          "-t", f"{total_sec:.3f}", "-c:a", "aac", "-b:a", "192k", str(out)])


def _dt_escape(text: str) -> str:
    """Escape văn bản cho tham số text= của bộ lọc drawtext (ffmpeg)."""
    return text.replace("\\", "\\\\").replace(":", "\\:").replace("'", "\\'")


_FONT_CANDIDATES = [
    r"C:\Windows\Fonts\arial.ttf",
    r"C:\Windows\Fonts\segoeui.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    "/System/Library/Fonts/Supplemental/Arial.ttf",
]


def _dt_font_arg() -> str:
    """Trỏ thẳng tới file .ttf thật — tránh lỗi fontconfig của drawtext
    trên các bản build ffmpeg Windows không có fontconfig.cfg."""
    for cand in _FONT_CANDIDATES:
        if Path(cand).exists():
            esc = cand.replace("\\", "/").replace(":", "\\:")
            return f"fontfile='{esc}'"
    return "font=Arial"


def _drawtext_filters(texts: list[dict]) -> list[str]:
    parts = []
    font_arg = _dt_font_arg()
    for t in texts:
        start_s = t.get("startMs", 0) / 1000.0
        end_s = (t.get("startMs", 0) + t.get("durationMs", 0)) / 1000.0
        txt = _dt_escape(str(t.get("text", "")))
        if not txt:
            continue
        parts.append(
            f"drawtext=text='{txt}':{font_arg}:fontsize=46:fontcolor=white:"
            f"bordercolor=black@0.85:borderw=3:x=(w-text_w)/2:y=h*0.08:"
            f"enable='between(t,{start_s:.3f},{end_s:.3f})'"
        )
    return parts


def _mux(video: Path, track: Path | None, burn_srt: Path | None,
         style: str, out: Path, texts: list[dict] | None = None) -> None:
    work = out.parent
    cmd = [FFMPEG, "-y", "-loglevel", "error", "-i", str(video.resolve())]
    sub_name: str | None = None
    if track is not None:
        cmd += ["-i", str(track.resolve())]
    vf_parts = _drawtext_filters(texts) if texts else []
    if burn_srt is not None:
        sub_name = "_ppsub.srt"
        shutil.copyfile(burn_srt, work / sub_name)
        vf_parts.append(f"subtitles={sub_name}:force_style='{style}'")
    if vf_parts:
        cmd += ["-vf", ",".join(vf_parts),
                "-c:v", "libx264", "-crf", "18", "-preset", "medium",
                "-pix_fmt", "yuv420p"]
    else:
        cmd += ["-c:v", "copy"]
    if track is not None:
        cmd += ["-map", "0:v:0", "-map", "1:a:0", "-c:a", "aac", "-b:a", "192k",
                "-af", "apad", "-shortest"]
    else:
        cmd += ["-map", "0:v:0", "-an"]
    cmd += [str(out.resolve())]
    try:
        print("  $ " + subprocess.list2cmdline(cmd))
        res = subprocess.run(cmd, cwd=str(work), capture_output=True, text=True,
                             encoding="utf-8", errors="replace")
        if res.returncode != 0:
            raise RuntimeError((res.stderr or res.stdout).strip()[:800])
    finally:
        if sub_name:
            (work / sub_name).unlink(missing_ok=True)


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description="Ghép âm thanh / khắc phụ đề vào video")
    p.add_argument("--video", required=True)
    p.add_argument("--output", required=True)
    p.add_argument("--audio-file")
    p.add_argument("--audio-clip", nargs="+", default=None,
                   help='các mục "MS=đường/dẫn/file"')
    p.add_argument("--tts-srt")
    p.add_argument("--tts-voice", default="vi-VN-HoaiMyNeural")
    p.add_argument("--tts-group", choices=["cue", "scene"], default="cue")
    p.add_argument("--scenes")
    p.add_argument("--burn-srt")
    p.add_argument("--texts", help="đường dẫn texts.json (chữ chèn trên timeline)")
    p.add_argument("--sub-fontsize", type=int, default=20)
    p.add_argument("--sub-margin-v", type=int, default=46)
    p.add_argument("--sub-font", default="Arial")
    args = p.parse_args(argv)

    if FFMPEG is None:
        print("[err] Không tìm thấy ffmpeg trong PATH. Cần ffmpeg (bản có libass) "
              "để ghép tiếng / khắc phụ đề.", file=sys.stderr)
        return 2

    video = Path(args.video)
    out = Path(args.output)
    if not video.exists():
        print(f"[err] Không thấy video: {video}", file=sys.stderr)
        return 1
    out.parent.mkdir(parents=True, exist_ok=True)
    total = _video_duration_sec(video) or 0.0

    sources = sum(bool(x) for x in (args.audio_file, args.audio_clip, args.tts_srt))
    if sources > 1:
        print("[err] Chỉ chọn một nguồn âm thanh.", file=sys.stderr)
        return 1

    tmp = Path(tempfile.mkdtemp(prefix="ppvid_"))
    track: Path | None = None
    try:
        if args.audio_file:
            track = Path(args.audio_file)
            if not track.exists():
                print(f"[err] Không thấy file âm thanh: {track}", file=sys.stderr)
                return 1
        elif args.audio_clip:
            clips: list[tuple[int, Path]] = []
            for item in args.audio_clip:
                ms_s, _, path_s = item.partition("=")
                fp = Path(path_s)
                if not fp.exists():
                    print(f"[err] Không thấy: {fp}", file=sys.stderr)
                    return 1
                clips.append((int(ms_s), fp))
            clips.sort(key=lambda c: c[0])
            track = tmp / "track.m4a"
            print(f"[..] Dựng dải âm thanh từ {len(clips)} clip …")
            _assemble_timeline(clips, total or (max(c[0] for c in clips) / 1000 + 5),
                               track)
        elif args.tts_srt:
            units = _tts_units(Path(args.tts_srt), args.tts_group,
                               Path(args.scenes) if args.scenes else None)
            print(f"[..] Tạo giọng đọc edge-tts ({args.tts_voice}) cho "
                  f"{len(units)} đoạn …")
            clips = []
            for i, (ms, text) in enumerate(units):
                clip = tmp / f"tts-{i:03d}.mp3"
                _edge_tts(text, args.tts_voice, clip)
                clips.append((ms, clip))
            track = tmp / "track.m4a"
            _assemble_timeline(clips, total or (units[-1][0] / 1000 + 8), track)

        burn = Path(args.burn_srt) if args.burn_srt else None
        if burn and not burn.exists():
            print(f"[err] Không thấy SRT phụ đề: {burn}", file=sys.stderr)
            return 1
        style = (f"FontName={args.sub_font},Fontsize={args.sub_fontsize},"
                 f"PrimaryColour=&H00202020,OutlineColour=&H80F5EBD7,"
                 f"BorderStyle=1,Outline=2,Shadow=0,MarginV={args.sub_margin_v}")

        texts: list[dict] = []
        if args.texts:
            texts_path = Path(args.texts)
            if not texts_path.exists():
                print(f"[err] Không thấy texts.json: {texts_path}", file=sys.stderr)
                return 1
            data = json.loads(texts_path.read_text(encoding="utf-8"))
            texts = data.get("items", []) if isinstance(data, dict) else data

        if track is None and burn is None and not texts:
            print("[err] Không có gì để làm: chọn nguồn âm thanh, --burn-srt hoặc "
                  "--texts.", file=sys.stderr)
            return 1

        print("[..] Ghép vào video …")
        _mux(video, track, burn, style, out, texts)
    except (RuntimeError, SystemExit) as exc:
        print(f"[err] {exc}", file=sys.stderr)
        return 1
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    size_mb = out.stat().st_size / (1024 * 1024)
    print(f"\nXong: {out}  ({size_mb:.2f} MB)")
    print(f"OUTPUT={out.resolve()}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
