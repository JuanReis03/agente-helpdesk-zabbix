# Agente Autônomo de Help Desk (Zabbix)

API em FastAPI que recebe alertas do Zabbix via webhook, decide qual script de
mitigação rodar (com base no nome da trigger) e executa o comando PowerShell
correspondente, retornando métricas de sucesso, tempo e espaço liberado.

## Stack

- Python 3.12
- [FastAPI](https://fastapi.tiangolo.com/) + Uvicorn
- [uv](https://docs.astral.sh/uv/) para gerenciamento de ambiente e dependências
- `logging` (com rotação de arquivo) para auditoria das execuções

## Estrutura do projeto

```
.
├── main.py                  # API FastAPI (endpoint /webhook/zabbix)
├── core/
│   ├── executor.py          # Executa os comandos PowerShell e mede o resultado
│   └── logging_config.py    # Configuração central de logging (console + arquivo)
├── scripts/
│   └── comandos.json        # Catálogo de ações/scripts disponíveis
├── src/projeto_agente/      # Pacote do projeto (entry point projeto-agente)
├── tests/                   # Testes automatizados (pytest)
└── Scripts_Limpeza (1).ipynb  # Protótipos/notebook de exploração
```

## Pré-requisitos

- [uv](https://docs.astral.sh/uv/getting-started/installation/) instalado
- Windows com PowerShell disponível (os scripts de mitigação rodam via `powershell -Command`)

## Setup

Instale o [uv](https://docs.astral.sh/uv/getting-started/installation/) e, na
raiz do projeto, sincronize o ambiente (cria o `.venv` e instala as
dependências travadas em `uv.lock`):

```powershell
uv sync
```

## Rodando a aplicação

```powershell
uv run uvicorn main:app --reload
```

A API sobe por padrão em `http://127.0.0.1:8000`.

- `GET /` → health check
- `POST /webhook/zabbix` → recebe o alerta do Zabbix (`hostname`, `trigger_name`, `severity`) e executa a ação mapeada em `scripts/comandos.json`

Teste local com curl:

```powershell
curl -X POST http://127.0.0.1:8000/webhook/zabbix -H "Content-Type: application/json" -d '{"hostname":"PC01","trigger_name":"Disk space low","severity":"high"}'
```

## Logging

Todas as execuções (recebimento de alertas, resultado dos scripts, erros) são
registradas via `logging`:

- Console (stdout)
- Arquivo rotativo em `logs/agente.log` (5 MB por arquivo, 3 backups)

O nível pode ser ajustado com a variável de ambiente `LOG_LEVEL` (padrão `INFO`):

```powershell
$env:LOG_LEVEL = "DEBUG"
uv run uvicorn main:app --reload
```

A pasta `logs/` não é versionada (está no `.gitignore`).

## Autenticação do webhook

O endpoint `/webhook/zabbix` executa comandos no sistema, então suporta um
token compartilhado opcional via variável de ambiente `WEBHOOK_TOKEN`. Se
definida, toda requisição precisa enviar o header `X-Webhook-Token` com o
mesmo valor (senão recebe `401`). Se não for definida, o endpoint fica aberto
e um aviso é logado — não deixe assim em produção.

```powershell
$env:WEBHOOK_TOKEN = "um-segredo-forte"
uv run uvicorn main:app --reload
```

## Testes e lint

```powershell
uv run pytest
uv run ruff check .
```

A CI (`.github/workflows/ci.yml`) roda os dois a cada push/PR.

## Roadmap e notas técnicas

O plano de implementação por fases e as anotações de pesquisa (Zabbix,
captura de tela em Sessão 0, LangChain/Ollama, etc.) estão em [andamento.md](andamento.md).
O checklist de melhorias e pendências (o que já foi feito e o que falta) está
em [CHECKLIST.md](CHECKLIST.md).
