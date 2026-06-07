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

| id | yıl | çalışma | veri kümesi / trafik | yöntem / model | controller / testbed | runtime doğrulama | tez açısından önemi |
|:---|---:|:---|:---|:---|:---|:---|:---|
| LR005 | 2026 | A Systematic Review of Machine-Learning-Based Detection of DDoS Attacks in Software-Defined Networks | İncelenen çalışmalarda çoklu veri kümeleri | ML tabanlı DDoS tespit yaklaşımları | Mininet, Ryu ve farklı SDN ortamları review düzeyinde ele alınır | Çalışmalara göre değişken | SDN/DDoS literatürünün güncel genel çerçevesini verir |
| LR002 | 2025 | Assessing SDN Controller Vulnerabilities: A Survey on Attack Detection and Datasets | SDN controller güvenliği ve saldırı tespit veri kümeleri | İstatistiksel ve ML tabanlı yaklaşımlar | Controller güvenliği bağlamı | Review düzeyi | Denetleyici güvenliği ve veri seti seçimi için arka plan sağlar |
| LR004 | 2025 | SNT: Simulated Network Traffic Using Mininet and Ryu | SNT dataset | ML eğitim/değerlendirme için trafik üretimi | Mininet / Ryu | Simülasyon ve veri üretimi odaklı | Tezdeki Mininet/Ryu tabanlı doğrulama hattı ile ilişkilidir |
| BIB053 | 2023 | A framework to detect DDoS attack in Ryu controller based software defined networks using feature extraction and classification | SDN/Ryu ortamında akış tabanlı trafik | XGBoost / Random Forest / SVM | Ryu controller | Controller tabanlı doğrulama | Tezin Ryu tabanlı IDS karar hattıyla doğrudan ilişkilidir |
| BIB036 | 2023 | SDN Controllers and ML-Based Anomaly Detection in Embedded Systems: A Comparative Analysis | SDN/embedded system bağlamı | SVM / Decision Tree / ML yaklaşımları | SDN controller karşılaştırması | Karşılaştırmalı değerlendirme | Controller seçimi ve ML tabanlı anomaly detection bağlamı sunar |
| BIB034 | 2022 | Machine Learning Based Distributed Denial-of-Services Attacks Detection and Mitigation Testbed for SDN-Enabled IoT Devices | SDN-enabled IoT trafik/testbed | ML tabanlı DDoS tespit ve mitigation | SDN-enabled IoT testbed | Testbed düzeyinde değerlendirme | Runtime/testbed ve mitigation boyutunu birlikte temsil eder |
| BIB051 | 2021 | Deep Neural Network (DNN) Solution for Real-time Detection of Distributed Denial of Service (DDoS) Attacks in Software Defined Networks | SDN bağlamlı DDoS trafiği | DNN | SDN ortamı | Real-time detection vurgusu | Çevrimdışı model başarımı ile real-time SDN tespiti arasındaki farkı tartışmak için uygundur |
| BIB012 | 2020 | Near real-time security system applied to SDN environments in IoT networks using convolutional neural network | SDN/IoT trafik | CNN / Deep Learning | SDN ortamı | Near real-time | Tezin çalışma zamanı doğrulama motivasyonunu destekler |
| BIB009 | 2015 | Interactive monitoring, visualization, and configuration of OpenFlow-based SDN | OpenFlow tabanlı ağ trafiği | İzleme / görselleştirme / yapılandırma | OpenFlow-based SDN | Yönetim düzlemi odaklı | OpenFlow yönetim ve izleme boyutu için destekleyici arka plan sağlar |

### Tablo 3.5. Mitigation/Prevention Odaklı Seçilmiş Çalışmalar

