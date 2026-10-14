#!/usr/bin/env python3
"""TAVARES Bot: ponte local para o Codex autenticado pelo ChatGPT.

Sem OPENAI_API_KEY. Porta apenas em 127.0.0.1.
Requer Codex CLI instalado e login com ChatGPT.
"""
import http.server
import json
import mimetypes
import os
import pathlib
import re
import shutil
import subprocess
import threading
import urllib.parse
import webbrowser
from datetime import datetime

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parent
WORKSPACE = ROOT / "projetos-locais"
PORT = int(os.environ.get("TAVARES_PORT", "8765"))
ALLOWED_ORIGINS = {
    "http://127.0.0.1:" + str(PORT),
    "http://localhost:" + str(PORT),
    "https://cincoregioes-star.github.io"
}
FILE_TYPES = {".html", ".css", ".js", ".json", ".txt", ".md", ".svg", ".png", ".jpg", ".jpeg", ".webp"}
WORKSPACE.mkdir(parents=True, exist_ok=True)


def codex_path():
    # shutil.which encontra .cmd no Windows via PATHEXT.
    return shutil.which("codex") or shutil.which("codex.cmd")


def clean_project(value):
    value = str(value or "novo-projeto").strip().lower()
    value = re.sub(r"[^a-z0-9_-]", "-", value)[:55].strip("-_")
    return value or "novo-projeto"


def project_dir(name):
    p = WORKSPACE / clean_project(name)
    p.mkdir(parents=True, exist_ok=True)
    return p


def codex_status():
    cli = codex_path()
    if not cli:
        return {"installed": False, "authenticated": False,
                "message": "Codex não encontrado. Instale a Codex CLI e entre com sua conta ChatGPT."}
    try:
        result = subprocess.run([cli, "login", "status"], capture_output=True, text=True,
                                timeout=15, shell=False)
        signed = result.returncode == 0
        return {"installed": True, "authenticated": signed,
                "message": "Codex conectado à conta ChatGPT." if signed else
                "Codex instalado, mas ainda não autenticado. Execute codex login."}
    except Exception:
        return {"installed": True, "authenticated": False,
                "message": "Não foi possível conferir o login. Execute codex login no terminal."}


