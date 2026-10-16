"""Client per il registro ClasseViva (Spaggiari), tramite l'API usata dall'app ufficiale per studenti e famiglie (sola lettura).

Sperimentale: l'API non è documentata da Spaggiari. Percorsi e campi vengono da progetti open source che la usano
(aiocvv, Classeviva-Official-Endpoints): se qualcosa non torna con il tuo account, segnalalo nelle issue.
"""

import re
from datetime import date, timedelta

import requests

from archivio import ErroreRegistro

API = "https://web.spaggiari.eu/rest/v1"
TIMEOUT = 30
# Le stesse intestazioni dell'app ClasseViva per Android: senza, l'API rifiuta le richieste.
INTESTAZIONI = {"User-Agent": "CVVS/std/4.1.7 Android/10", "Z-Dev-Apikey": "Tg1NWEwNGIgIC0K", "Content-Type": "application/json"}

# L'agenda (verifiche, compiti, annotazioni) si legge da un mese fa a due mesi avanti.
GIORNI_INDIETRO = 30
GIORNI_AVANTI = 60


class ClassevivaError(ErroreRegistro):
    pass


def _giorno(giorno):
    return giorno.strftime("%Y%m%d")


def inizio_anno(oggi):
    """Il 1° settembre dell'anno scolastico in corso."""
    return date(oggi.year if oggi.month >= 9 else oggi.year - 1, 9, 1)


def _elenco(risposta, chiave):
    valore = risposta.get(chiave) if isinstance(risposta, dict) else None
    return [v for v in valore if isinstance(v, dict)] if isinstance(valore, list) else []


class ClassevivaClient:
    def __init__(self, utente, password, scelta=""):
        self.utente = utente
        self.password = password
        self.scelta = scelta  # lo studente scelto nel profilo (ident), per gli account con più studenti
        self.session = requests.Session()
        self.session.headers.update(INTESTAZIONI)
        self.studente = None
        self.scelte = []  # gli studenti collegati all'account, se più d'uno: [{"ident", "name"}]
        self.avviso = None  # per esempio: account di un genitore con più figli

    def _accedi(self, identita=None):
        corpo = {"uid": self.utente, "pass": self.password, **({"ident": identita} if identita else {})}
        risposta = self.session.post(f"{API}/auth/login", json=corpo, timeout=TIMEOUT, allow_redirects=False)
        if risposta.status_code in (401, 422):
            raise ClassevivaError("Login rifiutato: controlla utente e password di ClasseViva.")
        try:
            dati = risposta.json()
        except ValueError:
            dati = None
        if risposta.status_code != 200 or not isinstance(dati, dict):
            raise ClassevivaError(f"ClasseViva non ha accettato l'accesso (risposta {risposta.status_code}).")
        return dati

    def login(self):
        dati = self._accedi()
        scelte = [s for s in dati.get("choices") or [] if isinstance(s, dict) and isinstance(s.get("ident"), str)]
        if not dati.get("token") and scelte:
            # Un account collegato a più studenti (per esempio un genitore con due figli): si usa quello scelto nel profilo,
            # altrimenti il primo. Tra le scelte può esserci anche il genitore stesso, che non ha voti: si tengono gli studenti.
            studenti = [s for s in scelte if s["ident"].upper().startswith("S")] or scelte
            self.scelte = [{"ident": s["ident"], "name": s["name"] if isinstance(s.get("name"), str) else ""} for s in studenti] if len(studenti) > 1 else []
            scelta = next((s for s in studenti if s["ident"] == self.scelta), None)
            if scelta is None:
                scelta = studenti[0]
                nome = scelta.get("name") or scelta["ident"]
                if self.scelta:
                    self.avviso = f"Lo studente scelto nel profilo non è più collegato all'account: viene mostrato {nome}."
                elif len(studenti) > 1:
                    self.avviso = f"L'account ha più studenti: viene mostrato {nome}. Puoi sceglierne un altro modificando il profilo."
            dati = self._accedi(scelta["ident"])
        token, identita = dati.get("token"), dati.get("ident")
        if not isinstance(token, str) or not token or not isinstance(identita, str):
            raise ClassevivaError("Accesso riuscito ma ClasseViva non ha rilasciato il token.")
        numero = re.sub(r"\D", "", identita)
        if not numero:
            raise ClassevivaError("ClasseViva non ha indicato lo studente di questo account.")
        self.session.headers["Z-Auth-Token"] = token
        self.studente = numero

    def _api(self, percorso):
        """Una chiamata all'API; None se la sezione non esiste o la scuola l'ha disattivata."""
        risposta = self.session.get(f"{API}/students/{self.studente}/{percorso}", timeout=TIMEOUT, allow_redirects=False)
        if risposta.status_code == 401:
            raise ClassevivaError("Sessione di ClasseViva scaduta: riprova.")
        if risposta.status_code == 429:
            raise ClassevivaError("ClasseViva ha ricevuto troppe richieste: riprova tra qualche minuto.")
        if risposta.status_code != 200:
            return None  # 403 = sezione disattivata dalla scuola, 404 = sezione inesistente
        try:
            return risposta.json()
        except ValueError:
            return None

    def scarica(self, oggi=None):
        """Tutti i dati grezzi, così come li restituisce ClasseViva (poche chiamate: l'API ha limiti stretti)."""
        oggi = oggi or date.today()
        agenda = f"agenda/all/{_giorno(oggi - timedelta(days=GIORNI_INDIETRO))}/{_giorno(oggi + timedelta(days=GIORNI_AVANTI))}"
        voti = self._api("grades2")
        if voti is None:
            voti = self._api("grades")
        scheda = self._api("card")
        return {
            "card": scheda["card"] if isinstance(scheda, dict) and isinstance(scheda.get("card"), dict) else {},
            "materie": _elenco(self._api("subjects"), "subjects"),
            "periodi": _elenco(self._api("periods"), "periods"),
            "voti": _elenco(voti, "grades"),
            "agenda": _elenco(self._api(agenda), "agenda"),
            "assenze": _elenco(self._api("absences/details"), "events"),
            "lezioni": _elenco(self._api(f"lessons/{_giorno(inizio_anno(oggi))}/{_giorno(oggi)}"), "lessons"),
            "avviso": self.avviso,
        }
