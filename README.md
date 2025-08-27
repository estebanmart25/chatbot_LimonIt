# Chatbot LaborTeknic 🤖

Este proyecto corresponde al desarrollo de un chatbot integrado con WhatsApp para automatizar respuestas y consultas técnicas/comerciales de LaborTeknic. El bot utiliza **FastAPI**, **Twilio** y está vinculado a **Chatwoot** para gestionar escalamientos hacia asesores humanos.

El chatbot utiliza una arquitectura basada en una lógica de **Máquina de Estados Finita (FSM)** para gestionar dinámicamente los flujos de interacción con los usuarios. Además, implementa una base de datos para garantizar la persistencia de usuarios y sesiones, permitiendo un manejo eficiente y estructurado de las interacciones.

---

## Contenido

- [Características](#características)
- [Arquitectura](#arquitectura)
- [Requisitos](#requisitos)
- [Instalación](#instalación)
- [Configuración](#configuración)
- [Despliegue Local y Webhooks](#despliegue-local-y-webhooks)
- [Pruebas](#pruebas)
- [Uso](#uso)
- [Colaboradores](#colaboradores)

---

## Características

- **📱 Automatización via WhatsApp:** El chatbot responde automáticamente a consultas técnicas y comerciales.
- **🛠️ Modularidad:** La lógica del bot, servicios auxiliares y configuración de base de datos están separadas de manera estructurada.
- **🔁 Máquina de Estados FSM:** Flujos optimizados para manejar interacciones dinámicas con el usuario.
- **🌐 Escalamiento a Chatwoot:** Permite derivar conversaciones a agentes humanos cuando es necesario.
- **📊 Catálogo comercial interactivo:** Soporte para listas seleccionables y botones clicables.
- **🔒 Seguridad mediante configuración `.env`:** Las credenciales sensibles (Twilio y Chatwoot) son gestionadas vía variables de entorno.

---

## Arquitectura

```plaintext
CHATBOT_LABORTEKNIC/
│
├── chatbot/                 # Módulo principal del bot
│   ├── __init__.py          # Inicialización del módulo
│   ├── bot_logic.py         # Lógica FSM para flujos y respuestas del chatbot
│   ├── database.py          # Configuración y conexión con base de datos (SQLAlchemy)
│   ├── main_app.py          # Configuración de la aplicación FastAPI
│   ├── models.py            # Modelos ORM para base de datos
│   └── services.py          # Funciones auxiliares (Twilio y Chatwoot)
│
├── .env                    # Variables de entorno (ignorado en git)
├── .env.production         # Ejemplo de configuración para entornos productivos
├── main.py                 # Punto de entrada de la aplicación
├── requirements.txt        # Dependencias del proyecto
├── .gitignore              # Archivos y extensiones ignorados por Git
└── venv/                   # Entorno virtual de Python  
```
---
Requisitos
Software Necesario
Python 3.9+
Descárgalo en python.org.
Claves y configuraciones de Twilio:
Credenciales para Twilio y WhatsApp API. Necesitas crear un Twilio Sandbox o activar un número de producción.
Cuenta de Chatwoot:
Configura una instancia en Chatwoot para gestionar las interacciones humanas.
Base de datos: Un servidor de base de datos, como SQLite (por defecto), MySQL o PostgreSQL.

---
Instalación
1️⃣ Clonar el repositorio
bash


git clone https://github.com/tu-usuario/chatbot_laborTeknic.git
cd chatbot_laborTeknic
2️⃣ Crear un entorno virtual
Es importante trabajar en un entorno aislado para manejar las dependencias.

bash


python -m venv venv                   # Crear entorno virtual
source venv/bin/activate              # Activar (Linux/Mac)
venv\Scripts\activate                 # Activar (Windows)
3️⃣ Instalar dependencias
bash


pip install -r requirements.txt
Configuración
Variables de entorno
Crea un archivo .env en el directorio raíz del proyecto para almacenar las credenciales y configuraciones sensibles. Ejemplo:

---


# 🔐 Twilio Credenciales
TWILIO_ACCOUNT_SID=tu_twilio_account_sid
TWILIO_AUTH_TOKEN=tu_twilio_auth_token
TWILIO_WHATSAPP_NUMBER=whatsapp:+14155238886

# 🌐 Chatwoot Credenciales
CHATWOOT_URL=https://app.chatwoot.com
CHATWOOT_API_TOKEN=tu_chatwoot_api_token
CHATWOOT_ACCOUNT_ID=tu_chatwoot_account_id
CHATWOOT_INBOX_ID=tu_chatwoot_inbox_id

# 💾 Base de Datos Configuración
DB_HOST=
DB_PORT=
DB_NAME=
DB_USER=
DB_PASS=

⚠️ Nota: Este archivo está incluido en .gitignore para evitar que se suba al repositorio.

Despliegue Local y Webhooks
Ejecutar el servidor
Inicia la aplicación localmente con:

bash


uvicorn main:app --reload
El servidor estará disponible en http://127.0.0.1:8000.

Configurar el Webhook de Twilio
Ve a tu Twilio Console.
Configura la URL del webhook con:


http://127.0.0.1:8000/webhook
Usar ngrok para pruebas externas
Si deseas que Twilio pueda comunicarse con tu servidor local, utiliza ngrok:

Descarga ngrok desde ngrok.com.
Ejecuta ngrok:
bash


ngrok http 8000
Obtén la URL HTTPS generada (por ejemplo, https://1234abcd.ngrok.io) y úsala como webhook en Twilio:


https://1234abcd.ngrok.io/webhook
Uso
Automatización WhatsApp: El bot interpreta mensajes enviados por los usuarios y responde según la lógica definida (FSM).
Catálogo comercial: Los usuarios pueden consultar productos y servicios mediante un flujo dinámico.
Escalamiento a Chatwoot: Las consultas complejas pueden ser derivadas al equipo humano de soporte.
Flujo de Trabajo con Git
Este proyecto utiliza un Git Flow simplificado para gestionar el desarrollo. La estructura principal incluye dos ramas iniciales estables:

main: Contiene el código listo para producción.
develop: Contiene el código en desarrollo y sirve como base para nuevas funcionalidades.
Flujo:
Crea una nueva rama basada en develop para trabajar en una nueva funcionalidad:

bash


git checkout develop
git checkout -b feature/nueva-funcionalidad
Realiza tus cambios y luego sube la rama con:

bash


git add .
git commit -m "Describe el cambio"
git push origin feature/nueva-funcionalidad
Cuando termines, fusiona tu rama feature con develop:

bash


git checkout develop
git merge feature/nueva-funcionalidad
Después de realizar pruebas en develop, incorpora los cambios en main:

bash


git checkout main
git merge develop
git push origin main
Diagrama del Flujo:



```plaintext
main    <------------------------- Código listo para producción
  ^
  |
develop  <------------------------ Integración de features
   ^
   |
feature/1-nueva-logica  <--------- Nuevas funcionalidades
feature/2-bugfix         <--------- Corrección de errores

```
Colaboradores
Esteban Martins - Desarrollador Principal
Victoria - Desarrollador Principal
Cesar Martins  - Desarrollador Principal
