"""Extrai os textos que aparecem na tela (OtimizadorGamer.py e extras.py) para i18n_catalogo.json.

Rode de novo depois de mudar textos do app: os que ainda não têm tradução em traducoes_data.py
ficam listados em i18n_faltando.json para traduzir.
    python i18n_extrair.py
"""
import ast
import json
import os
import re
import sys

AQUI = os.path.dirname(os.path.abspath(__file__))
ARQUIVOS = ["OtimizadorGamer.py", "extras.py"]

# Coisas que são comandos, caminhos ou chaves internas, nunca texto de tela
NAO_TELA = re.compile(
    r"(^|[\s\"'])(powershell|reg (add|delete|query)|cmd(\.exe)?\s*/|sc (config|start|stop|query)|netsh|bcdedit|fsutil|"
    r"schtasks|wmic|taskkill|chkdsk|robocopy|start \"\"|del /|copy /|rmdir|winget|Set-|Get-|Stop-|Start-|Remove-|New-|"
    r"Disable-|Enable-|Invoke-|Optimize-|Add-|Clear-|-Command|-NoProfile|-ExecutionPolicy)"
    r"|HKEY_|HKLM|HKCU|\\\\|[A-Za-z]:\\|://|\.(exe|png|jpg|json|bat|ps1|dll|ico|txt|log|apbx|sys|reg)\b|\$env:|%[A-Z]+%",
    re.I)


def _e_texto(s):
    t = s.strip()
    if len(t) < 2 or not re.search(r"[A-Za-zÀ-ÿ]", t):
        return False
    if NAO_TELA.search(t):
        return False
    if re.fullmatch(r"[a-z0-9_./\-]+", t):          # chaves internas: "futebol", "btn_trial", "lol.exe"
        return False
    if re.fullmatch(r"#[0-9A-Fa-f]{3,8}", t):       # cores
        return False
    if " " not in t and (re.search(r"[a-z][A-Z]", t) or re.search(r"\w[.\\_]\w", t) or "*" in t):
        return False                                # nomes internos: dmFields, Microsoft.Xbox..., SteamLibrary\...
    if re.fullmatch(r"[A-Z0-9_]{2,}", t):           # constantes: "SSD", "NTFS"
        return False
    return True


def _docstrings(tree):
    ids = set()
    for n in ast.walk(tree):
        if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef, ast.Module)) and n.body:
            b = n.body[0]
            if isinstance(b, ast.Expr) and isinstance(b.value, ast.Constant) and isinstance(b.value.value, str):
                ids.add(id(b.value))
    return ids


def extrair():
    simples, modelos = {}, {}
    for nome in ARQUIVOS:
        src = open(os.path.join(AQUI, nome), encoding="utf-8").read()
        tree = ast.parse(src)
        docs = _docstrings(tree)
        dentro_fstring = set()
        for n in ast.walk(tree):
            if isinstance(n, ast.JoinedStr):
                partes, i = [], 0
                for v in n.values:
                    if isinstance(v, ast.Constant):
                        dentro_fstring.add(id(v))
                        partes.append(v.value.replace("{", "{{").replace("}", "}}"))
                    else:
                        partes.append("{%d}" % i)
                        i += 1
                modelo = "".join(partes)
                estatico = re.sub(r"\{\d+\}", "", modelo)
                if i and _e_texto(estatico):
                    modelos[modelo] = None
                elif not i and _e_texto(modelo):
                    simples[modelo.replace("{{", "{").replace("}}", "}")] = None
        for n in ast.walk(tree):
            if isinstance(n, ast.Constant) and isinstance(n.value, str) and id(n) not in docs and id(n) not in dentro_fstring:
                if _e_texto(n.value):
                    simples[n.value] = None
    return sorted(simples), sorted(modelos)


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    simples, modelos = extrair()
    with open(os.path.join(AQUI, "i18n_catalogo.json"), "w", encoding="utf-8") as f:
        json.dump({"simples": simples, "modelos": modelos}, f, ensure_ascii=False, indent=1)
    # Já tratados: tudo da lista congelada (traduzido ou marcado "=") + o que está em extra.json
    feitos = set()
    base = os.path.join(AQUI, "i18n_trad", "catalogo_base.json")
    if os.path.exists(base):
        b = json.load(open(base, encoding="utf-8"))
        feitos.update(b["simples"] + b["modelos"])
    extra = os.path.join(AQUI, "i18n_trad", "extra.json")
    if os.path.exists(extra):
        feitos.update(json.load(open(extra, encoding="utf-8")))
    falt = {"simples": [s for s in simples if s not in feitos], "modelos": [m for m in modelos if m not in feitos]}
    with open(os.path.join(AQUI, "i18n_faltando.json"), "w", encoding="utf-8") as f:
        json.dump(falt, f, ensure_ascii=False, indent=1)
    print(f"textos: {len(simples)} | modelos com variáveis: {len(modelos)} | faltando traduzir: "
          f"{len(falt['simples'])} + {len(falt['modelos'])}")
