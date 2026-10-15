# Sicurezza

L'app maneggia password dei registri, voti e assenze: un problema di sicurezza conta più di qualunque altro bug.

## Come segnalarlo

**Non aprire una issue pubblica.** Usa la segnalazione privata di GitHub: scheda *Security* del repository → *Report a vulnerability*. Descrivi il problema e, se puoi, come riprodurlo. Non allegare dati veri (password, voti, nomi).

## Cosa è dentro il perimetro

- lettura dei dati o delle password da parte di un altro programma, di un altro utente del computer o di un sito web;
- intercettazione o manomissione della sincronizzazione PC ↔ telefono;
- collegamenti a server diversi da quelli elencati nel README;
- password salvate in chiaro dove non dovrebbero.

## Come è protetta l'app (in breve)

- Il server ascolta solo su `127.0.0.1` e risponde solo alla pagina che presenta il gettone segreto (cookie HttpOnly, SameSite=Strict), che riceve dal collegamento aperto all'avvio. Controlla anche l'intestazione Host contro il DNS rebinding.
- Ogni richiesta che modifica qualcosa deve portare un'intestazione personalizzata, che un altro sito non può aggiungere (CSRF).
- La Content-Security-Policy vieta script e risorse esterne. Tutti i testi del registro vengono messi in pagina con escape.
- Le password stanno nel portachiavi del sistema; sul telefono sono cifrate con una chiave dell'Android Keystore.
- La sincronizzazione è cifrata e autenticata (Fernet) con una chiave ricavata da un codice casuale da 100 bit. Ogni messaggio vale una volta sola e per 15 minuti, e il PC accetta al massimo due scambi alla volta.
- Gli indirizzi del server WebUntis sono limitati a `*.webuntis.com` e quello del PC, sul telefono, agli indirizzi di rete privata.
