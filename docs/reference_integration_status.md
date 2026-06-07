# Reference Integration Status

Bu rapor, APA-benzeri kaynakça taslağının ana SAÜ FBE tez DOCX dosyasına entegrasyon durumunu özetler.

## Entegre Edilen Dosyalar

- Kaynakça Markdown taslağı: `docs/references_apa_like.md`
- Kaynakça CSV taslağı: `docs/references_apa_like.csv`
- Ana tez DOCX: `docs/tez_ana_taslak_tr_guncel_sau_fbe.docx`
- Entegrasyon öncesi yedek: `docs/tez_ana_taslak_tr_guncel_sau_fbe.before_references_replace.docx`
- Entegrasyon çıktısı: `docs/tez_ana_taslak_tr_guncel_sau_fbe_references_apa.docx`

## Uygulanan Politika

- Teknik `[BIBxxx]`, `[LRxxx]`, `[MANxxx]` marker’ları nihai tez metninde kullanılmamaktadır.
- Metin içi atıflar APA-benzeri `(Yazar, Yıl)` veya `(Yazar vd., Yıl)` biçimine yaklaştırılmıştır.
- Kaynakça, canonical ID override tablosu üzerinden seçilen kayıtlarla oluşturulmuştur.
- Duplicate `MAN` kayıtları ve `To verify from full text` placeholder kayıtları kaynakçaya alınmamıştır.
- `LR001` ve `LR005` gibi review kayıtlarında yazar ayrıştırma hatasını önlemek için manuel APA override uygulanmıştır.

## Nihai Kontrol Notu

Bu kaynakça otomatik olarak APA7’ye yakın biçimde üretilmiştir. Nihai teslim öncesinde Zotero/BibTeX kayıtları üzerinden yazar adları, makale başlıkları, dergi adları, cilt/sayı/sayfa bilgileri ve DOI biçimleri manuel kontrol edilmelidir.
