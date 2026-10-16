# Novità

## 0.2.1-beta

- **Linux e macOS**: nuovo `avvia.sh`. Su tutti e tre i sistemi lo script di avvio (`avvia.bat` su Windows) prepara da solo, al primo avvio, un ambiente Python nella cartella `.venv` con le librerie giuste: niente più `pip install` a mano, e su Debian e Ubuntu recenti non si scontra con il Python del sistema. Controlla anche che ci sia Python 3.12 o successivo.
- **Sincronizzazione col telefono**:
  - su Linux, dopo averla disattivata non si riusciva a riattivarla senza riavviare l'app;
  - su macOS «Attiva» restava bloccato per più di un minuto.
- I test automatici ora girano su Windows, Linux e macOS.

## 0.2.0-beta

- **ClasseViva, account con più studenti** (per esempio un genitore con due figli): dopo il primo «Aggiorna», nel profilo compare «Studente da mostrare» per scegliere quale figlio vedere. La scelta passa anche al telefono con la sincronizzazione. Da provare su account veri ([#6](https://github.com/Double-bited-Hamburger/parser-compiti/issues/6)).
- **Nuvola**: le date dei voti si calcolano sempre nell'ora italiana, anche se il computer o il telefono è impostato su un altro fuso orario (prima un voto di mezzanotte poteva finire al giorno prima).
- APK Android scaricabile direttamente dal README e dalle Release, con impronta SHA-256.

## 0.1.0-beta

Prima versione pubblica.

- Registri: Argo didUP, Nuvola e, sperimentale, **ClasseViva** (Spaggiari). Orario da WebUntis.
- Schede: oggi, agenda, compiti da spuntare, studio, orario con variazioni, voti con grafici e simulatore, carico di lavoro, assenze. PDF della settimana e dei compiti.
- Più profili, con la panoramica di tutti insieme.
- App Android con notifiche e widget, sincronizzata con il PC in Wi‑Fi.
- **100% locale**: rimossa la vecchia modalità «sito» online. Il programma gira solo sul PC o sul telefono.
- Sicurezza:
  - la pagina sul PC risponde solo con il gettone segreto dato all'avvio, così gli altri programmi non leggono dati né codice di abbinamento;
  - i messaggi della sincronizzazione valgono una volta sola e per 15 minuti;
  - al massimo due sincronizzazioni contemporanee;
  - portachiavi del sistema anche su Linux e macOS;
  - dipendenze con versioni fisse.
