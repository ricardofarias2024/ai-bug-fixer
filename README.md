# AI Bug Fixer

Automação para resolução de incidentes: recebe um incidente do Jira via Slack, processa a correção com Claude (Anthropic API) via MCP, aplica mudanças no repositório correto e abre Pull Requests automaticamente.

## Objetivo

O projeto implementa um fluxo fim a fim para:

1. Listar incidentes em aberto (TODO) no Jira.
2. Permitir que um usuário solicite a correção de um incidente específico pelo Slack.
3. Encaminhar os dados do incidente para o servidor MCP, que aciona a Anthropic API (Claude) via agentic loop.
4. Identificar o repositório afetado, preparar workspace local e aplicar correções.
5. Criar Pull Requests para as branches `master`, `stage` e `integration`.

## Ferramentas e Integrações

- **Slack**: interface de comando para operadores.
- **Jira**: origem dos incidentes.
- **GitHub**: criação de branches e Pull Requests.
- **Linux FS**: clonagem e manipulação local de repositórios.
- **Anthropic API** (Claude): geração e execução da estratégia de correção via agentic loop.
- **MCP (Model Context Protocol)**: camada principal de integração entre componentes.

> Regra de integração: usar MCP sempre que possível. APIs tradicionais devem ser usadas apenas quando não houver suporte MCP para a ferramenta.

## Fluxo Funcional

### 1) Operação via Slack

No canal/grupo **AI Resolver**, o usuário interage com comandos como:

- `/list-open-incidents` → lista incidentes em TODO prontos para correção.
- `/resolve-incident IN-XXX` → inicia resolução automática do incidente selecionado.

### 2) Processamento do incidente

Após receber `IN-XXX`, o backend:

1. Busca detalhes do incidente no Jira.
2. Envia contexto e critérios para o servidor MCP, que aciona a Anthropic API (Claude) em agentic loop.
3. Determina o repositório relacionado ao problema.
4. Caso necessário, realiza `git clone` do projeto.
5. Aplica correções com validações locais.
6. Abre Pull Requests para:
	- `master`
	- `stage`
	- `integration`

## Arquitetura (módulos deste repositório)

```text
ai-bug-fixer/
├── incident_processor/
│   ├── processor.py      # orquestração da resolução do incidente
│   ├── jira_client.py    # integração Jira
│   ├── git_manager.py    # operações git/repositório
│   └── pr_manager.py     # criação de Pull Requests
├── slack_bot/
│   ├── app.py            # comandos e interface Slack
│   └── mcp_client.py     # cliente MCP para comunicação com servidor
├── mcp_server/
│   └── server.py         # servidor MCP SSE — expõe list_open_incidents e process_incident
├── config.py             # configuração central
└── requirements.txt      # dependências Python
```

## Requisitos

- Python 3.10+
- Credenciais e acessos para Slack, Jira e GitHub
- Ambiente Linux com `git`
- Chave de API da Anthropic (`ANTHROPIC_API_KEY`)

## Configuração

1. Criar e ativar ambiente virtual Python.
2. Instalar dependências:

	```bash
	pip install -r requirements.txt
	```

3. Configurar variáveis de ambiente (copiar `.env.example` para `.env` e preencher):

	| Variável | Descrição |
	|---|---|
	| `SLACK_BOT_TOKEN` | Token do bot Slack (xoxb-…) |
	| `SLACK_SIGNING_SECRET` | Signing secret do app Slack |
	| `JIRA_SERVER` | URL base do Jira (ex.: `https://org.atlassian.net`) |
	| `JIRA_EMAIL` | E-mail da conta de serviço Jira |
	| `JIRA_API_TOKEN` | Token de API do Jira |
	| `JIRA_PROJECT_KEY` | Prefixo do projeto Jira (padrão: `IN`) |
	| `GITHUB_TOKEN` | Token de acesso pessoal do GitHub |
	| `GITHUB_ORG` | Organização/usuário do GitHub para fallback de clone |
	| `ANTHROPIC_API_KEY` | Chave de API da Anthropic (sk-ant-…) |
	| `ANTHROPIC_MODEL` | Modelo Claude a usar (padrão: `claude-sonnet-4-6`) |
	| `MCP_SERVER_HOST` | Host do servidor MCP (padrão: `localhost`) |
	| `MCP_SERVER_PORT` | Porta do servidor MCP (padrão: `8080`) |
	| `REPOS_DIR` | Diretório local para clones dos repositórios (padrão: `/tmp/ai-bug-fixer-repos`) |

4. Ajustar parâmetros em `config.py` conforme ambiente.

## Execução

Fluxo típico de execução:

1. Iniciar o servidor MCP.
2. Iniciar o bot do Slack.
3. Validar comando `/list-open-incidents` no Slack.
4. Executar `/resolve-incident IN-XXX` para testar o pipeline completo.

## Diretrizes de Desenvolvimento

- Linguagem principal obrigatória: **Python**.
- Priorizar comunicação entre componentes via **MCP**.
- Garantir rastreabilidade de cada incidente processado (logs e status).
- Falhas parciais devem ser tratadas com mensagens claras para operador.

## Roadmap sugerido

- [ ] Harden de autenticação/autorização por ferramenta.
- [ ] Estratégia de retries e circuit breaker para integrações externas.
- [ ] Testes automatizados (unitários e integração).
- [ ] Observabilidade (métricas, tracing e auditoria de ações).
- [ ] Política de segurança para execução de mudanças automáticas no código.

## Licença

Definir conforme política do projeto/organização.
