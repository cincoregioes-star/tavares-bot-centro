#!/usr/bin/env python3
"""TAVARES IA: projetos por linguagem natural, somente em branches para revisão."""
import json, os, pathlib, re, subprocess, urllib.parse, urllib.request, urllib.error

OWNER="cincoregioes-star"
REPO="tavares-bot-centro"
BASE="https://api.github.com/repos/"+OWNER+"/"+REPO
MARK="<!-- TAVARES_AI_REQUEST_V1 -->"
GITHUB_TOKEN=os.environ.get("GITHUB_TOKEN","")
OPENAI_KEY=os.environ.get("OPENAI_API_KEY","")
MODEL=os.environ.get("TAVARES_AI_MODEL","gpt-5-mini")

def gh(method,path,body=None):
    request=urllib.request.Request(BASE+path,
        data=json.dumps(body,ensure_ascii=False).encode() if body is not None else None,
        method=method,headers={"Authorization":"Bearer "+GITHUB_TOKEN,
        "Accept":"application/vnd.github+json",
        "X-GitHub-Api-Version":"2022-11-28","Content-Type":"application/json"})
    with urllib.request.urlopen(request,timeout=30) as reply:return json.load(reply)

def comment(num,message):
    gh("POST","/issues/"+str(num)+"/comments",{"body":message[:60000]})

def cmd(*args,check=True):
    return subprocess.run(args,check=check,text=True,capture_output=True)

def branch_for(number):
    name="tavares-ia/issue-"+str(number)
    cmd("git","config","user.name","github-actions[bot]")
    cmd("git","config","user.email","41898282+github-actions[bot]@users.noreply.github.com")
    status=cmd("git","ls-remote","--exit-code","--heads","origin",name,check=False)
    if status.returncode==0:
        cmd("git","fetch","origin",name)
        cmd("git","checkout","-B",name,"FETCH_HEAD")
    else:cmd("git","checkout","-b",name)
    return name

def generate(original,request,prior):
    schema={"type":"object","additionalProperties":False,"properties":{
        "summary":{"type":"string"},
        "files":{"type":"array","items":{"type":"object","additionalProperties":False,
            "properties":{"path":{"type":"string"},"content":{"type":"string"}},
            "required":["path","content"]}},
        "test_plan":{"type":"array","items":{"type":"string"}},
        "limitations":{"type":"string"}},
        "required":["summary","files","test_plan","limitations"]}
    instructions=(
        "Você é um desenvolvedor sênior do TAVARES Bot. Crie sistemas reais conforme "
        "o pedido do usuário, em português brasileiro. Não transforme projetos diferentes "
        "em um painel genérico de agenda, inspeções ou cadastros. "
        "Crie frontend HTML, CSS e JS completo, responsivo, acessível, com fluxo funcional, "
        "validações e tratamento de erros. Use APIs públicas legítimas quando possível. "
        "Quando exigir backend, login ou bancos de dados, explique claramente essa limitação "
        "e ofereça frontend funcional sem fingir que esses recursos existem. "
        "Sem serviços pagos, segredos, tokens, pacotes npm nem builds. "
        "Gere até dez arquivos completos, incluindo index.html, e referências locais corretas. "
        "Se for revisão, retorne o conjunto completo de arquivos atualizado. "
        "Seu resultado é um MVP para revisão, não uma versão testada/publicada. "
        "Não inclua dados pessoais reais nem alegue taxas, informações ou testes inventados."
    )
    input_data={"pedido_original":original[:9000],"nova_instrucao":request[:5000],
                "arquivos_anteriores":{k:v[:35000] for k,v in prior.items()}}
    payload={"model":MODEL,"instructions":instructions,
             "input":json.dumps(input_data,ensure_ascii=False),
             "max_output_tokens":16000,"store":False,
             "text":{"format":{"type":"json_schema","name":"tavares_project",
                     "schema":schema,"strict":True}}}
    req=urllib.request.Request("https://api.openai.com/v1/responses",
        data=json.dumps(payload,ensure_ascii=False).encode(),method="POST",
        headers={"Content-Type":"application/json","Authorization":"Bearer "+OPENAI_KEY})
    try:
        with urllib.request.urlopen(req,timeout=300) as response:output=json.load(response)
    except urllib.error.HTTPError as ex:
        raise RuntimeError("A API de IA retornou HTTP "+str(ex.code)+". Verifique modelo, saldo e limites.") from ex
    if output.get("status")!="completed":
        raise RuntimeError("A geração não foi concluída: "+str(output.get("status")))
    parts=[p.get("text","") for item in output.get("output",[]) if item.get("type")=="message"
           for p in item.get("content",[]) if p.get("type")=="output_text"]
    if not parts:raise RuntimeError("A IA retornou uma resposta vazia.")
    return json.loads("\n".join(parts))

