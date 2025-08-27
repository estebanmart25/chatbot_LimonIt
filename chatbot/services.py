# chatbot/services.py
import logging
import requests
from dotenv import load_dotenv
from twilio.rest import Client
from twilio.base.exceptions import TwilioRestException, TwilioException
import os

load_dotenv()

# --- Configuración de Twilio ---
TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID")
TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")
TWILIO_WHATSAPP_NUMBER = os.getenv("TWILIO_WHATSAPP_NUMBER")
twilio_client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN) if TWILIO_ACCOUNT_SID and TWILIO_AUTH_TOKEN else None

# --- Configuración de Chatwoot ---
CW_BASE = os.getenv("CHATWOOT_URL", "https://app.chatwoot.com").rstrip("/")
CW_TOKEN = os.getenv("CHATWOOT_API_TOKEN")
CW_ACC = os.getenv("CHATWOOT_ACCOUNT_ID")
CW_INBOX = os.getenv("CHATWOOT_INBOX_ID")
CW_HEADERS = {"api_access_token": CW_TOKEN, "Content-Type": "application/json"}

# --- Funciones de Servicio ---

# chatbot/services.py



def send_message(to: str, body: str) -> bool:
    """
    Envía un mensaje por WhatsApp vía Twilio si está habilitado.
    Si hay restricciones (Sandbox, Trial), se imprime el mensaje en la consola.
    Devuelve True si el envío fue exitoso o simulado, False si falló.
    """
    # Verificar si Twilio está habilitado en la configuración
    is_twilio_enabled = str(os.getenv("TWILIO_ENABLED", "false")).lower() == "true"

    if not twilio_client or not is_twilio_enabled:
        logging.info("--- MODO SIMULACIÓN (TWILIO DESHABILITADO) ---")
        logging.info(f"Para: {to}")
        logging.info(f"Mensaje: {body}")
        logging.info("---------------------------------------------")
        return True  # Simulamos un envío exitoso

    try:
        # Intentar enviar un mensaje real mediante Twilio
        logging.info(f"--- MODO REAL (TWILIO HABILITADO) ---")
        msg = twilio_client.messages.create(
            from_=TWILIO_WHATSAPP_NUMBER,  # Número de WhatsApp de Twilio
            to=to,
            body=body
        )

        # Si obtenemos un SID, el envío fue exitoso
        if msg.sid:
            logging.info(f"Twilio SID: {msg.sid} -> Mensaje enviado a {to}")
            return True

    except TwilioRestException as te:
        # Manejo específico de errores de Twilio
        error_code = getattr(te, 'code', None)  # Obtener el código de error, si existe

        if error_code == 63016:  # Número no registrado en el Sandbox de WhatsApp
            logging.warning(
                f"Restricción en Twilio Sandbox: El número '{to}' no está registrado en el Sandbox de WhatsApp."
            )
        elif error_code == 20429:  # Exceso de solicitudes
            logging.warning(
                "Has excedido el límite de velocidad de solicitudes a la API de Twilio."
            )

        # En cualquier caso de restricción, imprimimos el mensaje por consola como fallback
        logging.info("--- RESTRICCIÓN DETECTADA: MENSAJE NO ENVIADO POR TWILIO ---")
        logging.info(f"FALLBACK - Para: {to}")
        logging.info(f"FALLBACK - Mensaje: {body}")
        logging.info("---------------------------------------------")
        return True  # Tratamos el fallback (impreso) como un envío exitoso

    except TwilioException as te:
        # Otros errores generales específicos de Twilio
        logging.error(f"Excepción de Twilio al enviar a {to}: {te}", exc_info=True)
    except Exception as e:
        # Otros errores generales
        logging.error(f"Error general al enviar a {to}: {e}", exc_info=True)

    # Si llegamos aquí, algo falló
    logging.error(f"Fallo al enviar mensaje a {to}. Revisar configuración del Sandbox de WhatsApp.")
    return False
def cw_ensure_contact(wa_id: str, name: str | None = None) -> dict | None:
    search_url = f"{CW_BASE}/api/v1/accounts/{CW_ACC}/contacts/search"
    params = {"q": wa_id.replace("whatsapp:", "")}
    try:
        r = requests.get(search_url, params=params, headers=CW_HEADERS, timeout=10)
        r.raise_for_status()
        data = r.json()
        if data['meta']['count'] > 0: return data['payload'][0]
        create_url = f"{CW_BASE}/api/v1/accounts/{CW_ACC}/contacts"
        payload = {"inbox_id": int(CW_INBOX), "name": name or wa_id, "phone_number": wa_id.replace("whatsapp:", "")}
        r_create = requests.post(create_url, json=payload, headers=CW_HEADERS, timeout=10)
        r_create.raise_for_status()
        return r_create.json()['payload']
    except Exception as e:
        logging.error(f"Error en cw_ensure_contact: {e}", exc_info=True)
        return None

def cw_find_or_create_conversation(contact_id: int, inbox_id: int, source_id: str) -> int | None:
    try:
        search_url = f"{CW_BASE}/api/v1/accounts/{CW_ACC}/contacts/{contact_id}/conversations"
        r_search = requests.get(search_url, headers=CW_HEADERS, timeout=10)
        if r_search.status_code == 200:
            for conv in r_search.json().get('payload', []):
                if conv.get('meta', {}).get('source_id') == source_id and conv.get('status') == 'open':
                    return conv['id']
        create_url = f"{CW_BASE}/api/v1/accounts/{CW_ACC}/conversations"
        payload = {"source_id": source_id, "inbox_id": inbox_id, "contact_id": contact_id, "status": "open"}
        r_create = requests.post(create_url, json=payload, headers=CW_HEADERS, timeout=10)
        r_create.raise_for_status()
        return r_create.json().get("id")
    except Exception as e:
        logging.error(f"Error en cw_find_or_create_conversation: {e}", exc_info=True)
        return None

def cw_add_private_note(conversation_id: int, content: str):
    url = f"{CW_BASE}/api/v1/accounts/{CW_ACC}/conversations/{conversation_id}/messages"
    payload = {"content": content, "private": True, "message_type": "outgoing"}
    try:
        requests.post(url, json=payload, headers=CW_HEADERS, timeout=10).raise_for_status()
    except Exception as e:
        logging.error(f"Error en cw_add_private_note: {e}", exc_info=True)

def cw_add_user_message(conversation_id: int, content: str):
    url = f"{CW_BASE}/api/v1/accounts/{CW_ACC}/conversations/{conversation_id}/messages"
    payload = {"content": content, "private": False, "message_type": "incoming"}
    try:
        requests.post(url, json=payload, headers=CW_HEADERS, timeout=10).raise_for_status()
    except Exception as e:
        logging.error(f"Error en cw_add_user_message: {e}", exc_info=True)

