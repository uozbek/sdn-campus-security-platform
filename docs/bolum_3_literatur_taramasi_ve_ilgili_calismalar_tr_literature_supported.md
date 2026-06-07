# Bölüm 3. Literatür Taraması ve İlgili Çalışmalar

_Bu taslak literatür sentez tablosundan otomatik olarak desteklenmiştir. Üretim zamanı: `2026-05-20T08:56:37.371051`_

## 3.1. Bölüme Genel Bakış

Bu bölümde, yazılım tanımlı ağlarda DDoS saldırılarının makine öğrenmesi ve derin öğrenme yöntemleriyle tespit edilmesi, SDN denetleyicisiyle bütünleşik önleme mekanizmaları ve çalışma zamanı doğrulama yaklaşımları incelenmektedir. Literatür taraması, bu tez çalışmasının yalnızca çevrimdışı bir sınıflandırma yaklaşımı değil, aynı zamanda SDN denetleyicisiyle bütünleşik aktif IDS/IPS prototipi olarak konumlandırılmasını destekleyecek şekilde yapılandırılmıştır.

Hazırlanan literatür havuzunda 67 aday kaynak yer almakta; bu kaynakların tamamı SDN, DDoS veya OpenFlow bağlamıyla ilişkili görünmektedir. Bunun yanında 42 çalışma ML/DL tabanlı yaklaşımlarla, 21 çalışma veri kümesi kullanımıyla, 9 çalışma runtime/controller/testbed bağlamıyla ve 8 çalışma mitigation/prevention bağlamıyla ilişkilendirilmiştir. Bu dağılım, literatürde tespit odaklı çalışmaların daha yoğun olduğunu; buna karşılık denetleyiciyle bütünleşik runtime enforcement çalışmalarının daha sınırlı kaldığını göstermektedir.

## 3.2. Literatür Tarama ve Sınıflandırma Yaklaşımı

Literatür taramasında SDN tabanlı DDoS tespiti, makine öğrenmesi, derin öğrenme, özellik seçimi, Mininet/Ryu/OpenFlow tabanlı deneysel kurulumlar ve aktif mitigation mekanizmaları ana sınıflandırma eksenleri olarak belirlenmiştir. Kaynaklar; kullanılan veri kümesi, model türü, test ortamı, runtime/offline ayrımı ve önleme aksiyonu içerip içermemesi bakımından karşılaştırılmıştır.

## 3.3. SDN Tabanlı DDoS Tespit Çalışmaları

SDN mimarisi, kontrol düzlemi ile veri düzlemini ayırdığı için ağ trafiğinin merkezi biçimde gözlemlenmesine ve programlanabilir güvenlik politikalarının uygulanmasına olanak sağlar. Bu nedenle DDoS saldırılarının tespiti için flow statistics, OpenFlow mesajları, port istatistikleri ve denetleyici gözlemleri literatürde sık kullanılan veri kaynaklarıdır. Literatür havuzundaki SDN/DDoS/OpenFlow odaklı çalışmalar, bu genel yaklaşımın farklı veri kümeleri, modeller ve testbed yapılarıyla uygulandığını göstermektedir.

Bu alt başlık için öne çıkan kaynaklar:

- `LR005` (2026.0) — A Systematic Review of Machine-Learning-Based Detection of DDoS Attacks in Software-Def...
- `LR001` (2025.0) — A Comprehensive Review of DDoS Detection and Mitigation Models in Software-Defined Netw...
- `LR002` (2025.0) — Assessing SDN Controller Vulnerabilities: A Survey on Attack Detection and Datasets
- `BIB029` (2024.0) — A Survey on the Latest Intrusion Detection Datasets for Software Defined Networking Env...
- `LR003` (2024.0) — Machine learning-based DDoS attack detection and prevention in SDN-enabled IoT systems
- `BIB039` (2024.0) — SDN-based detection and mitigation of DDoS attacks on smart homes
- `MAN008` (2023.0) — A framework to detect DDoS attack in Ryu controlle
- `MAN011` (2023.0) — SDN Controllers and ML-Based Anomaly Detection in
- `BIB021` (2022.0) — A new DDoS attacks intrusion detection model based on deep learning for cybersecurity
- `BIB105` (2022.0) — An optimized weighted voting based ensemble model for DDoS attack detection and mitigat...
- `BIB049` (2022.0) — Network intrusion detection in software defined networking with self-organized constrai...
- `BIB014` (2021.0) — A GRU deep learning system against attacks in software defined networks
- `MAN020` (2021.0) — A generalized machine learning model for DDoS atta
- `MAN006` (2021.0) — DIDDOS An approach for detection and identificati
- `BIB061` (2021.0) — DLSDN: Deep Learning for DDOS attack detection in Software Defined Networking

