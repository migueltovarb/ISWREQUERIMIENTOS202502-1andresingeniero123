#!/usr/bin/env python3
"""
monitor_ip_async.py
Monitorea una IP consultando múltiples servicios de geolocalización públicos,
guarda el historial en SQLite y notifica cambios por Telegram (preferido) o email.
Diseño: asyncio, aiohttp, backoff exponencial, deduplicación.
"""

import os
from dotenv import load_dotenv
load_dotenv()
import asyncio
import aiohttp
import aiosqlite
import json
import time
from datetime import datetime
from typing import Dict, Any, List, Optional
import smtplib
from email.message import EmailMessage
import math

# ---------------------------
# Configuración via ENV VARS
# ---------------------------
IP_TO_MONITOR = os.getenv("MONITOR_IP", "190.130.109.115")
CHECK_INTERVAL = int(os.getenv("CHECK_INTERVAL_SEC", str(60*60)))  # por defecto 1 hora
DB_PATH = os.getenv("DB_PATH", "monitor_ip.db")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")  # si no está, no enviará Telegram
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
SMTP_HOST = os.getenv("SMTP_HOST")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USER = os.getenv("SMTP_USER")
SMTP_PASS = os.getenv("SMTP_PASS")
ALERT_EMAIL = os.getenv("ALERT_EMAIL")  # email destino si se usa email
# Timeout y reintentos
HTTP_TIMEOUT = int(os.getenv("HTTP_TIMEOUT_SEC", "15"))
MAX_RETRIES = int(os.getenv("MAX_RETRIES", "3"))

# ---------------------------
# Utilidades
# ---------------------------
now_iso = lambda: datetime.utcnow().isoformat() + "Z"

def normalize_result(data: Dict[str, Any]) -> Dict[str, Any]:
    """Extrae campos relevantes y normaliza tipos."""
    return {
        "query": str(data.get("query") or data.get("ip") or ""),
        "country": data.get("country") or data.get("countryName") or None,
        "region": data.get("regionName") or data.get("region") or None,
        "city": data.get("city") or None,
        "lat": float(data.get("lat")) if data.get("lat") not in (None, "") else None,
        "lon": float(data.get("lon")) if data.get("lon") not in (None, "") else None,
        "isp": data.get("isp") or data.get("org") or None,
        "as": data.get("as") or data.get("asn") or None,
    }

def consensus(results: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Calcula una 'votación' simple por cada campo para encontrar el valor más frecuente.
       Para lat/lon hace media ponderada ignorando None."""
    out = {}
    keys = ["query","country","region","city","isp","as"]
    for k in keys:
        votes = [r.get(k) for r in results if r.get(k)]
        out[k] = max(set(votes), key=votes.count) if votes else None

    # lat/lon: promediar valores numéricos (descartar outliers sencillos)
    lats = [r["lat"] for r in results if isinstance(r.get("lat"), (int,float))]
    lons = [r["lon"] for r in results if isinstance(r.get("lon"), (int,float))]
    if lats and lons:
        # simple trimmed mean para evitar valores atípicos
        def trimmed_mean(arr):
            arr_sorted = sorted(arr)
            n = len(arr_sorted)
            if n <= 2: return sum(arr_sorted)/n
            trim = max(1, n//6)  # recorta extremos si hay suficientes
            trimmed = arr_sorted[trim: n-trim]
            return sum(trimmed)/len(trimmed)
        out["lat"] = float(trimmed_mean(lats))
        out["lon"] = float(trimmed_mean(lons))
    else:
        out["lat"] = None
        out["lon"] = None

    return out

# ---------------------------
# Proveedores (async)
# ---------------------------
async def fetch_ip_api(session: aiohttp.ClientSession, ip: str) -> Dict[str, Any]:
    url = f"http://ip-api.com/json/{ip}?fields=status,message,country,regionName,city,lat,lon,isp,as,query"
    async with session.get(url, timeout=HTTP_TIMEOUT) as r:
        return await r.json()

async def fetch_ipinfo(session: aiohttp.ClientSession, ip: str, token: Optional[str]) -> Dict[str, Any]:
    if not token:
        return {}
    url = f"https://ipinfo.io/{ip}/json"
    headers = {"Authorization": f"Bearer {token}"}
    async with session.get(url, headers=headers, timeout=HTTP_TIMEOUT) as r:
        return await r.json()

async def fetch_dbip(session: aiohttp.ClientSession, ip: str, token: Optional[str]) -> Dict[str, Any]:
    # db-ip requires token for full data, but hay endpoints limitados.
    url = f"https://api.db-ip.com/v2/free/{ip}"
    async with session.get(url, timeout=HTTP_TIMEOUT) as r:
        try:
            return await r.json()
        except:
            return {}

PROVIDERS = [
    ("ip-api", fetch_ip_api),
    ("ipinfo", fetch_ipinfo),
    ("db-ip", fetch_dbip),
]

# ---------------------------
# Notificaciones
# ---------------------------
async def notify_telegram(message: str):
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        return False
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {"chat_id": TELEGRAM_CHAT_ID, "text": message}
    async with aiohttp.ClientSession() as s:
        async with s.post(url, data=payload, timeout=HTTP_TIMEOUT) as r:
            return r.status == 200

def notify_email_sync(subject: str, body: str):
    if not (SMTP_HOST and SMTP_USER and SMTP_PASS and ALERT_EMAIL):
        return False
    msg = EmailMessage()
    msg["From"] = SMTP_USER
    msg["To"] = ALERT_EMAIL
    msg["Subject"] = subject
    msg.set_content(body)
    with smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=30) as s:
        s.starttls()
        s.login(SMTP_USER, SMTP_PASS)
        s.send_message(msg)
    return True

# ---------------------------
# DB: SQLite helpers
# ---------------------------
async def init_db():
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""CREATE TABLE IF NOT EXISTS checks (
            id INTEGER PRIMARY KEY,
            ts TEXT,
            ip TEXT,
            country TEXT,
            region TEXT,
            city TEXT,
            lat REAL,
            lon REAL,
            isp TEXT,
            asn TEXT
        )""")
        await db.execute("""CREATE TABLE IF NOT EXISTS events (
            id INTEGER PRIMARY KEY,
            ts TEXT,
            ip TEXT,
            change_json TEXT
        )""")
        await db.commit()

