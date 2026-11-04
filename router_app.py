import os
from datetime import datetime, timezone, timedelta
import requests
import numpy as np
import pandas as pd
import xarray as xr
from scipy.interpolate import RegularGridInterpolator
import matplotlib.pyplot as plt
import json
import cartopy.crs as ccrs
import cartopy.feature as cfeature
import tkinter as tk
from tkinter import messagebox, ttk, filedialog

CONFIG_FILE = "config_routing.json"

# ==========================================
# 0. TRADUCTIONS (FR / EN)
# ==========================================
LANGS = {
    "FR": {
        "title": "Routage Météo IMOCA - Sailaway III",
        "lang_label": "Langue / Language :",
        "polar_frame": " Fichier Polaire Bateau ",
        "polar_btn": "Parcourir...",
        "start_frame": " Point de Départ & Horodatage (Référence Session) ",
        "finish_frame": " Point d'Arrivée ",
        "time_frame": " Paramètres Temporels & Météo ",
        "lat_deg": "Lat Deg:", "min": "Min (0-60):", "lon_deg": "Lon Deg:",
        "timestep": "Pas de temps (h) :", "steps": "Nb Étapes max :", "offset": "Décalage vent Sailaway (h) :",
        "sim_start_lbl": "Début Simu UTC (AAAA-MM-JJ HH:MM:SS) :",
        "set_time_btn": "Set",
        "get_boat_gps_btn": "⛵ Saisir GPS Sailaway",
        "time_set_success": "Horodatage de départ verrouillé avec succès à :",
        "force_grib": "Forcer le rafraîchissement des GRIBs (ignorer le cache)",
        "avoid_land": "Éviter la terre (côtes et îles, marge 5 NM)",
        "error_title": "Erreur",
        "params_frame": " Paramètres de Routage ", "polar_lbl": "Polaire:",
        "ok_btn": "Valider", "cancel_btn": "Annuler",
        "lat_title": " Latitude (ex: 50° 36.81') ", "lon_title": " Longitude (ex: 14° 12.83') ",
        "invalid_fmt": "Format invalide :", "min_lat_err": "Minutes de latitude entre 0.00 et 59.99.", "min_lon_err": "Minutes de longitude entre 0.00 et 59.99.",
        "bad_datetime": "Format de date/heure invalide :", "gps_updated": "Position de départ mise à jour avec succès :",
        "success": "Succès", "routing_done": "Routage terminé !", "routing_error": "Erreur du routage :",
        "no_coast": "Trait de côte indisponible, routage SANS test de terre :", "polar_missing": "Polaire introuvable :",
        "use_as_start": "Utiliser comme départ du routage", "start_updated": "Départ mis à jour — relance le routage",
        "corridor_lbl": "Couloir : perte max (h) :", "legend_corridor": "Couloir de navigation (perte ≤ {tol:g} h)", "corr_calc_error": "Couloir non calculé :", "corr_unreached": "Couloir non calculé : la route n'atteint pas l'arrivée dans le nombre de pas choisi. Augmente « Nombre de pas » (ou le pas de temps).",
        "legend_track": "Route parcourue", "track_btn": "Trace parcourue…", "track_title": "Trace parcourue",
        "track_summary": "{n} point(s) enregistré(s)  ·  {nm:.0f} NM parcourus", "track_delete": "Supprimer la sélection", "track_clear": "Tout effacer",
        "track_confirm": "Effacer toute la trace enregistrée ?", "track_empty": "Aucun point enregistré. Chaque « Où en suis-je ? » ajoute un point.", "close_btn": "Fermer",
        "run_btn": "Lancer le Routage",
        "where_btn": "📍 Où en suis-je ?",
        "exit_btn": "🚪 Sortie",
        "error_title": "Erreur",
        "results_title": "Feuille de Route Optimisée (Roadbook)",
        "col_utc": "UTC", "col_local": "Heure solaire", "col_hour": "Échéance", "col_lat": "Latitude", "col_lon": "Longitude", 
        "col_tws": "TWS (nds)", "col_twd": "TWD (°)", "col_twa": "TWA (°)", "col_bsp": "BSP (nds)",
        "arrival": "ARRIVÉE",
        "plot_title": "Routage Météo - Navigation Interactive",
        "legend_opt": "Route Optimale",
        "legend_start": "Départ Session",
        "legend_finish": "Arrivée",
        "legend_boat": "Position Réelle (⛵)",
        "legend_theo": "Position Théorique",
        "boat_label": "Position Réelle ⛵\n"
    },
    "EN": {
        "title": "IMOCA Weather Routing - Sailaway III",
        "lang_label": "Language / Langue :",
        "polar_frame": " Boat Polar File ",
        "polar_btn": "Browse...",
        "start_frame": " Start Point & Timestamp (Session Reference) ",
        "finish_frame": " Finish Point ",
        "time_frame": " Time & Weather Parameters ",
        "lat_deg": "Lat Deg:", "min": "Min (0-60):", "lon_deg": "Lon Deg:",
        "timestep": "Time step (h):", "steps": "Max steps:", "offset": "Sailaway wind shift (h):",
        "sim_start_lbl": "Sim Start UTC (YYYY-MM-DD HH:MM:SS):",
        "set_time_btn": "Set",
        "get_boat_gps_btn": "⛵ Import Sailaway GPS",
        "time_set_success": "Simulation start timestamp successfully locked to:",
        "force_grib": "Force GRIB refresh (ignore cache)",
        "avoid_land": "Avoid land (coasts and islands, 5 NM margin)",
        "error_title": "Error",
        "params_frame": " Routing Parameters ", "polar_lbl": "Polar:",
        "ok_btn": "OK", "cancel_btn": "Cancel",
        "lat_title": " Latitude (e.g. 50° 36.81') ", "lon_title": " Longitude (e.g. 14° 12.83') ",
        "invalid_fmt": "Invalid format:", "min_lat_err": "Latitude minutes must be between 0.00 and 59.99.", "min_lon_err": "Longitude minutes must be between 0.00 and 59.99.",
        "bad_datetime": "Invalid date/time format:", "gps_updated": "Start position updated:",
        "success": "Success", "routing_done": "Routing complete!", "routing_error": "Routing error:",
        "no_coast": "Coastline unavailable, routing WITHOUT land test:", "polar_missing": "Polar file not found:",
        "use_as_start": "Use as routing start", "start_updated": "Start updated — run the routing again",
        "corridor_lbl": "Corridor: max loss (h):", "legend_corridor": "Navigation corridor (loss ≤ {tol:g} h)", "corr_calc_error": "Corridor not computed:", "corr_unreached": "Corridor not computed: the route does not reach the finish within the chosen number of steps. Increase the number of steps (or the time step).",
        "legend_track": "Track sailed", "track_btn": "Sailed track…", "track_title": "Sailed track",
        "track_summary": "{n} point(s) recorded  ·  {nm:.0f} NM sailed", "track_delete": "Delete selected", "track_clear": "Clear all",
        "track_confirm": "Clear the whole recorded track?", "track_empty": "No point recorded yet. Each “Where am I?” adds a point.", "close_btn": "Close",
        "run_btn": "Run Routing",
        "where_btn": "📍 Where am I?",
        "exit_btn": "🚪 Exit",
        "results_title": "Optimized Roadbook",
        "col_utc": "UTC", "col_local": "Solar time", "col_hour": "Elapsed", "col_lat": "Latitude", "col_lon": "Longitude", 
        "col_tws": "TWS (kts)", "col_twd": "TWD (°)", "col_twa": "TWA (°)", "col_bsp": "BSP (kts)",
        "arrival": "ARRIVAL",
        "plot_title": "Weather Routing - Interactive Navigation",
        "legend_opt": "Optimal Route",
        "legend_start": "Session Start",
        "legend_finish": "Finish",
        "legend_boat": "Actual Position (⛵)",
        "legend_theo": "Theoretical Position",
        "boat_label": "Actual Position ⛵\n"
    }
}


