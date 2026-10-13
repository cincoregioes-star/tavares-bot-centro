# TAVARES Bot v5 — Painel e auditoria pública automatizada

## Abrir
Abra `index.html` diretamente no navegador. O logotipo oficial e os avatares estão incorporados ao arquivo, evitando imagens quebradas. O menu ☰, catálogo, dicionário, pesquisa e exportações funcionam offline.

## Auditoria real, gratuita e somente leitura
`python scripts/auditar.py` consulta a API pública do GitHub, enumera os repositórios públicos, verifica existência de `README.md` e `index.html` e, quando GitHub indica Pages, testa a URL publicada. Produz `data/auditoria.json` e `data/RELATORIO.md`. Não altera os repositórios auditados.

## Automatizar sem API paga
1. Crie um repositório **novo** para este centro e envie todo o conteúdo do ZIP, inclusive `.github/workflows/auditoria.yml`.
2. Em Settings → Actions → General, habilite leitura e escrita do token do workflow para permitir salvar os relatórios no **repositório do centro**. O workflow não recebe acesso de escrita aos outros repositórios.
3. Execute Actions → TAVARES Bot - Auditoria semanal → Run workflow. Depois, a auditoria roda às segundas-feiras, aproximadamente 08:17 (horário de Brasília; agendamentos podem atrasar).
4. Para visualizar os relatórios no painel web, ative GitHub Pages nesse novo repositório, publicando a raiz da branch padrão. No navegador local (`file://`), o painel continua funcional, mas o navegador normalmente impede carregar o JSON por fetch.

## Limites e segurança
- Verificar existência de arquivos não comprova a execução dos módulos, a ausência de vulnerabilidades ou a qualidade do código.
- O monitoramento é público; não inclui repositórios privados nem dados de conversas do ChatGPT.
- GitHub Actions e GitHub Pages têm limites e políticas de uso; não se garante custo zero para toda conta e volume.
- A análise não executa código de repositórios monitorados. Não use segredos no HTML ou no JSON público.
- Agentes de redação, programação e criação proativa continuam como **papéis planejados**, sem autonomia operacional nesta versão.
- Nenhum repositório GitHub foi criado ou alterado nesta entrega.

## Publicar e ativar (versão 6)
1. No GitHub, crie o repositório público **tavares-bot-centro** (sem adicionar README ou licença inicial).
2. Extraia este ZIP no computador. Envie os arquivos e pastas para a raiz do novo repositório, **incluindo a pasta oculta `.github`**. O envio pelo navegador pode exigir selecionar arquivos/pastas dentro da pasta extraída; confira se `.github/workflows/auditoria.yml` aparece no GitHub.
3. Em **Settings → Actions → General → Workflow permissions**, selecione **Read and write permissions** e salve. Se a opção não estiver disponível, a política da conta/organização deve ser ajustada pelo proprietário.
4. Em **Actions → TAVARES Bot - Auditoria semanal → Run workflow**, execute uma vez. Confira o relatório em `data/RELATORIO.md`. A agenda é segunda-feira às **11:17 UTC (08:17 Brasília)**, sujeita a atrasos do GitHub.
5. Em **Settings → Pages → Build and deployment**, escolha **Deploy from a branch**, branch padrão e pasta **/(root)**, e salve. O endereço esperado será `https://cincoregioes-star.github.io/tavares-bot-centro/` após publicação bem-sucedida; **não é um link confirmado até publicar**.
6. O workflow utiliza `GITHUB_TOKEN` automático da execução para evitar o limite baixo de consultas anônimas; não é necessário criar token pessoal nem pagar API. O token só grava relatórios neste novo repositório.

**Atenção:** Este ZIP está pronto para publicação, mas **a instalação/ativação na conta GitHub ainda depende da criação do novo repositório e do envio dos arquivos**.
