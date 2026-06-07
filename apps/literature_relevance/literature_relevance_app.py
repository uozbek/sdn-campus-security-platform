import re
import json
import math
from pathlib import Path
from collections import Counter, defaultdict

import pandas as pd
import streamlit as st

try:
    import bibtexparser
except Exception:
    bibtexparser = None

try:
    from pypdf import PdfReader
except Exception:
    PdfReader = None


# ------------------------------------------------------------
# Default thesis profile
# ------------------------------------------------------------

DEFAULT_PROFILE = {
    "core_domain": {
        "weight": 5,
        "terms": [
            "software defined networking", "software-defined networking", "sdn",
            "openflow", "ryu", "mininet", "open vswitch", "ovs",
            "controller", "data plane", "control plane"
        ],
    },
    "attack_focus": {
        "weight": 5,
        "terms": [
            "ddos", "distributed denial of service", "dos attack",
            "udp flood", "syn flood", "http flood", "amplification attack"
        ],
    },
    "security_function": {
        "weight": 4,
        "terms": [
            "intrusion detection", "intrusion prevention", "ids", "ips",
            "anomaly detection", "attack detection", "attack prevention",
            "mitigation", "defense", "rate limit", "rate-limit",
            "drop", "quarantine", "blocking"
        ],
    },
    "ml_dl": {
        "weight": 3,
        "terms": [
            "machine learning", "deep learning", "classification",
            "random forest", "xgboost", "lightgbm", "decision tree",
            "svm", "support vector machine", "lstm", "gru", "cnn",
            "autoencoder", "ensemble"
        ],
    },
    "feature_selection": {
        "weight": 3,
        "terms": [
            "feature selection", "feature extraction", "cicflowmeter",
            "flow feature", "flow-based", "top-k", "pca",
            "hho", "harris hawks", "pso", "particle swarm",
            "grey wolf", "gwo", "dragonfly", "metaheuristic",
            "bio-inspired", "swarm intelligence"
        ],
    },
    "dataset": {
        "weight": 3,
        "terms": [
            "cic-ddos2019", "cicddos2019", "cic ddos 2019",
            "cicids2017", "cse-cic-ids2018", "insdn",
            "nsl-kdd", "kdd99", "dataset", "benchmark"
        ],
    },
    "runtime_testbed": {
        "weight": 4,
        "terms": [
            "real-time", "realtime", "near real-time", "runtime",
            "testbed", "emulation", "simulation", "prototype",
            "flow statistics", "packet-in", "pcap", "traffic generation",
            "controller overhead", "latency"
        ],
    },
    "out_of_scope": {
        "weight": -6,
        "terms": [
            "chatbot", "education", "student learning", "medical",
            "healthcare", "finance", "cryptocurrency", "blockchain",
            "sentiment analysis", "recommendation system"
        ],
    },
}


# ------------------------------------------------------------
# Text utilities
# ------------------------------------------------------------

