from google import genai
from config import get_settings
import json, asyncio, random

settings = get_settings()
# Initialiser le client avec la clé API
client = genai.Client(api_key=settings.gemini_api_key)

async def classify_intent(message: str) -> dict:
    prompt = f"""Tu es un classificateur d'intention. Analyse ce message et retourne
UNIQUEMENT un JSON valide, sans markdown, sans commentaire :

{{
    "intention": "RECHERCHE_PRODUIT" | "SUIVI_COMMANDE" | "SAV" | "PROMOTION" | "QUESTION_GENERALE" | "HORS_SUJET",
    "sous_intention": "recommandation" | "disponibilite" | "prix" | "statut_commande" | "retour" | "remboursement" | "code_promo" | "livraison" | "autre",
    "entites": {{"produit": "", "numero_commande": "", "email_client": ""}},
    "sentiment": "positif" | "neutre" | "negatif"
}}

Message : "{message}" """
    loop = asyncio.get_event_loop()
    response = await loop.run_in_executor(
        None,
        lambda: client.models.generate_content(
            model=settings.gemini_model,
            contents=prompt
        )
    )
    try:
        return json.loads(response.text.strip())
    except json.JSONDecodeError:
        return {
            "intention": "QUESTION_GENERALE",
            "sous_intention": "autre",
            "entites": {"produit": "", "numero_commande": "", "email_client": ""},
            "sentiment": "neutre"
        }

async def generate_response(
    system_prompt: str,
    conversation_history: list[dict],
    context_data: str,
    user_message: str,
) -> str:
    if settings.use_dummy_chat:
        return "Je suis un assistant simulé. L'API Google est momentanément indisponible."
    full_prompt = (
        f"{system_prompt}\n\n"
        f"=== DONNÉES CONTEXTUELLES ===\n{context_data}\n\n"
        f"=== HISTORIQUE DE CONVERSATION ===\n"
        + "\n".join(f"{m['role'].upper()}: {m['content']}" for m in conversation_history)
        + f"\n\nUSER: {user_message}\nAGENT:"
    )
    loop = asyncio.get_event_loop()
    response = await loop.run_in_executor(
        None,
        lambda: client.models.generate_content(
            model=settings.gemini_model,
            contents=full_prompt
        )
    )
    return response.text.strip()

async def embed(text: str) -> list[float]:
    if settings.use_dummy_embeddings:
        return [random.random() for _ in range(3072)]
    loop = asyncio.get_event_loop()
    response = await loop.run_in_executor(
        None,
        lambda: client.models.embed_content(
            model=settings.gemini_embedding_model,
            contents=text
        )
    )
    # La réponse contient .embeddings[0].values
    return list(response.embeddings[0].values)