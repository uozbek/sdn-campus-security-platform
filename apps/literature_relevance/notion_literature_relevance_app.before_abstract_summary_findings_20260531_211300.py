import re
import json
import math
import zipfile
from pathlib import Path
from collections import Counter

import pandas as pd
import streamlit as st


# ============================================================
# Thesis-specific keyword profile
# ============================================================

PROFILE = {
    "SDN_Hits": {
        "weight": 5,
        "terms": [
            "software defined networking", "software-defined networking", "sdn",
            "openflow", "open flow", "ryu", "mininet", "open vswitch", "ovs",
            "sdn controller", "controller", "data plane", "control plane",
            "programmable network", "programmable networking"
        ],
    },
    "DDoS_Hits": {
        "weight": 5,
        "terms": [
            "ddos", "distributed denial of service", "distributed denial-of-service",
            "dos attack", "udp flood", "syn flood", "tcp syn flood",
            "http flood", "dns amplification", "amplification attack",
            "volumetric attack"
        ],
    },
    "IDS_IPS_Hits": {
        "weight": 4,
        "terms": [
            "intrusion detection", "intrusion prevention", "ids", "ips",
            "anomaly detection", "attack detection", "attack prevention",
            "network intrusion detection", "security monitoring"
        ],
    },
    "ML_DL_Hits": {
        "weight": 3,
        "terms": [
            "machine learning", "deep learning", "classification",
            "random forest", "rf", "xgboost", "lightgbm", "decision tree",
            "svm", "support vector machine", "knn", "naive bayes",
            "lstm", "gru", "cnn", "autoencoder", "ensemble learning",
            "neural network"
        ],
    },
    "Feature_Selection_Hits": {
        "weight": 3,
        "terms": [
            "feature selection", "feature extraction", "feature reduction",
            "cicflowmeter", "cicflowmeter-style", "flow feature", "flow-based",
            "top-20", "top-k", "pca", "information gain", "mutual information",
            "chi-square", "recursive feature elimination", "rfe", "shap",
            "hho", "harris hawks", "pso", "particle swarm",
            "gwo", "grey wolf", "dragonfly", "metaheuristic",
            "bio-inspired", "swarm intelligence", "binary bat"
        ],
    },
    "Dataset_Hits": {
        "weight": 3,
        "terms": [
            "cic-ddos2019", "cicddos2019", "cic ddos 2019",
            "cicids2017", "cse-cic-ids2018", "insdn",
            "unsw-nb15", "nsl-kdd", "kdd99", "dataset", "benchmark",
            "traffic dataset"
        ],
    },
    "Runtime_Testbed_Hits": {
        "weight": 4,
        "terms": [
            "real-time", "realtime", "near real-time", "runtime",
            "live traffic", "online detection", "testbed", "emulation",
            "simulation", "prototype", "flow statistics", "packet-in",
            "pcap", "traffic generation", "controller overhead",
            "latency", "round trip", "flow-stat polling"
        ],
    },
    "Mitigation_Hits": {
        "weight": 4,
        "terms": [
            "mitigation", "defense", "prevention", "countermeasure",
            "rate limit", "rate-limit", "drop", "block", "blocking",
            "quarantine", "isolation", "filtering", "openflow rule",
            "meter", "enforcement"
        ],
    },
    "Out_Of_Scope_Hits": {
        "weight": -8,
        "terms": [
            "chatbot", "chatbots", "education", "student learning",
            "medical", "healthcare", "finance", "cryptocurrency",
            "blockchain", "sentiment analysis", "recommendation system",
            "e-learning", "learning analytics"
        ],
    },
}


KEEP_FIRST_COLUMNS = [
    "Name",
    "Title",
    "Authors",
    "Item Type",
    "Tags",
    "Year",
    "DOI",
    "Publication",
    "Proceedings Title",
    "Collections",
    "Citation Key",
    "In-Text Citation",
    "Full Citation",
    "URL",
    "Zotero URI",
    "File Path",
    "Abstract",
    "Abstract Summary",
    "Translation",
    "ZoteroNotes",
    "Other Notes",
]


