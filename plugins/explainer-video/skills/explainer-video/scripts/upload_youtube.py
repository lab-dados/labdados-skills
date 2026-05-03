#!/usr/bin/env python3
"""
Faz upload de um vídeo no YouTube como NÃO-LISTADO via YouTube Data API v3.

Pré-requisitos:
1. Google Cloud project com YouTube Data API v3 habilitada
2. OAuth 2.0 client (Desktop app) — baixar client_secret.json
3. Setar env var YT_CLIENT_SECRET_PATH apontando para o client_secret.json
4. Token de acesso é cacheado em ~/.explainer-video-yt-token.json após primeiro login

Uso:
  python upload_youtube.py \
      --video final.mp4 \
      --title "Tour da minha ferramenta" \
      --description "Descrição..." \
      [--tags tag1,tag2] \
      [--category 28]   # 28 = Science & Tech (default), 22 = People & Blogs, etc

Saída (stdout JSON):
  {"video_id": "...", "url": "https://youtu.be/...", "privacy": "unlisted"}

Em caso de falta de credenciais, sai com código 2 e instruções no stderr.
"""
import argparse
import json
import os
import sys
from pathlib import Path

SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]
TOKEN_PATH = Path.home() / ".explainer-video-yt-token.json"


def get_credentials():
    try:
        from google.oauth2.credentials import Credentials
        from google_auth_oauthlib.flow import InstalledAppFlow
        from google.auth.transport.requests import Request
    except ImportError:
        print("ERROR: missing dependencies. Run:", file=sys.stderr)
        print("  pip install --break-system-packages google-api-python-client google-auth-oauthlib", file=sys.stderr)
        sys.exit(2)

    creds = None
    if TOKEN_PATH.exists():
        creds = Credentials.from_authorized_user_file(str(TOKEN_PATH), SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            client_secret = os.environ.get("YT_CLIENT_SECRET_PATH")
            if not client_secret or not Path(client_secret).exists():
                print("ERROR: YT_CLIENT_SECRET_PATH not set or file missing.", file=sys.stderr)
                print("Steps to set up:", file=sys.stderr)
                print("  1. Go to https://console.cloud.google.com/", file=sys.stderr)
                print("  2. Create or select a project, enable 'YouTube Data API v3'", file=sys.stderr)
                print("  3. Credentials → Create OAuth client ID → Desktop app", file=sys.stderr)
                print("  4. Download the client_secret.json", file=sys.stderr)
                print("  5. export YT_CLIENT_SECRET_PATH=/path/to/client_secret.json", file=sys.stderr)
                sys.exit(2)
            flow = InstalledAppFlow.from_client_secrets_file(client_secret, SCOPES)
            # run_local_server abre o navegador no localhost para auth
            creds = flow.run_local_server(port=0)
        TOKEN_PATH.write_text(creds.to_json())
        print(f"INFO: cached token to {TOKEN_PATH}", file=sys.stderr)

    return creds


def upload(video_path: Path, title: str, description: str, tags: list[str],
           category: str, privacy: str = "unlisted") -> dict:
    from googleapiclient.discovery import build
    from googleapiclient.http import MediaFileUpload

    creds = get_credentials()
    youtube = build("youtube", "v3", credentials=creds)

    body = {
        "snippet": {
            "title": title,
            "description": description,
            "tags": tags,
            "categoryId": category,
        },
        "status": {
            "privacyStatus": privacy,        # "unlisted" | "private" | "public"
            "selfDeclaredMadeForKids": False,
        },
    }

    media = MediaFileUpload(str(video_path), chunksize=-1, resumable=True,
                            mimetype="video/*")
    request = youtube.videos().insert(
        part="snippet,status",
        body=body,
        media_body=media,
    )

    response = None
    while response is None:
        status, response = request.next_chunk()
        if status:
            print(f"INFO: upload progress {int(status.progress() * 100)}%", file=sys.stderr)

    return {
        "video_id": response["id"],
        "url": f"https://youtu.be/{response['id']}",
        "privacy": response["status"]["privacyStatus"],
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--video", required=True)
    ap.add_argument("--title", required=True)
    ap.add_argument("--description", default="")
    ap.add_argument("--tags", default="")
    ap.add_argument("--category", default="28")
    ap.add_argument("--privacy", default="unlisted",
                    choices=["unlisted", "private", "public"])
    args = ap.parse_args()

    tags = [t.strip() for t in args.tags.split(",") if t.strip()]
    result = upload(Path(args.video), args.title, args.description,
                    tags, args.category, args.privacy)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