### Tablo 3.1. SDN/DDoS/OpenFlow Odaklı Seçilmiş Çalışmalar

| id     |   year | title                                                                                                   | dataset                                                 | ml_dl_model                                   | real_time_or_offline                                                | mitigation_action                                       | relevance_to_this_thesis   |
|:-------|-------:|:--------------------------------------------------------------------------------------------------------|:--------------------------------------------------------|:----------------------------------------------|:--------------------------------------------------------------------|:--------------------------------------------------------|:---------------------------|
| LR005  |   2026 | A Systematic Review of Machine-Learning-Based Detection of DDoS Attacks in Software-Defined Networks    | Multiple datasets across reviewed studies               | ML-based DDoS detection approaches            | Mostly review-level classification                                  | Detection-centered; mitigation varies by reviewed study | High                       |
| LR001  |   2025 | A Comprehensive Review of DDoS Detection and Mitigation Models in Software-Defined Networks             | Legacy compatible and SDN-contextual datasets discussed | ML / DL / Federated Learning models           | Mostly literature-level comparison; includes performance discussion | Detection and mitigation models reviewed                | High                       |
| LR002  |   2025 | Assessing SDN Controller Vulnerabilities: A Survey on Attack Detection and Datasets                     | Datasets used in ML-based detection methods discussed   | Statistical and ML approaches                 | Survey-level discussion                                             | Detection focus; controller protection context          | High                       |
| BIB029 |   2024 | A Survey on the Latest Intrusion Detection Datasets for Software Defined Networking Environments        | InSDN                                                   | Deep Learning / Machine Learning              | To verify                                                           | To verify                                               | High                       |
| LR003  |   2024 | Machine learning-based DDoS attack detection and prevention in SDN-enabled IoT systems                  | To be extracted from full text                          | Machine learning algorithms                   | Detection/prevention setting; runtime details to verify             | Prevention method proposed                              | High                       |
| BIB039 |   2024 | SDN-based detection and mitigation of DDoS attacks on smart homes                                       |                                                         | SVM / Decision Tree / Machine Learning        | To verify                                                           | To verify                                               | High                       |
| MAN008 |   2023 | A framework to detect DDoS attack in Ryu controlle                                                      |                                                         |                                               | To verify from full text                                            | To verify from full text                                | High                       |
| MAN011 |   2023 | SDN Controllers and ML-Based Anomaly Detection in                                                       |                                                         |                                               | To verify from full text                                            | To verify from full text                                | High                       |
| BIB021 |   2022 | A new DDoS attacks intrusion detection model based on deep learning for cybersecurity                   | CIC-DDoS2019                                            | LSTM / CNN / Deep Learning / Machine Learning | To verify                                                           | To verify                                               | High                       |
| BIB105 |   2022 | An optimized weighted voting based ensemble model for DDoS attack detection and mitigation in SDN en... | CIC-DDoS2019                                            | Random Forest / SVM / Ensemble                | To verify                                                           | To verify                                               | High                       |

## 3.4. Makine Öğrenmesi ve Derin Öğrenme Tabanlı IDS Yaklaşımları

Makine öğrenmesi ve derin öğrenme tabanlı çalışmalar, ağ trafiğinden çıkarılan özellikler üzerinden benign ve saldırı akışlarını ayırt etmeyi hedefler. Literatürde Random Forest, SVM, Decision Tree, XGBoost, ensemble learning, LSTM, CNN ve autoencoder gibi modellerin farklı veri kümeleri üzerinde değerlendirildiği görülmektedir. Bu çalışmaların önemli bir bölümü yüksek sınıflandırma başarısı raporlamakla birlikte, modelin SDN denetleyicisiyle çalışma zamanı bütünleşmesi her zaman ayrıntılı olarak ele alınmamaktadır.

Bu alt başlık için öne çıkan kaynaklar:

