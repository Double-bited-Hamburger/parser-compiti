"""Prove del registro ClasseViva, con risposte finte costruite sui campi documentati dell'API."""

import json
import unittest
from datetime import date
from unittest import mock

import classeviva_adatta
import classeviva_client
import dati
from classeviva_client import ClassevivaClient, ClassevivaError

OGGI = date(2026, 10, 8)

GREZZO = {
    "card": {"ident": "S1234567X", "usrId": 1234567, "firstName": "MARIO", "lastName": "ROSSI", "schName": "ISTITUTO DI PROVA"},
    "materie": [
        {"id": 11, "description": "MATEMATICA", "teachers": [{"teacherId": "T1", "teacherName": "BIANCHI ANNA"}]},
        {"id": 12, "description": "STORIA", "teachers": [{"teacherId": "T2", "teacherName": "VERDI LUCA"}]},
        {"id": 13, "description": "FISICA", "teachers": [{"teacherId": "T1", "teacherName": "BIANCHI ANNA"}]},
    ],
    "periodi": [{"periodCode": "Q1", "periodDesc": "Trimestre", "dateStart": "2026-09-14", "dateEnd": "2026-12-22", "isFinal": False}],
    "voti": [
        {"subjectId": 11, "subjectDesc": "MATEMATICA", "evtDate": "2026-09-20", "decimalValue": 7.5, "displayValue": "7½", "color": "green",
         "canceled": False, "componentDesc": "Scritto/Grafico", "notesForFamily": "Equazioni"},
        {"subjectId": 11, "subjectDesc": "MATEMATICA", "evtDate": "2026-09-28", "decimalValue": None, "displayValue": "6+", "color": "green",
         "canceled": False, "componentDesc": "Orale", "notesForFamily": ""},
        {"subjectId": 12, "subjectDesc": "STORIA", "evtDate": "2026-09-25", "decimalValue": 4, "displayValue": "4", "color": "blue",
         "canceled": False, "componentDesc": "Orale", "notesForFamily": "Non fa media"},
        {"subjectId": 12, "subjectDesc": "STORIA", "evtDate": "2026-09-26", "decimalValue": 9, "displayValue": "9", "color": "green",
         "canceled": True, "componentDesc": "Orale"},
    ],
    "agenda": [
        {"evtId": 1, "evtCode": "AGHW", "evtDatetimeBegin": "2026-10-09T08:00:00+02:00", "evtDatetimeEnd": "2026-10-09T09:00:00+02:00",
         "isFullDay": False, "notes": "Es. 1-5 pag. 40", "authorName": "BIANCHI ANNA", "classDesc": "3A INFORMATICA", "subjectDesc": "MATEMATICA"},
        {"evtId": 2, "evtCode": "AGNT", "evtDatetimeBegin": "2026-10-12T09:00:00+02:00", "evtDatetimeEnd": "2026-10-12T11:00:00+02:00",
         "isFullDay": False, "notes": "Verifica di storia cap. 3", "authorName": "VERDI LUCA", "classDesc": "3A INFORMATICA", "subjectDesc": None},
        {"evtId": 3, "evtCode": "AGNT", "evtDatetimeBegin": "2026-10-20T00:00:00+02:00", "evtDatetimeEnd": "2026-10-20T23:59:59+02:00",
         "isFullDay": True, "notes": "Uscita didattica", "authorName": "BIANCHI ANNA", "classDesc": "3A INFORMATICA", "subjectDesc": ""},
        {"evtId": 4, "evtCode": "AGCR", "evtDatetimeBegin": "2026-10-13T10:00:00+02:00", "notes": "Laboratorio prenotato", "authorName": "X"},
        {"evtId": 5, "evtCode": "AGNT", "evtDatetimeBegin": "2026-10-14T10:00:00+02:00", "notes": "   ", "authorName": "X"},
    ],
    "assenze": [
        {"evtId": 1, "evtCode": "ABA0", "evtDate": "2026-10-06", "evtHPos": None, "isJustified": False, "justifReasonDesc": None},
        {"evtId": 2, "evtCode": "ABR0", "evtDate": "2026-10-07", "evtHPos": 2, "isJustified": True, "justifReasonDesc": "Motivi di salute"},
        {"evtId": 3, "evtCode": "ABU0", "evtDate": "2026-10-07", "evtHPos": 4, "isJustified": True},
        {"evtId": 4, "evtCode": "ABR1", "evtDate": "2026-10-05", "evtHPos": 1, "isJustified": True},
    ],
    "lezioni": [
        {"evtDate": "2026-10-06", "evtCode": "LSF0", "evtHPos": 1, "evtDuration": 2, "subjectDesc": "MATEMATICA", "authorName": "BIANCHI ANNA", "classDesc": "3A INFORMATICA"},
        {"evtDate": "2026-10-07", "evtCode": "LSC0", "evtHPos": 1, "evtDuration": 1, "subjectDesc": "SOSTEGNO", "authorName": "NERI EVA"},
        {"evtDate": "2026-10-07", "evtCode": "LSF0", "evtHPos": 1, "evtDuration": 1, "subjectDesc": "STORIA", "authorName": "VERDI LUCA"},
        {"evtDate": "2026-10-07", "evtCode": "LSF0", "evtHPos": 2, "evtDuration": 3, "subjectDesc": "FISICA", "authorName": "BIANCHI ANNA"},
        {"evtDate": "2026-10-07", "evtCode": "LSF0", "evtHPos": "x", "subjectDesc": "STORIA"},
    ],
    "avviso": None,
}


