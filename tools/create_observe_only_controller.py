#!/usr/bin/env python3

from pathlib import Path
import re

SRC = Path("controller/campus_l3_ids_controller_v10_ml_ready.py")
DST = Path("controller/campus_l3_ids_controller_v10_observe_only.py")

if not SRC.exists():
    raise FileNotFoundError(f"Source controller not found: {SRC}")

text = SRC.read_text(encoding="utf-8")

header = '''"""
campus_l3_ids_controller_v10_observe_only.py

Bu sürüm, campus_l3_ids_controller_v10_ml_ready.py dosyasından türetilmiştir.

Amaç:
- L3 routing davranışını korumak
- IDS/ML prediction ve policy decision loglarını üretmek
- Drop, rate-limit ve quarantine OpenFlow mitigation kurallarını kurmamak
- Controller CPU/memory ve runtime metric testleri için güvenli observe-only mod sağlamak

Not:
- Bu dosya normal trafik baseline ölçümleri içindir.
- Gerçek IPS aksiyon testleri için campus_l3_ids_controller_v10_ml_ready.py kullanılacaktır.
"""

CONTROLLER_MODE = "observe_only"
ENABLE_MITIGATION = False

'''

# İlk docstring varsa değiştir; yoksa başa ekle.
if text.lstrip().startswith('"""'):
    text = re.sub(r'^\s*""".*?"""', header.rstrip(), text, count=1, flags=re.DOTALL)
else:
    text = header + "\n" + text

# Eğer yukarıdaki replacement sabitleri importlardan önce koyduysa sorun olmaz; Python sabitleri importtan önce olabilir.
# Ama dosyada tekrar ENABLE_MITIGATION varsa onu False yapalım.
text = re.sub(r'ENABLE_MITIGATION\s*=\s*True', 'ENABLE_MITIGATION = False', text)
text = re.sub(r'CONTROLLER_MODE\s*=\s*["\'].*?["\']', 'CONTROLLER_MODE = "observe_only"', text)

def replace_method_body(source, method_name, new_body_lines):
    """
    Class içindeki 4-space indentli method gövdesini bir sonraki methoda kadar değiştirir.
    """
    pattern = rf'(    def {method_name}\(self, [^\)]*\):\n)(.*?)(?=\n    def |\nclass |\Z)'
    match = re.search(pattern, source, flags=re.DOTALL)
    if not match:
        print(f"[WARN] Method not found: {method_name}")
        return source

    def_line = match.group(1)
    body = "".join(f"        {line}\n" for line in new_body_lines)
    print(f"[INFO] Patched method: {method_name}")
    return source[:match.start()] + def_line + body.rstrip() + "\n" + source[match.end():]

# Mitigation karar kapıları.
text = replace_method_body(
    text,
    "should_apply_mitigation",
    [
        '"""Observe-only modda drop/quarantine mitigation uygulanmaz."""',
        'return False',
    ],
)

text = replace_method_body(
    text,
    "should_apply_rate_limit",
    [
        '"""Observe-only modda meter/rate-limit mitigation uygulanmaz."""',
        'return False',
    ],
)

# Dosyada varsa quarantine kapısını da kapat.
text = replace_method_body(
    text,
    "should_apply_quarantine",
    [
        '"""Observe-only modda quarantine forwarding uygulanmaz."""',
        'return False',
    ],
)

# Daha güvenli olsun diye install_* fonksiyonlarının başına da erken çıkış ekleyelim.
def inject_early_return(source, method_name, message):
    pattern = rf'(    def {method_name}\(self, [^\)]*\):\n)'
    if not re.search(pattern, source):
        print(f"[WARN] Install method not found: {method_name}")
        return source

    injection = (
        rf'\1'
        f'        if not ENABLE_MITIGATION:\n'
        f'            self.logger.info("[OBSERVE_ONLY] {message}")\n'
        f'            return\n'
    )

    # Aynı injection daha önce eklendiyse tekrar ekleme.
    idx = source.find(f'[OBSERVE_ONLY] {message}')
    if idx != -1:
        print(f"[INFO] Already injected: {method_name}")
        return source

    print(f"[INFO] Injected early return: {method_name}")
    return re.sub(pattern, injection, source, count=1)

text = inject_early_return(
    text,
    "install_drop_rules_for_flow",
    "DROP mitigation skipped."
)

text = inject_early_return(
    text,
    "install_rate_limit_for_flow",
    "RATE_LIMIT mitigation skipped."
)

text = inject_early_return(
    text,
    "install_quarantine_rules_for_flow",
    "QUARANTINE mitigation skipped."
)

text = inject_early_return(
    text,
    "install_quarantine_forwarding_for_flow",
    "QUARANTINE forwarding skipped."
)

DST.write_text(text, encoding="utf-8")

print(f"[INFO] Observe-only controller written: {DST}")