- `BIB029` (2024.0) — A Survey on the Latest Intrusion Detection Datasets for Software Defined Networking Env...
- `LR003` (2024.0) — Machine learning-based DDoS attack detection and prevention in SDN-enabled IoT systems
- `BIB039` (2024.0) — SDN-based detection and mitigation of DDoS attacks on smart homes
- `BIB021` (2022.0) — A new DDoS attacks intrusion detection model based on deep learning for cybersecurity
- `BIB105` (2022.0) — An optimized weighted voting based ensemble model for DDoS attack detection and mitigat...
- `BIB049` (2022.0) — Network intrusion detection in software defined networking with self-organized constrai...
- `BIB014` (2021.0) — A GRU deep learning system against attacks in software defined networks
- `MAN020` (2021.0) — A generalized machine learning model for DDoS atta
- `BIB061` (2021.0) — DLSDN: Deep Learning for DDOS attack detection in Software Defined Networking
- `BIB043` (2021.0) — Designing a Network Intrusion Detection System Based on Machine Learning for Software D...
- `BIB047` (2021.0) — Efficient Intrusion Detection System for SDN Orchestrated Internet of Things
- `BIB023` (2020.0) — A Flexible SDN-Based Architecture for Identifying and Mitigating Low-Rate DDoS Attacks ...
- `BIB054` (2020.0) — Hybrid Deep Learning: An Efficient Reconnaissance and Surveillance Detection Mechanism ...
- `BIB060` (2019.0) — Survey on SDN based network intrusion detection system using machine learning approaches
- `BIB032` (2018.0) — OpCloudSec: Open cloud software defined wireless network security for the Internet of T...

### Tablo 3.2. ML/DL Tabanlı Seçilmiş IDS Çalışmaları

| id     |   year | title                                                                                                   | dataset                        | ml_dl_model                                                | real_time_or_offline                                    | mitigation_action          | relevance_to_this_thesis   |
|:-------|-------:|:--------------------------------------------------------------------------------------------------------|:-------------------------------|:-----------------------------------------------------------|:--------------------------------------------------------|:---------------------------|:---------------------------|
| BIB029 |   2024 | A Survey on the Latest Intrusion Detection Datasets for Software Defined Networking Environments        | InSDN                          | Deep Learning / Machine Learning                           | To verify                                               | To verify                  | High                       |
| LR003  |   2024 | Machine learning-based DDoS attack detection and prevention in SDN-enabled IoT systems                  | To be extracted from full text | Machine learning algorithms                                | Detection/prevention setting; runtime details to verify | Prevention method proposed | High                       |
| BIB039 |   2024 | SDN-based detection and mitigation of DDoS attacks on smart homes                                       |                                | SVM / Decision Tree / Machine Learning                     | To verify                                               | To verify                  | High                       |
| BIB021 |   2022 | A new DDoS attacks intrusion detection model based on deep learning for cybersecurity                   | CIC-DDoS2019                   | LSTM / CNN / Deep Learning / Machine Learning              | To verify                                               | To verify                  | High                       |
| BIB105 |   2022 | An optimized weighted voting based ensemble model for DDoS attack detection and mitigation in SDN en... | CIC-DDoS2019                   | Random Forest / SVM / Ensemble                             | To verify                                               | To verify                  | High                       |
| BIB049 |   2022 | Network intrusion detection in software defined networking with self-organized constraint-based inte... |                                | Machine Learning                                           | To verify                                               | To verify                  | High                       |
| BIB014 |   2021 | A GRU deep learning system against attacks in software defined networks                                 |                                | GRU / Deep Learning / Machine Learning                     | To verify                                               | To verify                  | High                       |
| MAN020 |   2021 | A generalized machine learning model for DDoS atta                                                      |                                | Machine Learning                                           | To verify from full text                                | To verify from full text   | High                       |
| BIB061 |   2021 | DLSDN: Deep Learning for DDOS attack detection in Software Defined Networking                           |                                | MLP / Deep Learning                                        | To verify                                               | To verify                  | High                       |
| BIB043 |   2021 | Designing a Network Intrusion Detection System Based on Machine Learning for Software Defined Networ... | NSL-KDD                        | XGBoost / Random Forest / Decision Tree / Machine Learning | To verify                                               | To verify                  | High                       |

## 3.5. Özellik Seçimi ve Hafif Model Tasarımları

SDN tabanlı runtime IDS/IPS sistemlerinde yalnızca model doğruluğu değil, özellik çıkarım maliyeti ve inference süresi de kritiktir. Bu nedenle özellik seçimi, modelin çalışma zamanı uygulanabilirliği açısından önemli bir konudur. Metaheuristic feature selection, top-k feature selection, PCA ve benzeri yaklaşımlar, modelin daha az sayıda özellik ile çalışmasını sağlayarak denetleyici ve model servisi üzerindeki yükü azaltabilir.

