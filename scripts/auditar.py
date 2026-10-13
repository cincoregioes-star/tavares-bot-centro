import json
import os
import urllib.request
from datetime import datetime, timezone

owner = "cincoregioes-star"
headers = {"Accept": "application/vnd.github+json", "User-Agent": "TAVARES-Bot"}
token = os.environ.get("GITHUB_TOKEN")
if token:
    headers["Authorization"] = "Bearer " + token

repos = []
for page in range(1, 11):
    url = "https://api.github.com/users/" + owner + "/repos?per_page=100&page=" + str(page)
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req, timeout=30) as response:
        batch = json.load(response)
    repos.extend(batch)
    if len(batch) < 100:
        break

if not repos:
    raise RuntimeError("Nenhum repositório encontrado")
os.makedirs("data", exist_ok=True)
items = [{"nome": r["name"], "url": r["html_url"], "descricao": r.get("description"), "atualizado": r.get("pushed_at")} for r in repos]
report = {"gerado_em": datetime.now(timezone.utc).isoformat(), "total": len(items), "repositorios": items}
with open("data/auditoria.json", "w", encoding="utf-8") as output:
    json.dump(report, output, ensure_ascii=False, indent=2)
with open("data/RELATORIO.md", "w", encoding="utf-8") as output:
    output.write("# Auditoria semanal TAVARES Bot\n\n")
    output.write("Total de repositórios: " + str(len(items)) + "\n\n")
    for item in items:
        output.write("- [" + item["nome"] + "](" + item["url"] + ")\n")
print("Auditoria concluída:", len(items))
