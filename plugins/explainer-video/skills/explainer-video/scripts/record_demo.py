#!/usr/bin/env python3
"""
Grava um vídeo de demo via Playwright a partir de um script.json.

Schema do script.json:
{
  "base_url": "https://...",         # opcional, prepended em "goto" relativos
  "viewport": {"width": 1920, "height": 1080},   # opcional, default 1920x1080
  "slow_mo_ms": 300,                  # opcional, padrão 300
  "show_cursor": true,                # opcional, padrão true (injeta CSS overlay)
  "scenes": [
    {
      "narration": "Texto que vai virar áudio (não usado aqui, só timing).",
      "actions": [
        {"type": "goto", "url": "/"},
        {"type": "wait", "ms": 1500},
        {"type": "click", "selector": "button#login"},
        {"type": "type", "selector": "input[name=email]", "text": "demo@x.com", "delay_ms": 80},
        {"type": "press", "selector": "input[name=email]", "key": "Enter"},
        {"type": "scroll", "selector": ".content", "direction": "down", "amount": 500},
        {"type": "highlight", "selector": ".header"},
        {"type": "screenshot", "path": "step1.png"}
      ],
      "duration_hint_seconds": 8
    }
  ]
}

Tipos de action suportados: goto, wait, click, type, press, scroll, highlight, screenshot, hover.

Uso: python record_demo.py <script.json> <output.mp4>

Saída: produz <output.mp4> e imprime no stdout um JSON com `scene_timings`:
[{"scene_index": 0, "start_ms": 0, "end_ms": 8400}, ...]
para o merge_av.py usar.
"""
import asyncio
import json
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

CURSOR_OVERLAY_JS = """
() => {
  if (document.getElementById('__pw_cursor')) return;
  const dot = document.createElement('div');
  dot.id = '__pw_cursor';
  dot.style.cssText = `
    position: fixed; top: 0; left: 0; width: 24px; height: 24px;
    background: rgba(255,80,80,0.85); border: 2px solid white;
    border-radius: 50%; pointer-events: none; z-index: 2147483647;
    transform: translate(-50%, -50%); transition: top .08s linear, left .08s linear;
    box-shadow: 0 0 0 2px rgba(0,0,0,0.3);
  `;
  document.body.appendChild(dot);
  document.addEventListener('mousemove', (e) => {
    dot.style.left = e.clientX + 'px';
    dot.style.top = e.clientY + 'px';
  }, true);
}
"""

HIGHLIGHT_JS = """
(selector) => {
  const el = document.querySelector(selector);
  if (!el) return;
  const old = el.style.cssText;
  el.style.outline = '4px solid rgba(255,200,0,0.95)';
  el.style.outlineOffset = '4px';
  el.style.transition = 'outline-color .3s';
  setTimeout(() => { el.style.cssText = old; }, 1800);
}
"""


async def execute_action(page, action, base_url):
    t = action["type"]
    if t == "goto":
        url = action["url"]
        if base_url and not url.startswith(("http://", "https://", "file://", "data:", "about:")):
            url = base_url.rstrip("/") + "/" + url.lstrip("/")
        await page.goto(url, wait_until="domcontentloaded")
    elif t == "wait":
        await page.wait_for_timeout(action.get("ms", 1000))
    elif t == "click":
        await page.locator(action["selector"]).first.click(timeout=action.get("timeout_ms", 8000))
    elif t == "hover":
        await page.locator(action["selector"]).first.hover(timeout=action.get("timeout_ms", 8000))
    elif t == "type":
        loc = page.locator(action["selector"]).first
        await loc.click()
        await loc.fill("")
        await loc.type(action["text"], delay=action.get("delay_ms", 60))
    elif t == "press":
        await page.locator(action["selector"]).first.press(action["key"])
    elif t == "scroll":
        sel = action.get("selector", "body")
        amt = action.get("amount", 400)
        direction = action.get("direction", "down")
        sign = 1 if direction == "down" else -1
        # body/html não scrollam por scrollBy; usar scrollingElement ou window.
        await page.evaluate(
            f"(s) => {{"
            f"  const el = document.querySelector(s);"
            f"  const target = (el && el !== document.body && el !== document.documentElement && el.scrollHeight > el.clientHeight) ? el : (document.scrollingElement || document.documentElement);"
            f"  target.scrollBy({{ top: {sign * amt}, behavior: 'smooth' }});"
            f"}}",
            sel,
        )
        await page.wait_for_timeout(900)
    elif t == "highlight":
        await page.evaluate(HIGHLIGHT_JS, action["selector"])
        await page.wait_for_timeout(action.get("hold_ms", 1500))
    elif t == "screenshot":
        await page.screenshot(path=action.get("path", f"shot-{int(time.time())}.png"))
    else:
        print(f"WARN: unknown action type {t!r}, skipping", file=sys.stderr)


async def record(script_path: Path, output_mp4: Path):
    from playwright.async_api import async_playwright

    script = json.loads(script_path.read_text())
    viewport = script.get("viewport", {"width": 1920, "height": 1080})
    slow_mo = script.get("slow_mo_ms", 300)
    show_cursor = script.get("show_cursor", True)
    base_url = script.get("base_url", "")
    color_scheme = script.get("color_scheme", "light")

    workdir = Path(tempfile.mkdtemp(prefix="explainer-video-"))
    print(f"INFO: recording to temp dir {workdir}", file=sys.stderr)

    scene_timings = []
    overall_start = time.monotonic()

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True, slow_mo=slow_mo)
        context = await browser.new_context(
            viewport=viewport,
            record_video_dir=str(workdir),
            record_video_size=viewport,
            color_scheme=color_scheme,
        )
        page = await context.new_page()

        if show_cursor:
            await page.add_init_script(CURSOR_OVERLAY_JS.replace("() => {", "").rsplit("}", 1)[0])
            # add_init_script wants a function body, but to be safe we re-inject after each goto:

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
            print(f"INFO: scene {i} done ({int(scene_end - scene_start)} ms)", file=sys.stderr)

        await context.close()
        await browser.close()

    # Find the produced webm and convert to mp4
    webms = list(workdir.glob("*.webm"))
    if not webms:
        raise RuntimeError(f"No video file produced in {workdir}")
    webm_path = webms[0]
    print(f"INFO: converting {webm_path.name} → {output_mp4.name}", file=sys.stderr)

    output_mp4.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run([
        "ffmpeg", "-y", "-i", str(webm_path),
        "-c:v", "libx264", "-preset", "slow", "-crf", "18",
        "-pix_fmt", "yuv420p",
        str(output_mp4),
    ], check=True, capture_output=True)

    shutil.rmtree(workdir, ignore_errors=True)

    print(json.dumps({"output": str(output_mp4), "scene_timings": scene_timings}, indent=2))


def main():
    if len(sys.argv) != 3:
        print("Usage: record_demo.py <script.json> <output.mp4>", file=sys.stderr)
        sys.exit(1)
    asyncio.run(record(Path(sys.argv[1]), Path(sys.argv[2])))


if __name__ == "__main__":
    main()
