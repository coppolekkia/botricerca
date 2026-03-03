# botricerca

Scraper per annunci immobiliari di affitto in Italia. Cerca appartamenti su diversi portali immobiliari con filtri su citta e canone massimo mensile.

## Siti supportati

- **Immobiliare.it** - Il portale immobiliare piu visitato in Italia
- **Idealista.it** - Portale leader nel sud Europa
- **Casa.it** - Storico portale italiano

## Installazione

```bash
pip install -r requirements.txt
```

## Uso

Ricerca base (Milano, max 1000 EUR/mese, tutti i siti):

```bash
python main.py
```

Con opzioni personalizzate:

```bash
# Solo immobiliare.it, max 800 EUR
python main.py --city milano --max-price 800 --sites immobiliare

# Tutti i siti, salva in CSV
python main.py --output risultati.csv

# Salva in JSON, 5 pagine per sito
python main.py --pages 5 --output risultati.json

# Verbose mode
python main.py -v
```

### Parametri

| Parametro | Default | Descrizione |
|-----------|---------|-------------|
| `--city` | `milano` | Citta in cui cercare |
| `--max-price` | `1000` | Canone massimo mensile (EUR) |
| `--pages` | `3` | Pagine massime per sito |
| `--sites` | tutti | Siti da cercare (`immobiliare`, `idealista`, `casa`) |
| `--delay` | `2.0` | Ritardo tra le richieste (secondi) |
| `--output` / `-o` | - | File di output (`.csv` o `.json`) |
| `--verbose` / `-v` | `false` | Log dettagliato |

## Struttura

```
botricerca/
  main.py              # Entry point e CLI
  requirements.txt     # Dipendenze Python
  scrapers/
    __init__.py        # Exports
    base.py            # Classe base e dataclass Listing
    immobiliare.py     # Scraper per immobiliare.it
    idealista.py       # Scraper per idealista.it
    casa.py            # Scraper per casa.it
```

## Note

- I siti immobiliari cambiano frequentemente la struttura HTML. I selettori CSS potrebbero necessitare aggiornamenti periodici.
- Idealista.it applica protezioni anti-scraping aggressive -- potrebbe restituire risultati limitati o richiedere un delay piu alto.
- Usa il parametro `--delay` per rispettare i rate limit dei siti.
- Per una ricerca completa, si consiglia di visitare anche i link diretti stampati dal programma.

## Licenza

MIT
