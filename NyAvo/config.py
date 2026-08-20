from pydantic_settings import BaseSettings
from functools import lru_cache

class Settings(BaseSettings):
    gemini_api_key: str
    gemini_model: str = "gemini-2.5-pro"
    gemini_embedding_model: str = "models/gemini-embedding-001"
    use_dummy_embeddings: bool = False
    use_dummy_chat: bool = False

    # SMTP (Gmail)
    smtp_server: str = "smtp.gmail.com"
    smtp_port: int = 587
    smtp_email: str = ""
    smtp_password: str = ""
    handoff_recipient: str = ""   # Email qui recevra les alertes

    class Config:
        env_file = ".env"

@lru_cache()
def get_settings() -> Settings:
    return Settings()

BRAND_CONFIG = {
    "brand_id": "marque",
    "brand_name": "Marque",
    "agent_name": "Alex",
    "agent_persona": (
        "Tu es Alex, conseiller(ère) de la marque. "
        "Tu incarnes les valeurs de la marque : qualité, transparence, durabilité. "
        "Tu tutoies le client, tu es direct et chaleureux sans être condescendant."
    ),
    "handoff_triggers_regex": r"humain|conseiller|personne réelle|parler à quelqu'un|urgent|rappeler",
}