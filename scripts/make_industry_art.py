"""Draws the nine Services industry illustrations as SVG files. Usage: python make_industry_art.py <out_dir>
Each scene: a main object, one supporting prop, a ground shadow and two-tone shading (about 15 shapes, ~36% more than the About set)."""
import math
import os
import sys

NAVY, NAVY_D, NAVY_DD = "#1E3A8A", "#172C6B", "#0F1E4A"
TEAL, TEAL_D, TEAL_L = "#14B8A6", "#0D9488", "#5EEAD4"
ORANGE, WHITE, INK = "#FF6A00", "#FFFFFF", "#0F172A"
SOFT, FAINT = "#C9D3EE", "#E4E9F5"
TINTS = {"mist": "#EEF2FB", "teal": "#E6F6F3", "sand": "#FFF1E6"}


def f(v):
    return f"{v:.1f}".rstrip("0").rstrip(".")


def gear(cx, cy, ro, ri, n, rot=0):
    p = 360 / n
    pts = []
    for i in range(n):
        a0 = rot + i * p
        for da, r in ((-0.34, ri), (-0.22, ro), (0.22, ro), (0.34, ri)):
            a = math.radians(a0 + da * p)
            pts.append(f"{f(cx + r * math.cos(a))},{f(cy + r * math.sin(a))}")
    return " ".join(pts)


def star(cx, cy, ro, ri):
    pts = []
    for i in range(10):
        r = ro if i % 2 == 0 else ri
        a = math.radians(-90 + i * 36)
        pts.append(f"{f(cx + r * math.cos(a))},{f(cy + r * math.sin(a))}")
    return " ".join(pts)


def shadow(cx, cy, rx, ry=8):
    return f'<ellipse cx="{cx}" cy="{cy}" rx="{rx}" ry="{ry}" fill="{INK}" opacity=".08"/>'


def wrap(tint, label, body):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 485 300" role="img" aria-label="{label}">'
            f'<rect width="485" height="300" fill="{TINTS[tint]}"/>{body}</svg>')


def it_technology():
    return wrap("mist", "A laptop showing code, with a cloud and a gear", f'''
{shadow(242, 262, 140)}
<rect x="150" y="216" width="184" height="12" rx="6" fill="{NAVY_D}"/>
<rect x="172" y="84" width="140" height="132" rx="12" fill="{NAVY}"/>
<rect x="182" y="94" width="120" height="112" rx="6" fill="{NAVY_DD}"/>
<rect x="196" y="112" width="52" height="7" rx="3.5" fill="{TEAL}"/>
<rect x="210" y="132" width="80" height="7" rx="3.5" fill="{WHITE}"/>
<rect x="210" y="152" width="46" height="7" rx="3.5" fill="{SOFT}"/>
<rect x="196" y="172" width="7" height="14" rx="2" fill="{ORANGE}"/>
<path d="M342 122H408A16 16 0 0 0 410 90A22 22 0 0 0 370 82A19 19 0 0 0 342 100A11 11 0 0 0 342 122Z" fill="{WHITE}"/>
<polyline points="376,116 376,92 367,101 376,92 385,101" fill="none" stroke="{TEAL}" stroke-width="5" stroke-linecap="round" stroke-linejoin="round"/>
<polygon points="{gear(110, 212, 24, 18, 8)}" fill="{TEAL}"/>
<circle cx="110" cy="212" r="8" fill="{WHITE}"/>
<circle cx="120" cy="96" r="8" fill="{ORANGE}"/>''')