class Handler(http.server.BaseHTTPRequestHandler):
    server_version = "TavaresLocalBridge/1.0"

    def log_message(self, fmt, *args):
        # Evita imprimir prompts ou URLs com dados pessoais nos logs.
        if not str(args[0] if args else "").startswith("GET /api/chat"):
            super().log_message(fmt, *args)

    def origin(self):
        return self.headers.get("Origin", "")

    def cors(self):
        origin = self.origin()
        if origin in ALLOWED_ORIGINS:
            self.send_header("Access-Control-Allow-Origin", origin)
            self.send_header("Vary", "Origin")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.send_header("Access-Control-Allow-Private-Network", "true")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Cache-Control", "no-store")

    def json_out(self, body, status=200):
        raw = json.dumps(body, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.cors()
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(raw)))
        self.end_headers()
        self.wfile.write(raw)

    def denied(self):
        self.json_out({"error": "Origem não autorizada."}, 403)

    def valid_origin(self):
        # Navegadores enviam Origin em POST/CORS.
        return self.origin() in ALLOWED_ORIGINS

    def do_OPTIONS(self):
        if not self.valid_origin():
            self.denied()
            return
        self.send_response(204)
        self.cors()
        self.send_header("Content-Length", "0")
        self.end_headers()

    def do_GET(self):
        path = urllib.parse.urlparse(self.path).path
        if path == "/api/status":
            self.json_out(codex_status())
            return
        if path == "/api/projects":
            items = sorted([p.name for p in WORKSPACE.iterdir() if p.is_dir()])
            self.json_out({"projects": items[:100]})
            return
        if path == "/" or path == "/assistente-gpt.html":
            self.serve(ROOT / "assistente-gpt.html")
            return
        if path.startswith("/files/"):
            parts = path.removeprefix("/files/").split("/")
            if len(parts) < 2 or parts[0] != clean_project(parts[0]) or any(
                p.startswith(".") or p in ("", "..") for p in parts
            ):
                self.json_out({"error": "Caminho inválido."}, 400)
                return
            requested = (WORKSPACE / "/".join(parts)).resolve()
            base = (WORKSPACE / parts[0]).resolve()
            if not requested.is_relative_to(base) or requested.suffix.lower() not in FILE_TYPES:
                self.json_out({"error": "Arquivo não permitido."}, 403)
                return
            self.serve(requested)
            return
        self.json_out({"error": "Rota não encontrada."}, 404)

    def serve(self, path):
        if not path.is_file():
            self.json_out({"error": "Arquivo não encontrado."}, 404)
            return
        if path.stat().st_size > 2_000_000:
            self.json_out({"error": "Arquivo acima do limite."}, 413)
            return
        raw = path.read_bytes()
        mime = mimetypes.guess_type(path.name)[0] or "application/octet-stream"
        self.send_response(200)
        self.cors()
        self.send_header("Content-Type", mime + ("; charset=utf-8" if mime.startswith("text/") else ""))
        self.send_header("Content-Length", str(len(raw)))
        self.end_headers()
        self.wfile.write(raw)

    def do_POST(self):
        if urllib.parse.urlparse(self.path).path != "/api/chat":
            self.json_out({"error": "Rota desconhecida."}, 404)
            return
        if not self.valid_origin():
            self.denied()
            return
        try:
            size = int(self.headers.get("Content-Length", "0"))
        except ValueError:
            self.json_out({"error": "Tamanho inválido."}, 400)
            return
        if not 0 < size <= 24_000:
            self.json_out({"error": "Solicitação excedeu o limite."}, 413)
            return
        try:
            params = json.loads(self.rfile.read(size))
            message = str(params.get("message", "")).strip()
            kind = params.get("mode", "conversar")
            project = clean_project(params.get("project", "novo-projeto"))
            hist = params.get("history", [])
            if not 2 <= len(message) <= 6500 or kind not in ("conversar", "desenvolver"):
                raise ValueError("Informe uma mensagem válida.")
            if not isinstance(hist, list):
                hist = []
        except (ValueError, json.JSONDecodeError, TypeError) as ex:
            self.json_out({"error": str(ex)}, 400)
            return
        cli = codex_path()
        if cli is None:
            self.json_out({"error": "Codex não está instalado. Veja as instruções na página."}, 503)
            return

        target = project_dir(project)
        prompt = [
            "Você está integrado ao TAVARES Bot, um centro de criação de projetos. "
            "Responda em português brasileiro, explique limitações e nunca afirme "
            "que um código foi testado se não foi. A pasta do projeto é " + target.name + ". "
            "Não publique no GitHub e não instale programas, bibliotecas ou serviços.",
            "Modalidade: " + kind + ".",
            ("Se desenvolver: crie ou melhore arquivos reais HTML/CSS/JS APENAS na pasta "
             "atual deste projeto. Preserve arquivos existentes e trabalhe progressivamente. "
             "Ao final liste os arquivos alterados e o que precisa ser testado. "
             "Se conversar: explique e planeje sem editar arquivos.")
        ]
        if hist:
            prompt.append("Contexto recente da conversa:")
            for item in hist[-8:]:
                if isinstance(item, dict) and item.get("role") in ("user", "assistant"):
                    txt = str(item.get("text", ""))[:900]
                    prompt.append(item["role"] + ": " + txt)
        prompt.append("PEDIDO ATUAL:\n" + message)
        command = [cli, "exec", "--json", "--skip-git-repo-check",
                   "--sandbox", "workspace-write" if kind == "desenvolver" else "read-only",
                   "-"]
        try:
            process = subprocess.Popen(
                command, cwd=str(target), stdin=subprocess.PIPE,
                stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                text=True, encoding="utf-8", errors="replace",
                shell=False, bufsize=1)
        except (OSError, ValueError) as err:
            self.json_out({"error": "Não foi possível iniciar Codex: " + str(err)[:140]}, 500)
            return
        try:
            process.stdin.write("\n\n".join(prompt))
            process.stdin.close()
        except (OSError, BrokenPipeError):
            process.kill()
            self.json_out({"error": "Codex encerrou antes de receber a mensagem."}, 502)
            return

        self.send_response(200)
        self.cors()
        self.send_header("Content-Type", "text/event-stream; charset=utf-8")
        self.send_header("Connection", "close")
        self.send_header("X-Accel-Buffering", "no")
        self.end_headers()

        errors = []
        def drain_err():
            for line in process.stderr:
                if len(errors) < 12:
                    errors.append(line.strip()[:200])
        threading.Thread(target=drain_err, daemon=True).start()

        def stream(kind, value):
            body = json.dumps({"type": kind, "value": value}, ensure_ascii=False)
            self.wfile.write(("data: " + body + "\n\n").encode("utf-8"))
            self.wfile.flush()

        success = False
        got_text = False
        try:
            stream("progress", "Codex está analisando a solicitação…")
            for line in process.stdout:
                try:
                    event = json.loads(line)
                except json.JSONDecodeError:
                    continue
                event_type = event.get("type")
                if event_type == "item.completed":
                    item = event.get("item") or {}
                    if item.get("type") == "agent_message" and item.get("text"):
                        got_text = True
                        stream("answer", str(item["text"]))
                elif event_type == "turn.completed":
                    success = True
                elif event_type in ("turn.failed", "error"):
                    msg = (event.get("error") or {}).get("message", "") if isinstance(event.get("error"), dict) else ""
                    stream("progress", "Codex informou uma falha: " + str(msg)[:180])
            exitcode = process.wait(timeout=10)
            if success and exitcode == 0:
                stream("done", "Concluído." if got_text else "Turno concluído sem resposta textual.")
            else:
                stream("error", "A execução não terminou com sucesso. Confira o login pelo comando codex login.")
        except (BrokenPipeError, ConnectionResetError, OSError):
            process.kill()
        finally:
            try:
                process.wait(timeout=3)
            except subprocess.TimeoutExpired:
                process.kill()


if __name__ == "__main__":
    server = http.server.ThreadingHTTPServer(("127.0.0.1", PORT), Handler)
    print("TAVARES Bot + Codex: http://127.0.0.1:" + str(PORT) + "/assistente-gpt.html")
    print("Conector disponível SOMENTE neste computador. Pressione Ctrl+C para encerrar.")
    webbrowser.open("http://127.0.0.1:" + str(PORT) + "/assistente-gpt.html")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
