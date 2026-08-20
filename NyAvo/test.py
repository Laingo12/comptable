from google import genai
import os
from dotenv import load_dotenv

load_dotenv()
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

# Test génération
response = client.models.generate_content(
    model="gemini-2.5-pro",
    contents="Bonjour"
)
print("Génération OK :", response.text)

# Test embedding
embedding_response = client.models.embed_content(
    model="gemini-embedding-001",
    contents="test"
)
print("Embedding OK, dimensions :", len(embedding_response.embeddings[0].values))