def healthcare():
    ecg = "M64 240H168L186 214L206 262L228 206L244 240H420"
    return wrap("teal", "A medical cross with a heartbeat line, a capsule and a heart", f'''
{shadow(242, 268, 150, 7)}
<rect x="182" y="56" width="120" height="126" rx="28" fill="{NAVY}"/>
<rect x="242" y="56" width="60" height="126" rx="28" fill="{NAVY_D}" opacity=".45"/>
<rect x="226" y="82" width="32" height="74" rx="9" fill="{WHITE}"/>
<rect x="205" y="103" width="74" height="32" rx="9" fill="{WHITE}"/>
<path d="M194 84Q194 66 214 66H240" fill="none" stroke="{WHITE}" stroke-width="3.5" stroke-linecap="round" opacity=".35"/>
<path d="{ecg}" fill="none" stroke="{TEAL}" stroke-width="7" stroke-linecap="round" stroke-linejoin="round"/>
<circle cx="420" cy="240" r="6" fill="{ORANGE}"/>
<path d="M364 102C354 94 346 90 346 84C346 78 352 74 358 76C361 77 363 79 364 81C365 79 367 77 370 76C376 74 382 78 382 84C382 90 374 94 364 102Z" fill="{ORANGE}"/>
<g transform="rotate(-32 372 168)"><rect x="338" y="154" width="68" height="28" rx="14" fill="{WHITE}"/><path d="M372 154H392A14 14 0 0 1 392 182H372Z" fill="{TEAL}"/></g>
<circle cx="112" cy="130" r="12" fill="{NAVY}"/><circle cx="140" cy="158" r="9" fill="{TEAL}"/>
<line x1="112" y1="130" x2="140" y2="158" stroke="{NAVY}" stroke-width="4" stroke-linecap="round" opacity=".5"/>''')


def finance():
    spec = [(148, 56, WHITE), (188, 86, WHITE), (228, 118, NAVY), (268, 150, TEAL)]
    bars, pts = [], []
    for x, h, c in spec:
        bars.append(f'<rect x="{x}" y="{236 - h}" width="30" height="{h}" rx="8" fill="{c}"/>')
        pts.append((x + 15, 236 - h - 20))
    coins = ""
    for i in range(3):
        y = 236 - i * 16
        coins += f'<rect x="338" y="{y - 10}" width="64" height="14" fill="{TEAL_D}"/><ellipse cx="370" cy="{y + 4}" rx="32" ry="9" fill="{TEAL_D}"/>'
    coins += f'<ellipse cx="370" cy="{236 - 2 * 16 - 10}" rx="32" ry="9" fill="{TEAL}"/>'
    line = " ".join(f"{a},{b}" for a, b in pts)
    return wrap("sand", "A bar chart with a rising line and a stack of coins", f'''
{shadow(250, 262, 170, 7)}
<rect x="130" y="236" width="296" height="4" rx="2" fill="#FBDCC6"/>
{''.join(bars)}
<polyline points="{line}" fill="none" stroke="{NAVY_D}" stroke-width="3.5" stroke-linejoin="round" stroke-linecap="round"/>
<circle cx="{pts[-1][0]}" cy="{pts[-1][1]}" r="9" fill="{ORANGE}"/>
{coins}''')


def engineering():
    return wrap("mist", "Two meshing gears with a set square and a hard hat", f'''
{shadow(250, 266, 170, 7)}
<polygon points="{gear(206, 160, 66, 54, 12, 8)}" fill="{NAVY}"/>
<circle cx="206" cy="160" r="40" fill="{NAVY_D}"/>
<circle cx="206" cy="160" r="14" fill="{WHITE}"/>
<polygon points="{gear(296, 110, 44, 35, 9, 14)}" fill="{TEAL}"/>
<circle cx="296" cy="110" r="14" fill="{WHITE}"/>
<path d="M176 114A60 60 0 0 1 220 100" fill="none" stroke="{WHITE}" stroke-width="4" stroke-linecap="round" opacity=".3"/>
<polygon points="76,244 76,168 152,244" fill="{WHITE}" stroke="{NAVY}" stroke-width="5" stroke-linejoin="round"/>
<line x1="76" y1="190" x2="88" y2="190" stroke="{NAVY}" stroke-width="3" stroke-linecap="round"/>
<line x1="76" y1="212" x2="88" y2="212" stroke="{NAVY}" stroke-width="3" stroke-linecap="round"/>
<path d="M338 214A38 38 0 0 1 414 214Z" fill="{TEAL}"/>
<path d="M376 176A38 38 0 0 1 414 214H376Z" fill="{TEAL_D}"/>
<rect x="328" y="212" width="96" height="14" rx="7" fill="{NAVY}"/>
<circle cx="376" cy="190" r="5" fill="{ORANGE}"/>''')


