# Checklist do Projeto — Agente de Help Desk Zabbix

Análise do estado atual do projeto, o que foi corrigido/implementado agora, e o
que falta para avançar. Última atualização: 2026-08-28.

## ✅ Feito

**Infra e organização**
- [x] Ambiente migrado para `uv` (`pyproject.toml` + `uv.lock`, `.venv` gerenciado pelo uv)
- [x] Repositório versionado e publicado no GitHub
- [x] Nome do arquivo `scripts/comandos.json` corrigido (estava salvo com caracteres de árvore de diretório no nome)
- [x] `.gitignore` cobrindo `.venv`, `logs/`, `.env`, checkpoints do Jupyter

**Observabilidade**
- [x] Logging estruturado (`core/logging_config.py`): console + arquivo rotativo em `logs/agente.log`, nível via `LOG_LEVEL`
- [x] `print()` e `logging.basicConfig` soltos substituídos pelo logger central em `main.py` e `core/executor.py`
- [x] Log de cada alerta recebido e do resultado (sucesso/falha) de cada execução

**Robustez (bugs corrigidos agora)**
- [x] `Path("scripts/comandos.json")` era relativo ao diretório de execução e quebrava se a API rodasse fora da raiz do projeto → agora resolvido a partir de `Path(__file__)`
- [x] `receber_alerta` era `async def` mas chamava `subprocess.run` (bloqueante) direto, travando o event loop do FastAPI durante cada execução → agora roda em threadpool (`run_in_threadpool`)
- [x] `subprocess.run` sem timeout — um comando travado (ex.: esperando input) prenderia a requisição para sempre → timeout padrão de 180s, com erro tratado
- [x] Falha ao iniciar o PowerShell (`FileNotFoundError`/`OSError`) não era tratada → agora retorna erro estruturado em vez de 500 cru
- [x] Entrada de catálogo sem `nome`/`comando` causava `KeyError` não tratado → agora retorna 500 com mensagem clara e loga o problema
- [x] Autenticação opcional por token no webhook (`WEBHOOK_TOKEN` + header `X-Webhook-Token`) — a API executa comandos no sistema, então faz sentido não deixar o endpoint totalmente aberto quando exposto

**Qualidade**
- [x] Suíte de testes automatizados com `pytest` (12 testes cobrindo `core/executor.py` e o endpoint `/webhook/zabbix`, incluindo auth, timeout, catálogo malformado)
- [x] Lint com `ruff` configurado e sem erros
- [x] CI no GitHub Actions (`.github/workflows/ci.yml`): roda lint + testes a cada push/PR

## 🔲 Pendente — decisões que só você pode tomar

Não implementei estes porque envolvem regras de negócio/risco que não são minha decisão:

- [ ] **Mapeamento trigger → ação**: hoje só 2 dos 17 scripts do catálogo (`esvaziar_lixeira`, `limpar_temp_usuario`) estão ligados a alguma trigger (`"Disk"`/`"Temp"` no nome). Os outros 15 (chkdsk, DISM, drivers, firewall, reset de rede, limpeza de logs de evento etc.) existem no catálogo mas nunca rodam sozinhos. Antes de automatizar isso, defina: quais devem disparar sozinhos vs. quais só devem rodar sob pedido explícito (chat/Teams/manual) — vários deles (DISM, chkdsk, fechar navegador do usuário) são "pesados" ou intrusivos.
- [ ] **Confirmação/aprovação antes de ações arriscadas** (já levantado na Fase 0 do `andamento.md`)
- [ ] **Configurar o Zabbix** (Actions + Webhook) para de fato chamar `/webhook/zabbix`
- [ ] **Fechamento automático do alerta no Zabbix** após a execução (Zabbix Sender/API), reportando o resultado

## 🔲 Pendente — próximas fases (roadmap em `andamento.md`)

- [ ] Interface de atendimento via Teams
- [ ] Camada de IA local (Ollama) com Function Calling para interpretar pedidos em linguagem natural
- [ ] Módulo de captura de tela (bypass de Sessão 0 via Tarefa Agendada/PsExec + prompt de consentimento LGPD)
- [ ] Forma de rodar o serviço em produção (Tarefa Agendada/NSSM como serviço Windows, ou container)

## 🔲 Vale considerar

- [ ] Definir `WEBHOOK_TOKEN` antes de expor a API fora do seu notebook — sem ele, o endpoint fica sem autenticação (hoje só loga um aviso)
- [ ] `langchain`, `ollama`, `reportlab`, `requests` já estão nas dependências mas ainda não são usados no código (são da Fase 2/3) — não é problema agora, mas evite deixar por muito tempo sem uso
- [ ] Validar o campo `severity` contra os valores reais que o Zabbix envia (hoje aceita qualquer string)
- [ ] Voltar o repositório para privado assim que não precisar mais do link público de compartilhamento
