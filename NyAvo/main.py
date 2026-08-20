from fastapi import FastAPI, HTTPException, Query, Form, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
import os, shutil, json, re, unicodedata, traceback
from datetime import datetime

from core.agent import handle_message
from core.rag import init_db, get_db
from core.admin import *
from utils.email import send_handoff_email
from config import BRAND_CONFIG

app = FastAPI(title="Agent IA DAMART")

app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

class ChatRequest(BaseModel):
    message: str
    history: list[dict] = []
    email: str = ""

class ChatResponse(BaseModel):
    response: str
    intent: dict = {}
    sources: list[str] = []
    agent_used: str = ""
    product_image: str | None = None

def clean_filename(filename: str) -> str:
    name = unicodedata.normalize('NFKD', filename).encode('ascii', 'ignore').decode('ascii')
    name = re.sub(r'[^a-zA-Z0-9_\-\.]', '_', name)
    name = name.strip('_')
    if not name:
        import uuid
        name = str(uuid.uuid4()) + '.jpg'
    return name

@app.on_event("startup")
async def startup():
    init_db()
    conn = get_db()
    conn.execute("INSERT OR IGNORE INTO settings (key,value) VALUES ('company_name','DAMART')")
    conn.execute("INSERT OR IGNORE INTO settings (key,value) VALUES ('company_logo','')")
    for s in ['Shopify', 'DHL', 'PayPal', 'Stripe', 'WhatsApp']:
        conn.execute("INSERT OR IGNORE INTO integrations (service,status) VALUES (?,?)", (s, 'simulé'))
    conn.commit()
    conn.close()

@app.get("/")
async def root():
    return FileResponse("static/index.html")

@app.get("/admin")
async def admin():
    return FileResponse("static/admin.html")

@app.get("/health")
async def health():
    return {"status":"ok"}

# ------------------------------------------------------------
# Chat avec handoff et sauvegarde de conversation
# ------------------------------------------------------------
@app.post("/api/chat", response_model=ChatResponse)
async def chat(req: ChatRequest):
    try:
        client_email = req.email.strip() if req.email else None

        # Détection du handoff
        if re.search(BRAND_CONFIG["handoff_triggers_regex"], req.message, re.IGNORECASE):
            await send_handoff_email(client_email, req.message)
            handoff_response = "Je te mets en relation avec un conseiller. Un instant..."
            save_conversation(client_email, req.message, handoff_response, "Handoff")
            return ChatResponse(
                response=handoff_response,
                intent={"intention": "HANDOFF"},
                sources=[],
                agent_used="Handoff",
                product_image=None
            )

        res = await handle_message(req.message, req.history, client_email=client_email)
        save_conversation(client_email, req.message, res["response"], res["agent_used"])
        return ChatResponse(**res)
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(500, detail=str(e))

def save_conversation(client_email, user_message, agent_response, agent_used):
    try:
        conn = get_db()
        client_id = None
        if client_email:
            client = conn.execute("SELECT id FROM clients WHERE email=?", (client_email,)).fetchone()
            if client:
                client_id = client["id"]
        summary = user_message[:100] + " → " + agent_response[:100]
        conn.execute(
            "INSERT INTO conversations (client_id, date, channel, summary, agent_used) VALUES (?,?,?,?,?)",
            (client_id, datetime.now().isoformat(), "chat", summary, agent_used)
        )
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"Erreur lors de la sauvegarde de la conversation : {e}")

# ------------------------------------------------------------
# Recherche
# ------------------------------------------------------------
@app.get("/api/search")
async def search(q: str = Query(..., min_length=2)):
    from core.rag import search_knowledge
    results = await search_knowledge(q)
    return {"results": [{"name": r["title"], "description": r["content"][:200]} for r in results]}

# ------------------------------------------------------------
# Produits
# ------------------------------------------------------------
@app.get("/api/products")
async def list_products():
    conn = get_db()
    rows = conn.execute("SELECT * FROM products").fetchall()
    conn.close()
    products = []
    for r in rows:
        p = dict(r)
        image = None
        if p.get("images"):
            try:
                imgs = json.loads(p["images"])
                if isinstance(imgs, list) and len(imgs) > 0:
                    image = str(imgs[0]).strip().replace('"','').replace("'","")
            except:
                image = str(p["images"]).strip()
        p["image"] = image
        del p["images"]
        products.append(p)
    return {"products": products}

@app.post("/api/products")
async def create_product(
    name: str = Form(...),
    description: str = Form(""),
    price: float = Form(...),
    promotion: str = Form(""),
    stock: int = Form(0),
    available: bool = Form(True),
    colors: str = Form(""),
    sizes: str = Form(""),
    features: str = Form("{}"),
    similar_products: str = Form(""),
    category: str = Form(...),
    image: UploadFile = File(None)
):
    img_path = None
    if image:
        os.makedirs("static/images", exist_ok=True)
        safe_name = clean_filename(image.filename)
        loc = f"static/images/{safe_name}"
        with open(loc, "wb") as f:
            shutil.copyfileobj(image.file, f)
        img_path = safe_name
    await add_product(name, description, price, category, promotion, stock, available,
                      colors, sizes, features, similar_products, img_path)
    return {"status":"ok"}

