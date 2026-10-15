"""Trasforma la dashboard grezza di Argo in verifiche, compiti, voti e assenze."""

import hashlib
import re
from dataclasses import dataclass
from datetime import date, datetime

import config


@dataclass
class Promemoria:
    data: date
    orario: str
    materia: str
    docente: str
    testo: str
    verifica: bool


@dataclass
class Compito:
    consegna: date
    assegnato: date | None
    materia: str
    docente: str
    testo: str

    @property
    def id(self):
        """Identificativo stabile tra un download e l'altro: serve per ricordare le spunte."""
        chiave = f"{self.consegna}|{self.materia}|{self.testo}"
        return hashlib.sha1(chiave.encode()).hexdigest()[:12]


@dataclass
class Voto:
    data: date
    materia: str
    valore: float
    codice: str
    tipo: str
    descrizione: str
    docente: str


@dataclass
class Lezione:
    data: date
    ora: int
    materia: str
    docente: str


@dataclass
class Assenza:
    data: date
    tipo: str  # "assenza", "ritardo" oppure "uscita"
    descrizione: str
    nota: str
    ora: int | None  # ora di lezione di ingresso/uscita, se indicata nella nota
    giustificata: bool
    da_giustificare: bool


TIPI_VOTO = {"S": "Scritto", "N": "Orale", "P": "Pratico"}
TIPI_ASSENZA = {"A": "assenza", "I": "ritardo", "U": "uscita"}

# Una voce del registro con un formato inatteso viene saltata, senza fermare tutto il resto.
ERRORI_DATI = (TypeError, ValueError, KeyError, AttributeError, IndexError)


def voci(dashboard, chiave):
    """Le voci valide (oggetti non eliminati) di una lista della dashboard."""
    lista = dashboard.get(chiave)
    if not isinstance(lista, list):
        return []
    return [v for v in lista if isinstance(v, dict) and v.get("operazione") != "D"]


def _data(value):
    if not value:
        return None
    text = str(value).strip()[:10]
    for fmt in ("%Y-%m-%d", "%d/%m/%Y"):
        try:
            return datetime.strptime(text, fmt).date()
        except ValueError:
            pass
    return None


def _pulisci(text):
    if isinstance(text, bool) or not isinstance(text, (str, int, float)):
        return ""
    return re.sub(r"\s+", " ", str(text)).strip()


def _docente(text):
    return _pulisci(re.sub(r"\(?\bProf\.?(ssa)?\b\.?", "", _pulisci(text), flags=re.I).strip("() "))


def _e_verifica(testo):
    for parola in config.PAROLE_VERIFICA:
        fine = "" if parola.endswith("*") else r"\b"
        if re.search(rf"\b{re.escape(parola.rstrip('*'))}{fine}", testo, flags=re.I):
            return True
    return False


def _orario(item):
    inizio, fine = _pulisci(item.get("oraInizio")), _pulisci(item.get("oraFine"))
    if not inizio or inizio == fine == "00:00":
        return ""
    return f"{inizio}–{fine}" if fine and fine != inizio else inizio


def _nome_materia(nome):
    nome = _pulisci(nome)
    return config.NOMI_MATERIE.get(nome.upper()) or nome.capitalize()


def _parole(testo):
    return set(re.findall(r"[a-zà-ù]{4,}", testo.lower()))


def materie_per_sigla(dashboard):
    """{sigla: nome della materia} dall'elenco materie di Argo."""
    return {
        m["abbreviazione"]: m["materia"]
        for m in voci(dashboard, "listaMaterie")
        if isinstance(m.get("abbreviazione"), str) and isinstance(m.get("materia"), str) and m["materia"].strip()
    }


def _materia_promemoria(item, dashboard):
    """Il promemoria non ha la materia: si parte dalle materie del docente e,
    se sono più di una, si sceglie quella nominata nel testo."""
    materie = materie_per_sigla(dashboard)
    candidate = []
    for prof in voci(dashboard, "listaDocentiClasse"):
        if prof.get("pk") and prof.get("pk") == item.get("pkDocente") and isinstance(prof.get("materie"), list):
            candidate = [materie[a] for a in prof["materie"] if isinstance(a, str) and a in materie]
    if len(candidate) == 1:
        return _nome_materia(candidate[0])

    testo = _pulisci(item.get("desAnnotazioni")).lower()
    for alias, materia in config.ALIAS_MATERIE.items():
        if re.search(rf"\b{re.escape(alias.lower())}\b", testo):
            return _nome_materia(materia)
    parole = _parole(testo)
    punteggi = {m: len(parole & _parole(f"{m} {_nome_materia(m)}")) for m in candidate or materie.values()}
    migliore = max(punteggi.values(), default=0)
    migliori = [m for m, punti in punteggi.items() if punti == migliore]
    if migliore and len(migliori) == 1:
        return _nome_materia(migliori[0])
    return " / ".join(_nome_materia(m) for m in candidate)


def _scarta(scartate, cosa):
    if scartate is not None:
        scartate.append(cosa)


