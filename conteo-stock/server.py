# conteo-stock/server.py
import json as _json
import os
from pathlib import Path
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from pydantic import BaseModel
from dotenv import load_dotenv

load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), "..", ".env"))

from scrape_stock import get_stock
from enviar_email import enviar
from productos import CATEGORIAS as _CATEGORIAS

app  = FastAPI()
HERE = Path(__file__).parent


@app.get("/", response_class=HTMLResponse)
async def index():
    html = (HERE / "index.html").read_text(encoding="utf-8")
    cats_json = _json.dumps(_CATEGORIAS, ensure_ascii=False)
    return HTMLResponse(content=html.replace("__CATEGORIAS_JSON__", cats_json))


@app.get("/api/stock")
async def api_stock():
    try:
        return JSONResponse(content=await get_stock())
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


class ConteoPayload(BaseModel):
    fecha: str
    hora: str
    turno: str
    responsable: str
    conteo: dict


@app.post("/api/enviar")
async def api_enviar(payload: ConteoPayload):
    try:
        enviar(payload.model_dump())
        return {"ok": True}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("server:app", host="0.0.0.0", port=8080, reload=True)
