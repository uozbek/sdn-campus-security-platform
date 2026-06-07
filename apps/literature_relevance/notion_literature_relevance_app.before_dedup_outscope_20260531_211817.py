import re
import json
import math
import zipfile
from pathlib import Path
from collections import Counter

import pandas as pd
import streamlit as st

try:
    from pypdf import PdfReader
except Exception:
    PdfReader = None


# ============================================================
# Thesis-specific profile
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
    "Name", "Title", "Authors", "Item Type", "Tags", "Year", "DOI",
    "Publication", "Proceedings Title", "Collections", "Citation Key",
    "In-Text Citation", "Full Citation", "URL", "Zotero URI", "File Path",
    "Abstract", "Abstract Summary", "Translation", "ZoteroNotes", "Other Notes",
]


OUTPUT_COLUMNS = [
    "Abstract_Original",
    "Extracted_Abstract",
    "Abstract_Final",
    "Abstract_Source",
    "Auto_Summary",
    "Extracted_Findings",
    "Extracted_Results",
    "Extracted_Conclusion",
    "Extraction_Status",
    "Extraction_Confidence",
    "Thesis_Relevance_Label",
    "Thesis_Relevance_Score",
    "Thesis_Role",
    "Manual_Review_Status",
    "Decision_For_Thesis",
    "Suggested_Chapter",
    "Suggested_Table_Group",
    "NSL_KDD_Status",
    "Full_Text_Available",
    "Full_Text_Used",
    "Full_Text_Status",
    "Full_Text_Char_Count",
    "Full_Text_Page_Limit",
    "Full_Text_Top_Keywords",
    "Full_Text_Relevance_Boost",
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
# Basic utilities
# ============================================================

def safe_str(value) -> str:
    if value is None:
        return ""
    if isinstance(value, float) and math.isnan(value):
        return ""
    return str(value)


def normalize_text(value: str) -> str:
    text = safe_str(value).lower()
    text = text.replace("ı", "i").replace("İ", "i")
    text = re.sub(r"[^a-z0-9çğıöşü\-/\. ]+", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def clean_extracted_text(text: str) -> str:
    text = safe_str(text)
    text = text.replace("\x00", " ")
    text = re.sub(r"-\s*\n\s*", "", text)
    text = re.sub(r"\n+", "\n", text)
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\s+\.", ".", text)
    return text.strip()


def compact_text(text: str, max_chars: int = 2000) -> str:
    text = clean_extracted_text(text)
    if len(text) <= max_chars:
        return text
    return text[:max_chars].rsplit(" ", 1)[0].strip() + " ..."


def count_term(text: str, term: str) -> int:
    text_n = normalize_text(text)
    term_n = normalize_text(term)

    if not text_n or not term_n:
        return 0

    if len(term_n) <= 4 and re.fullmatch(r"[a-z0-9]+", term_n):
        return len(re.findall(rf"\b{re.escape(term_n)}\b", text_n))

    return text_n.count(term_n)


def sentence_split(text: str):
    text = clean_extracted_text(text)
    parts = re.split(r"(?<=[.!?])\s+", text)
    return [p.strip() for p in parts if len(p.strip()) > 20]


# ============================================================
# PDF extraction
# ============================================================

def normalize_pdf_path(raw_path: str, pdf_base_dir: str = "") -> str:
    raw = safe_str(raw_path).strip()
    if not raw:
        return ""

    raw = raw.replace("\\", "/")

    pdf_candidates = re.findall(r"[^;\n\r]*?\.pdf", raw, flags=re.IGNORECASE)
    if pdf_candidates:
        raw = pdf_candidates[0].strip()

    p = Path(raw)
    if p.exists():
        return str(p)

    if pdf_base_dir:
        base = Path(pdf_base_dir)

        candidate = base / p.name
        if candidate.exists():
            return str(candidate)

        matches = list(base.rglob(p.name))
        if matches:
            return str(matches[0])

    return raw


def detect_full_text_available(file_path_value: str, pdf_base_dir: str = "") -> tuple:
    normalized = normalize_pdf_path(file_path_value, pdf_base_dir=pdf_base_dir)

    if not normalized:
        return "No", ""

    if ".pdf" in normalized.lower():
        if Path(normalized).exists():
            return "Yes", normalized
        return "Path listed but file not found", normalized

    return "Unknown", normalized


def extract_pdf_text(pdf_path: str, max_pages: int = 20) -> tuple:
    if PdfReader is None:
        return "", "pypdf_not_installed"

    if not pdf_path:
        return "", "no_pdf_path"

    p = Path(pdf_path)
    if not p.exists():
        return "", "pdf_not_found"

    try:
        reader = PdfReader(str(p))
        parts = []
        for page in reader.pages[:max_pages]:
            try:
                parts.append(page.extract_text() or "")
            except Exception:
                continue

        text = clean_extracted_text("\n".join(parts))
        if not text:
            return "", "pdf_read_but_no_text"

        return text, "ok"

    except Exception as e:
        return "", f"pdf_read_error: {type(e).__name__}"


# ============================================================
# Section extraction from full text
# ============================================================

SECTION_PATTERNS = {
    "abstract": [
        r"\babstract\b",
        r"\bsummary\b",
        r"\böz\b",
    ],
    "introduction": [
        r"\b1\.?\s*introduction\b",
        r"\bintroduction\b",
        r"\bgiriş\b",
    ],
    "keywords": [
        r"\bkeywords?\b",
        r"\bindex terms\b",
        r"\banahtar kelimeler\b",
    ],
    "results": [
        r"\bresults?\b",
        r"\bexperimental results?\b",
        r"\bevaluation results?\b",
        r"\bfindings?\b",
        r"\bbulgular\b",
    ],
    "discussion": [
        r"\bdiscussion\b",
        r"\btartışma\b",
    ],
    "conclusion": [
        r"\bconclusions?\b",
        r"\bconclusion and future work\b",
        r"\bsonuç\b",
        r"\bsonuçlar\b",
    ],
    "references": [
        r"\breferences\b",
        r"\bbibliography\b",
        r"\bkaynakça\b",
    ],
}


def find_heading_positions(text: str, patterns):
    positions = []
    lines = text.splitlines()
    cursor = 0

    for line in lines:
        stripped = line.strip()
        line_start = cursor
        cursor += len(line) + 1

        if not stripped:
            continue

        # headings are usually short; this avoids matching ordinary sentences too often
        shortish = len(stripped) <= 120

        for pat in patterns:
            if shortish and re.search(pat, stripped, flags=re.IGNORECASE):
                positions.append((line_start, stripped))
                break

    return positions


def find_first_position(text: str, pattern_list, start: int = 0):
    best = None
    best_label = ""

    for pat in pattern_list:
        m = re.search(pat, text[start:], flags=re.IGNORECASE)
        if m:
            pos = start + m.start()
            if best is None or pos < best:
                best = pos
                best_label = pat

    return best, best_label


def extract_between_markers(text: str, start_patterns, end_patterns, max_chars=2500):
    if not text:
        return "", "not_found", 0.0

    start, start_label = find_first_position(text, start_patterns, start=0)
    if start is None:
        return "", "start_not_found", 0.0

    # start from end of heading line
    line_end = text.find("\n", start)
    if line_end == -1:
        line_end = start + len(start_label)

    body_start = line_end + 1

    end_candidates = []
    for pat in end_patterns:
        m = re.search(pat, text[body_start:], flags=re.IGNORECASE)
        if m:
            end_candidates.append(body_start + m.start())

    if end_candidates:
        body_end = min(end_candidates)
    else:
        body_end = min(len(text), body_start + max_chars)

    extracted = compact_text(text[body_start:body_end], max_chars=max_chars)

    confidence = 0.0
    if extracted:
        confidence = 0.65
        if len(extracted) >= 400:
            confidence += 0.15
        if len(extracted) <= max_chars:
            confidence += 0.10

    return extracted, "ok" if extracted else "empty", min(confidence, 0.95)


def extract_section_by_heading(text: str, section_name: str, max_chars=3000):
    if not text:
        return "", "not_found", 0.0

    start_patterns = SECTION_PATTERNS.get(section_name, [])
    if not start_patterns:
        return "", "no_patterns", 0.0

    all_end_patterns = []
    for key, pats in SECTION_PATTERNS.items():
        if key != section_name:
            all_end_patterns.extend(pats)

    return extract_between_markers(
        text=text,
        start_patterns=start_patterns,
        end_patterns=all_end_patterns,
        max_chars=max_chars,
    )


def extract_abstract_from_fulltext(full_text: str):
    # Prefer abstract -> keywords/introduction
    abstract, status, conf = extract_between_markers(
        text=full_text,
        start_patterns=SECTION_PATTERNS["abstract"],
        end_patterns=SECTION_PATTERNS["keywords"] + SECTION_PATTERNS["introduction"],
        max_chars=2200,
    )

    if abstract:
        return abstract, status, conf

    # Fallback: first long paragraph after title area
    paragraphs = [p.strip() for p in re.split(r"\n\s*\n", full_text) if len(p.strip()) > 250]
    if paragraphs:
        candidate = compact_text(paragraphs[0], max_chars=1600)
        return candidate, "fallback_first_long_paragraph", 0.35

    return "", "abstract_not_found", 0.0


def extract_summary_from_text(abstract_final: str, full_text: str, max_sentences: int = 4):
    source = abstract_final if abstract_final else full_text
    sentences = sentence_split(source)

    if not sentences:
        return ""

    # Extractive summary: first informative sentences from abstract or beginning.
    selected = sentences[:max_sentences]
    return compact_text(" ".join(selected), max_chars=1400)


def extract_findings_from_fulltext(full_text: str):
    results, r_status, r_conf = extract_section_by_heading(full_text, "results", max_chars=2600)
    conclusion, c_status, c_conf = extract_section_by_heading(full_text, "conclusion", max_chars=2600)

    finding_sentences = []

    keywords = [
        "result", "results", "finding", "findings", "achieved", "accuracy",
        "precision", "recall", "f1", "auc", "outperform", "performance",
        "experimental", "evaluation", "shows", "showed", "demonstrate",
        "mitigation", "detection rate", "false positive"
    ]

    search_space = "\n".join([results, conclusion])
    for s in sentence_split(search_space):
        s_norm = normalize_text(s)
        if any(k in s_norm for k in keywords):
            finding_sentences.append(s)

    if not finding_sentences:
        # fallback from conclusion/results
        fallback = results or conclusion
        finding_sentences = sentence_split(fallback)[:4]

    findings = compact_text(" ".join(finding_sentences[:5]), max_chars=1600)

    return {
        "Extracted_Findings": findings,
        "Extracted_Results": compact_text(results, max_chars=1800),
        "Extracted_Conclusion": compact_text(conclusion, max_chars=1800),
        "results_status": r_status,
        "conclusion_status": c_status,
        "confidence": round(max(r_conf, c_conf), 3),
    }


# ============================================================
# Scoring and interpretation
# ============================================================

def build_analysis_fields(row: pd.Series, abstract_final: str, auto_summary: str, findings: str, results: str, conclusion: str, full_text: str):
    return {
        "title": safe_str(row.get("Title", "")),
        "abstract": abstract_final,
        "abstract_summary": safe_str(row.get("Abstract Summary", "")),
        "auto_summary": auto_summary,
        "findings": findings,
        "results": results,
        "conclusion": conclusion,
        "tags": safe_str(row.get("Tags", "")),
        "publication": safe_str(row.get("Publication", "")),
        "proceedings": safe_str(row.get("Proceedings Title", "")),
        "notes": " ".join([
            safe_str(row.get("ZoteroNotes", "")),
            safe_str(row.get("Other Notes", "")),
            safe_str(row.get("Translation", "")),
        ]),
        "full_text": full_text,
    }


def score_fields(fields: dict):
    field_weights = {
        "title": 3.0,
        "abstract": 2.5,
        "abstract_summary": 2.0,
        "auto_summary": 2.0,
        "findings": 2.0,
        "results": 1.8,
        "conclusion": 1.7,
        "tags": 2.5,
        "publication": 1.0,
        "proceedings": 1.0,
        "notes": 1.5,
        "full_text": 0.35,
    }

    total_score = 0.0
    full_text_score = 0.0
    category_hits = {}
    matched_detail = {}
    all_terms = Counter()
    full_text_terms = Counter()

    for category, cfg in PROFILE.items():
        cat_weight = cfg["weight"]
        term_counter = Counter()
        cat_raw_hits = 0
        cat_weighted_hits = 0.0

        for term in cfg["terms"]:
            raw_total = 0
            weighted_total = 0.0

            for field_name, field_text in fields.items():
                c = count_term(field_text, term)
                if c:
                    raw_total += c
                    weighted_total += c * field_weights.get(field_name, 1.0)

                    if field_name == "full_text":
                        full_text_terms[term] += c
                        full_text_score += c * field_weights[field_name] * cat_weight

            if raw_total:
                term_counter[term] += raw_total
                all_terms[term] += raw_total
                cat_raw_hits += raw_total
                cat_weighted_hits += weighted_total

        cat_score = cat_weight * cat_weighted_hits
        total_score += cat_score
        category_hits[category] = cat_raw_hits
        matched_detail[category] = ", ".join([f"{k}={v}" for k, v in term_counter.most_common(12)])

    return {
        "total_score": total_score,
        "full_text_score": full_text_score,
        "category_hits": category_hits,
        "matched_detail": matched_detail,
        "all_terms": all_terms,
        "full_text_terms": full_text_terms,
    }


def interpret_result(row, score, hits):
    sdn = hits.get("SDN_Hits", 0)
    ddos = hits.get("DDoS_Hits", 0)
    ids = hits.get("IDS_IPS_Hits", 0)
    ml = hits.get("ML_DL_Hits", 0)
    fs = hits.get("Feature_Selection_Hits", 0)
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

    return label, role, manual, decision, chapter, table_group, nsl_status, " ".join(reason_parts)


# ============================================================
# Row analysis
# ============================================================

def analyze_row(row: pd.Series, use_fulltext: bool, pdf_base_dir: str, max_pdf_pages: int, abstract_update_mode: str) -> dict:
    abstract_original = safe_str(row.get("Abstract", "")).strip()

    full_text_available, pdf_path_normalized = detect_full_text_available(
        row.get("File Path", ""),
        pdf_base_dir=pdf_base_dir
    )

    full_text = ""
    full_text_status = "not_used"
    full_text_used = "No"

    if use_fulltext:
        full_text, full_text_status = extract_pdf_text(pdf_path_normalized, max_pages=max_pdf_pages)
        if full_text_status == "ok" and full_text:
            full_text_used = "Yes"

    extracted_abstract = ""
    abstract_extract_status = "not_used"
    abstract_confidence = 0.0

    extracted_findings = ""
    extracted_results = ""
    extracted_conclusion = ""
    extraction_confidence = 0.0

    if full_text_used == "Yes":
        extracted_abstract, abstract_extract_status, abstract_confidence = extract_abstract_from_fulltext(full_text)
        section_data = extract_findings_from_fulltext(full_text)
        extracted_findings = section_data["Extracted_Findings"]
        extracted_results = section_data["Extracted_Results"]
        extracted_conclusion = section_data["Extracted_Conclusion"]
        extraction_confidence = max(abstract_confidence, section_data["confidence"])

    # Abstract update logic
    if abstract_update_mode == "Boşsa full text abstract ile doldur":
        if abstract_original:
            abstract_final = abstract_original
            abstract_source = "Notion_Abstract"
        elif extracted_abstract:
            abstract_final = extracted_abstract
            abstract_source = "Full_Text_Extracted_Abstract"
        else:
            abstract_final = ""
            abstract_source = "Missing"
    elif abstract_update_mode == "Her zaman full text abstract kullan":
        if extracted_abstract:
            abstract_final = extracted_abstract
            abstract_source = "Full_Text_Extracted_Abstract"
        elif abstract_original:
            abstract_final = abstract_original
            abstract_source = "Notion_Abstract_Fallback"
        else:
            abstract_final = ""
            abstract_source = "Missing"
    else:
        abstract_final = abstract_original
        abstract_source = "Notion_Abstract"

    auto_summary = extract_summary_from_text(abstract_final, full_text, max_sentences=4)

    fields = build_analysis_fields(
        row=row,
        abstract_final=abstract_final,
        auto_summary=auto_summary,
        findings=extracted_findings,
        results=extracted_results,
        conclusion=extracted_conclusion,
        full_text=full_text,
    )

    score_data = score_fields(fields)

    label, role, manual_status, decision, chapter, table_group, nsl_status, reason = interpret_result(
        row=row,
        score=score_data["total_score"],
        hits=score_data["category_hits"],
    )

    if full_text_used == "Yes":
        reason += f" PDF tam metin incelemesi kullanıldı; {len(full_text)} karakter metin çıkarıldı."
    if extracted_abstract:
        reason += " Abstract bölümü full text içinden çıkarıldı."
    if extracted_findings or extracted_results or extracted_conclusion:
        reason += " Bulgular/sonuç bölümleri için metin çıkarımı yapıldı."

    extraction_status = "; ".join([
        f"pdf={full_text_status}",
        f"abstract={abstract_extract_status}",
        f"fulltext_used={full_text_used}",
    ])

    result = {
        "Abstract_Original": abstract_original,
        "Extracted_Abstract": extracted_abstract,
        "Abstract_Final": abstract_final,
        "Abstract_Source": abstract_source,
        "Auto_Summary": auto_summary,
        "Extracted_Findings": extracted_findings,
        "Extracted_Results": extracted_results,
        "Extracted_Conclusion": extracted_conclusion,
        "Extraction_Status": extraction_status,
        "Extraction_Confidence": round(extraction_confidence, 3),
        "Thesis_Relevance_Label": label,
        "Thesis_Relevance_Score": round(score_data["total_score"], 3),
        "Thesis_Role": role,
        "Manual_Review_Status": manual_status,
        "Decision_For_Thesis": decision,
        "Suggested_Chapter": chapter,
        "Suggested_Table_Group": table_group,
        "NSL_KDD_Status": nsl_status,
        "Full_Text_Available": full_text_available,
        "Full_Text_Used": full_text_used,
        "Full_Text_Status": full_text_status,
        "Full_Text_Char_Count": len(full_text),
        "Full_Text_Page_Limit": max_pdf_pages if use_fulltext else 0,
        "Full_Text_Top_Keywords": "; ".join([f"{k}={v}" for k, v in score_data["full_text_terms"].most_common(20)]),
        "Full_Text_Relevance_Boost": round(score_data["full_text_score"], 3),
        "PDF_Path_Normalized": pdf_path_normalized,
        "Matched_Keywords": "; ".join([f"{k}={v}" for k, v in score_data["all_terms"].most_common(25)]),
        "Matched_Keyword_Detail": json.dumps(score_data["matched_detail"], ensure_ascii=False),
        "Relevance_Reason_TR": reason,
    }

    for col in [
        "SDN_Hits", "DDoS_Hits", "IDS_IPS_Hits", "ML_DL_Hits",
        "Feature_Selection_Hits", "Dataset_Hits", "Runtime_Testbed_Hits",
        "Mitigation_Hits", "Out_Of_Scope_Hits",
    ]:
        result[col] = score_data["category_hits"].get(col, 0)

    return result


# ============================================================
# Input loading
# ============================================================

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


def analyze_dataframe(df: pd.DataFrame, use_fulltext: bool, pdf_base_dir: str, max_pdf_pages: int, abstract_update_mode: str) -> pd.DataFrame:
    for col in KEEP_FIRST_COLUMNS:
        if col not in df.columns:
            df[col] = ""

    analysis_rows = []
    progress = st.progress(0)
    total = len(df)

    for i, (_, row) in enumerate(df.iterrows(), start=1):
        analysis_rows.append(
            analyze_row(
                row=row,
                use_fulltext=use_fulltext,
                pdf_base_dir=pdf_base_dir,
                max_pdf_pages=max_pdf_pages,
                abstract_update_mode=abstract_update_mode,
            )
        )
        progress.progress(min(i / max(total, 1), 1.0))

    analysis_df = pd.DataFrame(analysis_rows)
    enriched = pd.concat([df.reset_index(drop=True), analysis_df.reset_index(drop=True)], axis=1)

    # If requested, update actual Notion Abstract column in output.
    if abstract_update_mode in [
        "Boşsa full text abstract ile doldur",
        "Her zaman full text abstract kullan",
    ]:
        enriched["Abstract"] = enriched["Abstract_Final"]

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

    fulltext_used = int((df["Full_Text_Used"] == "Yes").sum()) if "Full_Text_Used" in df.columns else 0
    abstract_extracted = int((df["Extracted_Abstract"].astype(str).str.len() > 0).sum()) if "Extracted_Abstract" in df.columns else 0
    findings_extracted = int((df["Extracted_Findings"].astype(str).str.len() > 0).sum()) if "Extracted_Findings" in df.columns else 0

    lines.append(f"- Full text kullanılan kayıt: `{fulltext_used}`")
    lines.append(f"- Full text'ten abstract çıkarılan kayıt: `{abstract_extracted}`")
    lines.append(f"- Bulgular/sonuç özeti çıkarılan kayıt: `{findings_extracted}`")

    lines.append("")
    lines.append("## 2. Tez İçin Öncelikli Kaynaklar")
    lines.append("")
    high = df[df["Thesis_Relevance_Label"] == "High"].head(50)

    if high.empty:
        lines.append("High düzeyinde kaynak bulunamadı.")
    else:
        lines.append("| Name | Year | Title | Score | Full text | Abstract source | Role | Suggested chapter | Keywords |")
        lines.append("|---|---:|---|---:|---|---|---|---|---|")

        for _, r in high.iterrows():
            lines.append(
                "| {name} | {year} | {title} | {score} | {ft} | {asrc} | {role} | {chapter} | {kw} |".format(
                    name=safe_str(r.get("Name", "")).replace("|", "/"),
                    year=safe_str(r.get("Year", "")),
                    title=safe_str(r.get("Title", "")).replace("|", "/")[:120],
                    score=safe_str(r.get("Thesis_Relevance_Score", "")),
                    ft=safe_str(r.get("Full_Text_Used", "")),
                    asrc=safe_str(r.get("Abstract_Source", "")),
                    role=safe_str(r.get("Thesis_Role", "")).replace("|", "/"),
                    chapter=safe_str(r.get("Suggested_Chapter", "")).replace("|", "/"),
                    kw=safe_str(r.get("Matched_Keywords", "")).replace("|", "/")[:160],
                )
            )

    lines.append("")
    lines.append("## 3. Full Text'ten Çıkarılan Abstract Örnekleri")
    lines.append("")
    extracted = df[df["Extracted_Abstract"].astype(str).str.len() > 0].head(20)

    if extracted.empty:
        lines.append("Full text'ten abstract çıkarılamadı.")
    else:
        for _, r in extracted.iterrows():
            lines.append(f"### {safe_str(r.get('Title', 'Untitled'))[:120]}")
            lines.append("")
            lines.append(f"- Abstract source: `{safe_str(r.get('Abstract_Source', ''))}`")
            lines.append(f"- Extraction confidence: `{safe_str(r.get('Extraction_Confidence', ''))}`")
            lines.append("")
            lines.append(compact_text(safe_str(r.get("Extracted_Abstract", "")), max_chars=900))
            lines.append("")

    lines.append("")
    lines.append("## 4. Bulgular/Sonuç Çıkarımı Örnekleri")
    lines.append("")
    findings = df[df["Extracted_Findings"].astype(str).str.len() > 0].head(20)

    if findings.empty:
        lines.append("Bulgular/sonuç metni çıkarılamadı.")
    else:
        for _, r in findings.iterrows():
            lines.append(f"### {safe_str(r.get('Title', 'Untitled'))[:120]}")
            lines.append("")
            lines.append(compact_text(safe_str(r.get("Extracted_Findings", "")), max_chars=900))
            lines.append("")

    out_md.write_text("\n".join(lines), encoding="utf-8")


# ============================================================
# Streamlit UI
# ============================================================

st.set_page_config(
    page_title="Notion Literature Relevance Analyzer",
    layout="wide"
)

st.title("Notion/Notero Literature Relevance Analyzer")
st.caption(
    "Notion literatür tablonuza tez uygunluk, anahtar kelime sıklığı, "
    "PDF full text abstract çıkarımı, otomatik özet ve bulgu/sonuç sütunları ekler."
)

with st.sidebar:
    st.header("Girdi")

    input_path = st.text_input(
        "Notion/Notero CSV, Excel veya ZIP yolu",
        value="/root/sdn-campus-security-platform/notero_lit_table.zip"
    )

    output_dir = st.text_input(
        "Çıktı klasörü",
        value="docs/literature_review/relevance_app_outputs"
    )

    st.header("Full text / PDF inceleme")

    use_fulltext = st.checkbox(
        "PDF full text incelemeyi kullan",
        value=True
    )

    pdf_base_dir = st.text_input(
        "PDF ana klasörü",
        value="/root/sdn-campus-security-platform/docs/literature_review/source_files/files"
    )

    max_pdf_pages = st.slider(
        "PDF başına okunacak maksimum sayfa",
        min_value=3,
        max_value=80,
        value=20,
        step=1
    )

    abstract_update_mode = st.selectbox(
        "Abstract sütununu nasıl güncelleyelim?",
        [
            "Boşsa full text abstract ile doldur",
            "Her zaman full text abstract kullan",
            "Abstract sütununu değiştirme"
        ],
        index=0
    )

    run = st.button("Analizi çalıştır", type="primary")


st.subheader("Yeni eklenecek analiz sütunları")
st.dataframe(pd.DataFrame({"New Columns": OUTPUT_COLUMNS}), use_container_width=True)

st.subheader("Anahtar kelime grupları")
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
        st.stop()

    out_dir = Path(output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    if use_fulltext and PdfReader is None:
        st.error("pypdf kurulu değil. Çalıştırın: pip install pypdf")
        st.stop()

    try:
        df = load_any_input(path)
        st.success(f"Girdi okundu. Kayıt sayısı: {len(df)}")

        result = analyze_dataframe(
            df=df,
            use_fulltext=use_fulltext,
            pdf_base_dir=pdf_base_dir,
            max_pdf_pages=max_pdf_pages,
            abstract_update_mode=abstract_update_mode,
        )

        out_csv = out_dir / "notion_literature_relevance_enriched.csv"
        out_xlsx = out_dir / "notion_literature_relevance_enriched.xlsx"
        out_md = out_dir / "notion_literature_relevance_report.md"
        out_profile = out_dir / "notion_literature_relevance_profile.json"

        result.to_csv(out_csv, index=False)
        result.to_excel(out_xlsx, index=False)
        write_markdown_report(result, out_md)
        out_profile.write_text(json.dumps(PROFILE, ensure_ascii=False, indent=2), encoding="utf-8")

        c1, c2, c3, c4, c5, c6 = st.columns(6)
        c1.metric("Toplam", len(result))
        c2.metric("High", int((result["Thesis_Relevance_Label"] == "High").sum()))
        c3.metric("Medium", int((result["Thesis_Relevance_Label"] == "Medium").sum()))
        c4.metric("Out of scope", int((result["Thesis_Relevance_Label"] == "Out of scope").sum()))
        c5.metric("Full text kullanılan", int((result["Full_Text_Used"] == "Yes").sum()))
        c6.metric("Abstract çıkarılan", int((result["Extracted_Abstract"].astype(str).str.len() > 0).sum()))

        st.subheader("Zenginleştirilmiş tablo")
        preview_cols = [
            "Name",
            "Year",
            "Title",
            "Thesis_Relevance_Label",
            "Thesis_Relevance_Score",
            "Full_Text_Used",
            "Full_Text_Status",
            "Abstract_Source",
            "Extracted_Abstract",
            "Abstract_Final",
            "Auto_Summary",
            "Extracted_Findings",
            "Extracted_Conclusion",
            "Thesis_Role",
            "Decision_For_Thesis",
            "Suggested_Chapter",
            "Matched_Keywords",
            "Relevance_Reason_TR",
        ]
        preview_cols = [c for c in preview_cols if c in result.columns]
        st.dataframe(result[preview_cols], use_container_width=True, height=600)

        st.subheader("Çıktılar")
        st.code(
            f"{out_csv}\n{out_xlsx}\n{out_md}\n{out_profile}",
            language="text"
        )

    except Exception as e:
        st.exception(e)
