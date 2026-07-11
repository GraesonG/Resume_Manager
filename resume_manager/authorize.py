"""One-time Drive OAuth sign-in.

Run once:  python -m resume_manager.authorize
Opens a browser to grant Drive access and saves a reusable token so uploads
run non-interactively thereafter.
"""

from __future__ import annotations

from . import gdrive


def main() -> None:
    print("Opening a browser to authorize Google Drive access…")
    result = gdrive.authorize(interactive=True)
    if result["authorized"]:
        print(f"Authorized. Token saved to: {result['token_path']}")
    else:
        print("Authorization did not complete.")


if __name__ == "__main__":
    main()
