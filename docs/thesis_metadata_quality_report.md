# Thesis Metadata Quality Report

- Generated at UTC: `2026-05-20T18:13:57.717327`
- Metadata: `docs/thesis_metadata.yaml`

## 1. Summary

- OK: `12`
- Check: `4`
- Total: `16`
- TODO count: `8`

## 2. Field Checks

| Field | Status | Value | Note |
|---|---|---|---|
| university | ok | SAKARYA ÜNİVERSİTESİ | required scalar field |
| institute | ok | FEN BİLİMLERİ ENSTİTÜSÜ | required scalar field |
| department | ok | BİLGİSAYAR VE BİLİŞİM MÜHENDİSLİĞİ ANABİLİM DALI | required scalar field |
| program | ok | BİLGİSAYAR MÜHENDİSLİĞİ | required scalar field |
| degree_type_tr | ok | DOKTORA TEZİ | required scalar field |
| degree_type_en | ok | Ph.D. Thesis | required scalar field |
| title_tr | ok | Yazılım Tanımlı Kampüs Ağlarında Makine Öğrenmesi Destekli DDoS Saldırı Tespiti ve Önleme Sistemi | required scalar field |
| title_en | ok | Machine Learning-Assisted DDoS Attack Detection and Prevention System in Software-Defined Campus Networks | required scalar field |
| author | check | TODO_AD_SOYAD | required scalar field |
| student_id | check | TODO_OGR_NO | required scalar field |
| advisor | check | TODO_DANISMAN | required scalar field |
| city | ok | SAKARYA | required scalar field |
| year | ok | 2026 | required scalar field |
| jury | check | ["TODO_JURI_1", "TODO_JURI_2", "TODO_JURI_3", "TODO_JURI_4", "TODO_JURI_5"] | contains TODO/missing items: TODO_JURI_1, TODO_JURI_2, TODO_JURI_3, TODO_JURI_4, TODO_JURI_5 |
| keywords_tr | ok | ["Yazılım Tanımlı Ağlar", "DDoS", "Makine Öğrenmesi", "Saldırı Tespit Sistemi", "Saldırı Önleme Sistemi"] | required list field |
| keywords_en | ok | ["Software-Defined Networking", "DDoS", "Machine Learning", "Intrusion Detection System", "Intrusion Prevention System"] | required list field |

## 3. TODO Hits

| Field | Value |
|---|---|
| author | TODO_AD_SOYAD |
| student_id | TODO_OGR_NO |
| advisor | TODO_DANISMAN |
| jury[0] | TODO_JURI_1 |
| jury[1] | TODO_JURI_2 |
| jury[2] | TODO_JURI_3 |
| jury[3] | TODO_JURI_4 |
| jury[4] | TODO_JURI_5 |

## 4. Suggested Next Action

Metadata içindeki `TODO_*` alanları doldurulduktan sonra `sau_fbe_frontmatter_generated.docx` ve `tez_ana_taslak_tr_sau_fbe.docx` yeniden üretilmelidir.