"""PDF stampabile di una settimana: orario con variazioni, verifiche e compiti."""

import io
from datetime import date
from pathlib import Path
from xml.sax.saxutils import escape

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

GIORNI = ["Lunedì", "Martedì", "Mercoledì", "Giovedì", "Venerdì", "Sabato", "Domenica"]
MESI = ["gennaio", "febbraio", "marzo", "aprile", "maggio", "giugno", "luglio", "agosto", "settembre", "ottobre", "novembre", "dicembre"]

INK = colors.HexColor("#1c2330")
MUTED = colors.HexColor("#5d6678")
ACCENT = colors.HexColor("#2a78d6")
LINE = colors.HexColor("#cfd5df")
HEAD = colors.HexColor("#eef3fe")
VARIAZIONE = colors.HexColor("#fff1d6")
ANNULLATA = colors.HexColor("#fde4e6")
MARGINE = 12 * mm


def _font():
    """Segoe UI se disponibile (Windows), altrimenti i font standard del PDF."""
    cartella = Path("C:/Windows/Fonts")
    try:
        pdfmetrics.registerFont(TTFont("UI", str(cartella / "segoeui.ttf")))
        pdfmetrics.registerFont(TTFont("UI-B", str(cartella / "segoeuib.ttf")))
        pdfmetrics.registerFontFamily("UI", normal="UI", bold="UI-B", italic="UI", boldItalic="UI-B")
        return "UI", "UI-B"
    except Exception:
        return "Helvetica", "Helvetica-Bold"


def _giorno(iso):
    return date.fromisoformat(iso[:10])


def _cella(lezioni, stile):
    parti = []
    for l in lezioni:
        annullata = l["stato"] == "annullata"
        materia = f"<b>{escape(l['materia'])}</b>"
        righe = [f"<strike>{materia}</strike>" if annullata else materia]
        dove = " · ".join(filter(None, [", ".join(l["docenti"]), ", ".join(l["aule"])]))
        if dove:
            righe.append(escape(dove))
        if l["variazione"]:
            previsto = ", ".join(l["docenti_previsti"] + l["aule_previste"])
            dettagli = " – ".join(filter(None, [l["stato"].upper(), f"al posto di {previsto}" if previsto else "", l["nota"]]))
            righe.append(f"<b>{escape(dettagli)}</b>")
        parti.append("<br/>".join(righe))
    return Paragraph("<br/><br/>".join(parti), stile)


