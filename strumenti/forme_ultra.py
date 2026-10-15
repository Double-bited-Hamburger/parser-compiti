"""Genera le forme del tema Ultra (lattina bianca) per la pagina e per i widget Android.

Uso, dalla cartella del progetto: py strumenti/forme_ultra.py web android/app/src/main/res/drawable
Scrive: ultra-ornamento.svg, ultra-artiglio.svg, ultra-trama.svg (web) e
ultra_ornamento_{largo,quadro,striscia}.xml, ultra_artiglio.xml (drawable).
"""
import math
import sys
from pathlib import Path

LATO = 300  # lato della mattonella dell'ornamento


class Caso:
    """Lo stesso generatore pseudo-casuale dello schizzo: risultati sempre uguali."""
    def __init__(self, seme):
        self.s = seme

    def __call__(self):
        self.s = (self.s * 9301 + 49297) % 233280
        return self.s / 233280


def ruota(punti, cx, cy, gradi):
    a = math.radians(gradi)
    c, s = math.cos(a), math.sin(a)
    return [(cx + (x - cx) * c - (y - cy) * s, cy + (x - cx) * s + (y - cy) * c) for x, y in punti]


def f(v):
    return f"{v:.1f}".replace("-0.0", "0.0")


def cubiche(inizio, segmenti):
    """Path da una serie di curve cubiche date con punti assoluti [(c1, c2, fine), ...]."""
    d = f"M{f(inizio[0])},{f(inizio[1])}"
    for c1, c2, fine in segmenti:
        d += f"C{f(c1[0])},{f(c1[1])} {f(c2[0])},{f(c2[1])} {f(fine[0])},{f(fine[1])}"
    return d


def cerchio(x, y, r):
    return f"M{f(x - r)},{f(y)}a{f(r)},{f(r)} 0 1,0 {f(2 * r)},0a{f(r)},{f(r)} 0 1,0 {f(-2 * r)},0"


def spirale(cx, cy, r0, giri, verso, partenza, passi=40):
    """Spirale che si stringe verso il centro (riccio barocco)."""
    pts = []
    for i in range(passi + 1):
        t = i / passi
        a = partenza + verso * t * giri * 2 * math.pi
        r = r0 * (1 - 0.82 * t)
        pts.append((cx + r * math.cos(a), cy + r * math.sin(a)))
    return pts


def bezier(p0, p1, p2, p3, n=24):
    return [tuple((1 - t) ** 3 * a + 3 * (1 - t) ** 2 * t * b + 3 * (1 - t) * t * t * c + t ** 3 * d for a, b, c, d in zip(p0, p1, p2, p3))
            for t in (i / n for i in range(n + 1))]


def direzione(punti, i):
    (x0, y0), (x1, y1) = punti[max(0, i - 1)], punti[min(len(punti) - 1, i + 1)]
    n = math.hypot(x1 - x0, y1 - y0) or 1
    return (x1 - x0) / n, (y1 - y0) / n


def colloca(linee, x, y, scala=1.0, gradi=0.0, specchio=False):
    """Sposta, ruota, ingrandisce (e se serve specchia) un disegno fatto attorno a (0, 0)."""
    a = math.radians(gradi)
    c, s = math.cos(a), math.sin(a)
    return [[(x + scala * ((-px if specchio else px) * c - py * s), y + scala * ((-px if specchio else px) * s + py * c)) for px, py in l] for l in linee]


def arco(r, a0, a1, bombatura, n=18, cx=0.0, cy=0.0):
    return [(cx + (r + bombatura * math.sin(math.pi * t)) * math.cos(a0 + (a1 - a0) * t),
             cy + (r + bombatura * math.sin(math.pi * t)) * math.sin(a0 + (a1 - a0) * t)) for t in (i / n for i in range(n + 1))]