@app.delete("/api/products/{product_id}")
async def del_product(product_id: int):
    delete_product(product_id)
    return {"status":"ok"}

# ------------------------------------------------------------
# FAQ
# ------------------------------------------------------------
@app.get("/api/faq")
async def list_faq():
    conn = get_db()
    rows = conn.execute("SELECT * FROM faq").fetchall()
    conn.close()
    return {"faq": [dict(r) for r in rows]}

@app.post("/api/faq")
async def create_faq(question: str = Form(...), answer: str = Form(...), category: str = Form("")):
    add_faq(question, answer, category)
    return {"status":"ok"}

@app.delete("/api/faq/{faq_id}")
async def del_faq(faq_id: int):
    delete_faq(faq_id)
    return {"status":"ok"}

# ------------------------------------------------------------
# Commandes
# ------------------------------------------------------------
@app.get("/api/orders")
async def list_orders():
    conn = get_db()
    rows = conn.execute("""
        SELECT o.*, c.name as customer_name, p.name as product_name
        FROM orders o
        LEFT JOIN clients c ON o.customer_id = c.id
        LEFT JOIN products p ON o.product_id = p.id
        ORDER BY o.date DESC
    """).fetchall()
    conn.close()
    return {"orders": [dict(r) for r in rows]}

@app.post("/api/orders")
async def create_order(
    order_number: str = Form(...),
    customer_id: int = Form(...),
    product_id: int = Form(...),
    status: str = Form(...),
    order_date: str = Form(""),
    carrier: str = Form(""),
    tracking: str = Form(""),
    estimated: str = Form(""),
    payment: str = Form("")
):
    if not order_date:
        order_date = datetime.now().isoformat()
    add_order(order_number, customer_id, product_id, status, carrier, tracking, estimated, payment, order_date)
    return {"status":"ok"}

@app.delete("/api/orders/{order_id}")
async def del_order(order_id: int):
    delete_order(order_id)
    return {"status":"ok"}

# ------------------------------------------------------------
# Clients
# ------------------------------------------------------------
@app.get("/api/clients")
async def list_clients():
    conn = get_db()
    rows = conn.execute("SELECT * FROM clients").fetchall()
    conn.close()
    return {"clients": [dict(r) for r in rows]}

@app.post("/api/clients")
async def create_client(
    name: str = Form(...),
    email: str = Form(...),
    phone: str = Form(""),
    purchase_history: str = Form("[]"),
    favorite_products: str = Form("[]"),
    preferences: str = Form("{}")
):
    add_client(name, email, phone, purchase_history, favorite_products, preferences)
    return {"status":"ok"}

@app.delete("/api/clients/{client_id}")
async def del_client(client_id: int):
    delete_client(client_id)
    return {"status":"ok"}

# ------------------------------------------------------------
# Promotions
# ------------------------------------------------------------
@app.get("/api/promotions")
async def list_promos():
    conn = get_db()
    rows = conn.execute("SELECT * FROM promotions").fetchall()
    conn.close()
    return {"promotions": [dict(r) for r in rows]}

@app.post("/api/promotions")
async def create_promo(
    name: str = Form(...),
    code: str = Form(...),
    discount: str = Form(...),
    start_date: str = Form(...),
    end_date: str = Form(...),
    conditions: str = Form("")
):
    add_promotion(name, code, discount, start_date, end_date, conditions)
    return {"status":"ok"}

@app.delete("/api/promotions/{promo_id}")
async def del_promo(promo_id: int):
    delete_promotion(promo_id)
    return {"status":"ok"}

# ------------------------------------------------------------
# Paiements
# ------------------------------------------------------------
@app.get("/api/payments")
async def list_payments():
    conn = get_db()
    rows = conn.execute("SELECT * FROM payments").fetchall()
    conn.close()
    return {"payments": [dict(r) for r in rows]}

@app.post("/api/payments")
async def create_payment(
    order_number: str = Form(...),
    method: str = Form(""),
    status: str = Form(""),
    failure_reason: str = Form(""),
    refund: str = Form("")
):
    add_payment(order_number, method, status, failure_reason, refund)
    return {"status":"ok"}

@app.delete("/api/payments/{pid}")
async def del_payment(pid: int):
    delete_payment(pid)
    return {"status":"ok"}

# ------------------------------------------------------------
# Livraisons
# ------------------------------------------------------------
@app.get("/api/deliveries")
async def list_deliveries():
    conn = get_db()
    rows = conn.execute("SELECT * FROM deliveries").fetchall()
    conn.close()
    return {"deliveries": [dict(r) for r in rows]}

