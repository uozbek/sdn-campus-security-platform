# Reference Cleanup Review Lists

Bu dosya, kaynakça ve literatür takip tablosu temizliği için üretilen inceleme listelerini özetler.

| Liste | Dosya | Kayıt sayısı | Amaç |
|---|---|---:|---|
| Out of scope candidates | `docs/out_of_scope_reference_candidates.csv` | 79 | Konu dışı kaynakları kaynakça/sentez dışı bırakmak |
| Method background low relevance candidates | `docs/method_background_low_relevance_candidates.csv` | 41 | Low relevance ama yöntemsel olarak tutulabilecek kaynakları seçmek |
| Manual reference review candidates | `docs/manual_reference_review_candidates.csv` | 20 | MAN kayıtlarını duplicate/promote/discard olarak sınıflamak |

## Karar Alanları

- `decision`: kullanıcı tarafından doldurulacak karar.
- `final_action`: karar uygulandıktan sonra sistem tarafından/manuel doldurulabilir.
- `notes`: gerekçe veya canonical karşılık notu.

## Önerilen Kararlar

### Out of scope

- `exclude_from_thesis`: tez kaynakçası ve sentezinden çıkar.
- `keep_method_background`: yöntemsel arka plan için tut.
- `keep_domain_relevant`: konuya aslında ilgiliyse tut.

### MAN kayıtları

- `canonical_duplicate`: BIB/LR karşılığı var, MAN kaynakçaya girmez.
- `promote_to_canonical`: değerli ve canonical karşılığı yok, yeni BIB/LR kaydı açılmalı.
- `discard_manual`: eksik/kırpılmış/doğrulanmamış, kullanılmayacak.