class Adattatore(unittest.TestCase):
    def setUp(self):
        self.pagina = dati.elabora({"classeviva": json.loads(json.dumps(GREZZO)), "dashboard": {}, "profilo": {}}, OGGI)

    def test_studente_e_classe(self):
        self.assertEqual((self.pagina["studente"], self.pagina["classe"]), ("Rossi Mario", "3A"))
        self.assertEqual(self.pagina["scartate"], {})

    def test_voti_blu_e_annullati_fuori_media(self):
        self.assertEqual([(v["materia"], v["valore"], v["tipo"]) for v in self.pagina["voti"]], [("Matematica", 7.5, "Scritto"), ("Matematica", 6.25, "Orale")])
        self.assertEqual({v["codice"] for v in self.pagina["voti_fuori_media"]}, {"4", "9"})
        self.assertEqual(self.pagina["voti"][0]["descrizione"], "Equazioni")

    def test_compiti_e_verifiche_dall_agenda(self):
        self.assertEqual([(c["materia"], c["testo"], c["consegna"]) for c in self.pagina["compiti"]], [("Matematica", "Es. 1-5 pag. 40", "2026-10-09")])
        promemoria = {p["testo"]: p for p in self.pagina["promemoria"]}
        self.assertEqual(set(promemoria), {"Verifica di storia cap. 3", "Uscita didattica"})  # niente aule prenotate né note vuote
        verifica = promemoria["Verifica di storia cap. 3"]
        self.assertEqual((verifica["verifica"], verifica["orario"], verifica["materia"]), (True, "09:00–11:00", "Storia"))
        self.assertEqual((promemoria["Uscita didattica"]["verifica"], promemoria["Uscita didattica"]["orario"]), (False, ""))

    def test_assenze_e_ore_perse(self):
        assenze = self.pagina["assenze"]
        self.assertEqual((assenze["giorni_assenza"], assenze["ritardi"], assenze["uscite"], assenze["da_giustificare"]), (1, 2, 1, 1))
        per_tipo = {(e["data"], e["tipo"]): e for e in assenze["eventi"]}
        self.assertEqual(per_tipo[("2026-10-06", "assenza")]["ore"], 2)  # la lezione di due ore conta due ore
        self.assertEqual(per_tipo[("2026-10-07", "ritardo")]["ore"], 1)  # entrato alla 2ª: persa la 1ª
        self.assertEqual(per_tipo[("2026-10-07", "uscita")]["ore"], 1)  # uscito alla 4ª: persa la 4ª
        self.assertEqual(per_tipo[("2026-10-05", "ritardo")]["descrizione"], "Ritardo breve")

    def test_compresenza_non_sostituisce_la_lezione(self):
        _, dashboard = classeviva_adatta.converti(GREZZO, OGGI)
        ore = {(r["datGiorno"], r["ora"]): r["materia"] for r in reversed(dashboard["registro"]) if r.get("ora")}
        self.assertEqual(ore[("2026-10-07", 1)], "STORIA")
        self.assertNotIn("Sostegno", self.pagina["materie"])

    def test_dati_malformati_non_bloccano(self):
        rotto = {"card": [], "materie": "x", "voti": [None, {"decimalValue": "dieci"}], "agenda": [{"evtCode": "AGHW"}], "assenze": [{}], "lezioni": [{}]}
        pagina = dati.elabora({"classeviva": rotto, "dashboard": {}, "profilo": {}}, OGGI)
        self.assertEqual(pagina["voti"], [])


class Risposta:
    def __init__(self, stato=200, corpo=None):
        self.status_code, self._corpo = stato, corpo

    def json(self):
        if self._corpo is None:
            raise ValueError
        return self._corpo


