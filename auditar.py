#!/usr/bin/env python3
"""Auditoria pública, somente leitura, sem dependências externas e sem IA paga."""
import datetime as dt,json,os,re,urllib.request,urllib.error,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
OWNER=os.getenv('GITHUB_OWNER','cincoregioes-star')
TOKEN=os.getenv('GH_AUDIT_TOKEN') or os.getenv('GITHUB_TOKEN','')
HEADERS={'Accept':'application/vnd.github+json','User-Agent':'TAVARES-Bot-Auditor/1.0'}
if TOKEN:HEADERS['Authorization']='Bearer '+TOKEN

def get(url):
    request=urllib.request.Request(url,headers=HEADERS)
    try:
        with urllib.request.urlopen(request,timeout=14) as response:
            return json.loads(response.read()),response.status,None
    except urllib.error.HTTPError as exc:
        return None,exc.code,str(exc)
    except Exception as exc:
        return None,None,str(exc)

def check_site(url):
    req=urllib.request.Request(url,headers={'User-Agent':'TAVARES-Bot-SiteCheck/1.0'})
    try:
        with urllib.request.urlopen(req,timeout=12) as response:
            return {'http':response.status,'url_final':response.url,'ok':200<=response.status<400}
    except urllib.error.HTTPError as e:return {'http':e.code,'ok':False}
    except Exception as e:return {'http':None,'ok':False,'erro':str(e)[:100]}

now=dt.datetime.now(dt.timezone.utc).isoformat()
records=[];page=1;errors=[]
while page<=5:
    payload,status,err=get(f'https://api.github.com/users/{OWNER}/repos?per_page=100&page={page}&type=owner&sort=updated')
    if not isinstance(payload,list):
        errors.append(f'Falha listando repositórios, página {page}: HTTP {status} {err}')
        break
    if not payload:break
    for repo in payload:
        name=repo['name'];entry={'nome':name,'url':repo.get('html_url'), 'descricao':repo.get('description'), 'linguagem':repo.get('language'), 'atualizado_em':repo.get('updated_at'), 'arquivado':repo.get('archived',False),'privado':repo.get('private',False),'branch':repo.get('default_branch'),'github_pages_url':f'https://{OWNER}.github.io/{name}/','status_site':'nao_verificado','readme':'nao_verificado','index':'nao_verificado'}
        # Checagem de arquivo por metadados; não executa código externo
        for filename,field in [('README.md','readme'),('index.html','index')]:
            _,s,e=get(f'https://api.github.com/repos/{OWNER}/{name}/contents/{filename}')
            entry[field]='presente' if s==200 else 'ausente' if s==404 else 'indeterminado'
        # Evita tratar ausência de site como erro do repositório: GitHub Pages é opcional
        if repo.get('has_pages'):
            site=check_site(entry['github_pages_url']);entry['site']=site;entry['status_site']='acessivel' if site['ok'] else 'falha_ou_indisponivel'
        else:entry['status_site']='pages_nao_indicado'
        records.append(entry)
    if len(payload)<100:break
    page+=1
    time.sleep(.2)

if not records:
    # preserva último relatório válido se a API estiver indisponível
    p=ROOT/'data/auditoria.json'
    if p.exists():
        print('API indisponível; relatório anterior preservado. '+str(errors));raise SystemExit(0)
    records=[{'nome':n,'url':f'https://github.com/{OWNER}/{n}','status_site':'nao_verificado','readme':'nao_verificado','index':'nao_verificado'} for n in json.loads((ROOT/'data/repositorios-iniciais.json').read_text())]

report={'gerado_em':now,'proprietario':OWNER,'total':len(records),'origem':'GitHub REST API' if not errors else 'Inventário de referência; API indisponível','erros':errors,'repositorios':records}
(ROOT/'data/auditoria.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
lines=['# Auditoria automática — TAVARES Bot','',f'Gerado em UTC: {now}',f'Repositórios: {len(records)}','', '> Inspeção automática de metadados, README, index e GitHub Pages indicado. Não comprova funcionamento interno, segurança integral nem qualidade do conteúdo.','', '| Repositório | README | index.html | Site |','|---|---|---|---|']
for r in records:lines.append(f"| [{r['nome']}]({r['url']}) | {r['readme']} | {r['index']} | {r['status_site']} |")
if errors:lines+=['','## Limitações da execução']+['- '+e for e in errors]
(ROOT/'data/RELATORIO.md').write_text('\n'.join(lines)+'\n')
print(f'Auditoria concluída: {len(records)} repositórios; {len(errors)} erro(s) de API')