@app.post("/api/deliveries")
async def create_delivery(
    order_number: str = Form(...),
    carrier: str = Form(""),
    status: str = Form(""),
    position: str = Form(""),
    delay: bool = Form(False),
    estimated_date: str = Form("")
):
    add_delivery(order_number, carrier, status, position, delay, estimated_date)
    return {"status":"ok"}

@app.delete("/api/deliveries/{did}")
async def del_delivery(did: int):
    delete_delivery(did)
    return {"status":"ok"}

# ------------------------------------------------------------
# Agents IA
# ------------------------------------------------------------
@app.get("/api/agents")
async def list_agents():
    conn = get_db()
    rows = conn.execute("SELECT * FROM ai_agents").fetchall()
    conn.close()
    return {"agents": [dict(r) for r in rows]}

@app.post("/api/agents")
async def create_agent(
    name: str = Form(...),
    mission: str = Form(...),
    status: str = Form("active"),
    knowledge_file: UploadFile = File(None)
):
    knowledge_path = ""
    if knowledge_file:
        os.makedirs("static/knowledge", exist_ok=True)
        safe_name = clean_filename(knowledge_file.filename)
        loc = f"static/knowledge/{safe_name}"
        with open(loc, "wb") as f:
            shutil.copyfileobj(knowledge_file.file, f)
        knowledge_path = f"knowledge/{safe_name}"
    add_agent(name, mission, knowledge_path, status)
    return {"status":"ok"}

@app.delete("/api/agents/{aid}")
async def del_agent(aid: int):
    delete_agent(aid)
    return {"status":"ok"}

# ------------------------------------------------------------
# Conversations
# ------------------------------------------------------------
@app.get("/api/conversations")
async def list_conversations():
    conn = get_db()
    rows = conn.execute("SELECT * FROM conversations ORDER BY date DESC").fetchall()
    conversations = []
    for r in rows:
        conv = dict(r)
        if conv.get("client_id"):
            client = conn.execute("SELECT email FROM clients WHERE id=?", (conv["client_id"],)).fetchone()
            conv["client_email"] = client["email"] if client else ""
        else:
            conv["client_email"] = ""
        conversations.append(conv)
    conn.close()
    return {"conversations": conversations}

@app.delete("/api/conversations/{conv_id}")
async def del_conversation(conv_id: int):
    conn = get_db()
    conn.execute("DELETE FROM conversations WHERE id=?", (conv_id,))
    conn.commit()
    conn.close()
    return {"status":"ok"}

# ------------------------------------------------------------
# Paramètres entreprise
# ------------------------------------------------------------
@app.get("/api/settings")
async def get_settings():
    conn = get_db()
    rows = conn.execute("SELECT * FROM settings").fetchall()
    conn.close()
    return {"settings": {row["key"]: row["value"] for row in rows}}

@app.post("/api/settings")
async def update_settings(
    company_name: str = Form(""),
    addresses: str = Form(""),
    phone: str = Form(""),
    hours: str = Form(""),
    logo: UploadFile = File(None),
    return_policy: UploadFile = File(None),
    delivery_info: UploadFile = File(None)
):
    settings_dir = "static/settings"
    os.makedirs(settings_dir, exist_ok=True)
    conn = get_db()

    def save_setting(key, value):
        conn.execute("INSERT OR REPLACE INTO settings (key,value) VALUES (?,?)", (key, value))

    save_setting("company_name", company_name)
    save_setting("addresses", addresses)
    save_setting("phone", phone)
    save_setting("hours", hours)

    if logo:
        logo_path = f"settings/{clean_filename(logo.filename)}"
        with open(f"static/{logo_path}", "wb") as f:
            shutil.copyfileobj(logo.file, f)
        save_setting("logo", logo_path)

    if return_policy:
        rp_path = f"settings/{clean_filename(return_policy.filename)}"
        with open(f"static/{rp_path}", "wb") as f:
            shutil.copyfileobj(return_policy.file, f)
        save_setting("return_policy", rp_path)

    if delivery_info:
        di_path = f"settings/{clean_filename(delivery_info.filename)}"
        with open(f"static/{di_path}", "wb") as f:
            shutil.copyfileobj(delivery_info.file, f)
        save_setting("delivery_info", di_path)

    conn.commit()
    conn.close()
    return {"status":"ok"}

# ------------------------------------------------------------
# Intégrations
# ------------------------------------------------------------
@app.get("/api/integrations")
async def get_integrations():
    conn = get_db()
    rows = conn.execute("SELECT * FROM integrations").fetchall()
    conn.close()
    return {"integrations": [dict(r) for r in rows]}

@app.post("/api/integrations")
async def update_integration(service: str = Form(...), status: str = Form("simulé")):
    set_integration(service, status)
    return {"status":"ok"}

app.mount("/static", StaticFiles(directory="static"), name="static")