def rosa(R, caso):
    """Rosa vista dall'alto, a contorno: bocciolo a spirale, tre giri di petali sfalsati, bordo esterno a sei petali
    con le pieghe e i bordi arricciati."""
    linee = [spirale(0, 0, R * 0.2, 1.7, 1, caso() * 6, 34)]
    giro = caso() * 6
    for k in range(3):  # petali interni che avvolgono il bocciolo
        a0 = giro + k * 2 * math.pi / 3
        linee.append(arco(R * 0.38, a0, a0 + 2.5, R * 0.08))
    for k in range(5):  # giro di mezzo
        a0 = giro + 0.5 + k * 2 * math.pi / 5
        linee.append(arco(R * 0.62, a0, a0 + 1.5, R * 0.1))
        linee.append(arco(R * 0.55, a0 + 0.35, a0 + 1.1, R * 0.05, 10))  # ombra interna del petalo
    esterno, pieghe = [], []
    for i in range(121):  # bordo esterno: sei petali, con una tacca dove si toccano
        th = giro + 0.2 + i / 120 * 2 * math.pi
        u = (i / 120 * 6) % 1
        r = R * (0.84 + 0.16 * math.sin(math.pi * u) ** 0.6 - (0.06 if u < 0.06 or u > 0.94 else 0)) + (caso() - 0.5) * R * 0.02
        esterno.append((r * math.cos(th), r * math.sin(th)))
    linee.append(esterno)
    for k in range(5):  # petali più esterni, visti da dietro: sbucano tra quelli del bordo
        th = giro + 0.75 + k * 2 * math.pi / 5
        linee.append(arco(R * 1.0, th - 0.42, th + 0.42, R * 0.2, 16))
        linee.append([(R * 1.02 * math.cos(th), R * 1.02 * math.sin(th)), (R * 1.13 * math.cos(th + 0.05), R * 1.13 * math.sin(th + 0.05))])
    for k in range(6):
        th = giro + 0.2 + k * 2 * math.pi / 6
        linee.append([(R * 0.8 * math.cos(th), R * 0.8 * math.sin(th)), (R * 0.66 * math.cos(th + 0.12), R * 0.66 * math.sin(th + 0.12))])  # piega tra due petali
        linee.append(arco(R * 0.86, th + 0.25, th + 0.8, -R * 0.04, 10))  # bordo arricciato
    return linee


def foglia_rosa(L, W):
    """Foglia di rosa: ovale appuntita a bordo seghettato, nervatura centrale e nervature laterali."""
    sopra, sotto = [], []
    n = 16
    for i in range(n + 1):
        t = i / n
        y = W * math.sin(math.pi * t) ** 0.75 * (1 - 0.25 * t)
        dente = W * 0.14 if (i % 2 and 0 < i < n) else 0
        sopra.append((L * t + dente * 0.6, -(y + dente)))
        sotto.append((L * t + dente * 0.6, y + dente))
    linee = [sopra + sotto[::-1], [(0, 0), (L * 0.96, 0)]]
    for t in (0.22, 0.42, 0.62, 0.8):
        h = W * math.sin(math.pi * t) ** 0.75 * (1 - 0.25 * t) * 0.8
        linee.append([(L * t, 0), (L * t + h * 0.7, -h)])
        linee.append([(L * t, 0), (L * t + h * 0.7, h)])
    return linee