| id | yıl | çalışma | veri kümesi / trafik | yöntem / model | mitigation / prevention yaklaşımı | runtime / controller bağlamı | tez açısından önemi |
|:---|---:|:---|:---|:---|:---|:---|:---|
| LR001 | 2025 | A Comprehensive Review of DDoS Detection and Mitigation Models in Software-Defined Networks | SDN bağlamlı çoklu veri kümeleri | ML / DL / federated learning tabanlı yaklaşımlar | Detection ve mitigation modelleri review düzeyinde ele alınır | Review düzeyi | Tezin detection-only yaklaşımlardan ayrıldığı noktayı konumlandırır |
| LR005 | 2026 | A Systematic Review of Machine-Learning-Based Detection of DDoS Attacks in Software-Defined Networks | İncelenen çalışmalarda çoklu veri kümeleri | ML tabanlı DDoS detection | Mitigation kapsamı çalışmalara göre değişir | Review düzeyi | ML tabanlı SDN/DDoS çalışmalarının genel sınırlarını gösterir |
| LR003 | 2024 | Machine learning-based DDoS attack detection and prevention in SDN-enabled IoT systems | SDN-enabled IoT bağlamı | Machine learning algorithms | Detection/prevention yaklaşımı | SDN-enabled IoT setting | Tespit ve önleme birlikteliğini güncel literatürden destekler |
| BIB039 | 2024 | SDN-based detection and mitigation of DDoS attacks on smart homes | Smart home / SDN trafik bağlamı | SVM / Decision Tree / ML | Detection and mitigation | SDN tabanlı ortam | Güncel SDN-based mitigation literatürünü temsil eder |
| BIB105 | 2022 | An optimized weighted voting based ensemble model for DDoS attack detection and mitigation in SDN environment | CIC-DDoS2019 | Weighted voting ensemble / RF / SVM | DDoS detection and mitigation | SDN environment | CIC-DDoS2019 ve ensemble tabanlı mitigation bağlamı açısından önemlidir |
| BIB034 | 2022 | Machine Learning Based Distributed Denial-of-Services Attacks Detection and Mitigation Testbed for SDN-Enabled IoT Devices | SDN-enabled IoT trafik/testbed | Machine learning | Detection and mitigation testbed | SDN-enabled testbed | Tezin testbed + mitigation yönüyle ilişkilidir |
| BIB006 | 2020 | Learning-Driven Detection and Mitigation of DDoS Attack in IoT via SDN-Cloud Architecture | IoT / SDN-cloud trafik bağlamı | Learning-driven detection | Detection and mitigation | SDN-cloud architecture | SDN tabanlı önleme mimarilerinin pratik boyutunu destekler |
| BIB002 | 2020 | Bandwidth Control Mechanism and Extreme Gradient Boosting Algorithm for Protecting Software-Defined Networks Against DDoS Attacks | SDN trafik bağlamı | Extreme Gradient Boosting | Bandwidth control | SDN protection setting | Tezdeki rate-limit/bandwidth-control aksiyonları için literatür desteği sağlar |
| BIB045 | 2017 | DoS attack mitigation using rule based and anomaly based techniques in software defined networking | SDN trafik bağlamı | Rule-based + anomaly-based techniques | DoS mitigation | SDN environment | Tezdeki heuristic + ML policy fikriyle ilişkilidir |
| BIB005 | 2016 | ATLANTIC: A framework for anomaly traffic detection, classification, and mitigation in SDN | SDN trafik bağlamı | ML tabanlı anomaly detection/classification | Detection, classification and mitigation | SDN framework | Detection sonucunun mitigation aksiyonuna bağlanması açısından erken ve önemli bir örnektir |

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

## 3.x. Literatürdeki Çalışmalar ile Bu Tez Çalışmasının Yöntemsel Karşılaştırması

Literatür taramasında incelenen çalışmalar, SDN tabanlı DDoS tespiti, ML/DL tabanlı sınıflandırma, özellik seçimi, çalışma zamanı doğrulama ve aktif önleme mekanizmaları açısından karşılaştırılmıştır. Tablo 3.x, seçili çalışmalar ile bu tez çalışmasını yöntemsel bileşenler bakımından özetlemektedir. Tabloda görüldüğü üzere, mevcut çalışmaların önemli bir kısmı SDN bağlamında yüksek tespit başarısı raporlamakla birlikte, port/protocol-aware controller karşılaştırması ve rate-limit/drop/quarantine aksiyonlarının birlikte doğrulanması daha sınırlı kalmaktadır.

**Tablo 3.7. SDN tabanlı DDoS tespit ve önleme çalışmalarının yöntemsel karşılaştırması**