Bu tez çalışmasında kullanılan Final XGBoost Top-20 yaklaşımı da bu bağlama yerleşmektedir. Amaç, CIC-DDoS2019 uyumlu özellikler arasından daha az sayıda fakat ayırt edici özelliği kullanarak runtime pipeline içinde uygulanabilir bir model elde etmektir.

Bu alt başlık için öne çıkan kaynaklar:

- `BIB013` (2024.0) — Building a Cloud-IDS by Hybrid Bio-Inspired Feature Selection Algorithms Along With Ran...
- `BIB087` (2021.0) — Efficient Detection of DDoS Attacks Using a Hybrid Deep Learning Model with Improved Fe...
- `BIB088` (2020.0) — Building an efficient intrusion detection system based on feature selection and ensembl...
- `BIB007` (2020.0) — Detecting DDoS Attacks in Software-Defined Networks Through Feature Selection Methods a...
- `BIB048` (2018.0) — Improving performance of intrusion detection system using ensemble methods and feature ...
- `MAN018` (2017.0) — Feature selection techniques for intrusion detecti
- `BIB018` (2017.0) — Feature selection techniques for intrusion detection using non-bio-inspired and bio-ins...
- `MAN002` () — Kaynak et al. - The search process of a PSO algorithm should be a
- `BIB167` (2023.0) — A review of opportunities and challenges of chatbots in education
- `BIB092` (2022.0) — An efficient IDS in cloud environment using feature selection based on DM algorithm

### Tablo 3.3. Özellik Seçimi Odaklı Seçilmiş Çalışmalar

| id     | year   | title                                                                                                   | dataset                  | ml_dl_model                                   | real_time_or_offline     | mitigation_action        | relevance_to_this_thesis   |
|:-------|:-------|:--------------------------------------------------------------------------------------------------------|:-------------------------|:----------------------------------------------|:-------------------------|:-------------------------|:---------------------------|
| BIB013 | 2024.0 | Building a Cloud-IDS by Hybrid Bio-Inspired Feature Selection Algorithms Along With Random Forest Mo... | CIC-DDoS2019 / UNSW-NB15 | XGBoost / Random Forest / SVM / LSTM          | To verify                | To verify                | Medium                     |
| BIB087 | 2021.0 | Efficient Detection of DDoS Attacks Using a Hybrid Deep Learning Model with Improved Feature Selecti... | CIC-DDoS2019             | LSTM / CNN / Deep Learning / Machine Learning | To verify                | To verify                | Medium                     |
| BIB088 | 2020.0 | Building an efficient intrusion detection system based on feature selection and ensemble classifier     | NSL-KDD                  | Random Forest / Ensemble / Machine Learning   | To verify                | To verify                | Medium                     |
| BIB007 | 2020.0 | Detecting DDoS Attacks in Software-Defined Networks Through Feature Selection Methods and Machine Le... |                          | SVM / Machine Learning                        | To verify                | To verify                | Medium                     |
| BIB048 | 2018.0 | Improving performance of intrusion detection system using ensemble methods and feature selection        | NSL-KDD                  | Ensemble / Machine Learning                   | To verify                | To verify                | Medium                     |
| MAN018 | 2017.0 | Feature selection techniques for intrusion detecti                                                      |                          |                                               | To verify from full text | To verify from full text | Medium                     |
| BIB018 | 2017.0 | Feature selection techniques for intrusion detection using non-bio-inspired and bio-inspired optimiz... |                          | Machine Learning                              | To verify                | To verify                | Medium                     |
| MAN002 |        | Kaynak et al. - The search process of a PSO algorithm should be a                                       |                          |                                               | To verify from full text | To verify from full text | Medium                     |
| BIB167 | 2023.0 | A review of opportunities and challenges of chatbots in education                                       |                          |                                               | To verify                | To verify                | Low                        |
| BIB092 | 2022.0 | An efficient IDS in cloud environment using feature selection based on DM algorithm                     |                          |                                               | To verify                | To verify                | Low                        |

## 3.6. Runtime, Controller ve Testbed Entegrasyonu