def alloro(lunghezza, curva, foglie):
    """Ramo d'alloro, come nelle corone: stelo curvo, foglie lanceolate a coppie sfalsate con nervatura, qualche bacca."""
    stelo = bezier((0, 0), (lunghezza * 0.3, -curva), (lunghezza * 0.7, curva * 0.6), (lunghezza, 0), 40)
    linee = [stelo]
    for i in range(foglie):
        t = 0.06 + 0.88 * i / max(1, foglie - 1)
        j = int(t * (len(stelo) - 1))
        x0, y0 = stelo[j]
        tx, ty = direzione(stelo, j)
        lato = 1 if i % 2 else -1
        ang = math.atan2(ty, tx) + lato * math.radians(38)
        L, W = 20 - 6 * t, 5.2 - 1.2 * t
        dx, dy = math.cos(ang), math.sin(ang)
        nx, ny = -dy, dx
        punta = (x0 + dx * L, y0 + dy * L)
        linee.append(bezier((x0, y0), (x0 + dx * L * 0.3 + nx * W, y0 + dy * L * 0.3 + ny * W), (x0 + dx * L * 0.75 + nx * W * 0.8, y0 + dy * L * 0.75 + ny * W * 0.8), punta, 12)
                     + bezier(punta, (x0 + dx * L * 0.75 - nx * W * 0.8, y0 + dy * L * 0.75 - ny * W * 0.8), (x0 + dx * L * 0.3 - nx * W, y0 + dy * L * 0.3 - ny * W), (x0, y0), 12)[1:])
        linee.append([(x0 + dx * 2, y0 + dy * 2), (x0 + dx * L * 0.85, y0 + dy * L * 0.85)])
        if i % 3 == 1:
            bx, by = x0 - nx * 5 + tx * 3, y0 - ny * 5 + ty * 3
            linee.append([(bx + 2.2 * math.cos(k / 12 * 2 * math.pi), by + 2.2 * math.sin(k / 12 * 2 * math.pi)) for k in range(13)])
    tx, ty = direzione(stelo, len(stelo) - 1)
    x0, y0 = stelo[-1]
    linee.append(bezier((x0, y0), (x0 + tx * 6 - ty * 4, y0 + ty * 6 + tx * 4), (x0 + tx * 14 - ty * 3, y0 + ty * 14 + tx * 3), (x0 + tx * 18, y0 + ty * 18), 10)
                 + bezier((x0 + tx * 18, y0 + ty * 18), (x0 + tx * 14 + ty * 3, y0 + ty * 14 - tx * 3), (x0 + tx * 6 + ty * 4, y0 + ty * 6 - tx * 4), (x0, y0), 10)[1:])
    return linee


# Composizione della mattonella: rose grandi e piccole con le loro foglie, rami d'alloro che riempiono gli spazi.
ROSE = ((72, 78, 36, 10), (222, 192, 33, 70), (92, 236, 23, 150), (252, 52, 21, 200), (168, 98, 16, 30),
        (16, 178, 17, 260), (284, 288, 13, 110), (170, 280, 15, 330), (150, 20, 11, 80), (44, 140, 9, 15))
FOGLIE = ((72, 78, 36, (200, 300, 60, 130)), (222, 192, 33, (100, 230, 340, 20)), (92, 236, 23, (20, 260, 110)),
          (252, 52, 21, (120, 300, 30)), (168, 98, 16, (200, 330)), (16, 178, 17, (330, 80)), (170, 280, 15, (90,)), (284, 288, 13, (200,)))
ALLORI = ((112, 12, 115, 22, 9, 20), (2, 118, 95, -20, 8, -62), (128, 140, 100, 24, 9, 125), (140, 300, 105, -18, 9, -22),
          (272, 114, 78, 16, 7, 98), (38, 300, 72, 14, 6, -82), (196, 52, 70, -16, 6, 160), (230, 252, 64, 14, 6, 15),
          (40, 22, 60, 12, 5, 145), (120, 178, 58, -12, 5, 40), (300, 160, 66, 14, 6, 205))


def elementi():
    """Gli elementi della mattonella (LATO×LATO): ((x, y) del centro, funzione (dx, dy) -> path)."""
    caso = Caso(5)
    forme = []
    pezzi = []
    for x, y, R, gradi in ROSE:
        pezzi.append(((x, y), colloca(rosa(R, caso), x, y, 1, gradi)))
    for x, y, R, angoli in FOGLIE:
        for a in angoli:
            th = math.radians(a)
            pezzi.append(((x, y), colloca(foglia_rosa(R * 0.95, R * 0.36), x + R * 0.82 * math.cos(th), y + R * 0.82 * math.sin(th), 1, a)))
    for x, y, lung, curva, foglie, gradi in ALLORI:
        pezzi.append(((x, y), colloca(alloro(lung, curva, foglie * 2), x, y, 1, gradi)))
    for centro, linee in pezzi:
        forme.append((centro, lambda dx, dy, linee=linee: "".join("M" + "L".join(f"{f(px + dx)},{f(py + dy)}" for px, py in l) for l in linee)))
    return forme