| Çalışma | Yıl | SDN bağlamı | Denetleyici/Testbed | Veri kümesi | Model/Yöntem | Özellik seçimi | Runtime doğrulama | Controller entegrasyonu | Mitigation/Prevention | Port/Protocol-aware karşılaştırma | Tezle ilişkisi |
|:---|---:|:---|:---|:---|:---|:---|:---|:---|:---|:---|:---|
| LR005 — Systematic review of ML-based DDoS detection in SDN | 2026 | Var | İncelenen çalışmalarda Mininet/Ryu örnekleri | Çoklu veri kümeleri | ML tabanlı DDoS detection | Çalışmalara göre değişken | Çalışmalara göre değişken | Çalışmalara göre değişken | Çalışmalara göre değişken | Yok/Belirsiz | Güncel literatür sentezi |
| LR001 — Comprehensive review of DDoS detection and mitigation models in SDN | 2025 | Var | Çoklu SDN ortamları tartışılır | SDN bağlamlı çoklu veri kümeleri | ML/DL/Federated learning | Çalışmalara göre değişken | Review düzeyi | Belirsiz/Yok | Mitigation modelleri tartışılır | Yok/Belirsiz | Detection ve mitigation alanını genel olarak konumlandırır |
| LR004 — SNT: Simulated Network Traffic Using Mininet and Ryu | 2025 | Var | Mininet / Ryu | SNT dataset | Trafik üretimi / ML veri seti | Uygulanmaz | Veri üretimi/simülasyon düzeyi | Var | Yok/Belirsiz | Yok/Belirsiz | Ryu/Mininet hattı için destekleyici kaynak |
| BIB039 — SDN-based detection and mitigation of DDoS attacks on smart homes | 2024 | Var | SDN tabanlı smart home ortamı | Smart home / SDN trafik | SVM / Decision Tree / ML | Yok/Belirsiz | Belirsiz | Belirsiz/Yok | Var | Yok/Belirsiz | Güncel SDN mitigation örneği |
| BIB053 — Ryu controller based DDoS detection framework | 2023 | Var | Ryu controller | SDN/Ryu ortamı | XGBoost / RF / SVM | Feature extraction | Controller tabanlı değerlendirme | Var | Yok/Belirsiz | Yok/Belirsiz | Tezin Ryu controller entegrasyonuyla doğrudan ilişkilidir |
| BIB036 — SDN controllers and ML-based anomaly detection | 2023 | Var | SDN controller karşılaştırması | SDN/embedded system bağlamı | SVM / Decision Tree / ML | Yok/Belirsiz | Karşılaştırmalı değerlendirme | Var | Yok/Belirsiz | Yok/Belirsiz | Controller/anomaly detection arka planı sağlar |
| BIB034 — ML-based DDoS detection and mitigation testbed for SDN-enabled IoT | 2022 | Var | SDN-enabled IoT testbed | SDN-enabled IoT trafik | Machine learning | Yok/Belirsiz | Testbed düzeyinde | Belirsiz/Yok | Var | Yok/Belirsiz | Testbed + mitigation boyutunu temsil eder |
| BIB105 — Optimized weighted voting ensemble for DDoS detection and mitigation in SDN | 2022 | Var | SDN environment | CIC-DDoS2019 | Weighted voting ensemble / RF / SVM | Optimizasyon/ensemble tasarımı | Belirsiz | Belirsiz/Yok | Var | Yok/Belirsiz | CIC-DDoS2019 ve ensemble-based mitigation açısından önemlidir |
| BIB051 — Real-time DNN solution for DDoS attacks in SDN | 2021 | Var | SDN environment | SDN/DDoS trafik | DNN | Yok/Belirsiz | Real-time detection | Belirsiz/Yok | Yok/Belirsiz | Yok/Belirsiz | Real-time SDN detection tartışması için uygundur |
| BIB012 — Near real-time security system in SDN/IoT using CNN | 2020 | Var | SDN/IoT environment | SDN/IoT trafik | CNN / Deep Learning | Yok/Belirsiz | Near real-time | Belirsiz/Yok | Yok/Belirsiz | Yok/Belirsiz | Runtime doğrulama ihtiyacını destekler |
| BIB002 — Bandwidth control + XGBoost for protecting SDN against DDoS | 2020 | Var | SDN protection setting | SDN trafik | XGBoost | Yok/Belirsiz | Belirsiz | Belirsiz/Yok | Bandwidth control | Yok/Belirsiz | Rate-limit/bandwidth-control aksiyonu için literatür desteği sağlar |
| BIB045 — Rule/anomaly-based DoS mitigation in SDN | 2017 | Var | SDN environment | SDN trafik | Rule-based + anomaly-based | Yok/Belirsiz | Belirsiz | Belirsiz/Yok | Var | Yok/Belirsiz | Heuristic + anomaly-based mitigation ile ilişkilidir |
| BIB005 — ATLANTIC anomaly detection/classification/mitigation framework | 2016 | Var | SDN framework | SDN trafik | ML tabanlı anomaly detection/classification | Yok/Belirsiz | Belirsiz | Belirsiz/Yok | Var | Yok/Belirsiz | Detection sonucunu mitigation ile ilişkilendiren erken örnektir |
| Bu tez çalışması | 2026 | Var | Mininet / Open vSwitch / Ryu / OpenFlow | CIC-DDoS2019 tabanlı seçilmiş veri + runtime PCAP | Final XGBoost Top-20 + FastAPI inference | Final Top-20 selected features | Var | Var | Rate-limit / Drop / Quarantine | Var | Önerilen çalışma |

