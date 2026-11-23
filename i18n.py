"""Tradução do app na hora em que o texto aparece (PT / ES / EN).

Os textos continuam em português no código. install() faz os widgets (CTkLabel, CTkButton...),
títulos de janela e caixas de mensagem passarem por tr(), que troca pelo texto traduzido
de traducoes_data.py (gerado por i18n_montar.py). Frases com números/nomes no meio, como
f"Otimizando {jogo}...", são achadas pelos "modelos" com {0}, {1}.
"""
import os
import re

try:
    import traducoes_data as _dados
except Exception:          # sem o arquivo de traduções o app continua em português
    _dados = None

IDIOMAS = ("pt", "es", "en")
_lang = "pt"
_exato = {}
_modelos = []              # (regex, modelo traduzido)
_cache = {}

_CFG = os.path.join(os.environ.get("LOCALAPPDATA") or os.path.expanduser("~"), "Bernal Otimizacoes", "idioma.txt")


def idioma_salvo():
    try:
        with open(_CFG, encoding="utf-8") as f:
            v = f.read().strip().lower()
        return v if v in IDIOMAS else "pt"
    except Exception:
        return "pt"


def salvar_idioma(lang):
    try:
        os.makedirs(os.path.dirname(_CFG), exist_ok=True)
        with open(_CFG, "w", encoding="utf-8") as f:
            f.write(lang)
    except Exception:
        pass


def lang():
    return _lang


def set_lang(novo):
    global _lang, _exato, _modelos, _cache
    _lang = novo if novo in IDIOMAS else "pt"
    _cache = {}
    if _lang == "pt" or _dados is None:
        _exato, _modelos = {}, []
        return
    tabela = _dados.ES if _lang == "es" else _dados.EN
    _exato, _modelos = {}, []
    for pt, tr_ in tabela.items():
        if re.search(r"\{\d+\}", pt):
            partes = re.split(r"(\{\d+\})", pt.replace("{{", "\x01").replace("}}", "\x02"))
            if not "".join(p for p in partes if not re.fullmatch(r"\{\d+\}", p)).strip():
                continue
            rx = "".join("(.*?)" if re.fullmatch(r"\{\d+\}", p)
                         else re.escape(p.replace("\x01", "{").replace("\x02", "}")) for p in partes)
            ordem = [int(n) for n in re.findall(r"\{(\d+)\}", pt)]
            _modelos.append((len(pt), re.compile(rx, re.S), ordem, tr_))
        else:
            _exato[pt] = tr_
    _modelos.sort(key=lambda m: -m[0])     # modelos mais longos (mais específicos) primeiro


def tr(s):
    """Texto traduzido para o idioma atual (ou o próprio texto se não houver tradução)."""
    if _lang == "pt" or not isinstance(s, str) or not s.strip():
        return s
    r = _exato.get(s)
    if r is not None:
        return r
    if s in _cache:
        return _cache[s]
    res = _traduz(s)
    if len(_cache) < 5000:
        _cache[s] = res
    return res


def _traduz(s):
    nucleo = s.strip()
    if nucleo != s:
        # Recuo/espaços nas pontas (comum no log): traduz o miolo e devolve os espaços
        t = _exato.get(nucleo)
        if t is None:
            t = _modelo(nucleo)
        if t is not None:
            return s.replace(nucleo, t.strip(), 1)
    t = _modelo(s)
    if t is not None:
        return t
    if "\n" in s:
        partes = s.split("\n")
        trad = [tr(p) for p in partes]
        if trad != partes:
            return "\n".join(trad)
    return s


def _modelo(s):
    """Tradução pelos modelos com {0}, {1}... ou None."""
    for _, rx, ordem, modelo in _modelos:
        m = rx.fullmatch(s)
        if m:
            valores = {n: tr(v) for n, v in zip(ordem, m.groups())}
            try:
                return modelo.replace("{{", "\x01").replace("}}", "\x02").format(
                    *[valores.get(i, "") for i in range(max(ordem) + 1)]).replace("\x01", "{").replace("\x02", "}")
            except Exception:
                return None
    return None


def install(ctk, messagebox):
    """Faz os widgets e caixas de mensagem passarem pela tradução."""
    def _envolve(cls, chaves=("text",)):
        init0, conf0 = cls.__init__, cls.configure

        def __init__(self, *a, **kw):
            for k in chaves:
                if k in kw:
                    kw[k] = tr(kw[k])
            init0(self, *a, **kw)

        def configure(self, *a, **kw):
            for k in chaves:
                if k in kw:
                    kw[k] = tr(kw[k])
            return conf0(self, *a, **kw)
        cls.__init__, cls.configure = __init__, configure
        try:
            cls.config = configure
        except Exception:
            pass

    for nome in ("CTkLabel", "CTkButton", "CTkCheckBox", "CTkRadioButton", "CTkSwitch"):
        c = getattr(ctk, nome, None)
        if c is not None:
            _envolve(c)
    if getattr(ctk, "CTkEntry", None) is not None:
        _envolve(ctk.CTkEntry, ("placeholder_text",))
    if getattr(ctk, "CTkInputDialog", None) is not None:
        _envolve(ctk.CTkInputDialog, ("text", "title"))

    for nome in ("CTk", "CTkToplevel"):
        c = getattr(ctk, nome, None)
        if c is None:
            continue
        t0 = c.title

        def title(self, *a, _t0=t0):
            if a:
                return _t0(self, tr(a[0]), *a[1:])
            return _t0(self)
        c.title = title

    for nome in ("showinfo", "showwarning", "showerror", "askyesno", "askokcancel", "askyesnocancel", "askquestion", "askretrycancel"):
        f0 = getattr(messagebox, nome, None)
        if f0 is None:
            continue

        def wrap(title=None, message=None, *a, _f0=f0, **kw):
            return _f0(tr(title), tr(message), *a, **kw)
        setattr(messagebox, nome, wrap)
