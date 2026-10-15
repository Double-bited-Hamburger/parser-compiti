"""Porta i dati grezzi di Nuvola nella stessa forma di quelli di Argo, così il resto dell'app non cambia.

Su Nuvola:
- i voti arrivano in un unico elenco, con la materia dentro ogni voto;
- i compiti si leggono per giorno di consegna;
- le lezioni sono ore con dentro gli «argomenti»; quelle future di tipo diverso dalla lezione
  ordinaria (per esempio «Compito in classe») sono le verifiche programmate.
"""

import re
from datetime import date, datetime

import parser as estrai

TIPI = {"scritt": "S", "oral": "N", "pratic": "P"}
FRAZIONI = {"½": 0.5, "1/2": 0.5, "+": 0.25, "-": -0.25, "/": 0.5}
LEZIONE_NORMALE = "lezione ordinaria"


def _lista(valore):
    return [v for v in valore if isinstance(v, dict)] if isinstance(valore, list) else []


def _giorno(valore):
    """Data ISO (AAAA-MM-GG) nel fuso locale, da un valore tipo «2026-10-07T00:00:00+02:00»."""
    if not isinstance(valore, str) or not valore.strip():
        return None
    testo = valore.strip()
    try:
        momento = datetime.fromisoformat(testo.replace("Z", "+00:00"))
        return (momento.astimezone() if momento.tzinfo else momento).date().isoformat()
    except ValueError:
        pass
    trovato = re.match(r"(\d{2})[/-](\d{2})[/-](\d{4})", testo)
    return f"{trovato.group(3)}-{trovato.group(2)}-{trovato.group(1)}" if trovato else None


def _ora(valore):
    """«HH:MM» da un orario; stringa vuota se manca."""
    trovato = re.match(r"\s*(\d{1,2}):(\d{2})", valore) if isinstance(valore, str) else None
    return f"{int(trovato.group(1)):02d}:{trovato.group(2)}" if trovato else ""


def _testo(valore):
    if isinstance(valore, list):
        return "\n".join(str(v) for v in valore if isinstance(v, (str, int, float)))
    return str(valore) if isinstance(valore, (str, int, float)) and not isinstance(valore, bool) else ""


def valore_voto(voce):
    """Il voto come numero: prima il valore «matematico» di Nuvola, poi la lettura di «7½», «6+», «7/8».

    Zero per i giudizi senza numero (lettere, «impreparato»…), che non entrano nelle medie.
    """
    matematico = voce.get("valutazioneMatematica")
    if isinstance(matematico, (int, float)) and not isinstance(matematico, bool):
        return float(matematico)
    for testo in (_testo(matematico), _testo(voce.get("valutazione"))):
        testo = testo.strip().replace(",", ".")
        try:
            return float(testo)
        except ValueError:
            pass
        trovato = re.fullmatch(r"(\d{1,2})\s*(½|1/2|\+|-|/)\s*(\d{1,2})?", testo)
        if trovato:
            base, segno, secondo = int(trovato.group(1)), trovato.group(2), trovato.group(3)
            if segno == "/" and secondo:  # «7/8» = tra il 7 e l'8
                return (base + int(secondo)) / 2
            return base + FRAZIONI[segno]
    return 0.0


def _voti(grezzo):
    voti = []
    for voto in _lista(grezzo.get("voti")):
        tipologia = _testo(voto.get("tipologia")).lower()
        voti.append({
            "datGiorno": _giorno(voto.get("data")),
            "desMateria": _testo(voto.get("nomeMateria")),
            "pkMateria": str(voto.get("idMateria")),
            "valore": valore_voto(voto),
            "codCodice": _testo(voto.get("valutazione")),
            "codVotoPratico": next((sigla for parte, sigla in TIPI.items() if parte in tipologia), ""),
            "faMenoMedia": "S" if voto.get("faMedia") is False else "",
            "docente": _testo(voto.get("docente")),
            "descrizioneProva": _testo(voto.get("descrizione")) or _testo(voto.get("nomeObiettivo")),
        })
    return voti


def _ore(dati):
    """Le ore di un giorno che hanno almeno un argomento: [(ora, argomento)], dalla classe e dai suoi gruppi."""
    for classe in _lista(dati.get("lezioni")):
        for ora in _lista(classe.get("ore")):
            for argomento in _lista(ora.get("argomenti")):
                yield ora, argomento


def _registro(grezzo, oggi):
    """Compiti (per giorno di consegna) e ore di lezione svolte, nella forma del registro di classe di Argo."""
    registro = []
    for giorno, dati in sorted((grezzo.get("giorni") or {}).items()):
        if not isinstance(dati, dict):
            continue
        for compito in _lista(dati.get("compiti")):
            testo = _testo(compito.get("descrizioneCompito"))
            if testo:
                registro.append({
                    "datGiorno": _giorno(compito.get("dataAssegnazione")) or giorno,
                    "materia": _testo(compito.get("materia")),
                    "docente": _testo(compito.get("docente")),
                    "compiti": [{"compito": testo, "dataConsegna": _giorno(compito.get("dataConsegna")) or giorno}],
                })
        if giorno <= oggi.isoformat():
            for ora, argomento in _ore(dati):
                registro.append({
                    "datGiorno": giorno,
                    "ora": ora.get("numeroOra"),
                    "materia": _testo(argomento.get("materia")),
                    "docente": _testo(argomento.get("docente")),
                    "compiti": [],
                })
    return registro


