"""Auditoria de repositórios públicos. Somente leitura nos projetos analisados."""
import json
import os
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone

OWNER = os.getenv("GITHUB_OWNER", "cincoregioes-star")
TOKEN = os.getenv("GITHUB_TOKEN", "")
HEADERS = {"Accept": "application/vnd.github+json", "User-Agent": "TAVARES-Bot"}
if TOKEN:
    HEADERS["Authorization"] = "Bearer " + TOKEN

def api(path):
    request = urllib.request.Request("https://api.github.com" + path, headers=HEADERS)
    try:
        with urllib.request.urlopen(request, timeout=25) as response:
            return json.load(response)
    except urllib.error.HTTPError as exc:
        if exc.code == 404:
            return None
        raise

def exists(repo, path, branch):
    q = urllib.parse.quote(path, safe="/")
    b = urllib.parse.quote(branch, safe="")
    return api("/repos/" + OWNER + "/" + urllib.parse.quote(repo, safe="") + "/contents/" + q + "?ref=" + b) is not None

repos = []
for page in range(1, 11):
    batch = api("/users/" + OWNER + "/repos?per_page=100&page=" + str(page))
    if not isinstance(batch, list):
        raise RuntimeError("Falha ao consultar a lista de repositórios")
    repos.extend(batch)
    if len(batch) < 100:
        break

if not repos:
    raise RuntimeError("Nenhum repositório encontrado: relatório anterior preservado")

items = []
for r in repos:
    name = r["name"]
    branch = r.get("default_branch") or "main"
    readme = exists(name, "README.md", branch)
    index = exists(name, "index.html", branch)
    workflow = exists(name, ".github/workflows", branch)
    alerts = []
    if not readme:
        alerts.append("README.md ausente na raiz")
    if not index:
        alerts.append("index.html ausente na raiz (pode usar outra estrutura)")
    if r.get("archived"):
        alerts.append("Repositório arquivado")
    items.append({
        "nome": name, "url": r["html_url"], "descricao": r.get("description"),
        "atualizado": r.get("pushed_at"), "arquivado": bool(r.get("archived")),
        "branch": branch, "readme_raiz": readme, "index_raiz": index,
        "workflows": workflow, "alertas": alerts
    })

now = datetime.now(timezone.utc).isoformat()
report = {"gerado_em": now, "usuario": OWNER, "total": len(items),
          "sem_readme_raiz": sum(not x["readme_raiz"] for x in items),
          "sem_index_raiz": sum(not x["index_raiz"] for x in items),
          "arquivados": sum(x["arquivado"] for x in items),
          "repositorios": items}
os.makedirs("data", exist_ok=True)
with open("data/auditoria.json", "w", encoding="utf-8") as f:
    json.dump(report, f, ensure_ascii=False, indent=2)
with open("data/RELATORIO.md", "w", encoding="utf-8") as f:
    f.write("# TAVARES Bot — Auditoria técnica\n\n")
    f.write("Gerado em UTC: " + now + "\n\n")
    f.write("**Repositórios:** " + str(len(items)) + " | **Sem README na raiz:** " +
            str(report["sem_readme_raiz"]) + " | **Sem index na raiz:** " +
            str(report["sem_index_raiz"]) + " | **Arquivados:** " + str(report["arquivados"]) + "\n\n")
    f.write("> A ausência de index.html ou README.md na raiz não prova defeito. Projetos podem ter outras estruturas.\n\n")
    f.write("| Repositório | README | index | Workflows | Alertas |\n|---|---|---|---|---|\n")
    for item in sorted(items, key=lambda x: x["nome"].lower()):
        mark = lambda b: "Sim" if b else "Não"
        alerts = "; ".join(item["alertas"]).replace("|", "/") or "—"
        f.write("| [" + item["nome"] + "](" + item["url"] + ") | " +
                mark(item["readme_raiz"]) + " | " + mark(item["index_raiz"]) +
                " | " + mark(item["workflows"]) + " | " + alerts + " |\n")
print("Auditoria concluída:", len(items), "repositórios")
