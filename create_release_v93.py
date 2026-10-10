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

def publish_v93_release():
    owner = "Bernalf5138"
    repo = "Bernal-Otimizacoes"
    tag = "v9.3"
    token = get_git_token()
    if not token:
        print("❌ Token do GitHub não encontrado.")
        return False

    headers = {
        'Authorization': f'token {token}',
        'Accept': 'application/vnd.github.v3+json',
        'User-Agent': 'Bernal-Release-Publisher'
    }

    # 1. Verifica se a release v9.3 já existe
    rel_url = f"https://api.github.com/repos/{owner}/{repo}/releases"
    req = urllib.request.Request(rel_url, headers=headers)
    with urllib.request.urlopen(req) as resp:
        releases = json.loads(resp.read().decode('utf-8'))

    target_rel = None
    for r in releases:
        if r.get('tag_name') in [tag, "9.3"]:
            target_rel = r
            break

    release_notes = """## ⚡ Bernal Otimizações Pro V9.3 Oficial (Edição Definitiva)
🔥 **Novidades & Correções Desta Versão:**
- 🖼️ **30 Wallpapers 4K Exclusivos:** Galeria completa expandida com até 5 cenas épicas por categoria (The Last of Us, Bernal Oficial, Futebol EA FC, Carros & Drift, Anime Cibernético, Retrô Arcade, Warzone FPS).
- ✨ **Marca d'Água Minimalista Elegante:** Todos os 30 papéis de parede contam com acabamento 'BERNAL OTIMIZAÇÕES PRO' minimalista e discreto no canto inferior direito.
- 🔔 **Alarme Gamer com Alerta Sonoro Alto (2s):** Notificação com alerta de alta penetração sonora de 2 segundos exatos em thread assíncrona, perfeito para não perder horários durante a gameplay.
- 🧠 **Expansor de Memória RAM Virtual (HD/SSD):** Alocação dinâmica de 8GB ou 16GB com feedback visual em tempo real no Card e no Painel de Telemetria de Hardware.
- 🚫 **Zero Telas Pretas CMD:** Todas as chamadas de sistema rodam 100% invisíveis em background.
- 🚀 **Sincronização Nuvem GitHub V9.3:** Versão atualizada em todos os módulos, instaladores e verificação automática."""

    if not target_rel:
        print(f"📦 Criando nova Release {tag} no GitHub...")
        create_payload = {
            "tag_name": tag,
            "target_commitish": "main",
            "name": "Bernal Otimizações PRO V9.3 Oficial",
            "body": release_notes,
            "draft": False,
            "prerelease": False
        }
        create_req = urllib.request.Request(rel_url, data=json.dumps(create_payload).encode('utf-8'), headers=headers, method='POST')
        with urllib.request.urlopen(create_req) as resp:
            target_rel = json.loads(resp.read().decode('utf-8'))
        print(f"✅ Release {tag} criada com sucesso!")
    else:
        print(f"🔄 Atualizando Release {tag} existente...")
        update_url = f"https://api.github.com/repos/{owner}/{repo}/releases/{target_rel['id']}"
        update_payload = {
            "name": "Bernal Otimizações PRO V9.3 Oficial",
            "body": release_notes
        }
        update_req = urllib.request.Request(update_url, data=json.dumps(update_payload).encode('utf-8'), headers=headers, method='PATCH')
        with urllib.request.urlopen(update_req) as resp:
            target_rel = json.loads(resp.read().decode('utf-8'))
        print(f"✅ Release {tag} atualizada!")

    release_id = target_rel['id']
    upload_url_template = target_rel['upload_url']
    upload_base = upload_url_template.split('{')[0]

    files_to_upload = [
        (r"dist\BernalOtimizacoes.exe", "BernalOtimizacoes.exe"),
        (r"dist\Setup_Bernal_Otimizacoes_V9.3.exe", "Setup_Bernal_Otimizacoes_V9.3.exe"),
        (r"dist\BernalOtimizacoes_V9.3.zip", "BernalOtimizacoes_V9.3.zip"),
    ]

    for fpath, aname in files_to_upload:
        if not os.path.exists(fpath):
            print(f"⚠️ Arquivo {fpath} não encontrado no disco para upload.")
            continue

        # Remove asset se já existir
        for existing in target_rel.get('assets', []):
            if existing.get('name') == aname:
                print(f"🗑️ Deletando versão anterior do asset '{aname}'...")
                del_url = f"https://api.github.com/repos/{owner}/{repo}/releases/assets/{existing['id']}"
                del_req = urllib.request.Request(del_url, headers=headers, method='DELETE')
                try:
                    urllib.request.urlopen(del_req)
                except Exception as e:
                    print(f"Aviso ao deletar: {e}")

        # Upload
        fsize = os.path.getsize(fpath)
        print(f"🚀 Enviando '{aname}' ({fsize/(1024*1024):.2f} MB) para a Release {tag}...")
        up_url = f"{upload_base}?name={aname}"
        up_headers = {
            'Authorization': f'token {token}',
            'Content-Type': 'application/octet-stream',
            'Content-Length': str(fsize),
            'User-Agent': 'Bernal-Release-Publisher'
        }
        with open(fpath, 'rb') as f_in:
            up_req = urllib.request.Request(up_url, data=f_in, headers=up_headers, method='POST')
            with urllib.request.urlopen(up_req) as up_resp:
                res = json.loads(up_resp.read().decode('utf-8'))
                print(f"✅ Concluído: {res.get('browser_download_url')}")

    print("🎉 TODAS AS ATUALIZAÇÕES V9.3 FORAM PUBLICADAS COM SUCESSO NO GITHUB!")
    return True

if __name__ == '__main__':
    publish_v93_release()
