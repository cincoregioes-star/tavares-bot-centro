# TAVARES Bot — Conversa GPT dentro da plataforma

Este módulo usa o **Codex CLI autenticado com a conta do ChatGPT** por meio de um programa Python local.

## Pré-requisitos (Windows 10/11)
1. Instale o [Python 3](https://www.python.org/downloads/windows/) (marque **Add Python to PATH**).
2. Instale o [Node.js LTS](https://nodejs.org/) para obter o comando npm.
3. Abra o PowerShell ou Terminal e execute:
   ```powershell
   npm install -g @openai/codex
   codex login
   ```
   Quando solicitado, escolha **Sign in with ChatGPT** e faça o login.
4. Baixe **Code → Download ZIP** do repositório e extraia a pasta, ou use `git clone`:
   https://github.com/cincoregioes-star/tavares-bot-centro
5. Dentro da pasta extraída, dê dois cliques em **INICIAR-TAVARES-GPT.bat**.
6. No navegador, abra **http://127.0.0.1:8765/assistente-gpt.html**.
7. Acesse a conversa, escolha a pasta do projeto e envie sua mensagem. Para criar ou alterar arquivos, selecione o modo **Desenvolver**.

## Como funciona
- O conector hospeda a interface em `127.0.0.1:8765` e executa a CLI já autenticada.
- Não utiliza nenhuma `OPENAI_API_KEY`; o login é feito diretamente no Codex.
- O uso é limitado pelas condições e cotas do seu plano ChatGPT.
- No modo **Conversar**, o Codex usa um ambiente de leitura; no modo **Desenvolver**, escreve em `projetos-locais/NOME/`.
- Não instala pacotes automaticamente nem publica código.
- Mantenha o terminal aberto enquanto estiver conversando.
- Se aparecer **Codex desconectado**, execute `codex login status` e, se necessário, `codex login`.
- No navegador online GitHub Pages, conexões a recursos locais podem ser bloqueadas. **Prefira a página hospedada pelo próprio servidor local**.
- O Codex tem autonomia para alterar arquivos *dentro do espaço de trabalho do projeto* no modo Desenvolver. Faça cópias de segurança.
- O primeiro acesso depende da instalação de Python/Node/Codex; não é uma solução puramente hospedada no GitHub Pages.

## Segurança
- Sem acesso remoto: o servidor escuta apenas `127.0.0.1`.
- Somente origens esperadas podem enviar mensagens para o conector.
- Não compartilhe o terminal com terceiros e não coloque senhas nos prompts.
- O código gerado **não é publicado nem testado automaticamente**.

## Documentação
- Codex CLI: https://developers.openai.com/codex/cli/
- Codex modo não interativo: https://developers.openai.com/codex/non-interactive/
