from fastapi import FastAPI
from pydantic import BaseModel
from pydantic_settings import BaseSettings
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import requests
import os

app = FastAPI()

from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # React dev server
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/")
def read_index():
    return FileResponse("static/index.html")

class Settings(BaseSettings):
    mistral_api_key: str = os.getenv("test1", "3ANq2PZ7RbZJS1pqJX5jiA09YFf1d1Ki")

settings = Settings()

class Question(BaseModel):
    text: str

def generate_answer_mistral(prompt: str) -> str:
    url = "https://api.mistral.ai/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {settings.mistral_api_key}",
        "Content-Type": "application/json"
    }
    body = {
        "model": "mistral-small",
        "messages": [
            {"role": "system", "content": "You are a helpful and knowledgeable assistant."},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.7,
        "top_p": 0.9,
        "max_tokens": 512
    }
    response = requests.post(url, headers=headers, json=body)
    response.raise_for_status()
    return response.json()["choices"][0]["message"]["content"].strip()

def search_duckduckgo(query: str):
    url = "https://api.duckduckgo.com/"
    params = {"q": query, "format": "json", "no_redirect": 1}
    res = requests.get(url, params=params).json()

    results = []
    if res.get("AbstractURL"):
        results.append({"name": "DuckDuckGo Answer", "url": res["AbstractURL"]})

    for topic in res.get("RelatedTopics", []):
        if isinstance(topic, dict) and "FirstURL" in topic:
            results.append({
                "name": topic.get("Text", "Related Resource"),
                "url": topic["FirstURL"]
            })
    return results

@app.post("/ask")
def ask_question(q: Question):
    prompt = f"Explain in detail: {q.text}"
    try:
        answer = generate_answer_mistral(prompt)
    except Exception as e:
        answer = f"Error generating response: {str(e)}"

    resources = search_duckduckgo(q.text)
    return {
        "answer": answer,
        "resources": resources
    }

# 👇 This allows you to run with `python main.py`
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True)