def ornamento(larghezza, altezza):
    """I path che servono a coprire larghezza×altezza, mattonella dopo mattonella (con i pezzi che sbordano), uno per elemento."""
    pezzi = []
    for (cx, cy), disegna in elementi():
        for i in range(-1, math.ceil(larghezza / LATO) + 1):
            for j in range(-1, math.ceil(altezza / LATO) + 1):
                x, y = cx + i * LATO, cy + j * LATO
                if -110 < x < larghezza + 110 and -110 < y < altezza + 110:
                    pezzi.append(disegna(i * LATO, j * LATO))
    return pezzi


def a_blocchi(pezzi, massimo=24000):
    """Android non accetta stringhe oltre 32 KB in una risorsa: il pathData va spezzato in più <path>."""
    blocchi, corrente = [], ""
    for p in pezzi:
        if corrente and len(corrente) + len(p) > massimo:
            blocchi.append(corrente)
            corrente = ""
        corrente += p
    return blocchi + ([corrente] if corrente else [])


STRATI = (("#C3C8CC", 0, 0, 1.0),)  # stampa grigio argento, come sulla lattina


def svg_ornamento():
    # Nella pagina sta dietro al testo: più chiaro che sulla lattina (e nei widget), perché si legga tutto.
    d = "".join(ornamento(LATO, LATO))
    gruppi = f'<path d="{d}" stroke="#D2D6D9"/>'
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{LATO}" height="{LATO}" viewBox="0 0 {LATO} {LATO}">'
            f'<g fill="none" stroke-width="1" stroke-linecap="round" stroke-linejoin="round">{gruppi}</g></svg>')


def vector_ornamento(larghezza, altezza):
    blocchi = a_blocchi(ornamento(larghezza, altezza))
    gruppi = "".join(
        f'    <path android:pathData="{d}" android:strokeColor="{colore}" android:strokeAlpha="{o}" android:strokeWidth="1" android:strokeLineCap="round" android:strokeLineJoin="round" />\n'
        for colore, _, _, o in STRATI for d in blocchi)
    return (f'<?xml version="1.0" encoding="utf-8"?>\n<!-- Generato da forme_ultra.py: rose e alloro a contorno, come l\'ornamento della lattina bianca (tema Ultra). -->\n'
            f'<vector xmlns:android="http://schemas.android.com/apk/res/android" android:width="{larghezza}dp" android:height="{altezza}dp" '
            f'android:viewportWidth="{larghezza}" android:viewportHeight="{altezza}">\n{gruppi}</vector>\n')


def graffi():
    """Tre graffi come sulla lattina: larghi e frastagliati in alto, appuntiti in basso, lunghezze diverse.
    Restituisce [(path, x_min, x_max)] per dare a ognuno la sua sfumatura argentata."""
    risultato = []
    for k, (x0, curva, lunghezza) in enumerate(((30, -10, 0.80), (85, 3, 1.0), (140, 14, 0.88))):
        r = Caso(11 + k * 5)
        altezza = 6 + 186 * lunghezza
        sinistra, destra = [], []
        for i in range(21):
            t = i / 20
            y = 6 + t * (altezza - 6)
            w = 1 + 34 * (1 - t) ** 0.8
            cx = x0 + curva * t * t + (r() - 0.5) * 3
            dente = 4 if i % 2 else 1  # bordi seghettati, come strappati
            sinistra.append((cx - w / 2 - r() * dente, y))
            destra.insert(0, (cx + w / 2 + r() * dente, y + (r() - 0.5) * 3))
        cima = [(sinistra[0][0] + (destra[-1][0] - sinistra[0][0]) * q, 6 - r() * 5) for q in (0.3, 0.65)]  # bordo superiore irregolare
        punti = sinistra + destra + cima[::-1]
        xs = [p[0] for p in punti]
        risultato.append(("M" + "L".join(f"{f(x)},{f(y)}" for x, y in punti) + "Z", min(xs), max(xs)))
    return risultato