SDN güvenliği çalışmalarında Mininet, Ryu, OpenFlow ve Open vSwitch tabanlı deneysel ortamlar sık kullanılmaktadır. Bu araçlar, kontrollü saldırı senaryoları üretmek, flow-level istatistik toplamak ve denetleyici taraflı karar mekanizmalarını test etmek için uygundur. Buna rağmen literatürdeki birçok çalışmanın offline veri kümesi değerlendirmesi ile sınırlı kaldığı; model çıktısının gerçek zamanlı veya yarı gerçek zamanlı denetleyici aksiyonlarına nasıl bağlandığını ayrıntılı göstermediği görülmektedir.

Bu alt başlık için öne çıkan kaynaklar:

- `LR005` (2026.0) — A Systematic Review of Machine-Learning-Based Detection of DDoS Attacks in Software-Def...
- `LR002` (2025.0) — Assessing SDN Controller Vulnerabilities: A Survey on Attack Detection and Datasets
- `LR003` (2024.0) — Machine learning-based DDoS attack detection and prevention in SDN-enabled IoT systems
- `MAN008` (2023.0) — A framework to detect DDoS attack in Ryu controlle
- `MAN011` (2023.0) — SDN Controllers and ML-Based Anomaly Detection in
- `LR004` (2025.0) — SNT: Simulated Network Traffic Using Mininet and Ryu
- `BIB053` (2023.0) — A framework to detect DDoS attack in Ryu controller based software defined networks usi...
- `BIB036` (2023.0) — SDN Controllers and ML-Based Anomaly Detection in Embedded Systems: A Comparative Analysis
- `BIB051` (2021.0) — Deep Neural Network (DNN) Solution for Real-time Detection of Distributed Denial of Ser...
- `BIB012` (2020.0) — Near real-time security system applied to SDN environments in IoT networks using convol...
- `BIB056` (2020.0) — Neural Network-Based Approach for Detection and Mitigation of DDoS Attacks in SDN Envir...
- `BIB056` (2016.0) — Deep learning approach for Network Intrusion Detection in Software Defined Networking

### Tablo 3.4. Runtime/Controller/Testbed Odaklı Seçilmiş Çalışmalar

| id     |   year | title                                                                                                   | dataset                                               | ml_dl_model                                      | real_time_or_offline                                    | mitigation_action                                       | relevance_to_this_thesis   |
|:-------|-------:|:--------------------------------------------------------------------------------------------------------|:------------------------------------------------------|:-------------------------------------------------|:--------------------------------------------------------|:--------------------------------------------------------|:---------------------------|
| LR005  |   2026 | A Systematic Review of Machine-Learning-Based Detection of DDoS Attacks in Software-Defined Networks    | Multiple datasets across reviewed studies             | ML-based DDoS detection approaches               | Mostly review-level classification                      | Detection-centered; mitigation varies by reviewed study | High                       |
| LR002  |   2025 | Assessing SDN Controller Vulnerabilities: A Survey on Attack Detection and Datasets                     | Datasets used in ML-based detection methods discussed | Statistical and ML approaches                    | Survey-level discussion                                 | Detection focus; controller protection context          | High                       |
| LR003  |   2024 | Machine learning-based DDoS attack detection and prevention in SDN-enabled IoT systems                  | To be extracted from full text                        | Machine learning algorithms                      | Detection/prevention setting; runtime details to verify | Prevention method proposed                              | High                       |
| MAN008 |   2023 | A framework to detect DDoS attack in Ryu controlle                                                      |                                                       |                                                  | To verify from full text                                | To verify from full text                                | High                       |
| MAN011 |   2023 | SDN Controllers and ML-Based Anomaly Detection in                                                       |                                                       |                                                  | To verify from full text                                | To verify from full text                                | High                       |
| LR004  |   2025 | SNT: Simulated Network Traffic Using Mininet and Ryu                                                    | SNT dataset                                           | Dataset for ML model training/evaluation         | Dataset resource                                        | Not primary focus                                       | Medium                     |
| BIB053 |   2023 | A framework to detect DDoS attack in Ryu controller based software defined networks using feature ex... |                                                       | XGBoost / Random Forest / SVM / Machine Learning | To verify                                               | To verify                                               | Medium                     |
| BIB036 |   2023 | SDN Controllers and ML-Based Anomaly Detection in Embedded Systems: A Comparative Analysis              |                                                       | SVM / Decision Tree / Machine Learning           | To verify                                               | To verify                                               | Medium                     |
| BIB051 |   2021 | Deep Neural Network (DNN) Solution for Real-time Detection of Distributed Denial of Service (DDoS) A... |                                                       |                                                  | To verify                                               | To verify                                               | Medium                     |
| BIB012 |   2020 | Near real-time security system applied to SDN environments in IoT networks using convolutional neura... |                                                       | CNN / Deep Learning                              | To verify                                               | To verify                                               | Medium                     |

