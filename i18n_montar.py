"""Junta os blocos de i18n_trad/bNNN.json (pares [espanhol, inglês] na ordem de i18n_catalogo.json)
e gera traducoes_data.py, que vai dentro do app.
    python i18n_montar.py
Cada bloco cobre 260 itens a partir de NNN da lista congelada i18n_trad/catalogo_base.json.
Frases novas do app vão em i18n_trad/extra.json (rode i18n_extrair.py para ver o que falta em i18n_faltando.json). "=" quer dizer "igual ao português".
"""
import glob
import json
import os
import re
import sys

AQUI = os.path.dirname(os.path.abspath(__file__))
BLOCO = 260


def _ajusta(pt, tr):
    """Copia os espaços/quebras de linha do começo e do fim do português para a tradução."""
    ini = pt[:len(pt) - len(pt.lstrip())]
    fim = pt[len(pt.rstrip()):]
    return ini + tr.strip() + fim


def montar():
    cat = json.load(open(os.path.join(AQUI, "i18n_trad", "catalogo_base.json"), encoding="utf-8"))
    itens = cat["simples"] + cat["modelos"]
    modelos = set(cat["modelos"])
    es, en, erros = {}, {}, []
    for arq in sorted(glob.glob(os.path.join(AQUI, "i18n_trad", "b*.json"))):
        ini = int(re.search(r"b(\d+)\.json$", arq).group(1))
        pares = json.load(open(arq, encoding="utf-8"))
        esperado = min(BLOCO, len(itens) - ini)
        if len(pares) != esperado:
            erros.append(f"{os.path.basename(arq)}: {len(pares)} itens, esperado {esperado}")
            continue
        for k, par in enumerate(pares):
            pt = itens[ini + k]
            if par == "=":
                continue
            t_es, t_en = par
            for lingua, t, dest in (("es", t_es, es), ("en", t_en, en)):
                if t == "=":
                    continue
                if pt in modelos and sorted(re.findall(r"\{\d+\}", pt)) != sorted(re.findall(r"\{\d+\}", t)):
                    erros.append(f"#{ini + k} {lingua}: variáveis diferentes: {pt!r} -> {t!r}")
                    continue
                dest[pt] = _ajusta(pt, t)
    # Frases novas (depois da lista base): i18n_trad/extra.json = {"português": ["espanhol", "inglês"]}
    extra = os.path.join(AQUI, "i18n_trad", "extra.json")
    if os.path.exists(extra):
        for pt, (t_es, t_en) in json.load(open(extra, encoding="utf-8")).items():
            if sorted(re.findall(r"\{\d+\}", pt)) != sorted(re.findall(r"\{\d+\}", t_es)) or                sorted(re.findall(r"\{\d+\}", pt)) != sorted(re.findall(r"\{\d+\}", t_en)):
                erros.append(f"extra: variáveis diferentes em {pt!r}")
                continue
            es[pt], en[pt] = _ajusta(pt, t_es), _ajusta(pt, t_en)
    return es, en, erros, len(itens)


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    es, en, erros, total = montar()
    for e in erros:
        print("ERRO", e)
    with open(os.path.join(AQUI, "traducoes_data.py"), "w", encoding="utf-8") as f:
        f.write("# Gerado por i18n_montar.py. Não edite à mão: edite i18n_trad/*.json e rode o script.\n")
        f.write("ES = " + json.dumps(es, ensure_ascii=False, indent=0) + "\n")
        f.write("EN = " + json.dumps(en, ensure_ascii=False, indent=0) + "\n")
    print(f"catálogo: {total} | traduzidos ES: {len(es)} | EN: {len(en)} | erros: {len(erros)}")