ARGENTO = (("0", "#8A9096"), (".3", "#E9EBED"), (".5", "#FFFFFF"), (".72", "#C9CED2"), ("1", "#7E858C"))


def svg_artiglio():
    sfumature, path = "", ""
    for i, (d, x0, x1) in enumerate(graffi()):
        sfumature += (f'<linearGradient id="g{i}" gradientUnits="userSpaceOnUse" x1="{f(x0)}" x2="{f(x1)}" y1="0" y2="0">'
                      + "".join(f'<stop offset="{o}" stop-color="{c}"/>' for o, c in ARGENTO) + "</linearGradient>")
        path += f'<path d="{d}" fill="url(#g{i})"/>'
    return ('<svg xmlns="http://www.w3.org/2000/svg" width="170" height="200" viewBox="0 0 170 200">'
            f'<defs>{sfumature}</defs><g stroke="#111111" stroke-width="3" stroke-linejoin="miter">{path}</g></svg>')


def vector_artiglio():
    path = ""
    for d, x0, x1 in graffi():
        path += (f'    <path android:pathData="{d}" android:strokeColor="#FF111111" android:strokeWidth="3">\n'
                 '        <aapt:attr name="android:fillColor">\n'
                 f'            <gradient android:type="linear" android:startX="{f(x0)}" android:startY="0" android:endX="{f(x1)}" android:endY="0">\n'
                 + "".join(f'                <item android:offset="{o if o != "0" else "0"}" android:color="#FF{c[1:]}" />\n' for o, c in ARGENTO).replace('offset=".', 'offset="0.')
                 + '            </gradient>\n        </aapt:attr>\n    </path>\n')
    return ('<?xml version="1.0" encoding="utf-8"?>\n<!-- Generato da forme_ultra.py: i tre graffi argentati con il bordo nero (tema Ultra). -->\n'
            '<vector xmlns:android="http://schemas.android.com/apk/res/android" xmlns:aapt="http://schemas.android.com/aapt"\n'
            '    android:width="170dp" android:height="200dp" android:viewportWidth="170" android:viewportHeight="200">\n'
            f'{path}</vector>\n')


def svg_trama():
    """Maschera 90×90 per le scritte «graffiate»: piena, con buchini e due graffi sottili (evenodd = buchi)."""
    r = Caso(3)
    d = "M0,0h90v90H0z"
    for _ in range(34):
        x, y, rr = r() * 90, r() * 90, 0.35 + r() * 0.95
        d += cerchio(x, y, rr)
    d += "M0,27l90,3v.8l-90,-3zM0,63l90,-4v.7l-90,4z"
    return f'<svg xmlns="http://www.w3.org/2000/svg" width="90" height="90"><path fill-rule="evenodd" d="{d}"/></svg>'


if __name__ == "__main__":
    web, drawable = Path(sys.argv[1]), Path(sys.argv[2])
    (web / "ultra-ornamento.svg").write_text(svg_ornamento(), encoding="utf-8")
    (web / "ultra-artiglio.svg").write_text(svg_artiglio(), encoding="utf-8")
    (web / "ultra-trama.svg").write_text(svg_trama(), encoding="utf-8")
    for nome, (w, h) in {"largo": (300, 150), "quadro": (200, 200), "striscia": (360, 90)}.items():
        (drawable / f"ultra_ornamento_{nome}.xml").write_text(vector_ornamento(w, h), encoding="utf-8")
    (drawable / "ultra_artiglio.xml").write_text(vector_artiglio(), encoding="utf-8")
    for p in sorted([*web.glob("ultra-*.svg"), *drawable.glob("ultra_*.xml")]):
        print(f"{p.stat().st_size:>7} {p.name}")
