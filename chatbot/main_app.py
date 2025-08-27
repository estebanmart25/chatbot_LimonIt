# chatbot/main_app.py
import logging
from fastapi import FastAPI, Request, Response, Depends
from sqlalchemy.orm import Session
from .database import SessionLocal, engine, Base
from . import bot_logic

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Laborteknic Business Bot (Estructurado)")

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.post("/webhook")
async def webhook(request: Request, db: Session = Depends(get_db)):
    try:
        form = dict(await request.form())
        bot_logic.process_user_message(db, form)
    except Exception as e:
        logging.error(f"Error fatal en webhook: {e}", exc_info=True)
    return Response(status_code=200)

@app.post("/chatwoot/webhook")
async def chatwoot_webhook(request: Request, db: Session = Depends(get_db)):
    try:
        payload = await request.json()
        bot_logic.process_chatwoot_event(db, payload)
    except Exception as e:
        logging.error(f"Error en webhook de Chatwoot: {e}", exc_info=True)
    return Response(status_code=200)

@app.get("/health")
def health():
    return {"status": "ok"}