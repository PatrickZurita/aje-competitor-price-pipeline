from __future__ import annotations

import argparse
import json
from pathlib import Path

from google_auth_oauthlib.flow import InstalledAppFlow

SCOPES = [
    "https://www.googleapis.com/auth/drive.file",
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/gmail.send",
]


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Authorize Google Drive, Sheets and Gmail for the AJE pipeline."
    )
    parser.add_argument("--client-secrets", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()

    flow = InstalledAppFlow.from_client_secrets_file(str(args.client_secrets), SCOPES)
    credentials = flow.run_local_server(port=0)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(credentials.to_json(), encoding="utf-8")
    print(f"OAuth credentials saved locally to {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