### 3.x. Full Text İncelemelerine Dayalı Literatür Sentezi

A Grubu çekirdek kaynaklar üzerinde yapılan full text incelemeleri, SDN tabanlı DDoS tespit literatürünün yalnızca kullanılan makine öğrenmesi veya derin öğrenme modeline göre değil, aynı zamanda çalışma zamanı doğrulama düzeyi, denetleyici entegrasyonu, önleme aksiyonu üretimi ve veri seti/özellik çıkarımı bakımından da ayrıştırılması gerektiğini göstermektedir. Birçok çalışmada accuracy, precision, recall, F1-score veya AUC gibi sınıflandırma metrikleri güçlü biçimde raporlanmakta; ancak bu başarıların SDN denetleyici üzerinde uygulanabilir politika kararlarına nasıl dönüştürüldüğü her zaman aynı açıklıkta sunulmamaktadır. Bu nedenle literatür karşılaştırmasının yalnızca model başarımı ekseninde yapılması, SDN tabanlı IDS/IPS sistemlerinin pratik uygulanabilirliğini değerlendirmek için yetersiz kalabilmektedir.

Full text bulguları özellikle üç ayrımı görünür kılmaktadır. Birinci ayrım, çevrimdışı tespit çalışmaları ile çalışma zamanı denetleyici/testbed doğrulaması yapan çalışmalar arasındadır. Bazı çalışmalar veri seti üzerinde yüksek sınıflandırma başarımı elde etmeye odaklanırken, bazıları Ryu, Mininet, OpenFlow veya benzeri SDN bileşenleriyle daha uygulamaya yakın senaryolar kurmaktadır. İkinci ayrım, yalnızca saldırı tespiti yapan yaklaşımlar ile tespit sonucunu `drop`, `rate-limit`, `block` veya benzeri önleme aksiyonlarına dönüştüren yaklaşımlar arasındadır. Üçüncü ayrım ise kullanılan veri seti ve özellik çıkarım yaklaşımıyla ilgilidir. Bu tezde deneysel omurga, güncel DDoS trafiği ve akış tabanlı özellikler bakımından daha uygun görülen CIC-DDoS2019 ve CICFlowMeter-style özellikler üzerine kurulmuştur; NSL-KDD ise güncellik ve temsil kabiliyeti tartışmaları nedeniyle yalnızca tarihsel/bağlamsal düzeyde ele alınmaktadır.

Bu çerçevede Tablo 3.1–Tablo 3.7 birlikte değerlendirildiğinde, mevcut literatürde yüksek tespit başarımı raporlayan çalışmaların önemli bir kısmının IDS çıktısının SDN denetleyici üzerinde nasıl politika aksiyonuna dönüştürüleceği konusunu sınırlı biçimde ele aldığı görülmektedir. Bu tez çalışması, çevrimdışı makine öğrenmesi başarımını Ryu denetleyici, FastAPI tabanlı çıkarım servisi ve OpenFlow tabanlı önleme aksiyonlarıyla ilişkilendirerek bu boşluğu hedeflemektedir. Böylece literatür değerlendirmesi, yalnızca “hangi model daha başarılıdır?” sorusundan çıkarak “hangi yaklaşım SDN tabanlı kampüs ağı bağlamında uygulanabilir bir IDS/IPS mekanizmasına dönüşebilmektedir?” sorusuna genişletilmektedir.
