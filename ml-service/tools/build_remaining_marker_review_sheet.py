#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path
import pandas as pd


def clean(value) -> str:
    if value is None:
        return ""
    s = str(value)
    if s.lower() == "nan":
        return ""
    return s.strip()


def main() -> None:
    audit_path = Path("docs/inline_reference_marker_audit.csv")
    override_path = Path("docs/inline_citation_manual_override.csv")

    if not audit_path.exists():
        raise SystemExit(f"[ERROR] Missing audit CSV: {audit_path}")

    audit = pd.read_csv(audit_path).fillna("")

    if override_path.exists():
        override = pd.read_csv(override_path).fillna("")
        replaced = set(
            override.loc[override["final_action"].eq("replace"), "marker"].astype(str)
        )
    else:
        replaced = set()

    rows = []
    for marker, group in audit.groupby("marker"):
        if marker in replaced:
            continue

        contexts = []
        for _, r in group.iterrows():
            contexts.append(
                f"{clean(r.get('file'))}:L{clean(r.get('line'))} — {clean(r.get('context'))}"
            )

        first = group.iloc[0]
        rows.append({
            "marker": marker,
            "occurrences": len(group),
            "current_suggested_citation": clean(first.get("authors")) + " / " + clean(first.get("year")),
            "title": clean(first.get("title")),
            "venue": clean(first.get("venue")),
            "relevance": clean(first.get("relevance")),
            "contexts": "\n".join(contexts),
            "manual_decision": "",
            "final_inline_citation": "",
            "final_action": "manual_review",
            "notes": "",
        })

    out = pd.DataFrame(rows).sort_values(["marker"])

    csv_out = Path("docs/remaining_inline_marker_manual_review.csv")
    md_out = Path("docs/remaining_inline_marker_manual_review.md")

    out.to_csv(csv_out, index=False)

    md = []
    md.append("# Remaining Inline Marker Manual Review")
    md.append("")
    md.append("Bu dosya, otomatik dönüştürülmeyen teknik atıf marker’larının bağlam odaklı manuel kontrolü için hazırlanmıştır.")
    md.append("")
    md.append("| Marker | Count | Suggested source | Title | Relevance | Decision | Final citation | Notes |")
    md.append("|---|---:|---|---|---|---|---|---|")

    for _, r in out.iterrows():
        suggested = clean(r["current_suggested_citation"]).replace("|", "\\|")
        title = clean(r["title"]).replace("|", "\\|")
        notes = clean(r["notes"]).replace("|", "\\|")
        md.append(
            f"| {r['marker']} | {r['occurrences']} | {suggested} | {title[:140]} | "
            f"{r['relevance']} | {r['manual_decision']} | {r['final_inline_citation']} | {notes} |"
        )

    md.append("")
    md.append("## Contexts")
    md.append("")

    for _, r in out.iterrows():
        md.append(f"### {r['marker']}")
        md.append("")
        md.append(f"- Title: {r['title']}")
        md.append(f"- Suggested source: {r['current_suggested_citation']}")
        md.append(f"- Relevance: {r['relevance']}")
        md.append("")
        for ctx in clean(r["contexts"]).splitlines():
            md.append(f"- {ctx}")
        md.append("")

    md_out.write_text("\n".join(md), encoding="utf-8")

    print("[INFO] CSV:", csv_out)
    print("[INFO] MD :", md_out)
    print("[INFO] Rows:", len(out))


if __name__ == "__main__":
    main()