async def get_last_entry(ip: str) -> Optional[Dict[str, Any]]:
    async with aiosqlite.connect(DB_PATH) as db:
        cur = await db.execute("SELECT ts,country,region,city,lat,lon,isp,asn FROM checks WHERE ip=? ORDER BY id DESC LIMIT 1", (ip,))
        row = await cur.fetchone()
        if not row:
            return None
        ts,country,region,city,lat,lon,isp,asn = row
        return {"ts":ts,"country":country,"region":region,"city":city,"lat":lat,"lon":lon,"isp":isp,"as":asn}

async def save_check(ip: str, result: Dict[str, Any]):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT INTO checks (ts,ip,country,region,city,lat,lon,isp,asn) VALUES (?,?,?,?,?,?,?,?,?)",
            (now_iso(), ip, result.get("country"), result.get("region"),
             result.get("city"), result.get("lat"), result.get("lon"),
             result.get("isp"), result.get("as"))
        )
        await db.commit()

async def save_event(ip: str, change: Dict[str, Any]):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT INTO events (ts,ip,change_json) VALUES (?,?,?)",
            (now_iso(), ip, json.dumps(change, ensure_ascii=False))
        )
        await db.commit()

# ---------------------------
# Lógica principal
# ---------------------------
async def query_providers(ip: str, session: aiohttp.ClientSession) -> List[Dict[str, Any]]:
    tasks = []
    token_ipinfo = os.getenv("IPINFO_TOKEN")
    for name, func in PROVIDERS:
        if name == "ipinfo":
            tasks.append(func(session, ip, token_ipinfo))
        else:
            tasks.append(func(session, ip))
    results_raw = await asyncio.gather(*tasks, return_exceptions=True)
    results = []
    for r in results_raw:
        if isinstance(r, Exception) or not r:
            continue
        norm = normalize_result(r)
        results.append(norm)
    return results

def diff(prev: Optional[Dict[str, Any]], current: Dict[str, Any]) -> Dict[str, Any]:
    if not prev:
        return current
    changes = {}
    for k in ["country","region","city","lat","lon","isp","as"]:
        pv = prev.get(k) if prev else None
        cv = current.get(k)
        # para floats, comparar con tolerancia (ej. 0.01 deg ~ 1km)
        if isinstance(cv, float) and isinstance(pv, float):
            if math.hypot((cv - pv), 0) > 0.01:  # tunable threshold
                changes[k] = {"old":pv,"new":cv}
        else:
            if pv != cv:
                changes[k] = {"old":pv,"new":cv}
    return changes

async def monitor_loop():
    await init_db()
    last = await get_last_entry(IP_TO_MONITOR)
    async with aiohttp.ClientSession() as session:
        while True:
            try:
                results = await query_providers(IP_TO_MONITOR, session)
                if not results:
                    # si no obtuvimos nada, esperar y continuar
                    await asyncio.sleep(min(60, CHECK_INTERVAL))
                    continue

                current = consensus(results)
                await save_check(IP_TO_MONITOR, current)
                changes = diff(last, {
                    "country": current.get("country"),
                    "region": current.get("region"),
                    "city": current.get("city"),
                    "lat": current.get("lat"),
                    "lon": current.get("lon"),
                    "isp": current.get("isp"),
                    "as": current.get("as"),
                })
                if changes:
                    event = {
                        "ip": IP_TO_MONITOR,
                        "time": now_iso(),
                        "changes": changes,
                        "raw_results": results
                    }
                    await save_event(IP_TO_MONITOR, event)
                    # Formatea mensaje
                    msg_lines = [f"Alerta: cambios detectados para IP {IP_TO_MONITOR} ({now_iso()})"]
                    for k,v in changes.items():
                        msg_lines.append(f"- {k}: {v['old']} -> {v['new']}")
                    msg_lines.append("\nFuente (consenso) 🙋:")
                    msg_lines.append(json.dumps(current, ensure_ascii=False, indent=2))
                    msg = "\n".join(msg_lines)

                    sent = False
                    if TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID:
                        sent = await notify_telegram(msg)
                    if not sent and SMTP_HOST and ALERT_EMAIL:
                        # fallback sync (rápido)
                        notify_email_sync(f"Alerta IP {IP_TO_MONITOR}", msg)
                    last = {
                        "country": current.get("country"),
                        "region": current.get("region"),
                        "city": current.get("city"),
                        "lat": current.get("lat"),
                        "lon": current.get("lon"),
                        "isp": current.get("isp"),
                        "as": current.get("as"),
                    }
                # Espera con jitter para evitar patrones
                jitter = int(min(60, CHECK_INTERVAL * 0.05))
                await asyncio.sleep(CHECK_INTERVAL + (jitter and (jitter * (0 if os.urandom(1)[0] < 128 else 1))))
            except Exception as e:
                print(f"[{now_iso()}] Error principal: {e}")
                await asyncio.sleep(30)

if __name__ == "__main__":
    asyncio.run(monitor_loop())
