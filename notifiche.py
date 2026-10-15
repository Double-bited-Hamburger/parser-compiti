"""Telefono: cosa c'è di nuovo sul registro (per le notifiche) e il riassunto che mostrano i widget.

Lo chiama l'app Android in sottofondo (WorkManager), nello stesso processo del server: per questo ogni
lavoro sui dati di un profilo si fa con server.BLOCCO preso, come le richieste della pagina.
"""

import json
from datetime import date, datetime, timedelta

import requests

import archivio
import dati
import profili
import server
from archivio import ErroreRegistro

GIORNI = ["lunedì", "martedì", "mercoledì", "giovedì", "venerdì", "sabato", "domenica"]
MESI = ["gen", "feb", "mar", "apr", "mag", "giu", "lug", "ago", "set", "ott", "nov", "dic"]
ORE_DOWNLOAD = range(7, 22)  # di notte non si disturba il registro (né la batteria)
ORE_PROMEMORIA = range(17, 21)  # il promemoria dei compiti per domani arriva nel tardo pomeriggio


def _giorno(iso):
    d = date.fromisoformat(iso[:10])
    return f"{GIORNI[d.weekday()]} {d.day} {MESI[d.month - 1]}"


def _quando(iso, oggi):
    n = (date.fromisoformat(iso[:10]) - oggi).days
    return "oggi" if n == 0 else "domani" if n == 1 else _giorno(iso)


def _prossimo_giorno_di_scuola(elaborati, oggi):
    """Come nella pagina: il primo giorno con lezione dall'orario, altrimenti domani saltando la domenica."""
    lezioni = (elaborati.get("orario") or {}).get("lezioni", [])
    date_ = sorted({l["data"] for l in lezioni if l["data"] > oggi.isoformat() and l["stato"] != "annullata"})
    if date_:
        return date_[0]
    g = oggi + timedelta(days=1)
    return (g + timedelta(days=1) if g.weekday() == 6 else g).isoformat()


def _impronte(elaborati, oggi):
    """Ciò che, se compare per la prima volta, merita una notifica: {categoria: {chiave: testo}}."""
    adesso = oggi.isoformat()
    voti = {f"{v['data']}|{v['materia']}|{v['codice']}|{v['descrizione'][:40]}": f"{v['codice']} in {v['materia']}" for v in elaborati["voti"]}
    verifiche = {
        f"{p['data']}|{p['materia']}|{p['testo'][:60]}": f"{p['materia'] or 'Verifica'} · {_quando(p['data'], oggi)}{' alle ' + p['orario'][:5] if p['orario'] else ''}"
        for p in elaborati["promemoria"] if p["verifica"] and p["data"] >= adesso
    }
    compiti = {c["id"]: f"{c['materia']} per {_quando(c['consegna'], oggi)}" for c in elaborati["compiti"] if c["consegna"] >= adesso}
    variazioni = {
        l["chiave"]: f"{_quando(l['data'], oggi)} {l['inizio']}, {l['materia']}: {l['stato']}"
        for l in (elaborati.get("orario") or {}).get("lezioni", []) if l["variazione"] and l["data"] >= adesso
    }
    return {"voti": voti, "verifiche": verifiche, "compiti": compiti, "variazioni": variazioni}


TITOLI = {
    "voti": ("Nuovo voto", "Nuovi voti"),
    "verifiche": ("Nuova verifica", "Nuove verifiche"),
    "compiti": ("Nuovo compito", "Nuovi compiti"),
    "variazioni": ("Orario cambiato", "Orario cambiato"),
}


def _novita_profilo(profilo, scarica, adesso, piu_profili):
    """Notifiche di un profilo; il profilo deve essere già attivo (dati.attiva) e BLOCCO preso."""
    if scarica:
        try:
            dati.scarica_orario()
        except Exception:
            server.annota_errore()
        try:
            dati.scarica()
        except (ErroreRegistro, requests.RequestException):
            pass  # password cambiata, registro offline o niente rete: si confronta con i dati di prima
    grezzi = dati.carica()
    if not grezzi:
        return []
    oggi = adesso.date()
    elaborati, stato = dati.elabora(grezzi, oggi), dati.leggi_stato()
    file = profili.cartella(profilo["id"]) / "notificati.json"
    vecchio = archivio.leggi(file) or {}
    nuovo = _impronte(elaborati, oggi)
    prefisso = f"{profilo['nome']} · " if piu_profili else ""
    avvisi = []
    if isinstance(vecchio.get("visti"), dict):  # al primo giro si prende nota di tutto senza avvisare
        for categoria, voci in nuovo.items():
            visti = set(vecchio["visti"].get(categoria, []))
            nuove = [testo for chiave, testo in voci.items() if chiave not in visti]
            if nuove:
                uno, molti = TITOLI[categoria]
                avvisi.append({
                    "id": f"{profilo['id']}-{categoria}",
                    "canale": "novita",
                    "titolo": prefisso + (uno if len(nuove) == 1 else f"{molti} ({len(nuove)})"),
                    "testo": "\n".join(nuove[:6]) + (f"\n…e altri {len(nuove) - 6}" if len(nuove) > 6 else ""),
                })
    # I già visti si tengono per un po' anche se spariscono dal registro: così un voto che va e viene non riavvisa.
    prima = vecchio.get("visti") if isinstance(vecchio.get("visti"), dict) else {}
    visti = {k: [*nuovo[k], *[x for x in prima.get(k, []) if x not in nuovo[k]]][:800] for k in nuovo}

    promemoria = vecchio.get("promemoria")
    if adesso.hour in ORE_PROMEMORIA and promemoria != oggi.isoformat():
        giorno = _prossimo_giorno_di_scuola(elaborati, oggi)
        da_fare = [c for c in elaborati["compiti"] if c["consegna"] == giorno and c["id"] not in stato["fatti"]]
        if da_fare:
            quando = _quando(giorno, oggi)
            avvisi.append({
                "id": f"{profilo['id']}-promemoria",
                "canale": "promemoria",
                "titolo": prefisso + (f"Per {quando}: 1 compito da fare" if len(da_fare) == 1 else f"Per {quando}: {len(da_fare)} compiti da fare"),
                "testo": "\n".join(f"{c['materia']} — {c['testo'][:80]}" for c in da_fare[:6]),
            })
        promemoria = oggi.isoformat()
    archivio.scrivi(file, {"visti": visti, "promemoria": promemoria})
    return avvisi


