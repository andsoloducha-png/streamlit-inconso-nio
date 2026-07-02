# Analiza Inconso NIO

Aplikacja Streamlit do analizy plików `Blocklist.csv` z danych Inconso/NIO.
Pozwala szybko sprawdzić rozkład problemów według czasu, sortera, stanowiska,
tacy, zrzutni i zmian.

## Funkcje

- upload pliku CSV przez `drag and drop` albo przycisk `Upload`,
- automatyczne czyszczenie wartości eksportowanych z Excela w formacie `="..."`,
- filtry: zakres dat, zmiana, fragment godzinowy, NIO/NokReason, sorter i station,
- fragmentator godzinowy z domyślnym pełnym zakresem i krokiem co 5 minut,
- zależne listy filtrów, m.in. `Station` po wybranym zakresie, NIO i sorterze,
- rozkład godzinowy NIO z poprawną kolejnością przedziałów czasu,
- wykresy kołowe dla stanowisk i tac,
- unikatowe tace w trybie `Sorter = Total`, np. `SO20 / 197`,
- osobna analiza zrzutni (`Chute`),
- skumulowany wykres `Chute` według `Station`,
- Pareto NIO i porównanie `Shift 1` vs `Shift 2`,
- ranking top kombinacji problemowych: sorter / station / taca / NIO,
- podgląd danych po filtrach.

## Wymagania

- Python 3.11+
- pakiety z `requirements.txt`

## Uruchomienie lokalne

```powershell
python -m venv .venv
.\.venv\Scripts\pip.exe install -r requirements.txt
.\.venv\Scripts\streamlit.exe run app.py
```

Aplikacja uruchomi się domyślnie pod adresem:

```text
http://localhost:8501
```

## Dane wejściowe

Wgraj plik CSV z separatorem `;`. Wymagane kolumny:

- `TimeTele`
- `Tray Sorter`
- `Tray Tray`
- `NokReason`
- `Station`

Opcjonalnie aplikacja wykorzystuje też kolumnę `Chute`, jeżeli jest dostępna
w danych. Jeśli w katalogu aplikacji znajduje się lokalny plik `Blocklist.csv`,
aplikacja może użyć go jako przykładu.

Pliki CSV i PDF są ignorowane przez Git, żeby nie publikować danych operacyjnych.

## Struktura projektu

```text
.
|-- app.py
|-- requirements.txt
|-- README.md
|-- .streamlit/
|   `-- config.toml
`-- inconso_app/
    |-- __init__.py
    |-- charts.py
    |-- config.py
    |-- data.py
    |-- styles.py
    |-- tables.py
    |-- time_filters.py
    `-- ui.py
```

## Moduły

- `app.py` - lekki punkt startowy Streamlit.
- `inconso_app/config.py` - stałe, zakresy zmian i przedziały godzinowe.
- `inconso_app/data.py` - wczytywanie i normalizacja CSV.
- `inconso_app/time_filters.py` - logika zmian, godzin i bucketów.
- `inconso_app/tables.py` - agregacje, tabele i pomocnicze etykiety.
- `inconso_app/charts.py` - wspólne ustawienia wykresów Plotly.
- `inconso_app/styles.py` - konfiguracja strony i CSS.
- `inconso_app/ui.py` - główny widok aplikacji i zakładki.

## Formatowanie

Kod jest formatowany Blackiem:

```powershell
.\.venv\Scripts\python.exe -m black app.py inconso_app
```

## Uwagi

Repozytorium nie powinno zawierać `.venv`, cache Pythona, plików CSV ani
eksportów PDF.