def promemoria(dashboard, da=None, scartate=None):
    """Promemoria dal giorno `da` in poi (tutto l'anno se `da` è None)."""
    risultati = []
    for item in voci(dashboard, "promemoria"):
        try:
            giorno = _data(item.get("datGiorno"))
            testo = _pulisci(item.get("desAnnotazioni"))
            if not giorno or not testo or (da and giorno < da):
                continue
            risultati.append(
                Promemoria(
                    data=giorno,
                    orario=_orario(item),
                    # Argo non indica la materia e va dedotta; Nuvola la fornisce già.
                    materia=_nome_materia(item["materia"]) if _pulisci(item.get("materia")) else _materia_promemoria(item, dashboard),
                    docente=_docente(item.get("docente")),
                    testo=testo,
                    verifica=_e_verifica(testo),
                )
            )
        except ERRORI_DATI:
            _scarta(scartate, "promemoria")
    return sorted(risultati, key=lambda p: (p.data, p.orario))


def compiti(dashboard, da=None, scartate=None):
    """Compiti con consegna dal giorno `da` in poi (tutto l'anno se `da` è None)."""
    risultati = {}
    for lezione in voci(dashboard, "registro"):
        try:
            for compito in lezione.get("compiti") or []:
                consegna = _data(compito.get("dataConsegna"))
                testo = _pulisci(compito.get("compito"))
                if not consegna or not testo or (da and consegna < da):
                    continue
                materia = _nome_materia(lezione.get("materia"))
                risultati[(consegna, materia, testo)] = Compito(
                    consegna=consegna,
                    assegnato=_data(lezione.get("datGiorno")),
                    materia=materia,
                    docente=_docente(lezione.get("docente")),
                    testo=testo,
                )
        except ERRORI_DATI:
            _scarta(scartate, "compito")
    return sorted(risultati.values(), key=lambda c: (c.consegna, c.materia))


def voti(dashboard, scartate=None, in_media=True):
    """I voti numerici che fanno media; con in_media=False gli altri (giudizi senza numero, voti che non fanno media)."""
    risultati = []
    for item in voci(dashboard, "voti"):
        try:
            giorno = _data(item.get("datGiorno"))
            valore = item.get("valore") or 0
            if isinstance(valore, bool) or not isinstance(valore, (int, float)) or valore > 10:
                raise ValueError("valore del voto non valido")
            conta = valore > 0 and item.get("faMenoMedia") != "S" and item.get("numMedia") != 0
            if not giorno or conta != in_media:
                continue
            materia = _nome_materia(item.get("desMateria"))
            if not materia:
                raise ValueError("voto senza materia")
            risultati.append(
                Voto(
                    data=giorno,
                    materia=materia,
                    valore=float(valore),
                    codice=_pulisci(item.get("codCodice")) or f"{valore:g}",
                    tipo=TIPI_VOTO.get(_pulisci(item.get("codVotoPratico")), ""),
                    descrizione=_pulisci(item.get("descrizioneProva")) or _pulisci(item.get("desCommento")),
                    docente=_docente(item.get("docente")),
                )
            )
        except ERRORI_DATI:
            if in_media:  # ogni voce malformata si conta una volta sola
                _scarta(scartate, "voto")
    return sorted(risultati, key=lambda v: v.data)


def lezioni(dashboard):
    """Le ore di lezione firmate sul registro di classe."""
    risultati = {}
    for item in voci(dashboard, "registro"):
        giorno, ora = _data(item.get("datGiorno")), item.get("ora")
        if not giorno or isinstance(ora, bool) or not isinstance(ora, int) or not 0 < ora < 20:
            continue
        # Due docenti in compresenza firmano la stessa ora: conta una volta sola.
        risultati.setdefault(
            (giorno, ora),
            Lezione(giorno, ora, _nome_materia(item.get("materia")), _docente(item.get("docente"))),
        )
    return sorted(risultati.values(), key=lambda l: (l.data, l.ora))


def assenze(dashboard, scartate=None):
    risultati = []
    for item in voci(dashboard, "appello"):
        try:
            giorno = _data(item.get("data") or item.get("datEvento"))
            if not giorno:
                continue
            descrizione = _pulisci(item.get("descrizione"))
            nota = _pulisci(item.get("nota"))
            tipo = TIPI_ASSENZA.get(_pulisci(item.get("codEvento")))
            if not tipo:
                tipo = next((t for t in ("ritardo", "uscita") if t in descrizione.lower()), "assenza")
            ora = re.search(r"(\d+)\s*\^?\s*ora\b", nota, flags=re.I)
            risultati.append(
                Assenza(
                    data=giorno,
                    tipo=tipo,
                    descrizione=descrizione,
                    nota=nota,
                    ora=int(ora.group(1)) if ora and tipo != "assenza" else None,
                    giustificata=item.get("giustificata") == "S",
                    da_giustificare=bool(item.get("daGiustificare")) and item.get("giustificata") != "S",
                )
            )
        except ERRORI_DATI:
            _scarta(scartate, "assenza")
    return sorted(risultati, key=lambda a: a.data)
