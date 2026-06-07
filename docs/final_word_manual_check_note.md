# Final Word Manual Check Note

- Updated at UTC: `2026-05-29T11:31:51.666279`
- Main thesis DOCX: `docs/tez_ana_taslak_tr_guncel_sau_fbe.docx`

## 1. Current Automated Check Status

The latest automated checks report that the main thesis DOCX is structurally consistent.

### General Quality

- Table count: `15`
- Inline shape count: `4`
- Heading order: `OK`
- Expected thesis headings: `found`
- Missing expected files: `0`
- Missing thesis artifacts: `0`

### Caption and Reference Check

- Caption/reference summary: `OK 6 / Check 0`
- Detected table captions: `15`
- Detected figure captions: `4`
- Duplicate caption groups: `0`
- Suspicious caption count: `0`
- Kaynakça heading: `present`

### Placeholder Check

- Unexpected placeholder review count: `0`
- Expected frontmatter TODO count: `9`

Expected frontmatter TODOs remain intentionally unresolved until final personal/institutional information is entered:

- `TODO_AD_SOYAD`
- `TODO_DANISMAN`
- `TODO_JURI_1`
- `TODO_JURI_2`
- `TODO_JURI_3`
- `TODO_JURI_4`
- `TODO_JURI_5`

## 2. Items That Must Be Checked Manually in Microsoft Word

The following items cannot be fully validated with the current automated Python checks and should be checked manually in Microsoft Word before submission.

### Front Matter

- Replace all `TODO_*` fields with the final author, advisor, and jury information.
- Confirm that the cover page, approval page, declaration/ethics text, acknowledgements, Turkish abstract, English abstract, keywords, table list, and figure list comply with the SAÜ FBE thesis template.
- Update the table of contents after all edits.

### Lists

- Update the Table of Contents.
- Update the List of Tables.
- Update the List of Figures.
- Confirm page numbers after updating all fields.

### Captions

- Confirm that table and figure captions are recognized correctly by Word if Word automatic lists are used.
- Verify that table captions are placed above tables and figure captions are placed below figures if required by the institute template.
- Confirm numbering consistency:
  - Chapter 3 tables: `Tablo 3.1`–`Tablo 3.7`
  - Chapter 4 tables: `Tablo 4.4.1`–`Tablo 4.4.7`
  - Chapter 4 figures: `Şekil 4.4.1`–`Şekil 4.4.4`
  - Chapter 5 table: `Tablo 5.1`

### References

- Confirm that the `Kaynakça` section starts on the correct page.
- Confirm hanging indent, line spacing, and font size according to SAÜ FBE requirements.
- Confirm that Zotero/reviewed bibliography entries are complete and visually consistent.
- Verify that the 95 reviewed references are intentionally represented in the final bibliography workflow.
- Confirm that NSL-KDD-related works are treated only as historical/contextual references and not as thesis experimental datasets.

### Figures and Tables

- Check that all figures are visible at sufficient resolution.
- Confirm that tables fit within page margins.
- Confirm that wide tables are readable and do not overflow.
- Check that Chapter 4 artifact-based tables and figures are placed correctly.

## 3. Latest Literature/Manuscript Alignment Status

The manuscript literature/comparison tables were aligned with the reviewed Zotero bibliography and full-text workflow.

Generated files:

- `docs/literature_review/manuscript_alignment/manuscript_table_inventory.md`
- `docs/literature_review/manuscript_alignment/manuscript_zotero_alignment_report_v2.md`
- `docs/literature_review/manuscript_alignment/manuscript_alignment_decision_report.md`

Summary:

- Compared manuscript rows: `59`
- Strong surname-year Zotero matches: `53`
- Thesis-usable literature/comparison rows: `40`
- NSL-KDD / historical-context-only rows: `10`
- Manual-check rows: `2`
- Proposed Model rows: `2`

The Chapter 5 discussion was updated to reflect that many CIC-DDoS2019-based studies report high classification performance, while fewer studies integrate that performance with SDN controller-level runtime decisions, port/protocol-aware interpretation, and active mitigation/prevention actions.

## 4. Final Recommendation

Before final submission, open `docs/tez_ana_taslak_tr_guncel_sau_fbe.docx` in Microsoft Word and perform the following sequence:

1. Replace all frontmatter TODO fields.
2. Update all fields with `Ctrl+A` → `F9`.
3. Re-check the Table of Contents, List of Tables, and List of Figures.
4. Review page breaks and section breaks.
5. Export a PDF from Word.
6. Perform final visual inspection of the PDF.
