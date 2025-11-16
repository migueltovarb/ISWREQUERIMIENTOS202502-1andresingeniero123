# monitor_ip.py
# Requiere: requests, smtplib, email.message
# Uso: python monitor_ip.py 190.130.109.115

import sys, time, json
import requests
from email.message import EmailMessage
import smtplib

IP = sys.argv[1] if len(sys.argv)>1 else "190.130.109.115"
CHECK_INTERVAL = 60*60  # segundos entre comprobaciones (ej. 1 hora)
API_URL = f"http://ip-api.com/json/{IP}?fields=status,country,regionName,city,lat,lon,isp,as,query"

# Configura tu correo (Gmail requiere app password o SMTP seguro)
SMTP_HOST = "smtp.gmail.com"
SMTP_PORT = 587
SMTP_USER = "tu.email@gmail.com"
SMTP_PASS = "TU_PASSWORD_APP"
TO_EMAIL = "tu.email@gmail.com"

def send_email(subject, body):
    msg = EmailMessage()
    msg["From"] = SMTP_USER
    msg["To"] = TO_EMAIL
    msg["Subject"] = subject
    msg.set_content(body)
    with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as s:
        s.starttls()
        s.login(SMTP_USER, SMTP_PASS)
        s.send_message(msg)

def fetch():
    r = requests.get(API_URL, timeout=10)
    return r.json()

def main():
    last = None
    try:
        while True:
            data = fetch()
            if data.get("status") != "success":
                print("Error API:", data)
            else:
                simplified = {
                    "query": data.get("query"),
                    "country": data.get("country"),
                    "region": data.get("regionName"),
                    "city": data.get("city"),
                    "lat": data.get("lat"),
                    "lon": data.get("lon"),
                    "isp": data.get("isp"),
                    "as": data.get("as"),
                }
                if simplified != last:
                    body = "Cambio detectado en geolocalización para IP {}\n\n{}".format(IP, json.dumps(simplified, indent=2))
                    print(body)
                    send_email(f"Alerta: cambio IP {IP}", body)
                    last = simplified
            time.sleep(CHECK_INTERVAL)
    except KeyboardInterrupt:
        print("Detenido por usuario.")

if __name__ == "__main__":
    main()
