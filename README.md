# Analiza Inconso NIO

Aplikacja Streamlit do analizy plików `Blocklist.csv` z danych Inconso/NIO.
Pozwala szybko sprawdzić rozkład problemów według czasu, sortera, stanowiska, tacy i zmian.

## Funkcje

- upload pliku CSV przez `drag and drop` albo przycisk `Upload`,
- automatyczne czyszczenie wartości eksportowanych z Excela w formacie `="..."`,
- filtry: zakres dat, zmiana, NIO/NokReason, sorter, station,
- filtr fragmentu godzinowego z domyślnym pełnym zakresem,
- zależna lista `Station` po wybranym zakresie, NIO i sorterze,
- rozkład godzinowy NIO,
- wykresy kołowe dla stanowisk i tac,
- unikatowe tace w trybie `Sorter = Total`, np. `SO20 / 197`,
- Pareto NIO,
- porównanie `Shift 1` vs `Shift 2`,
- osobna zakładka z analizą zrzutni (`Chute`),
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

Wgraj plik CSV z separatorami `;`. Wymagane kolumny:

- `TimeTele`
- `Tray Sorter`
- `Tray Tray`
- `NokReason`
- `Station`

Jeśli w katalogu aplikacji znajduje się lokalny plik `Blocklist.csv`, aplikacja może użyć go jako przykładu.
Pliki CSV i PDF są ignorowane przez Git, żeby nie publikować danych operacyjnych.

## Struktura

```text
.
├── app.py
├── requirements.txt
├── .streamlit/
│   └── config.toml
└── README.md
```

## Uwagi

Repozytorium nie powinno zawierać `.venv`, cache Pythona, plików CSV ani eksportów PDF.
