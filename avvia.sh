#!/bin/sh
# Avvia Parser Compiti su Linux e macOS: ./avvia.sh (oppure sh avvia.sh).
# La prima volta prepara in .venv un ambiente Python tutto suo, con le librerie giuste: niente da installare nel sistema.
cd "$(dirname "$0")" || exit 1

if [ ! -x .venv/bin/python ]; then
    if ! command -v python3 >/dev/null 2>&1; then
        echo "Serve Python 3.12 o successivo: installalo dal gestore pacchetti o da https://www.python.org/downloads/"
        exit 1
    fi
    if ! python3 -c 'import sys; sys.exit(sys.version_info < (3, 12))'; then
        echo "Serve Python 3.12 o successivo, qui c'è $(python3 --version 2>&1)."
        exit 1
    fi
    echo "Prima installazione: preparo l'ambiente Python, ci vuole qualche minuto..."
    if ! python3 -m venv .venv; then
        rm -rf .venv
        echo "Non riesco a creare l'ambiente Python. Su Debian e Ubuntu installa prima: sudo apt install python3-venv"
        exit 1
    fi
fi

# Le librerie si (re)installano la prima volta e quando cambia requirements.txt (dopo un aggiornamento).
if ! cmp -s requirements.txt .venv/requisiti.txt; then
    if ! .venv/bin/python -m pip install --disable-pip-version-check -r requirements.txt; then
        echo "Installazione delle librerie non riuscita: controlla la connessione e i messaggi qui sopra."
        exit 1
    fi
    cp requirements.txt .venv/requisiti.txt
fi

exec .venv/bin/python main.py "$@"
