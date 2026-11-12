import os
import sys
import json
import hashlib
import urllib.request
import subprocess

try:
    sys.stdout.reconfigure(encoding='utf-8')
except Exception:
    pass

OWNER = "Bernalf5138"
REPO = "Bernal-Otimizacoes"
TAG = "v10.6"
NAME = "Bernal Otimizações PRO V10.6 Oficial"

FILES = [
    (os.path.join("dist", "BernalOtimizacoes.exe"), "BernalOtimizacoes.exe"),
    (os.path.join("dist", "Setup_Bernal_Otimizacoes_V10.6.exe"), "Setup_Bernal_Otimizacoes_V10.6.exe"),
]
HASH_ASSET = "BernalOtimizacoes.exe"


def get_git_token():
    p = subprocess.Popen(['git', 'credential', 'fill'], stdin=subprocess.PIPE,
                         stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    out, _ = p.communicate('protocol=https\nhost=github.com\n\n')
    for line in out.splitlines():
        if line.startswith('password='):
            return line.split('=', 1)[1].strip()
    return None


def sha256(path):
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        for blk in iter(lambda: f.read(1024 * 1024), b''):
            h.update(blk)
    return h.hexdigest()


def main():
    faltando = [fp for fp, _ in FILES if not os.path.exists(fp)]
    if faltando:
        print("❌ Os arquivos abaixo não existem ainda. Rode o build V10.6 primeiro:")
        for fp in faltando:
            print("   -", fp)
        return False

    asset_path = dict((a, fp) for fp, a in FILES)[HASH_ASSET]
    digest = sha256(asset_path)
    print(f"🔐 SHA-256 de {HASH_ASSET}: {digest}")

    token = get_git_token()
    if not token:
        print("❌ Token do GitHub não encontrado. Faça um 'git push' manual uma vez para salvar o login e tente de novo.")
        return False

    headers = {
        'Authorization': f'token {token}',
        'Accept': 'application/vnd.github.v3+json',
        'User-Agent': 'Bernal-Release-Publisher'
    }

    release_notes = f"""## 🔧 Bernal Otimizações Pro V10.6

- 🌙 **Modo Escuro agora muda de verdade na hora:** ao aplicar um wallpaper escuro/claro, a cor das janelas E da barra de tarefas troca na mesma hora (o Explorer é reiniciado automaticamente para aplicar o tema).
- ➕ **Meus Wallpapers:** importe qualquer imagem do seu PC para a galeria.
- ↩️ Tudo reversível no botão Reverter.

SHA256: {digest}
"""

    rel_url = f"https://api.github.com/repos/{OWNER}/{REPO}/releases"
    req = urllib.request.Request(rel_url, headers=headers)
    with urllib.request.urlopen(req) as resp:
        releases = json.loads(resp.read().decode('utf-8'))
    target = next((r for r in releases if r.get('tag_name') in (TAG, "10.6")), None)

    if not target:
        print(f"📦 Criando release {TAG}...")
        payload = {"tag_name": TAG, "target_commitish": "main", "name": NAME,
                   "body": release_notes, "draft": False, "prerelease": False}
        r = urllib.request.Request(rel_url, data=json.dumps(payload).encode('utf-8'), headers=headers, method='POST')
        with urllib.request.urlopen(r) as resp:
            target = json.loads(resp.read().decode('utf-8'))
        print(f"✅ Release {TAG} criada.")
    else:
        print(f"🔄 Atualizando release {TAG} existente...")
        up = f"https://api.github.com/repos/{OWNER}/{REPO}/releases/{target['id']}"
        payload = {"name": NAME, "body": release_notes}
        r = urllib.request.Request(up, data=json.dumps(payload).encode('utf-8'), headers=headers, method='PATCH')
        with urllib.request.urlopen(r) as resp:
            target = json.loads(resp.read().decode('utf-8'))
        print(f"✅ Release {TAG} atualizada.")

    upload_base = target['upload_url'].split('{')[0]

    for fpath, aname in FILES:
        for ex in target.get('assets', []):
            if ex.get('name') == aname:
                print(f"🗑️ Removendo asset anterior '{aname}'...")
                dreq = urllib.request.Request(
                    f"https://api.github.com/repos/{OWNER}/{REPO}/releases/assets/{ex['id']}",
                    headers=headers, method='DELETE')
                try:
                    urllib.request.urlopen(dreq)
                except Exception as e:
                    print(f"  aviso: {e}")

        fsize = os.path.getsize(fpath)
        print(f"🚀 Enviando '{aname}' ({fsize/(1024*1024):.1f} MB)...")
        up_headers = {
            'Authorization': f'token {token}',
            'Content-Type': 'application/octet-stream',
            'Content-Length': str(fsize),
            'User-Agent': 'Bernal-Release-Publisher'
        }
        with open(fpath, 'rb') as f_in:
            ureq = urllib.request.Request(f"{upload_base}?name={aname}", data=f_in, headers=up_headers, method='POST')
            with urllib.request.urlopen(ureq) as ur:
                res = json.loads(ur.read().decode('utf-8'))
                print(f"  ✅ {res.get('browser_download_url')}")

    print("\n🎉 Release V10.6 publicada! Os clientes nas versões antigas vão receber o aviso de atualização.")
    return True


if __name__ == '__main__':
    ok = main()
    try:
        input("\nEnter para sair...")
    except Exception:
        pass
    sys.exit(0 if ok else 1)
