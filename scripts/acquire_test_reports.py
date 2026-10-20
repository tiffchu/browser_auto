"""Acquire explicitly selected public report URLs and extract PDF text for review."""
import argparse
import concurrent.futures
import hashlib
import json
import re
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlsplit
from urllib.parse import urljoin
from urllib.robotparser import RobotFileParser

import pypdfium2 as pdfium
import requests

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data/test_run_2025"


class Links(HTMLParser):
    def __init__(self):
        super().__init__()
        self.links = []
        self.current = None

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == "a" and attrs.get("href"):
            self.current = [attrs["href"], ""]
        if tag == "script" and attrs.get("src"):
            self.links.append([attrs["src"], "SCRIPT"])

    def handle_data(self, data):
        if self.current is not None:
            self.current[1] += data.strip()

    def handle_endtag(self, tag):
        if tag == "a" and self.current:
            self.links.append(self.current)
            self.current = None


def fetch_links(entry):
    url = entry.get("landing_url")
    if not url:
        return None
    result = requests.get(url, timeout=30)
    result.raise_for_status()
    (DATA / f"landing_{entry['input_rank']:02d}.html").write_text(result.text, encoding="utf-8")
    parser = Links()
    parser.feed(result.text)
    return {"rank": entry["input_rank"], "links": [[urljoin(url, href), label] for href, label in parser.links
             if re.search(r"2025|annual|\.pdf|SCRIPT", href + " " + label, re.I)]}


def acquire(entry):
    rank, url = entry["input_rank"], entry.get("report_url")
    if not url:
        return {"rank": rank, "status": "no_url"}
    path = DATA / f"company_{rank:02d}.pdf"
    text_path = DATA / f"company_{rank:02d}_pages.json"
    try:
        if not path.exists():
            origin = urlsplit(url)
            robots_url = f"{origin.scheme}://{origin.netloc}/robots.txt"
            robots = requests.get(robots_url, timeout=15)
            if robots.status_code == 200:
                rules = RobotFileParser()
                rules.parse(robots.text.splitlines())
                if not rules.can_fetch("FinancialStatementResearch", url):
                    raise PermissionError("robots.txt disallows the report path")
            # RFC 9309 section 2.3.1.3: 4xx robots response is unavailable,
            # not a Disallow directive. Actual report HTTP access is still enforced.
            elif not (400 <= robots.status_code < 500 and robots.status_code != 429):
                raise PermissionError(f"robots.txt access unresolved: {robots.status_code}")
            result = requests.get(url, timeout=60)
            result.raise_for_status()
            if not result.content.startswith(b"%PDF"):
                raise ValueError("URL did not return a PDF")
            path.write_bytes(result.content)
        if not text_path.exists():
            with pdfium.PdfDocument(path) as pdf:
                pages = []
                for i in range(len(pdf)):
                    page = pdf[i]
                    text_page = page.get_textpage()
                    pages.append({"pdf_page": i + 1, "text": text_page.get_text_bounded() or ""})
                    text_page.close()
                    page.close()
            text_path.write_text(json.dumps(pages, ensure_ascii=False), encoding="utf-8")
        return {"rank": rank, "status": "downloaded", "file": str(path),
                "sha256": hashlib.sha256(path.read_bytes()).hexdigest()}
    except Exception as error:
        return {"rank": rank, "status": "error", "error": str(error)}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--ranks", default="")
    parser.add_argument("--links", action="store_true")
    parser.add_argument("--fx", action="store_true")
    args = parser.parse_args()
    DATA.mkdir(parents=True, exist_ok=True)
    if args.fx:
        url = "https://www.bankofcanada.ca/valet/observations/FXUSDCAD/json?start_date=2025-12-20&end_date=2025-12-31"
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        (DATA / "bank_of_canada_fx.json").write_text(response.text, encoding="utf-8")
        print(response.text)
        return 0
    manifest = json.loads((ROOT / "inputs/test_run_2025_sources.json").read_text(encoding="utf-8"))
    selected = {int(value) for value in args.ranks.split(",") if value}
    entries = [entry for entry in manifest if not selected or entry["input_rank"] in selected]
    # PDFium is not thread-safe. Each worker process owns its PDF engine state.
    with concurrent.futures.ProcessPoolExecutor(max_workers=4) as pool:
        results = []
        for task in concurrent.futures.as_completed([pool.submit(fetch_links if args.links else acquire, entry) for entry in entries]):
            try:
                result = task.result()
            except Exception as error:
                result = {"status": "error", "error": str(error)}
            results.append(result)
            print(json.dumps(result), flush=True)
    print(json.dumps(results, indent=2))
    (DATA / "acquisition_log.json").write_text(json.dumps(results, indent=2), encoding="utf-8")
    return 1 if any(item and item.get("status") == "error" for item in results) else 0


if __name__ == "__main__":
    raise SystemExit(main())
