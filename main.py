import json
import os
import secrets
from pathlib import Path

from fastapi import FastAPI, Header, HTTPException
from fastapi.concurrency import run_in_threadpool
from pydantic import BaseModel

from core.executor import executar_limpeza
from core.logging_config import get_logger

logger = get_logger(__name__)

app = FastAPI(title="Agente de Help Desk Zabbix", version="1.0")

BASE_DIR = Path(__file__).resolve().parent
CATALOGO_PATH = BASE_DIR / "scripts" / "comandos.json"

WEBHOOK_TOKEN = os.getenv("WEBHOOK_TOKEN")
if not WEBHOOK_TOKEN:
    logger.warning(
        "WEBHOOK_TOKEN não configurado: o endpoint /webhook/zabbix está aberto "
        "sem autenticação. Defina a variável de ambiente antes de expor a API."
    )


# Modelo de dados que o Zabbix vai enviar
class AlertaZabbix(BaseModel):
    hostname: str
    trigger_name: str
    severity: str


def carregar_catalogo_scripts():
    """Função auxiliar para ler o arquivo JSON atualizado sempre que acionada."""
    try:
        with open(CATALOGO_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        logger.error(f"Arquivo {CATALOGO_PATH} não encontrado.")
        return {}
    except json.JSONDecodeError:
        logger.error("O arquivo comandos.json possui um erro de formatação (sintaxe JSON inválida).")
        return {}


def validar_token(x_webhook_token: str | None) -> None:
    """Compara o token enviado com o configurado, quando WEBHOOK_TOKEN estiver definido."""
    if not WEBHOOK_TOKEN:
        return
    if not x_webhook_token or not secrets.compare_digest(x_webhook_token, WEBHOOK_TOKEN):
        raise HTTPException(status_code=401, detail="Token de autenticação inválido ou ausente.")


@app.post("/webhook/zabbix")
async def receber_alerta(alerta: AlertaZabbix, x_webhook_token: str | None = Header(default=None)):
    """Endpoint que recebe o alerta e decide qual script rodar."""

    validar_token(x_webhook_token)

    logger.info(f"Alerta recebido: host={alerta.hostname} trigger={alerta.trigger_name} severity={alerta.severity}")

    catalogo = carregar_catalogo_scripts()

    if not catalogo:
        raise HTTPException(status_code=500, detail="Catálogo de scripts indisponível.")

    # Lógica base (Fase 1) - Um roteador simples baseado em palavras-chave
    acao_desejada = None

    # Exemplo: O Zabbix mandou uma trigger contendo a palavra "Disk" (Falta de Espaço)
    if "Disk" in alerta.trigger_name:
        acao_desejada = "esvaziar_lixeira"

    # Exemplo: O Zabbix mandou uma trigger contendo "Temp" ou "Slow" (Lentidão)
    elif "Temp" in alerta.trigger_name:
        acao_desejada = "limpar_temp_usuario"

    # Se encontramos uma ação válida para a trigger
    if acao_desejada and acao_desejada in catalogo:
        script_info = catalogo[acao_desejada]
        nome = script_info.get("nome")
        comando = script_info.get("comando")

        if not nome or not comando:
            logger.error(f"Entrada '{acao_desejada}' do catálogo está incompleta (faltam 'nome'/'comando').")
            raise HTTPException(status_code=500, detail=f"Ação '{acao_desejada}' mal configurada no catálogo.")

        # O executor recebe exatamente o nome e o comando cadastrados no JSON.
        # Roda em threadpool pois é uma chamada bloqueante (subprocess).
        resultado = await run_in_threadpool(executar_limpeza, nome, comando)

        return {
            "status": "Ação de mitigação executada",
            "alerta_original": alerta.trigger_name,
            "detalhes_execucao": resultado
        }

    return {"status": "Alerta recebido, mas não há ações automáticas mapeadas para este gatilho."}

@app.get("/")
def health_check():
    return {"status": "Agente Online e Operante"}