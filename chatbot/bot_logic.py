# chatbot/bot_logic.py (Versión completa con catálogo comercial y lista)
import logging
import json
import datetime
from sqlalchemy.orm import Session
from . import services
from .models import Customer, Ticket, SessionState

# --- Textos del Bot ---
GREETING_TEXT = (
    "👋 Hola, soy el Bot de Laborteknic y estoy aquí para ayudarte. "
    "Por favor, elegí la opción que mejor describa tu consulta.\n\n"
    "1️⃣ Soporte técnico\n2️⃣ Consultas comerciales\n3️⃣ Otras consultas\n\n"
    "Escribí 'menú' o 'volver' para reiniciar."
)
ASK_SERIAL_TEXT = "🔧 Perfecto, para poder ayudarte necesito que me indiques el número de serie de tu equipo."
ASK_MEDIA_TEXT = "📸 Gracias. Para diagnosticar mejor el problema, por favor envía una foto o video mostrando el inconveniente. Si no tenés, escribí 'No'."
ASK_DESCRIPTION_TEXT = "Por favor, añadí una breve descripción de tu consulta."
ASK_COMMERCIAL_INTRO = "🛒 Gracias por tu interés. Seleccioná un producto/servicio de la siguiente lista (respondiendo con el número o el nombre):"
ASK_COMMERCIAL_MEDIA = "📸 Si querés, podés adjuntar una foto o video relacionado (o escribí 'No' para omitir)."
ASK_OTHER_TEXT = "ℹ️ Por favor, escribí tu consulta de forma breve."
INVALID_OPTION_TEXT = "Opción no válida. Por favor, escribí 1, 2 o 3."
HANDOFF_MESSAGE = "✅ Gracias, he registrado toda la información. Ahora un asesor te atenderá en breve. Tiempo estimado de respuesta: 15 minutos."
SURVEY_TEXT = "🙏 Gracias por comunicarte con Laborteknic. Antes de despedirnos, ¿cómo calificarías la atención recibida?\n\n1. ⭐ Muy buena\n2. 🙂 Buena\n3. 😐 Regular\n4. 😞 Mala"

# --- Catálogo Comercial (editable) ---
PRODUCT_CATALOG = [
    {"id": "1", "title": "Equipos - Microscopios", "aliases": ["microscopio", "microscopios"]},
    {"id": "2", "title": "Equipos - Centrífugas", "aliases": ["centrifuga", "centrífuga", "centrifugas", "centrífugas"]},
    {"id": "3", "title": "Reactivos - Hematología", "aliases": ["hematologia", "hematología", "reactivos hematologia"]},
    {"id": "4", "title": "Reactivos - Química Clínica", "aliases": ["quimica", "química", "reactivos quimica"]},
    {"id": "5", "title": "Servicios - Mantenimiento Preventivo", "aliases": ["mantenimiento", "mantenimiento preventivo", "servicio mantenimiento"]},
    {"id": "6", "title": "Servicios - Calibración y Validación", "aliases": ["calibracion", "calibración", "validacion", "validación"]},
]

def build_product_list_text() -> str:
    lines = [ASK_COMMERCIAL_INTRO, ""]
    for p in PRODUCT_CATALOG:
        lines.append(f"{p['id']}. {p['title']}")
    lines.append("")
    lines.append("También podés escribir el nombre.")
    return "\n".join(lines)

PRODUCT_LIST_TEXT = build_product_list_text()

def match_product(user_text: str) -> str | None:
    """
    Devuelve el título del producto/servicio según el texto ingresado (número o nombre).
    """
    t = (user_text or "").strip().lower()
    if not t:
        return None
    # Por número
    for p in PRODUCT_CATALOG:
        if t == p["id"]:
            return p["title"]
    # Por coincidencia en título/aliases
    for p in PRODUCT_CATALOG:
        title_norm = p["title"].lower()
        if t in title_norm or title_norm in t:
            return p["title"]
        for alias in p.get("aliases", []):
            if alias in t or t in alias:
                return p["title"]
    return None

