# Novità

## In arrivo

- **Scheda «Oggi» ridisegnata**:
  - in alto quattro numeri: compiti da fare, verifiche della settimana, giorni alla prossima verifica, media generale;
  - nel riquadro «Adesso» un conto alla rovescia che scorre secondo per secondo e una barra a tacche (una ogni 5 minuti di lezione) al posto dell'anello;
  - l'orario ha il riassunto della giornata («5 ore · 1 supplenza · 1 annullata») e accanto a ogni ora se è fatta, quanto manca o cosa è cambiato;
  - barre di avanzamento per i compiti del giorno dopo, per lo studio e sotto ogni voto recente;
  - sul PC la scheda si divide in tre colonne.
- **Menu nuovo**: sul PC è una barra laterale con le icone; sul telefono una barra fissa in basso con tutte e otto le sezioni, sempre a portata di pollice.
- **Scheda «Voti» ridisegnata**:
  - «Cosa fare adesso»: le materie sotto il 6, quelle in calo e le verifiche della settimana nelle materie in bilico, con il voto che serve;
  - una scheda per materia al posto della tabella: media, mini-grafico degli ultimi voti, andamento, scritto/orale/pratico, minimo e massimo, quanto serve per il 6;
  - il simulatore diventa «Che voto mi serve?»: tocchi materia e voto e vedi subito come cambiano le medie; si possono ancora impilare più voti ipotetici;
  - grafici, elenco di tutti i voti e consigli completi restano, in sezioni che si aprono con un tocco.
- Tutti i temi vestono il nuovo disegno.

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
