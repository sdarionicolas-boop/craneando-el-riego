# alerts/telegram.py
"""
Módulo para el envío de alertas automáticas vía Telegram.
Anticipa cruzamientos de umbral de estrés con 48-72h de margen.
"""

import os
import requests
import datetime

# Para desarrollo/pruebas, se pueden definir aquí o cargar de variables de entorno
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", None)
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID", None)

def send_telegram_message(text: str) -> bool:
    """Envia un mensaje enriquecido a un chat/canal de Telegram."""
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print(f"[TELEGRAM ALERT SIMULATOR] (Sin token de BOT configurado):\n{text}\n")
        return False
        
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": text,
        "parse_mode": "Markdown"
    }
    
    try:
        response = requests.post(url, json=payload, timeout=5)
        if response.status_code == 200:
            print("[TELEGRAM ALERT] Mensaje enviado exitosamente.")
            return True
        else:
            print(f"[TELEGRAM ALERT] Fallo al enviar: {response.text}")
            return False
    except Exception as e:
        print(f"[TELEGRAM ALERT] Error en petición a Telegram: {e}")
        return False


def check_and_send_alerts(lote: str, df_proj, eval_date, lamina_rec: float, tiempo_horas: float) -> bool:
    """
    Analiza la proyección a 7 días y envía una alerta si se detecta
    un cruzamiento inminente del umbral de estrés en las próximas 48-72hs.
    """
    alert_triggered = False
    target_row = None
    
    # Buscar cruzamiento en los primeros 3 días de proyección (48-72h)
    for idx, row in df_proj.head(3).iterrows():
        if row["au_riego"] < row["umbral"]:
            alert_triggered = True
            target_row = row
            break
            
    if alert_triggered and target_row is not None:
        proj_date = target_row["fecha"]
        proj_au = target_row["au_riego"]
        proj_umbral = target_row["umbral"]
        dias = (proj_date - eval_date).days
        
        mensaje = (
            f"⚠️ *ALERTA RIEGO CRÍTICA - LOTE {lote.upper()}*\n\n"
            f"Se proyecta que el nivel de Agua Útil cruzará el umbral de estrés en *{dias} días* ({proj_date.strftime('%d/%m')}).\n\n"
            f"📈 *Valores Proyectados:*\n"
            f"- Agua Útil Proyectada: {proj_au:.1f} mm\n"
            f"- Umbral de Estrés: {proj_umbral:.1f} mm\n\n"
            f"💧 *Recomendación Agronómica:*\n"
            f"- Lámina sugerida: *{lamina_rec:.1f} mm*\n"
            f"- Tiempo estimado de pivote: *{tiempo_horas:.1f} horas*\n\n"
            f"_Alerta generada automáticamente por Craneando el Riego v1.0._"
        )
        return send_telegram_message(mensaje)
        
    return False
