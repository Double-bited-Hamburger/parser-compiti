"""Legge l'orario pubblico di WebUntis in accesso anonimo (sola lettura)."""

import base64
from datetime import timedelta

import requests

TIMEOUT = 30
TIPO_CLASSE = 1


class UntisError(Exception):
    pass


class UntisClient:
    def __init__(self, server, scuola):
        self.base = f"https://{server}/WebUntis"
        self.session = requests.Session()
        # WebUntis riconosce la scuola da questo cookie, come fa la pagina di accesso anonimo.
        codice = base64.b64encode(scuola.encode()).decode()
        self.session.cookies.set("schoolname", f'"_{codice}"', domain=server)
        self.session.get(f"{self.base}/", params={"school": scuola}, timeout=TIMEOUT)

    def _get(self, percorso, **parametri):
        res = self.session.get(f"{self.base}/api/public/timetable/weekly/{percorso}", params=parametri, timeout=TIMEOUT)
        try:
            return res.json()["data"]
        except (ValueError, KeyError, TypeError):
            raise UntisError(f"Risposta non valida da WebUntis (HTTP {res.status_code}).")

    def id_classe(self, nome, giorno):
        configurazione = self._get("pageconfig", type=TIPO_CLASSE, date=giorno.isoformat(), formatId=1)
        classi = configurazione.get("elements") if isinstance(configurazione, dict) else None
        cercato = nome.replace(" ", "").lower()
        for classe in classi if isinstance(classi, list) else []:
            if isinstance(classe, dict) and str(classe.get("name", "")).replace(" ", "").lower() == cercato and "id" in classe:
                return classe["id"]
        raise UntisError(f"Classe «{nome}» non trovata su WebUntis: controlla UNTIS_CLASSE in config.py.")

    def settimana(self, id_classe, giorno):
        """Dati grezzi della settimana che contiene `giorno`."""
        dati = self._get("data", elementType=TIPO_CLASSE, elementId=id_classe, date=giorno.isoformat(), formatId=1)
        try:
            dati = dati["result"]["data"]
            # In una settimana senza lezioni (vacanze) la classe può mancare del tutto.
            return {"lezioni": dati["elementPeriods"].get(str(id_classe)) or [], "elementi": dati.get("elements") or []}
        except (KeyError, TypeError, AttributeError):
            raise UntisError("WebUntis non ha restituito l'orario della classe.")


def cerca_scuole(testo):
    """Scuole WebUntis il cui nome contiene `testo`: [{nome, indirizzo, server, scuola}]."""
    risposta = requests.post(
        "https://mobile.webuntis.com/ms/schoolquery2",
        json={"id": "ricerca", "method": "searchSchool", "params": [{"search": testo}], "jsonrpc": "2.0"},
        timeout=TIMEOUT,
    )
    try:
        scuole = risposta.json()["result"]["schools"]
    except (ValueError, KeyError, TypeError):
        return []  # troppi risultati o nessuno: WebUntis risponde con un errore
    return [
        {"nome": s.get("displayName"), "indirizzo": s.get("address"), "server": s.get("server"), "scuola": s.get("loginName")}
        for s in scuole if isinstance(s, dict) and s.get("server") and s.get("loginName")
    ][:20]


def scarica(server, scuola, classe, oggi, settimane=2):
    """Orario grezzo della settimana corrente e delle successive."""
    client = UntisClient(server, scuola)
    id_classe = client.id_classe(classe, oggi)
    return [client.settimana(id_classe, oggi + timedelta(days=7 * i)) for i in range(settimane)]
