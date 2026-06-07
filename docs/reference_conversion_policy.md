# Reference Conversion Policy

Bu dosya, tez geliştirme sürecinde kullanılan teknik kaynak işaretlerinin nihai tez diline dönüştürülmesi için izlenecek politikayı açıklar.

## 1. Mevcut Durum

Tez bölümlerinde kaynaklar geliştirme ve izlenebilirlik amacıyla şu teknik işaretlerle tutulmaktadır:

- `[BIBxxx]`
- `[LRxxx]`
- `[MANxxx]`

Bu işaretler, literatür takip tablosu ve kaynakça üretim süreciyle bağlantılıdır.

## 2. Nihai Tez İçin Hedef

Nihai tez metninde bu teknik işaretlerin doğrudan kalmaması hedeflenmektedir. Bunların yerine APA7 ve SAÜ FBE kılavuzuna uygun metin içi atıf biçimleri kullanılmalıdır.

Örnek dönüşüm:

- Teknik işaret: `[BIB053]`
- Nihai metin içi atıf: `(Chouhan vd., 2023)`

## 3. Dönüşüm İlkeleri

- Otomatik dönüşüm doğrudan final metne uygulanmadan önce öneri tablosu incelenmelidir.
- Aynı cümlede birden fazla teknik işaret varsa bunlar tek parantez içinde birleştirilebilir.
- Türkçe tez metninde çok yazarlı kaynaklar için genel biçim `(Yazar vd., Yıl)` olarak kullanılabilir.
- Tek yazarlı kaynaklarda `(Yazar, Yıl)` biçimi tercih edilmelidir.
- Sistematik derleme veya survey kaynakları literatür değerlendirmesi cümlelerinde açıkça belirtilmelidir.
- Kaynakça bölümü nihai aşamada APA7 biçim kurallarına göre ayrıca gözden geçirilmelidir.

## 4. Üretilen Yardımcı Dosyalar

- `docs/inline_reference_marker_audit.md`
- `docs/inline_reference_marker_audit.csv`
- `docs/inline_reference_marker_audit.json`
- `docs/inline_citation_replacement_plan.md`
- `docs/inline_citation_replacement_plan.csv`

## 5. Nihai Uygulama Notu

Bu aşamada otomatik replace yapılmamıştır. Önce marker envanteri ve önerilen APA benzeri metin içi atıf planı üretilmiştir. Final dönüşüm, öneri tablosu kontrol edildikten sonra yapılmalıdır.