def admin():
    rows = ""
    for i, y in enumerate((120, 152, 184)):
        rows += f'<rect x="196" y="{y}" width="20" height="20" rx="5" fill="{TEAL if i < 2 else WHITE}" stroke="{TEAL}" stroke-width="3"/>'
        rows += f'<rect x="226" y="{y + 3}" width="{64 - i * 10}" height="8" rx="4" fill="{NAVY if i == 0 else SOFT}"/>'
    return wrap("teal", "A clipboard with a checklist, a stack of papers and a pen", f'''
{shadow(250, 268, 150, 7)}
<g transform="rotate(8 340 170)"><rect x="296" y="104" width="100" height="132" rx="8" fill="{WHITE}"/></g>
<rect x="168" y="66" width="136" height="182" rx="16" fill="{NAVY}"/>
<rect x="180" y="88" width="112" height="148" rx="7" fill="{WHITE}"/>
{rows}
<polyline points="201,130 205,134 212,125" fill="none" stroke="{WHITE}" stroke-width="3.5" stroke-linecap="round" stroke-linejoin="round"/>
<polyline points="201,162 205,166 212,157" fill="none" stroke="{WHITE}" stroke-width="3.5" stroke-linecap="round" stroke-linejoin="round"/>
<rect x="218" y="54" width="40" height="28" rx="9" fill="{TEAL}"/>
<g transform="rotate(38 372 230)"><rect x="344" y="224" width="82" height="13" rx="6.5" fill="{NAVY}"/></g>
<circle cx="84" cy="92" r="7" fill="{ORANGE}"/>''')


def manufacturing():
    roof = "".join(f'<polygon points="{140 + i * 56},160 {140 + i * 56},126 {140 + i * 56 + 56},160" fill="{TEAL}"/>' for i in range(4))
    return wrap("sand", "A factory with a chimney, smoke and a conveyor belt", f'''
{shadow(250, 270, 180, 6)}
<rect x="330" y="86" width="30" height="76" rx="3" fill="{NAVY_D}"/>
<rect x="326" y="80" width="38" height="12" rx="3" fill="{TEAL}"/>
<circle cx="350" cy="58" r="12" fill="{WHITE}"/>
<rect x="124" y="160" width="244" height="86" rx="4" fill="{NAVY}"/>
<rect x="246" y="160" width="122" height="86" rx="4" fill="{NAVY_D}" opacity=".35"/>
{roof}
<rect x="150" y="184" width="22" height="20" rx="3" fill="{WHITE}"/>
<rect x="306" y="190" width="40" height="56" rx="4" fill="{TEAL}"/>
<rect x="100" y="246" width="320" height="14" rx="7" fill="{NAVY_D}"/>
<rect x="200" y="222" width="28" height="24" rx="3" fill="{WHITE}"/>
<circle cx="420" cy="120" r="8" fill="{ORANGE}"/>''')


def logistics():
    return wrap("teal", "A delivery truck with parcels and a route to a map pin", f'''
{shadow(240, 264, 170, 6)}
<rect x="70" y="238" width="350" height="8" rx="4" fill="#C9ECE6"/>
<rect x="112" y="124" width="160" height="100" rx="10" fill="{WHITE}"/>
<rect x="112" y="188" width="160" height="14" fill="{TEAL}"/>
<path d="M272 156H328L354 190V224H272Z" fill="{NAVY}"/>
<path d="M284 166H322L340 188H284Z" fill="{TEAL_L}" opacity=".85"/>
<circle cx="156" cy="228" r="18" fill="{NAVY_D}"/><circle cx="156" cy="228" r="8" fill="{WHITE}"/>
<circle cx="318" cy="228" r="18" fill="{NAVY_D}"/><circle cx="318" cy="228" r="8" fill="{WHITE}"/>
<line x1="62" y1="156" x2="96" y2="156" stroke="{NAVY}" stroke-width="4" stroke-linecap="round" opacity=".35"/>
<path d="M150 112Q220 40 380 64" fill="none" stroke="{NAVY}" stroke-width="4" stroke-linecap="round" stroke-dasharray="1 10" opacity=".55"/>
<path d="M388 38C376 38 368 47 368 58C368 72 388 90 388 90C388 90 408 72 408 58C408 47 400 38 388 38Z" fill="{TEAL}"/>
<circle cx="388" cy="58" r="9" fill="{WHITE}"/><circle cx="388" cy="58" r="4" fill="{ORANGE}"/>''')