def controlla(scarica=True):
    """Riscarica ogni profilo (se è un'ora decente) e restituisce, in JSON, le notifiche da mostrare."""
    adesso = datetime.now()
    scarica = scarica and adesso.hour in ORE_DOWNLOAD
    elenco = profili.elenco()
    avvisi = []
    for profilo in elenco:
        with server.BLOCCO:
            corrente = dati.PROFILO
            try:
                dati.attiva(profilo, ricorda=False)
                avvisi += _novita_profilo(profilo, scarica, adesso, len(elenco) > 1)
            except Exception:
                server.annota_errore()
            finally:
                dati.attiva(corrente, ricorda=False)
    return json.dumps(avvisi, ensure_ascii=False)


def _adesso(elaborati, adesso):
    """La lezione in corso, o la prossima, per il widget «Adesso». Gli istanti sono in secondi (epoch):
    «cambio» dice al telefono quando ridisegnare il widget, perché la lezione cambia."""
    lezioni = sorted(
        (l for l in (elaborati.get("orario") or {}).get("lezioni", []) if l["stato"] != "annullata"),
        key=lambda l: (l["data"], l["inizio"]),
    )
    oggi, ora = adesso.date().isoformat(), adesso.strftime("%H:%M")
    istante = lambda giorno, hhmm: datetime.combine(date.fromisoformat(giorno), datetime.strptime(hhmm, "%H:%M").time()).timestamp()
    di_oggi = [l for l in lezioni if l["data"] == oggi]
    corrente = next((l for l in di_oggi if l["inizio"] <= ora < l["fine"]), None)
    if corrente:
        dopo = next((l for l in di_oggi if l["inizio"] >= corrente["fine"]), None)
        fine = istante(oggi, corrente["fine"])
        return {"stato": "ora", "materia": corrente["materia"], "orario": corrente["fine"], "istante": fine, "cambio": fine,
                "dopo": f"{dopo['materia']} · {dopo['inizio']}" if dopo else ""}
    prossima = next((l for l in lezioni if (l["data"], l["inizio"]) > (oggi, ora)), None)
    if not prossima:
        return None
    inizio = istante(prossima["data"], prossima["inizio"])
    return {"stato": "prossima", "materia": prossima["materia"], "orario": prossima["inizio"], "istante": inizio, "cambio": inizio,
            "quando": _quando(prossima["data"], adesso.date())}


def widget():
    """Il riassunto per i widget, in JSON: prossima verifica e compiti per il prossimo giorno di scuola."""
    elenco = profili.elenco()
    scelto = profili.trova(profili.ultimo()) if profili.ultimo() else (elenco[0] if elenco else None)
    if not scelto:
        return json.dumps({"vuoto": True, "tema": tema()})
    with server.BLOCCO:
        corrente = dati.PROFILO
        try:
            dati.attiva(scelto, ricorda=False)
            grezzi = dati.carica()
            if not grezzi:
                return json.dumps({"vuoto": True, "nome": scelto["nome"], "tema": tema()})
            oggi = date.today()
            elaborati, fatti = dati.elabora(grezzi, oggi), dati.leggi_stato()["fatti"]
        finally:
            dati.attiva(corrente, ricorda=False)
    verifiche = sorted((p for p in elaborati["promemoria"] if p["verifica"] and p["data"] >= oggi.isoformat()), key=lambda p: p["data"])
    giorno = _prossimo_giorno_di_scuola(elaborati, oggi)
    compiti = [c for c in elaborati["compiti"] if c["consegna"] == giorno]
    prossima = verifiche[0] if verifiche else None
    return json.dumps({
        "nome": elaborati["studente"] or scelto["nome"],
        "verifica": prossima and {
            "giorni": (date.fromisoformat(prossima["data"]) - oggi).days,
            "materia": prossima["materia"] or "Verifica",
            "quando": _giorno(prossima["data"]) + (f" · {prossima['orario'][:5]}" if prossima["orario"] else ""),
            "altre": len(verifiche) - 1,
        },
        "compiti": {
            "quando": _quando(giorno, oggi),
            "da_fare": [{"materia": c["materia"], "testo": c["testo"]} for c in compiti if c["id"] not in fatti],
            "totale": len(compiti),
        },
        "media": elaborati["media_generale"],
        "adesso": _adesso(elaborati, datetime.now()),
        "tema": tema(),
    }, ensure_ascii=False)


def tema():
    """Il tema scelto nell'app (lo salva la pagina in server.PREFERENZE): i widget lo seguono."""
    return (archivio.leggi(server.PREFERENZE) or {}).get("tema", "auto")
