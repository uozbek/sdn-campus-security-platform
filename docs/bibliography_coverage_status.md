# Bibliography Coverage Status

Bu rapor, tezde literatür karşılaştırması ve sentez kapsamında kullanılan çalışmaların kaynakçada yer alıp almadığını özetler.

## Son Denetim

Kullanılan rapor:

- `docs/compared_studies_bibliography_audit_refined.md`
- `docs/compared_studies_bibliography_audit_refined.csv`
- `docs/compared_studies_bibliography_audit_refined.json`

## Özet Sonuç

Refined denetime göre literatürde karşılaştırılan ve kaynakçada bulunması zorunlu görülen çalışmaların tamamı kaynakçada yer almaktadır.

| Ölçüt | Değer |
|---|---:|
| Candidate count | 197 |
| Bibliography ID count | 47 |
| Required missing count | 0 |
| Bibliography OK | 36 |
| Inline canonical OK | 11 |
| Manual / duplicate check | 20 |
| Excluded low or out of scope | 130 |

## Yorum

İlk ham denetimde çok sayıda eksik kaynak görünmüş olsa da bu durum, `Low` relevance veya konu dışı adayların da karşılaştırma havuzuna dahil edilmesinden kaynaklanmıştır. Refined denetim; SDN, DDoS, IDS/IPS, makine öğrenmesi, derin öğrenme, runtime/testbed, mitigation ve dataset bağlamında gerçekten gerekli olan çalışmaları ayırarak kontrol etmiştir.

Bu denetime göre:

- Zorunlu eksik kaynak yoktur.
- Kaynakçada 47 adet ilgili/canonical kayıt bulunmaktadır.
- `MAN` kayıtları doğrudan kaynakçaya alınmamıştır; bunlar canonical `BIB` veya `LR` kayıtlarıyla temsil edilebilecek duplicate/manual kayıtlar olarak değerlendirilmiştir.
- `Low` relevance veya konu dışı kaynaklar kaynakçaya dahil edilmemiştir.

## Nihai Tez Politikası

Kaynakçaya alınacak kayıtlar:

- Bölüm 3 literatür tablolarında kullanılan High/Medium relevance çalışmalar
- Bölüm 5 sonuç/işlevsellik karşılaştırmasında kullanılan çalışmalar
- Metin içinde APA-benzeri atıf verilen canonical kaynaklar
- Tezin yöntemsel altyapısını destekleyen seçilmiş temel ML/feature-selection kaynakları

Kaynakçaya alınmayacak kayıtlar:

- Konu dışı LMS/chatbot/eğitim/uluslararası burs/solar/stock forecasting vb. kaynaklar
- Yanlış eşleşmiş veya düşük ilgililikte domain dışı çalışmalar
- Canonical karşılığı bulunan `MAN` duplicate kayıtları
- Placeholder veya doğrulanmamış kayıtlar

## Durum

Kaynakça kapsamı mevcut tez taslağı için yeterli ve tutarlı görünmektedir. Nihai teslim öncesinde APA7 ayrıntıları ve tam yazar bilgileri ayrıca manuel kontrol edilmelidir.