# ==========================================
# 1. POPUP DE SAISIE DE POSITION BATEAU
# ==========================================
class BoatPosDialog(tk.Toplevel):
    def __init__(self, parent, default_lat=50.6, default_lon=-14.2, lang="FR", ask_time=False, time_hint=""):
        super().__init__(parent)
        self.title("Position Actuelle du Bateau (Sailaway)" if lang == "FR" else "Current Boat Position")
        self.ask_time = ask_time
        self.geometry("380x300" if ask_time else "380x250")
        self.resizable(False, False)
        self.transient(parent)
        self.grab_set()

        d_lat_deg = int(abs(default_lat))
        d_lat_min = round((abs(default_lat) - d_lat_deg) * 60, 2)
        d_lat_hem = "N" if default_lat >= 0 else "S"

        d_lon_deg = int(abs(default_lon))
        d_lon_min = round((abs(default_lon) - d_lon_deg) * 60, 2)
        d_lon_hem = "E" if default_lon >= 0 else "W"

        self.lat_deg = tk.StringVar(value=str(d_lat_deg))
        self.lat_min = tk.StringVar(value=f"{d_lat_min:.2f}")
        self.lat_hemi = tk.StringVar(value=d_lat_hem)

        self.lon_deg = tk.StringVar(value=str(d_lon_deg))
        self.lon_min = tk.StringVar(value=f"{d_lon_min:.2f}")
        self.lon_hemi = tk.StringVar(value=d_lon_hem)

        self.result = None
        t = LANGS[lang]
        self.t = t

        lat_frame = tk.LabelFrame(self, text=t["lat_title"], font=("Arial", 9, "bold"))
        lat_frame.pack(fill="x", padx=10, pady=5)
        tk.Label(lat_frame, text=t["lat_deg"]).grid(row=0, column=0, padx=2, pady=5)
        tk.Entry(lat_frame, textvariable=self.lat_deg, width=5, justify="center").grid(row=0, column=1)
        tk.Label(lat_frame, text=t["min"]).grid(row=0, column=2, padx=2)
        tk.Entry(lat_frame, textvariable=self.lat_min, width=6, justify="center").grid(row=0, column=3)
        tk.Radiobutton(lat_frame, text="N", variable=self.lat_hemi, value="N").grid(row=0, column=4)
        tk.Radiobutton(lat_frame, text="S", variable=self.lat_hemi, value="S").grid(row=0, column=5)

        lon_frame = tk.LabelFrame(self, text=t["lon_title"], font=("Arial", 9, "bold"))
        lon_frame.pack(fill="x", padx=10, pady=5)
        tk.Label(lon_frame, text=t["lon_deg"]).grid(row=0, column=0, padx=2, pady=5)
        tk.Entry(lon_frame, textvariable=self.lon_deg, width=5, justify="center").grid(row=0, column=1)
        tk.Label(lon_frame, text=t["min"]).grid(row=0, column=2, padx=2)
        tk.Entry(lon_frame, textvariable=self.lon_min, width=6, justify="center").grid(row=0, column=3)
        tk.Radiobutton(lon_frame, text="E", variable=self.lon_hemi, value="E").grid(row=0, column=4)
        tk.Radiobutton(lon_frame, text="W", variable=self.lon_hemi, value="W").grid(row=0, column=5)

        self.when_utc = None
        self.time_var = tk.StringVar(value=datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S"))
        if ask_time:
            time_frame = tk.LabelFrame(self, text=" Heure UTC de cette position " if lang == "FR" else " UTC time of this position ", font=("Arial", 9, "bold"))
            time_frame.pack(fill="x", padx=10, pady=5)
            tk.Entry(time_frame, textvariable=self.time_var, width=22, justify="center").pack(padx=5, pady=5)
            if time_hint:
                tk.Label(time_frame, text=time_hint, font=("Arial", 8), fg="#444444", justify="left").pack(padx=5, pady=(0, 5))

        btn_frame = tk.Frame(self)
        btn_frame.pack(fill="x", padx=10, pady=10)
        tk.Button(btn_frame, text=t["ok_btn"], command=self.validate, bg="#2e7d32", fg="white", font=("Arial", 9, "bold"), width=12).pack(side=tk.LEFT, expand=True)
        tk.Button(btn_frame, text=t["cancel_btn"], command=self.destroy, bg="#c62828", fg="white", font=("Arial", 9, "bold"), width=12).pack(side=tk.RIGHT, expand=True)

    def validate(self):
        try:
            ld = float(self.lat_deg.get().strip())
            lm = float(self.lat_min.get().strip())
            if not (0.0 <= lm < 60.0): raise ValueError(self.t["min_lat_err"])
            lat = ld + (lm / 60.0)
            if self.lat_hemi.get() == "S": lat = -lat

            lod = float(self.lon_deg.get().strip())
            lom = float(self.lon_min.get().strip())
            if not (0.0 <= lom < 60.0): raise ValueError(self.t["min_lon_err"])
            lon = lod + (lom / 60.0)
            if self.lon_hemi.get() == "W": lon = -lon

            if self.ask_time:
                raw = self.time_var.get().strip()
                try:
                    self.when_utc = datetime.strptime(raw, "%Y-%m-%d %H:%M:%S").replace(tzinfo=timezone.utc)
                except ValueError:
                    self.when_utc = datetime.strptime(raw, "%Y-%m-%d %H:%M").replace(tzinfo=timezone.utc)
            self.result = (lat, lon)
            self.destroy()
        except Exception as e:
            messagebox.showerror(self.t["error_title"], f"{self.t['invalid_fmt']}\n{e}", parent=self)


# ==========================================
# 2. CHARGEMENT DE LA POLAIRE & GFS
# ==========================================
def load_polar(filepath):
    ext = os.path.splitext(filepath)[1].lower()
    if ext == '.csv':
        try:
            df = pd.read_csv(filepath, index_col=0, sep=';')
            if len(df.columns) <= 1: df = pd.read_csv(filepath, index_col=0, sep=',')
        except Exception:
            df = pd.read_csv(filepath, index_col=0, sep=',')
    elif ext == '.pol':
        df = pd.read_csv(filepath, comment='#', sep=r'\s+', index_col=0)
    else:
        raise ValueError(f"Format de polaire non supporté : {ext}")

    df = df.apply(pd.to_numeric, errors='coerce').fillna(0.0)
    return RegularGridInterpolator((df.index.values.astype(float), df.columns.values.astype(float)), 
                                 df.values.astype(float), method='linear', bounds_error=False, fill_value=0.0)


def try_download_cycle(lat_min, lat_max, lon_min, lon_max, gfs_cycle_time, max_hours, step_hours, output_dir, force_download):
    date_str = gfs_cycle_time.strftime("%Y%m%d")
    cycle_str = f"{gfs_cycle_time.hour:02d}"
    
    meta_file = os.path.join(output_dir, "metadata.json")
    should_download = force_download

    if not should_download and os.path.exists(meta_file):
        try:
            with open(meta_file, 'r') as f:
                meta = json.load(f)
                if meta.get("cycle") != f"{date_str}_{cycle_str}":
                    should_download = True
        except Exception:
            should_download = True

    downloaded_files = []
    for f in range(0, max_hours + 1, step_hours):
        f_str = f"f{f:03d}"
        filename = os.path.join(output_dir, f"gfs_{f_str}.grib")
        if not should_download and os.path.exists(filename) and os.path.getsize(filename) > 1000:
            downloaded_files.append(filename)
            continue
        
        params = {
            'file': f'gfs.t{cycle_str}z.pgrb2.0p25.{f_str}',
            'lev_10_m_above_ground': 'on', 'var_UGRD': 'on', 'var_VGRD': 'on',
            'subregion': '', 'leftlon': lon_min, 'rightlon': lon_max,
            'bottomlat': lat_min, 'toplat': lat_max, 'dir': f'/gfs.{date_str}/{cycle_str}/atmos'
        }
        try:
            res = requests.get("https://nomads.ncep.noaa.gov/cgi-bin/filter_gfs_0p25.pl", params=params, stream=True, timeout=10)
            if res.status_code == 200 and len(res.content) > 1000:
                with open(filename, 'wb') as fo:
                    fo.write(res.content)
                downloaded_files.append(filename)
            elif os.path.exists(filename) and os.path.getsize(filename) > 1000:
                downloaded_files.append(filename)
        except Exception:
            if os.path.exists(filename) and os.path.getsize(filename) > 1000:
                downloaded_files.append(filename)

    if not downloaded_files:
        return None

    if should_download:
        try:
            with open(meta_file, 'w') as mf: 
                json.dump({"cycle": f"{date_str}_{cycle_str}", "last_download": datetime.now(timezone.utc).isoformat()}, mf)
        except Exception:
            pass

    datasets = []
    for fn in downloaded_files:
        try:
            d = xr.open_dataset(fn, engine='cfgrib')
            # cfgrib : 'time' = heure du cycle (identique pour tous les fichiers), 'valid_time' = heure réelle de la prévision.
            vt = np.atleast_1d(d['valid_time'].values)
            d = d.drop_vars(['time', 'step', 'valid_time'], errors='ignore').expand_dims(time=vt)
            datasets.append(d)
        except Exception:
            pass

    if not datasets:
        return None

    with xr.set_options(use_new_combine_kwarg_defaults=True):
        ds = xr.concat(datasets, dim='time')
    if 'time' in ds.dims: 
        ds = ds.sortby('time').drop_duplicates(dim='time')
    return ds

def download_gfs_forecast(lat_min, lat_max, lon_min, lon_max, base_time, max_hours=360, step_hours=6, output_dir="grib_cache", force_download=False):
    os.makedirs(output_dir, exist_ok=True)
    gfs_hour = (base_time.hour // 6) * 6
    gfs_cycle_time = base_time.replace(hour=gfs_hour, minute=0, second=0, microsecond=0)

    ds = try_download_cycle(lat_min, lat_max, lon_min, lon_max, gfs_cycle_time, max_hours, step_hours, output_dir, force_download)
    if ds is not None:
        return ds

    for _ in range(3):
        gfs_cycle_time -= timedelta(hours=6)
        ds = try_download_cycle(lat_min, lat_max, lon_min, lon_max, gfs_cycle_time, max_hours, step_hours, output_dir, force_download)
        if ds is not None:
            return ds

    raise RuntimeError(f"Impossible de télécharger les fichiers GRIB GFS.\nVérifiez votre connexion internet.")


# ==========================================
# 3. CALCULS & ROUTAGE
# ==========================================
def compute_bearing(lat1, lon1, lat2, lon2):
    phi1, phi2 = np.radians(lat1), np.radians(lat2)
    dlon = np.radians(lon2 - lon1)
    x = np.sin(dlon) * np.cos(phi2)
    y = np.cos(phi1) * np.sin(phi2) - np.sin(phi1) * np.cos(phi2) * np.cos(dlon)
    return (np.degrees(np.arctan2(x, y)) + 360) % 360

EARTH_RADIUS_NM = 3440.065

def great_circle_nm(lat1, lon1, lat2, lon2):
    phi1, phi2 = np.radians(lat1), np.radians(lat2)
    dphi = phi2 - phi1
    dlmb = np.radians(np.asarray(lon2) - np.asarray(lon1))
    a = np.sin(dphi / 2) ** 2 + np.cos(phi1) * np.cos(phi2) * np.sin(dlmb / 2) ** 2
    return 2 * EARTH_RADIUS_NM * np.arcsin(np.sqrt(np.clip(a, 0.0, 1.0)))

def destination_point(lat, lon, hdg, dist_nm):
    phi1, lmb1 = np.radians(lat), np.radians(lon)
    theta = np.radians(hdg)
    delta = dist_nm / EARTH_RADIUS_NM
    phi2 = np.arcsin(np.sin(phi1) * np.cos(delta) + np.cos(phi1) * np.sin(delta) * np.cos(theta))
    lmb2 = lmb1 + np.arctan2(np.sin(theta) * np.sin(delta) * np.cos(phi1), np.cos(delta) - np.sin(phi1) * np.sin(phi2))
    return np.degrees(phi2), (np.degrees(lmb2) + 540.0) % 360.0 - 180.0

class WindField:
    def __init__(self, ds):
        self.lat = np.asarray(ds.latitude.values, dtype=float)
        self.lon = np.asarray(ds.longitude.values, dtype=float)
        times = np.asarray(ds.time.values).astype('datetime64[s]')
        order = np.argsort(times)
        self.times = times[order]
        self.u = ds['u10'].transpose('time', 'latitude', 'longitude').values[order]
        self.v = ds['v10'].transpose('time', 'latitude', 'longitude').values[order]
        self.lon360 = self.lon.max() > 180.0

    def get(self, lat, lon, when):
        lat = np.atleast_1d(np.asarray(lat, dtype=float))
        lon = np.atleast_1d(np.asarray(lon, dtype=float))
        if self.lon360: lon = lon % 360.0
        if when.tzinfo is not None: when = when.replace(tzinfo=None)
        t = np.datetime64(when, 's')
        n = len(self.times)
        i1 = int(np.clip(np.searchsorted(self.times, t), 0, n - 1))
        i0 = max(i1 - 1, 0)
        t0, t1 = self.times[i0], self.times[i1]
        w = 0.0 if t1 == t0 else float(np.clip((t - t0) / (t1 - t0), 0.0, 1.0))
        ilat = np.abs(self.lat[:, None] - lat[None, :]).argmin(axis=0)
        ilon = np.abs(self.lon[:, None] - lon[None, :]).argmin(axis=0)
        u = (1 - w) * self.u[i0, ilat, ilon] + w * self.u[i1, ilat, ilon]
        v = (1 - w) * self.v[i0, ilat, ilon] + w * self.v[i1, ilat, ilon]
        return np.hypot(u, v) * 1.94384, (270.0 - np.degrees(np.arctan2(v, u))) % 360.0

    def inside(self, lat, lon, tol=0.25):
        lat, lon = np.asarray(lat, dtype=float), np.asarray(lon, dtype=float)
        if self.lon360: lon = lon % 360.0
        return (lat >= self.lat.min() - tol) & (lat <= self.lat.max() + tol) & (lon >= self.lon.min() - tol) & (lon <= self.lon.max() + tol)

def polar_speed(polar_interp, twa, tws):
    twa_grid, tws_grid = polar_interp.grid
    twa = np.minimum(np.abs(twa), twa_grid.max())
    tws = np.minimum(tws, tws_grid.max())
    twa, tws = np.broadcast_arrays(twa, tws)
    return polar_interp(np.column_stack([twa.ravel(), tws.ravel()])).reshape(twa.shape)

# ==========================================
# 3b. TERRE : MASQUE CÔTIER ET TEST (land_test)
# ==========================================
_LAND_CACHE = {}

def make_land_test(lat_min, lat_max, lon_min, lon_max, res_deg=0.05, margin_nm=5.0, resolution='10m', geoms=None):
    """
    Construit un test terre/mer rapide (grille booléenne) à partir du trait de côte Natural Earth (cartopy).
    Retourne land_test(lat, lon) -> tableau booléen (True = terre, ou mer à moins de ~margin_nm de la côte).
      - Les sommets du trait de côte sont aussi marqués : les îlots plus petits qu'une cellule ne sont pas ratés.
      - Marge réelle = margin_nm + 0 à 3 NM (taille d'une cellule).
      - Hors de la zone [lat_min..lat_max, lon_min..lon_max], tout est considéré comme de la mer.
      - geoms : liste de polygones shapely (tests) ; sinon Natural Earth 'land' est téléchargé par cartopy (une fois).
    """
    cache_key = (lat_min, lat_max, lon_min, lon_max, res_deg, margin_nm, resolution)
    use_cache = geoms is None
    if use_cache and cache_key in _LAND_CACHE:
        return _LAND_CACHE[cache_key]

    import shapely
    from scipy import ndimage

    if geoms is None:
        import cartopy.io.shapereader as shpreader
        path = shpreader.natural_earth(resolution=resolution, category='physical', name='land')
        geoms = list(shpreader.Reader(path).geometries())

    lats = lat_min + res_deg * np.arange(int(np.ceil((lat_max - lat_min) / res_deg)) + 1)
    lons = lon_min + res_deg * np.arange(int(np.ceil((lon_max - lon_min) / res_deg)) + 1)
    mask = np.zeros((len(lats), len(lons)), dtype=bool)
    bbox = shapely.box(lon_min, lat_min, lon_max, lat_max)

    for g in geoms:
        if not g.is_valid:
            g = shapely.make_valid(g)
        if not g.intersects(bbox):
            continue
        for poly in shapely.get_parts(g.intersection(bbox)):
            if poly.geom_type != 'Polygon' or poly.is_empty:
                continue
            x0, y0, x1, y1 = poly.bounds
            i0 = max(int(np.floor((y0 - lat_min) / res_deg)), 0)
            i1 = min(int(np.ceil((y1 - lat_min) / res_deg)) + 1, len(lats))
            j0 = max(int(np.floor((x0 - lon_min) / res_deg)), 0)
            j1 = min(int(np.ceil((x1 - lon_min) / res_deg)) + 1, len(lons))
            X, Y = np.meshgrid(lons[j0:j1], lats[i0:i1])
            mask[i0:i1, j0:j1] |= shapely.contains_xy(poly, X, Y)
            xy = shapely.get_coordinates(poly)
            vi = np.rint((xy[:, 1] - lat_min) / res_deg).astype(int)
            vj = np.rint((xy[:, 0] - lon_min) / res_deg).astype(int)
            good = (vi >= 0) & (vi < len(lats)) & (vj >= 0) & (vj < len(lons))
            mask[vi[good], vj[good]] = True

    # Marge de sécurité : dilatation elliptique (1° de longitude vaut moins de NM que 1° de latitude)
    mid_lat = 0.5 * (lat_min + lat_max)
    r_lat = int(round(margin_nm / 60.0 / res_deg))
    r_lon = int(round(margin_nm / (60.0 * np.cos(np.radians(mid_lat))) / res_deg))
    if r_lat > 0 or r_lon > 0:
        yy, xx = np.ogrid[-r_lat:r_lat + 1, -r_lon:r_lon + 1]
        struct = (yy / max(r_lat, 1)) ** 2 + (xx / max(r_lon, 1)) ** 2 <= 1.0
        mask = ndimage.binary_dilation(mask, structure=struct)

    def land_test(lat, lon):
        lat, lon = np.broadcast_arrays(np.asarray(lat, dtype=float), np.asarray(lon, dtype=float))
        i = np.rint((lat - lat_min) / res_deg).astype(int)
        j = np.rint((lon - lon_min) / res_deg).astype(int)
        inside = (i >= 0) & (i < mask.shape[0]) & (j >= 0) & (j < mask.shape[1])
        out = np.zeros(lat.shape, dtype=bool)
        out[inside] = mask[i[inside], j[inside]]
        return out

    land_test.mask, land_test.lats, land_test.lons = mask, lats, lons
    if use_cache:
        _LAND_CACHE[cache_key] = land_test
    return land_test


# ==========================================
# 3c. SUIVI : POSITION RÉELLE vs ROUTE OPTIMALE
# ==========================================
def fmt_dm(lat, lon):
    """Format degrés / minutes décimales, comme Sailaway : 50°36.81'N 014°12.83'W"""
    def one(v, pos, neg, width):
        hemi = pos if v >= 0 else neg
        v = abs(v)
        d = int(v)
        m = round((v - d) * 60.0, 2)
        if m >= 60.0:
            d, m = d + 1, 0.0
        return f"{d:0{width}d}°{m:05.2f}'{hemi}"
    return f"{one(lat, 'N', 'S', 2)} {one(lon, 'E', 'W', 3)}"


def _point_on_route(P, k):
    """Position (lat, lon) à l'indice fractionnaire k de la route P (tableau Nx2) : grand cercle entre points."""
    n = len(P)
    if n == 1:
        return float(P[0, 0]), float(P[0, 1])
    k = float(np.clip(k, 0.0, n - 1))
    i = min(int(k), n - 2)
    f = k - i
    d = float(great_circle_nm(P[i, 0], P[i, 1], P[i + 1, 0], P[i + 1, 1]))
    if d < 1e-9:
        return float(P[i, 0]), float(P[i, 1])
    brg = float(compute_bearing(P[i, 0], P[i, 1], P[i + 1, 0], P[i + 1, 1]))
    lat, lon = destination_point(P[i, 0], P[i, 1], brg, f * d)
    return float(lat), float(lon)


def locate_on_route(path, step_h, t0, boat, when):
    """
    Compare la position réelle du bateau à la route optimale.
      path   : [(lat, lon), ...] ; path[i] est atteint à t0 + i * step_h
      t0     : datetime UTC du début de la route (base_time + offset)
      boat   : (lat, lon) position réelle
      when   : datetime UTC auquel le bateau était à cette position
    Retourne un dict :
      theo        position théorique à l'heure `when` (si on avait suivi la route à la lettre)
      near        point de la route le plus proche du bateau (projection sur la route)
      xte         écart latéral à la route (NM) et side ('port' / 'starboard' : côté du bateau par rapport à la route)
      ahead_h     > 0 : bateau en avance sur le plan, < 0 : en retard (heures)
      dist_to_theo, bearing_to_theo : distance et cap du bateau vers la position théorique
      remaining_nm distance restante par la route depuis le point le plus proche
    """
    P = np.asarray(path, dtype=float)
    n = len(P)
    if n < 2:
        raise ValueError("Route trop courte")
    blat, blon = float(boat[0]), float(boat[1])

    # 1) Position théorique à l'heure donnée (progression horaire le long de la route)
    k_now = (when - t0).total_seconds() / 3600.0 / step_h
    status = 'before' if k_now < 0 else ('finished' if k_now > n - 1 else 'underway')
    theo = _point_on_route(P, k_now)

    # 2) Projection du bateau sur la route (repère local plat centré sur le bateau, en NM)
    dl = (P[:, 1] - blon + 180.0) % 360.0 - 180.0
    x = dl * np.cos(np.radians(blat)) * 60.0
    y = (P[:, 0] - blat) * 60.0
    ax_, ay_, bx_, by_ = x[:-1], y[:-1], x[1:], y[1:]
    abx, aby = bx_ - ax_, by_ - ay_
    L2 = abx ** 2 + aby ** 2
    safe = np.where(L2 > 1e-12, L2, 1.0)
    u = np.where(L2 > 1e-12, np.clip(-(ax_ * abx + ay_ * aby) / safe, 0.0, 1.0), 0.0)
    dist = np.hypot(ax_ + u * abx, ay_ + u * aby)
    i = int(np.argmin(dist))
    k_near = i + float(u[i])
    cross = abx[i] * (-ay_[i]) - aby[i] * (-ax_[i])
    side = 'starboard' if cross < 0 else 'port'

    seg_len = great_circle_nm(P[:-1, 0], P[:-1, 1], P[1:, 0], P[1:, 1])
    remaining = float(seg_len[i] * (1.0 - u[i]) + seg_len[i + 1:].sum())

    return {
        "status": status, "theo": theo, "near": _point_on_route(P, k_near),
        "k_now": float(k_now), "k_near": k_near, "t0": t0,
        "rel_now_h": float(k_now * step_h), "rel_near_h": float(k_near * step_h),
        "nearest_idx": int(round(k_near)),
        "leg_idx": int(min(max(int(np.floor(max(k_now, 0.0))), 0), n - 2)),
        "xte": float(dist[i]), "side": side,
        "ahead_h": float((k_near - k_now) * step_h),
        "dist_to_theo": float(great_circle_nm(blat, blon, theo[0], theo[1])),
        "bearing_to_theo": float(compute_bearing(blat, blon, theo[0], theo[1])),
        "remaining_nm": remaining,
        "t_near": t0 + timedelta(hours=k_near * step_h),
        "eta": t0 + timedelta(hours=(n - 1) * step_h),
    }


def position_report(info, boat, when, details, lang="FR", ref=None, corridor=None):
    """
    Synthèse structurée de « Où en suis-je ? » :
      headline / subline / tone ('ok' | 'late' | 'info') pour le bandeau,
      notes (avertissements), sections [(titre, [(libellé, valeur), ...])],
      text (version texte brut pour « Copier »), short (annotation de la carte).
    Tous les temps sont donnés en UTC et en « T+ » (même échelle que la colonne Échéance du roadbook).
    """
    fr = (lang == "FR")
    fmt = "%Y-%m-%d %H:%M:%S"
    fmt_min = "%Y-%m-%d %H:%M"

    def L(a, b):
        return a if fr else b

    def trel(h):
        return "T%s%.1f h" % ("+" if h >= 0 else "−", abs(h))

    t0, status = info["t0"], info["status"]
    leg = details[min(info["leg_idx"], len(details) - 1)] if details else None
    side = {"starboard": L("tribord", "starboard"), "port": L("bâbord", "port")}[info["side"]]
    cap = f"{info['bearing_to_theo']:.0f}°"
    on_route = info["xte"] < 0.5
    xte_fr = "sur la route" if on_route else f"{info['xte']:.1f} NM à {side} de la route"
    xte_en = "on the route" if on_route else f"{info['xte']:.1f} NM to {side} of the route"
    lat_short = (L("sur la route", "on the route") if on_route else f"{info['xte']:.1f} NM {side}")
    a = info["ahead_h"]
    rel_now, rel_near = info["rel_now_h"], info["rel_near_h"]

    # --- bandeau ---------------------------------------------------------------------------
    if status == "before":
        tone = "info"
        headline = L("Route pas encore commencée à l'heure saisie", "Route not started at the time entered")
        pace = L("non calculé", "not computed")
        pace_short = L("route pas encore commencée", "route not started")
    elif abs(a) <= 0.05:
        tone = "ok"
        headline = L("Dans les temps sur la route optimale", "On schedule on the optimal route")
        pace = pace_short = L("dans les temps", "on schedule")
    elif a > 0:
        tone = "ok"
        headline = L(f"En avance de {a:.1f} h sur la route optimale", f"{a:.1f} h ahead of the optimal route")
        pace = pace_short = L(f"{a:.1f} h d'avance", f"{a:.1f} h ahead")
    else:
        tone = "late"
        headline = L(f"En retard de {-a:.1f} h sur la route optimale", f"{-a:.1f} h behind the optimal route")
        pace = pace_short = L(f"{-a:.1f} h de retard", f"{-a:.1f} h behind")
    subline = L(f"{info['dist_to_theo']:.1f} NM de la position théorique  ·  {xte_fr}  ·  cap {cap} pour la rejoindre",
                f"{info['dist_to_theo']:.1f} NM from the theoretical position  ·  {xte_en}  ·  bearing {cap} to reach it")

    # --- avertissements --------------------------------------------------------------------
    notes = []
    if status == "before":
        mins = int(round((t0 - when).total_seconds() / 60.0))
        notes.append(L(f"L'heure saisie ({trel(rel_now)}) précède le départ de la route (dans {mins // 60} h {mins % 60:02d} min). "
                       f"La position théorique est donc le point de départ, et l'avance / retard n'est pas calculé.",
                       f"The time entered ({trel(rel_now)}) is before the route start (in {mins // 60} h {mins % 60:02d} min). "
                       f"The theoretical position is therefore the start point, and pace is not computed."))
    elif status == "finished":
        notes.append(L("L'heure saisie est postérieure à l'arrivée théorique de la route optimale.",
                       "The time entered is after the theoretical arrival of the optimal route."))

    # --- sections --------------------------------------------------------------------------
    time_rows = [(L("T+000h (début simu)", "T+000h (sim start)"), f"{t0.strftime(fmt)} UTC")]
    if ref:
        w0 = (t0 + timedelta(hours=ref['offset_h'])).strftime(fmt)
        time_rows.append((L("Vent", "Wind"),
                          L(f"GFS décalé de {ref['offset_h']:+g} h (à T+000h : GFS de {w0} UTC)",
                            f"GFS shifted by {ref['offset_h']:+g} h (at T+000h: GFS of {w0} UTC)")))
    time_rows.append((L("Heure saisie", "Time entered"), f"{when.strftime(fmt)} UTC  =  {trel(rel_now)}"))

    pos_rows = [(L("Position réelle", "Actual position"), fmt_dm(*boat)),
                (L("Position théorique", "Theoretical position") + (L(" (départ)", " (start)") if status == "before" else f" ({trel(rel_now)})"),
                 fmt_dm(*info["theo"]))]

    gap_rows = [(L("Écart réel / théorique", "Actual / theoretical"), L(f"{info['dist_to_theo']:.1f} NM, cap {cap} pour la rejoindre", f"{info['dist_to_theo']:.1f} NM, bearing {cap} to reach it")),
                (L("Écart latéral", "Cross-track"), L(xte_fr if on_route else f"{info['xte']:.1f} NM, bateau à {side} de la route", xte_en if on_route else f"{info['xte']:.1f} NM, boat to {side} of the route")),
                (L("Avance / retard", "Pace"), pace)]
    near = f"{trel(rel_near)}  ({info['t_near'].strftime(fmt_min)} UTC)"
    if status != "before":
        gap_rows.append((L("Tu es au niveau du point", "You are at route point"), L(f"{near}, tu devrais être à {trel(rel_now)}", f"{near}, you should be at {trel(rel_now)}")))

    if corridor:
        c_in, c_nm = corridor_status(corridor["geom"], boat[0], boat[1])
        c_txt = L("dans le couloir", "inside the corridor") if c_in else L(f"hors couloir, à {c_nm:.1f} NM du bord", f"outside the corridor, {c_nm:.1f} NM from its edge")
        gap_rows.append((L("Couloir de navigation", "Navigation corridor"), c_txt + L(f"  (perte ≤ {corridor['tol_h']:g} h)", f"  (loss ≤ {corridor['tol_h']:g} h)")))
    route_rows = []
    if status == "before":
        route_rows.append((L("Point de route le plus proche", "Nearest route point"), near))
    route_rows += [(L("Reste à parcourir", "Remaining"), L(f"{info['remaining_nm']:.0f} NM par la route", f"{info['remaining_nm']:.0f} NM along the route")),
                   (L("Arrivée prévue", "Planned arrival"), f"{info['eta'].strftime(fmt)} UTC")]
    if leg:
        route_rows.append((L("Cap de la route", "Route heading"), L(f"{leg['hdg']:.0f}°   ·   TWA {leg['twa']:.0f}°   ·   BSP {leg['bsp']:.1f} nds", f"{leg['hdg']:.0f}°   ·   TWA {leg['twa']:.0f}°   ·   BSP {leg['bsp']:.1f} kts")))
        route_rows.append((L("Vent sur la route", "Wind on route"), L(f"{leg['tws']:.0f} nds du {leg['twd']:.0f}°", f"{leg['tws']:.0f} kts from {leg['twd']:.0f}°")))

    sections = [(L("REPÈRES DE TEMPS", "TIME REFERENCES"), time_rows),
                (L("POSITIONS", "POSITIONS"), pos_rows),
                (L("ÉCARTS", "GAPS"), gap_rows),
                (L("SUITE DE LA ROUTE", "REST OF THE ROUTE"), route_rows)]

    # --- texte brut (bouton Copier) ------------------------------------------------------------
    out = [headline, subline, ""] + [f"/!\\ {n}" for n in notes] + ([""] if notes else [])
    for title, rows in sections:
        out.append(title)
        out += [f"  {k} : {v}" for k, v in rows]
        out.append("")
    text = "\n".join(out).rstrip() + "\n"

    short = L(f"Théorique ({'T+0.0 h' if status == 'before' else trel(rel_now)}) : {fmt_dm(*info['theo'])}\nÉcart : {info['dist_to_theo']:.1f} NM (cap {cap})\nLatéral : {lat_short}\n{pace_short}",
              f"Theoretical ({'T+0.0 h' if status == 'before' else trel(rel_now)}): {fmt_dm(*info['theo'])}\nGap: {info['dist_to_theo']:.1f} NM (brg {cap})\nCross-track: {lat_short}\n{pace_short}")
    return {"headline": headline, "subline": subline, "tone": tone, "notes": notes, "sections": sections, "text": text, "short": short}


def describe_position(info, boat, when, details, lang="FR", ref=None):
    """Compatibilité : (texte brut, texte court pour la carte)."""
    r = position_report(info, boat, when, details, lang, ref)
    return r["text"], r["short"]


def split_dm(v):
    """Degrés entiers + minutes décimales (arrondies à 0.01, sans jamais afficher 60.00)."""
    a = abs(float(v))
    d = int(a)
    m = round((a - d) * 60.0, 2)
    if m >= 60.0:
        d, m = d + 1, 0.0
    return d, m


def fill_start_fields(e_lat_deg, e_lat_min, e_lon_deg, e_lon_min, lat_hemi, lon_hemi, e_time, lat, lon, when=None):
    """Recopie la position (et l'heure UTC) dans les champs « Point de départ » de la fenêtre principale."""
    lat_d, lat_m = split_dm(lat)
    lon_d, lon_m = split_dm(lon)
    lat_hemi.set("N" if lat >= 0 else "S")
    lon_hemi.set("E" if lon >= 0 else "W")
    for entry, val in ((e_lat_deg, str(lat_d)), (e_lat_min, f"{lat_m:.2f}"), (e_lon_deg, str(lon_d)), (e_lon_min, f"{lon_m:.2f}")):
        entry.delete(0, tk.END)
        entry.insert(0, val)
    if when is not None and e_time is not None:
        e_time.delete(0, tk.END)
        e_time.insert(0, when.strftime("%Y-%m-%d %H:%M:%S"))


def show_position_popup(parent, report, lang="FR", on_use_as_start=None):
    """Fenêtre de synthèse en lecture seule (texte non éditable, sélectionnable), avec bouton Copier."""
    fr = (lang == "FR")
    win = tk.Toplevel(parent)
    win.title("Où en suis-je ?" if fr else "Where am I?")
    try:
        win.geometry(f"620x600+{parent.winfo_rootx() + 40}+{parent.winfo_rooty() + 30}")
    except Exception:
        win.geometry("620x600")
    win.minsize(540, 420)
    win.transient(parent)

    tone = {"ok": "#2e7d32", "late": "#e65100", "info": "#455a64"}.get(report["tone"], "#455a64")
    band = tk.Frame(win, bg=tone)
    band.pack(fill="x")
    tk.Label(band, text=report["headline"], bg=tone, fg="white", font=("Arial", 13, "bold"), anchor="w", justify="left", wraplength=580).pack(fill="x", padx=14, pady=(12, 2))
    tk.Label(band, text=report["subline"], bg=tone, fg="white", font=("Arial", 9), anchor="w", justify="left", wraplength=580).pack(fill="x", padx=14, pady=(0, 12))

    btns = tk.Frame(win)
    btns.pack(side="bottom", fill="x", padx=10, pady=(0, 10))
    body = tk.Frame(win)
    body.pack(side="top", fill="both", expand=True, padx=10, pady=10)

    txt = tk.Text(body, wrap="word", font=("Arial", 10), bg="#fafafa", relief="flat", highlightthickness=1,
                  highlightbackground="#cfd8dc", padx=12, pady=8, cursor="arrow", tabs=("215",))
    sb = tk.Scrollbar(body, orient="vertical", command=txt.yview)
    txt.configure(yscrollcommand=sb.set)
    sb.pack(side="right", fill="y")
    txt.pack(side="left", fill="both", expand=True)

    txt.tag_configure("h", font=("Arial", 9, "bold"), foreground="#1976d2", spacing1=12, spacing3=4)
    txt.tag_configure("row", lmargin1=8, lmargin2=223, spacing1=2, spacing3=2)
    txt.tag_configure("k", foreground="#607d8b")
    txt.tag_configure("v", font=("Arial", 10, "bold"), foreground="#212121")
    txt.tag_configure("warn", background="#fff3cd", foreground="#5d4037", lmargin1=8, lmargin2=8, rmargin=8, spacing1=6, spacing3=6)

    for n in report["notes"]:
        txt.insert("end", n + "\n", "warn")
    for title, rows in report["sections"]:
        txt.insert("end", title + "\n", "h")
        for k, v in rows:
            txt.insert("end", k + "\t", ("row", "k"))
            txt.insert("end", v + "\n", ("row", "v"))
    txt.configure(state="disabled")          # lecture seule : la sélection et Ctrl+C restent possibles

    def copy_text():
        win.clipboard_clear()
        win.clipboard_append(report["text"])
        copy_btn.config(text="Copié !" if fr else "Copied!")

    copy_btn = tk.Button(btns, text="Copier le texte" if fr else "Copy text", command=copy_text, width=16)
    copy_btn.pack(side="left")
    if on_use_as_start is not None:
        T = LANGS["FR" if fr else "EN"]

        def use_start():
            on_use_as_start()
            use_btn.config(text=T["start_updated"], state="disabled")

        use_btn = tk.Button(btns, text=T["use_as_start"], command=use_start, bg="#00838f", fg="white", font=("Arial", 9, "bold"))
        use_btn.pack(side="left", padx=8)
    tk.Button(btns, text="Fermer" if fr else "Close", command=win.destroy, bg="#1976d2", fg="white", font=("Arial", 10, "bold"), width=14).pack(side="right")
    win.bind("<Escape>", lambda e: win.destroy())
    win.bind("<Return>", lambda e: win.destroy())
    win.grab_set()
    win.focus_set()
    parent.wait_window(win)


def run_isochrone_routing(polar_path, ds_grib, base_time, start, finish, time_step_hours=3, total_steps=12, time_offset_hours=6, heading_step_deg=5, sector_width_deg=1.0, arrival_radius_nm=20.0, land_test=None):
    polar = load_polar(polar_path)
    wind = WindField(ds_grib)
    headings = np.arange(0.0, 360.0, heading_step_deg)
    H, s_lat, s_lon, f_lat, f_lon = len(headings), start[0], start[1], finish[0], finish[1]
    layers = [(np.array([s_lat]), np.array([s_lon]), np.array([-1]))]
    prev_hdg, history_fronts, reached = np.array([np.nan]), [[(s_lat, s_lon)]], False
    best_idx = None

    for step in range(total_steps):
        lats, lons, _ = layers[-1]
        N = len(lats)
        t_start = base_time + timedelta(hours=time_offset_hours + step * time_step_hours)
        tws, twd = wind.get(lats, lons, t_start)

        # L'arrivée est-elle atteignable en ligne droite pendant ce pas ? (un rayon fixe peut être « enjambé » entre deux points du front)
        d_f = great_circle_nm(lats, lons, f_lat, f_lon)
        brg_f = compute_bearing(lats, lons, f_lat, f_lon)
        bsp_f = polar_speed(polar, np.abs((brg_f - twd + 180.0) % 360.0 - 180.0), tws)
        can = (bsp_f > 0.1) & (d_f <= bsp_f * time_step_hours)
        if land_test is not None and can.any():
            for frac in (0.25, 0.5, 0.75):
                q_lat, q_lon = destination_point(lats, lons, brg_f, d_f * frac)
                can &= ~land_test(q_lat, q_lon)
        if can.any():
            cand = np.where(can)[0]
            best_idx = int(cand[np.argmin(d_f[cand] / bsp_f[cand])])
            reached = True
            break
        twa = np.abs((headings[None, :] - twd[:, None] + 180.0) % 360.0 - 180.0)
        bsp = polar_speed(polar, twa, tws[:, None])
        
        diff = np.abs((headings[None, :] - prev_hdg[:, None] + 180.0) % 360.0 - 180.0)
        sail_h = np.maximum(time_step_hours - np.where(diff > 45.0, 0.2, 0.0), 0.0)
        new_lat, new_lon = destination_point(lats[:, None], lons[:, None], headings[None, :], bsp * sail_h)

        ok = bsp > 0.1
        ok &= wind.inside(new_lat, new_lon)   # on reste dans la zone GFS téléchargée (hors zone, le vent serait inventé)
        if land_test is not None:
            # on teste plusieurs points le long de chaque segment, pas seulement l'arrivée (sinon on enjambe caps et îlots)
            leg_nm = bsp * sail_h
            for frac in (0.25, 0.5, 0.75, 1.0):
                p_lat, p_lon = destination_point(lats[:, None], lons[:, None], headings[None, :], leg_nm * frac)
                ok &= ~land_test(p_lat, p_lon)
        parent = np.broadcast_to(np.arange(N)[:, None], (N, H))[ok]
        c_hdg = np.broadcast_to(headings[None, :], (N, H))[ok]
        c_lat, c_lon = new_lat[ok], new_lon[ok]
        if c_lat.size == 0: break

        dist_start = great_circle_nm(s_lat, s_lon, c_lat, c_lon)
        brg = compute_bearing(s_lat, s_lon, c_lat, c_lon)
        sector = (brg // sector_width_deg).astype(int)
        order = np.lexsort((-dist_start, sector))
        keep = order[np.unique(sector[order], return_index=True)[1]]

        layers.append((c_lat[keep], c_lon[keep], parent[keep]))
        prev_hdg = c_hdg[keep]
        history_fronts.append(list(zip(c_lat[keep].tolist(), c_lon[keep].tolist())))

        if great_circle_nm(c_lat[keep], c_lon[keep], f_lat, f_lon).min() <= arrival_radius_nm:
            reached = True
            break

    lats, lons, _ = layers[-1]
    idx = best_idx if best_idx is not None else int(np.argmin(great_circle_nm(lats, lons, f_lat, f_lon)))
    best_path = []
    for k in range(len(layers) - 1, -1, -1):
        l_lat, l_lon, l_par = layers[k]
        best_path.append((float(l_lat[idx]), float(l_lon[idx])))
        idx = int(l_par[idx])
    best_path.reverse()
    if reached: best_path.append((f_lat, f_lon))
    return history_fronts, best_path


# ==========================================
# 3d. COULOIR DE NAVIGATION (zone où la perte de temps reste ≤ tolérance)
# ==========================================
def _parse_tol(txt):
    """Champ « Couloir : perte max (h) » -> float >= 0 (0 = pas de couloir). Accepte la virgule."""
    try:
        return max(float(str(txt).strip().replace(",", ".")), 0.0)
    except ValueError:
        return 0.0


def front_polygon(lats, lons, center):
    """Polygone d'un front d'isochrone : points triés par azimut autour de `center` (coordonnées lon/lat)."""
    from shapely.geometry import Polygon
    lats, lons = np.asarray(lats, dtype=float), np.asarray(lons, dtype=float)
    if len(lats) < 3:
        return None
    brg = np.asarray(compute_bearing(center[0], center[1], lats, lons), dtype=float)
    order = np.argsort(brg)
    pts = list(zip(lons[order], lats[order]))
    # Un front ne couvre souvent qu'un secteur d'angle : sans le centre, le polygone n'est qu'une mince calotte
    # (arc + corde) et l'intérieur de la zone atteignable est perdu. On ferme donc l'arc par le centre.
    b_sorted = brg[order]
    gaps = np.diff(np.concatenate([b_sorted, [b_sorted[0] + 360.0]]))
    gi = int(np.argmax(gaps))
    if gaps[gi] > 60.0:
        pts = pts[gi + 1:] + pts[:gi + 1]
        pts.append((center[1], center[0]))
    poly = Polygon(pts)
    return poly if poly.is_valid else poly.buffer(0)


def route_eta_hours(path, polar_path, ds_grib, base_time, finish, time_step_hours, time_offset_hours):
    """Durée (h, depuis T+000h) jusqu'à l'arrivée sur la route optimale, dernier tronçon partiel inclus. None si non atteinte."""
    if len(path) < 2 or great_circle_nm(path[-1][0], path[-1][1], finish[0], finish[1]) > 0.5:
        return None
    polar, wind = load_polar(polar_path), WindField(ds_grib)
    n_full = len(path) - 2
    a = path[-2]
    when = base_time + timedelta(hours=time_offset_hours + n_full * time_step_hours)
    tws, twd = wind.get(a[0], a[1], when)
    hdg = float(compute_bearing(a[0], a[1], finish[0], finish[1]))
    twa = abs((hdg - float(twd[0]) + 180.0) % 360.0 - 180.0)
    bsp = float(polar_speed(polar, np.array([twa]), np.array([float(tws[0])]))[0])
    d = float(great_circle_nm(a[0], a[1], finish[0], finish[1]))
    return n_full * time_step_hours + d / max(bsp, 0.5)


def compute_corridor(polar_path, ds_grib, base_time, start, finish, history_fronts, best_path,
                     time_step_hours, time_offset_hours, tol_h, heading_step_deg=5, sector_width_deg=1.0,
                     land_test=None, return_lenses=False):
    """
    Couloir = ensemble des positions par lesquelles on peut encore arriver au plus tard à ETA_optimale + tol_h.
    À chaque pas k : (zone atteignable depuis le départ à t_k) ∩ (zone d'où l'on atteint l'arrivée avant l'échéance).
      - la première zone est le front d'isochrone aller (déjà calculé) ;
      - la seconde vient d'un routage INVERSE depuis l'arrivée (même polaire, même vent, mêmes pas de temps).
    Retourne une géométrie shapely en (lon, lat), ou None si l'arrivée n'a pas été atteinte.
    """
    from shapely.geometry import Point, LineString
    from shapely.ops import unary_union
    dt = float(time_step_hours)
    if tol_h <= 0 or len(best_path) < 2:
        return None
    eta = route_eta_hours(best_path, polar_path, ds_grib, base_time, finish, dt, time_offset_hours)
    if eta is None:
        # Arrivée non atteinte : l'horizon (pas de temps x nombre de pas) fait office de fin de route,
        # et le dernier point de la route devient l'arrivée « virtuelle » du couloir.
        finish = (float(best_path[-1][0]), float(best_path[-1][1]))
        eta = (len(best_path) - 1) * dt
    polar, wind = load_polar(polar_path), WindField(ds_grib)
    headings = np.arange(0.0, 360.0, heading_step_deg)
    f_lat, f_lon = finish
    s = len(history_fronts) - 1                       # dernier front aller calculé (instant t_s)
    deadline = eta + tol_h
    k_end = int(np.floor(deadline / dt))
    delta0 = deadline - k_end * dt                    # durée partielle du premier pas inverse

    def reverse_step(lats, lons, k_start, dur):
        """Positions d'où l'on atteint (lats, lons) en `dur` heures en partant à t_k_start (vent lu au point d'arrivée du tronçon)."""
        t_wind = base_time + timedelta(hours=time_offset_hours + k_start * dt)
        tws, twd = wind.get(lats, lons, t_wind)
        twa = np.abs((headings[None, :] - twd[:, None] + 180.0) % 360.0 - 180.0)
        bsp = polar_speed(polar, twa, tws[:, None])
        back_hdg = (headings[None, :] + 180.0) % 360.0
        p_lat, p_lon = destination_point(lats[:, None], lons[:, None], back_hdg, bsp * dur)
        ok = (bsp > 0.1) & wind.inside(p_lat, p_lon)
        if land_test is not None:
            for frac in (0.25, 0.5, 0.75, 1.0):
                q_lat, q_lon = destination_point(lats[:, None], lons[:, None], back_hdg, bsp * dur * frac)
                ok &= ~land_test(q_lat, q_lon)
        c_lat, c_lon = p_lat[ok], p_lon[ok]
        if c_lat.size == 0:
            return None
        d_f = great_circle_nm(f_lat, f_lon, c_lat, c_lon)
        sector = (compute_bearing(f_lat, f_lon, c_lat, c_lon) // sector_width_deg).astype(int)
        order = np.lexsort((-d_f, sector))
        keep = order[np.unique(sector[order], return_index=True)[1]]       # le plus éloigné de l'arrivée par secteur
        return c_lat[keep], c_lon[keep]

    back = {}
    cur = (np.array([f_lat]), np.array([f_lon]))
    if delta0 > 1e-6:
        nxt = reverse_step(cur[0], cur[1], k_end, delta0)
        cur = nxt if nxt is not None else cur
    back[k_end] = cur
    for k in range(k_end - 1, -1, -1):
        nxt = reverse_step(cur[0], cur[1], k, dt)
        if nxt is None:
            break
        cur = nxt
        back[k] = cur

    if return_lenses == 'back':
        return back
    eps = 0.04                                        # ≈ 2,4 NM : la route optimale reste toujours dans le couloir
    lenses = {}
    for k in range(0, min(s, len(best_path) - 1) + 1):
        if k not in back:
            continue
        pf = history_fronts[k]
        F = front_polygon([p[0] for p in pf], [p[1] for p in pf], start) if len(pf) >= 3 else None
        B = front_polygon(back[k][0], back[k][1], finish) if len(back[k][0]) >= 3 else None
        route_pt = Point(best_path[k][1], best_path[k][0]).buffer(eps)
        F = F if F is not None else Point(start[1], start[0]).buffer(eps)
        B = B if B is not None else Point(f_lon, f_lat).buffer(eps)
        # Le routage inverse perd ~0,3-0,7 NM par pas (bruit de discrétisation des caps et des secteurs) : au début de la route,
        # cette dérive dépasse la tolérance et le couloir disparaissait. La marge de B croît donc avec le nombre de pas inverses.
        eps_b = eps + min(0.7 * (k_end - k) / 38.0, 1.5)
        lens = F.buffer(eps).intersection(B.buffer(eps_b))
        lenses[k] = unary_union([lens, route_pt]) if not lens.is_empty else route_pt

    ks = sorted(lenses)
    parts = [lenses[k] for k in ks] + [LineString([(p[1], p[0]) for p in best_path]).buffer(eps)]
    parts += [unary_union([lenses[a], lenses[b]]).convex_hull for a, b in zip(ks[:-1], ks[1:])]        # pas de trou entre deux pas
    if ks:
        parts.append(unary_union([lenses[ks[-1]], Point(f_lon, f_lat).buffer(eps)]).convex_hull)
    corridor = unary_union(parts).simplify(0.005)
    return (corridor, lenses) if return_lenses else corridor


def corridor_status(geom, lat, lon):
    """(dans_le_couloir, distance_au_bord_en_NM) pour une position."""
    from shapely.geometry import Point
    from shapely import affinity
    p = Point(lon, lat)
    if geom.contains(p) or geom.touches(p):
        return True, 0.0
    k = np.cos(np.radians(lat)) * 60.0
    g2 = affinity.scale(geom, xfact=k, yfact=60.0, origin=(0, 0))
    p2 = affinity.scale(p, xfact=k, yfact=60.0, origin=(0, 0))
    return False, float(g2.distance(p2))


def analyze_route_performance(best_path, ds_grib, base_time, polar_interp, time_step_hours, time_offset_hours=0):
    wind = WindField(ds_grib)
    route_details = []
    for i in range(len(best_path) - 1):
        lat1, lon1 = best_path[i]
        lat2, lon2 = best_path[i + 1]
        elapsed_hours = i * time_step_hours
        when = base_time + timedelta(hours=elapsed_hours)                 # horloge de la route : T+000h = début simu
        wind_when = when + timedelta(hours=time_offset_hours)            # vent Sailaway = prévision GFS décalée de l'offset
        tws, twd = wind.get(lat1, lon1, wind_when)
        hdg = float(compute_bearing(lat1, lon1, lat2, lon2))
        twa = abs((hdg - float(twd[0]) + 180.0) % 360.0 - 180.0)
        bsp = float(polar_speed(polar_interp, np.array([twa]), np.array([float(tws[0])]))[0])
        route_details.append({
            "utc": when.strftime("%Y-%m-%d %H:%M:%S"), "local": (when + timedelta(hours=lon1 / 15.0)).strftime("%Y-%m-%d %H:%M:%S"),
            "hour": elapsed_hours, "lat": lat1, "lon": lon1, "tws": float(tws[0]), "twd": float(twd[0]), "twa": twa, "bsp": bsp, "hdg": hdg
        })
    return route_details


def export_to_gpx(best_path, filename="route_optimale.gpx"):
    gpx = '<?xml version="1.0" encoding="UTF-8"?>\n<gpx version="1.1" creator="Python IMOCA Router" xmlns="http://www.topografix.com/GPX/1/1">\n  <trk><name>Route Optimisée</name><trkseg>\n'
    for lat, lon in best_path: gpx += f'    <trkpt lat="{lat:.6f}" lon="{lon:.6f}"/>\n'
    with open(filename, 'w', encoding='utf-8') as f: f.write(gpx + '  </trkseg></trk>\n</gpx>')


def plot_interactive_routing(history_fronts, best_path, start, finish, theoretical_pos=None, boat_pos=None, next_heading_info="", lang="FR", track=None, corridor=None):
    t = LANGS[lang]
    fig, ax = plt.subplots(figsize=(12, 7), subplot_kw={'projection': ccrs.PlateCarree()})
    ax.add_feature(cfeature.LAND, facecolor='#e0e0e0', zorder=0)
    ax.add_feature(cfeature.OCEAN, facecolor='#f0f8ff', zorder=0)
    ax.add_feature(cfeature.COASTLINE, linewidth=0.8, edgecolor='black', zorder=1)
    ax.add_feature(cfeature.BORDERS, linestyle=':', alpha=0.5, zorder=1)
    
    gl = ax.gridlines(draw_labels=True, linewidth=0.5, color='gray', alpha=0.5, linestyle='--')
    gl.top_labels, gl.right_labels = False, False

    for front in history_fronts:
        if front: ax.scatter([pt[1] for pt in front], [pt[0] for pt in front], color='lightblue', s=8, alpha=0.4, transform=ccrs.PlateCarree(), zorder=2)
    if corridor is not None:
        ax.add_geometries([corridor["geom"]], crs=ccrs.PlateCarree(), facecolor='#c9a9b6', edgecolor='#a67c8e', alpha=0.45, linewidth=1.0, zorder=1.5)
    if best_path:
        ax.plot([pt[1] for pt in best_path], [pt[0] for pt in best_path], color='red', linewidth=2, marker='o', markersize=3, transform=ccrs.PlateCarree(), label=t["legend_opt"], zorder=3)
        
    ax.scatter(start[1], start[0], color='green', s=100, marker='s', transform=ccrs.PlateCarree(), label=t["legend_start"], zorder=4)
    ax.scatter(finish[1], finish[0], color='purple', s=100, marker='*', transform=ccrs.PlateCarree(), label=t["legend_finish"], zorder=4)

    if theoretical_pos:
        ax.scatter(theoretical_pos[1], theoretical_pos[0], color='orange', s=120, marker='o', transform=ccrs.PlateCarree(), zorder=5, label=t["legend_theo"])

    if track:
        ax.plot([p[1] for p in track], [p[0] for p in track], color='#0d47a1', linewidth=2, marker='o', markersize=4, transform=ccrs.PlateCarree(), zorder=5, label=t["legend_track"])
    b_lat, b_lon = boat_pos if boat_pos else start
    ax.scatter(b_lon, b_lat, color='blue', s=150, marker='^', transform=ccrs.PlateCarree(), zorder=6, label=t["legend_boat"])
    if theoretical_pos and boat_pos:
        ax.plot([boat_pos[1], theoretical_pos[1]], [boat_pos[0], theoretical_pos[0]], color='orange', linestyle='--', linewidth=1.5, transform=ccrs.PlateCarree(), zorder=5)

    extra = [p for p in (boat_pos, theoretical_pos) if p] + list(track or [])
    if corridor is not None:
        bx0, by0, bx1, by1 = corridor["geom"].bounds
        extra += [(by0, bx0), (by1, bx1)]
    all_lats = [pt[0] for f in history_fronts for pt in f] + [pt[0] for pt in best_path] + [p[0] for p in extra]
    all_lons = [pt[1] for f in history_fronts for pt in f] + [pt[1] for pt in best_path] + [p[1] for p in extra]
    if all_lats and all_lons:
        ax.set_extent([min(all_lons) - 3.0, max(all_lons) + 3.0, min(all_lats) - 2.0, max(all_lats) + 2.0], crs=ccrs.PlateCarree())
    else:
        ax.set_extent([-65.0, 0.0, 12.0, 52.0], crs=ccrs.PlateCarree())

    annotation = ax.annotate("", xy=(0, 0), xytext=(20, 20), textcoords="offset points", bbox=dict(boxstyle="round", fc="yellow", alpha=0.9), arrowprops=dict(arrowstyle="->", connectionstyle="arc3,rad=0"))
    annotation.set_visible(False)

    def on_click(event):
        if event.inaxes == ax and event.xdata is not None and event.ydata is not None:
            if np.hypot(event.xdata - b_lon, event.ydata - b_lat) < 1.5:
                annotation.xy = (b_lon, b_lat)
                annotation.set_text(t["boat_label"] + next_heading_info)
                annotation.set_visible(True)
                fig.canvas.draw_idle()
            else:
                annotation.set_visible(False)
                fig.canvas.draw_idle()

    fig.canvas.mpl_connect('button_press_event', on_click)
    plt.title(t["plot_title"])
    handles, _labels = ax.get_legend_handles_labels()
    if corridor is not None:
        from matplotlib.patches import Patch
        handles.append(Patch(facecolor='#c9a9b6', edgecolor='#a67c8e', alpha=0.6, label=t["legend_corridor"].format(tol=corridor["tol_h"])))
    ax.legend(handles=handles, loc='upper right')
    plt.show()


# ==========================================
# 6. INTERFACE GRAPHIQUE (TKINTER)
# ==========================================
def load_last_config():
    now_utc = datetime.now(timezone.utc)
    default_cycle = (now_utc.hour // 6) * 6
    default_base = now_utc.replace(hour=default_cycle, minute=0, second=0, microsecond=0).strftime("%Y-%m-%d %H:%M:%S")

    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, 'r') as f: return json.load(f)
        except Exception: pass
    return {
        "polar_file": "imoca_polar.csv",
        "start_lat_deg": 50, "start_lat_min": 36.81, "start_lat_hemi": "N",
        "start_lon_deg": 14, "start_lon_min": 12.83, "start_lon_hemi": "W",
        "finish_lat_deg": 16, "finish_lat_min": 14.4, "finish_lat_hemi": "N",
        "finish_lon_deg": 61, "finish_lon_min": 31.8, "finish_lon_hemi": "W",
        "time_step_hours": 3, "total_steps": 150, "time_offset_hours": 3,
        "sim_start_utc": default_base,
        "language": "FR", "force_grib": False, "avoid_land": True
    }

def save_config(cfg):
    try:
        if "track" not in cfg:
            cfg = {**cfg, "track": load_track()}    # la trace enregistrée n'est jamais écrasée par une sauvegarde des paramètres
        with open(CONFIG_FILE, 'w') as f: json.dump(cfg, f, indent=4)
    except Exception as e: print(f"Erreur config : {e}")

# ---- Trace de la route parcourue (stockée dans le JSON, clé "track") ----
def load_track():
    """[{'utc': 'AAAA-MM-JJ HH:MM:SS', 'lat': .., 'lon': ..}, ...] triée par heure."""
    out = []
    for p in load_last_config().get("track", []):
        try:
            out.append({"utc": str(p["utc"]), "lat": float(p["lat"]), "lon": float(p["lon"])})
        except Exception:
            pass
    return sorted(out, key=lambda p: p["utc"])

def save_track(track):
    cfg = load_last_config()
    cfg["track"] = track
    save_config(cfg)

def add_track_point(lat, lon, when):
    """Ajoute un point (sans doublon exact) et retourne la trace à jour."""
    track = load_track()
    pt = {"utc": when.strftime("%Y-%m-%d %H:%M:%S"), "lat": round(float(lat), 6), "lon": round(float(lon), 6)}
    if not any(p["utc"] == pt["utc"] and abs(p["lat"] - pt["lat"]) < 1e-6 and abs(p["lon"] - pt["lon"]) < 1e-6 for p in track):
        track.append(pt)
    track.sort(key=lambda p: p["utc"])
    save_track(track)
    return track

def track_points(track):
    return [(p["lat"], p["lon"]) for p in track]

def track_length_nm(track):
    import math
    total = 0.0
    for a, b in zip(track[:-1], track[1:]):
        p1, p2 = math.radians(a["lat"]), math.radians(b["lat"])
        h = math.sin((p2 - p1) / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(math.radians(b["lon"] - a["lon"]) / 2) ** 2
        total += 2 * 3440.065 * math.asin(math.sqrt(min(1.0, h)))
    return total

def show_track_manager(parent, lang="FR"):
    """Liste des positions enregistrées : supprimer une sélection ou tout effacer."""
    T = LANGS["FR" if lang == "FR" else "EN"]
    win = tk.Toplevel(parent)
    win.title(T["track_title"])
    try:
        win.geometry(f"580x420+{parent.winfo_rootx() + 60}+{parent.winfo_rooty() + 40}")
    except Exception:
        win.geometry("580x420")
    win.minsize(500, 300)
    win.transient(parent)

    summary = tk.Label(win, font=("Arial", 10, "bold"), anchor="w")
    summary.pack(fill="x", padx=12, pady=(12, 4))
    btns = tk.Frame(win)
    btns.pack(side="bottom", fill="x", padx=12, pady=(4, 12))
    hint = tk.Label(win, fg="#607d8b", font=("Arial", 9), anchor="w", justify="left", wraplength=540)
    hint.pack(side="bottom", fill="x", padx=12)
    body = tk.Frame(win)
    body.pack(side="top", fill="both", expand=True, padx=12, pady=4)
    lb = tk.Listbox(body, selectmode="extended", font=("Courier", 10), activestyle="none")
    sb = tk.Scrollbar(body, orient="vertical", command=lb.yview)
    lb.configure(yscrollcommand=sb.set)
    sb.pack(side="right", fill="y")
    lb.pack(side="left", fill="both", expand=True)

    def refresh():
        track = load_track()
        lb.delete(0, "end")
        for p in track:
            lb.insert("end", f"{p['utc']} UTC   {fmt_dm(p['lat'], p['lon'])}")
        summary.config(text=T["track_summary"].format(n=len(track), nm=track_length_nm(track)))
        hint.config(text="" if track else T["track_empty"])

    def delete_selected():
        sel = set(lb.curselection())
        if sel:
            save_track([p for i, p in enumerate(load_track()) if i not in sel])
            refresh()

    def clear_all():
        if messagebox.askyesno(T["track_title"], T["track_confirm"], parent=win):
            save_track([])
            refresh()

    tk.Button(btns, text=T["track_delete"], command=delete_selected, width=22).pack(side="left")
    tk.Button(btns, text=T["track_clear"], command=clear_all, bg="#c62828", fg="white", width=14).pack(side="left", padx=8)
    tk.Button(btns, text=T["close_btn"], command=win.destroy, bg="#1976d2", fg="white", font=("Arial", 10, "bold"), width=12).pack(side="right")
    win.bind("<Escape>", lambda e: win.destroy())
    refresh()
    win.grab_set()
    parent.wait_window(win)


def run_gui_application():
    last_cfg = load_last_config()
    root = tk.Tk()
    root.geometry("900x880")
    root.title("Routage Météo Sailaway III")
    root.resizable(True, True)

    lang_var = tk.StringVar(value=last_cfg.get("language", "FR"))
    polar_path_var = tk.StringVar(value=last_cfg.get("polar_file", "imoca_polar.csv"))
    force_grib_var = tk.BooleanVar(value=False)
    land_var = tk.BooleanVar(value=last_cfg.get("avoid_land", True))

    s_lat_hemi = tk.StringVar(value=last_cfg.get("start_lat_hemi", "N"))
    s_lon_hemi = tk.StringVar(value=last_cfg.get("start_lon_hemi", "W"))
    f_lat_hemi = tk.StringVar(value=last_cfg.get("finish_lat_hemi", "N"))
    f_lon_hemi = tk.StringVar(value=last_cfg.get("finish_lon_hemi", "W"))

    main_container = tk.Frame(root)
    main_container.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

    e_s_lat_deg = e_s_lat_min = e_s_lon_deg = e_s_lon_min = None
    e_f_lat_deg = e_f_lat_min = e_f_lon_deg = e_f_lon_min = None
    e_timestep = e_steps = e_offset = e_sim_start = tree = e_corr = None
    stored_route_details = []
    stored_route = None      # {'path': [...], 'step': h, 't0': datetime UTC}
    stored_history = []
    finish_coords = (0, 0)
    _trk = load_track()
    current_boat_coords = (_trk[-1]["lat"], _trk[-1]["lon"]) if _trk else None   # dernière position connue
    theo_coords = None

    def browse_polar():
        fn = filedialog.askopenfilename(title="Polaire", filetypes=[("CSV / POL", "*.csv *.pol"), ("Tous", "*.*")])
        if fn: polar_path_var.set(fn)

    def set_simulation_time():
        current_lang = lang_var.get()
        t = LANGS[current_lang]
        val = e_sim_start.get().strip()
        try:
            datetime.strptime(val, "%Y-%m-%d %H:%M:%S")
            messagebox.showinfo("Confirmation", f"{t['time_set_success']}\n{val}")
        except ValueError:
            try:
                dt = datetime.strptime(val, "%Y-%m-%d %H:%M")
                val_fixed = dt.strftime("%Y-%m-%d %H:%M:%S")
                e_sim_start.delete(0, tk.END)
                e_sim_start.insert(0, val_fixed)
                messagebox.showinfo("Confirmation", f"{t['time_set_success']}\n{val_fixed}")
            except Exception as e:
                messagebox.showerror(t["error_title"], f"{t['bad_datetime']}\n{e}")

    def import_sailaway_gps():
        nonlocal e_s_lat_deg, e_s_lat_min, e_s_lon_deg, e_s_lon_min, s_lat_hemi, s_lon_hemi
        current_lang = lang_var.get()
        
        # Récupérer les valeurs actuelles des champs si l'utilisateur y a déjà mis des chiffres
        try:
            cur_lat_approx = (float(e_s_lat_deg.get().strip()) + float(e_s_lat_min.get().strip()) / 60.0) * (-1 if s_lat_hemi.get() == "S" else 1)
            cur_lon_approx = (float(e_s_lon_deg.get().strip()) + float(e_s_lon_min.get().strip()) / 60.0) * (-1 if s_lon_hemi.get() == "W" else 1)
        except Exception:
            cur_lat_approx, cur_lon_approx = 50.61, -14.21

        dialog = BoatPosDialog(root, default_lat=cur_lat_approx, default_lon=cur_lon_approx, lang=current_lang)
        root.wait_window(dialog)
        if dialog.result is None: return

        lat, lon = dialog.result
        
        # Mettre à jour les champs du formulaire principal
        lat_d = int(abs(lat))
        lat_m = round((abs(lat) - lat_d) * 60, 2)
        lon_d = int(abs(lon))
        lon_m = round((abs(lon) - lon_d) * 60, 2)

        s_lat_hemi.set("N" if lat >= 0 else "S")
        s_lon_hemi.set("E" if lon >= 0 else "W")

        e_s_lat_deg.delete(0, tk.END); e_s_lat_deg.insert(0, str(lat_d))
        e_s_lat_min.delete(0, tk.END); e_s_lat_min.insert(0, f"{lat_m:.2f}")
        e_s_lon_deg.delete(0, tk.END); e_s_lon_deg.insert(0, str(lon_d))
        e_s_lon_min.delete(0, tk.END); e_s_lon_min.insert(0, f"{lon_m:.2f}")
        
        messagebox.showinfo("GPS Sailaway", f"{LANGS[current_lang]['gps_updated']}\nLat: {lat_d}° {lat_m:.2f}' {s_lat_hemi.get()}\nLon: {lon_d}° {lon_m:.2f}' {s_lon_hemi.get()}")

    def locate_current_position():
        nonlocal current_boat_coords, theo_coords
        current_lang = lang_var.get()
        t = LANGS[current_lang]
        if not stored_route or len(stored_route["path"]) < 2:
            messagebox.showwarning(t["error_title"], "Veuillez lancer un routage d'abord." if current_lang == "FR" else "Please run a routing first.")
            return

        d_lat, d_lon = current_boat_coords if current_boat_coords else stored_route["path"][0]
        r_t0, r_n = stored_route["t0"], len(stored_route["path"])
        r_end = r_t0 + timedelta(hours=(r_n - 1) * stored_route["step"])
        r_fmt = "%Y-%m-%d %H:%M:%S"
        hint = (f"Route : T+000h = {r_t0.strftime(r_fmt)} UTC\nArrivée prévue : {r_end.strftime(r_fmt)} UTC" if current_lang == "FR"
                else f"Route: T+000h = {r_t0.strftime(r_fmt)} UTC\nPlanned arrival: {r_end.strftime(r_fmt)} UTC")
        dialog = BoatPosDialog(root, default_lat=d_lat, default_lon=d_lon, lang=current_lang, ask_time=True, time_hint=hint)
        root.wait_window(dialog)
        if dialog.result is None: return

        cur_lat, cur_lon = dialog.result
        when = dialog.when_utc or datetime.now(timezone.utc)
        try:
            info = locate_on_route(stored_route["path"], stored_route["step"], stored_route["t0"], (cur_lat, cur_lon), when)
        except Exception as e:
            messagebox.showerror(t["error_title"], str(e))
            return
        current_boat_coords = (cur_lat, cur_lon)
        theo_coords = info["theo"]
        track = add_track_point(cur_lat, cur_lon, when)      # enregistré dans config_routing.json

        # ⛵ sur la ligne du tableau la plus proche du bateau
        idx = min(info["nearest_idx"], len(stored_route_details) - 1)
        children = tree.get_children()
        for i, item in enumerate(children):
            if i >= len(stored_route_details): break
            vals = list(tree.item(item, 'values'))
            if vals:
                echeance_str = f"T+{stored_route_details[i]['hour']:03d}h"
                vals[2] = f"⛵ {echeance_str}" if i == idx else echeance_str
                tree.item(item, values=vals)
        if children:
            tree.selection_set(children[idx])
            tree.see(children[idx])

        report = position_report(info, (cur_lat, cur_lon), when, stored_route_details, current_lang, ref=stored_route, corridor=stored_route.get("corridor"))
        short = report["short"]
        def use_as_start():
            fill_start_fields(e_s_lat_deg, e_s_lat_min, e_s_lon_deg, e_s_lon_min, s_lat_hemi, s_lon_hemi, e_sim_start, cur_lat, cur_lon, when)

        show_position_popup(root, report, current_lang, on_use_as_start=use_as_start)

        # La carte est redessinée avec les deux positions (avant, elle était tracée avant la saisie)
        plt.close('all')
        plot_interactive_routing(stored_history, stored_route["path"], stored_route["path"][0], finish_coords,
                                 theoretical_pos=theo_coords, boat_pos=current_boat_coords, next_heading_info=short, lang=current_lang, track=track_points(track), corridor=stored_route.get("corridor"))

    def exit_application():
        plt.close('all')
        root.destroy()

    def build_gui():
        nonlocal main_container, e_s_lat_deg, e_s_lat_min, e_s_lon_deg, e_s_lon_min, e_f_lat_deg, e_f_lat_min, e_f_lon_deg, e_f_lon_min, e_timestep, e_steps, e_offset, e_sim_start, tree, e_corr
        for widget in main_container.winfo_children(): widget.destroy()

        current_lang = lang_var.get()
        t = LANGS[current_lang]
        root.title(t["title"])

        params_frame = tk.LabelFrame(main_container, text=t["params_frame"], font=("Arial", 10, "bold"))
        params_frame.pack(fill=tk.X, padx=5, pady=5)

        lang_frame = tk.Frame(params_frame)
        lang_frame.pack(fill="x", padx=10, pady=2)
        tk.Label(lang_frame, text=t["lang_label"], font=("Arial", 9, "bold")).pack(side=tk.LEFT)
        tk.Radiobutton(lang_frame, text="Français", variable=lang_var, value="FR", command=build_gui).pack(side=tk.LEFT, padx=5)
        tk.Radiobutton(lang_frame, text="English", variable=lang_var, value="EN", command=build_gui).pack(side=tk.LEFT, padx=5)

        polar_frame = tk.Frame(params_frame)
        polar_frame.pack(fill="x", padx=10, pady=2)
        tk.Label(polar_frame, text=t["polar_lbl"]).pack(side=tk.LEFT)
        tk.Entry(polar_frame, textvariable=polar_path_var, width=45).pack(side=tk.LEFT, padx=5)
        tk.Button(polar_frame, text=t["polar_btn"], command=browse_polar).pack(side=tk.LEFT)

        coords_container = tk.Frame(params_frame)
        coords_container.pack(fill="x", padx=10, pady=2)

        start_frame = tk.LabelFrame(coords_container, text=t["start_frame"], font=("Arial", 9, "bold"))
        start_frame.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        
        tk.Label(start_frame, text=t["lat_deg"]).grid(row=0, column=0, padx=2, pady=2)
        e_s_lat_deg = tk.Entry(start_frame, width=5, justify="center")
        e_s_lat_deg.insert(0, str(last_cfg.get("start_lat_deg", 50)))
        e_s_lat_deg.grid(row=0, column=1)
        tk.Label(start_frame, text=t["min"]).grid(row=0, column=2, padx=2)
        e_s_lat_min = tk.Entry(start_frame, width=6, justify="center")
        e_s_lat_min.insert(0, str(last_cfg.get("start_lat_min", 36.81)))
        e_s_lat_min.grid(row=0, column=3)
        tk.Radiobutton(start_frame, text="N", variable=s_lat_hemi, value="N").grid(row=0, column=4)
        tk.Radiobutton(start_frame, text="S", variable=s_lat_hemi, value="S").grid(row=0, column=5)

        tk.Label(start_frame, text=t["lon_deg"]).grid(row=1, column=0, padx=2, pady=2)
        e_s_lon_deg = tk.Entry(start_frame, width=5, justify="center")
        e_s_lon_deg.insert(0, str(last_cfg.get("start_lon_deg", 14)))
        e_s_lon_deg.grid(row=1, column=1)
        tk.Label(start_frame, text=t["min"]).grid(row=1, column=2, padx=2)
        e_s_lon_min = tk.Entry(start_frame, width=6, justify="center")
        e_s_lon_min.insert(0, str(last_cfg.get("start_lon_min", 12.83)))
        e_s_lon_min.grid(row=1, column=3)
        tk.Radiobutton(start_frame, text="E", variable=s_lon_hemi, value="E").grid(row=1, column=4)
        tk.Radiobutton(start_frame, text="W", variable=s_lon_hemi, value="W").grid(row=1, column=5)

        # Bouton d'import direct GPS Sailaway
        tk.Button(start_frame, text=t["get_boat_gps_btn"], command=import_sailaway_gps, bg="#00838f", fg="white", font=("Arial", 8, "bold")).grid(row=2, column=0, columnspan=6, sticky="ew", padx=2, pady=2)

        time_set_frame = tk.Frame(start_frame)
        time_set_frame.grid(row=3, column=0, columnspan=6, sticky="ew", padx=2, pady=(2, 2))
        tk.Label(time_set_frame, text="UTC:", font=("Arial", 8, "bold")).pack(side=tk.LEFT)
        e_sim_start = tk.Entry(time_set_frame, width=19, justify="center", font=("Arial", 9))
        e_sim_start.insert(0, str(last_cfg.get("sim_start_utc", datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S"))))
        e_sim_start.pack(side=tk.LEFT, padx=3)
        tk.Button(time_set_frame, text=t["set_time_btn"], command=set_simulation_time, bg="#1976d2", fg="white", font=("Arial", 8, "bold"), padx=5).pack(side=tk.LEFT)

        finish_frame = tk.LabelFrame(coords_container, text=t["finish_frame"], font=("Arial", 9, "bold"))
        finish_frame.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        tk.Label(finish_frame, text=t["lat_deg"]).grid(row=0, column=0, padx=2, pady=2)
        e_f_lat_deg = tk.Entry(finish_frame, width=5, justify="center")
        e_f_lat_deg.insert(0, str(last_cfg.get("finish_lat_deg", 16)))
        e_f_lat_deg.grid(row=0, column=1)
        tk.Label(finish_frame, text=t["min"]).grid(row=0, column=2, padx=2)
        e_f_lat_min = tk.Entry(finish_frame, width=6, justify="center")
        e_f_lat_min.insert(0, str(last_cfg.get("finish_lat_min", 14.4)))
        e_f_lat_min.grid(row=0, column=3)
        tk.Radiobutton(finish_frame, text="N", variable=f_lat_hemi, value="N").grid(row=0, column=4)
        tk.Radiobutton(finish_frame, text="S", variable=f_lat_hemi, value="S").grid(row=0, column=5)

        tk.Label(finish_frame, text=t["lon_deg"]).grid(row=1, column=0, padx=2, pady=2)
        e_f_lon_deg = tk.Entry(finish_frame, width=5, justify="center")
        e_f_lon_deg.insert(0, str(last_cfg.get("finish_lon_deg", 61)))
        e_f_lon_deg.grid(row=1, column=1)
        tk.Label(finish_frame, text=t["min"]).grid(row=1, column=2, padx=2)
        e_f_lon_min = tk.Entry(finish_frame, width=6, justify="center")
        e_f_lon_min.insert(0, str(last_cfg.get("finish_lon_min", 31.8)))
        e_f_lon_min.grid(row=1, column=3)
        tk.Radiobutton(finish_frame, text="E", variable=f_lon_hemi, value="E").grid(row=1, column=4)
        tk.Radiobutton(finish_frame, text="W", variable=f_lon_hemi, value="W").grid(row=1, column=5)

        time_frame = tk.Frame(params_frame)
        time_frame.pack(fill="x", padx=10, pady=5)
        tk.Label(time_frame, text=t["timestep"]).pack(side=tk.LEFT)
        e_timestep = tk.Entry(time_frame, width=5, justify="center")
        e_timestep.insert(0, str(last_cfg.get("time_step_hours", 3)))
        e_timestep.pack(side=tk.LEFT, padx=5)

        tk.Label(time_frame, text=t["steps"]).pack(side=tk.LEFT, padx=(10, 0))
        e_steps = tk.Entry(time_frame, width=6, justify="center")
        e_steps.insert(0, str(last_cfg.get("total_steps", 150)))
        e_steps.pack(side=tk.LEFT, padx=5)

        tk.Label(time_frame, text=t["offset"]).pack(side=tk.LEFT, padx=(10, 0))
        e_offset = tk.Entry(time_frame, width=5, justify="center")
        e_offset.insert(0, str(last_cfg.get("time_offset_hours", 3)))
        e_offset.pack(side=tk.LEFT, padx=5)

        tk.Label(time_frame, text=t["corridor_lbl"]).pack(side=tk.LEFT, padx=(10, 0))
        e_corr = tk.Entry(time_frame, width=5, justify="center")
        e_corr.insert(0, str(last_cfg.get("corridor_tol_h", 1.0)))
        e_corr.pack(side=tk.LEFT, padx=5)

        tk.Checkbutton(params_frame, text=t["force_grib"], variable=force_grib_var).pack(anchor="w", padx=10, pady=2)
        tk.Checkbutton(params_frame, text=t["avoid_land"], variable=land_var).pack(anchor="w", padx=10, pady=2)

        actions_frame = tk.Frame(params_frame)
        actions_frame.pack(fill="x", padx=10, pady=5)

        def on_run():
            nonlocal stored_route_details, stored_route, stored_history, finish_coords, current_boat_coords, theo_coords
            try:
                p_file = polar_path_var.get().strip()
                if not os.path.exists(p_file): raise FileNotFoundError(f"{t['polar_missing']} {p_file}")

                s_lat = (float(e_s_lat_deg.get().strip()) + float(e_s_lat_min.get().strip()) / 60.0) * (-1 if s_lat_hemi.get() == "S" else 1)
                s_lon = (float(e_s_lon_deg.get().strip()) + float(e_s_lon_min.get().strip()) / 60.0) * (-1 if s_lon_hemi.get() == "W" else 1)
                f_lat = (float(e_f_lat_deg.get().strip()) + float(e_f_lat_min.get().strip()) / 60.0) * (-1 if f_lat_hemi.get() == "S" else 1)
                f_lon = (float(e_f_lon_deg.get().strip()) + float(e_f_lon_min.get().strip()) / 60.0) * (-1 if f_lon_hemi.get() == "W" else 1)

                finish_coords, t_step, tot_steps, offset_val = (f_lat, f_lon), int(e_timestep.get().strip()), int(e_steps.get().strip()), int(e_offset.get().strip())
                sim_start_str = e_sim_start.get().strip()
                try:
                    base_time = datetime.strptime(sim_start_str, "%Y-%m-%d %H:%M:%S").replace(tzinfo=timezone.utc)
                except ValueError:
                    base_time = datetime.strptime(sim_start_str, "%Y-%m-%d %H:%M").replace(tzinfo=timezone.utc)
                    sim_start_str = base_time.strftime("%Y-%m-%d %H:%M:%S")

                save_config({
                    "polar_file": p_file,
                    "start_lat_deg": float(e_s_lat_deg.get().strip()), "start_lat_min": float(e_s_lat_min.get().strip()), "start_lat_hemi": s_lat_hemi.get(),
                    "start_lon_deg": float(e_s_lon_deg.get().strip()), "start_lon_min": float(e_s_lon_min.get().strip()), "start_lon_hemi": s_lon_hemi.get(),
                    "finish_lat_deg": float(e_f_lat_deg.get().strip()), "finish_lat_min": float(e_f_lat_min.get().strip()), "finish_lat_hemi": f_lat_hemi.get(),
                    "finish_lon_deg": float(e_f_lon_deg.get().strip()), "finish_lon_min": float(e_f_lon_min.get().strip()), "finish_lon_hemi": f_lon_hemi.get(),
                    "time_step_hours": t_step, "total_steps": tot_steps, "time_offset_hours": offset_val,
                    "sim_start_utc": sim_start_str, "language": current_lang, "avoid_land": land_var.get(), "corridor_tol_h": _parse_tol(e_corr.get())
                })

                root.config(cursor="watch"); root.update()
                ds_grib = download_gfs_forecast(12.0, 55.0, -68.0, 0.0, base_time, max_hours=t_step * tot_steps + abs(offset_val) + 12, step_hours=6, force_download=force_grib_var.get())
                polar_interp = load_polar(p_file)
                
                land_test = None
                if land_var.get():
                    try:
                        land_test = make_land_test(12.0, 55.0, -68.0, 0.0, res_deg=0.05, margin_nm=5.0)
                    except Exception as e:
                        messagebox.showwarning(t["error_title"], f"{t['no_coast']}\n{e}")
                history, optimal_route = run_isochrone_routing(p_file, ds_grib, base_time, (s_lat, s_lon), (f_lat, f_lon), time_step_hours=t_step, total_steps=tot_steps, time_offset_hours=offset_val, land_test=land_test)
                export_to_gpx(optimal_route, "route_optimale.gpx")
                corridor = None
                corr_tol = _parse_tol(e_corr.get())
                if corr_tol > 0:
                    try:
                        geom = compute_corridor(p_file, ds_grib, base_time, (s_lat, s_lon), (f_lat, f_lon), history, optimal_route, t_step, offset_val, corr_tol, land_test=land_test)
                        corridor = {"geom": geom, "tol_h": corr_tol} if geom is not None else None
                        if corridor is None:
                            messagebox.showwarning(t["error_title"], t["corr_unreached"])
                    except Exception as e:
                        messagebox.showwarning(t["error_title"], f"{t['corr_calc_error']}\n{e}")
                stored_route_details = analyze_route_performance(optimal_route, ds_grib, base_time, polar_interp, t_step, time_offset_hours=offset_val)
                stored_route = {"path": optimal_route, "step": t_step, "t0": base_time, "sim_start": base_time, "offset_h": offset_val, "corridor": corridor}
                stored_history = history
                theo_coords = None

                for row in tree.get_children(): tree.delete(row)
                for rd in stored_route_details:
                    tree.insert("", tk.END, values=(rd['utc'], rd['local'], f"T+{rd['hour']:03d}h", f"{rd['lat']:.2f}°", f"{rd['lon']:.2f}°", f"{rd['tws']:.1f}", f"{rd['twd']:.0f}°", f"{rd['twa']:.0f}°", f"{rd['bsp']:.1f}"))
                if stored_route_details:
                    last = stored_route_details[-1]
                    tree.insert("", tk.END, values=("-", "-", t["arrival"], f"{last['lat']:.2f}°", f"{last['lon']:.2f}°", "-", "-", "-", "-"))

                root.config(cursor="")
                messagebox.showinfo(t["success"], t["routing_done"])
                
                tws_init, twd_init = WindField(ds_grib).get(s_lat, s_lon, base_time + timedelta(hours=offset_val))
                twa_init = abs(compute_bearing(s_lat, s_lon, f_lat, f_lon) - twd_init[0]) % 360
                bsp_theo = polar_interp([360 - twa_init if twa_init > 180 else twa_init, tws_init[0]])[0]
                info_texte = (f"Départ: {s_lat:.2f}°, {s_lon:.2f}°\nVitesse Polaire: {bsp_theo:.1f} nds\nVent GFS: {tws_init[0]:.1f} nds du {twd_init[0]:.0f}°" if current_lang == "FR"
                              else f"Start: {s_lat:.2f}°, {s_lon:.2f}°\nPolar speed: {bsp_theo:.1f} kts\nGFS wind: {tws_init[0]:.1f} kts from {twd_init[0]:.0f}°")
                
                plot_interactive_routing(history, optimal_route, (s_lat, s_lon), (f_lat, f_lon), theoretical_pos=theo_coords, boat_pos=current_boat_coords, next_heading_info=info_texte, lang=current_lang, track=track_points(load_track()), corridor=corridor)
            except Exception as e:
                root.config(cursor="")
                messagebox.showerror(t["error_title"], f"{t['routing_error']}\n{e}")

        tk.Button(actions_frame, text=t["run_btn"], command=on_run, bg="#2e7d32", fg="white", font=("Arial", 10, "bold")).pack(side=tk.LEFT, expand=True, fill=tk.X, padx=3)
        tk.Button(actions_frame, text=t["where_btn"], command=locate_current_position, bg="#1976d2", fg="white", font=("Arial", 10, "bold")).pack(side=tk.LEFT, expand=True, fill=tk.X, padx=3)
        tk.Button(actions_frame, text=t["track_btn"], command=lambda: show_track_manager(root, current_lang), bg="#6a1b9a", fg="white", font=("Arial", 10, "bold")).pack(side=tk.LEFT, expand=True, fill=tk.X, padx=3)
        tk.Button(actions_frame, text=t["exit_btn"], command=exit_application, bg="#c62828", fg="white", font=("Arial", 10, "bold")).pack(side=tk.LEFT, expand=True, fill=tk.X, padx=3)

        results_frame = tk.LabelFrame(main_container, text=t["results_title"], font=("Arial", 10, "bold"))
        results_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        cols = ("utc", "local", "hour", "lat", "lon", "tws", "twd", "twa", "bsp")
        tree = ttk.Treeview(results_frame, columns=cols, show="headings", height=8)
        for col in cols: tree.heading(col, text=t[f"col_{col}"])
        tree.column("utc", width=140, anchor="center")
        tree.column("local", width=140, anchor="center")
        tree.column("hour", width=75, anchor="center")
        tree.column("lat", width=80, anchor="center")
        tree.column("lon", width=80, anchor="center")
        tree.column("tws", width=75, anchor="center")
        tree.column("twd", width=70, anchor="center")
        tree.column("twa", width=70, anchor="center")
        tree.column("bsp", width=75, anchor="center")

        scrollbar = ttk.Scrollbar(results_frame, orient=tk.VERTICAL, command=tree.yview)
        tree.configure(yscrollcommand=scrollbar.set)
        tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

    build_gui()
    root.mainloop()

if __name__ == "__main__":
    run_gui_application()
