# World Clock

A minimalist desktop clock that shows the time of a chosen country side by side with a home country's time (Brazil by default), including the time zone and the hour difference between the two. Originally built for Linux (KDE Plasma); also runs on Windows 11.

![World Clock screenshot](docs/screenshot.png)

## Features

- Real-time clock for the selected target country, next to your chosen home country's time
- Both the target and the home country can be changed independently
- Smart search: type any part of a country's (or city's) name to filter the list — "sydney" finds Australia (Sydney), not just names starting with it
- Time zone (UTC±X) shown for both countries, plus the hour difference between them, calculated automatically (accounts for daylight saving time)
- About 40 pre-loaded countries, each with a flag, in a searchable picker
- Dark, minimalist design with rounded corners and a soft shadow
- Borderless, draggable window, optionally always on top
- Remembers both selections between runs

## Requirements

- Linux with a graphical session (tested on Fedora with KDE Plasma / Wayland) **or** Windows 11
- Python 3.9+
- [PySide6](https://pypi.org/project/PySide6/)
- On Windows only: [`tzdata`](https://pypi.org/project/tzdata/) — Windows has no built-in IANA time zone database, so Python's `zoneinfo` needs this package to resolve time zones like `Europe/Lisbon`. It's listed in `requirements.txt` (installed automatically on Windows, skipped on Linux) so you don't need to install it by hand.

## Installation

```bash
git clone https://github.com/<your-username>/world-clock.git
cd world-clock
pip install -r requirements.txt
```

On Windows (PowerShell), the equivalent is:

```powershell
git clone https://github.com/<your-username>/world-clock.git
cd world-clock
py -m pip install -r requirements.txt
```

## Usage

```bash
python3 world_clock.py
```

On Windows:

```powershell
py world_clock.py
```

- Click the target country field (top right, large) and start typing to search — matches anywhere in the name, not just the start
- Click the home country field (bottom right, smaller) to search and change the country you're comparing against
- Click the "⌄" next to either field to browse the full, unfiltered country list
- Click and drag any empty area of the window to move it
- Click the "×" in the top-right corner to close

### Application menu shortcut (KDE Plasma)

To launch it from the Plasma menu like any other app, create `~/.local/share/applications/world-clock.desktop` with the following content (adjust the `Exec` path to wherever you cloned the project):

```ini
[Desktop Entry]
Type=Application
Name=World Clock
Comment=Time in countries around the world compared to Brasília time
Exec=python3 /full/path/to/world-clock/world_clock.py
Icon=clock
Terminal=false
Categories=Utility;Clock;
```

Then run `update-desktop-database ~/.local/share/applications` and look for "World Clock" in the menu.

### Start Menu / taskbar shortcut (Windows)

1. Right-click on your Desktop → **New → Shortcut**.
2. For the location, point it at `pythonw.exe` (the windowless launcher, so no console window stays open) plus the script path, e.g.:
   ```
   C:\Users\<you>\AppData\Local\Programs\Python\Python312\pythonw.exe C:\full\path\to\world-clock\world_clock.py
   ```
3. Name the shortcut "World Clock" and finish.
4. Optionally right-click the new shortcut → **Properties** → **Change Icon** to pick something clock-shaped, then drag the shortcut onto the taskbar or into `shell:startup` to launch it at login.

## Adding or removing countries

The country list lives at the top of [world_clock.py](world_clock.py), in the `COUNTRIES` constant. Each entry is a tuple of `(display name, IANA time zone, ISO country code)`:

```python
("Portugal", "Europe/Lisbon", "PT"),
```

The two-letter code is used to look up the matching flag image in `assets/flags/` (named `<code>.png`, lowercase) — add a new PNG there if the country isn't already covered. Time zones follow the [IANA time zone database](https://en.wikipedia.org/wiki/List_of_tz_database_time_zones). The bundled fonts (see below) cover Latin script plus accents (e.g. "Brasília"); a country name in another script would need its own font handling.

## Tech stack

- [PySide6](https://doc.qt.io/qtforpython/) (Qt6) for the interface
- `zoneinfo` (Python standard library, backed by the `tzdata` package on Windows) for time zone calculations
- Flag images in `assets/flags/` are rasterized from [flag-icons](https://github.com/lipis/flag-icons) (MIT license — see [assets/flags/LICENSE](assets/flags/LICENSE)). They're bundled as PNGs rather than rendered as emoji because Qt doesn't reliably compose flag emoji into an actual flag picture on every platform/font — a real image looks the same everywhere.
- Fonts in `assets/fonts/` are Noto Sans / Noto Sans Mono (SIL Open Font License — see [assets/fonts/LICENSE](assets/fonts/LICENSE)), trimmed to the Latin characters this app actually uses (~65KB per weight instead of the ~2MB full variable font). Bundling them means the app looks identical on Linux and Windows instead of silently falling back to whatever generic font Windows picks when Noto Sans isn't installed.

## License

Distributed under the MIT License. See [LICENSE](LICENSE) for details.
