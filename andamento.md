# Andamento do Projeto

## Status atual (2026-08-28)

- Ambiente migrado para `uv` (já vinha com `pyproject.toml` + `uv.lock`; `.venv` recriado via `uv sync`).
- Logging estruturado implementado (`core/logging_config.py`): console + arquivo rotativo em `logs/agente.log`, nível configurável via `LOG_LEVEL`. `main.py` e `core/executor.py` usam o logger em vez de `print()`.
- Corrigido nome do arquivo `scripts/comandos.json` (estava salvo com caracteres de árvore de diretório no nome).
- Projeto movido para repositório Git privado no GitHub (antes só existia localmente no notebook de casa).

### Próximo passo prático

Rodar a aplicação com `uv run uvicorn main:app --reload` e usar Postman, Thunder
Client ou curl para simular um envio de JSON do Zabbix para a rota
`/webhook/zabbix` (ver exemplo no [README](README.md)).

---

## Roteiro de Implementação do Projeto: Agente Autônomo e Help Desk

### Fase 0: Infraestrutura e Regras Locais do Sistema Operacional

Contexto de Serviço do Windows: Quando o agente Zabbix roda um comando, ele geralmente roda como o usuário Local System ou Network Service. Descubra como os seus comandos PowerShell se comportam sob esses usuários (por exemplo, a variável $env:TEMP apontará para o Temp do sistema, e não do usuário logado).

Execution Policies do PowerShell: Como contornar ou assinar scripts para que o Windows não bloqueie a execução via automação.

Concorrência e Locks de Arquivo: O seu script 4 já lida com arquivos bloqueados caso os navegadores estejam abertos. Na vida real, o agente precisará decidir se ele força o fechamento do navegador do usuário (o que pode causar irritação) ou se ele agenda a limpeza para o próximo boot.

### Fase 1: Integração com o Monitoramento (Zabbix)

Zabbix Actions & Remote Commands: Como configurar o Zabbix para rodar comandos localmente na máquina quando uma "Trigger" (alerta) é ativada.

Zabbix Webhooks: Como fazer o Zabbix disparar um payload JSON (contendo o nome da máquina, o erro e o contexto) para uma API externa assim que o disco C: atingir 95% de uso, por exemplo.

Zabbix Sender / Zabbix API: Como o seu agente, após terminar a limpeza, pode devolver a informação para o Zabbix (ex: "Feche o alerta, liberei 2GB").

### Fase 2: Inteligência e Orquestração (O Cérebro do Agente)

APIs RESTful (FastAPI): O seu agente precisará de uma porta de entrada para receber as requisições web do Zabbix ou de um chat de Help Desk.

Modelos Locais (Ollama): Caso o chatbot precise processar linguagem natural de forma segura e local, sem enviar dados de infraestrutura da empresa cliente para a nuvem.

Bancos de Dados Vetoriais (ChromaDB) e Orquestração (LangChain): Para criar um sistema onde o chatbot "entende" o problema. Você pode indexar as descrições que já escreveu para o seu PDF, como as definições de esvaziamento de lixeira e limpeza de arquivos recentes.

Function Calling / Tool Use (A Abordagem Moderna de Agentes): Se o agente for interagir com humanos no Help Desk e você quiser usar IA, o mercado atual tem se afastado do RAG clássico (Bancos Vetoriais) para tarefas de execução e focado em Function Calling.

Como funciona (Function Calling): Você não indexa os scripts em um ChromaDB. Em vez disso, você fornece ao LLM (seja local via Ollama ou externo) um System Prompt contendo a descrição das suas funções em formato JSON. Quando o usuário digita "Meu navegador travou", o LLM processa o texto e, em vez de responder com texto livre, ele devolve uma chamada de função estruturada: {"action": "limpar_cache_navegadores", "target": "chrome"}.

Vantagem (Function Calling): O modelo de linguagem entende o contexto (a semântica), mas a decisão de qual script rodar é mapeada diretamente para as funções do seu código, eliminando a etapa de calcular similaridade de vetores.