def _verifiche(grezzo, oggi):
    """Le lezioni da oggi in poi che non sono ordinarie: è così che su Nuvola si programmano le verifiche."""
    promemoria = []
    for giorno, dati in sorted((grezzo.get("giorni") or {}).items()):
        if not isinstance(dati, dict) or giorno < oggi.isoformat():
            continue
        for ora, argomento in _ore(dati):
            tipo, nome = _testo(argomento.get("tipo")), _testo(argomento.get("nomeArgomento"))
            testo = ": ".join(p for p in (tipo, nome) if p)
            if tipo.lower() == LEZIONE_NORMALE and not estrai._e_verifica(nome):
                continue
            voce = {
                "datGiorno": giorno, "desAnnotazioni": testo, "materia": _testo(argomento.get("materia")), "docente": _testo(argomento.get("docente")),
                "oraInizio": _ora(ora.get("inizioOra")), "oraFine": _ora(ora.get("fineOra")),
            }
            precedente = promemoria[-1] if promemoria else None
            # Una verifica di due ore compare in due ore consecutive: diventa una voce sola.
            if precedente and all(precedente[k] == voce[k] for k in ("datGiorno", "desAnnotazioni", "materia")) and precedente["oraFine"] == voce["oraInizio"]:
                precedente["oraFine"] = voce["oraFine"]
            else:
                promemoria.append(voce)
    return promemoria


def _eventi(grezzo):
    """Eventi e avvisi della classe e dell'alunno (circolari, incontri…)."""
    eventi = []
    for chiave in ("eventi_classe", "eventi_alunno"):
        for evento in _lista(grezzo.get(chiave)):
            eventi.append({
                "datGiorno": _giorno(evento.get("dataInizio")),
                "desAnnotazioni": _testo(evento.get("nome")) or _testo(evento.get("descrizione")),
                "materia": "",
                "docente": _testo(evento.get("docente")),
                "oraInizio": _ora(evento.get("oraInizio")),
                "oraFine": _ora(evento.get("oraFine")),
            })
    return eventi


def _ora_lezione(valore, dati):
    """L'ora di lezione (1, 2, 3…) di un ingresso o di un'uscita, da un numero o da un orario «HH:MM»."""
    if isinstance(valore, int) and not isinstance(valore, bool):
        return valore
    orario = _ora(valore)
    if not orario or not isinstance(dati, dict):
        return None
    for classe in _lista(dati.get("lezioni")):
        for ora in _lista(classe.get("ore")):
            if _ora(ora.get("inizioOra")) <= orario < _ora(ora.get("fineOra")) and isinstance(ora.get("numeroOra"), int):
                return ora["numeroOra"]
    return None


def _appello(grezzo):
    appello = []
    for assenza in _lista(grezzo.get("assenze")):
        tipo, giorno = _testo(assenza.get("tipo")).lower(), _giorno(assenza.get("data"))
        codice = "I" if "ritard" in tipo or "ingress" in tipo or "entrat" in tipo else "U" if "uscit" in tipo else "A"
        ora = _ora_lezione(assenza.get("ora"), (grezzo.get("giorni") or {}).get(giorno))
        giustificata = assenza.get("giustificata") is True
        appello.append({
            "data": giorno,
            "codEvento": codice,
            "descrizione": _testo(assenza.get("tipo")).capitalize(),
            # Stessa dicitura delle note di Argo, così le ore perse si calcolano allo stesso modo.
            "nota": f"{'Ingresso' if codice == 'I' else 'Uscita'} in {ora}^ ora" if ora and codice != "A" else _testo(assenza.get("tipoAssenza")),
            "giustificata": "S" if giustificata else "N",
            "daGiustificare": assenza.get("giustificabile") is not False and not giustificata,
        })
    return appello


def converti(grezzo, oggi=None):
    """(profilo, dashboard) nella forma prodotta dal client Argo."""
    oggi = oggi or date.today()
    voti, registro = _voti(grezzo), _registro(grezzo, oggi)
    materie = {_testo(m.get("materia")) for m in _lista(grezzo.get("materie"))} | {v["desMateria"] for v in voti} | {r["materia"] for r in registro}
    alunno = grezzo.get("alunno") if isinstance(grezzo.get("alunno"), dict) else {}
    profilo = {
        "alunno": {"nominativo": " ".join(p for p in (_testo(alunno.get("cognome")), _testo(alunno.get("nome"))) if p)},
        "scheda": {"classe": {"desDenominazione": _testo(alunno.get("classe")), "desSezione": ""}},
    }
    dashboard = {
        "listaMaterie": [{"abbreviazione": m, "materia": m, "faMedia": True} for m in sorted(materie) if m],
        "listaDocentiClasse": [],
        "listaPeriodi": [],
        "voti": voti,
        "registro": registro,
        "promemoria": _verifiche(grezzo, oggi) + _eventi(grezzo),
        "appello": _appello(grezzo),
    }
    return profilo, dashboard
