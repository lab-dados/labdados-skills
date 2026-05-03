#!/usr/bin/env python3
"""
Gera um clipe de áudio (mp3) por cena do roteiro.

Tenta provedores nessa ordem (até um funcionar):
1. ElevenLabs   — se ELEVENLABS_API_KEY estiver setada
2. OpenAI TTS   — se OPENAI_API_KEY estiver setada
3. edge-tts     — sempre disponível (gratuito, usa voz neural Microsoft via API pública)

Uso: python generate_tts.py <script.json> <output_dir> [--lang pt-BR] [--voice ...] [--provider auto|elevenlabs|openai|edge]

Output: arquivos `<output_dir>/scene_000.mp3`, `scene_001.mp3`, ... e um `tts_manifest.json`
com:
  [{"scene_index": 0, "audio_path": "...", "duration_ms": 5840, "provider": "edge"}, ...]
"""
import argparse
import asyncio
import json
import os
import subprocess
import sys
from pathlib import Path


VOICE_DEFAULTS = {
    "elevenlabs": {"pt-BR": "21m00Tcm4TlvDq8ikWAM", "en": "21m00Tcm4TlvDq8ikWAM"},  # "Rachel"
    "openai": {"pt-BR": "nova", "en": "nova"},
    "edge": {"pt-BR": "pt-BR-FranciscaNeural", "en": "en-US-AriaNeural"},
}


def probe_duration_ms(path: Path) -> int:
    """Use ffprobe to get duration in ms."""
    out = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "default=noprint_wrappers=1:nokey=1", str(path)],
        capture_output=True, text=True, check=True,
    )
    return int(float(out.stdout.strip()) * 1000)


def try_elevenlabs(text: str, out_path: Path, voice_id: str) -> bool:
    if not os.environ.get("ELEVENLABS_API_KEY"):
        return False
    try:
        import requests
        r = requests.post(
            f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}",
            headers={
                "xi-api-key": os.environ["ELEVENLABS_API_KEY"],
                "Content-Type": "application/json",
                "Accept": "audio/mpeg",
            },
            json={"text": text, "model_id": "eleven_multilingual_v2"},
            timeout=60,
        )
        if r.status_code != 200:
            print(f"WARN: ElevenLabs returned {r.status_code}: {r.text[:200]}", file=sys.stderr)
            return False
        out_path.write_bytes(r.content)
        return True
    except Exception as e:
        print(f"WARN: ElevenLabs failed: {e}", file=sys.stderr)
        return False


def try_openai(text: str, out_path: Path, voice: str) -> bool:
    if not os.environ.get("OPENAI_API_KEY"):
        return False
    try:
        import requests
        model = os.environ.get("OPENAI_TTS_MODEL", "gpt-4o-mini-tts")
        payload = {"model": model, "input": text, "voice": voice}
        instructions = os.environ.get("OPENAI_TTS_INSTRUCTIONS")
        if instructions and model.startswith("gpt-4o"):
            payload["instructions"] = instructions
        r = requests.post(
            "https://api.openai.com/v1/audio/speech",
            headers={
                "Authorization": f"Bearer {os.environ['OPENAI_API_KEY']}",
                "Content-Type": "application/json",
            },
            json=payload,
            timeout=60,
        )
        if r.status_code != 200:
            print(f"WARN: OpenAI returned {r.status_code}: {r.text[:200]}", file=sys.stderr)
            return False
        out_path.write_bytes(r.content)
        return True
    except Exception as e:
        print(f"WARN: OpenAI failed: {e}", file=sys.stderr)
        return False


async def try_edge_tts_async(text: str, out_path: Path, voice: str) -> bool:
    try:
        import edge_tts
        communicate = edge_tts.Communicate(text, voice)
        await communicate.save(str(out_path))
        return out_path.exists() and out_path.stat().st_size > 0
    except Exception as e:
        print(f"WARN: edge-tts failed: {e}", file=sys.stderr)
        return False


def try_edge_tts(text: str, out_path: Path, voice: str) -> bool:
    return asyncio.run(try_edge_tts_async(text, out_path, voice))


def synthesize(text: str, out_path: Path, lang: str, provider: str, voice_override: str | None) -> str:
    """Returns the provider name that succeeded, or raises."""
    chain = [provider] if provider != "auto" else ["elevenlabs", "openai", "edge"]
    for prov in chain:
        voice = voice_override or VOICE_DEFAULTS[prov].get(lang, list(VOICE_DEFAULTS[prov].values())[0])
        if prov == "elevenlabs" and try_elevenlabs(text, out_path, voice):
            return "elevenlabs"
        if prov == "openai" and try_openai(text, out_path, voice):
            return "openai"
        if prov == "edge" and try_edge_tts(text, out_path, voice):
            return "edge"
    raise RuntimeError(f"All TTS providers failed for chain {chain}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("script_path")
    ap.add_argument("output_dir")
    ap.add_argument("--lang", default="pt-BR")
    ap.add_argument("--voice", default=None)
    ap.add_argument("--provider", default="auto",
                    choices=["auto", "elevenlabs", "openai", "edge"])
    args = ap.parse_args()

    script = json.loads(Path(args.script_path).read_text())
    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    manifest = []
    for i, scene in enumerate(script["scenes"]):
        narration = (scene.get("narration") or "").strip()
        if not narration:
            print(f"INFO: scene {i} has no narration, skipping audio", file=sys.stderr)
            manifest.append({"scene_index": i, "audio_path": None,
                             "duration_ms": 0, "provider": None})
            continue
        out_path = out_dir / f"scene_{i:03d}.mp3"
        provider = synthesize(narration, out_path, args.lang, args.provider, args.voice)
        dur = probe_duration_ms(out_path)
        manifest.append({"scene_index": i, "audio_path": str(out_path),
                         "duration_ms": dur, "provider": provider})
        print(f"INFO: scene {i} → {out_path.name} ({dur} ms, {provider})", file=sys.stderr)

    manifest_path = out_dir / "tts_manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False))
    print(json.dumps({"manifest": str(manifest_path), "items": manifest}, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
