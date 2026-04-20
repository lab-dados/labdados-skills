#!/usr/bin/env python3
"""Parse WhatsApp chat export zip into structured JSON.

Usage:
    python parse_whatsapp.py <zip_path_or_glob> [--since-days N] [--since YYYY-MM-DD]

Output: JSON list on stdout, one object per message:
    {"author": str, "timestamp": ISO8601, "text": str, "is_media": bool}

Handles both iOS and Android export formats. If --since-days or --since is
provided, filters messages newer than that.

Exits with code 0 on success (even if empty), 1 on error. Prints diagnostic
info to stderr.
"""
from __future__ import annotations

import argparse
import glob
import io
import json
import os
import re
import sys
import zipfile
from datetime import datetime, timedelta, timezone
from typing import Iterable


# iOS:   [15/04/2026, 14:32:07] Author: text
IOS_RE = re.compile(
    r"^\[(\d{1,2})/(\d{1,2})/(\d{2,4}),\s+(\d{1,2}):(\d{2})(?::(\d{2}))?\]\s+([^:]+?):\s?(.*)$"
)
# Android: 15/04/2026, 14:32 - Author: text     OR     15/04/26 14:32 - Author: text
ANDROID_RE = re.compile(
    r"^(\d{1,2})/(\d{1,2})/(\d{2,4}),?\s+(\d{1,2}):(\d{2})(?::(\d{2}))?\s*-\s+([^:]+?):\s?(.*)$"
)

MEDIA_MARKERS = (
    "<Media omitted>",
    "<midia oculta>",  # pt-br android
    "<arquivo de mídia oculto>",
    "<anexado:",
    "image omitted",
    "audio omitted",
    "video omitted",
    "sticker omitted",
    "GIF omitted",
)


def parse_line(line: str, date_order: str = "auto"):
    """Parse a WhatsApp header line.

    date_order: "dmy" (BR/EU), "mdy" (US), or "auto" (caller decides).
    Returns dict with author/timestamp/text, or None if not a header line.
    """
    for regex in (IOS_RE, ANDROID_RE):
        m = regex.match(line)
        if m:
            a, b, year, hour, minute, second, author, text = m.groups()
            year_i = int(year)
            if year_i < 100:
                year_i += 2000
            second_i = int(second) if second else 0
            a_i, b_i = int(a), int(b)
            if date_order == "dmy":
                day, month = a_i, b_i
            elif date_order == "mdy":
                day, month = b_i, a_i
            else:
                # auto: let caller do two-pass detection. Return raw parts.
                return {
                    "_raw_a": a_i,
                    "_raw_b": b_i,
                    "year": year_i,
                    "hour": int(hour),
                    "minute": int(minute),
                    "second": second_i,
                    "author": author.strip(),
                    "text": text.strip(),
                }
            try:
                ts = datetime(year_i, month, day, int(hour), int(minute), second_i)
            except ValueError:
                return None
            return {"author": author.strip(), "timestamp": ts, "text": text.strip()}
    return None


def detect_date_order(text: str) -> str:
    """Scan headers looking for an unambiguous D/M or M/D marker."""
    for raw_line in text.splitlines()[:5000]:
        line = raw_line.replace("\u200e", "").replace("\u200f", "").rstrip()
        parts = parse_line(line, date_order="auto")
        if parts is None or "timestamp" in parts:
            continue
        a, b = parts["_raw_a"], parts["_raw_b"]
        if a > 12 and b <= 12:
            return "dmy"
        if b > 12 and a <= 12:
            return "mdy"
    # Ambiguous — default to DMY (more common outside US; user is in BR).
    return "dmy"


def iter_messages(text: str, date_order: str) -> Iterable[dict]:
    current = None
    for raw_line in text.splitlines():
        # WhatsApp sometimes puts invisible LRM/RTL markers around timestamps
        line = raw_line.replace("\u200e", "").replace("\u200f", "").rstrip()
        if not line:
            if current is not None:
                current["text"] += "\n"
            continue
        parsed = parse_line(line, date_order=date_order)
        if parsed:
            if current is not None:
                yield current
            current = parsed
        else:
            # continuation line for previous message
            if current is not None:
                current["text"] = (current["text"] + "\n" + line).strip()
    if current is not None:
        yield current


def find_chat_text_in_zip(zf: zipfile.ZipFile) -> str:
    candidates = [n for n in zf.namelist() if n.lower().endswith(".txt")]
    if not candidates:
        raise FileNotFoundError("No .txt file found inside the zip")
    # Prefer _chat.txt or WhatsApp Chat*.txt
    preferred = [
        n for n in candidates if "chat" in os.path.basename(n).lower()
    ]
    name = preferred[0] if preferred else candidates[0]
    with zf.open(name) as f:
        raw = f.read()
    # Handle BOM and utf-8
    try:
        return raw.decode("utf-8-sig")
    except UnicodeDecodeError:
        return raw.decode("latin-1", errors="replace")


def resolve_zip_path(pattern: str) -> str:
    # Accept exact file path first
    if os.path.isfile(pattern):
        return pattern
    matches = sorted(glob.glob(pattern), key=os.path.getmtime, reverse=True)
    if not matches:
        # Try common fallbacks in cwd
        fallbacks = sorted(
            glob.glob("WhatsApp Chat*.zip") + glob.glob("*.zip"),
            key=os.path.getmtime,
            reverse=True,
        )
        if fallbacks:
            return fallbacks[0]
        raise FileNotFoundError(f"No zip matched: {pattern}")
    return matches[0]


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("zip", help="Path or glob to WhatsApp export zip")
    p.add_argument(
        "--since-days",
        type=int,
        default=None,
        help="Only include messages from the last N days",
    )
    p.add_argument(
        "--since",
        type=str,
        default=None,
        help="Only include messages from this date onward (YYYY-MM-DD)",
    )
    p.add_argument(
        "--date-order",
        choices=["auto", "dmy", "mdy"],
        default="auto",
        help="Date format in the export. Default: auto-detect.",
    )
    args = p.parse_args()

    try:
        zip_path = resolve_zip_path(args.zip)
    except FileNotFoundError as e:
        print(f"error: {e}", file=sys.stderr)
        return 1

    print(f"# using zip: {zip_path}", file=sys.stderr)

    with zipfile.ZipFile(zip_path) as zf:
        chat_text = find_chat_text_in_zip(zf)

    date_order = args.date_order
    if date_order == "auto":
        date_order = detect_date_order(chat_text)
        print(f"# detected date order: {date_order}", file=sys.stderr)

    cutoff = None
    if args.since_days is not None:
        cutoff = datetime.now() - timedelta(days=args.since_days)
    elif args.since:
        cutoff = datetime.fromisoformat(args.since)

    out = []
    for msg in iter_messages(chat_text, date_order=date_order):
        if cutoff is not None and msg["timestamp"] < cutoff:
            continue
        is_media = any(marker.lower() in msg["text"].lower() for marker in MEDIA_MARKERS)
        out.append(
            {
                "author": msg["author"],
                "timestamp": msg["timestamp"].isoformat(),
                "text": msg["text"],
                "is_media": is_media,
            }
        )

    print(f"# parsed {len(out)} messages in window", file=sys.stderr)
    json.dump(out, sys.stdout, ensure_ascii=False, indent=2)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
