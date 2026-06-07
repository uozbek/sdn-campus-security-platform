# Tez İçin TikZ Görsel Taslakları

Bu dosya, tez Bölüm 4 içinde kullanılabilecek TikZ tabanlı mimari, model geliştirme ve çalışma zamanı IDS/IPS karar döngüsü görsel taslaklarını içerir.

---

## Şekil 4.x. Önerilen SDN Tabanlı IDS/IPS Mimarisinin Bileşenleri

\begin{tikzpicture}[
  node distance=1.6cm,
  box/.style={draw, rounded corners, align=center, minimum width=3.2cm, minimum height=1cm},
  arrow/.style={->, thick}
]
\node[box] (mininet) {Mininet / Open vSwitch\\Kampüs Benzeri Topoloji};
\node[box, right=2.4cm of mininet] (ryu) {Ryu SDN Denetleyicisi\\Akış İzleme ve Politika};
\node[box, right=2.4cm of ryu] (fastapi) {FastAPI ML Servisi\\Çalışma Zamanı Çıkarım};
\node[box, below=1.5cm of ryu] (config) {config.yaml\\Eşikler ve Politika Ayarları};
\node[box, above=1.5cm of ryu] (monitor) {Kaynak İzleme\\CPU / Bellek / Gecikme};

\draw[arrow] (mininet) -- node[above]{Packet-In / Flow Stats} (ryu);
\draw[arrow] (ryu) -- node[above]{POST /predict} (fastapi);
\draw[arrow] (fastapi) -- node[below]{Tahmin + Güven Skoru} (ryu);
\draw[arrow] (ryu) -- node[below]{OpenFlow FlowMod / Meter} (mininet);
\draw[arrow] (config) -- (ryu);
\draw[arrow] (config) -- (fastapi);
\draw[arrow] (monitor) -- (ryu);
\end{tikzpicture}

---

## Şekil 4.x. Model Geliştirme ve Nihai Model Seçimi İş Akışı

\begin{tikzpicture}[
  node distance=1.3cm,
  box/.style={draw, rounded corners, align=center, minimum width=3.1cm, minimum height=0.9cm},
  arrow/.style={->, thick}
]
\node[box] (raw) {CIC-DDoS2019\\Ham Veri};
\node[box, right=1.4cm of raw] (clean) {Veri Temizleme};
\node[box, right=1.4cm of clean] (reduce) {Özellik Azaltma};
\node[box, below=1.3cm of reduce] (meta) {Meta-sezgisel\\PSO / HHO / GWO / DFO};
\node[box, above=1.3cm of reduce] (topk) {XGBoost\\Top-K Özellik Önemi};
\node[box, right=1.6cm of reduce] (train) {Aday Model\\Eğitimi};
\node[box, right=1.4cm of train] (compare) {Model\\Karşılaştırma};
\node[box, right=1.4cm of compare] (final) {Final XGBoost\\Top-20};
\node[box, right=1.4cm of final] (api) {FastAPI\\Çıkarım Servisi};

\draw[arrow] (raw) -- (clean);
\draw[arrow] (clean) -- (reduce);
\draw[arrow] (reduce) -- (meta);
\draw[arrow] (reduce) -- (topk);
\draw[arrow] (meta) -- (train);
\draw[arrow] (topk) -- (train);
\draw[arrow] (train) -- (compare);
\draw[arrow] (compare) -- (final);
\draw[arrow] (final) -- (api);
\end{tikzpicture}

---

## Şekil 4.x. Çalışma Zamanı IDS/IPS Karar Döngüsü

\begin{tikzpicture}[
  node distance=1.4cm,
  box/.style={draw, rounded corners, align=center, minimum width=3cm, minimum height=0.9cm},
  decision/.style={draw, diamond, aspect=2, align=center},
  arrow/.style={->, thick}
]
\node[box] (flow) {Akış İstatistikleri};
\node[box, right=1.5cm of flow] (controller) {Ryu IDS/IPS\\Denetleyicisi};
\node[box, right=1.5cm of controller] (api) {FastAPI\\ML Servisi};
\node[decision, below=1.4cm of api] (risk) {Risk yüksek mi?};
\node[box, left=1.5cm of risk] (allow) {Allow / Monitor};
\node[box, right=1.5cm of risk] (mitigate) {Rate-limit / Drop\\Quarantine};
\node[box, below=1.4cm of risk] (flowmod) {OpenFlow\\FlowMod / Meter};

\draw[arrow] (flow) -- (controller);
\draw[arrow] (controller) -- node[above]{POST /predict} (api);
\draw[arrow] (api) -- (risk);
\draw[arrow] (risk) -- node[above]{Hayır} (allow);
\draw[arrow] (risk) -- node[above]{Evet} (mitigate);
\draw[arrow] (mitigate) -- (flowmod);
\draw[arrow] (flowmod) -| (controller);
\end{tikzpicture}