def handoff_to_agent(db: Session, customer: Customer, category: str, session_data: dict):
    logging.info(f"Handoff -> cliente {customer.id}, categoría '{category}'")
    contact_payload = services.cw_ensure_contact(customer.phone, customer.name)
    if not contact_payload:
        services.send_message(to=customer.phone, body="Hubo un problema al contactar con nuestros sistemas. Intentá nuevamente.")
        return

    contact_id = contact_payload["id"]
    inbox_id = int(services.CW_INBOX)
    source_id = f"whatsapp:{customer.phone.replace('whatsapp:+', '')}"
    conversation_id = services.cw_find_or_create_conversation(contact_id, inbox_id, source_id)
    if not conversation_id:
        services.send_message(to=customer.phone, body="Hubo un problema al iniciar una conversación con nuestro equipo. Intentá de nuevo.")
        return

    # Armar nota privada para el agente
    note = f"Nueva consulta de '{category}'.\nCliente: {customer.name or customer.phone}\n"
    if session_data.get("serial"):
        note += f"N° de Serie: {session_data['serial']}\n"
    if session_data.get("product"):
        note += f"Producto/Servicio: {session_data['product']}\n"
    if session_data.get("description"):
        note += f"Descripción: {session_data['description']}\n"
    if session_data.get("media_url"):
        note += f"Adjunto: {session_data['media_url']}"

    services.cw_add_private_note(conversation_id, note)

    # Crear ticket
    ticket = Ticket(
        customer_id=customer.id,
        category=category,
        initial_message=(
            session_data.get("description")
            or session_data.get("product")
            or session_data.get("serial")
            or ""
        ),
        media_url=session_data.get("media_url"),
        chatwoot_conversation_id=conversation_id,
        status="open"
    )
    db.add(ticket)

    # Confirmación al usuario
    services.send_message(to=customer.phone, body=HANDOFF_MESSAGE)

    # Dejar al usuario en estado 'handoff' y limpiar datos temporales
    session = db.query(SessionState).filter(SessionState.customer_id == customer.id).first()
    session.state = "handoff"
    session.data_json = '{}'  # limpia para próximas consultas
    db.commit()
    logging.info("Handoff completado y sesión limpiada.")

