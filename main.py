from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from core.executor import executar_limpeza
from core.logging_config import get_logger
import json
from pathlib import Path

logger = get_logger(__name__)

app = FastAPI(title="Agente de Help Desk Zabbix", version="1.0")

# Modelo de dados que o Zabbix vai enviar
class AlertaZabbix(BaseModel):
    hostname: str
    trigger_name: str
    severity: str

def carregar_catalogo_scripts():
    """Função auxiliar para ler o arquivo JSON atualizado sempre que acionada."""
    caminho_arquivo = Path("scripts/comandos.json")
    try:
        with open(caminho_arquivo, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        logger.error("Arquivo comandos.json não encontrado.")
        return {}
    except json.JSONDecodeError:
        logger.error("O arquivo comandos.json possui um erro de formatação (sintaxe JSON inválida).")
        return {}

@app.post("/webhook/zabbix")
async def receber_alerta(alerta: AlertaZabbix):
    """Endpoint que recebe o alerta e decide qual script rodar."""

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
        
        # O executor recebe exatamente o nome e o comando cadastrados no JSON
        resultado = executar_limpeza(script_info["nome"], script_info["comando"])
        
        return {
            "status": "Ação de mitigação executada",
            "alerta_original": alerta.trigger_name,
            "detalhes_execucao": resultado
        }
        
    return {"status": "Alerta recebido, mas não há ações automáticas mapeadas para este gatilho."}

@app.get("/")
def health_check():
    return {"status": "Agente Online e Operante"}