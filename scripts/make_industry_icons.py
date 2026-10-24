"""Draws the nine small industry icons used in the home page ticker. Usage: python scripts/make_industry_icons.py assets/icons

Each icon is the main object of that industry's illustration (assets/cards/industry-*.svg), with no scene, shadow or
background, centred in a square so every icon has the same visual weight."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from make_industry_art import (NAVY, NAVY_D, NAVY_DD, TEAL, TEAL_D, TEAL_L, ORANGE, WHITE, SOFT, gear, f)  # noqa: E402


def wrap(box, label, body):
    x, y, w, h = box
    side = max(w, h) + 8                      # a little air, then centre the drawing in a square
    cx, cy = x + w / 2, y + h / 2
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="{f(cx - side / 2)} {f(cy - side / 2)} {f(side)} {f(side)}" '
            f'role="img" aria-label="{label}">{body}</svg>')


def it_technology():
    return wrap((150, 84, 184, 144), "Laptop", f'''
<rect x="150" y="216" width="184" height="12" rx="6" fill="{NAVY_D}"/>
<rect x="172" y="84" width="140" height="132" rx="12" fill="{NAVY}"/>
<rect x="182" y="94" width="120" height="112" rx="6" fill="{NAVY_DD}"/>
<rect x="196" y="112" width="52" height="7" rx="3.5" fill="{TEAL}"/>
<rect x="210" y="132" width="80" height="7" rx="3.5" fill="{WHITE}"/>
<rect x="210" y="152" width="46" height="7" rx="3.5" fill="{SOFT}"/>
<rect x="196" y="172" width="7" height="14" rx="2" fill="{ORANGE}"/>''')


def healthcare():
    return wrap((182, 56, 120, 126), "Medical cross", f'''
<rect x="182" y="56" width="120" height="126" rx="28" fill="{NAVY}"/>
<rect x="242" y="56" width="60" height="126" rx="28" fill="{NAVY_D}" opacity=".45"/>
<rect x="226" y="82" width="32" height="74" rx="9" fill="{WHITE}"/>
<rect x="205" y="103" width="74" height="32" rx="9" fill="{WHITE}"/>
<circle cx="296" cy="64" r="9" fill="{ORANGE}"/>''')


def finance():
    bars = ""
    pts = []
    for x, h, c in [(148, 56, WHITE), (188, 86, SOFT), (228, 118, NAVY), (268, 150, TEAL)]:
        bars += f'<rect x="{x}" y="{236 - h}" width="30" height="{h}" rx="8" fill="{c}"/>'
        pts.append(f"{x + 15},{236 - h - 20}")
    return wrap((148, 66, 150, 170), "Rising bar chart", f'''
<rect x="136" y="236" width="174" height="4" rx="2" fill="{SOFT}"/>
{bars}
<polyline points="{' '.join(pts)}" fill="none" stroke="{NAVY_D}" stroke-width="4" stroke-linejoin="round" stroke-linecap="round"/>
<circle cx="{pts[-1].split(',')[0]}" cy="{pts[-1].split(',')[1]}" r="9" fill="{ORANGE}"/>''')


def engineering():
    return wrap((140, 66, 200, 160), "Gears", f'''
<polygon points="{gear(206, 160, 66, 54, 12, 8)}" fill="{NAVY}"/>
<circle cx="206" cy="160" r="40" fill="{NAVY_D}"/>
<circle cx="206" cy="160" r="14" fill="{WHITE}"/>
<polygon points="{gear(296, 110, 44, 35, 9, 14)}" fill="{TEAL}"/>
<circle cx="296" cy="110" r="14" fill="{WHITE}"/>
<circle cx="296" cy="110" r="5" fill="{ORANGE}"/>''')


def admin():
    rows = ""
    for i, y in enumerate((120, 152, 184)):
        rows += f'<rect x="196" y="{y}" width="20" height="20" rx="5" fill="{TEAL if i < 2 else WHITE}" stroke="{TEAL}" stroke-width="3"/>'
        rows += f'<rect x="226" y="{y + 3}" width="{64 - i * 10}" height="8" rx="4" fill="{NAVY if i == 0 else SOFT}"/>'
    return wrap((168, 54, 136, 194), "Clipboard checklist", f'''
<rect x="168" y="66" width="136" height="182" rx="16" fill="{NAVY}"/>
<rect x="180" y="88" width="112" height="148" rx="7" fill="{WHITE}"/>
{rows}
<polyline points="201,130 205,134 212,125" fill="none" stroke="{WHITE}" stroke-width="3.5" stroke-linecap="round" stroke-linejoin="round"/>
<polyline points="201,162 205,166 212,157" fill="none" stroke="{WHITE}" stroke-width="3.5" stroke-linecap="round" stroke-linejoin="round"/>
<rect x="218" y="54" width="40" height="28" rx="9" fill="{TEAL}"/>
<circle cx="238" cy="68" r="5" fill="{ORANGE}"/>''')


def manufacturing():
    roof = "".join(f'<polygon points="{140 + i * 56},160 {140 + i * 56},126 {140 + i * 56 + 56},160" fill="{TEAL}"/>' for i in range(4))
    return wrap((124, 46, 244, 200), "Factory", f'''
<rect x="330" y="86" width="30" height="76" rx="3" fill="{NAVY_D}"/>
<rect x="326" y="80" width="38" height="12" rx="3" fill="{TEAL}"/>
<circle cx="350" cy="58" r="12" fill="{SOFT}"/>
<rect x="124" y="160" width="244" height="86" rx="4" fill="{NAVY}"/>
<rect x="246" y="160" width="122" height="86" rx="4" fill="{NAVY_D}" opacity=".35"/>
{roof}
<rect x="150" y="184" width="22" height="20" rx="3" fill="{WHITE}"/>
<rect x="200" y="184" width="22" height="20" rx="3" fill="{WHITE}"/>
<rect x="306" y="190" width="40" height="56" rx="4" fill="{TEAL}"/>
<circle cx="266" cy="194" r="6" fill="{ORANGE}"/>''')


def logistics():
    return wrap((112, 124, 242, 122), "Delivery truck", f'''
<rect x="112" y="124" width="160" height="100" rx="10" fill="{SOFT}"/>
<rect x="112" y="188" width="160" height="14" fill="{TEAL}"/>
<path d="M272 156H328L354 190V224H272Z" fill="{NAVY}"/>
<path d="M284 166H322L340 188H284Z" fill="{TEAL_L}" opacity=".9"/>
<circle cx="156" cy="228" r="18" fill="{NAVY_D}"/><circle cx="156" cy="228" r="8" fill="{WHITE}"/>
<circle cx="318" cy="228" r="18" fill="{NAVY_D}"/><circle cx="318" cy="228" r="8" fill="{WHITE}"/>
<rect x="346" y="206" width="12" height="8" rx="3" fill="{ORANGE}"/>''')


def telecom():
    brace = ""
    for y in (150, 200):
        k = (y - 92) / 154
        brace += f'<line x1="{f(242 - 38 * k)}" y1="{y}" x2="{f(242 + 38 * k)}" y2="{y}" stroke="{NAVY_D}" stroke-width="4" stroke-linecap="round"/>'
    return wrap((176, 38, 132, 222), "Cell tower", f'''
<path d="M{f(242 - 30 * .7)} {f(88 - 30 * .7)}A30 30 0 0 1 {f(242 + 30 * .7)} {f(88 - 30 * .7)}" fill="none" stroke="{TEAL}" stroke-width="7" stroke-linecap="round"/>
<path d="M{f(242 - 52 * .7)} {f(88 - 52 * .7)}A52 52 0 0 1 {f(242 + 52 * .7)} {f(88 - 52 * .7)}" fill="none" stroke="{TEAL}" stroke-width="7" stroke-linecap="round" opacity=".55"/>
<line x1="242" y1="92" x2="204" y2="246" stroke="{NAVY}" stroke-width="8" stroke-linecap="round"/>
<line x1="242" y1="92" x2="280" y2="246" stroke="{NAVY}" stroke-width="8" stroke-linecap="round"/>
{brace}
<rect x="190" y="244" width="104" height="14" rx="7" fill="{NAVY_D}"/>
<circle cx="242" cy="88" r="12" fill="{WHITE}" stroke="{NAVY}" stroke-width="5"/>
<circle cx="242" cy="88" r="5" fill="{ORANGE}"/>''')


def retail():
    awning = f'<rect x="120" y="86" width="240" height="34" rx="6" fill="{NAVY}"/>'
    for i in (1, 3, 5):
        awning += f'<rect x="{120 + i * 40}" y="86" width="40" height="34" fill="{WHITE}"/>'
    return wrap((120, 84, 240, 164), "Storefront", f'''
<rect x="130" y="118" width="220" height="130" rx="6" fill="{SOFT}"/>
{awning}
<rect x="144" y="146" width="64" height="62" rx="5" fill="#E6F6F3" stroke="{NAVY}" stroke-width="5"/>
<rect x="272" y="146" width="64" height="62" rx="5" fill="#E6F6F3" stroke="{NAVY}" stroke-width="5"/>
<rect x="220" y="172" width="44" height="76" rx="4" fill="{TEAL}"/>
<circle cx="250" cy="212" r="4" fill="{ORANGE}"/>''')


ICONS = {
    "industry-it-technology": it_technology,
    "industry-healthcare-life-sciences": healthcare,
    "industry-finance-accounting": finance,
    "industry-engineering-construction": engineering,
    "industry-administrative-clerical": admin,
    "industry-manufacturing-industrial": manufacturing,
    "industry-logistics-supply-chain": logistics,
    "industry-telecommunications": telecom,
    "industry-retail-customer-support": retail,
}

if __name__ == "__main__":
    out = sys.argv[1]
    os.makedirs(out, exist_ok=True)
    for name, fn in ICONS.items():
        with open(os.path.join(out, name + ".svg"), "w", encoding="utf-8") as fh:
            fh.write(fn())
        print("wrote", name)
