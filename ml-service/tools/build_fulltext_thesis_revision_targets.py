#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path
from datetime import datetime
import pandas as pd


def has_value(row, col: str) -> bool:
    return bool(str(row.get(col, "")).strip())


def contains_any(text: str, terms) -> bool:
    t = str(text or "").lower()
    return any(term.lower() in t for term in terms)


def classify_revision_targets(row):
    targets = []
    reasons = []

    title = str(row.get("title", ""))
    dataset = str(row.get("dataset_signals_found", ""))
    sdn = str(row.get("sdn_testbed_signals_found", ""))
    mitigation = str(row.get("mitigation_signals_found", ""))
    runtime = str(row.get("runtime_signals_found", ""))
    fs = str(row.get("feature_selection_signals_found", ""))
    models = str(row.get("model_signals_found", ""))
    metrics = str(row.get("metric_signals_found", ""))
    nsl_policy = str(row.get("nsl_kdd_policy_after_fulltext", ""))

    all_text = " ".join([title, dataset, sdn, mitigation, runtime, fs, models, metrics])

    # NSL-KDD politika notu
    if nsl_policy == "context_only_if_needed" or contains_any(all_text, ["NSL-KDD", "KDD Cup"]):
        targets.append("Context only")
        reasons.append("NSL-KDD/KDD signal detected; thesis core should remain CIC-DDoS2019/SDN runtime focused.")
        return targets, reasons

    # Bölüm 2: kavramsal/method background
    if has_value(row, "feature_selection_signals_found") or has_value(row, "model_signals_found") or has_value(row, "metric_signals_found"):
        targets.append("Bölüm 2")
        reasons.append("Supports conceptual/method background: feature selection, ML/DL models, or evaluation metrics.")

    # Bölüm 3: literatür karşılaştırma
    if has_value(row, "sdn_testbed_signals_found") or contains_any(all_text, ["DDoS", "SDN", "software-defined", "intrusion detection"]):
        targets.append("Bölüm 3")
        reasons.append("Supports literature comparison on SDN/DDoS/ML-based IDS studies.")

    # Bölüm 4: yöntem gerekçesi
    if has_value(row, "dataset_signals_found") or has_value(row, "feature_selection_signals_found") or has_value(row, "runtime_signals_found"):
        targets.append("Bölüm 4")
        reasons.append("Supports method justification: dataset, feature extraction/selection, runtime or evaluation setup.")

    # Bölüm 5: tartışma/sınırlılıklar
    if has_value(row, "mitigation_signals_found") or has_value(row, "runtime_signals_found") or contains_any(all_text, ["limitation", "false positive", "latency", "overhead", "real-time"]):
        targets.append("Bölüm 5")
        reasons.append("Supports discussion of runtime validation, mitigation, limitations, and practical deployment gap.")

    if not targets:
        targets.append("Bölüm 3")
        reasons.append("General supporting literature source.")

    return sorted(set(targets)), sorted(set(reasons))