## 3.7. SDN Tabanlı Önleme ve Mitigation Yaklaşımları

DDoS tespitinin güvenlik açısından anlamlı hale gelebilmesi için tespit sonucunun ağ üzerinde uygulanabilir önleme aksiyonlarına dönüştürülmesi gerekir. Literatürde drop, rate-limit, reroute, quarantine veya blacklist gibi aksiyonlar farklı biçimlerde ele alınmaktadır. Ancak bu aksiyonların aynı çalışma zamanı prototipi içinde birlikte değerlendirilmesi ve model-controller uyumunun flow-level olarak gösterilmesi daha sınırlı bir araştırma alanıdır.

Bu tez çalışması bu noktada literatürdeki boşluğa odaklanmaktadır. Canonical runtime validation sürecinde rate-limit, drop ve quarantine aksiyonları aynı port-aware/protocol-aware deney zinciri içinde gözlemlenmiştir.

Bu alt başlık için öne çıkan kaynaklar:

- `LR005` (2026.0) — A Systematic Review of Machine-Learning-Based Detection of DDoS Attacks in Software-Def...
- `LR001` (2025.0) — A Comprehensive Review of DDoS Detection and Mitigation Models in Software-Defined Netw...
- `LR003` (2024.0) — Machine learning-based DDoS attack detection and prevention in SDN-enabled IoT systems
- `BIB039` (2024.0) — SDN-based detection and mitigation of DDoS attacks on smart homes
- `BIB105` (2022.0) — An optimized weighted voting based ensemble model for DDoS attack detection and mitigat...
- `MAN016` (2020.0) — Learning-Driven Detection and Mitigation of DDoS A
- `BIB045` (2017.0) — DoS attack mitigation using rule based and anomaly based techniques in software defined...
- `BIB005` (2016.0) — ATLANTIC: A framework for anomaly traffic detection, classification, and mitigation in SDN
- `BIB034` (2022.0) — Machine Learning Based Distributed Denial-of-Services Attacks Detection and Mitigation ...
- `BIB006` (2020.0) — Learning-Driven Detection and Mitigation of DDoS Attack in IoT via SDN-Cloud Architecture
- `BIB108` (2020.0) — Long Short-Term Memory and Fuzzy Logic for Anomaly Detection and Mitigation in Software...
- `BIB056` (2020.0) — Neural Network-Based Approach for Detection and Mitigation of DDoS Attacks in SDN Envir...

### Tablo 3.5. Mitigation/Prevention Odaklı Seçilmiş Çalışmalar

| id     |   year | title                                                                                                   | dataset                                                 | ml_dl_model                            | real_time_or_offline                                                | mitigation_action                                       | relevance_to_this_thesis   |
|:-------|-------:|:--------------------------------------------------------------------------------------------------------|:--------------------------------------------------------|:---------------------------------------|:--------------------------------------------------------------------|:--------------------------------------------------------|:---------------------------|
| LR005  |   2026 | A Systematic Review of Machine-Learning-Based Detection of DDoS Attacks in Software-Defined Networks    | Multiple datasets across reviewed studies               | ML-based DDoS detection approaches     | Mostly review-level classification                                  | Detection-centered; mitigation varies by reviewed study | High                       |
| LR001  |   2025 | A Comprehensive Review of DDoS Detection and Mitigation Models in Software-Defined Networks             | Legacy compatible and SDN-contextual datasets discussed | ML / DL / Federated Learning models    | Mostly literature-level comparison; includes performance discussion | Detection and mitigation models reviewed                | High                       |
| LR003  |   2024 | Machine learning-based DDoS attack detection and prevention in SDN-enabled IoT systems                  | To be extracted from full text                          | Machine learning algorithms            | Detection/prevention setting; runtime details to verify             | Prevention method proposed                              | High                       |
| BIB039 |   2024 | SDN-based detection and mitigation of DDoS attacks on smart homes                                       |                                                         | SVM / Decision Tree / Machine Learning | To verify                                                           | To verify                                               | High                       |
| BIB105 |   2022 | An optimized weighted voting based ensemble model for DDoS attack detection and mitigation in SDN en... | CIC-DDoS2019                                            | Random Forest / SVM / Ensemble         | To verify                                                           | To verify                                               | High                       |
| MAN016 |   2020 | Learning-Driven Detection and Mitigation of DDoS A                                                      |                                                         |                                        | To verify from full text                                            | Mitigation / prevention                                 | High                       |
| BIB045 |   2017 | DoS attack mitigation using rule based and anomaly based techniques in software defined networking      |                                                         |                                        | To verify                                                           | To verify                                               | High                       |
| BIB005 |   2016 | ATLANTIC: A framework for anomaly traffic detection, classification, and mitigation in SDN              |                                                         | Machine Learning                       | To verify                                                           | To verify                                               | High                       |
| BIB034 |   2022 | Machine Learning Based Distributed Denial-of-Services Attacks Detection and Mitigation Testbed for S... |                                                         | Machine Learning                       | To verify                                                           | To verify                                               | Medium                     |
| BIB006 |   2020 | Learning-Driven Detection and Mitigation of DDoS Attack in IoT via SDN-Cloud Architecture               |                                                         |                                        | To verify                                                           | To verify                                               | Medium                     |

