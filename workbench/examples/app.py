"""Chapter 39 example. Run: uvicorn app:app --reload, then open http://127.0.0.1:8000/docs"""
from fastapi import FastAPI
from pydantic import BaseModel
app = FastAPI()

class Question(BaseModel):
    text: str

@app.post("/ask")
def ask(q: Question):
    return {"answer": f"You asked: {q.text}"}
