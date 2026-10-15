"""Avvio dentro l'app Android: lo stesso server del PC, raggiungibile solo dal telefono stesso."""

import threading


def avvia():
    """Avvia il server in sottofondo e restituisce la porta su cui risponde."""
    # Si importa qui: l'app imposta prima le variabili d'ambiente che config legge.
    import config
    import server

    try:
        app = server.avvia()  # stessa porta ogni volta, così la pagina ritrova le sue preferenze
    except OSError:
        app = server.avvia(porta=0)  # occupata da un'altra app: una qualsiasi libera
    config.PORTA = app.server_address[1]
    app.daemon_threads = True
    threading.Thread(target=app.serve_forever, daemon=True).start()
    return config.PORTA