## 3.8. Veri Kümeleri ve Deneysel Değerlendirme

DDoS tespit çalışmalarında CIC-DDoS2019, CICIDS, InSDN, NSL-KDD, UNSW-NB15 ve özel oluşturulmuş veri kümeleri gibi farklı kaynaklar kullanılmaktadır. Veri kümesi seçimi, modelin saldırı tiplerini öğrenme kapasitesini ve çalışma zamanı ortamına aktarılabilirliğini doğrudan etkiler. SDN bağlamı içeren veri kümeleri, denetleyici ve flow-level güvenlik analizi açısından daha uygun olabilir; ancak klasik IDS veri kümeleri de model karşılaştırması için yaygın olarak kullanılmaktadır.

Bu alt başlık için öne çıkan kaynaklar:

- `LR005` (2026.0) — A Systematic Review of Machine-Learning-Based Detection of DDoS Attacks in Software-Def...
- `LR001` (2025.0) — A Comprehensive Review of DDoS Detection and Mitigation Models in Software-Defined Netw...
- `LR002` (2025.0) — Assessing SDN Controller Vulnerabilities: A Survey on Attack Detection and Datasets
- `BIB029` (2024.0) — A Survey on the Latest Intrusion Detection Datasets for Software Defined Networking Env...
- `LR003` (2024.0) — Machine learning-based DDoS attack detection and prevention in SDN-enabled IoT systems
- `BIB021` (2022.0) — A new DDoS attacks intrusion detection model based on deep learning for cybersecurity
- `BIB105` (2022.0) — An optimized weighted voting based ensemble model for DDoS attack detection and mitigat...
- `BIB043` (2021.0) — Designing a Network Intrusion Detection System Based on Machine Learning for Software D...
- `BIB047` (2021.0) — Efficient Intrusion Detection System for SDN Orchestrated Internet of Things
- `BIB054` (2020.0) — Hybrid Deep Learning: An Efficient Reconnaissance and Surveillance Detection Mechanism ...
- `LR004` (2025.0) — SNT: Simulated Network Traffic Using Mininet and Ryu
- `MAN009` (2024.0) — A Survey on the Latest Intrusion Detection Dataset

### Tablo 3.6. Veri Kümesi Odaklı Seçilmiş Çalışmalar

