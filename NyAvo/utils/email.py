import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from config import get_settings
import asyncio

settings = get_settings()

async def send_handoff_email(client_email: str | None, user_message: str):
    """Envoie un email à l'agent pour un handoff."""
    if not settings.handoff_recipient or not settings.smtp_server:
        print("⚠️ SMTP non configuré, email non envoyé.")
        return

    recipient = settings.handoff_recipient
    subject = "Demande de transfert à un conseiller"
    body = f"""
    Un client souhaite parler à un conseiller.

    Email du client : {client_email if client_email else 'Non renseigné'}
    Message : {user_message}

    Prenez en charge la conversation dès que possible.
    """

    msg = MIMEMultipart()
    msg['From'] = settings.smtp_email
    msg['To'] = recipient
    msg['Subject'] = subject
    msg.attach(MIMEText(body, 'plain', 'utf-8'))

    loop = asyncio.get_event_loop()
    await loop.run_in_executor(None, _send_sync, msg)

def _send_sync(msg):
    if settings.smtp_port == 465:
        with smtplib.SMTP_SSL(settings.smtp_server, settings.smtp_port) as server:
            server.login(settings.smtp_email, settings.smtp_password)
            server.send_message(msg)
    else:
        with smtplib.SMTP(settings.smtp_server, settings.smtp_port) as server:
            server.starttls()
            server.login(settings.smtp_email, settings.smtp_password)
            server.send_message(msg)
    print(f"✅ Email de handoff envoyé à {settings.handoff_recipient}")