def process_user_message(db: Session, form: dict):
    from_wa = form.get("From")
    profile_name = form.get("ProfileName")
    body = (form.get("Body") or "").strip()
    num_media = int(form.get("NumMedia", "0"))
    logging.info(f"INICIO -> De {from_wa} ({profile_name}): '{body}' | Media: {num_media}")

    # Customer y Session
    customer = db.query(Customer).filter(Customer.phone == from_wa).first()
    if not customer:
        customer = Customer(phone=from_wa, name=profile_name)
        db.add(customer); db.commit(); db.refresh(customer)
        logging.info(f"Nuevo cliente ID {customer.id}")

    session = db.query(SessionState).filter(SessionState.customer_id == customer.id).first()
    if not session:
        session = SessionState(customer_id=customer.id, state="start")
        db.add(session); db.commit()
        logging.info(f"Nueva sesión creada para cliente {customer.id}")

    session_data = json.loads(session.data_json or '{}')
    current_state = session.state
    logging.info(f"Estado previo: {current_state} | Datos: {session_data}")

    # Reinicio a pedido del usuario (salvo si está en handoff o encuesta)
    if body.lower() in ["menú", "menu", "volver"] and current_state not in ["handoff", "wait_survey_response"]:
        current_state = "start"

    # Máquina de estados con respuesta garantizada
    response = None

    if current_state == "start":
        # Limpiar datos al iniciar un nuevo flujo para no arrastrar adjuntos/descripcion previos
        session_data = {}
        response = GREETING_TEXT
        session.state = "menu_wait_choice"

    elif current_state == "menu_wait_choice":
        if body == "1":
            session.state = "soporte_wait_serial"
            response = ASK_SERIAL_TEXT
        elif body == "2":
            # Nuevo flujo: mostrar lista comercial
            session.state = "comercial_show_list"
            response = PRODUCT_LIST_TEXT
        elif body == "3":
            session.state = "otras_wait_description"
            response = ASK_OTHER_TEXT
        else:
            response = f"{INVALID_OPTION_TEXT}\n\n{GREETING_TEXT}"

    # --- Flujo: Soporte Técnico ---
    elif current_state == "soporte_wait_serial":
        session_data["serial"] = body
        session.state = "soporte_wait_media"
        response = ASK_MEDIA_TEXT

    elif current_state == "soporte_wait_media":
        if num_media > 0 and 'no' not in body.lower():
            session_data["media_url"] = form.get("MediaUrl0")
        session.state = "soporte_wait_description"
        response = ASK_DESCRIPTION_TEXT

    elif current_state == "soporte_wait_description":
        session_data["description"] = body
        handoff_to_agent(db, customer, "Soporte Técnico", session_data)

    # --- Flujo: Consultas Comerciales con lista ---
    elif current_state == "comercial_show_list":
        # Usuario debe responder con número o nombre -> pasamos a esperar selección
        session.state = "comercial_wait_selection"
        # Si el usuario escribió cualquier otra cosa antes de recibir la lista, re-mostramos la lista
        response = PRODUCT_LIST_TEXT

    elif current_state == "comercial_wait_selection":
        # Resolver selección por número o palabra
        sel = match_product(body)
        if sel:
            session_data["product"] = sel
            session.state = "comercial_wait_media"
            response = ASK_COMMERCIAL_MEDIA
        else:
            response = f"No reconocí tu selección.\n\n{PRODUCT_LIST_TEXT}"

    elif current_state == "comercial_wait_media":
        if num_media > 0 and 'no' not in body.lower():
            session_data["media_url"] = form.get("MediaUrl0")
        # Derivar directamente (la descripción es opcional en comercial)
        handoff_to_agent(db, customer, "Consultas Comerciales", session_data)

    # --- Flujo: Otras Consultas ---
    elif current_state == "otras_wait_description":
        session_data["description"] = body
        handoff_to_agent(db, customer, "Otras Consultas", session_data)

    # --- Flujo: Durante conversación con agente ---
    elif current_state == "handoff":
        # Reenviamos lo que diga el cliente a la conversación de Chatwoot
        last_ticket = db.query(Ticket).filter(
            Ticket.customer_id == customer.id, Ticket.status == 'open'
        ).order_by(Ticket.created_at.desc()).first()
        if last_ticket:
            services.cw_add_user_message(last_ticket.chatwoot_conversation_id, body)
        else:
            session.state = "start"
            response = "No encuentro una conversación activa. Escribí algo para empezar de nuevo."

    # --- Flujo: Encuesta ---
    elif current_state == "wait_survey_response":
        rating_map = {"1": "Muy buena", "2": "Buena", "3": "Regular", "4": "Mala"}
        rating = rating_map.get(body, f"Texto: {body}")
        last_ticket = db.query(Ticket).filter(
            Ticket.customer_id == customer.id, Ticket.status == 'resolved'
        ).order_by(Ticket.closed_at.desc()).first()
        if last_ticket:
            last_ticket.satisfaction_rating = rating
        response = "¡Muchas gracias por tu feedback! Que tengas un buen día."
        session.state = "start"

    # Enviar respuesta si corresponde
    if response:
        ok = services.send_message(to=from_wa, body=response)
        if not ok:
            logging.error("Fallo al enviar mensaje por Twilio. Revisar credenciales o ventana de WhatsApp Sandbox.")

    # Guardar estado y datos
    session.data_json = json.dumps(session_data)
    db.commit()
    logging.info(f"FIN -> Estado nuevo: {session.state} | Datos: {session_data}")

def process_chatwoot_event(db: Session, payload: dict):
    event = payload.get("event")
    logging.info(f"Procesando evento de Chatwoot: {event}")
    
    if event == "message_created" and payload.get("message_type") == "outgoing" and not payload.get("private"):
        content = payload.get("content")
        source_id = payload.get("conversation", {}).get("contact_inbox", {}).get("source_id")
        if content and source_id:
            phone_number_from_cw = f"whatsapp:+{source_id.split(':')[1]}"
            customer = db.query(Customer).filter(Customer.phone == phone_number_from_cw).first()
            if customer:
                services.send_message(to=customer.phone, body=content)
    
    elif event == "conversation_status_changed" and payload.get("status") == "resolved":
        conv_id = payload.get("id")
        ticket = db.query(Ticket).filter(Ticket.chatwoot_conversation_id == conv_id, Ticket.status == 'open').order_by(Ticket.created_at.desc()).first()
        if ticket:
            ticket.status = "resolved"
            ticket.closed_at = datetime.datetime.utcnow()
            customer = ticket.customer
            session = db.query(SessionState).filter(SessionState.customer_id == customer.id).first()
            if session:
                session.state = "wait_survey_response"
                services.send_message(to=customer.phone, body=SURVEY_TEXT)
            db.commit()