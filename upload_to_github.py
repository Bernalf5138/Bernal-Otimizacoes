import os
import sys
import json
import urllib.request
import subprocess

try:
    sys.stdout.reconfigure(encoding='utf-8')
except Exception:
    pass

def get_git_token():
    p = subprocess.Popen(['git', 'credential', 'fill'], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    out, err = p.communicate('protocol=https\nhost=github.com\n\n')
    for line in out.splitlines():
        if line.startswith('password='):
            return line.split('=', 1)[1].strip()
    return None

def upload_release_asset(owner, repo, release_tag, file_path, asset_name=None):
    token = get_git_token()
    if not token:
        print("❌ Erro: Token do GitHub não encontrado.")
        return False
        
    if not os.path.exists(file_path):
        print(f"❌ Erro: Arquivo {file_path} não encontrado.")
        return False

    if not asset_name:
        asset_name = os.path.basename(file_path)

    headers = {
        'Authorization': f'token {token}',
        'Accept': 'application/vnd.github.v3+json',
        'User-Agent': 'Bernal-Release-Uploader'
    }

    # 1. Localiza a Release
    rel_url = f"https://api.github.com/repos/{owner}/{repo}/releases"
    req = urllib.request.Request(rel_url, headers=headers)
    with urllib.request.urlopen(req) as resp:
        releases = json.loads(resp.read().decode('utf-8'))

    target_rel = None
    for r in releases:
        if r.get('tag_name') == release_tag or r.get('tag_name') == f"v{release_tag}":
            target_rel = r
            break

    if not target_rel:
        print(f"❌ Release {release_tag} não encontrada no repositório.")
        return False

    release_id = target_rel['id']
    upload_url_template = target_rel['upload_url'] # e.g. https://uploads.github.com/.../assets{?name,label}
    upload_base = upload_url_template.split('{')[0]

    # 2. Deleta asset existente com mesmo nome se houver
    for existing_asset in target_rel.get('assets', []):
        if existing_asset.get('name') == asset_name:
            aid = existing_asset['id']
            print(f"🗑️ Removendo asset antigo '{asset_name}' (ID {aid})...")
            del_url = f"https://api.github.com/repos/{owner}/{repo}/releases/assets/{aid}"
            del_req = urllib.request.Request(del_url, headers=headers, method='DELETE')
            urllib.request.urlopen(del_req)
            print("✅ Asset antigo removido com sucesso!")

    # 3. Faz o upload do novo binário
    file_size = os.path.getsize(file_path)
    print(f"🚀 Enviando novo '{asset_name}' ({file_size / (1024*1024):.2f} MB) para a Release {release_tag}...")

    upload_url = f"{upload_base}?name={asset_name}"
    upload_headers = {
        'Authorization': f'token {token}',
        'Content-Type': 'application/octet-stream',
        'Content-Length': str(file_size),
        'User-Agent': 'Bernal-Release-Uploader'
    }

    with open(file_path, 'rb') as f_data:
        upload_req = urllib.request.Request(upload_url, data=f_data, headers=upload_headers, method='POST')
        with urllib.request.urlopen(upload_req) as upload_resp:
            result = json.loads(upload_resp.read().decode('utf-8'))
            print(f"✅ SUCESSO! Asset publicado: {result.get('browser_download_url')}")

    # 4. Atualiza a descrição da release
    update_url = f"https://api.github.com/repos/{owner}/{repo}/releases/{release_id}"
    update_body = {
        "name": f"Bernal Otimizações PRO V{release_tag} Oficial",
        "body": """## ⚡ Bernal Otimizações Pro V9.1 Oficial
🔥 **Melhorias e Atualizações Desta Versão:**
- 🚫 **Zero Telas de CMD:** Eliminadas 100% das janelas que abriam/piscavam na tela.
- 🌐 **Telemetria de DNS Ultrarrápida:** Medição direta via socket TCP/UDP sem timeouts (Cloudflare, Google e Nativo).
- 🖼️ **Wallpapers 4K Restaurados:** Remoção completa da marca d'água com caractere quebrado.
- 🌿 **The Last of Us Exclusivo:** 3 Papéis de parede novos adicionados em categoria exclusiva (Ellie Violão, Joel & Ellie Seattle, Vaga-Lumes Neon).
- 🚀 **Auto-Updater Estabilizado:** Atualização direta em alta velocidade com reinício automático e seguro."""
    }
    update_data = json.dumps(update_body).encode('utf-8')
    update_headers = {
        'Authorization': f'token {token}',
        'Content-Type': 'application/json',
        'User-Agent': 'Bernal-Release-Uploader'
    }
    update_req = urllib.request.Request(update_url, data=update_data, headers=update_headers, method='PATCH')
    with urllib.request.urlopen(update_req) as resp:
        print("✅ Release notes e título atualizados no GitHub!")

    return True

if __name__ == '__main__':
    tag = sys.argv[1] if len(sys.argv) > 1 else "9.1"
    fpath = sys.argv[2] if len(sys.argv) > 2 else r"dist\BernalOtimizacoes.exe"
    upload_release_asset("Bernalf5138", "Bernal-Otimizacoes", tag, fpath)
