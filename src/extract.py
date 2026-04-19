import os
import io
import json
import hashlib
from pathlib import Path
from datetime import datetime, timedelta

import pandas as pd
import requests
from dotenv import load_dotenv

load_dotenv()

DATA_URL = os.getenv("DATA_URL")
DATA_FORMAT = os.getenv("DATA_FORMAT", "csv").lower()
CHECK_INTERVAL_MINUTES = int(os.getenv("CHECK_INTERVAL_MINUTES", "15"))

DATA_DIR = Path("data")
LOCAL_FILE = DATA_DIR / "trafico_ani.csv"
META_FILE = DATA_DIR / "sync_meta.json"


def _now_iso() -> str:
    return datetime.now().isoformat()


def _read_meta() -> dict:
    if META_FILE.exists():
        try:
            with open(META_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}


def _write_meta(meta: dict) -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    with open(META_FILE, "w", encoding="utf-8") as f:
        json.dump(meta, f, ensure_ascii=False, indent=2)


def _hash_bytes(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


def _fetch_remote_df() -> pd.DataFrame:
    if not DATA_URL:
        raise ValueError("Falta DATA_URL en el archivo .env")

    response = requests.get(DATA_URL, timeout=60)
    response.raise_for_status()

    if DATA_FORMAT == "csv":
        df = pd.read_csv(io.BytesIO(response.content))
    elif DATA_FORMAT == "json":
        data = response.json()
        df = pd.DataFrame(data)
    else:
        raise ValueError("DATA_FORMAT debe ser 'csv' o 'json'")

    if df.empty:
        raise ValueError("La fuente devolvió un dataset vacío.")

    return df


def _df_to_csv_bytes(df: pd.DataFrame) -> bytes:
    return df.to_csv(index=False).encode("utf-8")


def sync_data(force: bool = False) -> dict:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    meta = _read_meta()

    last_check_str = meta.get("last_check")
    if not force and CHECK_INTERVAL_MINUTES > 0 and last_check_str:
        try:
            last_check = datetime.fromisoformat(last_check_str)
            next_check = last_check + timedelta(minutes=CHECK_INTERVAL_MINUTES)
            if datetime.now() < next_check and LOCAL_FILE.exists():
                return {
                    "checked": False,
                    "updated": False,
                    "message": "Se omitió la revisión por intervalo.",
                    "last_check": meta.get("last_check"),
                    "last_update": meta.get("last_update"),
                    "rows": meta.get("rows", 0),
                }
        except Exception:
            pass

    df_remote = _fetch_remote_df()
    remote_csv_bytes = _df_to_csv_bytes(df_remote)
    remote_hash = _hash_bytes(remote_csv_bytes)

    local_hash = None
    if LOCAL_FILE.exists():
        try:
            with open(LOCAL_FILE, "rb") as f:
                local_hash = _hash_bytes(f.read())
        except Exception:
            local_hash = None

    updated = (not LOCAL_FILE.exists()) or (remote_hash != local_hash)

    if updated:
        with open(LOCAL_FILE, "wb") as f:
            f.write(remote_csv_bytes)

    new_meta = {
        "data_url": DATA_URL,
        "data_format": DATA_FORMAT,
        "last_check": _now_iso(),
        "last_update": _now_iso() if updated else meta.get("last_update"),
        "rows": int(len(df_remote)),
        "hash": remote_hash,
    }
    _write_meta(new_meta)

    return {
        "checked": True,
        "updated": updated,
        "message": "CSV local actualizado." if updated else "No hubo cambios en la fuente.",
        "last_check": new_meta["last_check"],
        "last_update": new_meta["last_update"],
        "rows": new_meta["rows"],
    }


def load_data(auto_sync: bool = True) -> pd.DataFrame:
    if auto_sync:
        sync_data(force=False)

    if not LOCAL_FILE.exists():
        sync_data(force=True)

    try:
        df = pd.read_csv(LOCAL_FILE)
    except pd.errors.EmptyDataError:
        sync_data(force=True)
        df = pd.read_csv(LOCAL_FILE)

    if df.empty:
        sync_data(force=True)
        df = pd.read_csv(LOCAL_FILE)

    return df


def get_sync_info() -> dict:
    return _read_meta()