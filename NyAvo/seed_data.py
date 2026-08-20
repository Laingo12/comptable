import asyncio, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
from core.admin import add_product, add_faq, add_order, add_client, add_promotion, add_agent, set_setting

async def seed():
    # Vokatra
    await add_product("T-shirt bio", "Coton bio, Portugal", 45, "homme", promotion="-10%", stock=20, available=True,
                      colors="blanc, noir", sizes="S, M, L", features='{"matière":"coton bio"}', similar_products="", image_path="tshirt.jpg")
    await add_product("Sweat molletonné", "Italie, 85€", 85, "femme", promotion="", stock=15, available=True,
                      colors="gris", sizes="M, L", features='{"matière":"coton peigné"}', similar_products="", image_path="sweat.jpg")
    # FAQ
    add_faq("Délais de livraison", "3-5 jours ouvrés", "livraison")
    add_faq("Retour produit", "14 jours gratuits", "retour")
    # Clients
    add_client("Jean Dupont", "jean@example.com", "0123456789", "[]", "[]", '{"VIP":true}')
    # Commandes
    add_order("CMD-1001", 1, 1, "Expédiée", "DHL", "TRK123", "2026-07-30", "Payé")
    # Promotions
    add_promotion("Soldes été", "SUMMER20", "-20%", "2026-07-01", "2026-08-31", "Dès 80€")
    # Agents
    add_agent("Commercial", "Conseiller ventes", "", "active")
    add_agent("SAV", "Service après-vente", "", "active")
    # Settings
    set_setting("company_name", "DAMART")
    set_setting("company_logo", "logo.png")
    print("✅ Données initiales insérées.")

if __name__ == "__main__":
    asyncio.run(seed())