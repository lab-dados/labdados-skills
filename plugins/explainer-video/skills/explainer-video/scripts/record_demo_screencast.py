#!/usr/bin/env python3
"""
Variante do record_demo.py que captura via CDP Page.startScreencast em vez do
record_video_dir do Playwright. Bypassa o codec VP8 lossy do Chromium e produz
H.264 de alta qualidade direto dos PNGs.

Uso: python record_demo_screencast.py <script.json> <output.mp4>

Mesmo schema de script.json que record_demo.py. Adicional:
  "screencast_fps": 24    (default 24, frames-per-second alvo)
  "screencast_quality": 95 (default 95, JPEG quality 1-100)
"""
import asyncio
import base64
import json
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

# Reutiliza a lógica de execute_action e os JS overlays do script principal.
sys.path.insert(0, str(Path(__file__).parent))
from record_demo import execute_action, CURSOR_OVERLAY_JS  # noqa: E402


async def record(script_path: Path, output_mp4: Path):
    from playwright.async_api import async_playwright

    script = json.loads(script_path.read_text())
    viewport = script.get("viewport", {"width": 1920, "height": 1080})
    slow_mo = script.get("slow_mo_ms", 300)
    show_cursor = script.get("show_cursor", True)
    base_url = script.get("base_url", "")
    color_scheme = script.get("color_scheme", "light")
    fps = script.get("screencast_fps", 24)
    quality = script.get("screencast_quality", 95)

    workdir = Path(tempfile.mkdtemp(prefix="explainer-screencast-"))
    frames_dir = workdir / "frames"
    frames_dir.mkdir()
    print(f"INFO: capturing frames to {frames_dir}", file=sys.stderr)

    scene_timings = []
    frame_records = []  # (relative_seconds, frame_path)
    overall_start = None

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True, slow_mo=slow_mo)
        context = await browser.new_context(
            viewport=viewport,
            color_scheme=color_scheme,
        )
        page = await context.new_page()

        cdp = await context.new_cdp_session(page)

        frame_idx = [0]

        async def on_screencast_frame(params):
            # Salva frame e ack pra continuar recebendo.
            i = frame_idx[0]
            frame_idx[0] += 1
            ts = time.monotonic() - overall_start if overall_start else 0.0
            data = base64.b64decode(params["data"])
            path = frames_dir / f"frame_{i:06d}.jpg"
            path.write_bytes(data)
            frame_records.append((ts, path))
            try:
                await cdp.send("Page.screencastFrameAck",
                               {"sessionId": params["sessionId"]})
            except Exception:
                pass

        cdp.on("Page.screencastFrame",
               lambda params: asyncio.create_task(on_screencast_frame(params)))

        # Vai pra about:blank ANTES de iniciar o screencast pra evitar
        # capturar a tela preta inicial do Chromium.
        await page.goto("about:blank")
        await page.wait_for_timeout(200)

        # everyNthFrame: 1 = recebe todo frame que o navegador renderiza.
        # Em screencast com pouca atividade, o navegador envia menos frames
        # naturalmente — então timing real é preservado pelos timestamps.
        await cdp.send("Page.startScreencast", {
            "format": "jpeg",
            "quality": quality,
            "everyNthFrame": 1,
        })

        # Warm-up: descarta os primeiros frames (podem ser tela em branco
        # ou em transição). Reseta após o warm-up pra timing começar do zero.
        await page.wait_for_timeout(300)
        frame_records.clear()
        frame_idx[0] = 0
        # Limpa o diretório também, pra não confundir indexação.
        for old in frames_dir.glob("frame_*.jpg"):
            old.unlink()
        overall_start = time.monotonic()

        for i, scene in enumerate(script["scenes"]):
            scene_start = (time.monotonic() - overall_start) * 1000
            for action in scene.get("actions", []):
                await execute_action(page, action, base_url)
                if show_cursor:
                    try:
                        await page.evaluate(CURSOR_OVERLAY_JS)
                    except Exception:
                        pass
            scene_end = (time.monotonic() - overall_start) * 1000
            scene_timings.append({
                "scene_index": i,
                "start_ms": int(scene_start),
                "end_ms": int(scene_end),
            })
            print(f"INFO: scene {i} done ({int(scene_end - scene_start)} ms)",
                  file=sys.stderr)

        try:
            await cdp.send("Page.stopScreencast")
        except Exception:
            pass

        await context.close()
        await browser.close()

    print(f"INFO: captured {len(frame_records)} frames", file=sys.stderr)

    # Frames vêm com timestamp irregular (chromium só envia quando há mudança).
    # Deduplica frames recebidos quase simultâneos (< 30ms) que causam piscadas
    # durante transições rápidas, e usa concat demuxer com "duration" preservando timing.
    if not frame_records:
        raise RuntimeError("No frames captured")

    deduped = [frame_records[0]]
    for ts, path in frame_records[1:]:
        if ts - deduped[-1][0] >= 0.030:
            deduped.append((ts, path))
        else:
            path.unlink(missing_ok=True)
    print(f"INFO: deduped {len(frame_records)} → {len(deduped)} frames", file=sys.stderr)

    total_duration = deduped[-1][0]
    list_path = workdir / "frames.txt"
    with list_path.open("w") as f:
        for idx, (ts, path) in enumerate(deduped):
            next_ts = (deduped[idx + 1][0]
                       if idx + 1 < len(deduped) else ts + 1.0 / fps)
            duration = max(1.0 / 60, next_ts - ts)
            f.write(f"file '{path.resolve().as_posix()}'\n")
            f.write(f"duration {duration:.4f}\n")
        # Último frame precisa ser repetido pra concat fechar o último duration.
        f.write(f"file '{deduped[-1][1].resolve().as_posix()}'\n")

    # -vsync cfr + -r força framerate constante sem interpolação ruim.
    # O concat demuxer já posiciona os frames no timeline correto via duration.
    output_mp4.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run([
        "ffmpeg", "-y",
        "-f", "concat", "-safe", "0", "-i", str(list_path),
        "-vsync", "cfr", "-r", str(fps),
        "-c:v", "libx264", "-preset", "slow", "-crf", "16",
        "-pix_fmt", "yuv420p",
        str(output_mp4),
    ], check=True, capture_output=True)

    print(f"INFO: encoded {output_mp4.name} ({total_duration:.2f}s, {fps}fps target)",
          file=sys.stderr)

    shutil.rmtree(workdir, ignore_errors=True)

    print(json.dumps({"output": str(output_mp4),
                      "scene_timings": scene_timings}, indent=2))


def main():
    if len(sys.argv) != 3:
        print("Usage: record_demo_screencast.py <script.json> <output.mp4>",
              file=sys.stderr)
        sys.exit(1)
    asyncio.run(record(Path(sys.argv[1]), Path(sys.argv[2])))


if __name__ == "__main__":
    main()
