# RoadBookMaker

RoadBookMaker is a Python-based GUI weather routing software designed for **Sailaway III** (IMOCA class). It processes GRIB2 weather forecasts (NOAA GFS), computes optimal loxodromic routes using polar performance diagrams, and renders interactive navigation maps.

---

## Features

* **GRIB2 Weather Processing**: Downloads and parses NOAA GFS wind data using `xarray` and `cfgrib`.
* **IMOCA Performance Polars**: Calculates optimal boat speed and true wind angles from `imoca_polar.csv`.
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

* Prompts for a target installation directory (defaults to `%LOCALAPPDATA%\RoadBookMaker`).
* Copies core application files to the target location.
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

## Usage

1. **Launch the GUI**: Run `run.bat` or click the **RoadBookMaker** shortcut on your Desktop.
2. **Load GRIB Data**: Import NOAA GFS GRIB2 files or trigger an automatic download within the application.
3. **Set Waypoints**: Define start and target coordinates for your IMOCA routing.
4. **Compute Route**: The solver calculates optimal headings based on polar diagrams and weather fields.

---

## Project Structure

```
RoadBookMaker/
├── router_app.py        # Main Tkinter GUI application
├── imoca_polar.csv      # IMOCA class performance polars
├── requirements.txt     # Python dependencies (xarray, cartopy, matplotlib, etc.)
├── run.bat              # Automated Windows setup & launch script
├── uninstall.bat        # Clean uninstallation script
└── README.md            # Project documentation

```

---

## License

Distributed under the MIT License. See `LICENSE` for more information.