def normalize_text(text: str) -> str:
    if not isinstance(text, str):
        return ""
    text = text.lower()
    text = text.replace("ı", "i").replace("İ", "i")
    text = re.sub(r"[^a-z0-9çğıöşü\-_/\. ]+", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def count_term(text: str, term: str) -> int:
    text_n = normalize_text(text)
    term_n = normalize_text(term)
    if not term_n:
        return 0

    # For short acronyms, use word boundary.
    if len(term_n) <= 4 and re.fullmatch(r"[a-z0-9]+", term_n):
        return len(re.findall(rf"\b{re.escape(term_n)}\b", text_n))

    return text_n.count(term_n)


def safe_str(x):
    if x is None:
        return ""
    if isinstance(x, float) and math.isnan(x):
        return ""
    return str(x)


def compact_reason(items, max_items=8):
    items = [x for x in items if x]
    return "; ".join(items[:max_items])


# ------------------------------------------------------------
# File readers
# ------------------------------------------------------------

def load_bibtex(path: Path) -> pd.DataFrame:
    if bibtexparser is None:
        raise RuntimeError("bibtexparser is not installed. Run: pip install bibtexparser")

    with open(path, "r", encoding="utf-8", errors="ignore") as f:
        bib_db = bibtexparser.load(f)

    rows = []
    for e in bib_db.entries:
        rows.append({
            "source_id": e.get("ID", ""),
            "title": e.get("title", ""),
            "year": e.get("year", ""),
            "authors": e.get("author", ""),
            "abstract": e.get("abstract", ""),
            "keywords": e.get("keywords", ""),
            "journal": e.get("journal", e.get("booktitle", "")),
            "doi": e.get("doi", ""),
            "url": e.get("url", ""),
            "file": e.get("file", ""),
            "raw_type": e.get("ENTRYTYPE", ""),
        })
    return pd.DataFrame(rows)


def load_csv_or_excel(path: Path) -> pd.DataFrame:
    if path.suffix.lower() in [".xlsx", ".xls"]:
        df = pd.read_excel(path)
    else:
        df = pd.read_csv(path)

    # Normalize common columns.
    rename_map = {}
    for c in df.columns:
        cl = c.lower().strip()
        if cl in ["id", "key", "bibtex_key", "source_id"]:
            rename_map[c] = "source_id"
        elif cl in ["title", "başlık"]:
            rename_map[c] = "title"
        elif cl in ["year", "yıl"]:
            rename_map[c] = "year"
        elif cl in ["authors", "author", "yazar", "yazarlar"]:
            rename_map[c] = "authors"
        elif cl in ["abstract", "özet"]:
            rename_map[c] = "abstract"
        elif cl in ["keywords", "anahtar kelimeler"]:
            rename_map[c] = "keywords"
        elif cl in ["journal", "booktitle", "venue"]:
            rename_map[c] = "journal"
        elif cl == "doi":
            rename_map[c] = "doi"
        elif cl == "url":
            rename_map[c] = "url"

    df = df.rename(columns=rename_map)
    for col in ["source_id", "title", "year", "authors", "abstract", "keywords", "journal", "doi", "url", "file"]:
        if col not in df.columns:
            df[col] = ""

    return df


def extract_pdf_text(pdf_path: Path, max_pages=20) -> str:
    if PdfReader is None:
        return ""

    try:
        reader = PdfReader(str(pdf_path))
        parts = []
        for i, page in enumerate(reader.pages[:max_pages]):
            try:
                parts.append(page.extract_text() or "")
            except Exception:
                continue
        return "\n".join(parts)
    except Exception:
        return ""


def build_pdf_index(pdf_root: Path, max_pages=20):
    pdf_index = {}
    if not pdf_root or not pdf_root.exists():
        return pdf_index

    pdfs = list(pdf_root.rglob("*.pdf"))
    for pdf in pdfs:
        txt = extract_pdf_text(pdf, max_pages=max_pages)
        pdf_index[str(pdf)] = {
            "file_name": pdf.name,
            "path": str(pdf),
            "text": txt,
        }
    return pdf_index


def match_pdf_to_record(row, pdf_index):
    title = normalize_text(safe_str(row.get("title", "")))
    authors = normalize_text(safe_str(row.get("authors", "")))
    year = normalize_text(safe_str(row.get("year", "")))

    title_tokens = [t for t in title.split() if len(t) >= 5][:8]
    author_tokens = [t for t in authors.replace(" and ", " ").split() if len(t) >= 4][:5]

    best_path = ""
    best_score = 0

    for path, item in pdf_index.items():
        fname = normalize_text(item["file_name"])
        score = 0

        for tok in title_tokens:
            if tok in fname:
                score += 3

        for tok in author_tokens:
            if tok in fname:
                score += 2

        if year and year in fname:
            score += 2

        if score > best_score:
            best_score = score
            best_path = path

    if best_score >= 5:
        return best_path, pdf_index[best_path]["text"], best_score

    return "", "", 0


# ------------------------------------------------------------
# Scoring
# ------------------------------------------------------------

def score_record(row, profile, use_fulltext=True, pdf_text=""):
    title = safe_str(row.get("title", ""))
    abstract = safe_str(row.get("abstract", ""))
    keywords = safe_str(row.get("keywords", ""))
    journal = safe_str(row.get("journal", ""))

    weighted_text = {
        "title": title,
        "abstract": abstract,
        "keywords": keywords,
        "journal": journal,
        "fulltext": pdf_text if use_fulltext else "",
    }

    field_weights = {
        "title": 3.0,
        "abstract": 2.0,
        "keywords": 2.5,
        "journal": 1.0,
        "fulltext": 0.6,
    }

    category_hits = {}
    term_hits = Counter()
    weighted_score = 0.0
    reasons = []

    for category, cfg in profile.items():
        cat_weight = float(cfg.get("weight", 1))
        terms = cfg.get("terms", [])
        cat_raw_hits = 0
        cat_weighted_hits = 0.0
        top_terms = []

        for term in terms:
            term_total = 0.0
            term_raw = 0

            for field, txt in weighted_text.items():
                c = count_term(txt, term)
                term_raw += c
                term_total += c * field_weights.get(field, 1.0)

            if term_raw > 0:
                term_hits[term] += term_raw
                cat_raw_hits += term_raw
                cat_weighted_hits += term_total
                top_terms.append(f"{term}={term_raw}")

        cat_score = cat_weight * cat_weighted_hits
        weighted_score += cat_score

        category_hits[category] = {
            "raw_hits": cat_raw_hits,
            "weighted_hits": round(cat_weighted_hits, 3),
            "score": round(cat_score, 3),
            "top_terms": ", ".join(top_terms[:10]),
        }

        if cat_raw_hits > 0:
            reasons.append(f"{category}: {', '.join(top_terms[:5])}")

    # Rule-based interpretation.
    core = category_hits.get("core_domain", {}).get("raw_hits", 0)
    attack = category_hits.get("attack_focus", {}).get("raw_hits", 0)
    sec = category_hits.get("security_function", {}).get("raw_hits", 0)
    ml = category_hits.get("ml_dl", {}).get("raw_hits", 0)
    runtime = category_hits.get("runtime_testbed", {}).get("raw_hits", 0)
    out_scope = category_hits.get("out_of_scope", {}).get("raw_hits", 0)

    if out_scope >= 2 and core == 0 and attack == 0:
        label = "Out of scope"
    elif core > 0 and attack > 0 and (sec > 0 or ml > 0) and weighted_score >= 35:
        label = "High"
    elif (core > 0 and (attack > 0 or sec > 0)) or weighted_score >= 18:
        label = "Medium"
    elif weighted_score >= 8:
        label = "Low"
    else:
        label = "Out of scope"

    # Recommended role in thesis.
    if label == "High" and runtime > 0:
        thesis_role = "Core: Bölüm 3 / Bölüm 4 / Bölüm 5 tartışma"
    elif label == "High":
        thesis_role = "Core: Bölüm 3 literatür veya yöntemsel karşılaştırma"
    elif label == "Medium":
        thesis_role = "Supporting: kavramsal arka plan veya tartışma"
    elif "nsl-kdd" in normalize_text(title + " " + abstract + " " + keywords):
        thesis_role = "Historical context only: NSL-KDD bağlamsal kullanım"
    else:
        thesis_role = "Exclude or manual review"

    return {
        "relevance_score": round(weighted_score, 3),
        "relevance_label": label,
        "thesis_role": thesis_role,
        "reason": compact_reason(reasons),
        "top_terms": "; ".join([f"{k}={v}" for k, v in term_hits.most_common(20)]),
        **{
            f"{cat}_hits": vals["raw_hits"]
            for cat, vals in category_hits.items()
        },
        **{
            f"{cat}_score": vals["score"]
            for cat, vals in category_hits.items()
        },
    }


def analyze_dataframe(df, profile, pdf_root=None, use_fulltext=True, max_pdf_pages=20):
    pdf_index = build_pdf_index(Path(pdf_root), max_pages=max_pdf_pages) if pdf_root else {}

    rows = []
    for _, row in df.fillna("").iterrows():
        pdf_path, pdf_text, pdf_match_score = "", "", 0

        if use_fulltext and pdf_index:
            pdf_path, pdf_text, pdf_match_score = match_pdf_to_record(row, pdf_index)

        result = score_record(row, profile, use_fulltext=use_fulltext, pdf_text=pdf_text)

        combined = row.to_dict()
        combined.update(result)
        combined["matched_pdf"] = pdf_path
        combined["pdf_match_score"] = pdf_match_score
        rows.append(combined)

    out = pd.DataFrame(rows)
    out = out.sort_values(["relevance_label", "relevance_score"], ascending=[True, False])

    label_order = {"High": 0, "Medium": 1, "Low": 2, "Out of scope": 3}
    out["_label_order"] = out["relevance_label"].map(label_order).fillna(9)
    out = out.sort_values(["_label_order", "relevance_score"], ascending=[True, False]).drop(columns=["_label_order"])

    return out


def write_markdown_report(df, out_md: Path):
    counts = df["relevance_label"].value_counts().to_dict()

    lines = []
    lines.append("# Literature Relevance Analysis Report")
    lines.append("")
    lines.append("## 1. Summary")
    lines.append("")
    lines.append(f"- Total records: `{len(df)}`")
    for label in ["High", "Medium", "Low", "Out of scope"]:
        lines.append(f"- {label}: `{counts.get(label, 0)}`")

    lines.append("")
    lines.append("## 2. High Relevance Studies")
    lines.append("")
    high = df[df["relevance_label"] == "High"].head(50)
    if high.empty:
        lines.append("No high relevance records detected.")
    else:
        lines.append("| ID | Year | Title | Score | Thesis role | Top terms |")
        lines.append("|---|---:|---|---:|---|---|")
        for _, r in high.iterrows():
            title = safe_str(r.get("title", "")).replace("|", " ")
            lines.append(
                f"| {safe_str(r.get('source_id',''))} | {safe_str(r.get('year',''))} | "
                f"{title[:120]} | {r.get('relevance_score','')} | "
                f"{safe_str(r.get('thesis_role','')).replace('|','/')} | "
                f"{safe_str(r.get('top_terms','')).replace('|','/')[:150]} |"
            )

    lines.append("")
    lines.append("## 3. Manual Review Candidates")
    lines.append("")
    manual = df[df["relevance_label"].isin(["Medium", "Low"])].head(80)
    if manual.empty:
        lines.append("No manual review candidates detected.")
    else:
        lines.append("| ID | Year | Title | Label | Score | Reason |")
        lines.append("|---|---:|---|---|---:|---|")
        for _, r in manual.iterrows():
            title = safe_str(r.get("title", "")).replace("|", " ")
            reason = safe_str(r.get("reason", "")).replace("|", "/")
            lines.append(
                f"| {safe_str(r.get('source_id',''))} | {safe_str(r.get('year',''))} | "
                f"{title[:120]} | {r.get('relevance_label','')} | "
                f"{r.get('relevance_score','')} | {reason[:160]} |"
            )

    lines.append("")
    lines.append("## 4. Out-of-Scope Examples")
    lines.append("")
    out_scope = df[df["relevance_label"] == "Out of scope"].head(50)
    if out_scope.empty:
        lines.append("No out-of-scope records detected.")
    else:
        lines.append("| ID | Year | Title | Score | Top terms |")
        lines.append("|---|---:|---|---:|---|")
        for _, r in out_scope.iterrows():
            title = safe_str(r.get("title", "")).replace("|", " ")
            lines.append(
                f"| {safe_str(r.get('source_id',''))} | {safe_str(r.get('year',''))} | "
                f"{title[:120]} | {r.get('relevance_score','')} | "
                f"{safe_str(r.get('top_terms','')).replace('|','/')[:120]} |"
            )

    out_md.write_text("\n".join(lines), encoding="utf-8")


# ------------------------------------------------------------
# Streamlit UI
# ------------------------------------------------------------

st.set_page_config(
    page_title="Literature Relevance Analyzer",
    layout="wide"
)

st.title("Literature Relevance Analyzer")
st.caption("SDN-DDoS-ML tez literatürü için kaynak uygunluk, anahtar kelime sıklığı ve yöntemsel ilişki analizi")

with st.sidebar:
    st.header("Input")

    default_bib = "docs/literature_review/source_files/SDN-ML-Security_Referans.bib"
    default_csv = "docs/references_zotero_apa_like_reviewed.csv"
    default_pdf_root = "docs/literature_review/source_files/files"

    input_path = st.text_input("BibTeX / CSV / Excel dosya yolu", value=default_bib)
    pdf_root = st.text_input("PDF klasörü — isteğe bağlı", value=default_pdf_root)

    use_fulltext = st.checkbox("PDF tam metin eşleştirmeyi dene", value=False)
    max_pdf_pages = st.slider("PDF başına okunacak maksimum sayfa", 3, 50, 15)

    st.header("Output")
    output_dir = st.text_input(
        "Çıktı klasörü",
        value="docs/literature_review/relevance_app_outputs"
    )

    run_btn = st.button("Analizi çalıştır", type="primary")


st.subheader("Tez profili anahtar kelime grupları")

profile_rows = []
for cat, cfg in DEFAULT_PROFILE.items():
    profile_rows.append({
        "category": cat,
        "weight": cfg["weight"],
        "terms": ", ".join(cfg["terms"]),
    })
st.dataframe(pd.DataFrame(profile_rows), use_container_width=True)


if run_btn:
    path = Path(input_path)
    out_dir = Path(output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    if not path.exists():
        st.error(f"Dosya bulunamadı: {path}")
        st.stop()

    try:
        if path.suffix.lower() == ".bib":
            df = load_bibtex(path)
        elif path.suffix.lower() in [".csv", ".xlsx", ".xls"]:
            df = load_csv_or_excel(path)
        else:
            st.error("Desteklenen dosya türleri: .bib, .csv, .xlsx, .xls")
            st.stop()

        st.success(f"Kaynak sayısı: {len(df)}")

        with st.spinner("Analiz yapılıyor..."):
            result = analyze_dataframe(
                df,
                DEFAULT_PROFILE,
                pdf_root=pdf_root if use_fulltext else None,
                use_fulltext=use_fulltext,
                max_pdf_pages=max_pdf_pages,
            )

        out_csv = out_dir / "literature_relevance_results.csv"
        out_xlsx = out_dir / "literature_relevance_results.xlsx"
        out_md = out_dir / "literature_relevance_report.md"
        out_profile = out_dir / "literature_relevance_profile.json"

        result.to_csv(out_csv, index=False)
        result.to_excel(out_xlsx, index=False)
        write_markdown_report(result, out_md)
        out_profile.write_text(json.dumps(DEFAULT_PROFILE, ensure_ascii=False, indent=2), encoding="utf-8")

        st.success("Analiz tamamlandı.")

        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Total", len(result))
        c2.metric("High", int((result["relevance_label"] == "High").sum()))
        c3.metric("Medium", int((result["relevance_label"] == "Medium").sum()))
        c4.metric("Out of scope", int((result["relevance_label"] == "Out of scope").sum()))

        st.subheader("Sonuç tablosu")
        show_cols = [
            "source_id", "year", "title", "relevance_label", "relevance_score",
            "thesis_role", "top_terms", "reason", "matched_pdf"
        ]
        show_cols = [c for c in show_cols if c in result.columns]
        st.dataframe(result[show_cols], use_container_width=True, height=520)

        st.subheader("Çıktılar")
        st.code(
            f"{out_csv}\n{out_xlsx}\n{out_md}\n{out_profile}",
            language="text"
        )

    except Exception as e:
        st.exception(e)