def build_revision_action(row, targets):
    title = str(row.get("title", ""))
    sdn = str(row.get("sdn_testbed_signals_found", ""))
    mitigation = str(row.get("mitigation_signals_found", ""))
    runtime = str(row.get("runtime_signals_found", ""))
    fs = str(row.get("feature_selection_signals_found", ""))
    models = str(row.get("model_signals_found", ""))
    dataset = str(row.get("dataset_signals_found", ""))
    metrics = str(row.get("metric_signals_found", ""))

    actions = []

    if "Bölüm 2" in targets:
        if fs:
            actions.append("Use as support for feature selection/metaheuristic optimization background.")
        if models:
            actions.append("Use as support for ML/DL model family background.")
        if metrics:
            actions.append("Use as support for IDS evaluation metrics beyond accuracy.")

    if "Bölüm 3" in targets:
        if sdn:
            actions.append("Add/strengthen in SDN-DDoS literature comparison tables.")
        else:
            actions.append("Use as supporting IDS/DDoS literature comparison source.")

    if "Bölüm 4" in targets:
        if dataset:
            actions.append("Use to justify dataset/traffic-feature selection choices.")
        if fs:
            actions.append("Use to justify feature selection stage and reduced feature-space design.")
        if runtime:
            actions.append("Use to motivate runtime/online validation need.")

    if "Bölüm 5" in targets:
        if mitigation:
            actions.append("Use to compare detection-only vs mitigation/prevention-oriented studies.")
        if runtime:
            actions.append("Use to discuss runtime validation, controller/testbed gap, latency, or deployment constraints.")

    if "Context only" in targets:
        actions.append("Mention only superficially/contextually; do not use as experimental thesis evidence.")

    if not actions:
        actions.append("Use selectively as supporting citation if the surrounding thesis paragraph requires it.")

    return " ".join(actions)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--evidence-csv",
        default="docs/literature_review/zotero_clean/fulltext_evidence_cards_A_core.csv",
    )
    parser.add_argument(
        "--output-csv",
        default="docs/literature_review/zotero_clean/fulltext_thesis_revision_targets.csv",
    )
    parser.add_argument(
        "--output-md",
        default="docs/literature_review/zotero_clean/fulltext_thesis_revision_targets.md",
    )
    args = parser.parse_args()

    evidence_path = Path(args.evidence_csv)
    if not evidence_path.exists():
        raise SystemExit(f"[ERROR] Missing evidence CSV: {evidence_path}")

    df = pd.read_csv(evidence_path).fillna("")

    rows = []
    for _, row in df.iterrows():
        targets, reasons = classify_revision_targets(row)
        action = build_revision_action(row, targets)

        rows.append({
            "zotero_key": row.get("zotero_key", ""),
            "year": row.get("year", ""),
            "title": row.get("title", ""),
            "priority_score": row.get("fulltext_priority_score", ""),
            "pdf_extract_status": row.get("pdf_extract_status", ""),
            "nsl_kdd_policy_after_fulltext": row.get("nsl_kdd_policy_after_fulltext", ""),
            "revision_targets": "; ".join(targets),
            "revision_reasons": " ".join(reasons),
            "recommended_action": action,
            "dataset_signals_found": row.get("dataset_signals_found", ""),
            "sdn_testbed_signals_found": row.get("sdn_testbed_signals_found", ""),
            "mitigation_signals_found": row.get("mitigation_signals_found", ""),
            "runtime_signals_found": row.get("runtime_signals_found", ""),
            "feature_selection_signals_found": row.get("feature_selection_signals_found", ""),
            "model_signals_found": row.get("model_signals_found", ""),
            "metric_signals_found": row.get("metric_signals_found", ""),
        })

    out = pd.DataFrame(rows)

    Path(args.output_csv).parent.mkdir(parents=True, exist_ok=True)
    out.to_csv(args.output_csv, index=False)

    target_counts = {}
    for val in out["revision_targets"]:
        for t in str(val).split("; "):
            if t:
                target_counts[t] = target_counts.get(t, 0) + 1

    md = []
    md.append("# Full Text Thesis Revision Targets")
    md.append("")
    md.append(f"- Generated at UTC: `{datetime.utcnow().isoformat()}`")
    md.append(f"- Evidence CSV: `{args.evidence_csv}`")
    md.append(f"- Output CSV: `{args.output_csv}`")
    md.append(f"- Source count: `{len(out)}`")
    md.append("")
    md.append("## 1. Target Counts")
    md.append("")
    md.append("| Target | Count |")
    md.append("|---|---:|")
    for k, v in sorted(target_counts.items()):
        md.append(f"| {k} | {v} |")

    md.append("")
    md.append("## 2. Chapter-Based Revision Guidance")
    md.append("")
    md.append("### Bölüm 2 — Kavramsal ve Kuramsal Arka Plan")
    md.append("")
    md.append("- Full text kartlarında feature selection, ML/DL model aileleri ve değerlendirme metrikleri geçen kaynaklar burada kullanılmalıdır.")
    md.append("- Özellikle accuracy yerine F1, AUC, FAR/FPR ve yanlış pozitif oranlarının IDS bağlamındaki önemi güçlendirilebilir.")
    md.append("- NSL-KDD deneysel veri seti olarak konumlandırılmamalı; yalnızca klasik/tarihsel IDS veri seti bağlamında kısa biçimde anılmalıdır.")
    md.append("")
    md.append("### Bölüm 3 — Literatür Taraması ve İlgili Çalışmalar")
    md.append("")
    md.append("- SDN, DDoS, controller, OpenFlow, Ryu, Mininet, mitigation ve runtime sinyalleri taşıyan çalışmalar karşılaştırma tablolarında güçlendirilmelidir.")
    md.append("- Literatür değerlendirmesinde çalışmalar yalnızca sınıflandırma başarımıyla değil; controller/testbed, mitigation aksiyonu, runtime validation ve kullanılan veri seti bakımından da ayrıştırılmalıdır.")
    md.append("")
    md.append("### Bölüm 4 — Yöntem ve Çalışma Zamanı Doğrulama")
    md.append("")
    md.append("- CIC-DDoS2019 ve CICFlowMeter-style flow feature tercihleri, full textlerdeki dataset/feature extraction sinyalleriyle desteklenmelidir.")
    md.append("- Feature selection ve model seçimi açıklamaları, offline IDS modelleme ile SDN runtime IDS/IPS entegrasyonu arasındaki köprü olarak verilmelidir.")
    md.append("")
    md.append("### Bölüm 5 — Tartışma, Sınırlılıklar ve Gelecek Çalışmalar")
    md.append("")
    md.append("- Runtime, latency, controller overhead, mitigation/prevention ve deployment gap içeren çalışmalar burada karşılaştırmalı tartışılmalıdır.")
    md.append("- Tezin özgün katkısı, detection-only literatürden ayrılarak IDS çıktısını OpenFlow tabanlı IPS aksiyonlarına dönüştürmesi üzerinden vurgulanmalıdır.")
    md.append("")

    md.append("## 3. Source-Level Revision Targets")
    md.append("")
    md.append("| Key | Year | Targets | Priority | Title | Recommended action |")
    md.append("|---|---:|---|---:|---|---|")
    for _, r in out.iterrows():
        key = str(r["zotero_key"])
        year = str(r["year"])
        targets = str(r["revision_targets"]).replace("|", "\\|")
        title = str(r["title"]).replace("|", "\\|")
        action = str(r["recommended_action"]).replace("|", "\\|")
        md.append(f"| {key} | {year} | {targets} | {r['priority_score']} | {title[:110]} | {action[:220]} |")

    md.append("")
    md.append("## 4. NSL-KDD Policy")
    md.append("")
    md.append("- NSL-KDD bu tezde deneysel veri seti olarak kullanılmayacaktır.")
    md.append("- Geçerlilik/güvenilirlik tartışmaları nedeniyle yalnızca tarihsel veya bağlamsal olarak kısa biçimde anılabilir.")
    md.append("- Tez sonrası makale revizyonunda NSL-KDD ile ilgili kısımlar çıkarılacak; makale CIC-DDoS2019 / CICFlowMeter-style features / SDN runtime IDS/IPS eksenine taşınacaktır.")

    Path(args.output_md).write_text("\n".join(md), encoding="utf-8")

    print("[INFO] Sources:", len(out))
    print("[INFO] Target counts:", target_counts)
    print("[INFO] CSV:", args.output_csv)
    print("[INFO] MD:", args.output_md)


if __name__ == "__main__":
    main()