### Fase 3: Help Desk, Interface e Funcionalidades Avançadas

Interface de Atendimento: O help desk será pelo Teams.

Auditoria e Logs: A função executar_limpeza gera um dicionário com sucesso, tempo e megabytes liberados. **(Concluído em 2026-08-28: logging estruturado via `core/logging_config.py`, arquivo rotativo em `logs/agente.log`.)**

Destino da Imagem Visual: Provavelmente, o agente enviaria a imagem diretamente para dentro de um chamado no sistema de Help Desk.

#### Módulo de Captura de Tela (Print Screen)

O Problema Arquitetural: O agente do Zabbix roda como um serviço de background (geralmente sob o usuário SYSTEM). Desde o Windows Vista, os serviços rodam na Sessão 0, que não tem interface gráfica. O usuário humano fica na Sessão 1, 2, etc. Se o Zabbix rodar o script de print na Sessão 0, você vai receber uma imagem totalmente preta.

A lógica Visual: O script precisará chamar essas classes, capturar as dimensões do monitor principal, "desenhar" a tela em um objeto de bitmap e salvar esse arquivo em um formato comprimido (como JPG ou PNG) em uma pasta temporária.

**Resultados das Pesquisas e Resoluções Técnicas:**

1. **Integração do PowerShell com System.Drawing e System.Windows.Forms** (Como fazer o print)

   Para realizar essa tarefa via script, você deve carregar os assemblies do .NET no PowerShell. O fluxo básico é:

   - Usar `Add-Type -AssemblyName System.Windows.Forms, System.Drawing` para ativar as classes.
   - Capturar o tamanho da tela com `[System.Windows.Forms.Screen]::PrimaryScreen.Bounds`.
   - Criar um objeto de imagem em branco (Bitmap) e um objeto de desenho (Graphics).
   - Usar o método `$graphics.CopyFromScreen()` para transferir a tela para o Bitmap e usar `.Save("C:\temp\print.png")` para guardar o arquivo.

2. **Como executar o script no contexto do usuário logado** (Bypass da Sessão 0)

   Como o Zabbix fica cego na Sessão 0, você não pode rodar o comando de print diretamente. As formas mais eficazes de contornar isso são:

   - Tarefas Agendadas (Task Scheduler): O Zabbix aciona um script que cria rapidamente uma Tarefa Agendada no Windows configurada para rodar como o "Usuário Logado no Momento". A tarefa roda o script do print (na Sessão 1) e depois se autoexclui.
   - Sysinternals PsExec: Você pode usar o utilitário oficial da Microsoft executando `psexec.exe -i -s powershell.exe -File meupript.ps1`. A flag `-i` força a execução de forma interativa na sessão do usuário.

3. **Como enviar a imagem gerada para o Zabbix, Python ou Teams**

   - Via PowerShell: Você pode usar o comando `Invoke-RestMethod` passando a imagem convertida para Base64 ou via formulário multipart/form-data diretamente para a API (webhook) do Teams ou da sua FastAPI.
   - Via Python: É muito mais simples. Com a biblioteca requests, basta abrir o arquivo salvo com `open('print.png', 'rb')` e enviá-lo em um POST request na chave `files={'file': arquivo}` para o seu sistema de chamados.

4. **Privacidade e Consentimento** (Como criar o prompt)

   Para não ferir regras de privacidade (LGPD), você pode fazer o PowerShell abrir uma caixa de diálogo nativa na tela do usuário antes de rodar o comando do print. Isso é feito com o comando `[System.Windows.Forms.MessageBox]::Show("A equipe de TI solicita um print da sua tela. Autoriza?", "Help Desk", "YesNo")`. O script recebe a variável da resposta; se o usuário clicar em "Sim", o script continua e tira o print. Se clicar em "Não" (ou não responder em X segundos), o script cancela a ação e avisa o Zabbix.