def genera(pagina, indice=0):
    """`pagina`: l'output di dati.elabora. Restituisce i byte del PDF della settimana `indice`."""
    normale, grassetto = _font()
    orario = pagina.get("orario") or {"settimane": [], "lezioni": []}
    if not orario["settimane"]:
        raise ValueError("Orario non disponibile: aggiorna i dati.")
    settimana = orario["settimane"][min(indice, len(orario["settimane"]) - 1)]
    inizio, fine = _giorno(settimana["inizio"]), _giorno(settimana["fine"])

    testo = ParagraphStyle("testo", fontName=normale, fontSize=8, leading=10.5, textColor=INK)
    piccolo = ParagraphStyle("piccolo", parent=testo, textColor=MUTED)
    testa = ParagraphStyle("testa", parent=testo, fontName=grassetto, fontSize=9, leading=12)
    titolo = ParagraphStyle("titolo", parent=testo, fontName=grassetto, fontSize=17, leading=21)
    sezione = ParagraphStyle("sezione", parent=testo, fontName=grassetto, fontSize=12, leading=16, textColor=ACCENT, spaceBefore=10, spaceAfter=5)

    larghezza = landscape(A4)[0] - 2 * MARGINE
    giorni = settimana["giorni"]
    col_ora = 17 * mm
    col = (larghezza - col_ora) / len(giorni)

    # Griglia dell'orario
    righe = [[""] + [Paragraph(f"{GIORNI[_giorno(g).weekday()]} {_giorno(g).day}", testa) for g in giorni]]
    stili = [
        ("GRID", (0, 0), (-1, -1), 0.5, LINE),
        ("BACKGROUND", (0, 0), (-1, 0), HEAD),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 4), ("RIGHTPADDING", (0, 0), (-1, -1), 4),
        ("TOPPADDING", (0, 0), (-1, -1), 3), ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]
    for r, (ora_inizio, ora_fine) in enumerate(settimana["fasce"], start=1):
        riga = [Paragraph(f"<b>{ora_inizio}</b><br/>{ora_fine}", piccolo)]
        for c, g in enumerate(giorni, start=1):
            lezioni = [l for l in orario["lezioni"] if l["data"] == g and l["inizio"] == ora_inizio]
            riga.append(_cella(lezioni, testo) if lezioni else "")
            if any(l["stato"] == "annullata" for l in lezioni):
                stili.append(("BACKGROUND", (c, r), (c, r), ANNULLATA))
            elif any(l["variazione"] for l in lezioni):
                stili.append(("BACKGROUND", (c, r), (c, r), VARIAZIONE))
        righe.append(riga)
    griglia = Table(righe, colWidths=[col_ora] + [col] * len(giorni), repeatRows=1)
    griglia.setStyle(TableStyle(stili))

    # Verifiche e compiti, giorno per giorno
    impegni = [[Paragraph("Giorno", testa), Paragraph("Verifiche e promemoria", testa), Paragraph("Compiti da consegnare", testa)]]
    fatti = set((pagina.get("stato") or {}).get("fatti", {}))
    giorno_corrente = inizio
    while giorno_corrente <= max(fine, inizio):
        iso = giorno_corrente.isoformat()
        promemoria = [p for p in pagina["promemoria"] if p["data"] == iso]
        compiti = [c for c in pagina["compiti"] if c["consegna"] == iso]
        if promemoria or compiti:
            impegni.append([
                Paragraph(f"<b>{GIORNI[giorno_corrente.weekday()]} {giorno_corrente.day}</b>", testo),
                Paragraph("<br/>".join(
                    f"{'<b>Verifica</b> – ' if p['verifica'] else ''}{escape(p['orario'])} <b>{escape(p['materia'])}</b>: {escape(p['testo'])}" for p in promemoria
                ) or "–", testo),
                Paragraph("<br/>".join(
                    f"{'[x]' if c['id'] in fatti else '[  ]'} <b>{escape(c['materia'])}</b>: {escape(c['testo'])}" for c in compiti
                ) or "–", testo),
            ])
        giorno_corrente = date.fromordinal(giorno_corrente.toordinal() + 1)
    tabella_impegni = Table(impegni, colWidths=[26 * mm, (larghezza - 26 * mm) * 0.45, (larghezza - 26 * mm) * 0.55], repeatRows=1)
    tabella_impegni.setStyle(TableStyle([
        ("GRID", (0, 0), (-1, -1), 0.5, LINE), ("BACKGROUND", (0, 0), (-1, 0), HEAD), ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 5), ("RIGHTPADDING", (0, 0), (-1, -1), 5),
        ("TOPPADDING", (0, 0), (-1, -1), 4), ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
    ]))

    periodo = f"dal {inizio.day}{'' if inizio.month == fine.month else ' ' + MESI[inizio.month - 1]} al {fine.day} {MESI[fine.month - 1]} {fine.year}"
    variazioni = sum(l["variazione"] for l in orario["lezioni"] if settimana["inizio"] <= l["data"] <= settimana["fine"])
    storia = [
        Paragraph(f"Settimana {periodo}", titolo),
        Paragraph(
            f"{escape(pagina.get('studente') or '')}{' · classe ' + escape(pagina['classe']) if pagina.get('classe') else ''} · "
            f"orario aggiornato il {_giorno(orario['scaricato']).strftime('%d/%m/%Y')} alle {orario['scaricato'][11:16]} · "
            f"{variazioni} {'variazione' if variazioni == 1 else 'variazioni'} (celle colorate)", piccolo),
        Spacer(1, 6),
        griglia,
        Paragraph("Verifiche e compiti della settimana", sezione),
        tabella_impegni if len(impegni) > 1 else Paragraph("Nessuna verifica e nessun compito segnati per questa settimana.", testo),
    ]

    def piede(canvas, doc):
        canvas.saveState()
        canvas.setFont(normale, 7.5)
        canvas.setFillColor(MUTED)
        canvas.drawRightString(landscape(A4)[0] - MARGINE, 6 * mm, f"Pagina {doc.page}")
        canvas.restoreState()

    buffer = io.BytesIO()
    SimpleDocTemplate(
        buffer, pagesize=landscape(A4), leftMargin=MARGINE, rightMargin=MARGINE, topMargin=10 * mm, bottomMargin=11 * mm,
        title=f"Settimana {periodo}",
    ).build(storia, onFirstPage=piede, onLaterPages=piede)
    return buffer.getvalue()
