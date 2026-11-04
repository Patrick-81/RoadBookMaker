# RoadBookMaker

RoadBookMaker is a Python-based GUI weather routing software designed for **Sailaway III** (IMOCA class). It processes GRIB2 weather forecasts (NOAA GFS), computes optimal loxodromic routes using polar performance diagrams, and renders interactive navigation maps.

---

## Features

* **Hourly GRIB2 Weather Processing**: Downloads and parses NOAA GFS wind data (0.25 degrees) using `xarray` and `cfgrib`, hourly out to forecast hour 120, then 3-hourly. One cache folder per GFS cycle, with a completeness check so a half-published run is never used.
* **Sailaway III Weather Calibration**: Queries the in-game weather API and fits the GFS field (time offset, speed scale, wind rotation) on a 3x3 grid around the boat, which typically brings the wind error from 4-6 knots down to about 1 knot.
* **IMOCA Performance Polars**: Calculates optimal boat speed and true wind angles from `imoca_polar.csv`.
* **Isochrone Routing & Corridor**: Time-stepped isochrone solver, navigation corridor ("no more than N hours lost"), roadbook, travelled track and GPX export.
* **Interactive Map & Routing**: Visualizes routing options and tracks using `matplotlib` and `cartopy`.
* **Tkinter GUI**: Lightweight desktop interface for tactical weather routing.
* **Easy Windows Deployment**: Script-based installation without requiring a standalone `.exe`.

---

## Requirements

* **Operating System**: Windows 10/11 or Linux.
* **Python**: Version 3.10 or higher.
* *Windows Users*: Make sure to check **"Add Python to PATH"** during Python installation.

---

## Installation & Launch (Windows)

No pre-compiled `.exe` file is required. Installation and virtual environment management are completely automated via batch scripts.

1. **Clone or Download the Repository**:
```cmd
git clone git@github.com:patrick-81/RoadBookMaker.git
cd RoadBookMaker
```

2. **Run the Application**:
Double-click `run.bat` or execute it from the Windows Command Prompt:
```cmd
run.bat
```

### What `run.bat` Does Automatically:

* Prompts for a target installation directory (defaults to `%LOCALAPPDATA%RoadBookMaker`).
* Copies the core application files (`router_app.py`, `sailaway_api.py`, `imoca_polar.csv`, `requirements.txt`) to the target location.
* Creates a desktop shortcut (`RoadBookMaker.lnk`).
* Sets up an isolated Python Virtual Environment (`.venv`).
* Installs all dependencies listed in `requirements.txt` via `pip`.
* Launches the main GUI application (`router_app.py`).

---

## Uninstallation (Windows)

To remove RoadBookMaker, its virtual environment, and its desktop shortcut:

1. Navigate to your installation folder (or open the local repository).
2. Double-click `uninstall.bat` or run:
```cmd
uninstall.bat
```

3. Confirm the removal prompt. You will also be asked whether to completely purge the installation directory.

---

## Weather Calibration (Sailaway III)

Sailaway's in-game weather is **not** the raw GFS forecast: it is a smoothed, time-shifted and slightly damped version of it. A GRIB-only router therefore over-estimates the wind near fronts.

To fix this, the app can query the game's own weather endpoint (documented in the archived `SailawayAPI.pdf`):

```
https://backend.sailaway.world/cgi-bin/sailaway/getenvironment.pl?lat=<lat>&lon=<lon>
```

On each routing run (option *"Calibrate weather on SA III"*, enabled by default):

1. a 3x3 grid of the game's current weather is sampled around the boat;
2. the best fit of the GFS field is computed: time offset (+/-8 h), speed scale and wind rotation;
3. the corrected field is used for the routing, and the result is shown in the roadbook header.

Measured on a real case: GFS said 13.1 kn / 134 deg where the game had 11.3 kn / 126 deg; after calibration the error drops from 4-6 knots to about 1 knot.

Notes:
* the endpoint returns the **current** weather only (no forecast), so routing still relies on GFS, but calibrated;
* the API asks for at least 10 minutes between calls, so results are cached in `sailaway_cache.json`;
* this endpoint is not officially supported and may change; if it is unreachable the app simply runs uncalibrated;
* uncheck the option to use the raw GFS field with a manual time offset.

---

## Usage

1. **Launch the GUI**: Run `run.bat` or click the **RoadBookMaker** shortcut on your Desktop.
2. **Set the start point and time**: enter the boat position from Sailaway (or use *Import Sailaway GPS*), and the in-game UTC time.
3. **Set the finish point** and the routing parameters (time step, number of steps, corridor tolerance).
4. **Compute the route**: the solver calculates the optimal headings from the polar diagram and the weather field, then shows the roadbook, the corridor and the map.
5. **Where am I?**: compares your actual position with the planned route (cross-track error, ahead/behind, remaining distance).

---

## Project Structure

```
RoadBookMaker/
├── router_app.py        # Main Tkinter GUI application (routing, roadbook, map)
├── sailaway_api.py      # Sailaway III in-game weather API (calibration)
├── imoca_polar.csv      # IMOCA class performance polars
├── requirements.txt     # Python dependencies (xarray, cfgrib, cartopy, matplotlib, ...)
├── run.bat              # Automated Windows setup & launch script
├── uninstall.bat        # Clean uninstallation script
└── README.md            # Project documentation
```

Local runtime data (not tracked by git): `grib_cache/`, `config_routing.json`, `sailaway_cache.json`, `route_optimale.gpx`.

---

## License

Distributed under the MIT License. See `LICENSE` for more information.
