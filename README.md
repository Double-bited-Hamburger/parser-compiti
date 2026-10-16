# Parser Compiti

**Versione 0.2 beta.** Un'app per studenti che legge il registro elettronico della scuola e l'orario WebUntis, e li mette insieme in un'unica pagina:
- agenda delle verifiche;
- compiti da spuntare;
- orario con supplenze e variazioni;
- voti con grafici e simulatore;
- carico di lavoro della settimana;
- assenze e ore perse rispetto al limite annuale.

Gira sul PC (Windows, ma anche Linux e macOS) e come app Android. Le due copie si possono sincronizzare in Wi‑Fi.

## Scarica

| | |
| --- | --- |
| 📱 **Android** | **[Scarica l'APK (0.2.0 beta)](https://github.com/Double-bited-Hamburger/parser-compiti/releases/download/v0.2.0-beta/parser-compiti-0.2.0-beta.apk)**: aprilo dal telefono e consenti l'installazione. Serve Android 7 o successivo. |
| 💻 **PC** | Scarica il codice dalla [pagina della versione](../../releases/tag/v0.2.0-beta) («Source code (zip)») e segui [Installazione sul PC](#installazione-sul-pc). |

Tutte le versioni, con l'impronta SHA-256 di ogni APK, sono nelle [Release](../../releases). Installa l'APK solo da qui: uno preso altrove potrebbe essere stato modificato per rubare le password.

> Progetto non ufficiale, fatto da uno studente. Non è affiliato né approvato da Argo Software, Madisoft, Gruppo Spaggiari Parma o Untis. Usa le stesse API delle app ufficiali per le famiglie, **solo in lettura**: sul registro non modifica nulla.

## 100% locale

Il programma gira solo sul tuo dispositivo. Non esiste un server del progetto, non ci sono account, statistiche d'uso, pubblicità o script esterni (la pagina ha una Content-Security-Policy che vieta di caricare qualunque cosa da fuori).

Si collega soltanto a:

| A chi | Perché |
| --- | --- |
| Il registro del tuo profilo: `portaleargo.it`, `nuvola.madisoft.it` oppure `web.spaggiari.eu` | per scaricare i tuoi dati con le tue credenziali |
| `*.webuntis.com` (facoltativo) | per l'orario della classe, in accesso anonimo |
| `itunes.apple.com` (solo per Argo) | per leggere il numero di versione dell'app Argo, che Argo richiede; non riceve dati tuoi |
| Il tuo PC o telefono, nella rete di casa (facoltativo) | per la sincronizzazione, cifrata, che non passa da Internet |

Le password dei registri restano sul dispositivo:
- **sul PC** nel portachiavi del sistema (su Windows il Gestione credenziali);
- **sul telefono** cifrate, con una chiave custodita dall'Android Keystore; l'app è esclusa dai backup.

## Registri supportati

| Registro | Stato |
| --- | --- |
| Argo didUP | stabile |
| Nuvola (Madisoft) | stabile, per studenti e tutori |
| ClasseViva (Spaggiari) | **sperimentale**: appena aggiunto, va provato su account veri ([cerchiamo tester](../../issues)) |
| Axios, Mastercom, altri | non ancora: chiedili con una [issue](../../issues/new/choose) |

Orario: WebUntis. Se la tua scuola usa altro, apri una issue.

## Installazione sul PC

Serve [Python](https://www.python.org/downloads/) 3.12 o successivo.

```
pip install -r requirements.txt
```

Poi doppio clic su `avvia.bat` (oppure `py main.py`, su Linux/macOS `python3 main.py`). Si apre il browser con la pagina dell'app; la finestra nera deve restare aperta mentre la usi. Al primo avvio crei un profilo (registro, utente, password, e facoltativamente la scuola WebUntis). Puoi avere più profili, per esempio per fratelli.

La pagina risponde solo al collegamento che apre `avvia.bat`, che contiene un gettone segreto: gli altri programmi del computer e gli altri utenti non possono leggere i tuoi dati. Se apri a mano `http://127.0.0.1:8765` vedrai un messaggio che ti chiede di usare `avvia.bat`.

Altre opzioni: `py main.py --help`.

## App Android

L'APK già pronto si scarica dalla sezione [Scarica](#scarica) qui sopra. In [ANDROID.md](ANDROID.md) c'è come installarlo, come costruirlo da te e come sincronizzarlo con il PC.

## Impostazioni

`config.py` raccoglie le cose personalizzabili a mano: parole che fanno riconoscere una verifica, nomi brevi delle materie, ore settimanali per il calcolo delle assenze, materie dell'orario da nascondere.

Per cambiarle senza toccare `config.py`, crea accanto un file `config_locale.py` con le sole voci che vuoi diverse (per esempio `ORE_SETTIMANALI = 30`). È escluso dal repository, quindi resta tuo anche quando aggiorni il programma.

## Feedback, problemi, nuovi registri

Tutto passa dalle [issue](../../issues/new/choose): segnalazioni di errori, idee, richieste di nuovi registri o orari.

**Non incollare mai password, voti o nomi** nelle issue. Per aiutare con un registro nuovo o con ClasseViva puoi lanciare `py main.py --dump`: scarica i dati del profilo e ne stampa **solo la struttura** (nomi dei campi e tipi, nessun contenuto). Rileggila comunque prima di incollarla.

Per un problema di sicurezza non aprire una issue pubblica: vedi [SECURITY.md](SECURITY.md).

## Sviluppo

```
py -m unittest
```

Struttura:
- `main.py` avvia l'app;
- `server.py` è il server locale, che ascolta solo su 127.0.0.1;
- `argo_client.py`, `nuvola_client.py` e `classeviva_client.py` scaricano dai registri; `*_adatta.py` portano i dati di Nuvola e ClasseViva nella forma di quelli di Argo;
- `parser.py` e `stats.py` fanno estrazione e calcoli;
- `sincronizza.py` gestisce lo scambio con il telefono;
- `web/` contiene la pagina, `android/` l'app Android.

## Licenza

[MIT](LICENSE).
