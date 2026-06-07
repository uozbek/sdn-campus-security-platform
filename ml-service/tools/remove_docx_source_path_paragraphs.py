#!/usr/bin/env python3
from argparse import ArgumentParser
from pathlib import Path
from docx import Document


def remove_paragraph(paragraph):
    element = paragraph._element
    element.getparent().remove(element)
    paragraph._p = paragraph._element = None


def main():
    ap = ArgumentParser()
    ap.add_argument("--docx", required=True)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    in_path = Path(args.docx)
    out_path = Path(args.out)

    doc = Document(in_path)

    removed = []
    for p in list(doc.paragraphs):
        text = p.text.strip()
        if text.startswith("Kaynak: tables/") or text.startswith("Kaynak: figures/"):
            removed.append(text)
            remove_paragraph(p)

    doc.save(out_path)

    print(f"[INFO] Input : {in_path}")
    print(f"[INFO] Output: {out_path}")
    print(f"[INFO] Removed source-path paragraphs: {len(removed)}")
    for item in removed:
        print(f"[REMOVED] {item}")


if __name__ == "__main__":
    main()
