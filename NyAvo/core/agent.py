import json
import re
from config import BRAND_CONFIG
from integrations.gemini import classify_intent, generate_response
from core.rag import search_knowledge, format_rag_context, get_db
import structlog

logger = structlog.get_logger()

async def handle_message(message: str, conversation_history=None, client_email=None):
    if conversation_history is None:
        conversation_history = []

    # Classification de l'intention
    intent = await classify_intent(message)

    # Recherche RAG
    rag_results = await search_knowledge(message)
    rag_context = format_rag_context(rag_results)

    # Contexte structuré
    additional_context = await get_structured_data(intent)

    # Choix de l'agent
    agent = get_agent_from_intent(intent.get("sous_intention"))
    system_prompt = agent["system_prompt"]

    # Génération de la réponse
    context = f"{rag_context}\n\n{additional_context}"
    try:
        response_text = await generate_response(
            system_prompt=system_prompt,
            conversation_history=conversation_history,
            context_data=context,
            user_message=message,
        )
    except Exception as e:
        logger.error("gemini_generation_error", error=str(e))
        response_text = "Désolé, je rencontre un problème technique. Pouvez-vous reformuler ?"

    # Recherche de l'image du produit correspondant
    product_image = await get_product_image(intent, rag_results)
    if not product_image:
        product_image = find_relevant_product_image(message, response_text)

    return {
        "response": response_text,
        "intent": intent,
        "rag_sources": [r.get("source") for r in rag_results],
        "agent_used": agent["name"],
        "product_image": product_image,
    }

def get_agent_from_intent(sous_intention):
    mapping = {
        "recommandation": {"name": "Commercial", "system_prompt": f"{BRAND_CONFIG['agent_persona']} Tu es un conseiller commercial. Recommande des produits."},
        "disponibilite": {"name": "Commercial", "system_prompt": "Vérifie la disponibilité."},
        "prix": {"name": "Commercial", "system_prompt": "Donne des informations de prix."},
        "statut_commande": {"name": "Livraison", "system_prompt": "Tu es un agent de suivi de commande."},
        "retour": {"name": "SAV", "system_prompt": "Tu es un agent SAV. Explique la procédure de retour."},
        "remboursement": {"name": "Paiement", "system_prompt": "Tu es un agent de paiement."},
        "code_promo": {"name": "Commercial", "system_prompt": "Parle des promotions en cours."},
        "livraison": {"name": "Livraison", "system_prompt": "Informe sur les délais de livraison."},
    }
    return mapping.get(sous_intention, {"name": "Général", "system_prompt": BRAND_CONFIG["agent_persona"]})

async def get_structured_data(intent):
    entites = intent.get("entites", {})
    data = ""
    try:
        if entites.get("numero_commande"):
            conn = get_db()
            row = conn.execute("SELECT * FROM orders WHERE order_number=?", (entites["numero_commande"],)).fetchone()
            conn.close()
            if row:
                data = f"Commande {row['order_number']}: statut={row['status']}, suivi={row['tracking_number']}"
    except Exception as e:
        logger.error("order_lookup_error", error=str(e))

    try:
        if entites.get("email_client"):
            conn = get_db()
            row = conn.execute("SELECT * FROM clients WHERE email=?", (entites["email_client"],)).fetchone()
            conn.close()
            if row:
                data += f"\nClient: {row['name']}"
    except Exception as e:
        logger.error("client_lookup_error", error=str(e))

    return data

async def get_product_image(intent, rag_results):
    """Récupère l'image du produit recommandé en premier lieu via RAG ou entité."""
    image = None
    try:
        # 1. Chercher dans les résultats RAG
        for r in rag_results:
            if r.get("source") == "produit":
                metadata = r.get("metadata", {})
                if metadata.get("image"):
                    image = "/static/images/" + str(metadata["image"]).strip()
                    return image
        # 2. Chercher dans la table products par le champ entité
        produit = intent.get("entites", {}).get("produit", "")
        if produit:
            conn = get_db()
            row = conn.execute("SELECT images FROM products WHERE name LIKE ? LIMIT 1", (f"%{produit}%",)).fetchone()
            conn.close()
            if row and row["images"]:
                try:
                    imgs = json.loads(row["images"])
                    if imgs and len(imgs) > 0:
                        image = "/static/images/" + str(imgs[0]).strip()
                except:
                    pass
    except Exception as e:
        logger.error("product_image_error", error=str(e))
    return image

def find_relevant_product_image(message: str, response_text: str) -> str | None:
    """
    Cherche un produit dont le nom apparaît dans le message ou la réponse de l'agent.
    Retourne le chemin de l'image si trouvé, sinon None.
    """
    stopwords = {"le", "la", "les", "un", "une", "des", "je", "vous", "pour", "avec", "sans", "sur", "dans", "est", "sont", "très", "bien", "bonjour", "salut", "merci", "quoi", "comment", "votre", "nos", "mon", "ma", "mes", "ton", "ta", "tes"}
    combined = f"{message} {response_text}".lower()
    words = re.findall(r"[a-zàâäéèêëïîôöùûüç]+", combined)
    keywords = [w for w in words if w not in stopwords and len(w) > 2]

    if not keywords:
        return None

    conn = get_db()
    try:
        rows = conn.execute("SELECT name, images FROM products").fetchall()
    finally:
        conn.close()

    best_match = None
    best_score = 0
    for row in rows:
        name = row["name"].lower()
        product_words = set(re.findall(r"[a-zàâäéèêëïîôöùûüç]+", name))
        score = sum(1 for w in keywords if w in product_words)
        if score > best_score:
            best_score = score
            best_match = row

    if best_match and best_match["images"]:
        try:
            imgs = json.loads(best_match["images"])
            if imgs and len(imgs) > 0:
                return "/static/images/" + str(imgs[0]).strip()
        except:
            pass
    return None