OUTPUT_COLUMNS = [
    "Thesis_Relevance_Label",
    "Thesis_Relevance_Score",
    "Thesis_Role",
    "Manual_Review_Status",
    "Decision_For_Thesis",
    "Suggested_Chapter",
    "Suggested_Table_Group",
    "NSL_KDD_Status",
    "Full_Text_Available",
    "PDF_Path_Normalized",
    "Matched_Keywords",
    "Matched_Keyword_Detail",
    "Relevance_Reason_TR",
    "SDN_Hits",
    "DDoS_Hits",
    "IDS_IPS_Hits",
    "ML_DL_Hits",
    "Feature_Selection_Hits",
    "Dataset_Hits",
    "Runtime_Testbed_Hits",
    "Mitigation_Hits",
    "Out_Of_Scope_Hits",
]


# ============================================================
# Utility functions
# ============================================================

def normalize_text(value: str) -> str:
    if value is None:
        return ""
    if isinstance(value, float) and math.isnan(value):
        return ""

    text = str(value).lower()
    text = text.replace("ı", "i").replace("İ", "i")
    text = re.sub(r"[^a-z0-9çğıöşü\-/\. ]+", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def safe_str(value) -> str:
    if value is None:
        return ""
    if isinstance(value, float) and math.isnan(value):
        return ""
    return str(value)


def count_term(text: str, term: str) -> int:
    text_n = normalize_text(text)
    term_n = normalize_text(term)

    if not text_n or not term_n:
        return 0

    # Acronyms should be counted as separate terms.
    if len(term_n) <= 4 and re.fullmatch(r"[a-z0-9]+", term_n):
        return len(re.findall(rf"\b{re.escape(term_n)}\b", text_n))

    return text_n.count(term_n)


def detect_full_text_available(file_path_value: str) -> tuple:
    raw = safe_str(file_path_value).strip()
    if not raw:
        return "No", ""

    # Notero exports usually contain Windows paths. We preserve them but also
    # normalize separators for easier filtering.
    normalized = raw.replace("\\", "/")

    if normalized.lower().endswith(".pdf"):
        return "Yes", normalized

    if ".pdf" in normalized.lower():
        return "Yes", normalized

    return "Unknown", normalized


def row_text(row: pd.Series) -> dict:
    return {
        "title": safe_str(row.get("Title", "")),
        "abstract": safe_str(row.get("Abstract", "")),
        "abstract_summary": safe_str(row.get("Abstract Summary", "")),
        "tags": safe_str(row.get("Tags", "")),
        "publication": safe_str(row.get("Publication", "")),
        "proceedings": safe_str(row.get("Proceedings Title", "")),
        "notes": " ".join([
            safe_str(row.get("ZoteroNotes", "")),
            safe_str(row.get("Other Notes", "")),
            safe_str(row.get("Translation", "")),
        ]),
    }


def analyze_row(row: pd.Series) -> dict:
    fields = row_text(row)

    field_weights = {
        "title": 3.0,
        "abstract": 2.0,
        "abstract_summary": 2.0,
        "tags": 2.5,
        "publication": 1.0,
        "proceedings": 1.0,
        "notes": 1.5,
    }

    total_score = 0.0
    category_hits = {}
    category_scores = {}
    matched_detail = {}
    all_terms = Counter()

    for category, cfg in PROFILE.items():
        terms = cfg["terms"]
        cat_weight = cfg["weight"]

        cat_raw_hits = 0
        cat_weighted_hits = 0.0
        term_counter = Counter()

        for term in terms:
            raw_total = 0
            weighted_total = 0.0

            for field_name, field_text in fields.items():
                c = count_term(field_text, term)
                if c:
                    raw_total += c
                    weighted_total += c * field_weights[field_name]

            if raw_total:
                term_counter[term] += raw_total
                all_terms[term] += raw_total
                cat_raw_hits += raw_total
                cat_weighted_hits += weighted_total

        cat_score = cat_weight * cat_weighted_hits
        total_score += cat_score
        category_hits[category] = cat_raw_hits
        category_scores[category] = round(cat_score, 3)
        matched_detail[category] = ", ".join([f"{k}={v}" for k, v in term_counter.most_common(10)])

    label, role, manual_status, decision, chapter, table_group, nsl_status, reason = interpret_result(
        row=row,
        score=total_score,
        hits=category_hits,
        matched_terms=all_terms,
    )

    full_text_available, pdf_path_normalized = detect_full_text_available(row.get("File Path", ""))

    result = {
        "Thesis_Relevance_Label": label,
        "Thesis_Relevance_Score": round(total_score, 3),
        "Thesis_Role": role,
        "Manual_Review_Status": manual_status,
        "Decision_For_Thesis": decision,
        "Suggested_Chapter": chapter,
        "Suggested_Table_Group": table_group,
        "NSL_KDD_Status": nsl_status,
        "Full_Text_Available": full_text_available,
        "PDF_Path_Normalized": pdf_path_normalized,
        "Matched_Keywords": "; ".join([f"{k}={v}" for k, v in all_terms.most_common(25)]),
        "Matched_Keyword_Detail": json.dumps(matched_detail, ensure_ascii=False),
        "Relevance_Reason_TR": reason,
    }

    for col in [
        "SDN_Hits",
        "DDoS_Hits",
        "IDS_IPS_Hits",
        "ML_DL_Hits",
        "Feature_Selection_Hits",
        "Dataset_Hits",
        "Runtime_Testbed_Hits",
        "Mitigation_Hits",
        "Out_Of_Scope_Hits",
    ]:
        result[col] = category_hits.get(col, 0)

    return result


def interpret_result(row, score, hits, matched_terms):
    sdn = hits.get("SDN_Hits", 0)
    ddos = hits.get("DDoS_Hits", 0)
    ids = hits.get("IDS_IPS_Hits", 0)
    ml = hits.get("ML_DL_Hits", 0)
    fs = hits.get("Feature_Selection_Hits", 0)
    dataset = hits.get("Dataset_Hits", 0)
    runtime = hits.get("Runtime_Testbed_Hits", 0)
    mitigation = hits.get("Mitigation_Hits", 0)
    out_scope = hits.get("Out_Of_Scope_Hits", 0)

    text_all = normalize_text(" ".join([
        safe_str(row.get("Title", "")),
        safe_str(row.get("Abstract", "")),
        safe_str(row.get("Tags", "")),
        safe_str(row.get("Publication", "")),
    ]))

    has_nsl = "nsl-kdd" in text_all or "nsl kdd" in text_all or "kdd99" in text_all
    has_cicddos = "cic-ddos2019" in text_all or "cicddos2019" in text_all or "cic ddos 2019" in text_all

    if has_nsl and not has_cicddos:
        nsl_status = "Historical/contextual only"
    elif has_nsl and has_cicddos:
        nsl_status = "Mixed: use CIC-DDoS2019 side; NSL-KDD contextual"
    else:
        nsl_status = "Not NSL-KDD focused"

    # Main relevance label
    if out_scope >= 2 and sdn == 0 and ddos == 0 and ids == 0:
        label = "Out of scope"
    elif sdn > 0 and ddos > 0 and (ids > 0 or ml > 0) and score >= 40:
        label = "High"
    elif sdn > 0 and (ddos > 0 or ids > 0 or mitigation > 0) and score >= 22:
        label = "Medium"
    elif ml > 0 and ids > 0 and score >= 18:
        label = "Medium"
    elif score >= 10:
        label = "Low"
    else:
        label = "Out of scope"

    # Thesis role and chapter mapping
    if label == "High" and runtime > 0 and mitigation > 0:
        role = "Core runtime/controller/mitigation study"
        chapter = "Bölüm 3, Bölüm 4, Bölüm 5"
        table_group = "Runtime/Controller/Testbed veya Mitigation/Prevention"
        decision = "Tezde çekirdek kaynak olarak kullanılabilir"
        manual = "Keep"
    elif label == "High" and fs > 0:
        role = "Core feature selection / lightweight model study"
        chapter = "Bölüm 3 ve Bölüm 4 yöntemsel arka plan"
        table_group = "Özellik Seçimi ve Hafif Model Tasarımları"
        decision = "Tezde çekirdek veya destekleyici kaynak olarak kullanılabilir"
        manual = "Keep"
    elif label == "High":
        role = "Core SDN-DDoS-ML study"
        chapter = "Bölüm 3 literatür taraması"
        table_group = "SDN/DDoS/OpenFlow veya ML/DL IDS"
        decision = "Tezde çekirdek kaynak olarak kullanılabilir"
        manual = "Keep"
    elif label == "Medium":
        role = "Supporting or comparison source"
        chapter = "Bölüm 2, Bölüm 3 veya Bölüm 5"
        table_group = "Destekleyici literatür / karşılaştırma"
        decision = "Manuel tam metin kontrolünden sonra kullanılmalı"
        manual = "Manual check"
    elif has_nsl:
        role = "Historical benchmark context"
        chapter = "Bölüm 3 veri kümesi tartışması"
        table_group = "Veri Kümesi Odaklı Çalışmalar"
        decision = "Sadece tarihsel/bağlamsal düzeyde kullanılmalı"
        manual = "Context only"
    else:
        role = "Probably not thesis-aligned"
        chapter = "Kullanılmamalı veya yalnızca çok özel bağlamda kullanılmalı"
        table_group = "Out of scope"
        decision = "Tez dışı bırakılması önerilir"
        manual = "Exclude"

    reason_parts = []

    if sdn:
        reason_parts.append(f"SDN/OpenFlow/Ryu/Mininet ilişkisi bulundu ({sdn} eşleşme).")
    if ddos:
        reason_parts.append(f"DDoS veya saldırı türü odağı bulundu ({ddos} eşleşme).")
    if ids:
        reason_parts.append(f"IDS/IPS veya saldırı tespiti/önleme ilişkisi bulundu ({ids} eşleşme).")
    if ml:
        reason_parts.append(f"Makine öğrenmesi/derin öğrenme yöntemi içeriyor ({ml} eşleşme).")
    if fs:
        reason_parts.append(f"Özellik seçimi veya özellik çıkarımı ile ilişkili ({fs} eşleşme).")
    if runtime:
        reason_parts.append(f"Çalışma zamanı/testbed/prototip bağlamı içeriyor ({runtime} eşleşme).")
    if mitigation:
        reason_parts.append(f"Mitigation/prevention/enforcement boyutu içeriyor ({mitigation} eşleşme).")
    if out_scope:
        reason_parts.append(f"Konu dışı olabilecek terimler içeriyor ({out_scope} eşleşme).")
    if has_nsl:
        reason_parts.append("NSL-KDD/KDD odaklı içerik varsa tezde yalnızca tarihsel/bağlamsal kullanılmalı.")

    if not reason_parts:
        reason_parts.append("Tez ana ekseniyle güçlü bir anahtar kelime ilişkisi bulunamadı.")

    return (
        label,
        role,
        manual,
        decision,
        chapter,
        table_group,
        nsl_status,
        " ".join(reason_parts),
    )


def load_any_input(path: Path) -> pd.DataFrame:
    suffix = path.suffix.lower()

    if suffix == ".csv":
        return pd.read_csv(path)

    if suffix in [".xlsx", ".xls"]:
        return pd.read_excel(path)

    if suffix == ".zip":
        return load_from_zip(path)

    raise ValueError("Desteklenen dosya türleri: .csv, .xlsx, .xls, .zip")


def load_from_zip(path: Path) -> pd.DataFrame:
    extract_dir = path.parent / f"{path.stem}_extracted"
    extract_dir.mkdir(parents=True, exist_ok=True)

    csv_paths = []

    def extract_zip_recursive(zip_path: Path, target_dir: Path):
        with zipfile.ZipFile(zip_path) as z:
            z.extractall(target_dir)

        for p in target_dir.rglob("*"):
            if p.suffix.lower() == ".zip":
                nested_dir = p.with_suffix("")
                nested_dir.mkdir(exist_ok=True)
                extract_zip_recursive(p, nested_dir)
            elif p.suffix.lower() == ".csv":
                csv_paths.append(p)

    extract_zip_recursive(path, extract_dir)

    if not csv_paths:
        raise ValueError("ZIP içinde CSV bulunamadı.")

    frames = []
    for csv_path in csv_paths:
        df = pd.read_csv(csv_path)
        df["Source_CSV_File"] = csv_path.name
        frames.append(df)

    return pd.concat(frames, ignore_index=True)


def analyze_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    # Ensure expected columns exist.
    for col in KEEP_FIRST_COLUMNS:
        if col not in df.columns:
            df[col] = ""

    analysis_rows = []
    for _, row in df.iterrows():
        analysis_rows.append(analyze_row(row))

    analysis_df = pd.DataFrame(analysis_rows)

    enriched = pd.concat([df.reset_index(drop=True), analysis_df.reset_index(drop=True)], axis=1)

    # Sort by relevance.
    label_order = {
        "High": 0,
        "Medium": 1,
        "Low": 2,
        "Out of scope": 3,
    }
    enriched["_sort_label"] = enriched["Thesis_Relevance_Label"].map(label_order).fillna(9)
    enriched = enriched.sort_values(
        ["_sort_label", "Thesis_Relevance_Score"],
        ascending=[True, False]
    ).drop(columns=["_sort_label"])

    # Reorder columns: Notion columns first, then analysis columns, then remaining columns.
    first_cols = [c for c in KEEP_FIRST_COLUMNS if c in enriched.columns]
    analysis_cols = [c for c in OUTPUT_COLUMNS if c in enriched.columns]
    remaining = [c for c in enriched.columns if c not in first_cols + analysis_cols]

    return enriched[first_cols + analysis_cols + remaining]


def write_markdown_report(df: pd.DataFrame, out_md: Path):
    lines = []
    lines.append("# Notion/Notero Literature Relevance Report")
    lines.append("")
    lines.append("## 1. Özet")
    lines.append("")
    lines.append(f"- Toplam kayıt: `{len(df)}`")

    for label in ["High", "Medium", "Low", "Out of scope"]:
        count = int((df["Thesis_Relevance_Label"] == label).sum())
        lines.append(f"- {label}: `{count}`")

    lines.append("")
    lines.append("## 2. Tez İçin Öncelikli Kaynaklar")
    lines.append("")
    high = df[df["Thesis_Relevance_Label"] == "High"].head(50)

    if high.empty:
        lines.append("High düzeyinde kaynak bulunamadı.")
    else:
        lines.append("| Name | Year | Title | Score | Role | Suggested chapter | Keywords |")
        lines.append("|---|---:|---|---:|---|---|---|")

        for _, r in high.iterrows():
            lines.append(
                "| {name} | {year} | {title} | {score} | {role} | {chapter} | {kw} |".format(
                    name=safe_str(r.get("Name", "")).replace("|", "/"),
                    year=safe_str(r.get("Year", "")),
                    title=safe_str(r.get("Title", "")).replace("|", "/")[:120],
                    score=safe_str(r.get("Thesis_Relevance_Score", "")),
                    role=safe_str(r.get("Thesis_Role", "")).replace("|", "/"),
                    chapter=safe_str(r.get("Suggested_Chapter", "")).replace("|", "/"),
                    kw=safe_str(r.get("Matched_Keywords", "")).replace("|", "/")[:160],
                )
            )

    lines.append("")
    lines.append("## 3. Manuel Kontrol Gerektiren Kaynaklar")
    lines.append("")
    manual = df[df["Manual_Review_Status"].isin(["Manual check", "Context only"])].head(80)

    if manual.empty:
        lines.append("Manuel kontrol gerektiren kaynak bulunamadı.")
    else:
        lines.append("| Name | Year | Title | Label | Decision | Reason |")
        lines.append("|---|---:|---|---|---|---|")

        for _, r in manual.iterrows():
            lines.append(
                "| {name} | {year} | {title} | {label} | {decision} | {reason} |".format(
                    name=safe_str(r.get("Name", "")).replace("|", "/"),
                    year=safe_str(r.get("Year", "")),
                    title=safe_str(r.get("Title", "")).replace("|", "/")[:120],
                    label=safe_str(r.get("Thesis_Relevance_Label", "")),
                    decision=safe_str(r.get("Decision_For_Thesis", "")).replace("|", "/"),
                    reason=safe_str(r.get("Relevance_Reason_TR", "")).replace("|", "/")[:200],
                )
            )

    lines.append("")
    lines.append("## 4. Konu Dışı Görünen Kaynaklar")
    lines.append("")
    out_scope = df[df["Thesis_Relevance_Label"] == "Out of scope"].head(80)

    if out_scope.empty:
        lines.append("Konu dışı kaynak bulunamadı.")
    else:
        lines.append("| Name | Year | Title | Score | Reason |")
        lines.append("|---|---:|---|---:|---|")

        for _, r in out_scope.iterrows():
            lines.append(
                "| {name} | {year} | {title} | {score} | {reason} |".format(
                    name=safe_str(r.get("Name", "")).replace("|", "/"),
                    year=safe_str(r.get("Year", "")),
                    title=safe_str(r.get("Title", "")).replace("|", "/")[:120],
                    score=safe_str(r.get("Thesis_Relevance_Score", "")),
                    reason=safe_str(r.get("Relevance_Reason_TR", "")).replace("|", "/")[:200],
                )
            )

    out_md.write_text("\n".join(lines), encoding="utf-8")


# ============================================================
# Streamlit app
# ============================================================

st.set_page_config(
    page_title="Notion Literature Relevance Analyzer",
    layout="wide"
)

st.title("Notion/Notero Literature Relevance Analyzer")
st.caption("Notion literatür tablonuza tez uygunluk, anahtar kelime sıklığı ve karar sütunları ekler.")

with st.sidebar:
    st.header("Girdi")

    default_input = "notero_lit_table.zip"
    input_path = st.text_input(
        "Notion/Notero CSV, Excel veya ZIP yolu",
        value=default_input
    )

    output_dir = st.text_input(
        "Çıktı klasörü",
        value="docs/literature_review/relevance_app_outputs"
    )

    run = st.button("Analizi çalıştır", type="primary")

st.subheader("Eklenecek analiz sütunları")
st.dataframe(pd.DataFrame({"New Columns": OUTPUT_COLUMNS}), use_container_width=True)

st.subheader("Kullanılan anahtar kelime grupları")
profile_preview = []
for k, v in PROFILE.items():
    profile_preview.append({
        "Column": k,
        "Weight": v["weight"],
        "Terms": ", ".join(v["terms"]),
    })
st.dataframe(pd.DataFrame(profile_preview), use_container_width=True)


if run:
    path = Path(input_path)

    if not path.exists():
        st.error(f"Dosya bulunamadı: {path}")
        st.info("Sunucuda çalışıyorsanız dosyanın tam yolunu girin. Örnek: /root/sdn-campus-security-platform/docs/notero_lit_table.zip")
        st.stop()

    out_dir = Path(output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    try:
        df = load_any_input(path)
        st.success(f"Girdi okundu. Kayıt sayısı: {len(df)}")

        result = analyze_dataframe(df)

        out_csv = out_dir / "notion_literature_relevance_enriched.csv"
        out_xlsx = out_dir / "notion_literature_relevance_enriched.xlsx"
        out_md = out_dir / "notion_literature_relevance_report.md"
        out_profile = out_dir / "notion_literature_relevance_profile.json"

        result.to_csv(out_csv, index=False)
        result.to_excel(out_xlsx, index=False)
        write_markdown_report(result, out_md)
        out_profile.write_text(json.dumps(PROFILE, ensure_ascii=False, indent=2), encoding="utf-8")

        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Toplam", len(result))
        c2.metric("High", int((result["Thesis_Relevance_Label"] == "High").sum()))
        c3.metric("Medium", int((result["Thesis_Relevance_Label"] == "Medium").sum()))
        c4.metric("Out of scope", int((result["Thesis_Relevance_Label"] == "Out of scope").sum()))

        st.subheader("Zenginleştirilmiş tablo")
        preview_cols = [
            "Name",
            "Year",
            "Title",
            "Thesis_Relevance_Label",
            "Thesis_Relevance_Score",
            "Thesis_Role",
            "Decision_For_Thesis",
            "Suggested_Chapter",
            "Suggested_Table_Group",
            "NSL_KDD_Status",
            "Matched_Keywords",
            "Relevance_Reason_TR",
        ]
        preview_cols = [c for c in preview_cols if c in result.columns]
        st.dataframe(result[preview_cols], use_container_width=True, height=560)

        st.subheader("Çıktılar")
        st.code(
            f"{out_csv}\n{out_xlsx}\n{out_md}\n{out_profile}",
            language="text"
        )

    except Exception as e:
        st.exception(e)