def telecom():
    arcs = ""
    for i, r in enumerate((34, 56, 78)):
        op = (.9, .6, .35)[i]
        arcs += f'<path d="M{f(242 - r * .7)} {f(88 - r * .7)}A{r} {r} 0 0 1 {f(242 + r * .7)} {f(88 - r * .7)}" fill="none" stroke="{TEAL}" stroke-width="6" stroke-linecap="round" opacity="{op}"/>'
    brace = ""
    for y in (150, 200):
        k = (y - 92) / 154
        brace += f'<line x1="{f(242 - 38 * k)}" y1="{y}" x2="{f(242 + 38 * k)}" y2="{y}" stroke="{NAVY_D}" stroke-width="4" stroke-linecap="round"/>'
    return wrap("mist", "A cell tower sending signals, with a phone", f'''
{shadow(242, 266, 150, 7)}
{arcs}
<line x1="242" y1="92" x2="204" y2="246" stroke="{NAVY}" stroke-width="7" stroke-linecap="round"/>
<line x1="242" y1="92" x2="280" y2="246" stroke="{NAVY}" stroke-width="7" stroke-linecap="round"/>
{brace}
<rect x="190" y="244" width="104" height="14" rx="7" fill="{NAVY_D}"/>
<circle cx="242" cy="88" r="12" fill="{WHITE}" stroke="{NAVY}" stroke-width="5"/>
<circle cx="242" cy="88" r="5" fill="{ORANGE}"/>
<g transform="rotate(8 372 180)"><rect x="344" y="130" width="56" height="100" rx="12" fill="{NAVY}"/><rect x="350" y="142" width="44" height="72" rx="5" fill="{WHITE}"/>
<rect x="358" y="190" width="6" height="14" rx="2" fill="{TEAL}"/><rect x="370" y="180" width="6" height="24" rx="2" fill="{TEAL}"/></g>''')


def retail():
    awning = f'<rect x="120" y="86" width="240" height="34" rx="6" fill="{NAVY}"/>'
    for i in (1, 3, 5):
        awning += f'<rect x="{120 + i * 40}" y="86" width="40" height="34" fill="{WHITE}"/>'
    return wrap("sand", "A storefront with an awning, a shopping bag and a chat bubble", f'''
{shadow(240, 262, 180, 6)}
<rect x="130" y="118" width="220" height="130" rx="6" fill="{WHITE}"/>
{awning}
<rect x="144" y="146" width="64" height="62" rx="5" fill="#E6F6F3" stroke="{NAVY}" stroke-width="4"/>
<rect x="272" y="146" width="64" height="62" rx="5" fill="#E6F6F3" stroke="{NAVY}" stroke-width="4"/>
<rect x="220" y="172" width="44" height="76" rx="4" fill="{TEAL}"/>
<g transform="rotate(-18 412 232)"><path d="M386 210H432L446 232L432 254H386Z" fill="{TEAL}"/><circle cx="400" cy="232" r="5.5" fill="{WHITE}"/></g>
<path d="M398 232Q372 214 370 190" fill="none" stroke="{NAVY}" stroke-width="3" stroke-linecap="round" opacity=".5"/>
<rect x="364" y="52" width="76" height="46" rx="16" fill="{WHITE}"/>
<circle cx="386" cy="75" r="5" fill="{TEAL}"/><circle cx="406" cy="75" r="5" fill="{NAVY}"/>
<polygon points="{star(86, 94, 24, 10)}" fill="{TEAL}"/>
<circle cx="108" cy="66" r="6" fill="{ORANGE}"/>''')


ART = {
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
    for name, fn in ART.items():
        with open(os.path.join(out, name + ".svg"), "w", encoding="utf-8") as fh:
            fh.write(fn())
        print("wrote", name)
