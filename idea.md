# Objetivo 
Desenvolver uma aplicação que será responsável por receber um incidente do Jira, resolver o problema automaticamente, e abrir uma pull request com a correção na codebase correta.

## Ferramentas envolvidas
1. Slack
2. Jira
3. Github
4. Sistema de Arquivos do Linux
5. Claude Code (Ou outros gerenciadores de LLM)
6. LLM's
7. Protocolo MCP

## Método de conexão com as ferramentas
O MCP deverá ser usado para se integrar as ferramentas e cumprir o objetivo da aplicação. Irá realizar uma integração com API's tradicionais somente se não houver integração com MCP disponível para aquela ferramenta.

## Descrição do funcionamento
Haverá um grupo no slack chamado "AI Resolver", um usuário irá interagir com o bot para recuperar os incidentes que estão em "TODO" no board de Incidentes do Jira, exemplo:

`/list-open-incidents` Lista todos os incidentes abertos e prontos para iniciar uma correção

Com a lista de incidentes, o usuário poderá optar por corrigir um incidente específico, exemplo:

`/resolve-incident IN-XXX` (onde XXX corresponde ao ID do incidente no Jira)

O bot, usando o protocolo MCP, irá enviar a descrição desse incidente para um servidor específico que contém a LLM local, gerenciada pelo Claude Caude ou outro gerenciador de LLM para resolver o problema.

## Do lado do servidor
O servidor receberá a descrição do incidente, processará a informação usando a LLM local e identificará qual é o repositório relacionado ao problema. Se ele não existir, o servidor irá realizar um git clone do projeto relacionado usando o git client.

Realizará a correção seguindo os critérios estabelecidos na tarefa e então, abrir uma pull request para as branches master, stage e integration do repositório em que atuou.

## Desenvolvimento
Realize o desenvolvimento da aplicação seguindo as diretrizes e critérios estabelecidos, garantindo a integração correta com as ferramentas mencionadas e o uso eficiente do protocolo MCP. Neste repositório pode desenvolver todos os projetos, como:

1. Integração entre Slack e Jira
2. Desenvolvimento do servidor que processa os incidentes e interage com a LLM local
3. Implementação do protocolo MCP para comunicação entre as ferramentas

## Stack
A única restrição é que você deve realizar o desenvolvimento das integrações e do server utilizando a linguagem Python.