#!/usr/bin/env python3
"""
Combina o vídeo gravado (mp4) com os clipes de áudio (mp3) cena-por-cena,
sincronizando o tempo de cada cena com a duração do áudio correspondente.

Estratégia:
- Para cada cena: cortar o pedaço correspondente do vídeo (entre start_ms e end_ms
  do scene_timings produzido por record_demo.py).
- Comparar a duração do pedaço com a duração do áudio dessa cena.
  - Se o áudio é MAIS LONGO: estender o vídeo segurando o último frame
    (loop do último frame por N segundos via ffmpeg tpad=stop_mode=clone).
  - Se o áudio é MAIS CURTO: deixar o vídeo rodar até o fim e o áudio termina antes.
    (Não acelerar — fica esquisito.)
- Concatenar todos os pedaços de vídeo+áudio em um arquivo final.

Uso:
  python merge_av.py \
      --video gravacao.mp4 \
      --audio-dir audio_clips/ \
      --timings scene_timings.json \
      --output final.mp4

scene_timings.json é o JSON impresso por record_demo.py (campo scene_timings).
audio_dir contém os scene_NNN.mp3 e o tts_manifest.json gerado por generate_tts.py.
"""
import argparse
import json
import shutil
import subprocess
import tempfile
from pathlib import Path


def run(cmd: list[str], capture: bool = True):
    return subprocess.run(cmd, check=True,
                          capture_output=capture, text=capture)


def cut_segment(input_video: Path, start_ms: int, end_ms: int, out_path: Path):
    """Corta input_video entre start_ms e end_ms para out_path."""
    duration_s = (end_ms - start_ms) / 1000.0
    if duration_s <= 0:
        duration_s = 0.5  # fallback mínimo
    run([
        "ffmpeg", "-y",
        "-ss", f"{start_ms / 1000.0:.3f}",
        "-i", str(input_video),
        "-t", f"{duration_s:.3f}",
        "-c:v", "libx264", "-preset", "slow", "-crf", "16",
        "-pix_fmt", "yuv420p",
        "-an",
        str(out_path),
    ])


def extend_video_to(input_segment: Path, target_duration_s: float, out_path: Path):
    """Estende input_segment para target_duration_s clonando o último frame."""
    # tpad=stop_mode=clone:stop_duration=X clona o último frame por X segundos
    current_dur = float(run([
        "ffprobe", "-v", "error", "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1", str(input_segment),
    ]).stdout.strip())
    extra = max(0.0, target_duration_s - current_dur)
    if extra < 0.05:
        shutil.copy(input_segment, out_path)
        return
    run([
        "ffmpeg", "-y", "-i", str(input_segment),
        "-vf", f"tpad=stop_mode=clone:stop_duration={extra:.3f}",
        "-c:v", "libx264", "-preset", "slow", "-crf", "16",
        "-pix_fmt", "yuv420p", "-an",
        str(out_path),
    ])


def mux_segment(video_seg: Path, audio_seg: Path | None, out_path: Path,
                target_duration_s: float):
    """Combina video_seg com audio_seg (ou silêncio) em um mp4 final."""
    if audio_seg is None:
        # gera um áudio silencioso da duração do vídeo
        run([
            "ffmpeg", "-y", "-i", str(video_seg),
            "-f", "lavfi", "-i", f"anullsrc=channel_layout=stereo:sample_rate=44100",
            "-shortest", "-c:v", "copy", "-c:a", "aac", "-b:a", "128k",
            str(out_path),
        ])
    else:
        run([
            "ffmpeg", "-y", "-i", str(video_seg), "-i", str(audio_seg),
            "-c:v", "copy", "-c:a", "aac", "-b:a", "192k",
            "-shortest",
            str(out_path),
        ])


def concat_segments(segments: list[Path], out_path: Path):
    """Concatena uma lista de mp4s usando o demuxer concat do ffmpeg."""
    with tempfile.NamedTemporaryFile("w", suffix=".txt", delete=False) as f:
        for s in segments:
            f.write(f"file '{s.resolve()}'\n")
        list_path = Path(f.name)
    try:
        # re-encode pra evitar problemas de codec mismatch entre segmentos
        run([
            "ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", str(list_path),
            "-c:v", "libx264", "-preset", "slow", "-crf", "16",
            "-pix_fmt", "yuv420p",
            "-c:a", "aac", "-b:a", "192k",
            str(out_path),
        ])
    finally:
        list_path.unlink(missing_ok=True)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--video", required=True)
    ap.add_argument("--audio-dir", required=True)
    ap.add_argument("--timings", required=True,
                    help="JSON file (or path to record_demo output) with scene_timings array")
    ap.add_argument("--output", required=True)
    args = ap.parse_args()

    video = Path(args.video)
    audio_dir = Path(args.audio_dir)
    output = Path(args.output)

    timings_data = json.loads(Path(args.timings).read_text())
    scene_timings = timings_data.get("scene_timings", timings_data)
    tts_manifest = json.loads((audio_dir / "tts_manifest.json").read_text())
    tts_by_idx = {item["scene_index"]: item for item in tts_manifest}

    workdir = Path(tempfile.mkdtemp(prefix="merge-av-"))
    print(f"INFO: workdir = {workdir}")
    final_segments = []

    for st in scene_timings:
        idx = st["scene_index"]
        seg_raw = workdir / f"scene_{idx:03d}_raw.mp4"
        seg_ext = workdir / f"scene_{idx:03d}_ext.mp4"
        seg_final = workdir / f"scene_{idx:03d}_final.mp4"

        cut_segment(video, st["start_ms"], st["end_ms"], seg_raw)

        tts = tts_by_idx.get(idx, {})
        audio_path = tts.get("audio_path")
        audio_dur_s = tts.get("duration_ms", 0) / 1000.0
        video_dur_s = (st["end_ms"] - st["start_ms"]) / 1000.0
        target_dur_s = max(video_dur_s, audio_dur_s, 0.5)

        extend_video_to(seg_raw, target_dur_s, seg_ext)
        mux_segment(seg_ext, Path(audio_path) if audio_path else None,
                    seg_final, target_dur_s)
        final_segments.append(seg_final)
        print(f"INFO: scene {idx} → video {video_dur_s:.2f}s, audio {audio_dur_s:.2f}s, final {target_dur_s:.2f}s")

    output.parent.mkdir(parents=True, exist_ok=True)
    concat_segments(final_segments, output)
    print(f"OK: wrote {output}")

    shutil.rmtree(workdir, ignore_errors=True)


if __name__ == "__main__":
    main()