| id     |   year | title                                                                                                   | dataset                                                 | ml_dl_model                                                | real_time_or_offline                                                | mitigation_action                                       | relevance_to_this_thesis   |
|:-------|-------:|:--------------------------------------------------------------------------------------------------------|:--------------------------------------------------------|:-----------------------------------------------------------|:--------------------------------------------------------------------|:--------------------------------------------------------|:---------------------------|
| LR005  |   2026 | A Systematic Review of Machine-Learning-Based Detection of DDoS Attacks in Software-Defined Networks    | Multiple datasets across reviewed studies               | ML-based DDoS detection approaches                         | Mostly review-level classification                                  | Detection-centered; mitigation varies by reviewed study | High                       |
| LR001  |   2025 | A Comprehensive Review of DDoS Detection and Mitigation Models in Software-Defined Networks             | Legacy compatible and SDN-contextual datasets discussed | ML / DL / Federated Learning models                        | Mostly literature-level comparison; includes performance discussion | Detection and mitigation models reviewed                | High                       |
| LR002  |   2025 | Assessing SDN Controller Vulnerabilities: A Survey on Attack Detection and Datasets                     | Datasets used in ML-based detection methods discussed   | Statistical and ML approaches                              | Survey-level discussion                                             | Detection focus; controller protection context          | High                       |
| BIB029 |   2024 | A Survey on the Latest Intrusion Detection Datasets for Software Defined Networking Environments        | InSDN                                                   | Deep Learning / Machine Learning                           | To verify                                                           | To verify                                               | High                       |
| LR003  |   2024 | Machine learning-based DDoS attack detection and prevention in SDN-enabled IoT systems                  | To be extracted from full text                          | Machine learning algorithms                                | Detection/prevention setting; runtime details to verify             | Prevention method proposed                              | High                       |
| BIB021 |   2022 | A new DDoS attacks intrusion detection model based on deep learning for cybersecurity                   | CIC-DDoS2019                                            | LSTM / CNN / Deep Learning / Machine Learning              | To verify                                                           | To verify                                               | High                       |
| BIB105 |   2022 | An optimized weighted voting based ensemble model for DDoS attack detection and mitigation in SDN en... | CIC-DDoS2019                                            | Random Forest / SVM / Ensemble                             | To verify                                                           | To verify                                               | High                       |
| BIB043 |   2021 | Designing a Network Intrusion Detection System Based on Machine Learning for Software Defined Networ... | NSL-KDD                                                 | XGBoost / Random Forest / Decision Tree / Machine Learning | To verify                                                           | To verify                                               | High                       |
| BIB047 |   2021 | Efficient Intrusion Detection System for SDN Orchestrated Internet of Things                            | CICIDS2017                                              | Random Forest / Machine Learning                           | To verify                                                           | To verify                                               | High                       |
| BIB054 |   2020 | Hybrid Deep Learning: An Efficient Reconnaissance and Surveillance Detection Mechanism in SDN           | CICIDS2017                                              | LSTM / CNN / Deep Learning / Machine Learning              | To verify                                                           | To verify                                               | High                       |

## 3.9. Literatürdeki Boşluklar

Literatür sentezinden hareketle aşağıdaki boşluklar öne çıkmaktadır:

- Çalışmaların önemli bir bölümü offline classification başarısına odaklanmakta, runtime SDN denetleyici entegrasyonunu sınırlı ele almaktadır.
- Model çıktısının OpenFlow tabanlı aksiyonlara nasıl dönüştürüldüğü her çalışmada açık değildir.
- Port-aware ve protocol-aware flow-level eşleştirme çoğu çalışmada ayrıntılı tartışılmamaktadır.
- Rate-limit, drop ve quarantine aksiyonlarının aynı prototip içinde birlikte değerlendirildiği çalışmalar sınırlıdır.
- Controller overhead, inference latency, flow-stat polling maliyeti ve OpenFlow kural kurulum gecikmesi çoğu çalışmada ikincil düzeyde kalmaktadır.

## 3.10. Bu Tez Çalışmasının Literatürdeki Konumu

Bu tez çalışması, literatürdeki offline ML tabanlı DDoS tespit yaklaşımları ile SDN tabanlı aktif IPS yaklaşımları arasında bir köprü kurmaktadır. Önerilen sistem; Final XGBoost Top-20 modeli, FastAPI inference servisi, PCAP tabanlı runtime feature extraction, Ryu tabanlı policy engine ve OpenFlow tabanlı enforcement mekanizmalarını bir arada kullanmaktadır.

Çalışmanın ayırt edici yönü, model çıktılarının port-aware ve protocol-aware biçimde controller loglarıyla karşılaştırılmasıdır. Bu sayede aynı kaynak-hedef IP çifti üzerindeki benign TCP, benign UDP, malicious UDP ve quarantine-observed akışlar birbirinden ayrılabilmektedir. Canonical run_05 deneyinde rate-limit, drop ve quarantine aksiyonlarının gözlenmesi, önerilen sistemin pasif IDS yerine aktif SDN tabanlı IDS/IPS prototipi olarak konumlandırılabileceğini göstermektedir.

## 3.11. Bölüm Özeti

Bu bölümde SDN tabanlı DDoS tespiti ve önleme literatürü, ML/DL yaklaşımları, özellik seçimi, runtime/controller entegrasyonu, mitigation/prevention ve veri kümesi kullanımı açısından değerlendirilmiştir. Literatür sentezi, bu tez çalışmasının temel katkısının makine öğrenmesi tabanlı tespiti çalışma zamanı SDN denetleyici aksiyonlarına bağlayan port-aware/protocol-aware aktif IDS/IPS zinciri olduğunu göstermektedir.
