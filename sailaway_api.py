#!/usr/bin/env python3
"""
sailaway_api.py - meteo reelle du jeu Sailaway III.

Endpoint (documente dans SailawayAPI.pdf, archive sur web.archive.org) :

    https://backend.sailaway.world/cgi-bin/sailaway/getenvironment.pl?lat=<lat>&lon=<lon>

Il renvoie l'etat meteo **courant** du jeu au point demande (pas de prevision) :
vent (composantes u/v, vitesse en m/s, direction), courant, vagues, pression,
temperature, nuages, brouillard, pluie.

Toutes les valeurs sont converties en noeuds / degres dans les fonctions ci-dessous.

La doc demande de ne pas appeler l'API plus d'une fois toutes les 10 minutes :
les grilles sont mises en cache dans sailaway_cache.json et reutilisees tant
qu'elles ont moins de MIN_INTERVAL_MIN minutes.
"""

from __future__ import annotations

import json
import math
import os
import time
from datetime import datetime, timezone

import requests

MPS_TO_KT = 1.9438444924406
BASE_URL = "https://backend.sailaway.world/cgi-bin/sailaway/getenvironment.pl"
CACHE_FILE = "sailaway_cache.json"
MIN_INTERVAL_MIN = 10.0


# --------------------------------------------------------------------------- #
#  Un point
# --------------------------------------------------------------------------- #
def get_environment(lat, lon, timeout=15, session=None):
    """Meteo du jeu au point (lat, lon). None si indisponible.

    Retourne un dict : tws_kt, twd_deg, u_kt, v_kt, cur_u_kt, cur_v_kt,
    pressure, temperature, waveheight, lat, lon.
    """
    get = session.get if session is not None else requests.get
    try:
        r = get(BASE_URL, params={"lat": f"{float(lat):.3f}", "lon": f"{float(lon):.3f}"},
                timeout=timeout)
        r.raise_for_status()
        env = r.json()["environment"]
    except Exception:
        return None
    if "windspeed" not in env:
        return None
    u = float(env.get("windu", 0.0)) * MPS_TO_KT
    v = float(env.get("windv", 0.0)) * MPS_TO_KT
    return {
        "lat": float(env.get("lat", lat)), "lon": float(env.get("lon", lon)),
        "tws_kt": float(env["windspeed"]) * MPS_TO_KT,
        "twd_deg": float(env.get("winddir", (270.0 - math.degrees(math.atan2(v, u))) % 360.0)),
        "u_kt": u, "v_kt": v,
        "cur_u_kt": float(env.get("curu", 0.0)) * MPS_TO_KT,
        "cur_v_kt": float(env.get("curv", 0.0)) * MPS_TO_KT,
        "pressure": float(env.get("pressure", 0.0)),
        "temperature": float(env.get("temperature", 0.0)),
        "waveheight": float(env.get("waveheight", 0.0)),
    }


# --------------------------------------------------------------------------- #
#  Cache disque
# --------------------------------------------------------------------------- #
def _load_cache(path=CACHE_FILE):
    try:
        with open(path, encoding="utf-8") as fh:
            return json.load(fh)
    except Exception:
        return None


def _save_cache(data, path=CACHE_FILE):
    try:
        with open(path, "w", encoding="utf-8") as fh:
            json.dump(data, fh, indent=2)
    except Exception:
        pass


def _cache_age_min(cache):
    try:
        t = datetime.strptime(cache["utc"], "%Y-%m-%d %H:%M:%S").replace(tzinfo=timezone.utc)
        return (datetime.now(timezone.utc) - t).total_seconds() / 60.0
    except Exception:
        return 1e9


# --------------------------------------------------------------------------- #
#  Grille de points autour du bateau
# --------------------------------------------------------------------------- #
def get_grid(lat, lon, span_deg=0.5, step_deg=0.5, min_interval_min=MIN_INTERVAL_MIN,
             force=False, path=CACHE_FILE, session=None, pause=0.25, progress=None):
    """Grille (3x3 par defaut) de meteo du jeu autour de (lat, lon).

    Retourne {"utc":..., "points":[{lat, lon, tws_kt, twd_deg, ...}, ...], "cached": bool}.
    Reutilise le cache si la derniere grille date de moins de min_interval_min.
    """
    cache = _load_cache(path)
    if (not force and cache is not None
            and abs(cache.get("lat", 1e9) - lat) < 0.3 and abs(cache.get("lon", 1e9) - lon) < 0.3
            and abs(cache.get("span", 0) - span_deg) < 1e-9
            and _cache_age_min(cache) < min_interval_min):
        cache["cached"] = True
        return cache

    offsets = [-span_deg, 0.0, span_deg] if step_deg >= span_deg else \
        [(-span_deg + i * step_deg) for i in range(int(round(2 * span_deg / step_deg)) + 1)]
    points, t0 = [], time.time()
    total = len(offsets) ** 2
    for dlat in offsets:
        for dlon in offsets:
            p = get_environment(lat + dlat, lon + dlon, session=session)
            if p is not None:
                points.append(p)
            if progress is not None:
                progress(len(points), total)
            if session is None:
                time.sleep(pause)
    if not points:
        return None
    data = {"utc": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S"),
            "lat": float(lat), "lon": float(lon), "span": float(span_deg),
            "points": points, "cached": False, "seconds": round(time.time() - t0, 1)}
    _save_cache(data, path)
    return data


def available(timeout=6):
    """Test rapide de disponibilite de l'API (un point au large)."""
    return get_environment(45.0, -20.0, timeout=timeout) is not None


# --------------------------------------------------------------------------- #
#  Auto-test
# --------------------------------------------------------------------------- #
if __name__ == "__main__":
    print("Test de l'API Sailaway...")
    p = get_environment(46.39, -28.08)
    if p is None:
        print("  indisponible")
        raise SystemExit(1)
    print(f"  vent : {p['tws_kt']:.2f} nds du {p['twd_deg']:.1f} deg "
          f"(u {p['u_kt']:+.2f} / v {p['v_kt']:+.2f} nds)")
    print(f"  courant : {p['cur_u_kt']:+.2f} / {p['cur_v_kt']:+.2f} nds "
          f"({math.hypot(p['cur_u_kt'], p['cur_v_kt']):.2f} nds)")
    print(f"  pression {p['pressure']:.1f} hPa, {p['temperature']:.1f} C")
    g = get_grid(46.39, -28.08, force=True)
    if g:
        print(f"\n  grille {len(g['points'])} points, {g['seconds']} s, cache={g['cached']}")
        for q in g["points"]:
            print(f"    {q['lat']:6.2f}/{q['lon']:7.2f} : {q['tws_kt']:5.2f} nds / {q['twd_deg']:5.1f} deg")