def validate(files):
    if not isinstance(files,list) or not(1<=len(files)<=10):raise ValueError("Quantidade de arquivos inválida.")
    allowed={".html",".css",".js",".json",".md",".txt",".svg"}
    result={}
    total=0
    for f in files:
        name=f.get("path");content=f.get("content")
        if not isinstance(name,str) or not isinstance(content,str):raise ValueError("Formato de arquivo inválido.")
        name=name.replace("\\","/")
        parts=name.split("/")
        if(name.startswith("/") or len(name)>120 or any(x in ("..",".","") or x.startswith(".") for x in parts)
           or not re.fullmatch("[a-zA-Z0-9_./-]+",name)
           or pathlib.PurePosixPath(name).suffix.lower() not in allowed):raise ValueError("Nome recusado: "+name[:100])
        total+=len(content.encode())
        if len(content.encode())>150000 or total>400000:raise ValueError("Arquivos grandes demais.")
        result[name]=content
    if "index.html" not in result or "<html" not in result["index.html"].lower():
        raise ValueError("A IA não gerou index.html válido.")
    return result

def get_old(folder):
    old={}
    if folder.exists():
        for path in folder.rglob("*"):
            if path.is_file() and path.suffix.lower() in (".html",".css",".js",".md",".json"):
                if len(old)>=10:break
                content=path.read_text("utf-8",errors="replace")
                if len(content)<=40000:old[path.relative_to(folder).as_posix()]=content
    return old

def get_pr(num,branch,summary):
    prs=gh("GET","/pulls?head="+OWNER+":"+urllib.parse.quote(branch)+"&base=main&state=open")
    if prs:return prs[0]["html_url"]
    return gh("POST","/pulls",{
        "title":"TAVARES IA: Projeto #"+str(num),
        "head":branch,"base":"main","draft":True,
        "body":"Código gerado pela IA a partir da issue #"+str(num)+
        "\n\nResumo: "+summary[:1800]+"\n\nRevisar e testar antes de mesclar. Não executado automaticamente."
    })["html_url"]

def main():
    event=json.loads(pathlib.Path(os.environ["GITHUB_EVENT_PATH"]).read_text("utf-8"))
    issue=event.get("issue") or {}
    num=issue.get("number")
    if not isinstance(num,int) or issue.get("pull_request"):return
    if not issue.get("title","").startswith("[TAVARES-IA]"):return
    if MARK not in (issue.get("body") or ""):return
    if issue.get("user",{}).get("login","").lower()!=OWNER:return
    event_name=os.environ.get("GITHUB_EVENT_NAME")
    if event_name=="issues":instruction="Crie a primeira versão funcional deste projeto."
    elif event_name=="issue_comment":
        com=event.get("comment") or {}
        body=(com.get("body") or "").strip()
        if com.get("user",{}).get("login","").lower()!=OWNER or not body.lower().startswith("/ajustar "):return
        instruction=body[len("/ajustar "):].strip()
        if len(instruction)<5:return
    else:return
    if not OPENAI_KEY:
        comment(num,"A IA ainda não está configurada. O proprietário deve criar o segredo "
            "OPENAI_API_KEY em Settings > Secrets and variables > Actions. "
            "A API pode gerar cobranças. Após configurar, comente: /ajustar iniciar criação")
        return
    branch=branch_for(num)
    folder=pathlib.Path("projetos/ia")/str(num)
    try:
        output=generate(issue["body"],instruction,get_old(folder))
        files=validate(output["files"])
        folder.mkdir(parents=True,exist_ok=True)
        for filename,content in files.items():
            path=folder/filename
            path.parent.mkdir(parents=True,exist_ok=True)
            path.write_text(content,"utf-8")
        (folder/"PLANO_E_TESTES.json").write_text(json.dumps({
            "summary":output["summary"],"limitations":output["limitations"],
            "test_plan":output["test_plan"],"model":MODEL},ensure_ascii=False,indent=2),"utf-8")
        cmd("git","add","--",str(folder))
        if cmd("git","diff","--cached","--quiet",check=False).returncode!=0:
            cmd("git","commit","-m","feat: gerar projeto IA #"+str(num))
            cmd("git","push","-u","origin",branch)
        compare="https://github.com/"+OWNER+"/"+REPO+"/compare/main..."+branch+"?expand=1"
        try:link=get_pr(num,branch,output["summary"])
        except (urllib.error.HTTPError,urllib.error.URLError):link=compare
        tests="\n".join("- "+str(x)[:350] for x in output["test_plan"][:8])
        comment(num,"TAVARES IA: projeto gerado para revisão!\n\n"
            "Revisar o código: "+link+"\n\nResumo: "+output["summary"][:2200]+
            "\n\nArquivos: "+", ".join(files)+
            "\n\nTestes sugeridos:\n"+tests+
            "\n\nLimitações: "+output["limitations"][:1200]+
            "\n\nO código está em uma branch; ainda NÃO foi publicado. "
            "Para pedir alterações, comente: /ajustar descreva a mudança. "
            "A publicação só ocorrerá após a sua aprovação.")
    except Exception as ex:
        print(type(ex).__name__+": "+str(ex)[:220])
        comment(num,"A geração não foi concluída: "+str(ex)[:350]+
                "\nVerifique a configuração e tente comentar: /ajustar gere uma versão inicial simplificada")
        raise

if __name__=="__main__":main()
