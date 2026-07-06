"""One-time knowledge ingestion.

Reads your resume PDF and (optionally) fetches your portfolio / GitHub page, then writes
everything into knowledge/about_me.md. The voice agent only ever reads that local file —
it never goes to the network during a call.

Your info is static, so just run this manually whenever your resume/portfolio actually
changes:

    python ingest.py --resume knowledge/resume.pdf --url https://your-portfolio.com --url https://github.com/you

You can pass --url multiple times. After it runs, open knowledge/about_me.md and tidy it
up by hand if you like — it's plain Markdown.
"""

import argparse
from pathlib import Path

import requests
from bs4 import BeautifulSoup
from pypdf import PdfReader

HERE = Path(__file__).parent
KNOWLEDGE_DIR = HERE / "knowledge"
OUTPUT = KNOWLEDGE_DIR / "about_me.md"


def extract_pdf(path: Path) -> str:
    reader = PdfReader(str(path))
    pages = [page.extract_text() or "" for page in reader.pages]
    text = "\n".join(pages)
    # Collapse excessive blank lines.
    return "\n".join(line.rstrip() for line in text.splitlines() if line.strip())


def fetch_url(url: str) -> str:
    resp = requests.get(url, timeout=20, headers={"User-Agent": "voice-agent-ingest/1.0"})
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")
    for tag in soup(["script", "style", "nav", "footer", "header", "noscript"]):
        tag.decompose()
    text = soup.get_text(separator="\n")
    # Drop blank/duplicate-whitespace lines.
    return "\n".join(line.strip() for line in text.splitlines() if line.strip())


def main() -> None:
    parser = argparse.ArgumentParser(description="Compile resume + URLs into knowledge/about_me.md")
    parser.add_argument("--resume", type=Path, help="Path to your resume PDF (e.g. knowledge/resume.pdf)")
    parser.add_argument("--url", action="append", default=[], help="Portfolio / GitHub URL (repeatable)")
    args = parser.parse_args()

    if not args.resume and not args.url:
        parser.error("Provide at least --resume and/or one --url")

    KNOWLEDGE_DIR.mkdir(exist_ok=True)
    sections: list[str] = []

    if args.resume:
        if not args.resume.exists():
            parser.error(f"Resume not found: {args.resume}")
        print(f"Reading resume: {args.resume}")
        sections.append("## Resume\n\n" + extract_pdf(args.resume))

    for url in args.url:
        print(f"Fetching: {url}")
        try:
            sections.append(f"## Source: {url}\n\n" + fetch_url(url))
        except Exception as exc:  # noqa: BLE001 - surface fetch problems but keep going
            print(f"  ! could not fetch {url}: {exc}")

    body = "\n\n---\n\n".join(sections)
    OUTPUT.write_text(f"# About Me (compiled knowledge)\n\n{body}\n", encoding="utf-8")
    print(f"\nWrote {OUTPUT} ({len(body)} chars).")
    print("Open it and clean it up by hand if needed — it's read verbatim by the agent.")


if __name__ == "__main__":
    main()
