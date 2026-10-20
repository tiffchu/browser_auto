import argparse
from pathlib import Path
import pypdfium2 as pdfium

parser = argparse.ArgumentParser()
parser.add_argument("rank", type=int)
parser.add_argument("pages")
args = parser.parse_args()
root = Path(__file__).resolve().parent.parent
out = root / "tmp/pdfs"
out.mkdir(parents=True, exist_ok=True)
with pdfium.PdfDocument(root / f"data/test_run_2025/company_{args.rank:02d}.pdf") as pdf:
    for number in map(int, args.pages.split(",")):
        image = pdf[number - 1].render(scale=1.5).to_pil()
        path = out / f"company_{args.rank:02d}_page_{number}.png"
        image.save(path)
        print(path)
