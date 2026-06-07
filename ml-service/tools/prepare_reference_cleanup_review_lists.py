#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd


OUT_OF_SCOPE_TERMS = [
    "moodle",
    "learning management",
    "chatbot",
    "chatgpt",
    "education",
    "student",
    "scholarship",
    "international",
    "solar",
    "photovoltaic",
    "stock forecasting",
    "autism",
    "eeg",
    "landslide",
    "seru production",
    "biometric",
    "gene expression",
    "government scholarship",
    "higher education",
    "language learning",
]

METHOD_BACKGROUND_TERMS = [
    "support-vector",
    "support vector",
    "machine learning",
    "feature selection",
    "particle swarm",
    "grey wolf",
    "gray wolf",
    "harris hawks",
    "dragonfly",
    "metaheuristic",
    "data preprocessing",
    "logistic regression",
    "decision forest",
    "ensemble",
    "xgboost",
    "lightgbm",
    "lgbm",
    "svm",
]


def clean(value) -> str:
    if value is None:
        return ""
    s = str(value)
    if s.lower() == "nan":
        return ""
    return s.strip()


def blob(row) -> str:
    return " ".join([
        clean(row.get("id")),
        clean(row.get("year")),
        clean(row.get("authors")),
        clean(row.get("title")),
        clean(row.get("venue")),
        clean(row.get("relevance_to_this_thesis")),
    ]).lower()


def has_any(text: str, terms: list[str]) -> bool:
    return any(t in text for t in terms)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--tracking-csv",
        default="docs/literature_review/literature_tracking_table.csv",
    )
    parser.add_argument(
        "--refined-audit-csv",
        default="docs/compared_studies_bibliography_audit_refined.csv",
    )
    parser.add_argument(
        "--out-dir",
        default="docs",
    )
    args = parser.parse_args()

    tracking = pd.read_csv(args.tracking_csv).fillna("")
    audit = pd.read_csv(args.refined_audit_csv).fillna("") if Path(args.refined_audit_csv).exists() else pd.DataFrame()

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    # Merge audit status into tracking when available.
    if not audit.empty and "id" in audit.columns:
        audit_small = audit[[
            c for c in [
                "id",
                "status",
                "required_for_bibliography",
                "in_bibliography",
                "domain_relevant",
                "out_of_scope",
                "selection_reason",
            ]
            if c in audit.columns
        ]].drop_duplicates("id")
        df = tracking.merge(audit_small, on="id", how="left")
    else:
        df = tracking.copy()
        df["status"] = ""

    rows_out_scope = []
    rows_method = []
    rows_manual = []

    for _, row in df.iterrows():
        rid = clean(row.get("id"))
        b = blob(row)
        relevance = clean(row.get("relevance_to_this_thesis"))

        is_out = has_any(b, OUT_OF_SCOPE_TERMS) or clean(row.get("status")) == "excluded_low_or_out_of_scope" and clean(row.get("out_of_scope")) == "True"
        is_method = has_any(b, METHOD_BACKGROUND_TERMS)

        base = {
            "id": rid,
            "year": clean(row.get("year")).replace(".0", ""),
            "authors": clean(row.get("authors")),
            "title": clean(row.get("title")),
            "venue": clean(row.get("venue")),
            "relevance_to_this_thesis": relevance,
            "audit_status": clean(row.get("status")),
            "in_bibliography": clean(row.get("in_bibliography")),
            "domain_relevant": clean(row.get("domain_relevant")),
            "out_of_scope": clean(row.get("out_of_scope")),
            "decision": "",
            "final_action": "",
            "notes": "",
        }

        if rid.startswith("MAN"):
            r = base.copy()
            r["suggested_decision"] = "review_manual_duplicate_or_promote"
            r["decision_options"] = "canonical_duplicate | promote_to_canonical | discard_manual"
            rows_manual.append(r)
            continue

        if is_out:
            r = base.copy()
            r["suggested_decision"] = "exclude_from_thesis"
            r["decision_options"] = "exclude_from_thesis | keep_method_background | keep_domain_relevant"
            rows_out_scope.append(r)
        elif relevance == "Low" and is_method:
            r = base.copy()
            r["suggested_decision"] = "review_method_background"
            r["decision_options"] = "keep_method_background | exclude_from_thesis"
            rows_method.append(r)

    out_scope = pd.DataFrame(rows_out_scope)
    method = pd.DataFrame(rows_method)
    manual = pd.DataFrame(rows_manual)

    out_scope_path = out_dir / "out_of_scope_reference_candidates.csv"
    method_path = out_dir / "method_background_low_relevance_candidates.csv"
    manual_path = out_dir / "manual_reference_review_candidates.csv"

    out_scope.to_csv(out_scope_path, index=False)
    method.to_csv(method_path, index=False)
    manual.to_csv(manual_path, index=False)

    md = []
    md.append("# Reference Cleanup Review Lists")
    md.append("")
    md.append("Bu dosya, kaynakça ve literatür takip tablosu temizliği için üretilen inceleme listelerini özetler.")
    md.append("")
    md.append("| Liste | Dosya | Kayıt sayısı | Amaç |")
    md.append("|---|---|---:|---|")
    md.append(f"| Out of scope candidates | `{out_scope_path}` | {len(out_scope)} | Konu dışı kaynakları kaynakça/sentez dışı bırakmak |")
    md.append(f"| Method background low relevance candidates | `{method_path}` | {len(method)} | Low relevance ama yöntemsel olarak tutulabilecek kaynakları seçmek |")
    md.append(f"| Manual reference review candidates | `{manual_path}` | {len(manual)} | MAN kayıtlarını duplicate/promote/discard olarak sınıflamak |")
    md.append("")
    md.append("## Karar Alanları")
    md.append("")
    md.append("- `decision`: kullanıcı tarafından doldurulacak karar.")
    md.append("- `final_action`: karar uygulandıktan sonra sistem tarafından/manuel doldurulabilir.")
    md.append("- `notes`: gerekçe veya canonical karşılık notu.")
    md.append("")
    md.append("## Önerilen Kararlar")
    md.append("")
    md.append("### Out of scope")
    md.append("")
    md.append("- `exclude_from_thesis`: tez kaynakçası ve sentezinden çıkar.")
    md.append("- `keep_method_background`: yöntemsel arka plan için tut.")
    md.append("- `keep_domain_relevant`: konuya aslında ilgiliyse tut.")
    md.append("")
    md.append("### MAN kayıtları")
    md.append("")
    md.append("- `canonical_duplicate`: BIB/LR karşılığı var, MAN kaynakçaya girmez.")
    md.append("- `promote_to_canonical`: değerli ve canonical karşılığı yok, yeni BIB/LR kaydı açılmalı.")
    md.append("- `discard_manual`: eksik/kırpılmış/doğrulanmamış, kullanılmayacak.")

    review_md = out_dir / "reference_cleanup_review_lists.md"
    review_md.write_text("\n".join(md), encoding="utf-8")

    print("[INFO] Out of scope:", out_scope_path, len(out_scope))
    print("[INFO] Method background:", method_path, len(method))
    print("[INFO] Manual review:", manual_path, len(manual))
    print("[INFO] Summary:", review_md)


if __name__ == "__main__":
    main()
