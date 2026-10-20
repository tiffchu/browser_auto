"""Print statement candidates from locally extracted reports for human review."""
import argparse
import json
import re
from pathlib import Path

DATA = Path(__file__).resolve().parent.parent / "data/test_run_2025"
parser = argparse.ArgumentParser()
parser.add_argument("--ranks", default="")
parser.add_argument("--pages", default="")
parser.add_argument("--links", action="store_true")
parser.add_argument("--index", action="store_true")
args = parser.parse_args()
ranks = {int(value) for value in args.ranks.split(",") if value}
selected_pages = {int(value) for value in args.pages.split(",") if value}
if args.links:
    from acquire_test_reports import Links
    for path in sorted(DATA.glob("landing_*.html")):
        rank = int(path.stem.split("_")[1])
        if ranks and rank not in ranks:
            continue
        print("LANDING", rank)
        parser = Links()
        parser.feed(path.read_text(encoding="utf-8"))
        for href, label in parser.links:
            if re.search(r"2025|annual|\.pdf|SCRIPT", href + label, re.I):
                print(href, label)
else:
    for path in sorted(DATA.glob("company_*_pages.json")):
        rank = int(path.name.split("_")[1])
        if ranks and rank not in ranks:
            continue
        print("COMPANY", rank)
        for page in json.loads(path.read_text(encoding="utf-8")):
            text = re.sub(r"[\r\n]+", "\n", page["text"])
            compact = re.sub(r"\s+", " ", text).lower()
            if args.index:
                print(page["pdf_page"], compact[:150], "...", compact[-80:])
                continue
            if selected_pages:
                if page["pdf_page"] not in selected_pages:
                    continue
                print("PDF PAGE", page["pdf_page"], "\n", text)
                continue
            statement = ("consolidated" in compact[:800] and "notes to" not in compact[:300] and
                         re.search(r"(?:statements? of|balance sheets?)", compact[:800]) and
                         re.search(r"total assets|net income|net loss|net earnings|profit for|earnings|loss for|profit \(loss\)", compact))
            if statement:
                print("PDF PAGE", page["pdf_page"])
                for line in text.splitlines():
                    if re.search(r"consolidated|year|\b2025\b|\b2024\b|total assets|net income|net loss|net earnings|profit|earnings|revenue|sales|tax|dollars|thousands|millions", line, re.I):
                        print(line)
            if re.search(r"we have audited", text, re.I):
                print("AUDIT PDF PAGE", page["pdf_page"], "LAST LINES", text.splitlines()[-4:])