class SessioneFinta:
    """Al posto di requests.Session: risponde secondo il percorso e ricorda cosa le è stato chiesto."""

    def __init__(self, risposte):
        self.risposte, self.headers, self.chiamate = risposte, {}, []

    def post(self, url, json=None, **kwargs):
        self.chiamate.append(("POST", url, json, dict(self.headers)))
        return self.risposte["login"](json)

    def get(self, url, **kwargs):
        self.chiamate.append(("GET", url, None, dict(self.headers)))
        percorso = url.split("/students/1234567/")[1]
        for prefisso, risposta in self.risposte.items():
            if percorso.startswith(prefisso):
                return risposta
        return Risposta(404)


def login_giusto(corpo):
    if corpo.get("pass") != "segreta":
        return Risposta(422, {"error": "auth/authentication failed", "info": "credenziali errate"})
    return Risposta(200, {"ident": "S1234567X", "firstName": "MARIO", "lastName": "ROSSI", "token": "tok", "expire": "2026-10-08T12:00:00+02:00"})


class Client(unittest.TestCase):
    def client(self, risposte, password="segreta"):
        sessione = SessioneFinta(risposte)
        with mock.patch.object(classeviva_client.requests, "Session", lambda: sessione):
            return ClassevivaClient("S1234567X", password), sessione

    def test_login_e_intestazioni(self):
        client, sessione = self.client({"login": login_giusto})
        client.login()
        metodo, url, corpo, intestazioni = sessione.chiamate[0]
        self.assertEqual((metodo, url, corpo), ("POST", "https://web.spaggiari.eu/rest/v1/auth/login", {"uid": "S1234567X", "pass": "segreta"}))
        self.assertEqual(intestazioni["Z-Dev-Apikey"], "Tg1NWEwNGIgIC0K")
        self.assertTrue(intestazioni["User-Agent"].startswith("CVVS/"))
        self.assertEqual((client.studente, sessione.headers["Z-Auth-Token"]), ("1234567", "tok"))

    def test_password_sbagliata(self):
        client, _ = self.client({"login": login_giusto}, password="no")
        with self.assertRaisesRegex(ClassevivaError, "Login rifiutato"):
            client.login()

    def test_account_con_piu_studenti(self):
        def login(corpo):
            if "ident" not in corpo:
                return Risposta(200, {"choices": [{"ident": "G7654321Y", "name": "Genitore"}, {"ident": "S1234567X", "name": "MARIO ROSSI"},
                                                  {"ident": "S1111111X", "name": "LUCIA ROSSI"}]})
            return login_giusto({**corpo, "pass": "segreta"})

        client, sessione = self.client({"login": login})
        client.login()
        self.assertEqual(sessione.chiamate[1][2]["ident"], "S1234567X")  # il primo studente, non il genitore
        self.assertIn("MARIO ROSSI", client.avviso)

    def test_scarica(self):
        risposte = {
            "login": login_giusto,
            "card": Risposta(200, {"card": GREZZO["card"]}),
            "subjects": Risposta(200, {"subjects": GREZZO["materie"]}),
            "periods": Risposta(403),  # sezione disattivata dalla scuola
            "grades2": Risposta(404),
            "grades": Risposta(200, {"grades": GREZZO["voti"]}),
            "agenda/all/20260908/20261207": Risposta(200, {"agenda": GREZZO["agenda"]}),
            "absences/details": Risposta(200, {"events": GREZZO["assenze"]}),
            "lessons/20260901/20261008": Risposta(200, {"lessons": GREZZO["lezioni"]}),
        }
        client, _ = self.client(risposte)
        client.login()
        grezzo = client.scarica(OGGI)
        self.assertEqual((len(grezzo["voti"]), len(grezzo["agenda"]), len(grezzo["lezioni"]), grezzo["periodi"]), (4, 5, 5, []))
        self.assertEqual(grezzo["card"]["lastName"], "ROSSI")

    def test_sessione_scaduta_e_troppe_richieste(self):
        for stato, messaggio in ((401, "scaduta"), (429, "troppe richieste")):
            client, _ = self.client({"login": login_giusto, "card": Risposta(stato)})
            client.login()
            with self.assertRaisesRegex(ClassevivaError, messaggio):
                client.scarica(OGGI)

    def test_inizio_anno(self):
        self.assertEqual(classeviva_client.inizio_anno(date(2027, 3, 1)), date(2026, 9, 1))
        self.assertEqual(classeviva_client.inizio_anno(date(2026, 9, 1)), date(2026, 9, 1))


if __name__ == "__main__":
    unittest.main()
