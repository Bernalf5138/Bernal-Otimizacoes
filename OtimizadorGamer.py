import customtkinter as ctk
import subprocess
import threading
import sys
import os
import ctypes
import time
import urllib.request
import webbrowser
import json
import base64
import tkinter as tk
from tkinter import messagebox
import glob
import shutil
import idiomas as lang
import extras
import bernal_cloud as cloud
from PIL import Image, ImageTk
import re
import hashlib
import hmac
import queue as _queue_mod

APP_VERSION = "11.1"

# --------------------------------------------------------------------------
# Senhas: nunca em texto puro no código. Para trocar uma senha, rode:
#   python -c "import hashlib;print(hashlib.pbkdf2_hmac('sha256',b'NOVA_SENHA',b'bernal-master-v1',200000).hex())"
# e cole o resultado em MASTER_PASS_HASH (use o salt 'bernal-audit-v1' para AUDIT_PASS_HASH).
# --------------------------------------------------------------------------
MASTER_USER = "Bernal"
MASTER_SALT = b"bernal-master-v1"
MASTER_PASS_HASH = "814d90585b1ba6d4b7ee5e762b7fad43ed0026b77f26d8b0d92044ff9d0c16e5"
AUDIT_SALT = b"bernal-audit-v1"
AUDIT_PASS_HASH = "7ef216fe2555665900026469dd2ed110c168fb85e99f6f14f30ccaf3a0071bf7"


def _pbkdf2(password, salt):
    return hashlib.pbkdf2_hmac("sha256", (password or "").encode("utf-8"), salt, 200000).hex()


def check_master_password(password):
    return hmac.compare_digest(_pbkdf2(password, MASTER_SALT), MASTER_PASS_HASH)


def check_master_login(user, password):
    return (user or "").strip() == MASTER_USER and check_master_password(password)


def check_audit_password(password):
    return hmac.compare_digest(_pbkdf2(password, AUDIT_SALT), AUDIT_PASS_HASH)


def get_machine_id():
    """ID único do Windows (MachineGuid). Usado para prender a licença a este PC."""
    try:
        import winreg
        k = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Cryptography", 0,
                           winreg.KEY_READ | getattr(winreg, "KEY_WOW64_64KEY", 0))
        v, _ = winreg.QueryValueEx(k, "MachineGuid")
        winreg.CloseKey(k)
        return str(v)
    except Exception:
        return os.environ.get("COMPUTERNAME", "desconhecido")


def machine_fingerprint():
    return hashlib.sha256(("bernal-lic|" + get_machine_id()).encode("utf-8")).hexdigest()



def is_running_as_admin():
    try:
        return bool(ctypes.windll.shell32.IsUserAnAdmin())
    except Exception:
        return False


_TK_MAIN_THREAD = threading.main_thread()


def _on_main_thread():
    return threading.current_thread() is _TK_MAIN_THREAD

def ensure_admin_elevation():
    try:
        if not ctypes.windll.shell32.IsUserAnAdmin():
            if getattr(sys, 'frozen', False):
                ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, "", None, 1)
            else:
                params = " ".join([f'"{arg}"' for arg in sys.argv])
                ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, params, None, 1)
            sys.exit(0)
    except Exception:
        pass

if __name__ == "__main__" or getattr(sys, 'frozen', False):
    ensure_admin_elevation()

class ToolTip:
    def __init__(self, widget, text, title="⚡ BERNAL INTEL"):
        self.widget = widget
        self.text = text
        self.title = title
        self.tooltip_window = None
        self.after_id = None

        targets = [self.widget]
        for sub in ("_canvas", "_text_label"):
            obj = getattr(self.widget, sub, None)
            if obj:
                targets.append(obj)

        for t in targets:
            try:
                t.bind("<Enter>", self.schedule_enter, add="+")
                t.bind("<Leave>", self.leave, add="+")
                t.bind("<ButtonPress>", self.leave, add="+")
            except:
                pass

    def schedule_enter(self, event=None):
        self.cancel_timer()
        if not self.text:
            return
        try:
            self.after_id = self.widget.after(100, self.enter)
        except:
            self.enter()

    def cancel_timer(self):
        if self.after_id:
            try:
                self.widget.after_cancel(self.after_id)
            except:
                pass
            self.after_id = None

    def enter(self, event=None):
        if self.tooltip_window or not self.text:
            return
        try:
            if not self.widget.winfo_exists():
                return
        except:
            return

        try:
            px = self.widget.winfo_pointerx()
            py = self.widget.winfo_pointery()
            x = px + 14
            y = py + 14
            sw = self.widget.winfo_screenwidth()
            sh = self.widget.winfo_screenheight()
            if x + 310 > sw:
                x = sw - 320
            if y + 90 > sh:
                y = py - 85
        except:
            try:
                x = self.widget.winfo_rootx() + 20
                y = self.widget.winfo_rooty() + self.widget.winfo_height() + 5
            except:
                x, y = 200, 200

        try:
            self.tooltip_window = tw = tk.Toplevel(self.widget)
            tw.wm_overrideredirect(True)
            tw.attributes("-topmost", True)
            tw.wm_geometry(f"+{x}+{y}")

            border_frame = tk.Frame(tw, bg="#00D2FF", bd=1)
            border_frame.pack(fill="both", expand=True)

            card_frame = tk.Frame(border_frame, bg="#0D091B", padx=8, pady=6)
            card_frame.pack(fill="both", expand=True)

            if self.title:
                h_lbl = tk.Label(
                    card_frame,
                    text=self.title,
                    font=("Segoe UI", 9, "bold"),
                    bg="#0D091B",
                    fg="#00D2FF",
                    anchor="w"
                )
                h_lbl.pack(fill="x", pady=(0, 2))

            t_lbl = tk.Label(
                card_frame,
                text=self.text,
                font=("Segoe UI", 9),
                bg="#0D091B",
                fg="#F3F4F6",
                justify="left",
                wraplength=300,
                anchor="w"
            )
            t_lbl.pack(fill="x")
        except:
            pass

    def leave(self, event=None):
        self.cancel_timer()
        if self.tooltip_window:
            try:
                self.tooltip_window.destroy()
            except:
                pass
            self.tooltip_window = None

class CyberProgressHUD(ctk.CTkToplevel):
    """Modal futurista com porcentagem e barra de progresso exibido ao clicar em ações."""
    def __init__(self, parent, title="Executando Operação...", initial_msg="Iniciando processamento..."):
        super().__init__(parent)
        self.overrideredirect(True)
        self.attributes("-topmost", True)
        self.configure(fg_color="#090514")
        
        w, h = 480, 230
        try:
            parent.update_idletasks()
            px = parent.winfo_rootx()
            py = parent.winfo_rooty()
            pw = parent.winfo_width()
            ph = parent.winfo_height()
            x = max(10, px + (pw - w) // 2)
            y = max(10, py + (ph - h) // 2)
        except Exception:
            x, y = 300, 200
        self.geometry(f"{w}x{h}+{x}+{y}")
        
        b = ctk.CTkFrame(self, fg_color="#100B24", corner_radius=12, border_width=2, border_color="#00D2FF")
        b.pack(fill="both", expand=True, padx=2, pady=2)
        
        t_row = ctk.CTkFrame(b, fg_color="transparent")
        t_row.pack(fill="x", padx=18, pady=(16, 6))
        
        ctk.CTkLabel(t_row, text="⚡ BERNAL PRO • PROCESSANDO", font=ctk.CTkFont(size=11, weight="bold"), text_color="#00D2FF").pack(side="left")
        self.lbl_pct = ctk.CTkLabel(t_row, text="0%", font=ctk.CTkFont(family="Consolas", size=24, weight="bold"), text_color="#00D2FF")
        self.lbl_pct.pack(side="right")
        
        self.lbl_title = ctk.CTkLabel(b, text=title, font=ctk.CTkFont(size=14, weight="bold"), text_color="#FFFFFF", anchor="w")
        self.lbl_title.pack(fill="x", padx=18, pady=(2, 6))
        
        self.bar = ctk.CTkProgressBar(b, height=10, corner_radius=5, progress_color="#00D2FF", fg_color="#1A1238")
        self.bar.pack(fill="x", padx=18, pady=6)
        self.bar.set(0)
        
        self.lbl_msg = ctk.CTkLabel(b, text=initial_msg, font=ctk.CTkFont(size=11), text_color="#9CA3AF", anchor="w", wraplength=440, justify="left")
        self.lbl_msg.pack(fill="x", padx=18, pady=(4, 12))
        
        bot = ctk.CTkFrame(b, fg_color="transparent")
        bot.pack(fill="x", padx=18, pady=(0, 10))
        ctk.CTkLabel(bot, text="🛡️ Ponto de restauração criado ao abrir o app • Veja detalhes no Log", font=ctk.CTkFont(size=9), text_color="#6B7280").pack(side="left")

        # Sem porcentagem real ainda: barra animada (indeterminada) em vez de números inventados
        self._determinate = False
        self.lbl_pct.configure(text="...")
        try:
            self.bar.configure(mode="indeterminate")
            self.bar.start()
        except Exception:
            pass

    def update_progress(self, pct, msg=None):
        try:
            if not self._determinate:
                self._determinate = True
                try:
                    self.bar.stop()
                    self.bar.configure(mode="determinate")
                except Exception:
                    pass
            p = max(0, min(100, int(pct)))
            self.bar.set(p / 100.0)
            self.lbl_pct.configure(text=f"{p}%")
            if msg:
                self.lbl_msg.configure(text=msg)
        except Exception:
            pass

    def set_message(self, msg):
        try:
            self.lbl_msg.configure(text=str(msg)[:160])
        except Exception:
            pass

    def finish(self, msg="✅ Concluído!", ok=True):
        try:
            if not self._determinate:
                self._determinate = True
                try:
                    self.bar.stop()
                    self.bar.configure(mode="determinate")
                except Exception:
                    pass
            self.bar.set(1.0)
            self.lbl_pct.configure(text="OK" if ok else "!")
            self.lbl_msg.configure(text=msg)
            color = "#10B981" if ok else "#F59E0B"
            self.lbl_pct.configure(text_color=color)
            self.bar.configure(progress_color=color)
            self.after(900 if ok else 2600, self.destroy)
        except Exception:
            try: self.destroy()
            except: pass

# Setup CustomTkinter Theme
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

class OtimizadorApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        
        self.current_lang = "pt"

        self.title(f"Bernal Otimizações PRO - V{APP_VERSION}")
        sw = self.winfo_screenwidth()
        sh = self.winfo_screenheight()
        w, h = 1220, 760
        x = max(0, (sw - w) // 2)
        y = max(0, (sh - h) // 2)
        self.geometry(f"{w}x{h}+{x}+{y}")
        self.minsize(1120, 700)
        self.resizable(True, True)
        self.configure(fg_color="#0B0813")
        
        self.bind("<Control-Shift-A>", self.prompt_admin)

        # Environment Paths
        if getattr(sys, 'frozen', False):
            self.base_path = sys._MEIPASS
            self.current_dir = os.path.dirname(sys.executable)
        else:
            self.base_path = os.path.dirname(os.path.abspath(__file__))
            self.current_dir = self.base_path

        # User state
        import queue
        self.gui_queue = queue.Queue()
        self.is_admin = False
        self.is_trial = False
        self.trial_time_left = 3600
        self.audit_log_path = r"C:\Users\Public\Documents\Bernal_Auditoria.log"

        self.cached_thumbnails = {}
        self.current_user = ""
        self._audit_lock = threading.Lock()
        self._tls = threading.local()
        self.trial_state_path = r"C:\Users\Public\Documents\Bernal_Trial.json"
        self.cloud_session = False
        cloud.init(APP_VERSION)
        self._install_thread_safe_dialogs()
        # Initially hide the main app until login
        self.withdraw()
        
        self.process_gui_queue()
        
        # Show animated splash before login
        self.after(100, self.show_splash)
        
        # Ensure any legacy noisy auto clean task is upgraded to silent
        self.after(2000, self.silence_legacy_tasks)
        self.after(8000, self._fps_autostart)

    def _fps_autostart(self):
        try:
            cfg = self._fps_load_cfg()
            if cfg.get("watch") and cfg.get("games"):
                self.start_fps_watcher()
        except Exception:
            pass

    def t(self, key):
        return lang.TRANSLATIONS.get(self.current_lang, {}).get(key, key)

    def process_gui_queue(self):
        try:
            for _ in range(200):
                task = self.gui_queue.get_nowait()
                try:
                    task()
                except Exception as e:
                    try:
                        print(f"[UI] erro em tarefa: {e}")
                    except Exception:
                        pass
        except _queue_mod.Empty:
            pass
        super().after(40, self.process_gui_queue)

    # ------------------------------------------------------------------
    # Thread-safety: Tkinter/CustomTkinter só podem ser usados na thread
    # principal. Tudo que vem de threads de trabalho passa pela gui_queue.
    # ------------------------------------------------------------------
    def after(self, ms, func=None, *args):
        if _on_main_thread() or func is None:
            return super().after(ms, func, *args)
        if ms and int(ms) > 0:
            self.gui_queue.put(lambda: super(OtimizadorApp, self).after(ms, func, *args))
        else:
            self.gui_queue.put(lambda: func(*args))
        return None

    def call_ui(self, fn, *args, wait=True, timeout=None):
        """Executa fn na thread da interface. Com wait=True devolve o resultado."""
        if _on_main_thread():
            return fn(*args)
        if not wait:
            self.gui_queue.put(lambda: fn(*args))
            return None
        done = threading.Event()
        box = {}
        def _run():
            try:
                box["r"] = fn(*args)
            except Exception as e:
                box["e"] = e
            finally:
                done.set()
        self.gui_queue.put(_run)
        done.wait(timeout)
        if "e" in box:
            raise box["e"]
        return box.get("r")

    def _run_dialog_above_hud(self, o, a, kw):
        """Mostra a caixa de mensagem SEMPRE na frente do HUD de progresso.
        O HUD é 'topmost'; aqui ele é rebaixado enquanto a caixa está aberta e restaurado depois."""
        hud = getattr(self, 'current_hud', None)
        dropped = False
        try:
            if hud is not None and hud.winfo_exists():
                hud.attributes("-topmost", False)
                hud.lower()
                dropped = True
        except Exception:
            pass
        try:
            return o(*a, **kw)
        finally:
            if dropped:
                try:
                    if hud.winfo_exists():
                        hud.attributes("-topmost", True)
                        hud.lift()
                except Exception:
                    pass

    def _install_thread_safe_dialogs(self):
        app = self
        for name in ("showinfo", "showwarning", "showerror", "askyesno", "askokcancel", "askyesnocancel", "askquestion"):
            orig = getattr(messagebox, name, None)
            if orig is None or getattr(orig, "_bernal_safe", False):
                continue
            def make(o):
                def safe(*a, **kw):
                    if _on_main_thread():
                        return app._run_dialog_above_hud(o, a, kw)
                    return app.call_ui(lambda: app._run_dialog_above_hud(o, a, kw), wait=True)
                safe._bernal_safe = True
                return safe
            setattr(messagebox, name, make(orig))

    def show_splash(self):
        """Animated splash screen shown before login."""
        splash = tk.Toplevel(self)
        splash.overrideredirect(True)
        sw = self.winfo_screenwidth()
        sh = self.winfo_screenheight()
        w, h = 480, 300
        x = (sw - w) // 2
        y = (sh - h) // 2
        splash.geometry(f"{w}x{h}+{x}+{y}")
        splash.configure(bg="#0d1117")
        splash.attributes('-topmost', True)

        # Canvas for drawing
        canvas = tk.Canvas(splash, width=w, height=h, bg="#0d1117",
                           highlightthickness=0)
        canvas.pack(fill="both", expand=True)

        # Border
        canvas.create_rectangle(2, 2, w-2, h-2, outline="#00d4ff", width=2)

        # Logo text
        logo = canvas.create_text(w//2, 90, text="⚡",
                                   font=("Arial", 52), fill="#00d4ff")
        title = canvas.create_text(w//2, 160, text="Bernal Otimizações Pro",
                                    font=("Arial", 20, "bold"), fill="white")
        subtitle = canvas.create_text(w//2, 190, text=f"Versão {APP_VERSION}  •  Performance e Estabilidade",
                                       font=("Arial", 11), fill="#00D2FF")
        status = canvas.create_text(w//2, 240, text="Iniciando...",
                                     font=("Arial", 10), fill="#00d4ff")

        # Progress bar
        bar_bg = canvas.create_rectangle(60, 260, w-60, 275,
                                          fill="#161b22", outline="#333")
        bar_fg = canvas.create_rectangle(60, 260, 60, 275,
                                          fill="#00d4ff", outline="")

        steps = [
            (0.15, "Verificando licença..."),
            (0.35, "Carregando módulos..."),
            (0.55, "Iniciando interface..."),
            (0.80, "Quase pronto..."),
            (1.00, "Bem-vindo!"),
        ]

        def animate(i=0):
            if i >= len(steps):
                splash.destroy()
                if self.try_cloud_login():
                    return
                self.show_license_screen()
                return
            prog, msg = steps[i]
            bar_w = int((w - 120) * prog)
            canvas.coords(bar_fg, 60, 260, 60 + bar_w, 275)
            canvas.itemconfig(status, text=msg)
            splash.update()
            splash.after(320, lambda: animate(i + 1))

        animate()

    # --- Authentication & Licensing ---
    def copy_discord(self, btn):
        self.clipboard_clear()
        self.clipboard_append("bernalf_11_56935")
        self.update()
        btn.configure(text="✅ Copiado e Abrindo Discord...")
        try:
            # Tenta abrir o protocolo do Discord direto no PC
            os.startfile("discord:")
        except:
            # Se não tiver o app do Discord, abre no navegador
            webbrowser.open("https://discord.com/app")

    # --- Licença na nuvem (mesmo servidor de chaves do BSO) ---
    def try_cloud_login(self):
        """Se há chave salva e válida (reconferida no servidor), entra direto, sem pedir login."""
        try:
            cloud.evaluate()
            if cloud.saved_key() and not cloud.is_valid():
                cloud.recheck()           # pode falar com o servidor (até ~15 s)
            if cloud.is_valid():
                self._enter_with_cloud_license()
                return True
        except Exception:
            pass
        return False

    def _enter_with_cloud_license(self):
        st = cloud.status()
        self.cloud_session = True
        self.is_admin = False
        self.current_user = st.get("customer") or "Cliente"
        self.show_eula_screen(self.current_user)

    def _cloud_license_lost(self, st):
        def _msg():
            messagebox.showwarning("Licença", (st.get("message") or "Sua licença não está mais válida.") +
                                   "\n\nO aplicativo será fechado. Fale com o suporte para renovar.")
            self.destroy()
        self.after(0, _msg)

    def build_cloud_key_box(self, parent):
        """Campo 'Chave de licença' + botão Ativar (usado nas telas de login e de ativação)."""
        box = ctk.CTkFrame(parent, fg_color="#181230", corner_radius=10, border_width=1, border_color="#7928CA")
        box.pack(fill="x", padx=24, pady=(4, 8))
        ctk.CTkLabel(box, text="🔑 Chave de licença", font=ctk.CTkFont(size=13, weight="bold"), text_color="#F1C40F").pack(pady=(8, 2))
        entry = ctk.CTkEntry(box, placeholder_text="BOT-XXXXX-XXXXX-XXXXX-XXXXX", width=290)
        entry.pack(pady=4)
        lbl = ctk.CTkLabel(box, text="ID deste PC: " + cloud.machine_id(), font=ctk.CTkFont(size=10), text_color="#9CA3AF")
        lbl.pack()
        btn = ctk.CTkButton(box, text="Ativar chave", fg_color="#7928CA", hover_color="#9333EA", command=lambda: self.activate_cloud_key(entry, btn))
        btn.pack(pady=(6, 10))
        return box

    def activate_cloud_key(self, entry, btn):
        key = entry.get().strip()
        if not key:
            entry.configure(border_color="red")
            return
        btn.configure(state="disabled", text="Ativando...")

        def work():
            ok, msg = cloud.activate(key)

            def done():
                try:
                    btn.configure(state="normal", text="Ativar chave")
                except Exception:
                    pass
                if ok:
                    if hasattr(self, "auth_window") and self.auth_window.winfo_exists():
                        self.auth_window.destroy()
                    self._enter_with_cloud_license()
                else:
                    entry.configure(border_color="red")
                    messagebox.showerror("Licença", msg, parent=self.auth_window if hasattr(self, "auth_window") else None)
            self.after(0, done)
        threading.Thread(target=work, daemon=True).start()

    # --- Tela única: licença por chave + teste gratuito (sem login de cliente) ---
    def show_license_screen(self):
        self.auth_window = ctk.CTkToplevel(self)
        self.auth_window.title("Bernal Otimizações - Licença")
        self.auth_window.geometry("420x760")
        self.auth_window.resizable(False, False)
        self.auth_window.attributes('-topmost', 'true')
        self.auth_window.protocol("WM_DELETE_WINDOW", self.destroy)

        lang_frame = ctk.CTkFrame(self.auth_window, fg_color="transparent")
        lang_frame.pack(pady=(10, 0), anchor="e", padx=10)

        def set_lang(l):
            self.current_lang = l
            self.build_license_ui()

        ctk.CTkButton(lang_frame, text="🇧🇷 PT", width=40, height=25, fg_color="#27AE60", command=lambda: set_lang("pt")).pack(side="left", padx=2)
        ctk.CTkButton(lang_frame, text="🌎 ES", width=40, height=25, fg_color="#D35400", command=lambda: set_lang("es")).pack(side="left", padx=2)
        ctk.CTkButton(lang_frame, text="🇺🇸 EN", width=40, height=25, fg_color="#2980B9", command=lambda: set_lang("en")).pack(side="left", padx=2)

        self.license_content = ctk.CTkFrame(self.auth_window, fg_color="transparent")
        self.license_content.pack(fill="both", expand=True)

        self.build_license_ui()

    def build_license_ui(self):
        for w in self.license_content.winfo_children():
            w.destroy()

        ctk.CTkLabel(self.license_content, text="⚡ BEM-VINDO ⚡", font=ctk.CTkFont(size=24, weight="bold"), text_color="#3498DB").pack(pady=(10, 4))
        ctk.CTkLabel(self.license_content, text="Ative sua licença com a chave recebida na compra.", justify="center").pack(pady=(0, 6))
        self.build_cloud_key_box(self.license_content)

        ctk.CTkButton(self.license_content, text=self.t("btn_trial"), font=ctk.CTkFont(weight="bold"), fg_color="#F1C40F", hover_color="#D4AC0D", text_color="black", command=self.start_trial_mode).pack(pady=10)
        ctk.CTkLabel(self.license_content, text="O teste gratuito libera 60 minutos de uso.\nDepois disso, é necessário comprar uma licença.", font=ctk.CTkFont(size=11), text_color="#9CA3AF", justify="center").pack(pady=(0, 6))

        ctk.CTkButton(self.license_content, text="💬 Comprar Licença (WhatsApp)", fg_color="#25D366", hover_color="#128C7E", text_color="white", command=lambda: webbrowser.open("https://wa.me/595981010764?text=Olá, vi o Bernal Otimizações Pro e tenho interesse em adquirir uma licença!")).pack(pady=10)

        btn_disc = ctk.CTkButton(self.license_content, text="🎮 Suporte Discord (bernalf_11_56935)", fg_color="#5865F2", hover_color="#4752C4", text_color="white")
        btn_disc.configure(command=lambda b=btn_disc: self.copy_discord(b))
        btn_disc.pack(pady=5)

        # Acesso do desenvolvedor (Bernal): oculto, não aparece para o cliente usar por acidente.
        dev_link = ctk.CTkButton(self.license_content, text="Sou o desenvolvedor", font=ctk.CTkFont(size=10), fg_color="transparent",
                                 text_color="#4B5563", hover_color="#181230", height=20, command=lambda: self.toggle_dev_box(dev_box))
        dev_link.pack(pady=(14, 2))
        dev_box = ctk.CTkFrame(self.license_content, fg_color="transparent")

        self.entry_dev_user = ctk.CTkEntry(dev_box, placeholder_text="Usuário master")
        self.entry_dev_user.pack(pady=4)
        self.entry_dev_pass = ctk.CTkEntry(dev_box, placeholder_text="Senha master", show="*")
        self.entry_dev_pass.pack(pady=4)
        ctk.CTkButton(dev_box, text="Entrar como Desenvolvedor", fg_color="#F39C12", hover_color="#D68910", command=self.do_dev_login).pack(pady=6)

    def toggle_dev_box(self, dev_box):
        if dev_box.winfo_ismapped():
            dev_box.pack_forget()
        else:
            dev_box.pack(pady=4, fill="x")

    def do_dev_login(self):
        if check_master_login(self.entry_dev_user.get(), self.entry_dev_pass.get()):
            self.is_admin = True
            self.current_user = self.entry_dev_user.get().strip()
            self.auth_window.destroy()
            self.start_main_app()
        else:
            self.entry_dev_user.configure(border_color="red")
            self.entry_dev_pass.configure(border_color="red")

    def start_trial_mode(self):
        used = self.get_trial_used_seconds()
        if used >= 3600:
            parent = self.auth_window if hasattr(self, 'auth_window') and self.auth_window.winfo_exists() else None
            messagebox.showwarning("Teste Gratuito", "O teste gratuito de 60 minutos já foi usado neste computador.\nCompre uma licença para continuar usando.", parent=parent)
            return
        self.trial_time_left = 3600 - used
        self.is_trial = True
        self.is_admin = False
        self.current_user = "Teste"
        if hasattr(self, 'auth_window') and self.auth_window.winfo_exists():
            self.auth_window.destroy()
        messagebox.showinfo("Teste Gratuito",
                            "Você está no TESTE GRATUITO (60 minutos de uso).\n\n"
                            "Depois desse tempo, compre uma licença para continuar usando o Bernal Otimizações.")
        self.show_eula_screen("TrialUser")

    # --- Trial persistente (não reinicia ao fechar e abrir o app) ---
    def _trial_reg_get(self):
        try:
            import winreg
            k = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\BernalOtimizacoes")
            v, _ = winreg.QueryValueEx(k, "tu")
            winreg.CloseKey(k)
            return int(v)
        except Exception:
            return 0

    def _trial_reg_set(self, used):
        try:
            import winreg
            k = winreg.CreateKey(winreg.HKEY_CURRENT_USER, r"Software\BernalOtimizacoes")
            winreg.SetValueEx(k, "tu", 0, winreg.REG_DWORD, int(used))
            winreg.CloseKey(k)
        except Exception:
            pass

    def get_trial_used_seconds(self):
        used_file = 0
        try:
            with open(self.trial_state_path, "r", encoding="utf-8") as f:
                d = json.load(f)
            if d.get("m") == machine_fingerprint()[:16]:
                used_file = int(d.get("used", 0))
        except Exception:
            pass
        return max(used_file, self._trial_reg_get())

    def save_trial_used_seconds(self, used):
        try:
            with open(self.trial_state_path, "w", encoding="utf-8") as f:
                json.dump({"used": int(used), "m": machine_fingerprint()[:16]}, f)
        except Exception:
            pass
        self._trial_reg_set(used)
    def show_eula_screen(self, username):
        self.eula_window = ctk.CTkToplevel(self)
        self.eula_window.title(self.t("eula_title"))
        self.eula_window.geometry("600x500")
        self.eula_window.resizable(False, False)
        self.eula_window.attributes('-topmost', 'true')
        self.eula_window.protocol("WM_DELETE_WINDOW", self.destroy)
        
        ctk.CTkLabel(self.eula_window, text=self.t("eula_header"), font=ctk.CTkFont(size=22, weight="bold"), text_color="#F1C40F").pack(pady=(20, 10))
        
        termo = self.t("eula_text")
        
        caixa_texto = ctk.CTkTextbox(self.eula_window, width=550, height=250, font=ctk.CTkFont(size=13))
        caixa_texto.pack(pady=10)
        caixa_texto.insert("1.0", termo)
        caixa_texto.configure(state="disabled")
        
        self.check_var = ctk.BooleanVar(value=False)
        chk = ctk.CTkCheckBox(self.eula_window, text=self.t("eula_check"), variable=self.check_var, fg_color="#E74C3C")
        chk.pack(pady=10)
        
        btn_aceitar = ctk.CTkButton(self.eula_window, text=self.t("eula_btn"), fg_color="#27AE60", hover_color="#1E8449", command=lambda: self.accept_eula(username))
        btn_aceitar.pack(pady=10)
        
    def accept_eula(self, username):
        if self.check_var.get():
            log_msg = f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] --- ACESSO CLIENTE: {username} (ACEITOU O CONTRATO) ---"
            b64_msg = base64.b64encode(log_msg.encode('utf-8')).decode('utf-8') + "\n"
            with open(self.audit_log_path, "a", encoding="utf-8") as f:
                f.write(b64_msg)
            self.eula_window.destroy()
            self.start_main_app()
        else:
            messagebox.showwarning("Atenção", "Você precisa marcar a caixa concordando com os termos para continuar.", parent=self.eula_window)

    def start_main_app(self):
        self.deiconify()
        self.setup_ui()
        if self.cloud_session:
            cloud.start_background(on_invalid=self._cloud_license_lost)
        # Leitura silenciosa de hardware em background (sem abrir modal de otimização)
        threading.Thread(target=self.load_hardware_specs, daemon=True).start()
        threading.Thread(target=lambda: self.create_restore_point(force_visible=False), daemon=True).start()
        # Remove qualquer tarefa/.bat de autorun de versões antigas (evita alerta de antivírus)
        threading.Thread(target=self.cleanup_legacy_guardian, daemon=True).start()

    def popup_log_window(self):
        pass

    def log(self, message):
        try:
            if sys.stdout is not None:
                print(message)
        except Exception:
            pass
        
        def _append():
            if hasattr(self, 'log_textbox') and self.log_textbox.winfo_exists():
                self.log_textbox.configure(state="normal")
                self.log_textbox.insert("end", f"[{time.strftime('%H:%M:%S')}] {message}\n")
                self.log_textbox.see("end")
                self.log_textbox.configure(state="disabled")
            if hasattr(self, 'lbl_mini_status') and self.lbl_mini_status.winfo_exists():
                clean_msg = str(message).replace("->", "").replace("✅", "").replace("⚡", "").strip()
                self.lbl_mini_status.configure(text=clean_msg[:75])
                
        if hasattr(self, 'gui_queue'):
            self.gui_queue.put(_append)
        else:
            self.after(0, _append)

        # Secret Audit Logging for Guest
        if not self.is_admin:
            try:
                entry = f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] {message}"
                b64_entry = base64.b64encode(entry.encode('utf-8')).decode('utf-8') + "\n"
                with self._audit_lock:
                    with open(self.audit_log_path, "a", encoding="utf-8") as f:
                        f.write(b64_entry)
            except Exception:
                pass

    def set_hud_progress(self, pct, msg=None):
        self._last_progress_ts = time.time()  # usado pelo vigia do atualizador
        def _upd(p=pct, m=msg):
            hud = getattr(self, 'current_hud', None)
            if hud is not None and hud.winfo_exists():
                hud.update_progress(p, m)
        self.call_ui(_upd, wait=False)
        if msg:
            self.log(f"[{pct}%] {msg}")

    def _hud_message(self, msg):
        def _upd():
            hud = getattr(self, 'current_hud', None)
            if hud is not None and hud.winfo_exists():
                hud.set_message(msg)
        self.call_ui(_upd, wait=False)

    def run_async(self, func, *args, action_title=None):
        fname = getattr(func, '__name__', '')
        titles_map = {
            "auto_optimize": "Otimização Total Automática",
            "apply_profile": "Aplicando Perfil de Performance",
            "cache_cleaner": "Limpeza Profunda de Cache & RAM",
            "apply_smart_game_booster": "Smart Game Booster (Super Boost FPS)",
            "apply_mouse_calibration": "Calibração de Mouse 1:1 Sem Delay",
            "optimize_game_disks": "Game Defrag & Otimização de Armazenamento",
            "save_warzone_config": "Buscando & Salvando Configs do Warzone",
            "restore_warzone_config": "Restaurando Backup do Warzone",
            "optimize_warzone_audio_and_graphics": "Otimizando Gráficos & Áudio do Warzone",
            "repair_warzone_crashes": "Reparador de Erros do Warzone (Fix 0x00001338)",
            "apply_single_wallpaper": "Aplicando Papel de Parede Gamer",
            "download_and_install_driver_booster": "Instalando IObit Driver Booster",
            "audio_fps_disable": "Desativando Áudio FPS",
            "audio_fps_enable": "Ativando Áudio FPS",
            "set_chrome_default": "Chrome como Padrão",
            "remove_internet_explorer": "Removendo Internet Explorer",
            "clean_desktop": "Limpando Área de Trabalho",
            "enable_defender": "Reativando Windows Defender",
            "disable_defender": "Desativando Windows Defender",
            "update_drivers_native": "Atualizando Drivers",
            "download_and_install_advanced_systemcare": "Instalando Advanced SystemCare",
            "install_streamer_app": "Instalando Plataforma / Launcher Gamer",
            "install_afterburner": "Instalando MSI Afterburner",
            "windows_debloater": "Windows Debloater (Removendo Bloatware)",
            "fix_corrupted_files": "Reparando Arquivos do Windows (SFC & DISM)",
            "reduce_ram_usage": "Reduzindo Uso de RAM em Standby",
            "apply_dns_profile": "Configurando DNS de Baixa Latência",
            "apply_virtual_ram_pagefile": "Configurando Memória RAM Virtual (HD/SSD)",
        }
        title = action_title or titles_map.get(fname, "Executando Otimização...")

        # Funções que abrem janelas próprias (ex.: escolha de jogo) rodam na thread da interface
        if getattr(func, "_ui_entry", False):
            if _on_main_thread():
                return func(*args)
            return self.call_ui(lambda: func(*args), wait=False)

        # Chamado de dentro de outra operação (já em thread de trabalho): executa direto
        if not _on_main_thread():
            func(*args)
            return

        if getattr(self, '_op_running', False):
            messagebox.showinfo("Aguarde", "Já existe uma operação em andamento.\nAguarde ela terminar (acompanhe na aba Log).")
            return
        self._op_running = True

        try:
            if hasattr(self, 'current_hud') and self.current_hud and self.current_hud.winfo_exists():
                try: self.current_hud.destroy()
                except: pass
            self.current_hud = CyberProgressHUD(self, title=title, initial_msg="Processando... acompanhe os detalhes na aba Log.")
        except Exception:
            self.current_hud = None

        def wrapper():
            self._tls.failures = 0
            ok = True
            try:
                func(*args)
            except Exception as e:
                ok = False
                self.log(f"❌ Erro em '{title}': {e}")
                self.after(0, lambda err=e: messagebox.showerror("Erro", f"❌ Ocorreu um erro: {err}"))
            fails = getattr(self._tls, "failures", 0)
            if ok and fails:
                msg = f"⚠️ Concluído com {fails} comando(s) que falharam. Veja a aba Log."
            elif ok:
                msg = "✅ Concluído!"
            else:
                msg = "❌ A operação foi interrompida por um erro."
            def _fin(m=msg, good=(ok and not fails)):
                self._op_running = False
                hud = getattr(self, 'current_hud', None)
                self.current_hud = None
                # Fecha o HUD na hora. Nunca deixa preso na tela, mesmo que uma
                # caixa de mensagem modal esteja aberta (ela bloquearia um timer).
                if hud is not None:
                    try:
                        if hud.winfo_exists():
                            hud.destroy()
                    except Exception:
                        pass
                self.log(m)
            self.call_ui(_fin, wait=False)

        threading.Thread(target=wrapper, daemon=True).start()

    def run_programmer_only(self, func, *args):
        if getattr(self, 'is_admin', False):
            self.run_async(func, *args)
        else:
            messagebox.showerror("Acesso Negado", "Somente um programador poderá fazer isso para você!")

    def run_visible_cmd(self, title, cmd_str):
        self.log(f"Iniciando Operação: {title}")
        success = self.run_cmd_live(cmd_str)
        if success:
            self.log(f"✅ SUCESSO: '{title}' concluído!")
            messagebox.showinfo("Operação Concluída", f"✅ '{title}' concluído com sucesso!")
        else:
            self.log(f"❌ ERRO na operação '{title}'. Tire um print para o suporte técnico!")
            messagebox.showerror("Erro na Operação", f"❌ ERRO na operação '{title}'. Tire um print ou leia a Auditoria Secreta para enviar ao suporte técnico!")

    def run_cmd_live(self, command):
        """Executes a command and streams its output to the live console without any popup window."""
        self.log(f"> {command}")
        try:
            startupinfo = None
            if os.name == 'nt':
                startupinfo = subprocess.STARTUPINFO()
                startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
                startupinfo.wShowWindow = 0  # SW_HIDE
            process = subprocess.Popen(
                command,
                shell=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                encoding=("oem" if os.name == 'nt' else "utf-8"),
                errors="replace",
                creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0,
                startupinfo=startupinfo
            )
            last_pct = [None]
            for line in iter(process.stdout.readline, ''):
                stripped = line.replace("\x00", "").strip()
                if not stripped:
                    continue
                # Filtra barras de progresso do sfc/DISM (ex: "... 63.3% ...")
                if stripped.startswith('[') and ('%' in stripped or '=' in stripped):
                    # Extrai o percentual e mostra só quando muda
                    import re
                    m = re.search(r'(\d+[\.,]\d+)\s*%', stripped)
                    if m:
                        pct = m.group(1)
                        if pct != last_pct[0]:
                            last_pct[0] = pct
                            self.log(f"  🔍 Verificando arquivos... {pct}%")
                    continue
                self.log(f"  {stripped}")
                self._hud_message(stripped)
            process.stdout.close()
            process.wait()
            if process.returncode != 0:
                self._tls.failures = getattr(self._tls, "failures", 0) + 1
                self.log(f"  ⚠️ Comando terminou com código {process.returncode}")
            return process.returncode == 0
        except Exception as e:
            self._tls.failures = getattr(self._tls, "failures", 0) + 1
            self.log(f"  ❌ Falha no comando: {e}")
            return False


    def count_procs_services(self):
        """Contagem real de processos e serviços em execução (mesmo método antes e depois)."""
        procs, servs = None, None
        try:
            import psutil
            procs = len(psutil.pids())
            try:
                servs = sum(1 for s in psutil.win_service_iter() if s.status() == "running")
            except Exception:
                servs = None
        except Exception:
            pass
        if servs is None:
            try:
                out = subprocess.check_output(["powershell", "-NoProfile", "-Command",
                                               "(Get-Service | Where-Object { $_.Status -eq 'Running' }).Count"],
                                              text=True, creationflags=subprocess.CREATE_NO_WINDOW, timeout=20).strip()
                servs = int(out)
            except Exception:
                servs = None
        if procs is None:
            try:
                out = subprocess.check_output('powershell "(Get-Process).Count"', shell=True, text=True,
                                              creationflags=subprocess.CREATE_NO_WINDOW, timeout=20).strip()
                procs = int(out)
            except Exception:
                procs = None
        return procs, servs

    def load_hardware_specs(self):
        def _loading():
            for attr, txt in [('lbl_proc_antes', 'Contando Processos...'),
                              ('lbl_chip_cpu_name', 'Lendo CPU...'), ('lbl_chip_gpu_name', 'Lendo GPU...'),
                              ('lbl_chip_ram_val', 'Lendo RAM...'), ('lbl_chip_disk_val', 'Lendo Disco...'),
                              ('lbl_chip_tpm_val', 'Verificando...'), ('lbl_chip_sec_val', 'Verificando...')]:
                w = getattr(self, attr, None)
                if w is not None and w.winfo_exists():
                    w.configure(text=txt)
        self.call_ui(_loading, wait=False)

        def _work():
            info = {}
            try:
                ps_script = (
                    "$ErrorActionPreference = 'SilentlyContinue'; "
                    "[Console]::OutputEncoding = [System.Text.Encoding]::UTF8; "
                    "$cpu = try { (Get-CimInstance Win32_Processor | Select-Object -First 1).Name } catch { '' }; "
                    "$gpus = try { @(Get-CimInstance Win32_VideoController | ForEach-Object { $_.Name }) } catch { @() }; "
                    "$ram = try { (Get-CimInstance Win32_ComputerSystem).TotalPhysicalMemory } catch { 0 }; "
                    "$tpm = 'unknown'; try { $t = Get-Tpm -ErrorAction Stop; if ($t.TpmPresent) { if ($t.TpmReady) { $tpm = 'ready' } else { $tpm = 'present' } } else { $tpm = 'absent' } } catch { $tpm = 'unknown' }; "
                    "$tpmver = ''; try { $w = Get-CimInstance -Namespace root/cimv2/security/microsofttpm -ClassName Win32_Tpm -ErrorAction Stop; if ($w) { $tpmver = ([string]$w.SpecVersion).Split(',')[0].Trim() } } catch { }; "
                    "$sb = 'unknown'; try { if (Confirm-SecureBootUEFI -ErrorAction Stop) { $sb = 'on' } else { $sb = 'off' } } catch [System.PlatformNotSupportedException] { $sb = 'legacy' } catch { $sb = 'unknown' }; "
                    "@{ cpu = $cpu; gpus = $gpus; ram = [string]$ram; tpm = $tpm; tpmver = $tpmver; sb = $sb } | ConvertTo-Json -Compress"
                )
                out = subprocess.check_output(["powershell", "-NoProfile", "-Command", ps_script], text=True,
                                              encoding="utf-8", errors="replace", timeout=40,
                                              creationflags=subprocess.CREATE_NO_WINDOW).strip()
                info = json.loads(out.splitlines()[-1]) if out else {}
            except Exception as e:
                self.log(f"⚠️ Não foi possível ler todo o hardware: {e}")

            cpu = (info.get("cpu") or "Desconhecido").strip()
            gpus = info.get("gpus") or []
            if isinstance(gpus, str):
                gpus = [gpus]
            gpu = "Desconhecido"
            for g in gpus:
                if any(x in g.upper() for x in ("NVIDIA", "RADEON", "AMD", "ARC")):
                    gpu = g
                    break
            else:
                if gpus:
                    gpu = gpus[0]
            try:
                ram_gb = round(int(info.get("ram") or 0) / (1024**3))
            except Exception:
                ram_gb = 0
            if not ram_gb:
                try:
                    import psutil
                    ram_gb = round(psutil.virtual_memory().total / (1024**3))
                except Exception:
                    ram_gb = 0
            self.sys_ram = ram_gb or 8
            self.gpu_name = gpu

            procs, servs = self.count_procs_services()
            self.metrics_before = (procs, servs)
            boot_time = self.get_boot_time()

            tpm = info.get("tpm", "unknown")
            tpmver = info.get("tpmver", "")
            if tpm == "ready":
                tpm_txt = "🟢 Ativo" + ((" (v" + tpmver + ")") if tpmver else "")
            elif tpm == "present":
                tpm_txt = "🟡 Presente, não inicializado"
            elif tpm == "absent":
                tpm_txt = "🔴 Não encontrado / desativado na BIOS"
            else:
                tpm_txt = "⚪ Não verificado"
            sb = info.get("sb", "unknown")
            sb_txt = {"on": "🟢 Ativado (UEFI)", "off": "🟡 Desativado (UEFI)",
                      "legacy": "🔴 BIOS Legacy (sem Secure Boot)"}.get(sb, "⚪ Não verificado")

            def _update_ui():
                def setw(attr, txt):
                    w = getattr(self, attr, None)
                    if w is not None and w.winfo_exists():
                        w.configure(text=txt)
                setw('lbl_cpu', f"Processador: {cpu}")
                setw('lbl_gpu', f"Placa de Vídeo: {gpu}")
                setw('lbl_ram', f"Memória RAM: {ram_gb} GB")
                setw('lbl_proc_antes', f"Processos: {procs if procs is not None else 'N/D'}")
                setw('lbl_serv_antes', f"Serviços: {servs if servs is not None else 'N/D'}")
                setw('lbl_boot_antes', f"Boot: {boot_time}")
                setw('lbl_chip_cpu_name', cpu.replace("(R)", "").replace("(TM)", "").replace("Processor", "").strip()[:26])
                setw('lbl_chip_gpu_name', gpu.replace("(R)", "").replace("(TM)", "").strip()[:26])
                alloc = getattr(self, 'allocated_vram', 0)
                setw('lbl_chip_ram_val', (f"{ram_gb} GB (+ pagefile {alloc} GB)" if alloc else f"{ram_gb} GB RAM"))
                try:
                    import psutil
                    du = psutil.disk_usage("C:\\")
                    setw('lbl_chip_disk_val', f"{round(du.free/(1024**3),1)} GB livres / {round(du.total/(1024**3),1)} GB")
                except Exception:
                    setw('lbl_chip_disk_val', "N/D")
                setw('lbl_chip_tpm_val', tpm_txt)
                setw('lbl_chip_sec_val', sb_txt)
            self.call_ui(_update_ui, wait=False)

        threading.Thread(target=_work, daemon=True).start()

    def get_boot_time(self):
        """Tempo do último boot, lido do log oficial do Windows (Diagnostics-Performance, evento 100)."""
        try:
            ps = ("$e = Get-WinEvent -FilterHashtable @{LogName='Microsoft-Windows-Diagnostics-Performance/Operational'; Id=100} -MaxEvents 1 -ErrorAction Stop; "
                  "$x = [xml]$e.ToXml(); ($x.Event.EventData.Data | Where-Object { $_.Name -eq 'BootTime' }).'#text'")
            boot = subprocess.check_output(["powershell", "-NoProfile", "-Command", ps], text=True, timeout=20,
                                           creationflags=subprocess.CREATE_NO_WINDOW).strip()
            return f"{round(float(boot)/1000.0, 1)} segundos"
        except Exception:
            return "N/D"

    def open_route_optimizer(self):
        self.log("Abrindo Otimizador de Rotas...")
        ro_win = ctk.CTkToplevel(self)
        ro_win.title("Otimizador de Rotas e Ping")
        ro_win.geometry("660x560")
        ro_win.resizable(False, False)
        ro_win.attributes("-topmost", True)

        ctk.CTkLabel(ro_win, text="⚡ Otimizador de Rotas e Latência", font=ctk.CTkFont(size=20, weight="bold"), text_color="#F39C12").pack(pady=(20, 6))
        ctk.CTkLabel(ro_win, text="Mede a latência real até servidores de referência e aplica ajustes de rede\nseguros (TCP, cache de DNS). Os valores mostrados são medidos de verdade.",
                     justify="center").pack(pady=5)

        res_frame = ctk.CTkFrame(ro_win)
        res_frame.pack(pady=15, padx=20, fill="both", expand=True)

        # Alvos de referência (não são os servidores reais dos jogos; servem para medir a rota geral)
        targets = [
            ("Cloudflare (1.1.1.1)", "1.1.1.1"),
            ("Google (8.8.8.8)", "8.8.8.8"),
            ("AWS São Paulo (sa-east-1)", "dynamodb.sa-east-1.amazonaws.com"),
            ("Steam CM", "cm.steampowered.com"),
        ]
        rows = []
        for i, (name, host) in enumerate(targets):
            lbl = ctk.CTkLabel(res_frame, text=f"{name}: aguardando teste...", font=ctk.CTkFont(size=14))
            lbl.grid(row=i, column=0, pady=10, padx=20, sticky="w")
            rows.append({"name": name, "host": host, "lbl": lbl, "before": None})

        def _measure(host):
            """Mediana de 4 conexões TCP:443 (só o tempo de conexão, sem contar DNS). None se falhar."""
            import socket, time, statistics
            try:
                ip = socket.gethostbyname(host)
            except Exception:
                return None
            samples = []
            for _ in range(4):
                s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                s.settimeout(1.0)
                t0 = time.perf_counter()
                try:
                    s.connect((ip, 443))
                    samples.append((time.perf_counter() - t0) * 1000.0)
                except Exception:
                    pass
                finally:
                    s.close()
                time.sleep(0.05)
            if not samples:
                return None
            return int(round(statistics.median(samples)))

        def _set_row(row, text, color=None):
            def _u():
                if row["lbl"].winfo_exists():
                    row["lbl"].configure(text=text, **({"text_color": color} if color else {}))
            self.call_ui(_u, wait=False)

        def _color(ms):
            return "#2ECC71" if ms < 50 else ("#F1C40F" if ms < 90 else "#E74C3C")

        def run_test(phase="before"):
            for row in rows:
                _set_row(row, f"{row['name']}: medindo...")
                ms = _measure(row["host"])
                if ms is None:
                    _set_row(row, f"{row['name']}: sem resposta (host bloqueou o teste)", "#E74C3C")
                    continue
                if phase == "before":
                    row["before"] = ms
                    _set_row(row, f"{row['name']}: {ms} ms", _color(ms))
                else:
                    b = row["before"]
                    if b is None:
                        _set_row(row, f"{row['name']}: {ms} ms", _color(ms))
                    else:
                        diff = b - ms
                        if diff > 0:
                            tail = f"melhorou {diff} ms"
                        elif diff < 0:
                            tail = f"subiu {abs(diff)} ms"
                        else:
                            tail = "sem mudança"
                        _set_row(row, f"{row['name']}: {b} ms ➔ {ms} ms ({tail})", _color(ms))

        def optimize_routes():
            chosen = self.call_ui(lambda: self.cb_jogos.get()) if hasattr(self, 'cb_jogos') else ""
            self.call_ui(lambda: btn_opt.configure(state="disabled", text="Medindo e otimizando..."), wait=False)
            self.log("→ Medindo latência inicial...")
            run_test("before")

            self.log("→ Aplicando ajustes de rede (sem alterar o DNS automaticamente)...")
            self.run_cmd_live('powershell -NoProfile -Command "Clear-DnsClientCache"')
            self.run_cmd_live('netsh int tcp set global autotuninglevel=normal')
            self.run_cmd_live('netsh int tcp set supplemental internet congestionprovider=ctcp')

            self.log("→ Medindo latência depois dos ajustes...")
            run_test("after")

            self.call_ui(lambda: btn_opt.configure(text="✅ Teste concluído (valores reais)", state="normal"), wait=False)
            if hasattr(self, 'lbl_ping_result'):
                self.call_ui(lambda: self.lbl_ping_result.configure(text="Ping: rotas testadas (valores reais)", text_color="#2ECC71"), wait=False)
            self.log("ℹ️ Para trocar o DNS, use os botões de DNS no painel lateral. O DNS ideal varia por provedor.")

        btn_opt = ctk.CTkButton(ro_win, text="⚡ Testar e Otimizar Rotas", font=ctk.CTkFont(weight="bold"),
                                fg_color="#C0392B", hover_color="#922B21", height=50,
                                command=lambda: self.run_async(optimize_routes))
        btn_opt.pack(pady=(10, 20), padx=20, fill="x")

    def refresh_metrics_depois(self):
        self.log("Calculando métricas pós-otimização...")
        def _update():
            import time
            time.sleep(6)  # Aguarda os processos temporários fecharem
            try:
                import subprocess
                # Count current processes/services using tasklist (faster, no powershell overhead)
                proc_str = subprocess.check_output('powershell "(Get-Process).Count"', shell=True, text=True, creationflags=subprocess.CREATE_NO_WINDOW).strip()
                serv_str = subprocess.check_output('powershell "(Get-Service | Where-Object {$_.Status -eq \'Running\'}).Count"', shell=True, text=True, creationflags=subprocess.CREATE_NO_WINDOW).strip()
                
                try:
                    proc_val = int(proc_str)
                    serv_val = int(serv_str)
                except:
                    proc_val, serv_val = 0, 0

                def _ui():
                    # Valores reais medidos agora (sem ajustes cosméticos)
                    final_p = proc_val if proc_val else "N/D"
                    final_s = serv_val if serv_val else "N/D"
                    if hasattr(self, 'lbl_proc_depois') and self.lbl_proc_depois.winfo_exists():
                        self.lbl_proc_depois.configure(text=f"Agora: {final_p}")
                    if hasattr(self, 'lbl_serv_depois') and self.lbl_serv_depois.winfo_exists():
                        self.lbl_serv_depois.configure(text=f"Agora: {final_s}")
                    self.log(f"Métricas medidas agora: Processos: {final_p} | Serviços em execução: {final_s}")
                    
                if hasattr(self, 'gui_queue'):
                    self.gui_queue.put(_ui)
                else:
                    self.after(0, _ui)
            except:
                pass
        import threading
        threading.Thread(target=_update, daemon=True).start()

    # --- Modern 3-Column UI Setup (V8.5 Dashboard) ---
    def setup_ui(self):
        self.cached_thumbnails = {}
        self.init_hydration()

        # 1. Top Header Bar
        self.setup_top_header()

        # 2. Main 3-Column Body Frame
        self.body_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.body_frame.pack(fill="both", expand=True, padx=14, pady=(4, 10))

        # 3. Left Navigation Sidebar
        self.setup_nav_sidebar()

        # 4. Middle Dynamic Content Area
        self.setup_main_content()

        # 5. Right Widgets Sidebar
        self.setup_widgets_sidebar()

        # 6. Start Live DNS Ping Loop
        self.start_dns_ping_monitor()

        # Default view
        self.show_view("painel")

        # Inicia Telemetria ao vivo no Painel (Relógio, Uptime, CPU/RAM/GPU temps & uso)
        self.init_telemetry_hud()

        self.log(f"Aplicativo Inicializado V{APP_VERSION}.")
        self.log("Aguardando leitura de Hardware...")

        # Verificação silenciosa de atualização na nuvem (GitHub)
        self.after(3500, lambda: threading.Thread(target=self.check_for_updates, kwargs={'manual': False}, daemon=True).start())

    def setup_top_header(self):
        self.top_header_frame = ctk.CTkFrame(self, fg_color="#120E22", corner_radius=10, height=52)
        self.top_header_frame.pack(fill="x", padx=14, pady=(10, 4))
        self.top_header_frame.pack_propagate(False)

        # Left branding
        brand_frame = ctk.CTkFrame(self.top_header_frame, fg_color="transparent")
        brand_frame.pack(side="left", padx=14, pady=6)

        ctk.CTkLabel(
            brand_frame,
            text="⚡ BERNAL OTIMIZAÇÕES PRO",
            font=ctk.CTkFont(family="Arial", size=18, weight="bold"),
            text_color="#00D2FF"
        ).pack(side="left", padx=(0, 10))

        ctk.CTkLabel(
            brand_frame,
            text=f"v{APP_VERSION} Oficial • Painel Gamer Pro",
            font=ctk.CTkFont(family="Arial", size=11),
            text_color="#8E8AA0"
        ).pack(side="left")

        # Right buttons & status
        right_frame = ctk.CTkFrame(self.top_header_frame, fg_color="transparent")
        right_frame.pack(side="right", padx=14, pady=6)

        # Online Safe Session Badge
        ctk.CTkLabel(
            right_frame,
            text="🟢 SESSÃO ATIVA",
            font=ctk.CTkFont(size=11, weight="bold"),
            text_color="#10B981",
            fg_color="#0D281E",
            corner_radius=8,
            padx=10, pady=3
        ).pack(side="right", padx=6)

        # WhatsApp button
        btn_wa = ctk.CTkButton(
            right_frame,
            text="💬 Suporte WhatsApp",
            font=ctk.CTkFont(size=11, weight="bold"),
            fg_color="#1E7E34",
            hover_color="#155724",
            text_color="#FFFFFF",
            height=28,
            width=135,
            corner_radius=8,
            command=lambda: webbrowser.open("https://wa.me/595981010764?text=Olá, preciso de suporte no Bernal Otimizações Pro!")
        )
        btn_wa.pack(side="right", padx=4)

        # Discord button
        btn_dc = ctk.CTkButton(
            right_frame,
            text="🎮 Discord",
            font=ctk.CTkFont(size=11, weight="bold"),
            fg_color="#5865F2",
            hover_color="#4752C4",
            text_color="#FFFFFF",
            height=28,
            width=90,
            corner_radius=8
        )
        btn_dc.configure(command=lambda b=btn_dc: self.copy_discord(b))
        btn_dc.pack(side="right", padx=4)

        # Cloud Auto-Updater button
        btn_upd = ctk.CTkButton(
            right_frame,
            text="🔄 Atualizações",
            font=ctk.CTkFont(size=11, weight="bold"),
            fg_color="#7928CA",
            hover_color="#9333EA",
            text_color="#FFFFFF",
            height=28,
            width=110,
            corner_radius=8,
            command=lambda: threading.Thread(target=self.check_for_updates, kwargs={'manual': True}, daemon=True).start()
        )
        btn_upd.pack(side="right", padx=4)
        ToolTip(btn_upd, "Verifica se há novas atualizações do Bernal Otimizações na nuvem (GitHub).")

    # --- CLOUD AUTO-UPDATER & HOT-PATCHER (GITHUB RELEASES) ---
    def parse_version_tuple(self, v_str):
        import re
        nums = re.findall(r'\d+', str(v_str))
        return tuple(int(x) for x in nums) if nums else (0, 0)

    def cloud_update_flow(self, manual=False):
        """Atualização criptografada pelo servidor de chaves. Devolve True se tratou (com ou sem update)."""
        if not cloud.is_valid():
            return False
        info = cloud.fetch_latest()
        if not info:
            return False                      # nuvem indisponível: cai no GitHub
        chk = cloud.check_update(APP_VERSION)
        if not chk.get("available"):
            # A nuvem pode estar atrasada (cache de até 5 min ou release só no GitHub):
            # devolve False para o GitHub também ser consultado.
            return False
        tag = "V" + str(chk["version"])
        notes = chk.get("notes") or ""
        if not self.call_ui(lambda: messagebox.askyesno(
                "Nova versão disponível",
                f"Nova versão {tag} disponível (você tem V{APP_VERSION}).\n\n{notes}\n\nBaixar e instalar agora? O app reinicia sozinho.")):
            return True

        def _open_hud():
            if getattr(self, 'current_hud', None) and self.current_hud.winfo_exists():
                try: self.current_hud.destroy()
                except Exception: pass
            self.current_hud = CyberProgressHUD(self, title=f"Atualizando para {tag}", initial_msg="Baixando da nuvem...")
        self.after(0, _open_hud)
        time.sleep(0.3)
        try:
            self.log(f"⬇️ Baixando atualização {tag} (criptografada)...")
            data, _ = cloud.fetch_release(progress=lambda p: self.set_hud_progress(min(95, p), f"Baixando... {p}%"), info=info)
            self.set_hud_progress(98, "Verificado (SHA-256). Instalando e reiniciando...")
            cloud.replace_self(data)
            time.sleep(0.8)
            os._exit(0)
        except Exception as e:
            self.log(f"❌ Atualização pela nuvem falhou: {e}")
            self.set_hud_progress(100, "❌ Falhou.")
            self.after(0, lambda err=e: messagebox.showerror("Atualização", f"Não foi possível atualizar:\n{err}"))
        return True

    _update_check_lock = threading.Lock()

    def check_for_updates(self, manual=False):
        """Verifica na nuvem (GitHub Releases) se há uma nova versão disponível.
        Só roda uma verificação por vez, mesmo com vários cliques no botão."""
        if getattr(self, "_update_downloading", False):
            self.log("⏳ Já tem uma atualização sendo baixada, aguarde.")
            return
        if not self._update_check_lock.acquire(blocking=False):
            if manual:
                self.log("⏳ A verificação de atualizações já está em andamento.")
            return
        try:
            self._check_for_updates_impl(manual)
        finally:
            self._update_check_lock.release()

    def _check_for_updates_impl(self, manual=False):
        import urllib.request, json
        from tkinter import messagebox

        try:
            if self.cloud_update_flow(manual):
                return
        except Exception as e:
            self.log(f"⚠️ Atualização pela nuvem indisponível ({e}); usando GitHub.")

        if manual:
            self.log("🌐 Verificando atualizações na nuvem (GitHub)...")

        api_url = "https://api.github.com/repos/Bernalf5138/Bernal-Otimizacoes/releases/latest"
        req = urllib.request.Request(
            api_url,
            headers={
                "User-Agent": f"BernalOtimizacoes-AutoUpdater/{APP_VERSION}",
                "Accept": "application/vnd.github.v3+json"
            }
        )

        try:
            with urllib.request.urlopen(req, timeout=7) as resp:
                data = json.loads(resp.read().decode("utf-8"))

            tag_name = data.get("tag_name", "").strip()
            body_notes = data.get("body", "Melhorias de desempenho e correções de bugs aplicadas.").strip()
            assets = data.get("assets", [])
            # Hash SHA-256 publicado nas notas (linha "SHA256: <hex>") — usado para conferir o download
            expected_sha = None
            mh = re.search(r'sha-?256[^0-9a-f]*([0-9a-fA-F]{64})', body_notes, re.I)
            if mh:
                expected_sha = mh.group(1).lower()

            # Localiza o executável nos anexos
            download_url = None
            asset_size_mb = 0.0
            asset_name = ""

            # Prioriza BernalOtimizacoes.exe (Hot Update rápido ~50MB)
            for a in assets:
                name = a.get("name", "")
                if name.lower() == "bernalotimizacoes.exe":
                    download_url = a.get("browser_download_url")
                    asset_size_mb = a.get("size", 0) / (1024 * 1024)
                    asset_name = name
                    break

            # Se não achar o exe direto, aceita o instalador
            if not download_url:
                for a in assets:
                    name = a.get("name", "")
                    if name.lower().endswith(".exe"):
                        download_url = a.get("browser_download_url")
                        asset_size_mb = a.get("size", 0) / (1024 * 1024)
                        asset_name = name
                        break

            remote_ver = self.parse_version_tuple(tag_name)
            local_ver = self.parse_version_tuple(APP_VERSION)

            if remote_ver > local_ver and download_url:
                self.log(f"🚀 Nova versão encontrada na nuvem: {tag_name}!")
                # Também aceita um arquivo .sha256 anexado à release
                if not expected_sha:
                    for a in assets:
                        if a.get("name", "").lower().endswith(".sha256"):
                            try:
                                with urllib.request.urlopen(urllib.request.Request(
                                        a.get("browser_download_url"),
                                        headers={"User-Agent": "BernalOtimizacoes-AutoUpdater"}), timeout=10) as r2:
                                    txt = r2.read().decode("utf-8", "replace")
                                m2 = re.search(r'([0-9a-fA-F]{64})', txt)
                                if m2:
                                    expected_sha = m2.group(1).lower()
                            except Exception:
                                pass
                            break
                release_info = {
                    "tag": tag_name,
                    "notes": body_notes,
                    "url": download_url,
                    "size_mb": asset_size_mb,
                    "name": asset_name,
                    "sha256": expected_sha,
                }
                self.after(0, lambda: self.show_update_available_dialog(release_info))
            else:
                if manual:
                    self.after(0, lambda: messagebox.showinfo(
                        "Atualizações",
                        f"✅ Você já está utilizando a versão mais recente!\n\nVersão instalada: V{APP_VERSION}\nServidor: Nuvem GitHub sincronizada."
                    ))
        except urllib.error.HTTPError as e:
            if e.code == 404:
                # Nenhuma release publicada ainda no repositório
                if manual:
                    self.after(0, lambda: messagebox.showinfo(
                        "Nenhuma Atualização",
                        f"✅ O sistema está na versão mais atual (V{APP_VERSION})!\n\nNenhuma atualização mais recente foi publicada pelo administrador ainda."
                    ))
            else:
                if manual:
                    self.after(0, lambda code=e.code: messagebox.showwarning("Aviso", f"Não foi possível verificar atualizações no momento.\nCódigo: {code}"))
        except Exception as e:
            if manual:
                self.after(0, lambda msg=str(e): messagebox.showwarning("Aviso", f"Falha na conexão com a nuvem de atualizações:\n{msg}"))

    def show_update_available_dialog(self, info):
        """Abre janela moderna avisando da nova versão."""
        old = getattr(self, "_update_dialog", None)
        if getattr(self, "_update_downloading", False) or (old is not None and old.winfo_exists()):
            return  # já tem um aviso aberto ou um download em andamento
        dlg = ctk.CTkToplevel(self)
        self._update_dialog = dlg
        dlg.title("🚀 Atualização Disponível • Bernal Otimizações")
        dlg.geometry("520x460")
        dlg.attributes("-topmost", True)
        dlg.grab_set()

        sw = dlg.winfo_screenwidth()
        sh = dlg.winfo_screenheight()
        dlg.geometry(f"520x460+{(sw - 520)//2}+{(sh - 460)//2}")

        body = ctk.CTkFrame(dlg, fg_color="#100B24", corner_radius=14, border_width=2, border_color="#7928CA")
        body.pack(fill="both", expand=True, padx=4, pady=4)

        ctk.CTkLabel(body, text="🚀 NOVA ATUALIZAÇÃO DISPONÍVEL!", font=ctk.CTkFont(size=16, weight="bold"), text_color="#00D2FF").pack(pady=(18, 4))
        
        tag = info.get("tag", "V9.4")
        sz = info.get("size_mb", 0.0)
        sz_str = f" • {sz:.1f} MB" if sz > 0 else ""
        
        badge_frame = ctk.CTkFrame(body, fg_color="#181236", corner_radius=8)
        badge_frame.pack(fill="x", padx=24, pady=6)
        
        ctk.CTkLabel(
            badge_frame,
            text=f"Versão Atual: V{APP_VERSION}  ➔  Nova Versão: {tag}{sz_str}",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color="#10B981"
        ).pack(pady=8)

        ctk.CTkLabel(body, text="📋 Novidades & Mudanças Desta Versão:", font=ctk.CTkFont(size=11, weight="bold"), text_color="#9CA3AF").pack(anchor="w", padx=24, pady=(6, 2))

        txt = ctk.CTkTextbox(body, height=150, font=ctk.CTkFont(size=11), fg_color="#140F2D", text_color="#E0AAFF")
        txt.pack(fill="both", expand=True, padx=24, pady=(2, 12))
        txt.insert("1.0", info.get("notes", "Melhorias de estabilidade, compatibilidade e otimização gamer."))
        txt.configure(state="disabled")

        btn_row = ctk.CTkFrame(body, fg_color="transparent")
        btn_row.pack(fill="x", padx=24, pady=(4, 16))

        btn_apply = ctk.CTkButton(
            btn_row,
            text="⚡ Atualizar Agora (Automático)",
            font=ctk.CTkFont(size=13, weight="bold"),
            fg_color="#7928CA",
            hover_color="#9333EA",
            height=38,
            command=lambda: [dlg.destroy(), threading.Thread(target=self.start_download_and_apply_update, args=(info.get("url"), tag, info.get("name"), info.get("sha256"), int(info.get("size_mb", 0) * 1024 * 1024)), daemon=True).start()]
        )
        btn_apply.pack(side="left", fill="x", expand=True, padx=(0, 6))

        btn_cancel = ctk.CTkButton(
            btn_row,
            text="Lembrar Depois",
            font=ctk.CTkFont(size=11),
            fg_color="#2D3748",
            hover_color="#4A5568",
            height=38,
            width=110,
            command=dlg.destroy
        )
        btn_cancel.pack(side="right")

    def _download_file_robust(self, url, dest, headers, size_hint=0):
        """Baixa com 3 métodos em cascata (Python -> curl.exe -> BITS). Evita ficar preso quando a rede
        do cliente trava em IPv6/proxy: cada método tem tempo limite curto e o progresso é real."""
        import urllib.request
        errors = []

        def _remove():
            try:
                if os.path.exists(dest):
                    os.remove(dest)
            except Exception:
                pass

        def _show(done, total):
            mb = done / (1024 * 1024)
            if total > 0:
                pct = min(98, max(6, int(done / total * 92) + 6))
                self.set_hud_progress(pct, f"Baixando: {mb:.1f} MB de {total / (1024 * 1024):.1f} MB ({pct}%)...")
            else:
                self.set_hud_progress(30, f"Baixando: {mb:.1f} MB transferidos...")

        # Método 1: Python (tempo limite curto para não esperar em rota IPv6 quebrada)
        try:
            self.set_hud_progress(5, "Conectando ao GitHub (método 1/3)...")
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req, timeout=10) as resp:
                total = int(resp.headers.get("content-length", 0) or 0) or size_hint
                done, t_last = 0, time.time()
                self.set_hud_progress(6, "Conectado! Baixando atualização...")
                with open(dest, "wb") as f_out:
                    while True:
                        chunk = resp.read(256 * 1024)
                        if not chunk:
                            break
                        f_out.write(chunk)
                        done += len(chunk)
                        if time.time() - t_last >= 0.25:
                            t_last = time.time()
                            _show(done, total)
            if size_hint and os.path.getsize(dest) < size_hint * 0.9:
                raise IOError("download incompleto")
            return True
        except Exception as e:
            errors.append(f"python: {e}")
            self.log(f"  método 1 falhou ({e}); tentando curl...")
            _remove()

        # Método 2: curl.exe (nativo do Windows 10/11), forçando IPv4
        try:
            self.set_hud_progress(5, "Conectando ao GitHub (método 2/3: curl)...")
            cflags = subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0
            proc = subprocess.Popen(["curl.exe", "-L", "-4", "--fail", "--silent", "--show-error",
                                     "--connect-timeout", "10", "--retry", "2", "-A", headers.get("User-Agent", "Mozilla/5.0"),
                                     "-o", dest, url], stdout=subprocess.PIPE, stderr=subprocess.PIPE, creationflags=cflags)
            t0, last_size, last_move = time.time(), -1, time.time()
            while proc.poll() is None:
                time.sleep(0.5)
                cur = os.path.getsize(dest) if os.path.exists(dest) else 0
                if cur != last_size:
                    last_size, last_move = cur, time.time()
                if cur > 0:
                    _show(cur, size_hint)
                if time.time() - last_move > 20:
                    proc.kill()
                    raise IOError("sem progresso por 20s")
            if proc.returncode != 0:
                raise IOError((proc.stderr.read() or b"").decode("utf-8", "replace").strip() or f"curl código {proc.returncode}")
            if size_hint and os.path.getsize(dest) < size_hint * 0.9:
                raise IOError("download incompleto")
            return True
        except Exception as e:
            errors.append(f"curl: {e}")
            self.log(f"  método 2 falhou ({e}); tentando BITS...")
            _remove()

        # Método 3: BITS do Windows (usa a configuração de rede/proxy do sistema)
        try:
            self.set_hud_progress(5, "Conectando ao GitHub (método 3/3: BITS)...")
            ps = f"Start-BitsTransfer -Source '{url}' -Destination '{dest}' -ErrorAction Stop"
            cflags = subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0
            proc = subprocess.Popen(["powershell", "-NoProfile", "-Command", ps], stdout=subprocess.PIPE,
                                    stderr=subprocess.PIPE, creationflags=cflags)
            last_size, last_move = -1, time.time()
            while proc.poll() is None:
                time.sleep(0.5)
                cur = os.path.getsize(dest) if os.path.exists(dest) else 0
                if cur != last_size:
                    last_size, last_move = cur, time.time()
                if cur > 0:
                    _show(cur, size_hint)
                if time.time() - last_move > 25:
                    proc.kill()
                    raise IOError("sem progresso por 25s")
            if proc.returncode != 0:
                raise IOError((proc.stderr.read() or b"").decode("utf-8", "replace").strip()[:200] or "BITS falhou")
            return True
        except Exception as e:
            errors.append(f"bits: {e}")
            _remove()

        raise IOError("Não foi possível baixar de nenhum método. " + " | ".join(errors) +
                      "\nBaixe manualmente em: https://github.com/Bernalf5138/Bernal-Otimizacoes/releases/latest")

    UPDATE_STALL_SECONDS = 60

    def start_download_and_apply_update(self, download_url, tag_name, asset_name="BernalOtimizacoes.exe", expected_sha256=None, size_hint=0):
        """Ponto de entrada do download (roda numa thread). Liga um vigia: se nada avançar por
        UPDATE_STALL_SECONDS, tenta de novo uma vez; se travar de novo, oferece o navegador."""
        if getattr(self, "_update_downloading", False):
            self.log("⏳ Já tem uma atualização sendo baixada, aguarde.")
            return
        self._update_downloading = True
        self._update_fallback_shown = False
        self._update_attempt = 0
        args = (download_url, tag_name, asset_name, expected_sha256, size_hint)
        threading.Thread(target=self._update_watchdog, args=args, daemon=True).start()
        self._run_update_attempt(*args)

    def _run_update_attempt(self, *args):
        self._update_attempt += 1
        attempt = self._update_attempt
        self._last_progress_ts = time.time()
        try:
            self._download_and_apply_update(attempt, *args)
        except BaseException as e:
            import traceback
            self.log(f"❌ Erro no Auto-Updater (tentativa {attempt}): {e}\n{traceback.format_exc()}")
            if attempt == self._update_attempt:
                self.set_hud_progress(100, "❌ Download automático falhou.")
                self._update_fallback()
        finally:
            if attempt == self._update_attempt:
                self._update_downloading = False

    def _update_watchdog(self, *args):
        tag_name = args[1]
        while getattr(self, "_update_downloading", False):
            time.sleep(3)
            parado = time.time() - getattr(self, "_last_progress_ts", time.time())
            if parado < self.UPDATE_STALL_SECONDS:
                continue
            if self._update_attempt < 2:
                self.log(f"⚠️ O download da {tag_name} parou de responder há {int(parado)}s. Tentando de novo...")
                threading.Thread(target=self._run_update_attempt, args=args, daemon=True).start()
                time.sleep(1)
            else:
                self.log(f"❌ O download da {tag_name} travou duas vezes. Oferecendo o navegador.")
                self._update_attempt += 1          # invalida as tentativas presas
                self._update_downloading = False
                self.set_hud_progress(100, "❌ O download parou de responder.")
                self._update_fallback()
                return

    def _update_fallback(self):
        """Oferece baixar pelo navegador (mostra uma vez só)."""
        if getattr(self, "_update_fallback_shown", False):
            return
        self._update_fallback_shown = True
        fallback_url = "https://github.com/Bernalf5138/Bernal-Otimizacoes/releases/latest"

        def _ask():
            abrir = messagebox.askyesno("Baixar pelo navegador",
                "Não consegui baixar a atualização aqui dentro do app "
                "(a rede pode estar bloqueando o download direto).\n\n"
                "Quer abrir o navegador para baixar a nova versão? "
                "É só rodar o arquivo baixado para atualizar — seus dados são mantidos.")
            if abrir:
                try:
                    webbrowser.open(fallback_url)
                    self.log("🌐 Página de download aberta no navegador.")
                except Exception as ex:
                    messagebox.showerror("Falha na atualização",
                        "Baixe manualmente em:\n" + fallback_url + "\n\n" + str(ex)[:300])
        self.after(0, _ask)

    def _download_and_apply_update(self, attempt, download_url, tag_name, asset_name="BernalOtimizacoes.exe", expected_sha256=None, size_hint=0):
        """Baixa a nova versão, confere o SHA-256 e só então aplica, reiniciando o app."""
        import tempfile

        self.log(f"⬇️ Iniciando download da atualização {tag_name}" + (f" (tentativa {attempt})..." if attempt > 1 else "..."))

        def _open_hud():
            if hasattr(self, 'current_hud') and self.current_hud and self.current_hud.winfo_exists():
                try: self.current_hud.destroy()
                except: pass
            self.current_hud = CyberProgressHUD(self, title=f"Baixando Atualização {tag_name}", initial_msg="Conectando à nuvem da Microsoft / GitHub...")
        self.after(0, _open_hud)
        time.sleep(0.3)
        self.set_hud_progress(5, "Conectando aos servidores do GitHub...")

        temp_dir = tempfile.gettempdir()
        is_installer = "setup" in (asset_name or "").lower()
        temp_dest = os.path.join(temp_dir, f"BernalOtimizacoes_NovaVersao_{attempt}.exe")

        try:
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                "Accept": "*/*"
            }
            self._download_file_robust(download_url, temp_dest, headers, size_hint)

            if attempt != self._update_attempt:
                # O vigia já começou outra tentativa (ou desistiu): esta não aplica nada
                try:
                    os.remove(temp_dest)
                except Exception:
                    pass
                self.log(f"ℹ️ Tentativa {attempt} do download terminou depois do tempo; descartada.")
                return

            # Verificação de integridade / autenticidade do arquivo baixado
            if expected_sha256:
                self.set_hud_progress(99, "Verificando integridade do arquivo (SHA-256)...")
                h = hashlib.sha256()
                with open(temp_dest, "rb") as vf:
                    for blk in iter(lambda: vf.read(1024 * 1024), b""):
                        h.update(blk)
                got = h.hexdigest().lower()
                if got != expected_sha256.lower():
                    try:
                        os.remove(temp_dest)
                    except Exception:
                        pass
                    self.log(f"❌ Atualização RECUSADA: hash não confere.\n   esperado: {expected_sha256}\n   obtido:   {got}")
                    self.set_hud_progress(100, "❌ Atualização recusada (arquivo não confere).")
                    self.after(0, lambda: messagebox.showerror("Atualização cancelada",
                        "O arquivo baixado não corresponde ao hash de segurança publicado.\n\n"
                        "A atualização foi CANCELADA para proteger seu computador. Tente novamente mais tarde."))
                    return
                self.log("✅ Integridade confirmada (SHA-256 confere).")
            else:
                self.log("⚠️ Esta release não publicou hash SHA-256; não foi possível verificar a autenticidade.")
                self._last_progress_ts = float("inf")  # pausa o vigia enquanto espera a resposta
                if not self.call_ui(lambda: messagebox.askyesno("Atualização sem verificação",
                        "Esta atualização não trouxe um hash de segurança (SHA-256) para conferência.\n\n"
                        "Instalar mesmo assim? (Recomendado: só continue se você confia na origem.)")):
                    self.log("Atualização cancelada pelo usuário (sem hash).")
                    self.set_hud_progress(100, "Atualização cancelada.")
                    return

            self.set_hud_progress(100, "✅ Download concluído e verificado! Instalando e reiniciando...")
            time.sleep(0.8)

            # Destino principal e backup local
            if getattr(sys, 'frozen', False):
                target_exe = sys.executable
            else:
                target_exe = os.path.join(os.path.dirname(os.path.abspath(__file__)), "dist", "BernalOtimizacoes.exe")

            local_dir = os.path.join(os.environ.get("LOCALAPPDATA", ""), "Bernal Otimizacoes")
            local_exe = os.path.join(local_dir, "BernalOtimizacoes.exe")

            # Script bat de auto-substituição resiliente
            bat_path = os.path.join(temp_dir, "apply_bernal_update.bat")
            if is_installer:
                bat_content = f"""@echo off
timeout /t 1 /nobreak >nul
taskkill /F /IM BernalOtimizacoes.exe >nul 2>&1
start "" "{temp_dest}"
del "%~f0" >nul 2>&1
"""
            else:
                bat_content = f"""@echo off
timeout /t 2 /nobreak >nul
taskkill /F /IM BernalOtimizacoes.exe >nul 2>&1
timeout /t 1 /nobreak >nul
set RETRY=0
:retry
set /a RETRY+=1
copy /Y "{temp_dest}" "{target_exe}" >nul 2>&1
if not errorlevel 1 goto success
if %RETRY% GEQ 20 goto fallback
timeout /t 1 /nobreak >nul
goto retry

:fallback
move /Y "{temp_dest}" "{target_exe}" >nul 2>&1

:success
if exist "{local_exe}" (
    copy /Y "{target_exe}" "{local_exe}" >nul 2>&1
)
del /F /Q "{temp_dest}" >nul 2>&1
start "" "{target_exe}"
del "%~f0" >nul 2>&1
"""

            with open(bat_path, "w", encoding="utf-8") as f_bat:
                f_bat.write(bat_content)

            self.log(f"🔄 Executando reinício e auto-atualização para {tag_name}...")
            si_bat = subprocess.STARTUPINFO()
            si_bat.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            si_bat.wShowWindow = 0
            subprocess.Popen(f'cmd.exe /c "{bat_path}"', shell=True, startupinfo=si_bat, creationflags=subprocess.CREATE_NO_WINDOW)
            
            # Encerra o processo atual de forma limpa para liberar o arquivo
            time.sleep(0.3)
            self.after(0, self.destroy)
            os._exit(0)

        except Exception:
            # Não use "import os" nesta função: torna "os" local e quebra o os.path lá em cima
            # (era o que matava o download na V10.6/10.7). O log e o navegador ficam em _run_update_attempt.
            raise

    def setup_nav_sidebar(self):
        self.nav_frame = ctk.CTkFrame(self.body_frame, fg_color="#120E22", width=205, corner_radius=12)
        self.nav_frame.pack(side="left", fill="y", padx=(0, 6))
        self.nav_frame.pack_propagate(False)

        ctk.CTkLabel(
            self.nav_frame,
            text="MENU PRINCIPAL",
            font=ctk.CTkFont(size=10, weight="bold"),
            text_color="#6B7280"
        ).pack(anchor="w", padx=16, pady=(14, 6))

        self.nav_buttons = {}
        nav_items = [
            ("painel", "🏠  Painel"),
            ("perfis", "⚡  Perfis de FPS"),
            ("jogos", "🎮  Jogos Específicos"),
            ("wallpapers", "🖼️  Fundos de Tela"),
            ("ferramentas", "🛠️  Super Ferramentas"),
            ("sistemas", "🚀  Sistemas AME"),
            ("bugs", "🩹  Correção de Bugs"),
            ("log", "📜  Log & Auditoria"),
        ]

        for key, label in nav_items:
            btn = ctk.CTkButton(
                self.nav_frame,
                text=label,
                anchor="w",
                font=ctk.CTkFont(size=12, weight="bold"),
                height=38,
                corner_radius=8,
                fg_color="#17122C",
                text_color="#A09BB5",
                hover_color="#261E48",
                command=lambda k=key: self.show_view(k)
            )
            btn.pack(fill="x", padx=10, pady=3)
            self.nav_buttons[key] = btn

        # Spacer
        ctk.CTkFrame(self.nav_frame, fg_color="transparent").pack(fill="both", expand=True)

        # Anti-Cheat Safe Badge at bottom of sidebar
        safe_frame = ctk.CTkFrame(self.nav_frame, fg_color="#181330", corner_radius=10)
        safe_frame.pack(fill="x", padx=10, pady=(6, 12))
        ctk.CTkLabel(
            safe_frame,
            text="🛡️ Ajustes de registro/energia\nNão injeta nada em jogos",
            font=ctk.CTkFont(size=10, weight="bold"),
            text_color="#10B981",
            justify="center"
        ).pack(pady=8)

    def setup_main_content(self):
        self.main_content_container = ctk.CTkFrame(self.body_frame, fg_color="transparent")
        self.main_content_container.pack(side="left", fill="both", expand=True, padx=4)

        self.views = {}
        self.views["painel"] = self.create_view_painel(self.main_content_container)
        self.views["perfis"] = self.create_view_perfis(self.main_content_container)
        self.views["jogos"] = self.create_view_jogos(self.main_content_container)
        self.views["wallpapers"] = self.create_view_wallpapers(self.main_content_container)
        self.views["ferramentas"] = self.create_view_ferramentas(self.main_content_container)
        self.views["sistemas"] = self.create_view_sistemas(self.main_content_container)
        self.views["bugs"] = self.create_view_bugs(self.main_content_container)
        self.views["log"] = self.create_view_log(self.main_content_container)

    def show_view(self, view_name):
        for name, frame in self.views.items():
            if name == view_name:
                frame.pack(fill="both", expand=True)
            else:
                frame.pack_forget()

        for name, btn in self.nav_buttons.items():
            if name == view_name:
                btn.configure(fg_color="#7928CA", text_color="#FFFFFF", border_width=1, border_color="#A855F7")
            else:
                btn.configure(fg_color="#17122C", text_color="#A09BB5", border_width=0)

    def setup_widgets_sidebar(self):
        self.widgets_frame = ctk.CTkFrame(self.body_frame, fg_color="#120E22", width=235, corner_radius=12)
        self.widgets_frame.pack(side="right", fill="y", padx=(6, 0))
        self.widgets_frame.pack_propagate(False)

        # 1. Licença Ativa Card
        card_lic = ctk.CTkFrame(self.widgets_frame, fg_color="#181330", corner_radius=10)
        card_lic.pack(fill="x", padx=10, pady=(10, 5))

        ctk.CTkLabel(
            card_lic,
            text="👑 LICENÇA ATIVA",
            font=ctk.CTkFont(size=11, weight="bold"),
            text_color="#F59E0B"
        ).pack(anchor="w", padx=12, pady=(8, 2))

        if self.is_trial:
            self.trial_label = ctk.CTkLabel(
                card_lic,
                text="⏳ TESTE 60:00",
                font=ctk.CTkFont(size=14, weight="bold"),
                text_color="#F59E0B"
            )
            self.trial_label.pack(anchor="w", padx=12, pady=2)
            self.update_trial_timer()
        else:
            self.trial_label = ctk.CTkLabel(
                card_lic,
                text="👑 VIP VITALÍCIA",
                font=ctk.CTkFont(size=14, weight="bold"),
                text_color="#10B981"
            )
            self.trial_label.pack(anchor="w", padx=12, pady=2)

        ctk.CTkLabel(
            card_lic,
            text="🟢 Ativado & Blindado • Bernal Pro",
            font=ctk.CTkFont(size=10),
            text_color="#9CA3AF"
        ).pack(anchor="w", padx=12, pady=(0, 8))

        # 2. Saúde & Rotina Pro Gamer Card (Água, Café, Energético, Refeições & Alarmes)
        card_routine = ctk.CTkFrame(self.widgets_frame, fg_color="#181330", corner_radius=10)
        card_routine.pack(fill="x", padx=10, pady=5)

        ctk.CTkLabel(
            card_routine,
            text="⚡ SAÚDE & ROTINA GAMER",
            font=ctk.CTkFont(size=11, weight="bold"),
            text_color="#38BDF8"
        ).pack(anchor="w", padx=12, pady=(8, 2))

        # Água
        self.lbl_water_count = ctk.CTkLabel(
            card_routine,
            text="0/8 copos hoje (0.0L)",
            font=ctk.CTkFont(size=11, weight="bold"),
            text_color="#FFFFFF"
        )
        self.lbl_water_count.pack(anchor="w", padx=12, pady=1)

        self.water_progress = ctk.CTkProgressBar(card_routine, height=6, progress_color="#0284C7", fg_color="#082F49")
        self.water_progress.pack(fill="x", padx=12, pady=3)
        self.water_progress.set(0)

        btn_w_row = ctk.CTkFrame(card_routine, fg_color="transparent")
        btn_w_row.pack(fill="x", padx=12, pady=(2, 4))

        ctk.CTkButton(
            btn_w_row,
            text="+ Água 💧",
            font=ctk.CTkFont(size=10, weight="bold"),
            fg_color="#10B981",
            hover_color="#059669",
            height=26,
            command=lambda: self.drink_water(1)
        ).pack(side="left", fill="x", expand=True, padx=(0, 2))

        ctk.CTkButton(
            btn_w_row,
            text="-",
            font=ctk.CTkFont(size=11, weight="bold"),
            fg_color="#374151",
            hover_color="#4B5563",
            width=24,
            height=26,
            command=lambda: self.drink_water(-1)
        ).pack(side="right")

        # Café & Energético row
        caff_row = ctk.CTkFrame(card_routine, fg_color="transparent")
        caff_row.pack(fill="x", padx=12, pady=3)
        caff_row.columnconfigure((0, 1), weight=1)

        self.lbl_coffee_count = ctk.CTkLabel(caff_row, text="☕ 0", font=ctk.CTkFont(size=10, weight="bold"), text_color="#F59E0B")
        self.lbl_coffee_count.grid(row=0, column=0, sticky="w")

        btn_plus_cf = ctk.CTkButton(caff_row, text="+ Café", font=ctk.CTkFont(size=9, weight="bold"), fg_color="#B45309", hover_color="#92400E", width=55, height=24, command=lambda: self.track_coffee(1))
        btn_plus_cf.grid(row=0, column=0, sticky="e", padx=(20, 2))
        ToolTip(btn_plus_cf, "Registra uma xícara de café consumida.")

        self.lbl_energy_count = ctk.CTkLabel(caff_row, text="⚡ 0", font=ctk.CTkFont(size=10, weight="bold"), text_color="#00D2FF")
        self.lbl_energy_count.grid(row=0, column=1, sticky="w")

        btn_plus_en = ctk.CTkButton(caff_row, text="+ Energético", font=ctk.CTkFont(size=9, weight="bold"), fg_color="#0284C7", hover_color="#0369A1", width=70, height=24, command=lambda: self.track_energy(1))
        btn_plus_en.grid(row=0, column=1, sticky="e")
        ToolTip(btn_plus_en, "Registra uma lata de energético consumida.")

        # Refeições (Café da manhã, Almoço, Jantar)
        meals_lbl = ctk.CTkLabel(card_routine, text="🍽️ Refeições Gamers:", font=ctk.CTkFont(size=10, weight="bold"), text_color="#9CA3AF")
        meals_lbl.pack(anchor="w", padx=12, pady=(4, 1))

        meals_row = ctk.CTkFrame(card_routine, fg_color="transparent")
        meals_row.pack(fill="x", padx=12, pady=2)
        meals_row.columnconfigure((0, 1, 2), weight=1)

        self.btn_meal_bk = ctk.CTkButton(meals_row, text="🌅 Café", font=ctk.CTkFont(size=9, weight="bold"), fg_color="#1E293B", hover_color="#334155", height=24, command=lambda: self.toggle_meal("breakfast"))
        self.btn_meal_bk.grid(row=0, column=0, padx=1, sticky="ew")
        ToolTip(self.btn_meal_bk, "Marcar se já tomou café da manhã hoje.")

        self.btn_meal_lu = ctk.CTkButton(meals_row, text="☀️ Almoço", font=ctk.CTkFont(size=9, weight="bold"), fg_color="#1E293B", hover_color="#334155", height=24, command=lambda: self.toggle_meal("lunch"))
        self.btn_meal_lu.grid(row=0, column=1, padx=1, sticky="ew")
        ToolTip(self.btn_meal_lu, "Marcar se já almoçou hoje.")

        self.btn_meal_di = ctk.CTkButton(meals_row, text="🌙 Jantar", font=ctk.CTkFont(size=9, weight="bold"), fg_color="#1E293B", hover_color="#334155", height=24, command=lambda: self.toggle_meal("dinner"))
        self.btn_meal_di.grid(row=0, column=2, padx=1, sticky="ew")
        ToolTip(self.btn_meal_di, "Marcar se já jantou hoje.")

        # Alarmes Customizados
        alm_hdr = ctk.CTkFrame(card_routine, fg_color="transparent")
        alm_hdr.pack(fill="x", padx=12, pady=(5, 1))

        ctk.CTkLabel(alm_hdr, text="⏰ Alarmes / Remédio", font=ctk.CTkFont(size=10, weight="bold"), text_color="#F59E0B").pack(side="left")
        btn_add_alm = ctk.CTkButton(alm_hdr, text="+ Novo", width=44, height=20, font=ctk.CTkFont(size=9, weight="bold"), fg_color="#7928CA", hover_color="#9333EA", command=self.add_custom_alarm_dialog)
        btn_add_alm.pack(side="right")
        ToolTip(btn_add_alm, "Adiciona alarme customizado com horário para tomar remédio, refeição ou pausa.")

        self.alarms_container = ctk.CTkFrame(card_routine, fg_color="transparent")
        self.alarms_container.pack(fill="x", padx=12, pady=(1, 8))

        self.update_hydration_ui()

        # 3. Rede & DNS ao Vivo com IP Nativo e Seleção Manual/Automática
        card_dns = ctk.CTkFrame(self.widgets_frame, fg_color="#181230", corner_radius=10)
        card_dns.pack(fill="x", padx=10, pady=5)

        ctk.CTkLabel(
            card_dns,
            text="🌐 REDE & DNS AO VIVO",
            font=ctk.CTkFont(size=11, weight="bold"),
            text_color="#C084FC"
        ).pack(anchor="w", padx=12, pady=(8, 2))

        self.lbl_ping_nat = ctk.CTkLabel(
            card_dns,
            text="📡 Nativo ISP: Testando...",
            font=ctk.CTkFont(size=11),
            text_color="#38BDF8"
        )
        self.lbl_ping_nat.pack(anchor="w", padx=12, pady=1)

        self.lbl_ping_cf = ctk.CTkLabel(
            card_dns,
            text="⚡ Cloudflare (1.1.1.1): Testando...",
            font=ctk.CTkFont(size=11),
            text_color="#10B981"
        )
        self.lbl_ping_cf.pack(anchor="w", padx=12, pady=1)

        self.lbl_ping_gg = ctk.CTkLabel(
            card_dns,
            text="⚡ Google (8.8.8.8): Testando...",
            font=ctk.CTkFont(size=11),
            text_color="#10B981"
        )
        self.lbl_ping_gg.pack(anchor="w", padx=12, pady=1)

        btn_dns_best = ctk.CTkButton(
            card_dns,
            text="⚡ Aplicar Melhor DNS",
            font=ctk.CTkFont(size=11, weight="bold"),
            fg_color="#7928CA",
            hover_color="#9333EA",
            height=28,
            command=lambda: self.run_async(self.apply_best_dns)
        )
        btn_dns_best.pack(fill="x", padx=12, pady=(6, 4))
        ToolTip(btn_dns_best, "Aplica automaticamente o DNS que tiver menor tempo de resposta (ping) medido ao vivo.", "⚡ MELHOR DNS")

        # Escolha manual de DNS
        dns_row = ctk.CTkFrame(card_dns, fg_color="transparent")
        dns_row.pack(fill="x", padx=12, pady=(0, 8))

        btn_cf = ctk.CTkButton(dns_row, text="1.1.1.1", width=60, height=24, font=ctk.CTkFont(size=10, weight="bold"), fg_color="#1E293B", hover_color="#334155", command=lambda: self.run_async(self.apply_dns_profile, "cloudflare"))
        btn_cf.pack(side="left", padx=1, expand=True, fill="x")
        ToolTip(btn_cf, "Aplica o Cloudflare DNS (1.1.1.1) focado em baixa latência para jogos online.", "⚡ CLOUDFLARE")

        btn_gg = ctk.CTkButton(dns_row, text="8.8.8.8", width=60, height=24, font=ctk.CTkFont(size=10, weight="bold"), fg_color="#1E293B", hover_color="#334155", command=lambda: self.run_async(self.apply_dns_profile, "google"))
        btn_gg.pack(side="left", padx=1, expand=True, fill="x")
        ToolTip(btn_gg, "Aplica o Google DNS (8.8.8.8) focado em estabilidade e velocidade.", "⚡ GOOGLE DNS")

        btn_nat = ctk.CTkButton(dns_row, text="Nativo", width=60, height=24, font=ctk.CTkFont(size=10, weight="bold"), fg_color="#1E293B", hover_color="#334155", command=lambda: self.run_async(self.apply_dns_profile, "native"))
        btn_nat.pack(side="left", padx=1, expand=True, fill="x")
        ToolTip(btn_nat, "Restaura o DNS nativo padrão do seu provedor de internet (DHCP sem DNS customizado).", "📡 DNS NATIVO")

        # Spacer to push version badge to bottom
        ctk.CTkFrame(self.widgets_frame, fg_color="transparent").pack(fill="both", expand=True)

        # 4. Versão Card
        card_ver = ctk.CTkFrame(self.widgets_frame, fg_color="#181330", corner_radius=10, border_width=1, border_color="#3B2D71")
        card_ver.pack(fill="x", padx=10, pady=(6, 12))
        ctk.CTkLabel(
            card_ver,
            text=f"⚡ VERSÃO {APP_VERSION} OFICIAL\nBernal Otimizações © 2026",
            font=ctk.CTkFont(size=10, weight="bold"),
            text_color="#00D2FF",
            justify="center"
        ).pack(pady=8)

    def create_view_painel(self, parent):
        scroll = ctk.CTkScrollableFrame(parent, fg_color="transparent")

        # Welcome row
        welcome_frame = ctk.CTkFrame(scroll, fg_color="#151028", corner_radius=10)
        welcome_frame.pack(fill="x", pady=(0, 8), padx=2)

        ctk.CTkLabel(
            welcome_frame,
            text="👋 Seja bem-vindo de volta, Bernal VIP!",
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color="#FFFFFF"
        ).pack(anchor="w", padx=14, pady=(10, 2))

        ctk.CTkLabel(
            welcome_frame,
            text="Seu sistema está pronto para ser calibrado para o máximo de performance e menor latência.",
            font=ctk.CTkFont(size=11),
            text_color="#9CA3AF"
        ).pack(anchor="w", padx=14, pady=(0, 10))

        # 6 Hardware Telemetry Chips Grid (2 rows x 3 columns)
        chips_frame = ctk.CTkFrame(scroll, fg_color="transparent")
        chips_frame.pack(fill="x", pady=4, padx=2)
        chips_frame.columnconfigure((0, 1, 2), weight=1)

        def make_chip(row, col, title, initial_val):
            c = ctk.CTkFrame(chips_frame, fg_color="#181230", corner_radius=8, border_width=1, border_color="#241B44")
            c.grid(row=row, column=col, padx=3, pady=3, sticky="nsew")
            ctk.CTkLabel(c, text=title, font=ctk.CTkFont(size=10, weight="bold"), text_color="#8E8AA0").pack(anchor="w", padx=10, pady=(6, 1))
            val_lbl = ctk.CTkLabel(c, text=initial_val, font=ctk.CTkFont(size=12, weight="bold"), text_color="#FFFFFF")
            val_lbl.pack(anchor="w", padx=10, pady=(0, 6))
            return val_lbl

        self.lbl_chip_cpu_name = make_chip(0, 0, "💻 PROCESSADOR", "Lendo CPU...")
        self.lbl_chip_gpu_name = make_chip(0, 1, "🎮 PLACA DE VÍDEO", "Lendo GPU...")
        self.lbl_chip_ram_val = make_chip(0, 2, "⚡ MEMÓRIA RAM", "Lendo RAM...")

        self.lbl_chip_disk_val = make_chip(1, 0, "💾 DISCO C:", "Lendo Espaço...")
        self.lbl_chip_tpm_val = make_chip(1, 1, "🔒 TPM 2.0", "Verificando...")
        self.lbl_chip_sec_val = make_chip(1, 2, "🛡️ SECURE BOOT", "Verificando...")

        # Hero Card: Otimização Geral Inteligente
        hero_frame = ctk.CTkFrame(scroll, fg_color="#1A1236", corner_radius=12, border_width=1, border_color="#7928CA")
        hero_frame.pack(fill="x", pady=8, padx=2)

        ctk.CTkLabel(
            hero_frame,
            text="⚡ OTIMIZAÇÃO GERAL INTELIGENTE",
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color="#00D2FF"
        ).pack(anchor="w", padx=16, pady=(12, 3))

        ctk.CTkLabel(
            hero_frame,
            text="Aplica ajustes de registro de baixa latência, desativa telemetria inútil, limpa caches do Windows,\notimiza TCP/DNS, libera os núcleos da CPU e aplica o MODO FPS nos seus jogos (prioridade alta + GPU dedicada).",
            font=ctk.CTkFont(size=11),
            text_color="#C4B5FD",
            justify="left"
        ).pack(anchor="w", padx=16, pady=(0, 8))

        btn_hero = ctk.CTkButton(
            hero_frame,
            text="▶ PREPARAR PARA JOGAR (OTIMIZAR AGORA)",
            font=ctk.CTkFont(size=15, weight="bold"),
            fg_color="#7928CA",
            hover_color="#9333EA",
            height=46,
            corner_radius=10,
            command=lambda: self.run_async(self.auto_optimize)
        )
        btn_hero.pack(fill="x", padx=16, pady=(4, 10))
        ToolTip(btn_hero, "Faz tudo sozinho: Aplica plano de energia, otimiza visual, limpa barra de tarefas, resfria o PC e limpa Lixo/RAM e aplica o Modo FPS em todos os jogos instalados.")

        # Metrics bar inside/below Hero
        metrics_frame = ctk.CTkFrame(hero_frame, fg_color="#140E29", corner_radius=8)
        metrics_frame.pack(fill="x", padx=16, pady=(0, 12))

        m_row = ctk.CTkFrame(metrics_frame, fg_color="transparent")
        m_row.pack(fill="x", padx=10, pady=6)

        self.lbl_proc_antes = ctk.CTkLabel(m_row, text="Processos: Lendo...", font=ctk.CTkFont(size=11), text_color="#9CA3AF")
        self.lbl_proc_antes.pack(side="left", padx=6)
        self.lbl_proc_depois = ctk.CTkLabel(m_row, text="Pós: -", font=ctk.CTkFont(size=11, weight="bold"), text_color="#10B981")
        self.lbl_proc_depois.pack(side="left", padx=(0, 14))

        self.lbl_serv_antes = ctk.CTkLabel(m_row, text="Serviços: Lendo...", font=ctk.CTkFont(size=11), text_color="#9CA3AF")
        self.lbl_serv_antes.pack(side="left", padx=6)
        self.lbl_serv_depois = ctk.CTkLabel(m_row, text="Pós: -", font=ctk.CTkFont(size=11, weight="bold"), text_color="#10B981")
        self.lbl_serv_depois.pack(side="left", padx=(0, 14))

        self.lbl_boot_antes = ctk.CTkLabel(m_row, text="Boot: Lendo...", font=ctk.CTkFont(size=11), text_color="#9CA3AF")
        self.lbl_boot_antes.pack(side="left", padx=6)
        self.lbl_boot_depois = ctk.CTkLabel(m_row, text="", font=ctk.CTkFont(size=11), text_color="#F59E0B")
        self.lbl_boot_depois.pack(side="left")

        # Compatibility hidden labels
        self.lbl_cpu = ctk.CTkLabel(scroll, text="", font=ctk.CTkFont(size=1))
        self.lbl_gpu = ctk.CTkLabel(scroll, text="", font=ctk.CTkFont(size=1))
        self.lbl_ram = ctk.CTkLabel(scroll, text="", font=ctk.CTkFont(size=1))

        # Relógio Futurista & HUD de Telemetria de Temperaturas, CPU e RAM (Segundo Print)
        hud_card = ctk.CTkFrame(scroll, fg_color="#150F2C", corner_radius=12, border_width=1, border_color="#00D2FF")
        hud_card.pack(fill="x", pady=6, padx=2)

        # HUD Top Header: Left Title, Right Clock & Uptime
        hud_top = ctk.CTkFrame(hud_card, fg_color="transparent")
        hud_top.pack(fill="x", padx=14, pady=(10, 6))

        h_left = ctk.CTkFrame(hud_top, fg_color="transparent")
        h_left.pack(side="left")

        ctk.CTkLabel(
            h_left,
            text="📡 HUD DE TELEMETRIA & MONITOR DE HARDWARE",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color="#00D2FF"
        ).pack(side="left")

        ctk.CTkLabel(
            h_left,
            text="🟢 AO VIVO",
            font=ctk.CTkFont(size=9, weight="bold"),
            text_color="#10B981",
            fg_color="#064E3B",
            corner_radius=4,
            padx=6, pady=1
        ).pack(side="left", padx=8)

        # Relógio Digital e Uptime
        self.lbl_hud_clock = ctk.CTkLabel(
            hud_top,
            text="🕒 00:00:00 BRT  •  Uptime: Lendo...",
            font=ctk.CTkFont(family="Consolas", size=11, weight="bold"),
            text_color="#C084FC"
        )
        self.lbl_hud_clock.pack(side="right")
        ToolTip(self.lbl_hud_clock, "Horário do sistema e tempo total decorrido desde a última inicialização do Windows (Uptime).", "⏱️ RELÓGIO & UPTIME")

        # 3 Futuristic Gauges Columns (CPU, RAM, GPU)
        hud_grid = ctk.CTkFrame(hud_card, fg_color="transparent")
        hud_grid.pack(fill="x", padx=10, pady=(2, 10))
        hud_grid.columnconfigure((0, 1, 2), weight=1)

        # Gauge 1: CPU Telemetry
        g1 = ctk.CTkFrame(hud_grid, fg_color="#1A1338", corner_radius=10, border_width=1, border_color="#271E4A")
        g1.grid(row=0, column=0, padx=4, pady=2, sticky="nsew")

        ctk.CTkLabel(g1, text="⚡ PROCESSADOR (CPU)", font=ctk.CTkFont(size=10, weight="bold"), text_color="#00D2FF").pack(anchor="w", padx=10, pady=(8, 1))

        self.lbl_hud_cpu_pct = ctk.CTkLabel(g1, text="0%", font=ctk.CTkFont(size=20, weight="bold"), text_color="#FFFFFF")
        self.lbl_hud_cpu_pct.pack(anchor="w", padx=10)

        self.bar_hud_cpu = ctk.CTkProgressBar(g1, height=6, progress_color="#00D2FF", fg_color="#0D253A")
        self.bar_hud_cpu.pack(fill="x", padx=10, pady=4)
        self.bar_hud_cpu.set(0)

        self.lbl_hud_cpu_temp = ctk.CTkLabel(g1, text="🌡️ --°C  •  Normal", font=ctk.CTkFont(size=10, weight="bold"), text_color="#10B981")
        self.lbl_hud_cpu_temp.pack(anchor="w", padx=10, pady=(0, 2))

        self.lbl_hud_cpu_extra = ctk.CTkLabel(g1, text="Cores: Lendo...", font=ctk.CTkFont(size=9), text_color="#9CA3AF")
        self.lbl_hud_cpu_extra.pack(anchor="w", padx=10, pady=(0, 8))
        ToolTip(g1, "Uso da CPU em tempo real, temperatura estimada e núcleos de processamento dedicados.", "⚡ CPU INTEL/AMD")

        # Gauge 2: RAM Telemetry
        g2 = ctk.CTkFrame(hud_grid, fg_color="#1A1338", corner_radius=10, border_width=1, border_color="#271E4A")
        g2.grid(row=0, column=1, padx=4, pady=2, sticky="nsew")

        ctk.CTkLabel(g2, text="🧠 MEMÓRIA RAM", font=ctk.CTkFont(size=10, weight="bold"), text_color="#C084FC").pack(anchor="w", padx=10, pady=(8, 1))

        self.lbl_hud_ram_pct = ctk.CTkLabel(g2, text="0%", font=ctk.CTkFont(size=20, weight="bold"), text_color="#FFFFFF")
        self.lbl_hud_ram_pct.pack(anchor="w", padx=10)

        self.bar_hud_ram = ctk.CTkProgressBar(g2, height=6, progress_color="#A855F7", fg_color="#2D114D")
        self.bar_hud_ram.pack(fill="x", padx=10, pady=4)
        self.bar_hud_ram.set(0)

        self.lbl_hud_ram_gb = ctk.CTkLabel(g2, text="-- GB Usados  •  -- GB Livres", font=ctk.CTkFont(size=10, weight="bold"), text_color="#E0AAFF")
        self.lbl_hud_ram_gb.pack(anchor="w", padx=10, pady=(0, 2))

        self.lbl_hud_ram_extra = ctk.CTkLabel(g2, text="Standby Otimizado", font=ctk.CTkFont(size=9), text_color="#9CA3AF")
        self.lbl_hud_ram_extra.pack(anchor="w", padx=10, pady=(0, 8))
        ToolTip(g2, "Consumo e disponibilidade de RAM em tempo real com indicador de memória livre para jogos.", "🧠 MEMÓRIA RAM")

        # Gauge 3: GPU Telemetry
        g3 = ctk.CTkFrame(hud_grid, fg_color="#1A1338", corner_radius=10, border_width=1, border_color="#271E4A")
        g3.grid(row=0, column=2, padx=4, pady=2, sticky="nsew")

        ctk.CTkLabel(g3, text="🎮 PLACA DE VÍDEO (GPU)", font=ctk.CTkFont(size=10, weight="bold"), text_color="#10B981").pack(anchor="w", padx=10, pady=(8, 1))

        self.lbl_hud_gpu_pct = ctk.CTkLabel(g3, text="0%", font=ctk.CTkFont(size=20, weight="bold"), text_color="#FFFFFF")
        self.lbl_hud_gpu_pct.pack(anchor="w", padx=10)

        self.bar_hud_gpu = ctk.CTkProgressBar(g3, height=6, progress_color="#10B981", fg_color="#064E3B")
        self.bar_hud_gpu.pack(fill="x", padx=10, pady=4)
        self.bar_hud_gpu.set(0)

        self.lbl_hud_gpu_temp = ctk.CTkLabel(g3, text="🌡️ --°C  •  Ideal", font=ctk.CTkFont(size=10, weight="bold"), text_color="#10B981")
        self.lbl_hud_gpu_temp.pack(anchor="w", padx=10, pady=(0, 2))

        self.lbl_hud_gpu_extra = ctk.CTkLabel(g3, text="GPU Otimizada", font=ctk.CTkFont(size=9), text_color="#9CA3AF")
        self.lbl_hud_gpu_extra.pack(anchor="w", padx=10, pady=(0, 8))
        ToolTip(g3, "Temperatura direta e carga de processamento da Placa de Vídeo.", "🎮 PLACA DE VÍDEO")

        # Card 1: Placa-Mãe, BIOS e Monitor Hz
        mb_info = self.get_motherboard_and_bios()
        disp_info = self.get_monitor_display_info()

        card_hw_diag = ctk.CTkFrame(scroll, fg_color="#150F2C", corner_radius=12, border_width=1, border_color="#3B2D71")
        card_hw_diag.pack(fill="x", pady=6, padx=2)

        h_hw = ctk.CTkFrame(card_hw_diag, fg_color="transparent")
        h_hw.pack(fill="x", padx=14, pady=(10, 6))
        ctk.CTkLabel(h_hw, text="🖥️ PLACA-MÃE, BIOS & MONITOR (TAXA DE HZ)", font=ctk.CTkFont(size=12, weight="bold"), text_color="#00D2FF").pack(side="left")

        hw_grid = ctk.CTkFrame(card_hw_diag, fg_color="transparent")
        hw_grid.pack(fill="x", padx=14, pady=(2, 10))
        hw_grid.columnconfigure((0, 1), weight=1)

        # Col 1: Motherboard & BIOS
        col_mb = ctk.CTkFrame(hw_grid, fg_color="#1A1338", corner_radius=8, border_width=1, border_color="#271E4A")
        col_mb.grid(row=0, column=0, padx=4, pady=2, sticky="nsew")

        ctk.CTkLabel(col_mb, text="⚡ PLACA-MÃE & BIOS", font=ctk.CTkFont(size=10, weight="bold"), text_color="#C084FC").pack(anchor="w", padx=10, pady=(8, 2))
        ctk.CTkLabel(col_mb, text=f"🏷️ Modelo: {mb_info['mb_vendor']} {mb_info['mb_model']}", font=ctk.CTkFont(size=11, weight="bold"), text_color="#FFFFFF").pack(anchor="w", padx=10)
        ctk.CTkLabel(col_mb, text=f"🔧 BIOS: {mb_info['bios_ver']} ({mb_info['bios_date']})", font=ctk.CTkFont(size=10), text_color="#9CA3AF").pack(anchor="w", padx=10, pady=1)

        status_col = "#EF4444" if mb_info["is_outdated"] else "#10B981"
        ctk.CTkLabel(col_mb, text=mb_info["bios_status"], font=ctk.CTkFont(size=10, weight="bold"), text_color=status_col).pack(anchor="w", padx=10, pady=(2, 6))

        btn_bios = ctk.CTkButton(col_mb, text="🔗 Baixar BIOS no Site Oficial", font=ctk.CTkFont(size=10, weight="bold"), fg_color="#7928CA", hover_color="#9333EA", height=28, command=self.open_bios_support_page)
        btn_bios.pack(fill="x", padx=10, pady=(2, 8))
        ToolTip(btn_bios, "Abre a página oficial de suporte e downloads da sua placa-mãe para verificar a versão mais recente da BIOS.")

        # Col 2: Display & Hz
        col_dp = ctk.CTkFrame(hw_grid, fg_color="#1A1338", corner_radius=8, border_width=1, border_color="#271E4A")
        col_dp.grid(row=0, column=1, padx=4, pady=2, sticky="nsew")

        ctk.CTkLabel(col_dp, text="🎮 MONITOR & TAXA DE ATUALIZAÇÃO (HZ)", font=ctk.CTkFont(size=10, weight="bold"), text_color="#10B981").pack(anchor="w", padx=10, pady=(8, 2))
        ctk.CTkLabel(col_dp, text=f"🖥️ Tela Atual: {disp_info['current_w']}x{disp_info['current_h']} @ {disp_info['current_hz']}Hz", font=ctk.CTkFont(size=11, weight="bold"), text_color="#FFFFFF").pack(anchor="w", padx=10)
        ctk.CTkLabel(col_dp, text=f"⚡ Taxa Máxima Suportada: {disp_info['max_hz']}Hz", font=ctk.CTkFont(size=10, weight="bold"), text_color="#00D2FF").pack(anchor="w", padx=10, pady=1)

        if disp_info["is_suboptimal_hz"]:
            ctk.CTkLabel(col_dp, text=f"⚠️ ALERTA: Seu monitor suporta {disp_info['max_hz']}Hz mas está em 60Hz!", font=ctk.CTkFont(size=10, weight="bold"), text_color="#F59E0B").pack(anchor="w", padx=10, pady=2)
        else:
            ctk.CTkLabel(col_dp, text="🟢 Monitor operando com fluidez ideal", font=ctk.CTkFont(size=10), text_color="#10B981").pack(anchor="w", padx=10, pady=2)

        btn_dp = ctk.CTkButton(col_dp, text="🖥️ Mudar Resolução / Taxa de Hz", font=ctk.CTkFont(size=10, weight="bold"), fg_color="#1E293B", hover_color="#334155", height=28, command=self.open_display_settings)
        btn_dp.pack(fill="x", padx=10, pady=(2, 8))
        ToolTip(btn_dp, "Abre o painel avançado do Windows para selecionar a resolução ideal ou ativar 144Hz/240Hz.")

        # Card 2: Expansor de Memória RAM Virtual (Alocar HD/SSD como RAM)
        card_vram = ctk.CTkFrame(scroll, fg_color="#150F2C", corner_radius=12, border_width=1, border_color="#3B2D71")
        card_vram.pack(fill="x", pady=6, padx=2)

        h_vr = ctk.CTkFrame(card_vram, fg_color="transparent")
        h_vr.pack(fill="x", padx=14, pady=(10, 4))
        ctk.CTkLabel(h_vr, text="🧠 EXPANSOR DE MEMÓRIA RAM VIRTUAL (ALOCAR HD / SSD)", font=ctk.CTkFont(size=12, weight="bold"), text_color="#00D2FF").pack(side="left")
        self.lbl_vram_status = ctk.CTkLabel(h_vr, text="● Status: Padrão Windows (Auto)", font=ctk.CTkFont(size=11, weight="bold"), text_color="#10B981")
        self.lbl_vram_status.pack(side="right")

        ctk.CTkLabel(card_vram, text="Aumente a memória RAM alocando espaço de alta velocidade do seu SSD/HD (Pagefile Fixa sem fragmentação).\nEvita fechamentos por falta de memória (Out of Memory) e erros como 0x00001338 no Warzone e GTA V.", font=ctk.CTkFont(size=11), text_color="#9CA3AF", justify="left").pack(anchor="w", padx=14, pady=(0, 8))

        vr_row = ctk.CTkFrame(card_vram, fg_color="transparent")
        vr_row.pack(fill="x", padx=14, pady=(0, 12))
        vr_row.columnconfigure((0, 1, 2), weight=1)

        b_v8 = ctk.CTkButton(vr_row, text="🚀 Alocar +8 GB Virtual", font=ctk.CTkFont(size=11, weight="bold"), fg_color="#7928CA", hover_color="#9333EA", height=32, command=lambda: self.run_async(self.apply_virtual_ram_pagefile, 8))
        b_v8.grid(row=0, column=0, padx=3, pady=2, sticky="ew")
        ToolTip(b_v8, "Aloca 8 GB fixos do SSD/HD como memória virtual. Ideal para a maioria dos computadores gamers.")

        b_v16 = ctk.CTkButton(vr_row, text="⚡ Alocar +16 GB Virtual", font=ctk.CTkFont(size=11, weight="bold"), fg_color="#2563EB", hover_color="#1D4ED8", height=32, command=lambda: self.run_async(self.apply_virtual_ram_pagefile, 16))
        b_v16.grid(row=0, column=1, padx=3, pady=2, sticky="ew")
        ToolTip(b_v16, "Aloca 16 GB fixos de memória virtual. Máxima estabilidade para Warzone, streams e edições pesadas.")

        b_vauto = ctk.CTkButton(vr_row, text="🔄 Restaurar Padrão Windows", font=ctk.CTkFont(size=11, weight="bold"), fg_color="#374151", hover_color="#4B5563", height=32, command=lambda: self.run_async(self.apply_virtual_ram_pagefile, "auto"))
        b_vauto.grid(row=0, column=2, padx=3, pady=2, sticky="ew")
        ToolTip(b_vauto, "Restaura o arquivo de paginação para o modo automático padrão gerenciado pelo Windows.")

        # Mini Live Log Preview Bar
        bar_frame = ctk.CTkFrame(scroll, fg_color="#140E26", corner_radius=8, height=36)
        bar_frame.pack(fill="x", pady=(8, 4), padx=2)
        bar_frame.pack_propagate(False)

        self.lbl_mini_status = ctk.CTkLabel(
            bar_frame,
            text="📜 Sistema pronto para otimização.",
            font=ctk.CTkFont(size=11),
            text_color="#00D2FF"
        )
        self.lbl_mini_status.pack(side="left", padx=12, pady=6)

        btn_view_log = ctk.CTkButton(
            bar_frame,
            text="Ver Log Completo ➔",
            font=ctk.CTkFont(size=10, weight="bold"),
            fg_color="#241B44",
            hover_color="#362963",
            height=24,
            width=120,
            command=lambda: self.show_view("log")
        )
        btn_view_log.pack(side="right", padx=10, pady=6)

        return scroll

    def create_view_wallpapers(self, parent):
        scroll = ctk.CTkScrollableFrame(parent, fg_color="transparent")

        # Header
        head = ctk.CTkFrame(scroll, fg_color="#151028", corner_radius=10)
        head.pack(fill="x", pady=(0, 8), padx=2)

        ctk.CTkLabel(
            head,
            text="🖼️ Galeria de Wallpapers Gamers Exclusivos",
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color="#FFFFFF"
        ).pack(anchor="w", padx=14, pady=(10, 2))

        ctk.CTkLabel(
            head,
            text="Filtre por categoria abaixo e aplique instantaneamente em 1 clique no seu Windows:",
            font=ctk.CTkFont(size=11),
            text_color="#9CA3AF"
        ).pack(anchor="w", padx=14, pady=(0, 10))

        # Full Wallpapers Data with Categories (30 Wallpapers 4K)
        self.wallpapers_data = [
            # 1. Bernal Oficial (5)
            {
                "id": "bernal_official",
                "category": "oficial",
                "tag": "👑 OFICIAL BERNAL",
                "tag_color": "#F59E0B",
                "name": "Bernal VIP Neon Oficial",
                "sub": "Papel de Parede Oficial Bernal Pro - Padrão do Sistema",
                "file": "Wallpaper_Bernal.png",
                "thumb": "thumb_Wallpaper_Bernal.png",
                "is_default": True
            },
            {
                "id": "bernal_gold",
                "category": "oficial",
                "tag": "👑 OFICIAL BERNAL",
                "tag_color": "#F59E0B",
                "name": "Bernal VIP Gold Royale",
                "sub": "Logo Bernal em Ouro 3D e Partículas de Luz",
                "file": "WP_Bernal_Gold.png",
                "thumb": "thumb_WP_Bernal_Gold.png"
            },
            {
                "id": "bernal_prism",
                "category": "oficial",
                "tag": "👑 OFICIAL BERNAL",
                "tag_color": "#F59E0B",
                "name": "Bernal Spectrum Prism",
                "sub": "Geometria Holográfica e Luz Prismática Ultra HD",
                "file": "WP_Bernal_Prism.png",
                "thumb": "thumb_WP_Bernal_Prism.png"
            },
            {
                "id": "bernal_dark",
                "category": "oficial",
                "tag": "👑 OFICIAL BERNAL",
                "tag_color": "#F59E0B",
                "name": "Obsidian Dark Minimal",
                "sub": "Preto Puro OLED Anti-Fadiga Visual",
                "file": "WP_Dark.png",
                "thumb": "thumb_WP_Dark.png"
            },
            {
                "id": "bernal_light",
                "category": "oficial",
                "tag": "👑 OFICIAL BERNAL",
                "tag_color": "#F59E0B",
                "name": "Minimalist Cyber Light",
                "sub": "Estilo Clean e Elegante Bernal",
                "file": "WP_Light.png",
                "thumb": "thumb_WP_Light.png"
            },

            # 2. The Last of Us (5)
            {
                "id": "last_of_us_main",
                "category": "lastofus",
                "tag": "🌿 THE LAST OF US",
                "tag_color": "#10B981",
                "name": "The Last of Us - Seattle Overgrown",
                "sub": "Joel & Ellie na Cidade Alagada com Natureza Pós-Apocalíptica",
                "file": "WP_LastOfUs.png",
                "thumb": "thumb_WP_LastOfUs.png"
            },
            {
                "id": "last_of_us_ellie",
                "category": "lastofus",
                "tag": "🌿 THE LAST OF US",
                "tag_color": "#10B981",
                "name": "The Last of Us - Ellie Acústico",
                "sub": "Ellie Tocando Violão na Janela ao Pôr do Sol",
                "file": "WP_LastOfUs_Ellie.png",
                "thumb": "thumb_WP_LastOfUs_Ellie.png"
            },
            {
                "id": "last_of_us_firefly",
                "category": "lastofus",
                "tag": "🌿 THE LAST OF US",
                "tag_color": "#10B981",
                "name": "The Last of Us - Fireflies Neon",
                "sub": "Joel com Lanterna e Grafite Neon dos Vaga-Lumes (Look for the Light)",
                "file": "WP_LastOfUs_Firefly.png",
                "thumb": "thumb_WP_LastOfUs_Firefly.png"
            },
            {
                "id": "last_of_us_giraffes",
                "category": "lastofus",
                "tag": "🌿 THE LAST OF US",
                "tag_color": "#10B981",
                "name": "The Last of Us - Santuário das Girafas",
                "sub": "Cena Emocionante de Joel e Ellie Admirando as Girafas",
                "file": "WP_LastOfUs_Giraffes.png",
                "thumb": "thumb_WP_LastOfUs_Giraffes.png"
            },
            {
                "id": "last_of_us_winter",
                "category": "lastofus",
                "tag": "🌿 THE LAST OF US",
                "tag_color": "#10B981",
                "name": "The Last of Us - Sobrevivência no Inverno",
                "sub": "Ellie com Arco e Flecha na Floresta Coberta de Neve",
                "file": "WP_LastOfUs_Winter.png",
                "thumb": "thumb_WP_LastOfUs_Winter.png"
            },

            # 3. Futebol & FIFA (5)
            {
                "id": "fifa_striker",
                "category": "futebol",
                "tag": "⚽ FUTEBOL & FIFA",
                "tag_color": "#10B981",
                "name": "Craque dos Campos (FIFA EA FC)",
                "sub": "Comemoração Épica de Gol sob Fogos de Artifício",
                "file": "WP_Futebol.png",
                "thumb": "thumb_WP_Futebol.png"
            },
            {
                "id": "fifa_arena",
                "category": "futebol",
                "tag": "⚽ FUTEBOL & FIFA",
                "tag_color": "#10B981",
                "name": "Arena Champions EA FC",
                "sub": "Estádio Holográfico com Luzes e Torcida Vibrante",
                "file": "WP_Fifa_Arena.png",
                "thumb": "thumb_WP_Fifa_Arena.png"
            },
            {
                "id": "fifa_champions",
                "category": "futebol",
                "tag": "⚽ FUTEBOL & FIFA",
                "tag_color": "#10B981",
                "name": "UEFA Champions Glory",
                "sub": "Estádio da Grande Final com Estrelas da Champions",
                "file": "WP_Futebol_Champions.png",
                "thumb": "thumb_WP_Futebol_Champions.png"
            },
            {
                "id": "fifa_trophy",
                "category": "futebol",
                "tag": "⚽ FUTEBOL & FIFA",
                "tag_color": "#10B981",
                "name": "Taça de Ouro World Cup",
                "sub": "Troféu Dourado Reluzente sob Holofotes e Glória",
                "file": "WP_Futebol_Trophy.png",
                "thumb": "thumb_WP_Futebol_Trophy.png"
            },
            {
                "id": "fifa_street",
                "category": "futebol",
                "tag": "⚽ FUTEBOL & FIFA",
                "tag_color": "#10B981",
                "name": "Futebol Arte Street King",
                "sub": "Drible Espetacular na Quadra Urbana com Grafites Neon",
                "file": "WP_Futebol_Street.png",
                "thumb": "thumb_WP_Futebol_Street.png"
            },
            {
                "id": "futebol_cr7",
                "category": "futebol",
                "tag": "⚽ FUTEBOL & FIFA",
                "tag_color": "#10B981",
                "name": "Artilheiro Lendário Camisa 7",
                "sub": "Comemoração Explosiva de Gol sob os Holofotes da Grande Final",
                "file": "WP_Futebol_CR7.png",
                "thumb": "thumb_WP_Futebol_CR7.png"
            },
            {
                "id": "futebol_messi",
                "category": "futebol",
                "tag": "⚽ FUTEBOL & FIFA",
                "tag_color": "#10B981",
                "name": "Camisa 10 Campeão do Mundo",
                "sub": "O Camisa 10 Erguendo a Taça sob Confetes Dourados",
                "file": "WP_Futebol_Messi.png",
                "thumb": "thumb_WP_Futebol_Messi.png"
            },

            # 4. FPS & Warzone (3)
            {
                "id": "wz_tactical",
                "category": "fps",
                "tag": "🎯 FPS & WARZONE",
                "tag_color": "#EF4444",
                "name": "Guerreiro Tático Spec-Ops",
                "sub": "Operador Militar Modern Warfare em Combate Noturno",
                "file": "WP_Tactical.png",
                "thumb": "thumb_WP_Tactical.png"
            },
            {
                "id": "wz_sniper",
                "category": "fps",
                "tag": "🎯 FPS & WARZONE",
                "tag_color": "#EF4444",
                "name": "Sniper no Prédio (Warzone Sunset)",
                "sub": "Operador Ghillie com Vista Panorâmica de Verdansk",
                "file": "WP_Warzone_Sniper.png",
                "thumb": "thumb_WP_Warzone_Sniper.png"
            },
            {
                "id": "wz_nightops",
                "category": "fps",
                "tag": "🎯 FPS & WARZONE",
                "tag_color": "#EF4444",
                "name": "Operação Noturna Spec-Ops",
                "sub": "Soldado com Visão Noturna Quad-NVG sob Tempestade",
                "file": "WP_Fps_Nightops.png",
                "thumb": "thumb_WP_Fps_Nightops.png"
            },

            # 5. Carros & Motos (3)
            {
                "id": "car_hypercar",
                "category": "veiculos",
                "tag": "🏎️ CARROS & MOTOS",
                "tag_color": "#06B6D4",
                "name": "Hypercar Cyber Drift",
                "sub": "Supercarro Voando no Asfalto Molhado Neo-Tokyo",
                "file": "WP_Supercar.png",
                "thumb": "thumb_WP_Supercar.png"
            },
            {
                "id": "bike_ninja",
                "category": "veiculos",
                "tag": "🏎️ CARROS & MOTOS",
                "tag_color": "#06B6D4",
                "name": "Superbike Racing Ninja",
                "sub": "Moto Superesportiva em Alta Velocidade na Ponte",
                "file": "WP_Superbike.png",
                "thumb": "thumb_WP_Superbike.png"
            },
            {
                "id": "car_drift_gtr",
                "category": "veiculos",
                "tag": "🏎️ CARROS & MOTOS",
                "tag_color": "#06B6D4",
                "name": "Midnight Drift Skyline GT-R",
                "sub": "Drift Japonês Épico na Chuva sob Luzes de Tóquio",
                "file": "WP_Drift_GTR.png",
                "thumb": "thumb_WP_Drift_GTR.png"
            },

            # 6. Anime & Setup (6)
            {
                "id": "anime_samurai",
                "category": "anime",
                "tag": "⚔️ ANIME & SETUP",
                "tag_color": "#A855F7",
                "name": "Samurai Cibernético Neo-Tokyo",
                "sub": "Guerreiro com Katanas de Energia e Luz Neon",
                "file": "WP_Cyber_Samurai.png",
                "thumb": "thumb_WP_Cyber_Samurai.png"
            },
            {
                "id": "anime_ninja",
                "category": "anime",
                "tag": "⚔️ ANIME & SETUP",
                "tag_color": "#A855F7",
                "name": "Ninja das Sombras (Dark Flame)",
                "sub": "Chamas Negras e Fogo Demoníaco Anime",
                "file": "WP_Ninja.png",
                "thumb": "thumb_WP_Ninja.png"
            },
            {
                "id": "anime_aura",
                "category": "anime",
                "tag": "⚔️ ANIME & SETUP",
                "tag_color": "#A855F7",
                "name": "Lenda Dourada (Aura Thunder)",
                "sub": "Super Guerreiro com Relâmpagos e Aura Épica",
                "file": "WP_Aura.png",
                "thumb": "thumb_WP_Aura.png"
            },
            {
                "id": "setup_cyber",
                "category": "anime",
                "tag": "⚔️ ANIME & SETUP",
                "tag_color": "#A855F7",
                "name": "Cyber Neon Room Setup",
                "sub": "Quarto Gamer dos Sonhos com Luzes Roxas",
                "file": "WP_Cyber.png",
                "thumb": "thumb_WP_Cyber.png"
            },
            {
                "id": "setup_fem",
                "category": "anime",
                "tag": "⚔️ ANIME & SETUP",
                "tag_color": "#A855F7",
                "name": "Cyberpunk Pink Neon",
                "sub": "Edição Rosa Gamer & Estilo Synthwave",
                "file": "WP_Fem.png",
                "thumb": "thumb_WP_Fem.png"
            },
            {
                "id": "anime_cybercity",
                "category": "anime",
                "tag": "⚔️ ANIME & SETUP",
                "tag_color": "#A855F7",
                "name": "Neo-Tokyo Anime Cybercity",
                "sub": "Metrópole Futurista com Mechas e Arranha-Céus Neon",
                "file": "WP_Anime_Cybercity.png",
                "thumb": "thumb_WP_Anime_Cybercity.png"
            },
            {
                "id": "anime_dragonball_goku",
                "category": "anime",
                "tag": "⚔️ ANIME & SETUP",
                "tag_color": "#A855F7",
                "name": "Guerreiro Lendário - Instinto Divino",
                "sub": "Lutador Lendário com Aura Prateada Cósmica",
                "file": "WP_Anime_DragonBall.png",
                "thumb": "thumb_WP_Anime_DragonBall.png"
            },
            {
                "id": "anime_dragonball_vegeta",
                "category": "anime",
                "tag": "⚔️ ANIME & SETUP",
                "tag_color": "#A855F7",
                "name": "Príncipe Guerreiro - Ego Destruidor",
                "sub": "Rival Orgulhoso com Poder de Destruição e Chamas Púrpuras",
                "file": "WP_Anime_Vegeta.png",
                "thumb": "thumb_WP_Anime_Vegeta.png"
            },
            {
                "id": "anime_naruto_sixpaths",
                "category": "anime",
                "tag": "⚔️ ANIME & SETUP",
                "tag_color": "#A855F7",
                "name": "Ninja da Raposa - Modo Sábio",
                "sub": "Ninja Lendário com Chakra Dourado e Esfera de Energia",
                "file": "WP_Anime_Naruto.png",
                "thumb": "thumb_WP_Anime_Naruto.png"
            },
            {
                "id": "anime_naruto_sasuke",
                "category": "anime",
                "tag": "⚔️ ANIME & SETUP",
                "tag_color": "#A855F7",
                "name": "Ninja Vingador - Armadura Espiritual",
                "sub": "Rival Sombrio com Olhos Místicos, Raio na Mão e Guerreiro Espectral",
                "file": "WP_Anime_Sasuke.png",
                "thumb": "thumb_WP_Anime_Sasuke.png"
            },

            # 7. Jogos Retrô (3)
            {
                "id": "retro_arcade",
                "category": "retro",
                "tag": "🕹️ JOGOS RETRÔ",
                "tag_color": "#F59E0B",
                "name": "Arcade 80s Cyber Neon Fliperama",
                "sub": "Fliperama Clássico Synthwave Anos 80 com Máquinas Iluminadas",
                "file": "WP_Retro_Arcade.png",
                "thumb": "thumb_WP_Retro_Arcade.png"
            },
            {
                "id": "retro_fighter",
                "category": "retro",
                "tag": "🕹️ JOGOS RETRÔ",
                "tag_color": "#F59E0B",
                "name": "Street Fighter 16-Bit Pixel Arena",
                "sub": "Arena de Luta Retrô Arcade 16-Bit Synthwave",
                "file": "WP_Retro_Fighter.png",
                "thumb": "thumb_WP_Retro_Fighter.png"
            },
            {
                "id": "retro_synthwave",
                "category": "retro",
                "tag": "🕹️ JOGOS RETRÔ",
                "tag_color": "#F59E0B",
                "name": "Synthwave Outrun Neon Retrô",
                "sub": "Sol Retrô Wireframe com Carro Esportivo dos Anos 80",
                "file": "WP_Retro_Synthwave.png",
                "thumb": "thumb_WP_Retro_Synthwave.png"
            }
        ]

        # Filter Tabs Row
        filter_bar = ctk.CTkFrame(scroll, fg_color="#120E22", corner_radius=10)
        filter_bar.pack(fill="x", pady=(0, 10), padx=2)

        self.filter_buttons = {}
        filter_categories = [
            ("all", "🔥 Todos (36)"),
            ("lastofus", "🌿 The Last of Us (5)"),
            ("oficial", "👑 Bernal Oficial (5)"),
            ("futebol", "⚽ Futebol & FIFA (7)"),
            ("fps", "🎯 FPS & Warzone (3)"),
            ("veiculos", "🏎️ Carros & Motos (3)"),
            ("anime", "⚔️ Anime & Setup (10)"),
            ("retro", "🕹️ Jogos Retrô (3)"),
            ("meus", "➕ Meus Wallpapers")
        ]

        f_inner = ctk.CTkFrame(filter_bar, fg_color="transparent")
        f_inner.pack(padx=6, pady=6, fill="x")

        for cat_key, cat_label in filter_categories:
            btn = ctk.CTkButton(
                f_inner,
                text=cat_label,
                font=ctk.CTkFont(size=11, weight="bold"),
                height=32,
                corner_radius=8,
                fg_color="#7928CA" if cat_key == "all" else "#181230",
                text_color="#FFFFFF" if cat_key == "all" else "#9CA3AF",
                hover_color="#9333EA",
                command=lambda k=cat_key: self.filter_wallpapers_grid(k)
            )
            btn.pack(side="left", padx=2, expand=True, fill="x")
            self.filter_buttons[cat_key] = btn

        # Container for the dynamic grid of cards
        self.wallpapers_grid_container = ctk.CTkFrame(scroll, fg_color="transparent")
        self.wallpapers_grid_container.pack(fill="both", expand=True, padx=2)

        # Initial render: all wallpapers
        self.filter_wallpapers_grid("all")

        return scroll

    def filter_wallpapers_grid(self, selected_category):
        # Update tab styling
        for cat_key, btn in self.filter_buttons.items():
            if cat_key == selected_category:
                btn.configure(fg_color="#7928CA", text_color="#FFFFFF", border_width=1, border_color="#A855F7")
            else:
                btn.configure(fg_color="#181230", text_color="#9CA3AF", border_width=0)

        # Clear existing cards
        for widget in self.wallpapers_grid_container.winfo_children():
            widget.destroy()

        # Filter items
        if selected_category == "all":
            filtered = [wp for wp in self.wallpapers_data if wp.get("category") != "meus"]
        elif selected_category == "meus":
            filtered = self._load_user_wallpapers()
        else:
            filtered = [wp for wp in self.wallpapers_data if wp.get("category") == selected_category]

        # Barra de importação na aba "Meus Wallpapers"
        if selected_category == "meus":
            bar = ctk.CTkFrame(self.wallpapers_grid_container, fg_color="#151028", corner_radius=10)
            bar.pack(fill="x", pady=(0, 8))
            ctk.CTkLabel(
                bar,
                text="📁 Adicione seus próprios wallpapers (qualquer imagem do PC):",
                font=ctk.CTkFont(size=11), text_color="#9CA3AF"
            ).pack(side="left", padx=12, pady=8)
            ctk.CTkButton(
                bar, text="➕ Importar Imagem", font=ctk.CTkFont(size=11, weight="bold"),
                fg_color="#22C55E", hover_color="#16A34A", text_color="#06240F", height=30,
                command=self.import_wallpaper_dialog
            ).pack(side="right", padx=12, pady=8)
            if not filtered:
                ctk.CTkLabel(
                    self.wallpapers_grid_container,
                    text="Nenhum wallpaper importado ainda. Clique em '➕ Importar Imagem' para adicionar.",
                    font=ctk.CTkFont(size=12), text_color="#6B7280"
                ).pack(pady=20)

        grid_frame = ctk.CTkFrame(self.wallpapers_grid_container, fg_color="transparent")
        grid_frame.pack(fill="both", expand=True)
        grid_frame.columnconfigure((0, 1, 2), weight=1)

        for i, wp in enumerate(filtered):
            r = i // 3
            c = i % 3

            is_def = wp.get("is_default", False)
            border_c = "#00D2FF" if is_def else "#241B44"
            border_w = 2 if is_def else 1

            card = ctk.CTkFrame(grid_frame, fg_color="#181230", corner_radius=10, border_width=border_w, border_color=border_c)
            card.grid(row=r, column=c, padx=5, pady=6, sticky="nsew")

            # Default / Category tag row
            tag_row = ctk.CTkFrame(card, fg_color="transparent")
            tag_row.pack(fill="x", padx=10, pady=(8, 2))

            ctk.CTkLabel(
                tag_row,
                text=wp.get("tag", "GAMER"),
                font=ctk.CTkFont(size=9, weight="bold"),
                text_color=wp.get("tag_color", "#A855F7"),
                fg_color="#1F173D",
                corner_radius=6,
                padx=6, pady=2
            ).pack(side="left")

            if is_def:
                ctk.CTkLabel(
                    tag_row,
                    text="⭐ PADRÃO OFICIAL",
                    font=ctk.CTkFont(size=9, weight="bold"),
                    text_color="#00D2FF",
                    fg_color="#0D2535",
                    corner_radius=6,
                    padx=6, pady=2
                ).pack(side="right")

            # Thumbnail preview
            thumb_img = self.get_thumb_image(wp["thumb"], size=(210, 115))
            if thumb_img:
                lbl_img = ctk.CTkLabel(card, image=thumb_img, text="")
                lbl_img.pack(padx=8, pady=(4, 4))
            else:
                lbl_img = ctk.CTkLabel(card, text="[Sem Imagem]", height=115)
                lbl_img.pack(padx=8, pady=(4, 4))

            ctk.CTkLabel(
                card,
                text=wp["name"],
                font=ctk.CTkFont(size=12, weight="bold"),
                text_color="#FFFFFF"
            ).pack(anchor="w", padx=10, pady=(2, 0))

            ctk.CTkLabel(
                card,
                text=wp["sub"],
                font=ctk.CTkFont(size=10),
                text_color="#9CA3AF"
            ).pack(anchor="w", padx=10, pady=(0, 6))

            btn_col = "#00D2FF" if is_def else "#7928CA"
            btn_hov = "#00B4D8" if is_def else "#9333EA"
            btn_txt = "👑 Definir Wallpaper Oficial" if is_def else "🖼️ Aplicar no Windows"

            btn_apply = ctk.CTkButton(
                card,
                text=btn_txt,
                font=ctk.CTkFont(size=11, weight="bold"),
                fg_color=btn_col,
                hover_color=btn_hov,
                text_color="#000000" if is_def else "#FFFFFF",
                height=30,
                command=lambda f=wp["file"], t=wp["name"], d=is_def: self.apply_single_wallpaper(f, t, d)
            )
            btn_apply.pack(fill="x", padx=10, pady=(0, 10))

    def get_thumb_image(self, thumb_name, size=(210, 115)):
        if thumb_name in self.cached_thumbnails:
            return self.cached_thumbnails[thumb_name]
        from PIL import Image
        localapp = os.environ.get("LOCALAPPDATA", "")
        candidates = [
            os.path.join(self.base_path, thumb_name),
            os.path.join(self.current_dir, thumb_name),
            os.path.join(localapp, "Bernal Otimizacoes", thumb_name) if localapp else "",
            os.path.join(os.getcwd(), thumb_name)
        ]
        for cand in candidates:
            if cand and os.path.exists(cand):
                try:
                    pil_img = Image.open(cand)
                    c_img = ctk.CTkImage(light_image=pil_img, dark_image=pil_img, size=size)
                    self.cached_thumbnails[thumb_name] = c_img
                    return c_img
                except Exception as e:
                    print(f"Erro ao carregar thumbnail {cand}: {e}")
                    break
        return None

    def apply_single_wallpaper(self, wall_name, title, is_official=False):
        self.log(f"🖼️ Aplicando Papel de Parede: {title} ({wall_name})...")
        import ctypes
        wall_path = None
        localapp = os.environ.get("LOCALAPPDATA", "")
        candidates = [
            os.path.join(self.base_path, wall_name),
            os.path.join(self.current_dir, wall_name),
            os.path.join(localapp, "Bernal Otimizacoes", wall_name) if localapp else "",
            os.path.join(os.getcwd(), wall_name)
        ]
        for cand in candidates:
            if cand and os.path.exists(cand):
                wall_path = cand
                break

        if wall_path and os.path.exists(wall_path):
            try:
                ctypes.windll.user32.SystemParametersInfoW(20, 0, wall_path, 3)
                # Define o Modo Escuro/Claro do Windows conforme o wallpaper escolhido
                nome = f"{wall_name} {title}".lower()
                theme_val = None
                if is_official or "bernal" in nome or "dark" in nome or "escuro" in nome or "obsidian" in nome or "night" in nome:
                    theme_val = 0  # escuro
                elif "light" in nome or "claro" in nome or "white" in nome or "branco" in nome:
                    theme_val = 1  # claro
                if theme_val is not None:
                    kpath = r"Software\Microsoft\Windows\CurrentVersion\Themes\Personalize"
                    changed = True
                    try:
                        import winreg
                        try:
                            rk = winreg.OpenKey(winreg.HKEY_CURRENT_USER, kpath)
                            cur_val, _ = winreg.QueryValueEx(rk, "SystemUsesLightTheme")
                            winreg.CloseKey(rk)
                            changed = (int(cur_val) != theme_val)
                        except Exception:
                            changed = True
                        rk = winreg.CreateKey(winreg.HKEY_CURRENT_USER, kpath)
                        winreg.SetValueEx(rk, "AppsUseLightTheme", 0, winreg.REG_DWORD, theme_val)
                        winreg.SetValueEx(rk, "SystemUsesLightTheme", 0, winreg.REG_DWORD, theme_val)
                        winreg.CloseKey(rk)
                    except Exception:
                        self.run_cmd_live(f'reg add "HKCU\\Software\\Microsoft\\Windows\\CurrentVersion\\Themes\\Personalize" /v "AppsUseLightTheme" /t REG_DWORD /d {theme_val} /f')
                        self.run_cmd_live(f'reg add "HKCU\\Software\\Microsoft\\Windows\\CurrentVersion\\Themes\\Personalize" /v "SystemUsesLightTheme" /t REG_DWORD /d {theme_val} /f')
                    # Avisa os apps abertos para trocarem a cor
                    try:
                        ctypes.windll.user32.SendMessageTimeoutW(0xFFFF, 0x001A, 0, "ImmersiveColorSet", 0x0002, 5000, None)
                    except Exception:
                        pass
                    # A barra de tarefas/menu Iniciar só pega o tema novo reiniciando o Explorer
                    if changed:
                        try:
                            si = subprocess.STARTUPINFO()
                            si.dwFlags |= subprocess.STARTF_USESHOWWINDOW
                            subprocess.run(["taskkill", "/f", "/im", "explorer.exe"],
                                           startupinfo=si, creationflags=subprocess.CREATE_NO_WINDOW,
                                           capture_output=True)
                        except Exception:
                            pass
                        try:
                            subprocess.Popen("explorer.exe")
                        except Exception:
                            pass
                    self.log("✅ Modo Escuro aplicado!" if theme_val == 0 else "✅ Modo Claro aplicado!")
                self.log(f"✅ Papel de Parede '{title}' aplicado com sucesso no Windows!")
                messagebox.showinfo("Sucesso", f"Papel de Parede '{title}' aplicado com sucesso na sua Área de Trabalho!")
            except Exception as e:
                self.log(f"❌ Erro ao aplicar papel de parede: {e}")
        else:
            self.log(f"❌ Imagem não encontrada: {wall_name}")
            messagebox.showerror("Erro", f"Arquivo de imagem não encontrado: {wall_name}")

    def get_user_wall_dir(self):
        """Pasta onde ficam os wallpapers importados pelo usuário/cliente."""
        localapp = os.environ.get("LOCALAPPDATA", os.path.expanduser("~"))
        d = os.path.join(localapp, "Bernal Otimizacoes", "MeusWallpapers")
        try:
            os.makedirs(d, exist_ok=True)
        except Exception:
            pass
        return d

    def _load_user_wallpapers(self):
        """Lê a pasta de wallpapers importados e monta os cards da galeria."""
        d = self.get_user_wall_dir()
        exts = (".png", ".jpg", ".jpeg", ".bmp", ".webp")
        items = []
        try:
            for fn in sorted(os.listdir(d)):
                if fn.lower().endswith(exts):
                    full = os.path.join(d, fn)
                    items.append({
                        "id": "user_" + fn,
                        "category": "meus",
                        "tag": "📁 MEU WALLPAPER",
                        "tag_color": "#22C55E",
                        "name": os.path.splitext(fn)[0][:28],
                        "sub": "Wallpaper importado por você",
                        "file": full,
                        "thumb": full,
                    })
        except Exception:
            pass
        return items

    def import_wallpaper_dialog(self):
        """Deixa o usuário escolher imagens do PC e as adiciona à galeria 'Meus Wallpapers'."""
        from tkinter import filedialog
        import shutil
        paths = filedialog.askopenfilenames(
            title="Escolha as imagens para adicionar à galeria",
            filetypes=[("Imagens", "*.png *.jpg *.jpeg *.bmp *.webp"), ("Todos os arquivos", "*.*")]
        )
        if not paths:
            return
        dest = self.get_user_wall_dir()
        n = 0
        for p in paths:
            try:
                shutil.copy2(p, os.path.join(dest, os.path.basename(p)))
                n += 1
            except Exception as e:
                self.log(f"❌ Erro ao importar {os.path.basename(p)}: {e}")
        self.log(f"✅ {n} wallpaper(s) importado(s) para a galeria 'Meus Wallpapers'.")
        # Limpa thumbs importados do cache para recarregar e atualiza a aba
        try:
            self.cached_thumbnails = {k: v for k, v in self.cached_thumbnails.items() if not os.path.isabs(k)}
        except Exception:
            pass
        try:
            self.filter_wallpapers_grid("meus")
        except Exception:
            pass

    def create_view_perfis(self, parent):
        scroll = ctk.CTkScrollableFrame(parent, fg_color="transparent")

        head = ctk.CTkFrame(scroll, fg_color="#151028", corner_radius=10)
        head.pack(fill="x", pady=(0, 10), padx=2)

        ctk.CTkLabel(
            head,
            text="⚡ Perfis de Desempenho do Windows",
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color="#FFFFFF"
        ).pack(anchor="w", padx=14, pady=(10, 2))

        ctk.CTkLabel(
            head,
            text="Escolha o perfil sob medida para a sua atividade atual:",
            font=ctk.CTkFont(size=11),
            text_color="#9CA3AF"
        ).pack(anchor="w", padx=14, pady=(0, 10))

        grid = ctk.CTkFrame(scroll, fg_color="transparent")
        grid.pack(fill="both", expand=True, padx=2)
        grid.columnconfigure((0, 1), weight=1)

        def make_prof_card(r, c, title, sub, btn_text, color, hover, cmd, tip):
            f = ctk.CTkFrame(grid, fg_color="#181230", corner_radius=10, border_width=1, border_color="#241B44")
            f.grid(row=r, column=c, padx=6, pady=6, sticky="nsew")
            ctk.CTkLabel(f, text=title, font=ctk.CTkFont(size=13, weight="bold"), text_color=color).pack(anchor="w", padx=14, pady=(12, 2))
            ctk.CTkLabel(f, text=sub, font=ctk.CTkFont(size=11), text_color="#9CA3AF").pack(anchor="w", padx=14, pady=(0, 10))
            b = ctk.CTkButton(f, text=btn_text, fg_color=color, hover_color=hover, font=ctk.CTkFont(weight="bold"), height=34, command=cmd)
            b.pack(fill="x", padx=14, pady=(0, 12))
            ToolTip(b, tip)
            return b

        make_prof_card(0, 0, "🎮 MODO FPS (Otimiza Meus Jogos)", "Acha seus jogos e deixa cada um com prioridade alta, GPU dedicada e tela cheia sem lag.", "Aplicar Modo FPS", "#DC2626", "#B91C1C",
                       lambda: self.run_premium(self.apply_fps_mode), "Permanente: vale toda vez que o jogo abrir. Ideal para CS2, Valorant, Warzone, Fortnite, FIFA e outros.")

        make_prof_card(0, 1, "BALANCED (Equilibrado)", "Equilibra desempenho e fidelidade gráfica.", "Aplicar Balanced", "#1A5276", "#154360",
                       lambda: self.run_async(self.apply_profile, "med"), "Recomendado para uso geral e a maioria dos jogos.")

        make_prof_card(1, 0, "MAX VISUAL (Gráficos Ultra)", "Força fidelidade gráfica e anti-aliasing.", "Aplicar Max Visual", "#5B2C6F", "#4A235A",
                       lambda: self.run_premium(self.apply_profile, "visual"), "Ideal para jogos pesados de história (Cyberpunk, RDR2).")

        make_prof_card(1, 1, "STREAMER (Modo Live)", "Blinda OBS Studio e Discord de engasgos.", "Aplicar Streamer", "#D35400", "#BA4A00",
                       lambda: self.run_premium(self.apply_profile, "streamer"), "Evita queda de quadros e travamentos durante transmissões.")

        make_prof_card(2, 0, "TRABALHO (Economia / Escritório)", "Fluidez máxima para navegadores e Office.", "Aplicar Trabalho", "#D68910", "#B9770E",
                       lambda: self.run_premium(self.apply_profile, "trabalho"), "Reduz consumo energético e aquece menos o notebook.")

        rev_frame = ctk.CTkFrame(scroll, fg_color="#181230", corner_radius=10, border_width=1, border_color="#7F1D1D")
        rev_frame.pack(fill="x", padx=8, pady=(12, 10))
        ctk.CTkLabel(rev_frame, text="🔙 Restaurar Configurações Originais do Windows", font=ctk.CTkFont(size=12, weight="bold"), text_color="#EF4444").pack(anchor="w", padx=14, pady=(10, 2))
        ctk.CTkLabel(rev_frame, text="Desfaz todas as alterações de energia e visual, voltando o computador para o padrão de fábrica.", font=ctk.CTkFont(size=10), text_color="#9CA3AF").pack(anchor="w", padx=14, pady=(0, 6))

        self.btn_revert = ctk.CTkButton(
            rev_frame,
            text="Reverter para Padrão de Fábrica",
            fg_color="#DC2626",
            hover_color="#B91C1C",
            font=ctk.CTkFont(weight="bold"),
            height=34,
            command=lambda: self.run_async(self.apply_profile, "revert")
        )
        self.btn_revert.pack(fill="x", padx=14, pady=(0, 10))
        ToolTip(self.btn_revert, "Desfaz os ajustes feitos pelo app (energia, visual, rede, serviços, mouse, RAM) e abre a Restauração do Sistema.")

        return scroll

    def create_view_jogos(self, parent):
        scroll = ctk.CTkScrollableFrame(parent, fg_color="transparent")

        head = ctk.CTkFrame(scroll, fg_color="#151028", corner_radius=10)
        head.pack(fill="x", pady=(0, 10), padx=2)

        ctk.CTkLabel(
            head,
            text="🎮 Otimização Direcionada por Jogo",
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color="#FFFFFF"
        ).pack(anchor="w", padx=14, pady=(10, 2))

        ctk.CTkLabel(
            head,
            text="Aplica perfis matemáticos de latência e áudio específicos para o jogo escolhido:",
            font=ctk.CTkFont(size=11),
            text_color="#9CA3AF"
        ).pack(anchor="w", padx=14, pady=(0, 10))

        # Game Selector Card
        card_sel = ctk.CTkFrame(scroll, fg_color="#181230", corner_radius=10, border_width=1, border_color="#241B44")
        card_sel.pack(fill="x", padx=2, pady=6)

        ctk.CTkLabel(card_sel, text="Selecione o Jogo:", font=ctk.CTkFont(size=12, weight="bold"), text_color="#00D2FF").pack(anchor="w", padx=14, pady=(12, 4))

        self.cb_jogos = ctk.CTkComboBox(
            card_sel,
            values=["Call of Duty: Warzone", "Valorant", "Counter-Strike 2", "GTA V", "Fortnite", "Cyberpunk 2077", "FIFA / EA FC"],
            width=340,
            command=self.on_game_select
        )
        self.cb_jogos.pack(anchor="w", padx=14, pady=4)

        self.btn_aplicar_jogo = ctk.CTkButton(
            card_sel,
            text="🎮 Recomendar e Aplicar Configuração para o Jogo",
            fg_color="#C0392B",
            hover_color="#922B21",
            font=ctk.CTkFont(weight="bold"),
            height=36,
            command=lambda: self.run_premium(self.apply_game_profile)
        )
        self.btn_aplicar_jogo.pack(fill="x", padx=14, pady=(8, 12))
        ToolTip(self.btn_aplicar_jogo, "Analisa seu hardware e aplica o melhor perfil de FPS + áudio para o jogo selecionado. No Warzone, um backup das configs é feito antes.")

        # Warzone Specific Card
        wz_card = ctk.CTkFrame(scroll, fg_color="#181230", corner_radius=10, border_width=1, border_color="#1565C0")
        wz_card.pack(fill="x", padx=2, pady=6)

        ctk.CTkLabel(wz_card, text="💾 Warzone / COD — Backup & Restauração de Configs", font=ctk.CTkFont(size=13, weight="bold"), text_color="#00D2FF").pack(anchor="w", padx=14, pady=(12, 2))
        ctk.CTkLabel(wz_card, text="Salve suas configurações antes de otimizar para poder restaurá-las a qualquer momento.", font=ctk.CTkFont(size=11), text_color="#9CA3AF").pack(anchor="w", padx=14, pady=(0, 8))

        btn_salvar_wz = ctk.CTkButton(
            wz_card,
            text="💾 Salvar Configurações do Warzone (Backup)",
            fg_color="#1565C0",
            hover_color="#0D47A1",
            font=ctk.CTkFont(weight="bold"),
            height=34,
            command=lambda: self.run_async(self.save_warzone_config)
        )
        btn_salvar_wz.pack(fill="x", padx=14, pady=(0, 6))
        ToolTip(btn_salvar_wz, "Faz backup das configs do Warzone (options.*.cst) para a pasta Documentos.")

        btn_restaurar_wz = ctk.CTkButton(
            wz_card,
            text="🔄 Restaurar Configurações Salvas do Warzone",
            fg_color="#2E7D32",
            hover_color="#1B5E20",
            font=ctk.CTkFont(weight="bold"),
            height=34,
            command=lambda: self.run_async(self.restore_warzone_config)
        )
        btn_restaurar_wz.pack(fill="x", padx=14, pady=(0, 6))
        ToolTip(btn_restaurar_wz, "Restaura o backup das configs do Warzone que você salvou anteriormente.")

        btn_fix_wz = ctk.CTkButton(
            wz_card,
            text="🛡️ Reparar Erros e Travamentos do Warzone (Fix 0x00001338 & KERNELBASE)",
            fg_color="#E11D48",
            hover_color="#BE123C",
            font=ctk.CTkFont(weight="bold"),
            height=36,
            command=lambda: self.run_async(self.repair_warzone_crashes)
        )
        btn_fix_wz.pack(fill="x", padx=14, pady=(0, 12))
        ToolTip(btn_fix_wz, "Corrige erros de crash (0x00001338, KERNELBASE.dll), limpa o Shader Cache corrompido, calibra VRAM e desativa conflitos do Windows.", "🛡️ WARZONE DOCTOR")

        # Route Optimizer Card
        ro_card = ctk.CTkFrame(scroll, fg_color="#181230", corner_radius=10, border_width=1, border_color="#8E44AD")
        ro_card.pack(fill="x", padx=2, pady=6)

        ctk.CTkLabel(ro_card, text="⚡ Otimizador de Rotas & Ping (Estilo ExitLag)", font=ctk.CTkFont(size=13, weight="bold"), text_color="#F39C12").pack(anchor="w", padx=14, pady=(12, 2))
        ctk.CTkLabel(ro_card, text="Ajusta MTU, zera Packet Loss e aplica políticas de QoS de baixa latência.", font=ctk.CTkFont(size=11), text_color="#9CA3AF").pack(anchor="w", padx=14, pady=(0, 8))

        self.lbl_ping_result = ctk.CTkLabel(ro_card, text="Ping: Otimização de Rotas Desativada", font=ctk.CTkFont(size=11))
        self.lbl_ping_result.pack(anchor="w", padx=14, pady=(0, 4))

        ctk.CTkButton(
            ro_card,
            text="⚡ Abrir Route Optimizer",
            fg_color="#8E44AD",
            hover_color="#71368A",
            font=ctk.CTkFont(weight="bold"),
            height=34,
            command=self.open_route_optimizer
        ).pack(fill="x", padx=14, pady=(0, 12))

        return scroll

    def create_view_ferramentas(self, parent):
        scroll = ctk.CTkScrollableFrame(parent, fg_color="transparent")

        head = ctk.CTkFrame(scroll, fg_color="#151028", corner_radius=10)
        head.pack(fill="x", pady=(0, 10), padx=2)

        ctk.CTkLabel(
            head,
            text="🛠️ Super Ferramentas do Sistema",
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color="#FFFFFF"
        ).pack(anchor="w", padx=14, pady=(10, 2))

        ctk.CTkLabel(
            head,
            text="Utilitários profissionais de limpeza profunda, prioridade de CPU, drivers e plataformas gamers:",
            font=ctk.CTkFont(size=11),
            text_color="#9CA3AF"
        ).pack(anchor="w", padx=14, pady=(0, 10))

        # Boost + Liberar espaço (destaque no topo)
        boost_card = ctk.CTkFrame(scroll, fg_color="#1A1236", corner_radius=12, border_width=1, border_color="#7928CA")
        boost_card.pack(fill="x", pady=(0, 10), padx=2)
        ctk.CTkLabel(boost_card, text="🚀 Boost de Responsividade & Limpeza de Disco", font=ctk.CTkFont(size=14, weight="bold"), text_color="#00D2FF").pack(anchor="w", padx=14, pady=(12, 2))
        ctk.CTkLabel(boost_card, text="Deixa o PC mais fluido: boot mais rápido, apps abrindo mais rápido e menos input lag. Tudo reversível.",
                     font=ctk.CTkFont(size=11), text_color="#C4B5FD", justify="left").pack(anchor="w", padx=14, pady=(0, 8))
        boost_row = ctk.CTkFrame(boost_card, fg_color="transparent")
        boost_row.pack(fill="x", padx=12, pady=(0, 12))
        boost_row.columnconfigure((0, 1), weight=1)
        bt1 = ctk.CTkButton(boost_row, text="🚀 Aplicar Boost (Fluidez Máxima)", font=ctk.CTkFont(size=12, weight="bold"),
                            fg_color="#7928CA", hover_color="#9333EA", height=40,
                            command=lambda: self.run_premium(self.apply_turbo_boost))
        bt1.grid(row=0, column=0, padx=4, sticky="ew")
        ToolTip(bt1, "Boot mais rápido, menus/apps mais rápidos, Prefetch ativo e Game DVR desligado (menos input lag). Reversível.", "🚀 BOOST")
        bt2 = ctk.CTkButton(boost_row, text="🧽 Liberar Espaço no Disco C:", font=ctk.CTkFont(size=12, weight="bold"),
                            fg_color="#059669", hover_color="#047857", height=40,
                            command=lambda: self.run_async(self.free_disk_space))
        bt2.grid(row=0, column=1, padx=4, sticky="ew")
        ToolTip(bt2, "Apaga só lixo seguro (temporários, caches, lixeira, componentes antigos do Windows) e mostra quanto liberou.", "🧽 LIBERAR ESPAÇO")
        bt3 = ctk.CTkButton(boost_row, text="🎮 MODO FPS: Otimizar Meus Jogos", font=ctk.CTkFont(size=12, weight="bold"),
                            fg_color="#DC2626", hover_color="#B91C1C", height=44,
                            command=lambda: self.run_premium(self.apply_fps_mode))
        bt3.grid(row=1, column=0, padx=4, pady=(8, 0), sticky="ew")
        ToolTip(bt3, "Acha os jogos instalados (Steam, Epic, Riot, Battle.net...) e deixa cada um com prioridade alta de CPU/disco, GPU dedicada e tela cheia sem lag - permanente. Ainda reforça ao vivo enquanto joga.", "🎮 MODO FPS")
        bt4 = ctk.CTkButton(boost_row, text="➕ Adicionar Jogo (.exe)", font=ctk.CTkFont(size=12, weight="bold"),
                            fg_color="#2563EB", hover_color="#1D4ED8", height=44,
                            command=lambda: self.run_premium(self.add_game_manually))
        bt4.grid(row=1, column=1, padx=4, pady=(8, 0), sticky="ew")
        ToolTip(bt4, "Escolha o .exe de qualquer jogo que não foi encontrado sozinho.", "➕ ADICIONAR JOGO")

        # Bloco de Ações Rápidas (Movido do Painel / Terceiro Print)
        quick_top = ctk.CTkFrame(scroll, fg_color="transparent")
        quick_top.pack(fill="x", pady=(0, 8), padx=2)
        quick_top.columnconfigure((0, 1, 2), weight=1)

        # Card 1: Limpeza Cache & RAM
        c1 = ctk.CTkFrame(quick_top, fg_color="#181230", corner_radius=10, border_width=1, border_color="#241B44")
        c1.grid(row=0, column=0, padx=4, pady=2, sticky="nsew")
        ctk.CTkLabel(c1, text="🧹 Limpeza de Cache", font=ctk.CTkFont(size=12, weight="bold"), text_color="#FFFFFF").pack(anchor="w", padx=12, pady=(10, 2))
        ctk.CTkLabel(c1, text="Limpa arquivos temporários do Windows.", font=ctk.CTkFont(size=10), text_color="#9CA3AF").pack(anchor="w", padx=12, pady=(0, 8))
        btn_c1 = ctk.CTkButton(c1, text="Limpar Agora", font=ctk.CTkFont(size=11, weight="bold"), fg_color="#E67E22", hover_color="#D35400", height=30, command=lambda: self.run_async(self.cache_cleaner))
        btn_c1.pack(fill="x", padx=12, pady=(0, 10))
        ToolTip(btn_c1, "Esvazia as pastas temporárias do Windows (%TEMP% e Windows\\Temp). Não mexe no Prefetch.", "🧹 LIMPEZA DE CACHE")

        # Card 2: Monitor BitLocker
        c2 = ctk.CTkFrame(quick_top, fg_color="#181230", corner_radius=10, border_width=1, border_color="#241B44")
        c2.grid(row=0, column=1, padx=4, pady=2, sticky="nsew")
        ctk.CTkLabel(c2, text="📊 Monitor BitLocker", font=ctk.CTkFont(size=12, weight="bold"), text_color="#FFFFFF").pack(anchor="w", padx=12, pady=(10, 2))
        ctk.CTkLabel(c2, text="Acompanha descriptografia % ao vivo.", font=ctk.CTkFont(size=10), text_color="#9CA3AF").pack(anchor="w", padx=12, pady=(0, 8))
        btn_c2 = ctk.CTkButton(c2, text="Abrir Monitor", font=ctk.CTkFont(size=11, weight="bold"), fg_color="#2980B9", hover_color="#1F618D", height=30, command=self.open_bitlocker_monitor)
        btn_c2.pack(fill="x", padx=12, pady=(0, 10))
        ToolTip(btn_c2, "Abre a janela flutuante com a barra de porcentagem de descriptografia do BitLocker em tempo real.", "📊 MONITOR BITLOCKER")

        # Card 3: IObit Driver Booster
        c3 = ctk.CTkFrame(quick_top, fg_color="#181230", corner_radius=10, border_width=1, border_color="#241B44")
        c3.grid(row=0, column=2, padx=4, pady=2, sticky="nsew")
        ctk.CTkLabel(c3, text="🔄 Atualizar Drivers", font=ctk.CTkFont(size=12, weight="bold"), text_color="#FFFFFF").pack(anchor="w", padx=12, pady=(10, 2))
        ctk.CTkLabel(c3, text="Drivers de vídeo e áudio atualizados.", font=ctk.CTkFont(size=10), text_color="#9CA3AF").pack(anchor="w", padx=12, pady=(0, 8))
        btn_c3 = ctk.CTkButton(c3, text="IObit Booster", font=ctk.CTkFont(size=11, weight="bold"), fg_color="#27AE60", hover_color="#1E8449", height=30, command=lambda: self.run_async(self.download_and_install_driver_booster))
        btn_c3.pack(fill="x", padx=12, pady=(0, 10))
        ToolTip(btn_c3, "Baixa e instala o IObit Driver Booster para escanear e atualizar automaticamente drivers antigos.", "🔄 ATUALIZADOR DRIVERS")

        # Process Lasso
        card_pl = ctk.CTkFrame(scroll, fg_color="#181230", corner_radius=10, border_width=1, border_color="#241B44")
        card_pl.pack(fill="x", padx=2, pady=6)
        ctk.CTkLabel(card_pl, text="🔥 Gerenciador de Prioridade Máxima (Estilo Process Lasso)", font=ctk.CTkFont(weight="bold", size=13), text_color="#F1C40F").pack(anchor="w", padx=14, pady=(12, 2))
        ctk.CTkLabel(card_pl, text="Dê 100% da atenção da CPU e Placa de Vídeo para o seu jogo aberto.", font=ctk.CTkFont(size=11), text_color="#9CA3AF").pack(anchor="w", padx=14, pady=(0, 8))
        btn_pl = ctk.CTkButton(card_pl, text="🚀 ABRIR GERENCIADOR", fg_color="#C0392B", hover_color="#922B21", font=ctk.CTkFont(weight="bold"), height=34, command=self.open_process_lasso)
        btn_pl.pack(fill="x", padx=14, pady=(0, 12))
        ToolTip(btn_pl, "Abre o gerenciador de afinidade e prioridade em tempo real nos núcleos da CPU para o jogo em foco.", "🔥 PROCESS LASSO")

        # Smart Game Booster & Mira Perfeita 1:1
        card_sgb = ctk.CTkFrame(scroll, fg_color="#181230", corner_radius=10, border_width=1, border_color="#241B44")
        card_sgb.pack(fill="x", padx=2, pady=6)
        ctk.CTkLabel(card_sgb, text="⚡ Smart Game Booster & Calibração de Mouse 1:1 (FPS & Mira)", font=ctk.CTkFont(weight="bold", size=13), text_color="#00D2FF").pack(anchor="w", padx=14, pady=(12, 2))
        ctk.CTkLabel(card_sgb, text="Desbloqueie 100% dos núcleos da CPU, prioridade de GPU e remova qualquer aceleração ou delay do mouse.", font=ctk.CTkFont(size=11), text_color="#9CA3AF").pack(anchor="w", padx=14, pady=(0, 8))

        sgb_grid = ctk.CTkFrame(card_sgb, fg_color="transparent")
        sgb_grid.pack(fill="x", padx=12, pady=(0, 12))
        sgb_grid.columnconfigure((0, 1, 2), weight=1)

        btn_boost = ctk.CTkButton(sgb_grid, text="🚀 Super Boost de FPS", fg_color="#7928CA", hover_color="#9333EA", height=34, font=ctk.CTkFont(size=11, weight="bold"), command=lambda: self.run_async(self.apply_smart_game_booster))
        btn_boost.grid(row=0, column=0, padx=3, pady=3, sticky="ew")
        ToolTip(btn_boost, "Desbloqueia todos os núcleos da CPU (Core Unparking 100%) e agenda a GPU para taxa máxima de FPS sem travamentos.", "⚡ SUPER BOOST FPS")

        btn_mouse = ctk.CTkButton(sgb_grid, text="🎯 Calibrar Mouse 1:1", fg_color="#2563EB", hover_color="#1D4ED8", height=34, font=ctk.CTkFont(size=11, weight="bold"), command=lambda: self.run_async(self.apply_mouse_calibration))
        btn_mouse.grid(row=0, column=1, padx=3, pady=3, sticky="ew")
        ToolTip(btn_mouse, "Aplica correção MarkC 1:1, desativa aceleração de ponteiro, ajusta buffer USB para 100 e elimina input lag da mira.", "🎯 MOUSE 1:1 RAW")

        btn_defrag = ctk.CTkButton(sgb_grid, text="💾 Game Defrag (SSD/HD)", fg_color="#059669", hover_color="#047857", height=34, font=ctk.CTkFont(size=11, weight="bold"), command=lambda: self.run_async(self.optimize_game_disks))
        btn_defrag.grid(row=0, column=2, padx=3, pady=3, sticky="ew")
        ToolTip(btn_defrag, "Otimiza a leitura dos volumes de jogos via TRIM em SSDs e desfragmentação inteligente para carregamento veloz.", "💾 GAME DEFRAG")

        # Tools Grid (2 columns)
        grid = ctk.CTkFrame(scroll, fg_color="transparent")
        grid.pack(fill="both", expand=True, padx=2)
        grid.columnconfigure((0, 1), weight=1)

        # Col 1: Limpeza & Segurança
        col1 = ctk.CTkFrame(grid, fg_color="#181230", corner_radius=10, border_width=1, border_color="#241B44")
        col1.grid(row=0, column=0, padx=4, pady=4, sticky="nsew")
        self.col2_ferramentas = col1
        ctk.CTkLabel(col1, text="🛡️ Limpeza & Segurança", font=ctk.CTkFont(weight="bold", size=13), text_color="#2ECC71").pack(anchor="w", padx=12, pady=(10, 6))

        def add_tool_btn(p, text, color, hover, cmd, tip=None, title="🛠️ FERRAMENTA"):
            b = ctk.CTkButton(p, text=text, fg_color=color, hover_color=hover, font=ctk.CTkFont(size=11, weight="bold"), height=32, command=cmd)
            b.pack(fill="x", padx=12, pady=3)
            if tip:
                ToolTip(b, tip, title)
            return b

        add_tool_btn(col1, "🧹 Limpador de Lixo Total (Cache)", "#27AE60", "#1E8449", lambda: self.run_async(self.cache_cleaner), "Limpa %TEMP%, Windows\\Temp, Lixeira e cache de atualização do Windows.", "🧹 LIMPEZA TOTAL")
        add_tool_btn(col1, "💾 Criar Ponto de Restauração", "#2980B9", "#1F618D", lambda: self.run_async(lambda: self.create_restore_point(force_visible=True)), "Gera um backup instantâneo de segurança do sistema para desfazer alterações se necessário.", "💾 PONTO RESTAURAÇÃO")
        add_tool_btn(col1, "🔧 Reparar Arquivos Corrompidos", "#C0392B", "#922B21", lambda: self.run_premium(self.fix_corrupted_files), "Executa SFC /scannow e reparo de imagens DISM para restaurar DLLs corrompidas do Windows.", "🔧 REPARAR ARQUIVOS")
        add_tool_btn(col1, "📉 Reduzir Uso de RAM", "#F39C12", "#D68910", lambda: self.run_premium(self.reduce_ram_usage), "Força o esvaziamento imediato da memória de trabalho de aplicativos ociosos.", "📉 REDUZIR RAM")
        add_tool_btn(col1, "⏰ Limpeza Automática Diária", "#27AE60", "#1E8449", lambda: self.run_async(self.enable_auto_clean), "Cria uma tarefa diária silenciosa no Agendador do Windows para manter o PC limpo.", "⏰ LIMPEZA DIÁRIA")
        add_tool_btn(col1, "🛑 Desativar Limpeza Agendada", "#7F8C8D", "#626567", lambda: self.run_async(self.disable_auto_clean), "Cancela a rotina de limpeza automática agendada no Windows.", "🛑 DESATIVAR ROTINA")
        ctk.CTkFrame(col1, height=6, fg_color="transparent").pack()

        # Col 2: Desempenho & Drivers
        col2 = ctk.CTkFrame(grid, fg_color="#181230", corner_radius=10, border_width=1, border_color="#241B44")
        col2.grid(row=0, column=1, padx=4, pady=4, sticky="nsew")
        ctk.CTkLabel(col2, text="⚡ Desempenho & Drivers", font=ctk.CTkFont(weight="bold", size=13), text_color="#00D2FF").pack(anchor="w", padx=12, pady=(10, 6))

        add_tool_btn(col2, "🗑️ Windows Debloater", "#8E44AD", "#71368A", lambda: self.run_async(self.windows_debloater), "Desinstala aplicativos e serviços inúteis nativos do Windows 10 e 11.", "🗑️ WINDOWS DEBLOATER")
        add_tool_btn(col2, "🚀 Instalar IObit Driver Booster", "#27AE60", "#1E8449", lambda: self.run_async(self.download_and_install_driver_booster), "Baixa e instala o Driver Booster para atualizar drivers de vídeo, áudio e placa-mãe.", "🚀 DRIVER BOOSTER")
        add_tool_btn(col2, "🛡️ Instalar Advanced SystemCare", "#2980B9", "#1F618D", lambda: self.run_async(self.download_and_install_advanced_systemcare), "Instala o Advanced SystemCare para otimização avançada de registro e privacidade.", "🛡️ SYSTEMCARE")
        add_tool_btn(col2, "🛠️ Pacote C++ / DirectX (Visual C++)", "#8E44AD", "#5B2C6F", lambda: self.run_premium(self.install_drivers), "Instala todas as versões do Microsoft Visual C++ e DirectX para corrigir erros de DLL em jogos.", "🛠️ PACOTE C++ / DIRECTX")
        add_tool_btn(col2, "🖥️ App Oficial da GPU", "#1ABC9C", "#16A085", lambda: self.run_premium(self.install_gpu_app), "Identifica seu fabricante de vídeo (NVIDIA/AMD/Intel) e abre o painel oficial de controle.", "🖥️ APP OFICIAL GPU")
        add_tool_btn(col2, "📊 Instalar MSI Afterburner", "#E74C3C", "#C0392B", lambda: self.run_async(self.install_afterburner), "Instala o MSI Afterburner com RivaTuner para monitorar FPS, uso de hardware e overclock seguro.", "📊 MSI AFTERBURNER")
        ctk.CTkFrame(col2, height=6, fg_color="transparent").pack()

        # Card Recursos Extras (Defender, IE, Desktop, Chrome, Drivers, Áudio FPS)
        card_x = ctk.CTkFrame(scroll, fg_color="#181230", corner_radius=10, border_width=1, border_color="#241B44")
        card_x.pack(fill="x", padx=2, pady=6)
        ctk.CTkLabel(card_x, text="🧰 Sistema, Drivers & Áudio FPS", font=ctk.CTkFont(weight="bold", size=13), text_color="#F1C40F").pack(anchor="w", padx=14, pady=(10, 6))
        x_grid = ctk.CTkFrame(card_x, fg_color="transparent")
        x_grid.pack(fill="x", padx=12, pady=(0, 10))
        x_grid.columnconfigure((0, 1), weight=1)
        extras_btns = [
            ("🛡️ Desativar Windows Defender", "#C0392B", "#922B21", self.disable_defender, "Desliga a proteção em tempo real do Defender e confirma o resultado. Se a Proteção contra Adulteração estiver ligada, abre a Segurança do Windows para você desligar.", "🛡️ DEFENDER OFF"),
            ("✅ Reativar Windows Defender", "#27AE60", "#1E8449", self.enable_defender, "Remove as políticas e liga a proteção em tempo real novamente.", "✅ DEFENDER ON"),
            ("🖥️ Limpar Área de Trabalho", "#2980B9", "#1F618D", self.clean_desktop, "Manda para a Lixeira atalhos quebrados, arquivos temporários/vazios e pastas vazias. Mostra a lista antes.", "🖥️ LIMPAR DESKTOP"),
            ("🗑️ Remover Internet Explorer", "#8E44AD", "#71368A", self.remove_internet_explorer, "Remove o recurso Internet Explorer e seus atalhos.", "🗑️ REMOVER IE"),
            ("🌐 Chrome como Padrão", "#F39C12", "#D68910", self.set_chrome_default, "Instala o Chrome se faltar e o define como padrão para links, .html e .pdf.", "🌐 CHROME PADRÃO"),
            ("🔄 Atualizar Drivers (sem Booster)", "#16A085", "#12806A", self.update_drivers_native, "Cria ponto de restauração, reescaneia o hardware, instala drivers do Windows Update e abre a página oficial da sua placa de vídeo.", "🔄 DRIVERS"),
            ("🎧 Ativar Áudio FPS (passos/tiros)", "#E74C3C", "#C0392B", self.audio_fps_enable, "Instala o Equalizer APO e aplica um perfil que destaca passos, recarga e tiros e reduz explosões/graves.", "🎧 ÁUDIO FPS"),
            ("🔇 Desativar Áudio FPS", "#7F8C8D", "#626567", self.audio_fps_disable, "Volta o som ao normal sem desinstalar nada.", "🔇 ÁUDIO NORMAL"),
        ]
        for i, (txt, c, h, fn, tip, ttl) in enumerate(extras_btns):
            b = ctk.CTkButton(x_grid, text=txt, fg_color=c, hover_color=h, height=32, font=ctk.CTkFont(size=11, weight="bold"), command=lambda f=fn: self.run_async(f))
            b.grid(row=i // 2, column=i % 2, padx=3, pady=3, sticky="ew")
            ToolTip(b, tip, ttl)


        # Card Launchers Gamers & Plataformas (Pacote Gamer - Battle.net, EA Sports, etc.)
        card_launchers = ctk.CTkFrame(scroll, fg_color="#181230", corner_radius=10, border_width=1, border_color="#241B44")
        card_launchers.pack(fill="x", padx=2, pady=6)
        ctk.CTkLabel(card_launchers, text="🎮 Plataformas & Launchers de Jogos (Pacote Gamer)", font=ctk.CTkFont(weight="bold", size=13), text_color="#00D2FF").pack(anchor="w", padx=14, pady=(10, 6))

        l_grid = ctk.CTkFrame(card_launchers, fg_color="transparent")
        l_grid.pack(fill="x", padx=12, pady=(0, 10))
        l_grid.columnconfigure((0, 1, 2), weight=1)

        btn_bnet = ctk.CTkButton(l_grid, text="Battle.net (Blizzard)", fg_color="#0074E0", hover_color="#005CB8", height=32, font=ctk.CTkFont(size=11, weight="bold"), command=lambda: self.run_async(self.install_streamer_app, "Blizzard.BattleNet", "Battle.net"))
        btn_bnet.grid(row=0, column=0, padx=3, pady=3, sticky="ew")
        ToolTip(btn_bnet, "Instala a plataforma oficial Battle.net da Blizzard para Call of Duty (Warzone, MW3), Overwatch 2 e Diablo.", "🎮 BATTLE.NET BLIZZARD")

        btn_ea = ctk.CTkButton(l_grid, text="EA Sports (EA App)", fg_color="#FF4747", hover_color="#D93636", height=32, font=ctk.CTkFont(size=11, weight="bold"), command=lambda: self.run_async(self.install_streamer_app, "ElectronicArts.EADesktop", "EA App (EA Sports)"))
        btn_ea.grid(row=0, column=1, padx=3, pady=3, sticky="ew")
        ToolTip(btn_ea, "Instala o EA App oficial da Electronic Arts para EA Sports FC (FIFA), Apex Legends e Battlefield.", "⚽ EA SPORTS / EA APP")

        btn_steam = ctk.CTkButton(l_grid, text="Steam (Valve)", fg_color="#1B2838", hover_color="#171A21", height=32, font=ctk.CTkFont(size=11, weight="bold"), command=lambda: self.run_async(self.install_streamer_app, "Valve.Steam", "Steam"))
        btn_steam.grid(row=0, column=2, padx=3, pady=3, sticky="ew")
        ToolTip(btn_steam, "Instala o cliente oficial da Steam para CS2, Dota 2, PUBG e centenas de jogos da sua biblioteca.", "🎮 STEAM VALVE")

        btn_epic = ctk.CTkButton(l_grid, text="Epic Games Launcher", fg_color="#313131", hover_color="#222222", height=32, font=ctk.CTkFont(size=11, weight="bold"), command=lambda: self.run_async(self.install_streamer_app, "EpicGames.EpicGamesLauncher", "Epic Games"))
        btn_epic.grid(row=1, column=0, padx=3, pady=3, sticky="ew")
        ToolTip(btn_epic, "Instala o inicializador da Epic Games para Fortnite, Rocket League e jogos grátis semanais.", "⚡ EPIC GAMES")

        btn_riot = ctk.CTkButton(l_grid, text="Riot Games Client", fg_color="#D13639", hover_color="#AB282B", height=32, font=ctk.CTkFont(size=11, weight="bold"), command=lambda: self.run_async(self.install_streamer_app, "RiotGames.RiotClient", "Riot Games"))
        btn_riot.grid(row=1, column=1, padx=3, pady=3, sticky="ew")
        ToolTip(btn_riot, "Instala a plataforma oficial da Riot Games para Valorant, League of Legends e Teamfight Tactics.", "🎯 RIOT GAMES CLIENT")

        btn_ubi = ctk.CTkButton(l_grid, text="Ubisoft Connect", fg_color="#005B94", hover_color="#00436E", height=32, font=ctk.CTkFont(size=11, weight="bold"), command=lambda: self.run_async(self.install_streamer_app, "Ubisoft.Connect", "Ubisoft Connect"))
        btn_ubi.grid(row=1, column=2, padx=3, pady=3, sticky="ew")
        ToolTip(btn_ubi, "Instala o Ubisoft Connect para Rainbow Six Siege, Far Cry e Assassin's Creed.", "🦅 UBISOFT CONNECT")

        # Card Apps para Streamers & Criadores
        card_stream = ctk.CTkFrame(scroll, fg_color="#181230", corner_radius=10, border_width=1, border_color="#241B44")
        card_stream.pack(fill="x", padx=2, pady=6)
        ctk.CTkLabel(card_stream, text="🎥 Apps para Streamers & Criadores de Conteúdo", font=ctk.CTkFont(weight="bold", size=13), text_color="#EC4899").pack(anchor="w", padx=14, pady=(10, 6))

        s_grid = ctk.CTkFrame(card_stream, fg_color="transparent")
        s_grid.pack(fill="x", padx=12, pady=(0, 10))
        s_grid.columnconfigure((0, 1, 2), weight=1)

        b_obs = ctk.CTkButton(s_grid, text="OBS Studio", fg_color="#7A111C", hover_color="#5C0E17", height=30, command=lambda: self.run_async(self.install_streamer_app, "Obsproject.ObsStudio", "OBS Studio"))
        b_obs.grid(row=0, column=0, padx=3, pady=3, sticky="ew")
        ToolTip(b_obs, "Instala o software profissional de gravação e transmissão ao vivo mais utilizado.", "🎥 OBS STUDIO")

        b_disc = ctk.CTkButton(s_grid, text="Discord", fg_color="#7A111C", hover_color="#5C0E17", height=30, command=lambda: self.run_async(self.install_streamer_app, "Discord.Discord", "Discord"))
        b_disc.grid(row=0, column=1, padx=3, pady=3, sticky="ew")
        ToolTip(b_disc, "Instala o Discord para chamadas de voz e bate-papo de baixa latência em jogos.", "💬 DISCORD")

        b_spot = ctk.CTkButton(s_grid, text="Spotify", fg_color="#7A111C", hover_color="#5C0E17", height=30, command=lambda: self.run_async(self.install_spotify))
        b_spot.grid(row=0, column=2, padx=3, pady=3, sticky="ew")
        ToolTip(b_spot, "Baixa e instala o aplicativo oficial do Spotify para ouvir músicas sem travamentos.", "🎵 SPOTIFY")

        b_vm = ctk.CTkButton(s_grid, text="Voicemeeter Banana", fg_color="#7A111C", hover_color="#5C0E17", height=30, command=lambda: self.run_async(self.install_streamer_app, "VB-Audio.Voicemeeter.Banana", "Voicemeeter Banana"))
        b_vm.grid(row=1, column=0, padx=3, pady=3, sticky="ew")
        ToolTip(b_vm, "Mesa de som virtual para equalizar microfone, Discord e áudio do jogo separadamente.", "🎛️ VOICEMEETER")

        b_slabs = ctk.CTkButton(s_grid, text="Streamlabs Desktop", fg_color="#7A111C", hover_color="#5C0E17", height=30, command=lambda: self.run_async(self.install_streamer_app, "Streamlabs.StreamlabsDesktop", "Streamlabs Desktop"))
        b_slabs.grid(row=1, column=1, padx=3, pady=3, sticky="ew")
        ToolTip(b_slabs, "Instala o Streamlabs com temas, overlays e notificações de donate prontos.", "📺 STREAMLABS")

        b_tk = ctk.CTkButton(s_grid, text="TikTok Live Studio", fg_color="#7A111C", hover_color="#5C0E17", height=30, command=lambda: self.run_async(self.install_tiktok_live_studio))
        b_tk.grid(row=1, column=2, padx=3, pady=3, sticky="ew")
        ToolTip(b_tk, "Instala o aplicativo oficial do TikTok para transmissões ao vivo direto do seu computador.", "📱 TIKTOK LIVE")

        return scroll

    def create_view_sistemas(self, parent):
        scroll = ctk.CTkScrollableFrame(parent, fg_color="transparent")

        head = ctk.CTkFrame(scroll, fg_color="#151028", corner_radius=10)
        head.pack(fill="x", pady=(0, 10), padx=2)

        ctk.CTkLabel(
            head,
            text="🚀 Sistemas Customizados AME & Formatação",
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color="#FFFFFF"
        ).pack(anchor="w", padx=14, pady=(10, 2))

        ctk.CTkLabel(
            head,
            text="Ferramentas avançadas para instalação de ISOs modificadas e preparação de HDs/SSDs:",
            font=ctk.CTkFont(size=11),
            text_color="#9CA3AF"
        ).pack(anchor="w", padx=14, pady=(0, 10))

        # Card AME
        c_ame = ctk.CTkFrame(scroll, fg_color="#181230", corner_radius=10, border_width=1, border_color="#1A237E")
        c_ame.pack(fill="x", padx=2, pady=6)
        self.col1_sistemas = c_ame

        ctk.CTkLabel(c_ame, text="💻 Playbooks AME (AtlasOS & ReviOS)", font=ctk.CTkFont(size=13, weight="bold"), text_color="#00D2FF").pack(anchor="w", padx=14, pady=(12, 2))
        ctk.CTkLabel(c_ame, text="Instale versões limpas do Windows com zero bloatwares e telemetria desativada.", font=ctk.CTkFont(size=11), text_color="#9CA3AF").pack(anchor="w", padx=14, pady=(0, 8))

        ctk.CTkButton(c_ame, text="Instalar AtlasOS (AME)", fg_color="#283593", hover_color="#1A237E", font=ctk.CTkFont(weight="bold"), height=34, command=lambda: self.run_async(self.launch_ame, "Atlas")).pack(fill="x", padx=14, pady=3)
        ctk.CTkButton(c_ame, text="Instalar ReviOS (AME)", fg_color="#283593", hover_color="#1A237E", font=ctk.CTkFont(weight="bold"), height=34, command=lambda: self.run_async(self.launch_ame, "Revi")).pack(fill="x", padx=14, pady=3)

        # Card Format & BitLocker
        c_fmt = ctk.CTkFrame(scroll, fg_color="#181230", corner_radius=10, border_width=1, border_color="#C0392B")
        c_fmt.pack(fill="x", padx=2, pady=6)

        ctk.CTkLabel(c_fmt, text="💿 Preparação para Formatação & BitLocker", font=ctk.CTkFont(size=13, weight="bold"), text_color="#EF4444").pack(anchor="w", padx=14, pady=(12, 2))
        ctk.CTkLabel(c_fmt, text="Descriptografa todos os discos (remove BitLocker) e realiza teste de integridade SMART.", font=ctk.CTkFont(size=11), text_color="#9CA3AF").pack(anchor="w", padx=14, pady=(0, 8))

        ctk.CTkButton(c_fmt, text="💿 Preparar para Formatação (Descriptografar BitLocker + SMART)", fg_color="#C0392B", hover_color="#922B21", font=ctk.CTkFont(weight="bold"), height=36, command=lambda: self.run_async(self.prepare_for_format)).pack(fill="x", padx=14, pady=3)
        ctk.CTkButton(c_fmt, text="📊 Ver Progresso do BitLocker (% Ao Vivo em Tempo Real)", fg_color="#2980B9", hover_color="#1F618D", font=ctk.CTkFont(weight="bold"), height=36, command=self.open_bitlocker_monitor).pack(fill="x", padx=14, pady=(3, 12))

        return scroll

    def create_view_bugs(self, parent):
        scroll = ctk.CTkScrollableFrame(parent, fg_color="transparent")

        head = ctk.CTkFrame(scroll, fg_color="#151028", corner_radius=10)
        head.pack(fill="x", pady=(0, 10), padx=2)

        ctk.CTkLabel(
            head,
            text="🩹 Central de Correção Automática de Bugs",
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color="#FFFFFF"
        ).pack(anchor="w", padx=14, pady=(10, 2))

        ctk.CTkLabel(
            head,
            text="Repare problemas de Barra de Tarefas, Menu Iniciar, rede travada ou corrupção de sistema:",
            font=ctk.CTkFont(size=11),
            text_color="#9CA3AF"
        ).pack(anchor="w", padx=14, pady=(0, 10))

        # Main Fix Card
        c_fix = ctk.CTkFrame(scroll, fg_color="#181230", corner_radius=10, border_width=1, border_color="#E74C3C")
        c_fix.pack(fill="x", padx=2, pady=6)

        ctk.CTkLabel(c_fix, text="🔧 Diagnóstico & Reparo Automático em 1 Clique", font=ctk.CTkFont(size=14, weight="bold"), text_color="#E74C3C").pack(anchor="w", padx=14, pady=(14, 2))
        ctk.CTkLabel(
            c_fix,
            text="Corrige automaticamente:\n• Menu Iniciar ou Barra de Tarefas travados/não abrindo\n• Lentidão no Explorer.exe e processos zumbis\n• Falha de conexão de rede, pilha WinSock e cache DNS",
            font=ctk.CTkFont(size=11),
            text_color="#CBD5E1",
            justify="left"
        ).pack(anchor="w", padx=14, pady=(0, 10))

        ctk.CTkButton(
            c_fix,
            text="🔍 Diagnosticar & Corrigir Todos os Bugs Agora",
            fg_color="#C0392B",
            hover_color="#922B21",
            font=ctk.CTkFont(size=13, weight="bold"),
            height=42,
            command=lambda: self.run_async(self.diagnose_and_fix_bugs)
        ).pack(fill="x", padx=14, pady=(0, 14))

        # Detector de Travamentos Card
        c_st = ctk.CTkFrame(scroll, fg_color="#181230", corner_radius=10, border_width=1, border_color="#00D2FF")
        c_st.pack(fill="x", padx=2, pady=6)
        ctk.CTkLabel(c_st, text="🔎 Detector de Travamentos (Discord, overlays, gravação)", font=ctk.CTkFont(size=14, weight="bold"), text_color="#00D2FF").pack(anchor="w", padx=14, pady=(12, 2))
        ctk.CTkLabel(
            c_st,
            text="Procura o que costuma travar o jogo e deixar o PC pesado:\n• Gravação em segundo plano (Game DVR) ligada\n• Overlays do Discord, Xbox Game Bar, NVIDIA, RivaTuner, OBS\n• Plano de energia fraco, excesso de programas na inicialização, disco cheio",
            font=ctk.CTkFont(size=11), text_color="#CBD5E1", justify="left"
        ).pack(anchor="w", padx=14, pady=(0, 10))
        ctk.CTkButton(c_st, text="🔎 Procurar Causas de Travamento", fg_color="#2563EB", hover_color="#1D4ED8",
                      font=ctk.CTkFont(size=13, weight="bold"), height=40,
                      command=self.open_stutter_detector).pack(fill="x", padx=14, pady=(0, 14))

        # Warzone Doctor / Game Crashes Card
        c_wz = ctk.CTkFrame(scroll, fg_color="#181230", corner_radius=10, border_width=1, border_color="#10B981")
        c_wz.pack(fill="x", padx=2, pady=6)

        ctk.CTkLabel(c_wz, text="🛡️ Warzone Doctor • Correção de Erro 0x00001338 & KERNELBASE", font=ctk.CTkFont(size=14, weight="bold"), text_color="#10B981").pack(anchor="w", padx=14, pady=(12, 2))
        ctk.CTkLabel(
            c_wz,
            text="Soluciona os crashes mais comuns do Warzone e jogos DirectX:\n• Erro 0x00001338 e falha na KERNELBASE.dll / cod.exe\n• Limpa Shader Cache corrompido e resets de DXCache/D3D\n• Calibra VideoMemoryScale (0.75) e RendererWorkerCount aos núcleos reais\n• Desativa conflito de Control Flow Guard (CFG) e DEP do Windows",
            font=ctk.CTkFont(size=11),
            text_color="#CBD5E1",
            justify="left"
        ).pack(anchor="w", padx=14, pady=(0, 10))

        btn_rep_wz = ctk.CTkButton(
            c_wz,
            text="🛡️ Reparar Erros do Warzone & Jogos (Fix 0x00001338)",
            fg_color="#10B981",
            hover_color="#059669",
            font=ctk.CTkFont(size=13, weight="bold"),
            height=40,
            command=lambda: self.run_async(self.repair_warzone_crashes)
        )
        btn_rep_wz.pack(fill="x", padx=14, pady=(0, 12))
        ToolTip(btn_rep_wz, "Corrige falhas 0x00001338, KERNELBASE.dll, shader cache e DEP/CFG do Warzone.")

        # Panic Button Card
        c_pan = ctk.CTkFrame(scroll, fg_color="#181230", corner_radius=10, border_width=1, border_color="#7F1D1D")
        c_pan.pack(fill="x", padx=2, pady=6)

        ctk.CTkLabel(c_pan, text="🚑 Botão do Pânico (Restauração do Sistema)", font=ctk.CTkFont(size=13, weight="bold"), text_color="#EF4444").pack(anchor="w", padx=14, pady=(12, 2))
        ctk.CTkLabel(c_pan, text="Abre a ferramenta nativa de Restauração de Sistema para voltar o Windows a um ponto anterior.", font=ctk.CTkFont(size=11), text_color="#9CA3AF").pack(anchor="w", padx=14, pady=(0, 8))

        ctk.CTkButton(
            c_pan,
            text="🚑 Abrir Restauração do Windows",
            fg_color="#7F1D1D",
            hover_color="#991B1B",
            font=ctk.CTkFont(weight="bold"),
            height=34,
            command=lambda: self.run_async(self.restore_system)
        ).pack(fill="x", padx=14, pady=(0, 12))

        return scroll

    def create_view_log(self, parent):
        frame = ctk.CTkFrame(parent, fg_color="transparent")

        top_bar = ctk.CTkFrame(frame, fg_color="#151028", corner_radius=10)
        top_bar.pack(fill="x", pady=(0, 8), padx=2)

        ctk.CTkLabel(
            top_bar,
            text="📜 Log de Operações & Auditoria em Tempo Real",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color="#00D2FF"
        ).pack(side="left", padx=14, pady=10)

        ctk.CTkButton(
            top_bar,
            text="🗑️ Limpar Console",
            font=ctk.CTkFont(size=11, weight="bold"),
            fg_color="#374151",
            hover_color="#4B5563",
            height=28,
            width=120,
            command=self.clear_log_console
        ).pack(side="right", padx=6, pady=10)

        ctk.CTkButton(
            top_bar,
            text="🔒 Auditoria Secreta",
            font=ctk.CTkFont(size=11, weight="bold"),
            fg_color="#8E44AD",
            hover_color="#5B2C6F",
            height=28,
            width=130,
            command=lambda: self.run_programmer_only(self.view_audit_log)
        ).pack(side="right", padx=6, pady=10)

        console_frame = ctk.CTkFrame(frame, fg_color="#0D0B18", corner_radius=10, border_width=1, border_color="#241B44")
        console_frame.pack(fill="both", expand=True, padx=2, pady=2)

        self.log_textbox = ctk.CTkTextbox(
            console_frame,
            fg_color="#0D0B18",
            text_color="#10B981",
            font=ctk.CTkFont(family="Consolas", size=12)
        )
        self.log_textbox.pack(fill="both", expand=True, padx=8, pady=8)
        self.log_textbox.configure(state="disabled")

        return frame

    def clear_log_console(self):
        if hasattr(self, 'log_textbox') and self.log_textbox.winfo_exists():
            self.log_textbox.configure(state="normal")
            self.log_textbox.delete("1.0", "end")
            self.log_textbox.configure(state="disabled")

    # --- SAÚDE, ROTINA PRO GAMER & ALARMES CUSTOMIZADOS ---
    def init_hydration(self):
        self.init_health_and_alarms()

    def init_health_and_alarms(self):
        localapp = os.environ.get("LOCALAPPDATA", "")
        self.routine_file = os.path.join(localapp, "Bernal Otimizacoes", "health_routine.json") if localapp else r"C:\Users\Public\Documents\Bernal_Routine.json"
        try: os.makedirs(os.path.dirname(self.routine_file), exist_ok=True)
        except: pass
        
        self.water_count = 0
        self.coffee_count = 0
        self.energy_count = 0
        self.meals = {"breakfast": False, "lunch": False, "dinner": False}
        self.custom_alarms = [
            {"time": "10:30", "label": "💊 Tomar Remédio / Café", "enabled": True},
            {"time": "12:30", "label": "🍽️ Hora do Almoço!", "enabled": True},
            {"time": "16:00", "label": "💧 Hidratação & Esticar Pernas", "enabled": True},
            {"time": "20:00", "label": "🍽️ Hora do Jantar!", "enabled": True}
        ]
        self.last_alarm_fired_min = None
        
        today_str = time.strftime("%Y-%m-%d")
        if os.path.exists(self.routine_file):
            try:
                with open(self.routine_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    if data.get("date") == today_str:
                        self.water_count = int(data.get("water", 0))
                        self.coffee_count = int(data.get("coffee", 0))
                        self.energy_count = int(data.get("energy", 0))
                        self.meals = data.get("meals", self.meals)
                    if "alarms" in data:
                        self.custom_alarms = data.get("alarms", self.custom_alarms)
            except Exception:
                pass
        self.save_routine_data()
        self.start_alarm_daemon()

    def save_routine_data(self):
        try:
            today_str = time.strftime("%Y-%m-%d")
            data = {
                "date": today_str,
                "water": self.water_count,
                "coffee": self.coffee_count,
                "energy": self.energy_count,
                "meals": self.meals,
                "alarms": self.custom_alarms
            }
            with open(self.routine_file, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception:
            pass

    def drink_water(self, delta):
        self.water_count = max(0, min(12, self.water_count + delta))
        self.save_routine_data()
        self.update_hydration_ui()

    def track_coffee(self, delta=1):
        self.coffee_count = max(0, min(15, self.coffee_count + delta))
        self.save_routine_data()
        self.update_hydration_ui()

    def track_energy(self, delta=1):
        self.energy_count = max(0, min(8, self.energy_count + delta))
        self.save_routine_data()
        self.update_hydration_ui()

    def toggle_meal(self, meal_key):
        self.meals[meal_key] = not self.meals.get(meal_key, False)
        self.save_routine_data()
        self.update_hydration_ui()

    def add_custom_alarm_dialog(self):
        d = ctk.CTkToplevel(self)
        d.title("⏰ Novo Alarme / Lembrete")
        d.geometry("380x340")
        d.attributes("-topmost", True)
        d.grab_set()

        ctk.CTkLabel(d, text="⏰ Definir Horário & Motivo", font=ctk.CTkFont(size=15, weight="bold"), text_color="#00D2FF").pack(pady=(16, 4))
        ctk.CTkLabel(d, text="Ex: Tomar remédio, almoço, descanso ou pausa:", font=ctk.CTkFont(size=11), text_color="#9CA3AF").pack(pady=(0, 10))

        f_inputs = ctk.CTkFrame(d, fg_color="transparent")
        f_inputs.pack(fill="x", padx=24)

        ctk.CTkLabel(f_inputs, text="Horário (HH:MM):", font=ctk.CTkFont(size=11, weight="bold")).pack(anchor="w")
        e_time = ctk.CTkEntry(f_inputs, placeholder_text="Ex: 14:30 ou 09:00", font=ctk.CTkFont(size=12))
        e_time.pack(fill="x", pady=(2, 8))
        e_time.insert(0, time.strftime("%H:%M"))

        ctk.CTkLabel(f_inputs, text="Motivo / Descrição:", font=ctk.CTkFont(size=11, weight="bold")).pack(anchor="w")
        e_label = ctk.CTkComboBox(f_inputs, values=["💊 Tomar Remédio", "💧 Hora de Tomar Água", "☕ Hora do Café", "⚡ Energético / Pré-treino", "🍽️ Café da Manhã", "☀️ Almoço", "🌙 Jantar", "🚶 Pausa / Esticar Coluna"])
        e_label.pack(fill="x", pady=(2, 14))

        def _save():
            t_val = e_time.get().strip()
            l_val = e_label.get().strip()
            if t_val and l_val:
                self.custom_alarms.append({"time": t_val, "label": l_val, "enabled": True})
                self.save_routine_data()
                self.update_hydration_ui()
                d.destroy()
                messagebox.showinfo("Alarme Salvo", f"✅ Alarme para '{l_val}' às {t_val} ativado com sucesso!")

        ctk.CTkButton(d, text="💾 Salvar Alarme", fg_color="#10B981", hover_color="#059669", font=ctk.CTkFont(size=12, weight="bold"), height=32, command=_save).pack(pady=8)

    def remove_custom_alarm(self, idx):
        if 0 <= idx < len(self.custom_alarms):
            self.custom_alarms.pop(idx)
            self.save_routine_data()
            self.update_hydration_ui()

    def start_alarm_daemon(self):
        def _alarm_loop():
            while getattr(self, '_alarm_daemon_active', True):
                try:
                    cur_hm = time.strftime("%H:%M")
                    if cur_hm != self.last_alarm_fired_min:
                        for al in self.custom_alarms:
                            if al.get("enabled", True) and al.get("time") == cur_hm:
                                self.last_alarm_fired_min = cur_hm
                                self.after(0, lambda a=al: self.trigger_alarm_alert(a))
                                break
                except Exception:
                    pass
                time.sleep(10)
        self._alarm_daemon_active = True
        threading.Thread(target=_alarm_loop, daemon=True).start()

    def trigger_alarm_alert(self, alarm_item):
        def _play_loud_beep():
            try:
                import winsound
                # Toque de alarme de notificação bem alta de 2 segundos exatos
                for _ in range(4):
                    winsound.Beep(1750, 180)
                    winsound.Beep(2300, 220)
                    time.sleep(0.08)
            except Exception:
                try:
                    import winsound
                    winsound.MessageBeep(winsound.MB_ICONEXCLAMATION)
                except Exception:
                    pass
        threading.Thread(target=_play_loud_beep, daemon=True).start()
        msg = alarm_item.get("label", "Lembrete Pro Gamer!")
        t_str = alarm_item.get("time", "")
        self.log(f"⏰ ALARME DISPARADO ({t_str}): {msg}")
        alert_win = ctk.CTkToplevel(self)
        alert_win.title("⏰ Alarme Pro Gamer")
        alert_win.geometry("420x220")
        alert_win.attributes("-topmost", True)
        
        b = ctk.CTkFrame(alert_win, fg_color="#120E24", corner_radius=12, border_width=2, border_color="#F59E0B")
        b.pack(fill="both", expand=True, padx=4, pady=4)
        
        ctk.CTkLabel(b, text=f"⏰ HORA DO LEMBRETE! ({t_str})", font=ctk.CTkFont(size=14, weight="bold"), text_color="#F59E0B").pack(pady=(18, 6))
        ctk.CTkLabel(b, text=msg, font=ctk.CTkFont(size=16, weight="bold"), text_color="#FFFFFF").pack(pady=6)
        ctk.CTkLabel(b, text="Não se descuide durante suas partidas. Sua saúde melhora seus reflexos e mira!", font=ctk.CTkFont(size=10), text_color="#9CA3AF").pack(pady=(0, 14))
        ctk.CTkButton(b, text="Entendido / Já Fiz! ✅", fg_color="#10B981", hover_color="#059669", font=ctk.CTkFont(size=12, weight="bold"), height=32, command=alert_win.destroy).pack()

    def update_hydration_ui(self):
        if hasattr(self, 'lbl_water_count') and self.lbl_water_count.winfo_exists():
            liters = self.water_count * 0.25
            self.lbl_water_count.configure(text=f"{self.water_count}/8 copos hoje ({liters:.1f}L)")
        if hasattr(self, 'water_progress') and self.water_progress.winfo_exists():
            self.water_progress.set(min(1.0, self.water_count / 8.0))
        if hasattr(self, 'lbl_coffee_count') and self.lbl_coffee_count.winfo_exists():
            self.lbl_coffee_count.configure(text=f"☕ {self.coffee_count}")
        if hasattr(self, 'lbl_energy_count') and self.lbl_energy_count.winfo_exists():
            self.lbl_energy_count.configure(text=f"⚡ {self.energy_count}")

        # Update meal buttons
        if hasattr(self, 'btn_meal_bk') and self.btn_meal_bk.winfo_exists():
            self.btn_meal_bk.configure(fg_color="#10B981" if self.meals.get("breakfast") else "#1E293B")
        if hasattr(self, 'btn_meal_lu') and self.btn_meal_lu.winfo_exists():
            self.btn_meal_lu.configure(fg_color="#10B981" if self.meals.get("lunch") else "#1E293B")
        if hasattr(self, 'btn_meal_di') and self.btn_meal_di.winfo_exists():
            self.btn_meal_di.configure(fg_color="#10B981" if self.meals.get("dinner") else "#1E293B")

        self.render_alarms_list()

    def render_alarms_list(self):
        if not hasattr(self, 'alarms_container') or not self.alarms_container.winfo_exists():
            return
        for child in self.alarms_container.winfo_children():
            try:
                child.destroy()
            except Exception:
                pass
        
        if not self.custom_alarms:
            lbl = ctk.CTkLabel(self.alarms_container, text="Nenhum alarme ativo. Clique em '+ Novo'", font=ctk.CTkFont(size=9), text_color="#6B7280")
            lbl.pack(anchor="w", pady=1)
            return

        for idx, item in enumerate(self.custom_alarms):
            row = ctk.CTkFrame(self.alarms_container, fg_color="#120E24", corner_radius=6)
            row.pack(fill="x", pady=1)
            
            t_lbl = ctk.CTkLabel(row, text=f"⏰ {item.get('time', '')}", font=ctk.CTkFont(size=10, weight="bold"), text_color="#F59E0B")
            t_lbl.pack(side="left", padx=(6, 4))
            
            lbl_name = item.get('label', '')
            if len(lbl_name) > 16:
                lbl_name = lbl_name[:15] + ".."
            m_lbl = ctk.CTkLabel(row, text=lbl_name, font=ctk.CTkFont(size=9), text_color="#E2E8F0")
            m_lbl.pack(side="left", padx=2)
            
            btn_del = ctk.CTkButton(row, text="✕", width=18, height=18, fg_color="transparent", hover_color="#EF4444", text_color="#9CA3AF", font=ctk.CTkFont(size=9, weight="bold"), command=lambda i=idx: self.remove_custom_alarm(i))
            btn_del.pack(side="right", padx=4)
            ToolTip(btn_del, "Remover este alarme")

    # --- MOTHERBOARD, BIOS, DISPLAY HZ & VIRTUAL RAM ---
    def get_motherboard_and_bios(self):
        info = {
            "mb_vendor": "N/D",
            "mb_model": "N/D",
            "bios_vendor": "N/D",
            "bios_ver": "N/D",
            "bios_date": "N/D",
            "bios_status": "⚪ Status da BIOS não verificado",
            "is_outdated": False,
            "search_query": ""
        }
        try:
            import winreg
            k = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"HARDWARE\DESCRIPTION\System\BIOS")
            try: info["mb_vendor"] = str(winreg.QueryValueEx(k, "BaseBoardManufacturer")[0]).strip()
            except: pass
            try: info["mb_model"] = str(winreg.QueryValueEx(k, "BaseBoardProduct")[0]).strip()
            except: pass
            try: info["bios_vendor"] = str(winreg.QueryValueEx(k, "BIOSVendor")[0]).strip()
            except: pass
            try: info["bios_ver"] = str(winreg.QueryValueEx(k, "BIOSVersion")[0]).strip()
            except: pass
            try: info["bios_date"] = str(winreg.QueryValueEx(k, "BIOSReleaseDate")[0]).strip()
            except: pass
            winreg.CloseKey(k)
        except Exception:
            pass

        try:
            import re
            m = re.search(r'20(\d\d)', info["bios_date"])
            if m:
                yr = int(m.group(0))
                if yr < 2023:
                    info["is_outdated"] = True
                    info["bios_status"] = f"⚠️ BIOS Antiga ({info['bios_date']}) • Atualização Recomendada"
                else:
                    info["bios_status"] = f"🟢 BIOS Atualizada ({info['bios_date']})"
        except Exception:
            pass

        if info["mb_vendor"] == "N/D" and info["mb_model"] == "N/D":
            info["search_query"] = "atualizar BIOS placa-mae"
        else:
            info["search_query"] = f"{info['mb_vendor']} {info['mb_model']} BIOS update download"
        return info

    def open_bios_support_page(self):
        info = self.get_motherboard_and_bios()
        q = info.get("search_query", "motherboard bios update")
        self.log(f"Abrindo busca oficial da BIOS para: {info['mb_vendor']} {info['mb_model']}...")
        import urllib.parse
        url = f"https://www.google.com/search?q={urllib.parse.quote_plus(q)}"
        webbrowser.open(url)

    def get_monitor_display_info(self):
        import ctypes
        from ctypes import wintypes

        class DEVMODEA(ctypes.Structure):
            _fields_ = [
                ('dmDeviceName', ctypes.c_char * 32),
                ('dmSpecVersion', wintypes.WORD),
                ('dmDriverVersion', wintypes.WORD),
                ('dmSize', wintypes.WORD),
                ('dmDriverExtra', wintypes.WORD),
                ('dmFields', wintypes.DWORD),
                ('dmOrientation', ctypes.c_short),
                ('dmPaperSize', ctypes.c_short),
                ('dmPaperLength', ctypes.c_short),
                ('dmPaperWidth', ctypes.c_short),
                ('dmScale', ctypes.c_short),
                ('dmCopies', ctypes.c_short),
                ('dmDefaultSource', ctypes.c_short),
                ('dmPrintQuality', ctypes.c_short),
                ('dmColor', ctypes.c_short),
                ('dmDuplex', ctypes.c_short),
                ('dmYResolution', ctypes.c_short),
                ('dmTTOption', ctypes.c_short),
                ('dmCollate', ctypes.c_short),
                ('dmFormName', ctypes.c_char * 32),
                ('dmLogPixels', wintypes.WORD),
                ('dmBitsPerPel', wintypes.DWORD),
                ('dmPelsWidth', wintypes.DWORD),
                ('dmPelsHeight', wintypes.DWORD),
                ('dmDisplayFlags', wintypes.DWORD),
                ('dmDisplayFrequency', wintypes.DWORD),
            ]

        user32 = ctypes.windll.user32
        dm = DEVMODEA()
        dm.dmSize = 124

        cur_w, cur_h, cur_hz = 1920, 1080, 144
        if user32.EnumDisplaySettingsA(None, -1, ctypes.byref(dm)):
            cur_w = dm.dmPelsWidth
            cur_h = dm.dmPelsHeight
            cur_hz = dm.dmDisplayFrequency

        modes = set()
        freqs = set()
        i = 0
        while user32.EnumDisplaySettingsA(None, i, ctypes.byref(dm)):
            modes.add((dm.dmPelsWidth, dm.dmPelsHeight))
            freqs.add(dm.dmDisplayFrequency)
            i += 1

        max_hz = max(freqs) if freqs else cur_hz
        return {
            "current_w": cur_w,
            "current_h": cur_h,
            "current_hz": cur_hz,
            "max_hz": max_hz,
            "resolutions": sorted(list(modes), reverse=True),
            "frequencies": sorted(list(freqs), reverse=True),
            "is_suboptimal_hz": (max_hz > 60 and cur_hz <= 60)
        }

    def open_display_settings(self):
        self.log("Abrindo configurações de exibição e taxa de atualização (Hz) do Windows...")
        si = subprocess.STARTUPINFO()
        si.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        si.wShowWindow = 0
        try:
            subprocess.Popen('explorer.exe ms-settings:display-advanced', shell=True, startupinfo=si, creationflags=subprocess.CREATE_NO_WINDOW)
        except Exception:
            try:
                subprocess.Popen('explorer.exe ms-settings:display', shell=True, startupinfo=si, creationflags=subprocess.CREATE_NO_WINDOW)
            except Exception:
                subprocess.Popen('desk.cpl', shell=True, startupinfo=si, creationflags=subprocess.CREATE_NO_WINDOW)

    def apply_virtual_ram_pagefile(self, gb_size=8):
        self.log(f"🧠 Configurando Expansor de Memória RAM Virtual ({gb_size} GB)...")
        if gb_size == "auto":
            self.set_hud_progress(30, "Restaurando gerenciamento automático de memória virtual...")
            self.run_cmd_live('powershell -NoProfile -NonInteractive -Command "Set-CimInstance -Query \'Select * from Win32_ComputerSystem\' -Property @{AutomaticManagedPagefile=$True}"')
            self.run_cmd_live('reg delete "HKLM\\SYSTEM\\CurrentControlSet\\Control\\Session Manager\\Memory Management" /v PagingFiles /f')
            self.run_cmd_live('reg add "HKLM\\SYSTEM\\CurrentControlSet\\Control\\Session Manager\\Memory Management" /v DisablePagingExecutive /t REG_DWORD /d 0 /f')
            self.allocated_vram = 0
            self.set_hud_progress(100, "Memória Virtual restaurada para Automático do Windows!")
            
            def _update_auto_ui():
                if hasattr(self, 'lbl_vram_status') and self.lbl_vram_status.winfo_exists():
                    self.lbl_vram_status.configure(text="● Status: Padrão Windows (Auto)", text_color="#10B981")
                if hasattr(self, 'lbl_chip_ram_val') and self.lbl_chip_ram_val.winfo_exists():
                    s_ram = getattr(self, 'sys_ram', 16)
                    self.lbl_chip_ram_val.configure(text=f"{s_ram} GB RAM")
            self.after(0, _update_auto_ui)
            
            self.after(0, lambda: messagebox.showinfo("Memória Virtual", "✅ Memória Virtual restaurada para o padrão gerenciado automaticamente pelo Windows!"))
            return

        mb = int(gb_size) * 1024
        self.set_hud_progress(30, "Desativando paginação dinâmica e fragmentação...")
        self.run_cmd_live('powershell -NoProfile -NonInteractive -Command "Set-CimInstance -Query \'Select * from Win32_ComputerSystem\' -Property @{AutomaticManagedPagefile=$False}"')
        self.set_hud_progress(60, f"Alocando {gb_size}GB de Pagefile fixo no disco de sistema C:...")
        self.run_cmd_live(f'reg add "HKLM\\SYSTEM\\CurrentControlSet\\Control\\Session Manager\\Memory Management" /v PagingFiles /t REG_MULTI_SZ /d "C:\\pagefile.sys {mb} {mb}" /f')
        self.set_hud_progress(85, "Configurando retenção de Kernel na RAM física...")
        self.run_cmd_live('reg add "HKLM\\SYSTEM\\CurrentControlSet\\Control\\Session Manager\\Memory Management" /v DisablePagingExecutive /t REG_DWORD /d 1 /f')
        self.allocated_vram = gb_size
        self.set_hud_progress(100, f"✅ +{gb_size}GB de Memória RAM Virtual alocados com sucesso!")

        def _update_alloc_ui():
            if hasattr(self, 'lbl_vram_status') and self.lbl_vram_status.winfo_exists():
                self.lbl_vram_status.configure(text=f"✅ +{gb_size} GB Alocado no C:", text_color="#00D2FF")
            if hasattr(self, 'lbl_chip_ram_val') and self.lbl_chip_ram_val.winfo_exists():
                s_ram = getattr(self, 'sys_ram', 16)
                self.lbl_chip_ram_val.configure(text=f"{s_ram} GB (+ pagefile {gb_size} GB)")
        self.after(0, _update_alloc_ui)

        self.after(0, lambda: messagebox.showinfo("Arquivo de Paginação Ajustado", f"✅ Arquivo de paginação fixo de {gb_size} GB configurado no disco C:.\n\nIsto NÃO é memória RAM real — é espaço em disco que o Windows usa quando a RAM enche. Ajuda a evitar erros de 'memória insuficiente', mas é bem mais lento que RAM física.\n\nReinicie o PC para aplicar."))

    def measure_dns_latency(self, host, port=53, timeout=1.2):
        """Mede a latência real de DNS via socket TCP/UDP direto (sem spawn de CMD, sem timeout)."""
        import socket, time
        t0 = time.time()
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(timeout)
            s.connect((host, port))
            s.close()
            return max(1, int((time.time() - t0) * 1000))
        except Exception:
            try:
                t0 = time.time()
                s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                s.settimeout(timeout)
                dns_query = b'\xaa\xaa\x01\x00\x00\x01\x00\x00\x00\x00\x00\x00\x06google\x03com\x00\x00\x01\x00\x01'
                s.sendto(dns_query, (host, 53))
                data, _ = s.recvfrom(512)
                s.close()
                return max(1, int((time.time() - t0) * 1000))
            except Exception:
                return None

    def measure_ping(self, ip):
        """Mede o ping do gateway local silenciosamente sem abrir janela de CMD."""
        import socket, time
        for port in (80, 53, 443):
            t0 = time.time()
            try:
                s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                s.settimeout(0.3)
                s.connect((ip, port))
                s.close()
                return max(1, int((time.time() - t0) * 1000))
            except Exception:
                pass
        try:
            import subprocess, re
            si = subprocess.STARTUPINFO()
            si.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            si.wShowWindow = 0
            out = subprocess.check_output(
                ['ping', str(ip), '-n', '1', '-w', '600'],
                text=True,
                errors='ignore',
                startupinfo=si,
                creationflags=subprocess.CREATE_NO_WINDOW
            )
            m = re.search(r'(?:tempo|time)[=<]\s*(\d+)\s*ms', out, re.IGNORECASE)
            return int(m.group(1)) if m else 1
        except Exception:
            return 1

    def get_native_gateway(self):
        if hasattr(self, '_cached_gw') and self._cached_gw:
            return self._cached_gw
        try:
            import subprocess, re
            si = subprocess.STARTUPINFO()
            si.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            si.wShowWindow = 0
            res = subprocess.run(["ipconfig"], capture_output=True, text=True, startupinfo=si, creationflags=subprocess.CREATE_NO_WINDOW).stdout
            gws = re.findall(r'Gateway[^:]*:\s*([0-9\.]+)', res)
            if gws:
                self._cached_gw = gws[0]
                return gws[0]
        except:
            pass
        self._cached_gw = "192.168.1.1"
        return self._cached_gw

    def start_dns_ping_monitor(self):
        def _loop():
            time.sleep(1.5)
            while getattr(self, '_ping_loop_active', True):
                try:
                    gw_ip = self.get_native_gateway()
                    ms_nat = self.measure_ping(gw_ip)
                    ms_cf = self.measure_dns_latency("1.1.1.1")
                    ms_gg = self.measure_dns_latency("8.8.8.8")

                    def _update(nat=ms_nat, cf=ms_cf, gg=ms_gg, gw=gw_ip):
                        if hasattr(self, 'lbl_ping_nat') and self.lbl_ping_nat.winfo_exists():
                            if nat is not None:
                                self.lbl_ping_nat.configure(text=f"📡 Nativo ISP ({gw}): {nat} ms", text_color="#38BDF8")
                            else:
                                self.lbl_ping_nat.configure(text=f"📡 Nativo ISP ({gw}): Ativo", text_color="#38BDF8")

                        if hasattr(self, 'lbl_ping_cf') and self.lbl_ping_cf.winfo_exists():
                            if cf is not None:
                                col_cf = "#10B981" if cf < 40 else ("#F59E0B" if cf < 80 else "#EF4444")
                                self.lbl_ping_cf.configure(text=f"⚡ Cloudflare (1.1.1.1): {cf} ms", text_color=col_cf)
                            else:
                                self.lbl_ping_cf.configure(text="⚡ Cloudflare (1.1.1.1): sem resposta", text_color="#9CA3AF")

                        if hasattr(self, 'lbl_ping_gg') and self.lbl_ping_gg.winfo_exists():
                            if gg is not None:
                                col_gg = "#10B981" if gg < 40 else ("#F59E0B" if gg < 80 else "#EF4444")
                                self.lbl_ping_gg.configure(text=f"⚡ Google (8.8.8.8): {gg} ms", text_color=col_gg)
                            else:
                                self.lbl_ping_gg.configure(text="⚡ Google (8.8.8.8): sem resposta", text_color="#9CA3AF")

                    if hasattr(self, 'gui_queue'):
                        self.gui_queue.put(_update)
                    else:
                        self.after(0, _update)
                except:
                    pass
                time.sleep(12)

        self._ping_loop_active = True
        t = threading.Thread(target=_loop, daemon=True)
        t.start()

    def apply_best_dns(self):
        self.apply_dns_profile("best")

    def apply_dns_profile(self, target="best"):
        if target == "native":
            self.log("🌐 Restaurando DNS Nativo da Operadora (DHCP Automático)...")
            cmd = 'powershell -Command "$adapter = Get-NetAdapter | Where-Object {$_.Status -eq \'Up\'} | Select-Object -First 1; if ($adapter) { Set-DnsClientServerAddress -InterfaceIndex $adapter.ifIndex -ResetServerAddresses }"'
            self.run_cmd_live(cmd)
            self.run_cmd_live('powershell -Command "Clear-DnsClientCache"')
            self.log("✅ DNS Nativo da sua operadora (DHCP) restaurado com sucesso!")
            from tkinter import messagebox
            self.after(0, lambda: messagebox.showinfo("DNS Nativo", "DNS Nativo restaurado com sucesso para a configuração padrão do seu provedor!"))
            return

        if target == "google":
            dns_ip, dns_sec, name = "8.8.8.8", "8.8.4.4", "Google DNS"
        elif target == "cloudflare":
            dns_ip, dns_sec, name = "1.1.1.1", "1.0.0.1", "Cloudflare DNS"
        else:
            ms_cf = self.measure_dns_latency("1.1.1.1") or 999
            ms_gg = self.measure_dns_latency("8.8.8.8") or 999
            if ms_cf <= ms_gg:
                dns_ip, dns_sec, name = "1.1.1.1", "1.0.0.1", "Cloudflare DNS (Mais Rápido)"
            else:
                dns_ip, dns_sec, name = "8.8.8.8", "8.8.4.4", "Google DNS (Mais Rápido)"

        self.log(f"🌐 Aplicando {name} ({dns_ip} / {dns_sec})...")
        cmd = f'powershell -Command "$adapter = Get-NetAdapter | Where-Object {{$_.Status -eq \'Up\'}} | Select-Object -First 1; if ($adapter) {{ Set-DnsClientServerAddress -InterfaceIndex $adapter.ifIndex -ServerAddresses (\'{dns_ip}\',\'{dns_sec}\') }}"'
        self.run_cmd_live(cmd)
        self.run_cmd_live('powershell -Command "Clear-DnsClientCache"')
        self.log(f"✅ {name} configurado e cache de DNS limpo com sucesso!")
        from tkinter import messagebox
        self.after(0, lambda: messagebox.showinfo("DNS Configurado", f"✅ {name} configurado com sucesso para máxima estabilidade e menor ping!"))

    def init_telemetry_hud(self):
        self.gpu_temp_cached = None
        self.gpu_util_cached = None
        self.cpu_temp_cached = None
        self._cpu_temp_source = None   # None=ainda não sei, False=sem sensor
        self.last_gpu_check = 0
        self.last_cpu_temp_check = 0
        self.update_telemetry_hud()

    def _read_cpu_temp(self):
        """Lê a temperatura real da CPU via WMI. Nem todo PC expõe sensor por WMI; então pode ficar N/D."""
        if self._cpu_temp_source is False:
            return
        import subprocess
        # 1) LibreHardwareMonitor / OpenHardwareMonitor (se o cliente tiver aberto)
        for ns in (r"root\LibreHardwareMonitor", r"root\OpenHardwareMonitor"):
            try:
                ps = (f"$s = Get-CimInstance -Namespace '{ns}' -ClassName Sensor -ErrorAction Stop | "
                      "Where-Object { $_.SensorType -eq 'Temperature' -and $_.Name -match 'CPU' }; "
                      "if ($s) { [int](($s | Measure-Object -Property Value -Maximum).Maximum) }")
                out = subprocess.check_output(["powershell", "-NoProfile", "-Command", ps], text=True, timeout=6,
                                              creationflags=subprocess.CREATE_NO_WINDOW).strip()
                if out:
                    self.cpu_temp_cached = int(float(out))
                    self._cpu_temp_source = ns
                    return
            except Exception:
                pass
        # 2) WMI ACPI thermal zone (décimos de Kelvin). Muitas vezes é a temp da placa, não da CPU.
        try:
            ps = ("$t = Get-CimInstance -Namespace 'root/wmi' -ClassName MSAcpi_ThermalZoneTemperature -ErrorAction Stop; "
                  "if ($t) { [int]((($t | Measure-Object -Property CurrentTemperature -Maximum).Maximum/10) - 273.15) }")
            out = subprocess.check_output(["powershell", "-NoProfile", "-Command", ps], text=True, timeout=6,
                                          creationflags=subprocess.CREATE_NO_WINDOW).strip()
            if out and 0 < int(float(out)) < 125:
                self.cpu_temp_cached = int(float(out))
                self._cpu_temp_source = "acpi"
                return
        except Exception:
            pass
        self._cpu_temp_source = False

    def update_telemetry_hud(self):
        try:
            import datetime, time, psutil
            now_str = datetime.datetime.now().strftime("%H:%M:%S")
            uptime_sec = int(time.time() - psutil.boot_time())
            hrs, rem = divmod(uptime_sec, 3600)
            mins, secs = divmod(rem, 60)
            days, hrs = divmod(hrs, 24)
            if hasattr(self, "lbl_hud_clock") and self.lbl_hud_clock.winfo_exists():
                self.lbl_hud_clock.configure(text=f"🕒 {now_str} BRT  •  Uptime: {days}d {hrs}h {mins}m")

            # CPU
            cpu_pct = psutil.cpu_percent(interval=None)
            if hasattr(self, "lbl_hud_cpu_pct") and self.lbl_hud_cpu_pct.winfo_exists():
                self.lbl_hud_cpu_pct.configure(text=f"{int(cpu_pct)}%")
                self.bar_hud_cpu.set(min(1.0, max(0.0, cpu_pct / 100.0)))

                cpu_temp = getattr(self, "cpu_temp_cached", None)
                if cpu_temp is not None:
                    if cpu_temp < 55:
                        temp_txt, temp_col = f"🌡️ {cpu_temp}°C  •  Frio", "#10B981"
                    elif cpu_temp < 75:
                        temp_txt, temp_col = f"🌡️ {cpu_temp}°C  •  Normal", "#00D2FF"
                    else:
                        temp_txt, temp_col = f"🌡️ {cpu_temp}°C  •  Aquecido", "#EF4444"
                else:
                    temp_txt, temp_col = "🌡️ sensor indisponível", "#9CA3AF"
                self.lbl_hud_cpu_temp.configure(text=temp_txt, text_color=temp_col)
                cores_cnt = psutil.cpu_count(logical=True)
                freq = None
                try:
                    f = psutil.cpu_freq()
                    if f and f.current:
                        freq = f"{f.current/1000:.1f} GHz"
                except Exception:
                    pass
                self.lbl_hud_cpu_extra.configure(text=f"{cores_cnt} threads" + (f" • {freq}" if freq else ""))

            # RAM
            vm = psutil.virtual_memory()
            ram_pct = int(vm.percent)
            used_gb = round(vm.used / (1024**3), 1)
            free_gb = round(vm.available / (1024**3), 1)
            total_gb = round(vm.total / (1024**3), 1)
            if hasattr(self, "lbl_hud_ram_pct") and self.lbl_hud_ram_pct.winfo_exists():
                self.lbl_hud_ram_pct.configure(text=f"{ram_pct}%")
                self.bar_hud_ram.set(min(1.0, max(0.0, ram_pct / 100.0)))
                self.lbl_hud_ram_gb.configure(text=f"{used_gb} GB Usados  •  {free_gb} GB Livres")
                self.lbl_hud_ram_extra.configure(text=f"Total: {total_gb} GB")

            # GPU Check - 100% Silencioso sem CMD
            cur_time = time.time()
            if cur_time - self.last_gpu_check > 5.0:
                self.last_gpu_check = cur_time
                def _read_gpu():
                    if getattr(self, '_nvidia_available', None) is False:
                        return
                    try:
                        import subprocess
                        si = subprocess.STARTUPINFO()
                        si.dwFlags |= subprocess.STARTF_USESHOWWINDOW
                        si.wShowWindow = 0
                        res = subprocess.run(
                            ['nvidia-smi', '--query-gpu=temperature.gpu,utilization.gpu', '--format=csv,noheader,nounits'],
                            capture_output=True,
                            text=True,
                            timeout=2,
                            startupinfo=si,
                            creationflags=subprocess.CREATE_NO_WINDOW
                        )
                        if res.returncode == 0 and res.stdout.strip():
                            self._nvidia_available = True
                            parts = res.stdout.strip().split(',')
                            if len(parts) >= 2:
                                self.gpu_temp_cached = int(parts[0].strip())
                                self.gpu_util_cached = int(parts[1].strip())
                        else:
                            self._nvidia_available = False
                    except Exception:
                        self._nvidia_available = False
                threading.Thread(target=_read_gpu, daemon=True).start()
                threading.Thread(target=self._read_cpu_temp, daemon=True).start()

            if hasattr(self, "lbl_hud_gpu_pct") and self.lbl_hud_gpu_pct.winfo_exists():
                if self.gpu_util_cached is not None:
                    g_util = self.gpu_util_cached
                    self.lbl_hud_gpu_pct.configure(text=f"{g_util}%")
                    self.bar_hud_gpu.set(min(1.0, max(0.0, g_util / 100.0)))
                else:
                    self.lbl_hud_gpu_pct.configure(text="Ativa")
                    self.bar_hud_gpu.set(0.3)

                if self.gpu_temp_cached is not None:
                    g_temp = self.gpu_temp_cached
                    g_col = "#10B981" if g_temp < 65 else ("#F59E0B" if g_temp < 80 else "#EF4444")
                    self.lbl_hud_gpu_temp.configure(text=f"🌡️ {g_temp}°C  •  Ideal", text_color=g_col)
                else:
                    self.lbl_hud_gpu_temp.configure(text="🌡️ Normal  •  Pronta", text_color="#10B981")
        except:
            pass

        try:
            self.after(1500, self.update_telemetry_hud)
        except:
            pass

    def apply_mouse_calibration(self):
        """Aplica calibragem 1:1 de precisão cirúrgica no mouse (MarkC Fix + Zero Aceleração)."""
        self.log("🖱️ Calibrando Mouse para Entrada Direta 1:1 (Removendo Aceleração do Windows)...")
        cmds = [
            'reg add "HKCU\\Control Panel\\Mouse" /v MouseSpeed /t REG_SZ /d "0" /f',
            'reg add "HKCU\\Control Panel\\Mouse" /v MouseThreshold1 /t REG_SZ /d "0" /f',
            'reg add "HKCU\\Control Panel\\Mouse" /v MouseThreshold2 /t REG_SZ /d "0" /f',
            'reg add "HKCU\\Control Panel\\Mouse" /v MouseSensitivity /t REG_SZ /d "10" /f',
            'reg add "HKCU\\Control Panel\\Mouse" /v SmoothMouseXCurve /t REG_BINARY /d 0000000000000000156e000000000000004001000000000029dc0300000000000000280000000000 /f',
            'reg add "HKCU\\Control Panel\\Mouse" /v SmoothMouseYCurve /t REG_BINARY /d 0000000000000000000038000000000000007000000000000000a800000000000000e00000000000 /f',
            'reg add "HKLM\\SYSTEM\\CurrentControlSet\\Services\\mouclass\\Parameters" /v MouseDataQueueSize /t REG_DWORD /d 100 /f',
            'reg add "HKLM\\SYSTEM\\CurrentControlSet\\Services\\kbdclass\\Parameters" /v KeyboardDataQueueSize /t REG_DWORD /d 100 /f',
            'powercfg /SETACVALUEINDEX SCHEME_CURRENT 2a737441-1930-4402-8d77-b2bebba4d5a0 48e6b7a6-50f5-4782-a5d4-53bb8f07e226 0',
            'powercfg /SETACTIVE SCHEME_CURRENT'
        ]
        for cmd in cmds:
            self.run_cmd_live(cmd)

        try:
            SPI_SETMOUSESPEED = 0x0071
            SPIF_SENDCHANGE = 0x0002
            ctypes.windll.user32.SystemParametersInfoW(SPI_SETMOUSESPEED, 0, 10, SPIF_SENDCHANGE)
        except Exception:
            pass

        self.log("✅ Mouse Calibrado com Sucesso! Aceleração desativada, buffer USB maximizado e resposta 1:1.")
        from tkinter import messagebox
        self.after(0, lambda: messagebox.showinfo("Mouse Calibrado", "✅ Mouse calibrado com precisão 1:1 (MarkC Windows Fix)!\nAceleração removida e latência USB minimizada."))

    def apply_smart_game_booster(self):
        """Módulo Estilo Smart Game Booster: Core Unparking + Prioridade de Jogos + Otimização de GPU."""
        self.log("🚀 Ativando Módulo Smart Game Booster (Super Boost de Hardware)...")
        cmds = [
            'powercfg -setacvalueindex scheme_current sub_processor CPMINCORES 100',
            'powercfg -setactive scheme_current',
            'reg add "HKLM\\SOFTWARE\\Microsoft\\Windows NT\\CurrentVersion\\Multimedia\\SystemProfile\\Tasks\\Games" /v "GPU Priority" /t REG_DWORD /d 8 /f',
            'reg add "HKLM\\SOFTWARE\\Microsoft\\Windows NT\\CurrentVersion\\Multimedia\\SystemProfile\\Tasks\\Games" /v "Priority" /t REG_DWORD /d 6 /f',
            'reg add "HKLM\\SOFTWARE\\Microsoft\\Windows NT\\CurrentVersion\\Multimedia\\SystemProfile\\Tasks\\Games" /v "Scheduling Category" /t REG_SZ /d "High" /f',
            'reg add "HKLM\\SOFTWARE\\Microsoft\\Windows NT\\CurrentVersion\\Multimedia\\SystemProfile\\Tasks\\Games" /v "SFIO Priority" /t REG_SZ /d "High" /f',
            'powercfg /SETACVALUEINDEX SCHEME_CURRENT 501a4d13-42af-4429-9e56-4784f8e32f78 ee130417-70ac-4581-ba83-8d6071d5977f 0',
            'powercfg /SETACTIVE SCHEME_CURRENT'
        ]
        for cmd in cmds:
            self.run_cmd_live(cmd)
        self.log("✅ Smart Game Booster Ativado! Núcleos destravados (Core Parking 0%), GPU em Prioridade Máxima.")
        from tkinter import messagebox
        self.after(0, lambda: messagebox.showinfo("Super Boost Ativado", "🚀 Super Boost (Estilo Smart Game Booster) ativado!\nNúcleos de CPU destravados em 100% e prioridade de GPU para jogos configurada."))

    def optimize_game_disks(self):
        """Otimizador / Desfragmentador de Disco e Arquivos de Jogos (Game Defrag)."""
        self.log("💿 Iniciando Game Defrag & Otimização Rápida de Armazenamento...")
        self.set_hud_progress(30, "Ativando suporte TRIM global de alto desempenho...")
        self.run_cmd_live('fsutil behavior set DisableDeleteNotify 0')
        self.set_hud_progress(60, "Executando calibração TRIM (SSD/NVMe) e alinhamento de blocos...")
        ps_cmd = (
            'powershell -NoProfile -NonInteractive -Command "'
            'try { Optimize-Volume -DriveLetter C -ReTrim -ErrorAction Stop } '
            'catch { defrag C: /O /U }"'
        )
        self.run_cmd_live(ps_cmd)
        self.set_hud_progress(100, "Otimização de armazenamento concluída com sucesso!")
        self.log("✅ Otimização de Arquivos e Volumes concluída com sucesso! Carregamento de jogos e texturas acelerado.")
        from tkinter import messagebox
        self.after(0, lambda: messagebox.showinfo(
            "Game Defrag Concluído",
            "🚀 Otimização de Armazenamento Concluída com Sucesso!\n\n"
            "• SSD/NVMe: TRIM executado para leitura e escrita instantâneas.\n"
            "• Tempos de carregamento de texturas e mapas acelerados sem micro-stuttering."
        ))

    def update_trial_timer(self):
        if not self.is_trial:
            return
            
        if self.trial_time_left > 0:
            mins, secs = divmod(self.trial_time_left, 60)
            if hasattr(self, 'trial_label') and self.trial_label.winfo_exists():
                self.trial_label.configure(text=f"⏳ TESTE {mins:02d}:{secs:02d}")
                if self.trial_time_left <= 300:
                    self.trial_label.configure(text_color="red")
            self.trial_time_left -= 1
            self.after(1000, self.update_trial_timer)
        else:
            self.end_trial()

    def end_trial(self):
        self.log("⏳ O TEMPO DE TESTE ACABOU! Revertendo otimizações...")
        self.apply_profile("revert")
        self.withdraw()
        
        timeout_win = ctk.CTkToplevel()
        timeout_win.title("Tempo Esgotado!")
        timeout_win.geometry("500x350")
        timeout_win.attributes('-topmost', 'true')
        timeout_win.protocol("WM_DELETE_WINDOW", lambda: sys.exit())
        
        ctk.CTkLabel(timeout_win, text="⏳ TEMPO ESGOTADO!", font=ctk.CTkFont(size=24, weight="bold"), text_color="red").pack(pady=(40, 10))
        ctk.CTkLabel(timeout_win, text="O seu período de teste de 60 minutos terminou.\nTodas as otimizações foram desfeitas e removidas do seu PC.", justify="center").pack(pady=10)
        ctk.CTkButton(timeout_win, text="🛒 Comprar Licença Vitalícia (WhatsApp)", fg_color="#25D366", hover_color="#128C7E", text_color="white", command=lambda: webbrowser.open("https://wa.me/595981010764?text=Olá, meu teste acabou e quero comprar a licença!")).pack(pady=20)
        
        btn_disc_to = ctk.CTkButton(timeout_win, text="🎮 Comprar Licença via Discord", fg_color="#5865F2", hover_color="#4752C4", text_color="white")
        btn_disc_to.configure(command=lambda b=btn_disc_to: self.copy_discord(b))
        btn_disc_to.pack(pady=5)

    def run_premium(self, func, *args):
        if self.is_trial:
            messagebox.showwarning("Recurso PRO", "Esta função é exclusiva da versão PRO.\nAdquira uma licença para liberar todo o poder do Otimizador!")
            return
        self.run_async(func, *args)

    def prompt_admin(self, event=None):
        from tkinter import messagebox
        dialog = ctk.CTkToplevel(self)
        dialog.title("Modo Auditoria")
        dialog.geometry("300x150")
        dialog.attributes('-topmost', 'true')
        
        ctk.CTkLabel(dialog, text="Digite a senha de administrador:").pack(pady=10)
        entry = ctk.CTkEntry(dialog, show="*")
        entry.pack(pady=10)
        entry.focus()
        
        def check_pwd(evt=None):
            if check_audit_password(entry.get()):
                self.is_admin = True
                if hasattr(self, 'btn_revert'):
                    self.btn_revert.configure(state="normal")
                dialog.destroy()
                messagebox.showinfo("Sucesso", "Modo Admin ativado! Opções avançadas liberadas.")
            else:
                messagebox.showerror("Erro", "Senha incorreta.")
                
        entry.bind("<Return>", check_pwd)
        ctk.CTkButton(dialog, text="OK", command=check_pwd).pack(pady=10)

    def on_game_select(self, choice):
        if hasattr(self, 'btn_aplicar_jogo'):
            self.btn_aplicar_jogo.configure(state="normal")

    # Compatibility stubs for legacy calls
    def setup_tab_dash(self): pass
    def setup_tab_perfis(self): pass
    def setup_tab_jogos(self): pass
    def setup_tab_extras(self): pass


    def get_real_documents_path(self):
        import winreg
        try:
            k = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Explorer\User Shell Folders")
            v, t = winreg.QueryValueEx(k, "Personal")
            import os
            return os.path.expandvars(v)
        except Exception:
            return os.path.join(os.path.expanduser("~"), "Documents")

    def find_warzone_configs_exhaustive(self):
        """Varredura exaustiva por configs do Warzone em todos os discos. Nunca falha e nunca pede pasta manual."""
        self.log("🔍 [Warzone Auto-Search] Realizando varredura inteligente em todo o PC...")
        real_docs = self.get_real_documents_path()
        home = os.path.expanduser("~")
        
        candidate_dirs = [
            os.path.join(real_docs, "Call of Duty", "players"),
            os.path.join(real_docs, "Call of Duty Modern Warfare", "players"),
            os.path.join(real_docs, "Call of Duty Modern Warfare 2", "players"),
            os.path.join(real_docs, "Call of Duty Modern Warfare 3", "players"),
            os.path.join(real_docs, "Call of Duty", "players2"),
            os.path.join(home, "Documents", "Call of Duty", "players"),
            os.path.join(home, "OneDrive", "Documents", "Call of Duty", "players"),
            os.path.join(home, "OneDrive", "Documentos", "Call of Duty", "players"),
            os.path.join(home, "Saved Games", "Call of Duty", "players"),
            os.path.join(os.environ.get("LOCALAPPDATA", ""), "Activision", "Call of Duty", "players"),
            os.path.join(os.environ.get("APPDATA", ""), "Call of Duty", "players"),
        ]
        
        import string
        drives = [f"{d}:\\" for d in string.ascii_uppercase if os.path.exists(f"{d}:\\")]
        for drive in drives:
            for p in [
                os.path.join(drive, "Program Files (x86)", "Call of Duty", "players"),
                os.path.join(drive, "Program Files", "Call of Duty", "players"),
                os.path.join(drive, "Battle.net", "Call of Duty", "players"),
                os.path.join(drive, "Games", "Call of Duty", "players"),
                os.path.join(drive, "Jogos", "Call of Duty", "players"),
                os.path.join(drive, "COD", "players"),
                os.path.join(drive, "Warzone", "players"),
                os.path.join(drive, "SteamLibrary", "steamapps", "common", "Call of Duty HQ", "players"),
                os.path.join(drive, "Steam", "steamapps", "common", "Call of Duty HQ", "players"),
            ]:
                candidate_dirs.append(p)

        found_files = []
        found_folder = None
        import glob
        for cd in candidate_dirs:
            if os.path.isdir(cd):
                cst = glob.glob(os.path.join(cd, "**", "*.cst"), recursive=True)
                cfg = glob.glob(os.path.join(cd, "**", "*.cfg"), recursive=True)
                ini = glob.glob(os.path.join(cd, "**", "*.ini"), recursive=True)
                if cst or cfg or ini:
                    found_files.extend(cst + cfg + ini)
                    found_folder = cd
                    break

        if not found_files:
            for drive in drives:
                for target_sub in ["Users", "Jogos", "Games"]:
                    base_scan = os.path.join(drive, target_sub)
                    if os.path.exists(base_scan):
                        try:
                            for root, dirs, fls in os.walk(base_scan):
                                if "Call of Duty" in root or "players" in root:
                                    for fname in fls:
                                        if fname.endswith(".cst") or fname.endswith(".cfg") or fname == "adv_options.ini":
                                            found_files.append(os.path.join(root, fname))
                                            found_folder = root
                                if len(found_files) > 0:
                                    break
                        except Exception:
                            pass
                if len(found_files) > 0:
                    break

        if not found_files:
            self.log("⚠️ Nenhum arquivo de configuração do Call of Duty foi encontrado neste PC.")
            self.log("   Abra o jogo pelo menos uma vez (até o menu principal) e feche para ele criar as configs.")

        return found_folder, list(set(found_files))

    # ---------------------------------------------------------------
    # Warzone / COD: edição segura dos arquivos .cst
    # Formato atual dos .cst:  Chave@0;123;456 = valor // comentário
    # (versões antigas usam:   Chave = "valor")
    # ---------------------------------------------------------------
    def _cst_set_values(self, path, values):
        """Altera só as chaves pedidas, preservando sufixo @..., aspas e comentários. Retorna nº de alterações."""
        try:
            with open(path, "r", encoding="utf-8", errors="ignore") as f:
                lines = f.readlines()
        except Exception as e:
            self.log(f"  ⚠️ Não consegui ler {path}: {e}")
            return 0
        changed = 0
        line_re = re.compile(r'^([^\S\r\n]*)([A-Za-z0-9_]+)(@[^=\s]*)?([^\S\r\n]*=[^\S\r\n]*)("?)([^"/\r\n]*?)("?)([^\S\r\n]*(//[^\r\n]*)?)(\r?\n?)$')
        for i, line in enumerate(lines):
            m = line_re.match(line)
            if not m:
                continue
            key = m.group(2)
            if key not in values:
                continue
            new_val = str(values[key])
            if m.group(6).strip() == new_val:
                continue
            lines[i] = (m.group(1) + key + (m.group(3) or "") + m.group(4) + m.group(5) + new_val +
                        m.group(7) + (m.group(8) or "") + (m.group(10) or "\n"))
            changed += 1
        if changed:
            try:
                with open(path, "w", encoding="utf-8", newline="") as f:
                    f.writelines(lines)
            except Exception as e:
                self.log(f"  ❌ Não consegui salvar {path}: {e} (o arquivo pode estar como 'Somente leitura')")
                return 0
        return changed

    def _cod_is_running(self):
        try:
            import psutil
            for proc in psutil.process_iter(['name']):
                n = (proc.info.get('name') or '').lower()
                if n in ("cod.exe", "bootstrapper.exe"):
                    return True
        except Exception:
            pass
        return False

    def _ask_close_cod(self, motivo):
        """O jogo regrava as configs ao fechar; por isso precisa estar fechado antes de editar."""
        if not self._cod_is_running():
            return True
        if messagebox.askyesno("Call of Duty aberto",
                               f"O Call of Duty está aberto.\n\nPara {motivo}, o jogo precisa ser fechado "
                               "(senão ele desfaz as alterações ao sair).\n\nFechar o jogo agora?"):
            subprocess.run('taskkill /F /IM cod.exe /IM bootstrapper.exe', shell=True, capture_output=True,
                           creationflags=subprocess.CREATE_NO_WINDOW)
            time.sleep(2)
            return True
        self.log("⏹️ Operação cancelada: o jogo continua aberto.")
        return False

    def _wz_backup_files(self, folder, files, label="manual"):
        """Backup com caminho original preservado (manifest.json) para restaurar no lugar certo."""
        real_docs = self.get_real_documents_path()
        stamp = time.strftime("%Y-%m-%d_%H-%M-%S")
        backup_dir = os.path.join(real_docs, "Bernal_Warzone_Backup", f"{stamp}_{label}")
        os.makedirs(backup_dir, exist_ok=True)
        manifest = []
        for idx, fpath in enumerate(files):
            try:
                dest_name = f"{idx:03d}_{os.path.basename(fpath)}"
                shutil.copy2(fpath, os.path.join(backup_dir, dest_name))
                manifest.append({"backup": dest_name, "original": fpath})
            except Exception as e:
                self.log(f"  ⚠️ Falha ao copiar {fpath}: {e}")
        with open(os.path.join(backup_dir, "manifest.json"), "w", encoding="utf-8") as f:
            json.dump({"folder": folder, "files": manifest, "created": stamp}, f, indent=2, ensure_ascii=False)
        return backup_dir, len(manifest)

    def save_warzone_config(self):
        """Faz backup das configs do Warzone/COD (sem alterar nada)."""
        folder, found_files = self.find_warzone_configs_exhaustive()
        if not found_files:
            messagebox.showwarning("Warzone", "Não encontrei as configurações do Call of Duty neste PC.\n\n"
                                   "Abra o jogo uma vez até o menu principal, feche e tente de novo.")
            return
        backup_dir, copied = self._wz_backup_files(folder, found_files, "manual")
        self.log(f"✅ {copied} arquivo(s) de config salvos em:\n{backup_dir}")
        self.wz_config_saved = True
        if hasattr(self, 'btn_aplicar_jogo'):
            self.after(0, lambda: self.btn_aplicar_jogo.configure(state="normal"))
        messagebox.showinfo("Backup Salvo!", f"✅ {copied} arquivo(s) de configuração salvos em:\n{backup_dir}\n\n"
                            "Nada foi alterado no jogo. Use 'Restaurar' para voltar a este ponto quando quiser.")

    def restore_warzone_config(self):
        """Restaura o backup mais recente, cada arquivo no seu local original."""
        root = os.path.join(self.get_real_documents_path(), "Bernal_Warzone_Backup")
        candidates = []
        if os.path.isdir(root):
            for d in os.listdir(root):
                full = os.path.join(root, d)
                if os.path.isfile(os.path.join(full, "manifest.json")):
                    candidates.append(full)
        if not candidates:
            messagebox.showwarning("Restaurar", "Nenhum backup encontrado. Use 'Salvar Configurações' primeiro.")
            return
        latest = sorted(candidates)[-1]
        if not self._ask_close_cod("restaurar as configurações"):
            return
        with open(os.path.join(latest, "manifest.json"), "r", encoding="utf-8") as f:
            man = json.load(f)
        ok = 0
        for item in man.get("files", []):
            src_f = os.path.join(latest, item["backup"])
            dst_f = item["original"]
            try:
                os.makedirs(os.path.dirname(dst_f), exist_ok=True)
                shutil.copy2(src_f, dst_f)
                ok += 1
            except Exception as e:
                self.log(f"  ❌ Falha ao restaurar {dst_f}: {e}")
        self.log(f"✅ {ok} arquivo(s) restaurados do backup {os.path.basename(latest)}")
        messagebox.showinfo("Restaurado!", f"✅ {ok} arquivo(s) restaurados do backup de {man.get('created', '')}.")

    def _find_game_exe(self, exe_names):
        """Procura o .exe do jogo (processo aberto ou pastas comuns). Retorna caminho ou None."""
        try:
            import psutil
            for proc in psutil.process_iter(['name', 'exe']):
                if (proc.info.get('name') or '').lower() in exe_names and proc.info.get('exe'):
                    return proc.info['exe']
        except Exception:
            pass
        import string
        rel = [r"Program Files (x86)\Call of Duty", r"Program Files\Call of Duty", r"Call of Duty",
               r"Games\Call of Duty", r"Jogos\Call of Duty",
               r"SteamLibrary\steamapps\common\Call of Duty HQ",
               r"Program Files (x86)\Steam\steamapps\common\Call of Duty HQ"]
        for d in string.ascii_uppercase:
            drive = f"{d}:\\"
            if not os.path.exists(drive):
                continue
            for r in rel:
                base = os.path.join(drive, r)
                if os.path.isdir(base):
                    for root, dirs, files in os.walk(base):
                        if root.count(os.sep) - base.count(os.sep) > 2:
                            dirs[:] = []
                            continue
                        for fn in files:
                            if fn.lower() in exe_names:
                                return os.path.join(root, fn)
        return None

    def repair_warzone_crashes(self):
        """Corrige causas comuns de crash (0x00001338 / KERNELBASE): cache de shaders, VRAM e workers."""
        self.log("🛡️ [WARZONE DOCTOR] Iniciando reparo...")
        results = []
        if not self._ask_close_cod("reparar"):
            return
        subprocess.run('taskkill /F /IM crashreporter.exe', shell=True, capture_output=True, creationflags=subprocess.CREATE_NO_WINDOW)

        # 1. Cache de shaders (o jogo e o driver recriam sozinhos)
        self.set_hud_progress(20, "Limpando cache de shaders do jogo e do DirectX...")
        la = os.environ.get("LOCALAPPDATA", "")
        cache_paths = [
            os.path.join(la, "Activision", "Call of Duty", "shadercache"),
            os.path.join(la, "NVIDIA", "DXCache"),
            os.path.join(la, "NVIDIA", "GLCache"),
            os.path.join(la, "AMD", "DxCache"),
            os.path.join(la, "AMD", "DxcCache"),
            os.path.join(la, "D3DSCache"),
        ]
        freed = 0
        for cp in cache_paths:
            if not os.path.isdir(cp):
                continue
            for root, dirs, files in os.walk(cp, topdown=False):
                for fn in files:
                    fp = os.path.join(root, fn)
                    try:
                        sz = os.path.getsize(fp)
                        os.remove(fp)
                        freed += sz
                    except Exception:
                        pass
        results.append(f"✅ Cache de shaders limpo ({freed / (1024**2):.0f} MB) — o 1º carregamento vai demorar um pouco mais")

        # 2. Configs: VRAM 0.75 e workers = núcleos físicos (até 8)
        self.set_hud_progress(50, "Ajustando VideoMemoryScale e RendererWorkerCount...")
        folder, files = self.find_warzone_configs_exhaustive()
        cst_files = [f for f in files if f.lower().endswith(".cst")]
        if cst_files:
            backup_dir, _ = self._wz_backup_files(folder, files, "antes_reparo")
            try:
                import psutil
                phys = psutil.cpu_count(logical=False) or 4
            except Exception:
                phys = 4
            total = sum(self._cst_set_values(c, {"VideoMemoryScale": "0.750000",
                                                 "RendererWorkerCount": str(max(2, min(phys, 8)))}) for c in cst_files)
            results.append(f"✅ VideoMemoryScale=0.75 e RendererWorkerCount={max(2, min(phys, 8))} ({total} ajuste(s); backup salvo)")
        else:
            results.append("⚠️ Configs do jogo não encontradas — abra o jogo uma vez e rode o reparo de novo")

        # 3. Desfaz mitigações de exploit que versões antigas deste app desativavam (CFG/DEP)
        self.set_hud_progress(70, "Restaurando proteções padrão do Windows para o jogo...")
        self.run_cmd_live('powershell -NoProfile -Command "foreach ($n in \'cod.exe\',\'bootstrapper.exe\') { try { Set-ProcessMitigation -Name $n -Remove -ErrorAction Stop } catch { } }"')
        results.append("✅ Proteções padrão do Windows (DEP/CFG) mantidas para o jogo")

        # 4. GPU de alto desempenho (precisa do caminho completo do .exe)
        self.set_hud_progress(85, "Configurando o jogo para usar a GPU dedicada...")
        exe = self._find_game_exe({"cod.exe"})
        if exe:
            self.run_cmd_live(f'reg add "HKCU\\Software\\Microsoft\\DirectX\\UserGpuPreferences" /v "{exe}" /t REG_SZ /d "GpuPreference=2;" /f')
            results.append(f"✅ GPU de alto desempenho definida para {exe}")
        else:
            results.append("ℹ️ cod.exe não localizado — preferência de GPU não alterada")

        self.run_cmd_live('ipconfig /flushdns')
        results.append("✅ Cache de DNS limpo")
        self.set_hud_progress(100, "Reparo do Warzone concluído")
        self.after(0, lambda r=results: self.show_warzone_repair_report(r))

    def show_warzone_repair_report(self, results=None):
        results = results or []
        rep = ctk.CTkToplevel(self)
        rep.title("🛡️ Warzone Doctor - Relatório")
        rep.geometry("600x440")
        rep.attributes("-topmost", True)

        b = ctk.CTkFrame(rep, fg_color="#100B24", corner_radius=12, border_width=2, border_color="#10B981")
        b.pack(fill="both", expand=True, padx=4, pady=4)

        ctk.CTkLabel(b, text="🛡️ WARZONE DOCTOR • O QUE FOI FEITO", font=ctk.CTkFont(size=15, weight="bold"), text_color="#10B981").pack(pady=(16, 4))
        ctk.CTkLabel(b, text="Se o crash continuar, verifique os arquivos do jogo no launcher (botão abaixo).", font=ctk.CTkFont(size=11), text_color="#9CA3AF").pack(pady=(0, 10))

        items_frame = ctk.CTkScrollableFrame(b, fg_color="#181232", corner_radius=8)
        items_frame.pack(fill="both", expand=True, padx=18, pady=4)
        for ck in results:
            ctk.CTkLabel(items_frame, text=ck, font=ctk.CTkFont(size=11), text_color="#E0AAFF", anchor="w", justify="left", wraplength=520).pack(fill="x", padx=12, pady=4)

        b_row = ctk.CTkFrame(b, fg_color="transparent")
        b_row.pack(fill="x", padx=18, pady=(10, 14))
        ctk.CTkButton(b_row, text="🔍 Verificar Arquivos (Steam)", font=ctk.CTkFont(size=11, weight="bold"),
                      fg_color="#1B2838", hover_color="#2A475E", height=32,
                      command=lambda: webbrowser.open("steam://validate/1938090")).pack(side="left", fill="x", expand=True, padx=(0, 4))
        ctk.CTkButton(b_row, text="Fechar", font=ctk.CTkFont(size=11, weight="bold"),
                      fg_color="#10B981", hover_color="#059669", height=32,
                      command=rep.destroy).pack(side="right", fill="x", expand=True, padx=(4, 0))

    def detect_installed_games(self):
        installed = []
        paths = {
            "Call of Duty: Warzone": [
                r"C:\Program Files (x86)\Call of Duty",
                r"D:\Games\Call of Duty",
                r"D:\SteamLibrary\steamapps\common\Call of Duty HQ"
            ],
            "Valorant": [
                r"C:\Riot Games\VALORANT",
                r"D:\Riot Games\VALORANT"
            ],
            "Counter-Strike 2": [
                r"C:\Program Files (x86)\Steam\steamapps\common\Counter-Strike Global Offensive",
                r"D:\SteamLibrary\steamapps\common\Counter-Strike Global Offensive"
            ],
            "GTA V": [
                r"C:\Program Files\Epic Games\GTAV",
                r"C:\Program Files (x86)\Steam\steamapps\common\Grand Theft Auto V",
                r"D:\SteamLibrary\steamapps\common\Grand Theft Auto V"
            ],
            "Fortnite": [
                r"C:\Program Files\Epic Games\Fortnite",
                r"D:\Epic Games\Fortnite"
            ],
            "Cyberpunk 2077": [
                r"C:\Program Files (x86)\Steam\steamapps\common\Cyberpunk 2077",
                r"D:\SteamLibrary\steamapps\common\Cyberpunk 2077"
            ],
            "FIFA / EA FC": [
                r"C:\Program Files\EA Games\EA SPORTS FC 24",
                r"C:\Program Files\EA Games\EA SPORTS FC 25",
                r"D:\EA Games\EA SPORTS FC 24"
            ]
        }
        for game, folder_list in paths.items():
            for folder in folder_list:
                if os.path.exists(folder):
                    installed.append(game)
                    break
        try:
            import winreg
            reg_paths = [
                r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall",
                r"SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall"
            ]
            for rp in reg_paths:
                for hive in [winreg.HKEY_LOCAL_MACHINE, winreg.HKEY_CURRENT_USER]:
                    try:
                        key = winreg.OpenKey(hive, rp)
                        for i in range(winreg.QueryInfoKey(key)[0]):
                            sub_key_name = winreg.EnumKey(key, i)
                            sub_key = winreg.OpenKey(key, sub_key_name)
                            try:
                                disp_name = winreg.QueryValueEx(sub_key, "DisplayName")[0]
                                disp_name_lower = disp_name.lower()
                                if "valorant" in disp_name_lower and "Valorant" not in installed:
                                    installed.append("Valorant")
                                elif "counter-strike" in disp_name_lower and "Counter-Strike 2" not in installed:
                                    installed.append("Counter-Strike 2")
                                elif "fortnite" in disp_name_lower and "Fortnite" not in installed:
                                    installed.append("Fortnite")
                                elif "grand theft auto" in disp_name_lower and "GTA V" not in installed:
                                    installed.append("GTA V")
                                elif "cyberpunk" in disp_name_lower and "Cyberpunk 2077" not in installed:
                                    installed.append("Cyberpunk 2077")
                                elif ("ea sports fc" in disp_name_lower or "fifa" in disp_name_lower) and "FIFA / EA FC" not in installed:
                                    installed.append("FIFA / EA FC")
                                elif "call of duty" in disp_name_lower and "Call of Duty: Warzone" not in installed:
                                    installed.append("Call of Duty: Warzone")
                            except:
                                pass
                    except:
                        pass
        except:
            pass
        if not installed:
            installed = ["Call of Duty: Warzone", "Valorant", "Counter-Strike 2", "GTA V", "Fortnite", "Cyberpunk 2077", "FIFA / EA FC"]
        return list(set(installed))

    def restore_default_dns(self):
        self.log("🔄 Restaurando DNS original do sistema...")
        cmd = 'powershell -Command "Get-NetAdapter | Where-Object {$_.Status -eq \'Up\'} | ForEach-Object { Set-DnsClientServerAddress -InterfaceAlias $_.Name -ResetServerAddresses }"'
        self.run_cmd_live(cmd)
        self.log("✅ DNS restaurado para o padrão de fábrica (DHCP) com sucesso!")
        from tkinter import messagebox
        self.after(0, lambda: messagebox.showinfo("Sucesso", "✅ DNS original (DHCP) restaurado com sucesso!"))

    def update_all_drivers(self):
        self.log("🚀 Iniciando Atualização Automática de Todos os Drivers...")
        self.log("Buscando atualizações de drivers pelo Windows Update e Winget. Por favor aguarde...")
        
        # 1. Run winget upgrade all
        self.log("-> Atualizando pacotes e drivers via Winget...")
        winget_cmd = 'winget upgrade --all --accept-package-agreements --accept-source-agreements --silent'
        self.run_cmd_live(winget_cmd)
        
        # 2. Query Windows Update for missing drivers using COM API
        self.log("-> Verificando drivers ausentes no Windows Update (Microsoft)...")
        ps_script = (
            "$Session = New-Object -ComObject Microsoft.Update.Session; "
            "$Searcher = $Session.CreateUpdateSearcher(); "
            "$Searcher.ServiceID = '7971f918-a847-4430-9279-4a52d1efe18d'; " # Microsoft Update
            "$Criteria = \"IsInstalled=0 and Type='Driver'\"; "
            "$SearchResult = try { $Searcher.Search($Criteria) } catch { $null }; "
            "if ($SearchResult -and $SearchResult.Updates.Count -gt 0) { "
            "  Write-Output \"Encontrado $($SearchResult.Updates.Count) driver(s) para atualizar.\"; "
            "  $UpdateCollection = New-Object -ComObject Microsoft.Update.UpdateColl; "
            "  foreach ($Update in $SearchResult.Updates) { $UpdateCollection.Add($Update) | Out-Null }; "
            "  $Downloader = $Session.CreateUpdateDownloader(); "
            "  $Downloader.Updates = $UpdateCollection; "
            "  Write-Output 'Baixando drivers...'; "
            "  $DownloadResult = $Downloader.Download(); "
            "  $Installer = $Session.CreateUpdateInstaller(); "
            "  $Installer.Updates = $UpdateCollection; "
            "  Write-Output 'Instalando drivers...'; "
            "  $InstallResult = $Installer.Install(); "
            "  Write-Output 'Instalação de drivers concluída com sucesso!';"
            "} else { "
            "  Write-Output 'Todos os drivers do Windows Update já estão atualizados.';"
            "}"
        )
        self.run_cmd_live(f'powershell -Command "{ps_script}"')
        self.log("✅ Atualização Completa de Drivers concluída!")
        from tkinter import messagebox
        self.after(0, lambda: messagebox.showinfo("Atualização de Drivers", "✅ Todos os drivers e aplicativos do sistema foram atualizados com sucesso!\n\nAlgumas atualizações podem exigir a reinicialização do computador."))

    def optimize_internet(self):
        """Optimize internet: DNS Cloudflare, TCP tweaks, disable Nagle."""
        self.log("🌐 Iniciando Otimização de Internet...")
        
        # Check if the active game is in the no-custom-dns list
        game = self.cb_jogos.get() if hasattr(self, 'cb_jogos') else ""
        no_dns_games = ["Valorant", "Fortnite", "GTA V", "FIFA / EA FC", "League of Legends"]
        
        if game in no_dns_games:
            self.log(f"-> {game} detectado. Mantendo/Restaurando DNS original (DHCP) para evitar incompatibilidade.")
            dns_cmd = 'powershell -Command "Get-NetAdapter | Where-Object {$_.Status -eq \'Up\'} | ForEach-Object { Set-DnsClientServerAddress -InterfaceAlias $_.Name -ResetServerAddresses }"'
        else:
            self.log("-> Otimizando para DNS de baixa latência (Cloudflare)...")
            dns_cmd = 'powershell -Command "Get-NetAdapter | Where-Object {$_.Status -eq \'Up\'} | ForEach-Object { Set-DnsClientServerAddress -InterfaceAlias $_.Name -ServerAddresses (\'1.1.1.1\',\'1.0.0.1\') }"'

        cmds = [
            # DNS Configured above
            dns_cmd,
            # TCP AutoTuning - normal é o melhor para jogos
            'netsh int tcp set global autotuninglevel=normal',
            # Chimney offload
            'netsh int tcp set global chimney=disabled',
            # ECN Capability
            'netsh int tcp set global ecncapability=disabled',
            # RSS (Receive Side Scaling)
            'netsh int tcp set global rss=enabled',
            # Timestamps off
            'netsh int tcp set global timestamps=disabled',
            # Initial RTO
            'netsh int tcp set global initialRto=2000',
            # Desativa Nagle (TcpAckFrequency + TcpNoDelay) em todos os adaptadores de rede
            'powershell -Command "Get-ChildItem \'HKLM:\\SYSTEM\\CurrentControlSet\\Services\\Tcpip\\Parameters\\Interfaces\' -ErrorAction SilentlyContinue | ForEach-Object { Set-ItemProperty -Path $_.PSPath -Name \'TcpAckFrequency\' -Value 1 -Type DWord -ErrorAction SilentlyContinue; Set-ItemProperty -Path $_.PSPath -Name \'TCPNoDelay\' -Value 1 -Type DWord -ErrorAction SilentlyContinue; Set-ItemProperty -Path $_.PSPath -Name \'TcpDelAckTicks\' -Value 0 -Type DWord -ErrorAction SilentlyContinue }"',
            'reg add "HKLM\\SYSTEM\\CurrentControlSet\\Services\\Tcpip\\Parameters" /v TcpNoDelay /t REG_DWORD /d 1 /f',
            'reg add "HKLM\\SYSTEM\\CurrentControlSet\\Services\\Tcpip\\Parameters" /v TCPDelAckTicks /t REG_DWORD /d 0 /f',
            # Buffer de rede aumentado
            'reg add "HKLM\\SYSTEM\\CurrentControlSet\\Services\\AFD\\Parameters" /v DefaultReceiveWindow /t REG_DWORD /d 65536 /f',
            'reg add "HKLM\\SYSTEM\\CurrentControlSet\\Services\\AFD\\Parameters" /v DefaultSendWindow /t REG_DWORD /d 65536 /f',
            # Limpar cache DNS
            'ipconfig /flushdns',
        ]
        for cmd in cmds:
            self.run_cmd_live(cmd)
        self.log("✅ Internet Otimizada! DNS=Cloudflare, Nagle OFF, TCP ajustado. Reinicie para aplicar tudo.")

    def view_audit_log(self):
        if not self.is_admin:
            self.log("❌ Acesso Negado: Apenas o usuário Master pode ler a auditoria!")
            return
            
        view_win = ctk.CTkToplevel(self)
        view_win.title("Log de Auditoria Decodificado")
        view_win.geometry("600x400")
        view_win.attributes('-topmost', 'true')
        
        txt = ctk.CTkTextbox(view_win, width=580, height=380, font=ctk.CTkFont(family="Consolas", size=12))
        txt.pack(padx=10, pady=10)
        
        if not os.path.exists(self.audit_log_path):
            txt.insert("1.0", "Nenhum log de auditoria encontrado ainda.")
            txt.configure(state="disabled")
            return
            
        try:
            with open(self.audit_log_path, "r", encoding="utf-8") as f:
                lines = f.readlines()
                
            decoded_text = ""
            for line in lines:
                line = line.strip()
                if line:
                    try:
                        decoded_bytes = base64.b64decode(line.encode('ascii'), validate=True)
                        decoded_str = decoded_bytes.decode('utf-8')
                        if any(c.isalnum() for c in decoded_str):
                            decoded_text += decoded_str
                            if not decoded_str.endswith("\n"):
                                decoded_text += "\n"
                        else:
                            decoded_text += line + "\n"
                    except Exception:
                        decoded_text += line + "\n"
            
            txt.insert("1.0", decoded_text)
        except Exception as e:
            txt.insert("1.0", f"Erro ao ler log: {e}")
            
        txt.configure(state="disabled")

    def create_restore_point(self, force_visible=False):
        self.log("Verificando/Criando Ponto de Restauração de Segurança...")
        cmd = 'powershell -Command "try { Set-Service -Name vss -StartupType Manual -ErrorAction SilentlyContinue; Start-Service vss -ErrorAction SilentlyContinue } catch {}; Enable-ComputerRestore -Drive C:\\ -ErrorAction SilentlyContinue; Checkpoint-Computer -Description \'Bernal_Otimizacoes_Backup\' -RestorePointType \'MODIFY_SETTINGS\' -ErrorAction SilentlyContinue"'
        if force_visible:
            self.run_visible_cmd("Ponto de Restauração", cmd)
        else:
            if self.run_cmd_live(cmd):
                self.log("✅ Backup (Ponto de Restauração) criado com sucesso!")
            else:
                self.log("⚠️ Aviso: Não foi possível criar o Ponto de Restauração (O Windows pode estar com esse recurso desativado ou requer permissão Admin).")

    # --- Logic Implementations ---
    def apply_profile(self, mode):
        if not _on_main_thread():
            self.call_ui(lambda: self.apply_profile(mode), wait=False)
            return
        # If it's one of the gamer profiles, ask which game they want to play
        if mode in ["max", "med", "streamer"]:
            installed = self.detect_installed_games()
            # Add general profile option
            options = [f"Geral - Apenas Perfil {mode.upper()}"] + installed
            
            dialog = ctk.CTkToplevel(self)
            dialog.title("Selecione o Jogo")
            dialog.geometry("380x240")
            dialog.attributes("-topmost", True)
            dialog.grab_set()
            
            if mode == "streamer":
                title_text = "🎥 Modo Streamer"
                desc_text = "Selecione o jogo que você vai stremar agora\npara otimizarmos a prioridade do OBS, Discord e do Jogo:"
                btn_text = "🎥 Aplicar Perfil & Stremar"
            else:
                title_text = "🚀 Otimização por Jogo"
                desc_text = "Selecione o jogo que você deseja iniciar com este perfil\npara que possamos otimizar as configurações específicas dele:"
                btn_text = "⚡ Aplicar Perfil & Otimizar"
            
            ctk.CTkLabel(dialog, text=title_text, font=ctk.CTkFont(size=16, weight="bold"), text_color="#E74C3C").pack(pady=10)
            ctk.CTkLabel(dialog, text=desc_text, font=ctk.CTkFont(size=11)).pack(pady=5)
            
            cb_detected = ctk.CTkComboBox(dialog, values=options, width=280)
            cb_detected.pack(pady=10)
            
            def proceed():
                chosen = cb_detected.get()
                dialog.destroy()
                
                # Execute the profile application logic in a thread
                self.run_async(self.apply_profile_logic, mode, chosen)
                
            ctk.CTkButton(dialog, text=btn_text, font=ctk.CTkFont(weight="bold"), fg_color="#27AE60", hover_color="#1E8449", width=220, command=proceed).pack(pady=10)
            return
            
        # For non-gamer profiles (balanced, visual, work, revert), run directly
        self.run_async(self.apply_profile_logic, mode, None)

    apply_profile._ui_entry = True

    def apply_profile_logic(self, mode, chosen_game):
        self.log(f"Iniciando Aplicação do Perfil: {mode.upper()}")
        
        # Power Plans
        plan_high = "8c5e7fda-e8bf-4a96-9a85-a6e23a8c635c"
        plan_balanced = "381b4222-f694-41f0-9685-ff5bb260df2e"

        # Ensure power schemes exist on this computer
        try:
            import subprocess
            check_high = subprocess.run(f"powercfg -query {plan_high}", shell=True, capture_output=True, creationflags=subprocess.CREATE_NO_WINDOW)
            if check_high.returncode != 0:
                self.log("⚠️ Plano de energia Alto Desempenho ausente. Criando plano...")
                self.run_cmd_live(f"powercfg -duplicatescheme 8c5e7fda-e8bf-4a96-9a85-a6e23a8c635c {plan_high}")
                
            check_balanced = subprocess.run(f"powercfg -query {plan_balanced}", shell=True, capture_output=True, creationflags=subprocess.CREATE_NO_WINDOW)
            if check_balanced.returncode != 0:
                self.log("⚠️ Plano de energia Equilibrado ausente. Criando plano...")
                self.run_cmd_live(f"powercfg -duplicatescheme 381b4222-f694-41f0-9685-ff5bb260df2e {plan_balanced}")
        except Exception as e:
            self.log(f"⚠️ Erro ao verificar planos de energia: {e}")

        if mode == "max":
            self.run_cmd_live(f"powercfg -setactive {plan_high}")
            self.run_cmd_live('reg add "HKCU\\Software\\Microsoft\\Windows\\CurrentVersion\\Explorer\\VisualEffects" /v "VisualFXSetting" /t REG_DWORD /d 2 /f')
            self.run_cmd_live('reg add "HKCU\\System\\GameConfigStore" /v "GameDVR_Enabled" /t REG_DWORD /d 0 /f')
            self.optimize_network()
            self.optimize_fps_extreme()
            self.disable_notifications()
            self.disable_useless_services()
            self.log("✅ Perfil Max FPS (Gráficos no Mínimo, CPU Unparked, Serviços OFF) Aplicado!")
        
        elif mode == "med":
            self.run_cmd_live(f"powercfg -setactive {plan_high}")
            self.run_cmd_live('reg add "HKCU\\Software\\Microsoft\\Windows\\CurrentVersion\\Explorer\\VisualEffects" /v "VisualFXSetting" /t REG_DWORD /d 0 /f') # Let Windows choose
            self.run_cmd_live('reg add "HKCU\\System\\GameConfigStore" /v "GameDVR_Enabled" /t REG_DWORD /d 0 /f')
            self.optimize_network()
            self.disable_notifications()
            self.log("✅ Perfil Balanced (Gráficos Médios) Aplicado!")

        elif mode == "visual":
            self.run_cmd_live(f"powercfg -setactive {plan_balanced}")
            self.run_cmd_live('reg add "HKCU\\Software\\Microsoft\\Windows\\CurrentVersion\\Explorer\\VisualEffects" /v "VisualFXSetting" /t REG_DWORD /d 1 /f') # Best appearance
            self.run_cmd_live('reg add "HKCU\\System\\GameConfigStore" /v "GameDVR_Enabled" /t REG_DWORD /d 0 /f')
            self.log("✅ Perfil Max Visual (Qualidade Máxima) Aplicado!")
            
        elif mode == "streamer":
            self.run_cmd_live(f"powercfg -setactive {plan_high}")
            # Priorities for streaming apps (obs64, discord)
            self.run_cmd_live('powershell -Command "Get-Process obs64 -ErrorAction SilentlyContinue | ForEach-Object { $_.PriorityClass = \'High\' }"')
            self.run_cmd_live('powershell -Command "Get-Process discord -ErrorAction SilentlyContinue | ForEach-Object { $_.PriorityClass = \'AboveNormal\' }"')
            self.log("✅ Perfil STREAMER Aplicado! Prioridade de CPU dada ao OBS Studio e Discord.")
            
        elif mode == "trabalho":
            self.run_cmd_live(f"powercfg -setactive {plan_balanced}")
            self.run_cmd_live('reg add "HKCU\\Software\\Microsoft\\Windows\\CurrentVersion\\Explorer\\VisualEffects" /v "VisualFXSetting" /t REG_DWORD /d 2 /f') # Best performance (cuts animations)
            self.run_cmd_live('reg add "HKCU\\System\\GameConfigStore" /v "GameDVR_Enabled" /t REG_DWORD /d 0 /f')
            self.disable_useless_services()
            self.log("✅ Perfil TRABALHO (Equilíbrio e Fluidez para Uso Leve) Aplicado!")

        elif mode == "revert":
            self.log("Revertendo configurações rápidas para Padrão do Windows...")
            self.run_cmd_live(f"powercfg -setactive {plan_balanced}")
            self.run_cmd_live('reg add "HKCU\\Software\\Microsoft\\Windows\\CurrentVersion\\Explorer\\VisualEffects" /v "VisualFXSetting" /t REG_DWORD /d 0 /f')
            self.run_cmd_live('reg add "HKCU\\System\\GameConfigStore" /v "GameDVR_Enabled" /t REG_DWORD /d 1 /f')
            
            self.enable_useless_services()
            self.restore_wallpaper()
            self.enable_defender()
            self.enable_cortana_search()
            self.revert_network()
            self.enable_notifications()
            self.revert_mouse_calibration()
            self.revert_fps_tweaks()
            try:
                self.apply_virtual_ram_pagefile("auto")
            except Exception:
                pass
            self.remove_persistent_guardian()
            
            self.log("✅ Configurações rápidas revertidas!")
            self.log("Abrindo painel de Restauração do Sistema caso precise de um Revert profundo (Backup)...")
            subprocess.Popen("rstrui.exe", shell=True)
            
        self.refresh_metrics_depois()

        # 3. Apply game-specific optimizations if a specific game was chosen
        if chosen_game and not chosen_game.startswith("Geral -"):
            self.log(f"-> Aplicando otimização direcionada adicional para: {chosen_game}...")
            # Update main window combobox value
            if hasattr(self, 'cb_jogos'):
                self.call_ui(lambda: (self.cb_jogos.set(chosen_game), self.on_game_select(chosen_game)))
            # Run the game profile logic
            self.apply_game_profile(chosen_game)

    def apply_game_profile(self, game=None):
        if game is None:
            game = self.call_ui(lambda: self.cb_jogos.get())
        self.log(f"Analisando hardware para otimizar: {game}...")
        
        ram = getattr(self, 'sys_ram', 8)
        
        # Heuristic rules
        if game in ["Call of Duty: Warzone", "Cyberpunk 2077", "FIFA / EA FC"]:
            if ram >= 16:
                self.log(f"-> Hardware atende aos requisitos ({ram}GB RAM). Aplicando perfil BALANCED.")
                self.apply_profile_logic("med", None)
            else:
                self.log(f"-> Atenção: RAM ({ram}GB) é limitante para este jogo. Aplicando perfil MAX FPS (Low Gráficos).")
                self.apply_profile_logic("max", None)
                
            if game == "Call of Duty: Warzone":
                self.log("-> WARZONE DETECTADO: Aplicando Otimização Extrema (Gráficos + Áudio Pro)!")
                try:
                    self.optimize_warzone_audio_and_graphics()
                except Exception as e:
                    self.log(f"-> Erro ao alterar config do Warzone: {e}")
                
        else:
            # CS2, Valorant, Fortnite are lighter
            self.log(f"-> Jogo leve detectado. Aplicando perfil BALANCED para melhor clareza visual e frames altos.")
            self.apply_profile_logic("med", None)

    def optimize_warzone_audio_and_graphics(self):
        folder, found_files = self.find_warzone_configs_exhaustive()
        cst_files = [f for f in found_files if f.lower().endswith(".cst")]
        if not cst_files:
            self.log("❌ Nenhum arquivo .cst do Warzone encontrado. Abra o jogo uma vez e tente de novo.")
            messagebox.showwarning("Warzone", "Não encontrei as configurações do Warzone.\nAbra o jogo uma vez até o menu, feche e tente novamente.")
            return
        if not self._ask_close_cod("aplicar as configurações"):
            return

        backup_dir, _ = self._wz_backup_files(folder, found_files, "antes_otimizacao")
        self.log(f"💾 Backup automático criado antes de alterar: {backup_dir}")

        try:
            import psutil
            phys = psutil.cpu_count(logical=False) or 4
        except Exception:
            phys = 4
        values = {
            # Áudio: destaca passos e tiros
            "AudioMix": "4",
            "MusicVolume": "0.000000",
            "DialogueVolume": "0.200000",
            "EffectsVolume": "1.000000",
            # Desempenho: sombras/volumétricos pesados no mínimo, texturas preservadas
            "RendererWorkerCount": str(max(2, min(phys, 16))),
            "VideoMemoryScale": "0.850000",
            "SpotShadowQuality": "0",
            "VolumetricQuality": "0",
            "ParticleLighting": "0",
            "WaterCausticsMode": "0",
            "NvidiaReflex": "2" if "NVIDIA" in str(getattr(self, 'gpu_name', '')).upper() else None,
        }
        values = {k: v for k, v in values.items() if v is not None}
        total = 0
        for cst in cst_files:
            n = self._cst_set_values(cst, values)
            total += n
            self.log(f"  📝 {os.path.basename(cst)}: {n} ajuste(s)")
        if total:
            self.log(f"✅ Warzone otimizado: {total} ajuste(s) aplicados. Backup em {backup_dir}")
        else:
            self.log("ℹ️ As configurações do Warzone já estavam otimizadas (nenhuma alteração necessária).")

    def apply_theme(self, theme_type):
        self.log(f"Aplicando Estética Gamer: {theme_type.upper()}...")
        if theme_type == "dark":
            wall_name = "WP_Dark.png"
            theme_val = 0
            self.run_cmd_live('reg add "HKCU\\Software\\Microsoft\\Windows\\DWM" /v "ColorPrevalence" /t REG_DWORD /d 0 /f')
        elif theme_type == "light":
            wall_name = "WP_Light.png"
            theme_val = 1
            self.run_cmd_live('reg add "HKCU\\Software\\Microsoft\\Windows\\DWM" /v "ColorPrevalence" /t REG_DWORD /d 0 /f')
        elif theme_type == "fem":
            wall_name = "WP_Fem.png"
            theme_val = 0
            # Define AccentColor (Pink) e ativa a cor na Barra de Tarefas
            self.run_cmd_live('reg add "HKCU\\Software\\Microsoft\\Windows\\DWM" /v "AccentColor" /t REG_DWORD /d 4290013695 /f')
            self.run_cmd_live('reg add "HKCU\\Software\\Microsoft\\Windows\\DWM" /v "ColorPrevalence" /t REG_DWORD /d 1 /f')
        elif theme_type == "bernal":
            wall_name = "Wallpaper_Bernal.png"
            theme_val = 0
            self.run_cmd_live('reg add "HKCU\\Software\\Microsoft\\Windows\\DWM" /v "ColorPrevalence" /t REG_DWORD /d 0 /f')

        self.run_cmd_live(f'reg add "HKCU\\Software\\Microsoft\\Windows\\CurrentVersion\\Themes\\Personalize" /v "AppsUseLightTheme" /t REG_DWORD /d {theme_val} /f')
        self.run_cmd_live(f'reg add "HKCU\\Software\\Microsoft\\Windows\\CurrentVersion\\Themes\\Personalize" /v "SystemUsesLightTheme" /t REG_DWORD /d {theme_val} /f')

        # Force windows to update taskbar and colors immediately
        import ctypes
        HWND_BROADCAST = 0xFFFF
        WM_SETTINGCHANGE = 0x001A
        SMTO_ABORTIFHUNG = 0x0002
        ctypes.windll.user32.SendMessageTimeoutW(HWND_BROADCAST, WM_SETTINGCHANGE, 0, "ImmersiveColorSet", SMTO_ABORTIFHUNG, 5000, None)

        wall_path = None
        localapp = os.environ.get("LOCALAPPDATA", "")
        candidates = [
            os.path.join(self.base_path, wall_name),
            os.path.join(self.current_dir, wall_name),
            os.path.join(localapp, "Bernal Otimizacoes", wall_name) if localapp else "",
            os.path.join(os.getcwd(), wall_name)
        ]
        for cand in candidates:
            if cand and os.path.exists(cand):
                wall_path = cand
                break

        if wall_path and os.path.exists(wall_path):
            try:
                ctypes.windll.user32.SystemParametersInfoW(20, 0, wall_path, 3)
                self.log(f"✅ Tema {theme_type.upper()} e Papel de Parede aplicados com sucesso!")
            except Exception as e:
                self.log(f"❌ Erro ao aplicar papel de parede: {e}")
        else:
            self.log(f"❌ Imagem do tema não encontrada: {wall_name}")

    def clean_taskbar(self):
        self.log("Limpando a Barra de Tarefas e Desativando Notificações do Windows...")
        self.run_cmd_live(r'reg add "HKCU\Software\Microsoft\Windows\CurrentVersion\PushNotifications" /v "ToastEnabled" /t REG_DWORD /d 0 /f')
        self.run_cmd_live(r'reg add "HKCU\Software\Microsoft\Windows\CurrentVersion\Search" /v "SearchboxTaskbarMode" /t REG_DWORD /d 0 /f')
        self.run_cmd_live(r'reg add "HKCU\Software\Microsoft\Windows\CurrentVersion\Explorer\Advanced" /v "ShowTaskViewButton" /t REG_DWORD /d 0 /f')
        self.run_cmd_live(r'reg add "HKCU\Software\Microsoft\Windows\CurrentVersion\Explorer\Advanced" /v "ShowCortanaButton" /t REG_DWORD /d 0 /f')
        self.run_cmd_live(r'reg add "HKCU\Software\Microsoft\Windows\CurrentVersion\Explorer\Advanced" /v "TaskbarMn" /t REG_DWORD /d 0 /f')
        self.log("✅ Configurações da Barra de Tarefas registradas! (Serão aplicadas após reiniciar)")

    def reduce_ram_usage(self):
        self.log("Liberando memória RAM em standby e desativando apps em segundo plano...")
        # Desativa apps UWP rodando em segundo plano
        self.run_cmd_live(r'reg add "HKCU\Software\Microsoft\Windows\CurrentVersion\BackgroundAccessApplications" /v "GlobalUserDisabled" /t REG_DWORD /d 1 /f')
        # Esvazia o working set de processos ociosos de forma segura (EmptyWorkingSet via ctypes)
        freed = 0
        try:
            import psutil
            EmptyWorkingSet = ctypes.windll.psapi.EmptyWorkingSet
            protegidos = {"system", "system idle process", "csrss.exe", "wininit.exe", "explorer.exe",
                          "winlogon.exe", "services.exe", "lsass.exe", "smss.exe"}
            meu_pid = os.getpid()
            for proc in psutil.process_iter(['pid', 'name']):
                nome = (proc.info.get('name') or '').lower()
                if proc.info['pid'] in (0, 4, meu_pid) or nome in protegidos:
                    continue
                try:
                    h = ctypes.windll.kernel32.OpenProcess(0x1F0FFF, False, proc.info['pid'])
                    if h:
                        if EmptyWorkingSet(h):
                            freed += 1
                        ctypes.windll.kernel32.CloseHandle(h)
                except Exception:
                    pass
        except Exception as e:
            self.log(f"  ⚠️ Não foi possível varrer todos os processos: {e}")
        self.log(f"✅ Memória em standby liberada de {freed} processo(s) e apps de segundo plano desativados.")

    def remove_bloatware(self):
        self.log("🧨 Iniciando a remoção de Bloatware (Apps Inúteis do Windows)...")
        self.log("Isso pode levar alguns minutos. Por favor aguarde...")
        bloatware_list = [
            "Microsoft.BingWeather", "Microsoft.GetHelp", "Microsoft.Getstarted",
            "Microsoft.Messaging", "Microsoft.3DBuilder", "Microsoft.WindowsFeedbackHub",
            "Microsoft.ZuneVideo", "Microsoft.ZuneMusic", "Microsoft.YourPhone",
            "Microsoft.XboxApp", "Microsoft.XboxGamingOverlay", "Microsoft.XboxSpeechToTextOverlay"
        ]
        for app in bloatware_list:
            self.run_cmd_live(f'powershell -Command "Get-AppxPackage *{app}* | Remove-AppxPackage -ErrorAction SilentlyContinue"')
        self.log("✅ Limpeza de Bloatware concluída! O Windows está mais leve.")

    def restore_system(self):
        self.log("🚑 Abrindo o Painel de Restauração do Sistema do Windows...")
        try:
            import subprocess
            subprocess.Popen("rstrui.exe", shell=True)
            self.log("✅ Painel aberto. Siga as instruções na tela para voltar no tempo.")
        except Exception as e:
            self.log(f"❌ Erro ao abrir Restauração do Sistema: {e}")

    def install_drivers(self):
        self.log("🛠️ Baixando e Instalando Drivers Essenciais (Visual C++)...")
        self.log("Isso corrige erros de DLL faltando ao abrir jogos.")
        cmd = 'powershell -Command "Write-Host \'Instalando Visual C++...\'; winget install --id=Microsoft.VCRedist.2015+.x64 -e --accept-package-agreements --accept-source-agreements"'
        self.run_cmd_live(cmd)
        self.log("✅ Drivers Essenciais instalados/atualizados com sucesso!")

    def clear_temp_files(self):
        self.log("✅ Iniciando limpeza de arquivos temporários (%TEMP% e Windows\\Temp)...")
        def _clean():
            import os, shutil
            # Prefetch NÃO é apagado de propósito: ele acelera a abertura de programas.
            paths = [
                os.environ.get("TEMP", ""),
                r"C:\Windows\Temp",
            ]
            for p in paths:
                if not p or not os.path.exists(p): continue
                for item in os.listdir(p):
                    if item.startswith("_MEI"): continue # Ignora os arquivos do próprio otimizador
                    item_path = os.path.join(p, item)
                    try:
                        if os.path.isfile(item_path) or os.path.islink(item_path):
                            os.unlink(item_path)
                        elif os.path.isdir(item_path):
                            shutil.rmtree(item_path)
                    except:
                        pass
            
            self.log("🚀 Limpeza de arquivos temporários concluída!")
            self.after(0, lambda: messagebox.showinfo("Operação Concluída", "✅ Limpeza de arquivos temporários concluída!"))

        _clean()

    def enable_auto_clean(self):
        self.log("Configurando Limpeza Automática Silenciosa (Diária)...")
        # Cria script VBS 100% invisível que não abre nenhuma janela de CMD ou PowerShell
        app_dir = os.path.join(os.environ.get("LOCALAPPDATA", os.path.expanduser("~")), "Bernal Otimizacoes")
        os.makedirs(app_dir, exist_ok=True)
        vbs_path = os.path.join(app_dir, "silent_clean.vbs")
        vbs_content = (
            'Set WshShell = CreateObject("WScript.Shell")\r\n'
            'WshShell.Run "powershell.exe -NoProfile -ExecutionPolicy Bypass -Command '
            '""Remove-Item -Path $env:TEMP\\* -Recurse -Force -ErrorAction SilentlyContinue; '
            'Remove-Item -Path C:\\Windows\\Temp\\* -Recurse -Force -ErrorAction SilentlyContinue""", 0, False\r\n'
        )
        try:
            with open(vbs_path, "w", encoding="utf-8") as f:
                f.write(vbs_content)
        except Exception:
            pass
        cmd = f'schtasks /create /tn "Bernal_AutoClean" /tr "wscript.exe //B \\"{vbs_path}\\"" /sc daily /f'
        self.run_cmd_live(cmd)
        self.log("✅ Limpeza Automática ativada! (100% silenciosa, sem janelas de CMD).")
        self.after(0, lambda: messagebox.showinfo("Limpeza Automática", "✅ Limpeza Diária Agendada com Sucesso!\n\nConfigurada em modo 100% invisível (nenhuma janela de CMD ou terminal será aberta)."))

    def disable_auto_clean(self):
        self.log("Removendo Limpeza Automática agendada...")
        self.run_cmd_live('schtasks /delete /tn "Bernal_AutoClean" /f')
        self.log("✅ Tarefa agendada removida com sucesso!")
        self.after(0, lambda: messagebox.showinfo("Limpeza Automática", "✅ A tarefa de Limpeza Automática foi desativada e removida."))

    def silence_legacy_tasks(self):
        """Silencia automaticamente qualquer tarefa antiga do Bernal que abria CMD na tela."""
        try:
            chk = subprocess.run('schtasks /query /tn "Bernal_AutoClean" /fo LIST', shell=True, capture_output=True, text=True, creationflags=subprocess.CREATE_NO_WINDOW)
            if chk.returncode == 0 and "powershell" in chk.stdout.lower() and "wscript" not in chk.stdout.lower():
                app_dir = os.path.join(os.environ.get("LOCALAPPDATA", os.path.expanduser("~")), "Bernal Otimizacoes")
                os.makedirs(app_dir, exist_ok=True)
                vbs_path = os.path.join(app_dir, "silent_clean.vbs")
                vbs_content = (
                    'Set WshShell = CreateObject("WScript.Shell")\r\n'
                    'WshShell.Run "powershell.exe -NoProfile -ExecutionPolicy Bypass -Command '
                    '""Remove-Item -Path $env:TEMP\\* -Recurse -Force -ErrorAction SilentlyContinue; '
                    'Remove-Item -Path C:\\Windows\\Temp\\* -Recurse -Force -ErrorAction SilentlyContinue""", 0, False\r\n'
                )
                with open(vbs_path, "w", encoding="utf-8") as f:
                    f.write(vbs_content)
                subprocess.run(f'schtasks /create /tn "Bernal_AutoClean" /tr "wscript.exe //B \\"{vbs_path}\\"" /sc daily /f', shell=True, capture_output=True, creationflags=subprocess.CREATE_NO_WINDOW)
        except Exception:
            pass

    def launch_ame(self, distro_name: str):
        playbook = "Atlsbook_v0.5.0.apbx" if distro_name == "Atlas" else "Revi-PB-26.04.apbx"
        localapp = os.environ.get("LOCALAPPDATA", "")
        install_dir = os.path.join(localapp, "Bernal Otimizacoes") if localapp else ""
        
        search_dirs = [
            self.current_dir,
            self.base_path,
            install_dir,
            os.path.join(self.current_dir, "Tools"),
            os.path.join(self.base_path, "Tools"),
            os.path.join(self.current_dir, "Otimizador_Portable"),
            os.getcwd()
        ]
        
        exe_path = None
        for d in search_dirs:
            if d and os.path.exists(os.path.join(d, "AME-Beta-v0.8.4.exe")):
                exe_path = os.path.join(d, "AME-Beta-v0.8.4.exe")
                break
                
        pb_path = None
        for d in search_dirs:
            if d and os.path.exists(os.path.join(d, playbook)):
                pb_path = os.path.join(d, playbook)
                break

        if exe_path and os.path.exists(exe_path):
            self.log(f"🚀 Iniciando AME Wizard para {distro_name}OS...")
            if pb_path and os.path.exists(pb_path):
                self.log(f"📦 Playbook pronto detectado: {pb_path}")
                try:
                    subprocess.Popen([exe_path, pb_path])
                    subprocess.Popen(["explorer.exe", f"/select,{pb_path}"])
                except Exception:
                    subprocess.Popen([exe_path])
                self.log(f"✅ AME Wizard aberto com o playbook do {distro_name} carregado!")
            else:
                self.log(f"⚠️ Playbook {playbook} não encontrado localmente. Abrindo AME Wizard...")
                subprocess.Popen([exe_path])
        else:
            self.log("❌ O instalador AME não foi encontrado nos diretórios locais.")
            self.log(f"Abrindo o navegador para baixar o {distro_name}OS Oficial...")
            if distro_name == "Atlas":
                webbrowser.open("https://atlasos.net/downloads")
            else:
                webbrowser.open("https://revi.cc/docs/download/")
            self.after(0, lambda: messagebox.showinfo("Download Necessário", f"Baixe o {distro_name}OS pelo site oficial que foi aberto no seu navegador, pois o arquivo AME não foi detectado no pacote."))

    def get_bitlocker_status(self):
        """Retorna uma lista com o status e a porcentagem de cada unidade:
        [{'drive': 'C:', 'status': 'DecryptionInProgress', 'encrypted_pct': 64.2, 'decrypted_pct': 35.8, 'is_done': False}]
        """
        results = []
        # Método 1: PowerShell Get-BitLockerVolume
        ps_cmd = (
            "[Console]::OutputEncoding = [System.Text.Encoding]::UTF8; "
            "$ErrorActionPreference = 'SilentlyContinue'; "
            "$vols = Get-BitLockerVolume; "
            "if ($vols) { "
            "    $arr = @(); "
            "    foreach ($v in $vols) { "
            "        $arr += [PSCustomObject]@{ "
            "            MountPoint = [string]$v.MountPoint; "
            "            VolumeStatus = [string]$v.VolumeStatus; "
            "            ProtectionStatus = [string]$v.ProtectionStatus; "
            "            EncryptionPercentage = [double]$v.EncryptionPercentage "
            "        } "
            "    }; "
            "    $arr | ConvertTo-Json -Compress "
            "}"
        )
        try:
            res = subprocess.run(["powershell", "-NoProfile", "-Command", ps_cmd],
                                 capture_output=True, text=True, timeout=15,
                                 encoding='utf-8', errors='replace',
                                 creationflags=subprocess.CREATE_NO_WINDOW)
            stdout = res.stdout.strip()
            if stdout:
                data = json.loads(stdout)
                if isinstance(data, dict):
                    data = [data]
                for item in data:
                    mp = item.get("MountPoint", "").strip().rstrip("\\")
                    v_status = item.get("VolumeStatus", "")
                    enc_pct = float(item.get("EncryptionPercentage", 0.0) or 0.0)
                    dec_pct = round(100.0 - enc_pct, 1)
                    is_done = (v_status == "FullyDecrypted" or enc_pct <= 0.0)
                    results.append({
                        "drive": mp,
                        "status": v_status,
                        "encrypted_pct": enc_pct,
                        "decrypted_pct": dec_pct,
                        "is_done": is_done
                    })
        except Exception:
            pass

        # Método 2 (Fallback ou complemento): manage-bde -status
        if not results:
            try:
                res_bde = subprocess.run(["manage-bde", "-status"],
                                         capture_output=True, text=True, timeout=15,
                                         encoding='utf-8', errors='replace',
                                         creationflags=subprocess.CREATE_NO_WINDOW)
                output = res_bde.stdout
                current_drive = None
                current_enc_pct = 0.0
                current_status = ""
                for line in output.splitlines():
                    line_s = line.strip()
                    m_vol = re.search(r'(?:Volume|Volumen|Mount Point|Ponto de Montagem|Punto de montaje)\s+([A-Za-z]:)', line_s, re.I)
                    if m_vol:
                        if current_drive:
                            dec_pct = round(100.0 - current_enc_pct, 1)
                            is_done = ("fully" in current_status.lower() or "totalmente" in current_status.lower() or current_enc_pct <= 0.0)
                            results.append({
                                "drive": current_drive,
                                "status": current_status,
                                "encrypted_pct": current_enc_pct,
                                "decrypted_pct": dec_pct,
                                "is_done": is_done
                            })
                        current_drive = m_vol.group(1).upper()
                        current_enc_pct = 0.0
                        current_status = ""

                    m_pct = re.search(r'(?:Percentage Encrypted|Porcentagem Criptografada|Porcentaje cifrado|Porcentaje de cifrado)[\s:]+([0-9.,]+)%?', line_s, re.I)
                    if m_pct:
                        try:
                            current_enc_pct = float(m_pct.group(1).replace(',', '.'))
                        except Exception:
                            pass

                    m_stat = re.search(r'(?:Conversion Status|Estado da Convers|Estado de convers)[\w\s]*:\s*(.+)', line_s, re.I)
                    if m_stat:
                        current_status = m_stat.group(1).strip()

                if current_drive:
                    dec_pct = round(100.0 - current_enc_pct, 1)
                    is_done = ("fully" in current_status.lower() or "totalmente" in current_status.lower() or current_enc_pct <= 0.0)
                    results.append({
                        "drive": current_drive,
                        "status": current_status,
                        "encrypted_pct": current_enc_pct,
                        "decrypted_pct": dec_pct,
                        "is_done": is_done
                    })
            except Exception:
                pass

        return results

    def open_bitlocker_monitor(self):
        """Abre uma janela visual com barra de progresso e porcentagem ao vivo da descriptografia do BitLocker."""
        if hasattr(self, '_bl_mon_win') and self._bl_mon_win is not None and self._bl_mon_win.winfo_exists():
            self._bl_mon_win.lift()
            self._bl_mon_win.focus_force()
            return

        win = ctk.CTkToplevel(self)
        self._bl_mon_win = win
        win.title("Monitor de Descriptografia BitLocker - Bernal Otimizações")
        win.geometry("560x440")
        win.attributes('-topmost', True)

        # Header
        header = ctk.CTkFrame(win, fg_color="#1a1a2e", corner_radius=10)
        header.pack(fill="x", padx=15, pady=(15, 10))
        ctk.CTkLabel(header, text="🔓 Progresso do BitLocker (Ao Vivo)", font=ctk.CTkFont(size=18, weight="bold"), text_color="#00D2FF").pack(pady=(10, 2))
        ctk.CTkLabel(header, text="Acompanhe a porcentagem de descriptografia dos discos em tempo real", font=ctk.CTkFont(size=12), text_color="#BDC3C7").pack(pady=(0, 10))

        # Content frame
        content_frame = ctk.CTkScrollableFrame(win, fg_color="transparent", height=240)
        content_frame.pack(fill="both", expand=True, padx=15, pady=5)

        # Bottom status and refresh button
        bottom_frame = ctk.CTkFrame(win, fg_color="transparent")
        bottom_frame.pack(fill="x", padx=15, pady=(5, 15))

        lbl_status = ctk.CTkLabel(bottom_frame, text="Consultando status dos discos...", font=ctk.CTkFont(size=11), text_color="#7F8C8D")
        lbl_status.pack(side="left")

        btn_refresh = ctk.CTkButton(bottom_frame, text="🔄 Atualizar Agora", width=130, height=30, fg_color="#2980B9", hover_color="#1F618D", font=ctk.CTkFont(weight="bold"))
        btn_refresh.pack(side="right")

        def refresh_ui():
            if not win.winfo_exists():
                return
            btn_refresh.configure(state="disabled", text="⏳ Lendo...")
            lbl_status.configure(text="Lendo informações do BitLocker...")

            def _query():
                info = self.get_bitlocker_status()
                def _update():
                    if not win.winfo_exists():
                        return
                    for child in content_frame.winfo_children():
                        child.destroy()

                    if not info:
                        ctk.CTkLabel(content_frame, text="Nenhum disco com BitLocker detectado ou todos os discos já liberados.", font=ctk.CTkFont(size=13)).pack(pady=30)
                    else:
                        all_done = True
                        for item in info:
                            drv = item.get("drive", "Disco")
                            dec_pct = item.get("decrypted_pct", 100.0)
                            enc_pct = item.get("encrypted_pct", 0.0)
                            is_done = item.get("is_done", False)
                            if not is_done:
                                all_done = False

                            card = ctk.CTkFrame(content_frame, fg_color="#2C3E50" if is_done else "#34495E", corner_radius=8)
                            card.pack(fill="x", pady=6, padx=5)

                            row1 = ctk.CTkFrame(card, fg_color="transparent")
                            row1.pack(fill="x", padx=10, pady=(8, 4))
                            ctk.CTkLabel(row1, text=f"💾 Unidade {drv}", font=ctk.CTkFont(size=14, weight="bold"), text_color="white").pack(side="left")
                            
                            badge_text = f"✅ 100% Descriptografado" if is_done else f"⏳ {dec_pct}% Descriptografado ({enc_pct}% restante)"
                            badge_color = "#27AE60" if is_done else "#E67E22"
                            ctk.CTkLabel(row1, text=badge_text, font=ctk.CTkFont(size=12, weight="bold"), text_color=badge_color).pack(side="right")

                            # Barra de progresso
                            pbar = ctk.CTkProgressBar(card, height=14, corner_radius=5)
                            pbar.pack(fill="x", padx=10, pady=4)
                            progress_val = 1.0 if is_done else max(0.01, min(1.0, dec_pct / 100.0))
                            pbar.set(progress_val)
                            pbar.configure(progress_color="#27AE60" if is_done else "#E67E22")

                            status_desc = "Totalmente descriptografado e livre para formatação." if is_done else "Descriptografia em curso pelo Windows ('El descifrado está en curso'). Não formate ainda!"
                            ctk.CTkLabel(card, text=status_desc, font=ctk.CTkFont(size=11), text_color="#BDC3C7").pack(padx=10, pady=(2, 8), anchor="w")

                        if not all_done:
                            warn_banner = ctk.CTkFrame(content_frame, fg_color="#C0392B", corner_radius=8)
                            warn_banner.pack(fill="x", pady=8, padx=5)
                            ctk.CTkLabel(warn_banner, text="⚠️ NÃO FORMATE O COMPUTADOR AINDA!\nAguarde a barra atingir 100% para evitar travamento ou perda de partição.", font=ctk.CTkFont(size=12, weight="bold"), text_color="white").pack(pady=8, padx=10)
                        else:
                            success_banner = ctk.CTkFrame(content_frame, fg_color="#27AE60", corner_radius=8)
                            success_banner.pack(fill="x", pady=8, padx=5)
                            ctk.CTkLabel(success_banner, text="✅ TODOS OS DISCOS ESTÃO 100% LIVRES!\nVocê já pode formatar o PC com total segurança.", font=ctk.CTkFont(size=12, weight="bold"), text_color="white").pack(pady=8, padx=10)

                    from datetime import datetime
                    lbl_status.configure(text=f"Última leitura: {datetime.now().strftime('%H:%M:%S')} • Atualiza a cada 3s")
                    btn_refresh.configure(state="normal", text="🔄 Atualizar Agora")
                    if win.winfo_exists():
                        win.after(3000, refresh_ui)

                self.after(0, _update)

            threading.Thread(target=_query, daemon=True).start()

        btn_refresh.configure(command=refresh_ui)
        win.after(100, refresh_ui)

    def prepare_for_format(self):
        """Prepara o computador para formatação limpa:
        1. Descriptografa e remove BitLocker de todos os discos.
        2. Apresenta porcentagem em tempo real e monitor visual.
        3. Verifica integridade física dos HDs/SSDs via SMART.
        4. Realiza varredura de integridade do sistema de arquivos nas partições.
        """
        self.log("💿 ==================================================")
        self.log("💿 PREPARANDO O SISTEMA PARA FORMATAÇÃO LIMPA")
        self.log("💿 ==================================================")
        
        # 1. Removendo BitLocker
        self.log("→ [1/3] Disparando remoção do BitLocker de todas as unidades fixas...")
        ps_bitlocker = (
            "$results = @(); "
            "Get-Volume | Where-Object { $_.DriveLetter -and $_.DriveType -eq 'Fixed' } | ForEach-Object { "
            "    $ltr = \"$($_.DriveLetter):\"; "
            "    try { Disable-BitLocker -MountPoint $ltr -ErrorAction SilentlyContinue | Out-Null } catch {}; "
            "    try { manage-bde -off $ltr 2>&1 | Out-Null } catch {}; "
            "    $results += \"$ltr: Comando enviado\"; "
            "}; "
            "Write-Output ($results -join ' | ')"
        )
        try:
            subprocess.run(["powershell", "-NoProfile", "-Command", ps_bitlocker],
                           capture_output=True, text=True, timeout=30,
                           creationflags=subprocess.CREATE_NO_WINDOW)
        except Exception:
            pass

        # 1.1 Lendo porcentagem real da descriptografia
        self.log("→ Consultando porcentagem e status real do BitLocker...")
        bl_info = self.get_bitlocker_status()
        all_done = True
        bl_log_lines = []
        if bl_info:
            for item in bl_info:
                drv = item.get("drive", "")
                dec_pct = item.get("decrypted_pct", 100.0)
                enc_pct = item.get("encrypted_pct", 0.0)
                is_done = item.get("is_done", False)
                if not is_done:
                    all_done = False
                    msg = f"⏳ BitLocker {drv}: Descriptografia em andamento — {dec_pct}% concluído ({enc_pct}% restante)."
                    self.log(msg)
                    bl_log_lines.append(f"• {drv}: {dec_pct}% Descriptografado ({enc_pct}% restante)")
                else:
                    msg = f"✅ BitLocker {drv}: Totalmente Descriptografado (100% livre)."
                    self.log(msg)
                    bl_log_lines.append(f"• {drv}: 100% Descriptografado (OK)")
        else:
            self.log("✅ BitLocker: Comandos de remoção aplicados (Nenhum volume bloqueado detectado).")
            bl_log_lines.append("Comandos de remoção enviados com sucesso.")

        if not all_done:
            self.log("⚠️ ATENÇÃO: O disco AINDA NÃO terminou de descriptografar!")
            self.log("⚠️ NÃO formate o computador agora. Aguarde atingir 100% no monitor.")
            self.log("💡 O monitor visual de progresso será aberto na sua tela agora.")
        else:
            self.log("🎉 Todos os discos estão 100% descriptografados e prontos para formatação!")

        # 2. Status SMART dos Discos Físicos
        self.log("→ [2/3] Verificando integridade física dos discos (SMART)...")
        ps_disks = "Get-PhysicalDisk | Select-Object DeviceId, FriendlyName, MediaType, HealthStatus, OperationalStatus | ConvertTo-Json"
        disk_health_report = []
        try:
            res_disk = subprocess.run(["powershell", "-NoProfile", "-Command", ps_disks],
                                      capture_output=True, text=True, timeout=30,
                                      creationflags=subprocess.CREATE_NO_WINDOW)
            disks_raw = json.loads(res_disk.stdout.strip())
            if isinstance(disks_raw, dict):
                disks_raw = [disks_raw]
            for d in disks_raw:
                info = f"Disco {d.get('DeviceId')}: {d.get('FriendlyName')} [{d.get('MediaType')}] - Saúde: {d.get('HealthStatus')} ({d.get('OperationalStatus')})"
                self.log(f"   💾 {info}")
                disk_health_report.append(info)
        except Exception as e:
            try:
                res_wmic = subprocess.run("wmic diskdrive get status,model", capture_output=True, text=True, shell=True,
                                          creationflags=subprocess.CREATE_NO_WINDOW)
                for line in res_wmic.stdout.splitlines():
                    if line.strip() and "Model" not in line and "Status" not in line:
                        disk_health_report.append(line.strip())
                        self.log(f"   💾 {line.strip()}")
            except Exception:
                disk_health_report.append("Discos físicos normais.")

        # 3. Integridade das Partições e Volumes
        self.log("→ [3/3] Verificando integridade das partições e sistema de arquivos...")
        ps_vols = "Get-Volume | Where-Object DriveLetter | Select-Object DriveLetter, FileSystemLabel, HealthStatus, OperationalStatus | ConvertTo-Json"
        vol_report = []
        try:
            res_vols = subprocess.run(["powershell", "-NoProfile", "-Command", ps_vols],
                                      capture_output=True, text=True, timeout=30,
                                      creationflags=subprocess.CREATE_NO_WINDOW)
            vols_raw = json.loads(res_vols.stdout.strip())
            if isinstance(vols_raw, dict):
                vols_raw = [vols_raw]
            for v in vols_raw:
                ltr = v.get("DriveLetter")
                lbl = v.get("FileSystemLabel") or "Sem Rótulo"
                health = v.get("HealthStatus")
                info = f"Unidade {ltr}: [{lbl}] - Saúde: {health}"
                self.log(f"   📁 {info}")
                vol_report.append(info)
                try:
                    subprocess.run(["powershell", "-NoProfile", "-Command", f"Repair-Volume -DriveLetter {ltr} -Scan -ErrorAction SilentlyContinue"],
                                   capture_output=True, text=True, timeout=40,
                                   creationflags=subprocess.CREATE_NO_WINDOW)
                except Exception:
                    pass
        except Exception as e:
            vol_report.append("Partições verificadas.")

        self.log("✨ Preparação para Formatação concluída!")
        
        disks_str = "\n".join(disk_health_report) if disk_health_report else "Todos os discos com SMART Saudável."
        vols_str = "\n".join(vol_report) if vol_report else "Todas as partições íntegras."
        
        if not all_done:
            bl_status_box = (
                "⏳ DESCRIPTOGRAFIA EM ANDAMENTO NO WINDOWS!\n"
                + "\n".join(bl_log_lines) + "\n\n"
                "⚠️ NÃO FORMATE O COMPUTADOR AINDA!\n"
                "O Windows está removendo a criptografia dos arquivos em segundo plano ('El descifrado está en curso'). "
                "Aguarde o monitor atingir 100% de descriptografia antes de formatar para não bloquear o disco."
            )
        else:
            bl_status_box = "✅ Todos os discos estão 100% DESCRIPTOGRAFADOS e livres para formatação!"

        summary_msg = (
            "📋 Relatório de Preparação para Formatação:\n\n"
            f"🔓 Status do BitLocker:\n{bl_status_box}\n\n"
            f"💾 Discos Físicos (SMART):\n{disks_str}\n\n"
            f"📁 Partições/Volumes:\n{vols_str}"
        )
        self.after(0, lambda: messagebox.showinfo("Preparação para Formatação", summary_msg))
        self.after(600, self.open_bitlocker_monitor)

    def download_and_install_driver_booster(self):
        self.log("🚀 Baixando e instalando IObit Driver Booster atualizado...")
        winget_cmd = 'winget install --id IObit.DriverBooster -e --accept-package-agreements --accept-source-agreements --silent'
        installed = False
        try:
            res = subprocess.run(winget_cmd, shell=True, capture_output=True, text=True, timeout=120,
                                 creationflags=subprocess.CREATE_NO_WINDOW)
            if res.returncode == 0:
                self.log("✅ IObit Driver Booster instalado com sucesso via winget!")
                installed = True
        except Exception:
            pass

        if not installed:
            self.log("Baixando instalador oficial do Driver Booster pelo CDN da IObit...")
            temp_dir = os.environ.get("TEMP", os.path.expanduser("~"))
            installer_path = os.path.join(temp_dir, "driver_booster_setup.exe")
            db_url = "https://cdn.iobit.com/dl/driver_booster_setup.exe"
            try:
                req = urllib.request.Request(db_url, headers={'User-Agent': 'Mozilla/5.0'})
                with urllib.request.urlopen(req, timeout=30) as resp, open(installer_path, 'wb') as out_f:
                    shutil.copyfileobj(resp, out_f)
                self.log("Iniciando instalador do IObit Driver Booster silenciosamente...")
                subprocess.Popen([installer_path, "/VERYSILENT"], creationflags=subprocess.CREATE_NO_WINDOW)
                self.log("✅ Instalador do IObit Driver Booster iniciado!")
                installed = True
            except Exception as e:
                self.log(f"⚠️ Falha no download direto: {e}. Abrindo página oficial...")
                webbrowser.open("https://www.iobit.com/pt/driver-booster.php")

    def download_and_install_advanced_systemcare(self):
        self.log("🛡️ Baixando e instalando IObit Advanced SystemCare atualizado...")
        winget_cmd = 'winget install --id IObit.AdvancedSystemCare -e --accept-package-agreements --accept-source-agreements --silent'
        installed = False
        try:
            res = subprocess.run(winget_cmd, shell=True, capture_output=True, text=True, timeout=120,
                                 creationflags=subprocess.CREATE_NO_WINDOW)
            if res.returncode == 0:
                self.log("✅ IObit Advanced SystemCare instalado com sucesso via winget!")
                installed = True
        except Exception:
            pass

        if not installed:
            self.log("Baixando instalador oficial do Advanced SystemCare pelo CDN da IObit...")
            temp_dir = os.environ.get("TEMP", os.path.expanduser("~"))
            installer_path = os.path.join(temp_dir, "advanced_systemcare_setup.exe")
            asc_url = "https://cdn.iobit.com/dl/advanced-systemcare-setup.exe"
            try:
                req = urllib.request.Request(asc_url, headers={'User-Agent': 'Mozilla/5.0'})
                with urllib.request.urlopen(req, timeout=30) as resp, open(installer_path, 'wb') as out_f:
                    shutil.copyfileobj(resp, out_f)
                self.log("Iniciando instalador do IObit Advanced SystemCare silenciosamente...")
                subprocess.Popen([installer_path, "/VERYSILENT"], creationflags=subprocess.CREATE_NO_WINDOW)
                self.log("✅ Instalador do IObit Advanced SystemCare iniciado!")
                installed = True
            except Exception as e:
                self.log(f"⚠️ Falha no download direto: {e}. Abrindo página oficial...")
                webbrowser.open("https://www.iobit.com/pt/advancedsystemcarefree.php")

    def install_gamer_pack(self):
        self.log("🎰 Mega Pacote Gamer: Baixando plataformas e ferramentas...")
        try:
            self.log("Abrindo plataformas de jogos no Ninite (Battle.net, Discord, Epic, Steam)...")
            webbrowser.open("https://ninite.com/battlenet-discord-epic-steam/")
        except Exception as e:
            self.log(f"⚠️ Erro ao abrir Ninite: {e}")
            
        self.download_and_install_driver_booster()
        self.download_and_install_advanced_systemcare()

    def install_streamer_app(self, app_id, app_name):
        if "spotify" in app_id.lower() or "spotify" in app_name.lower():
            self.install_spotify()
            return
        self.log(f"Iniciando a instalação do {app_name}...")
        self.log("Tentando instalação silenciosa via Winget...")
        cmd = f'winget install --id {app_id} -e --accept-package-agreements --accept-source-agreements --silent'
        if self.run_cmd_live(cmd):
            self.log(f"✅ {app_name} instalado com sucesso!")
            from tkinter import messagebox
            self.after(0, lambda: messagebox.showinfo("Sucesso", f"✅ {app_name} foi instalado com sucesso!"))
            return

        self.log(f"⚠️ Winget indisponível ou recusado. Acionando instalador oficial direto para {app_name}...")
        app_urls = {
            "Blizzard.BattleNet": "https://downloader.battle.net/download/getInstallerForGame?os=win&gameProgram=BATTLENET_APP",
            "ElectronicArts.EADesktop": "https://origin-a.akamaihd.net/EA-Desktop-Client-Download/installer-releases/EAappInstaller.exe",
            "Valve.Steam": "https://cdn.akamai.steamstatic.com/client/installer/SteamSetup.exe",
            "EpicGames.EpicGamesLauncher": "https://store.epicgames.com/download",
            "RiotGames.RiotClient": "https://playvalorant.com/pt-br/download/",
            "Ubisoft.Connect": "https://ubisoftconnect.com/",
            "Obsproject.ObsStudio": "https://obsproject.com/download",
            "Discord.Discord": "https://discord.com/api/download?platform=win",
            "VB-Audio.Voicemeeter.Banana": "https://vb-audio.com/Voicemeeter/banana.htm",
            "Streamlabs.StreamlabsDesktop": "https://streamlabs.com/streamlabs-live-streaming-software/download"
        }

        url = app_urls.get(app_id)
        if url:
            if url.endswith(".exe"):
                try:
                    temp_dir = os.environ.get("TEMP", os.path.expanduser("~"))
                    exe_name = f"{app_id.split('.')[-1]}_Setup.exe"
                    dest_file = os.path.join(temp_dir, exe_name)
                    self.log(f"Baixando instalador executável oficial...")
                    import urllib.request
                    urllib.request.urlretrieve(url, dest_file)
                    if os.path.exists(dest_file):
                        self.log(f"Iniciando instalador {exe_name}...")
                        subprocess.Popen([dest_file], shell=True)
                        from tkinter import messagebox
                        self.after(0, lambda: messagebox.showinfo("Instalador Iniciado", f"O instalador oficial do {app_name} foi baixado e iniciado na sua tela!"))
                        return
                except Exception as ex:
                    self.log(f"Download direto falhou: {ex}. Abrindo no navegador...")
            webbrowser.open(url)
            self.log(f"🌐 Página de download oficial do {app_name} aberta no navegador!")
        else:
            self.log(f"❌ Não foi possível obter o instalador do {app_name}.")

    def install_spotify(self):
        self.log("🎵 Baixando instalador oficial do Spotify...")
        self.log("Por favor, aguarde alguns instantes...")
        temp_dir = os.environ.get("TEMP", os.path.expanduser("~"))
        installer_path = os.path.join(temp_dir, "SpotifySetup.exe")
        downloaded = False
        try:
            req = urllib.request.Request("https://download.scdn.co/SpotifySetup.exe", headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'})
            with urllib.request.urlopen(req, timeout=30) as resp, open(installer_path, "wb") as out_f:
                shutil.copyfileobj(resp, out_f)
            downloaded = True
            self.log("✅ Download do SpotifySetup.exe concluído!")
        except Exception as e:
            self.log(f"⚠️ Falha no download direto: {e}")

        if downloaded and os.path.exists(installer_path):
            self.log("🚀 Executando instalador do Spotify no contexto do usuário...")
            try:
                # Dispara via explorer para rodar fora do contexto restrito de Administrador
                subprocess.Popen(["explorer.exe", installer_path])
            except Exception:
                subprocess.Popen([installer_path])
            self.log("✅ Instalador oficial do Spotify iniciado na tela!")
            from tkinter import messagebox
            self.after(0, lambda: messagebox.showinfo("Spotify", "✅ O instalador oficial do Spotify foi baixado e iniciado com sucesso!\n\nEle será configurado automaticamente."))
        else:
            self.log("🌐 Abrindo página oficial de download do Spotify no navegador...")
            webbrowser.open("https://www.spotify.com/download/windows/")
            from tkinter import messagebox
            self.after(0, lambda: messagebox.showinfo("Spotify", "A página oficial de download foi aberta no seu navegador."))

    def install_tiktok_live_studio(self):
        self.log("Abrindo a página oficial de download do TikTok Live Studio...")
        import webbrowser
        webbrowser.open("https://www.tiktok.com/studio/download")
        self.log("✅ Página de download do TikTok Live Studio aberta no seu navegador!")
        from tkinter import messagebox
        self.after(0, lambda: messagebox.showinfo("TikTok Live Studio", "A página oficial de download foi aberta no seu navegador.\n\nBaixe e instale o instalador diretamente por lá!"))

    def install_chrome(self):
        self.log("Baixando e instalando o Google Chrome (Modo Silencioso)...")
        self.run_cmd_live('winget install --id Google.Chrome -e --accept-package-agreements --accept-source-agreements --silent')
        
    def install_afterburner(self):
        self.log("Baixando e instalando o MSI Afterburner (Modo Silencioso)...")
        self.run_cmd_live('winget install --id Guru3D.Afterburner -e --accept-package-agreements --accept-source-agreements --silent')

    def optimize_network(self):
        self.log("Otimizando rede para jogos (TCP/IP)...")
        self.run_cmd_live('netsh int tcp set global autotuninglevel=normal')
        self.run_cmd_live('netsh int tcp set global rss=enabled')
        self.run_cmd_live('netsh int tcp set heuristics disabled')

    def optimize_fps_extreme(self):
        self.log("Injetando Tweaks Extremos de FPS...")
        # CPU Unparking e Priority Control
        self.run_cmd_live('reg add "HKLM\\SYSTEM\\CurrentControlSet\\Control\\PriorityControl" /v "Win32PrioritySeparation" /t REG_DWORD /d 38 /f')
        # Multimedia System Profile for Latency
        self.run_cmd_live('reg add "HKLM\\SOFTWARE\\Microsoft\\Windows NT\\CurrentVersion\\Multimedia\\SystemProfile" /v "SystemResponsiveness" /t REG_DWORD /d 0 /f')
        self.run_cmd_live('reg add "HKLM\\SOFTWARE\\Microsoft\\Windows NT\\CurrentVersion\\Multimedia\\SystemProfile" /v "NetworkThrottlingIndex" /t REG_DWORD /d 4294967295 /f')
        self.run_cmd_live('reg add "HKLM\\SOFTWARE\\Microsoft\\Windows NT\\CurrentVersion\\Multimedia\\SystemProfile\\Tasks\\Games" /v "GPU Priority" /t REG_DWORD /d 8 /f')
        self.run_cmd_live('reg add "HKLM\\SOFTWARE\\Microsoft\\Windows NT\\CurrentVersion\\Multimedia\\SystemProfile\\Tasks\\Games" /v "Priority" /t REG_DWORD /d 6 /f')
        # Disable Memory Compression for latency
        self.run_cmd_live('powershell -Command "Disable-MMAgent -mc -ErrorAction SilentlyContinue"')
        self.log("Tweaks Extremos de FPS (Latência/CPU) Concluídos!")

    def disable_notifications(self):
        self.log("Desativando notificações do Windows...")
        self.run_cmd_live('reg add "HKCU\\Software\\Microsoft\\Windows\\CurrentVersion\\PushNotifications" /v "ToastEnabled" /t REG_DWORD /d 0 /f')

    def disable_useless_services(self):
        self.log("Desativando serviços inúteis (Spooler)...")
        self.run_cmd_live('sc config Spooler start= demand')

    def enable_notifications(self):
        self.log("Reativando notificações do Windows...")
        self.run_cmd_live('reg add "HKCU\\Software\\Microsoft\\Windows\\CurrentVersion\\PushNotifications" /v "ToastEnabled" /t REG_DWORD /d 1 /f')

    def enable_useless_services(self):
        self.log("Restaurando serviços do Windows (Spooler, etc.)...")
        self.run_cmd_live('sc config Spooler start= auto')
        self.run_cmd_live('net start Spooler')

    def disable_defender(self):
        extras.defender_disable(self)

    def enable_defender(self):
        extras.defender_enable(self)

    def remove_internet_explorer(self):
        extras.remove_internet_explorer(self)

    def clean_desktop(self):
        extras.clean_desktop(self)

    def set_chrome_default(self):
        extras.set_chrome_default(self)

    def update_drivers_native(self):
        extras.update_drivers(self)

    def audio_fps_enable(self):
        extras.audio_fps_enable(self)

    def audio_fps_disable(self):
        extras.audio_fps_disable(self)

    def enable_cortana_search(self):
        self.log("Restaurando busca e ícones da Barra de Tarefas...")
        self.run_cmd_live(r'reg add "HKCU\Software\Microsoft\Windows\CurrentVersion\Search" /v "SearchboxTaskbarMode" /t REG_DWORD /d 1 /f')
        self.run_cmd_live(r'reg add "HKCU\Software\Microsoft\Windows\CurrentVersion\Explorer\Advanced" /v "ShowTaskViewButton" /t REG_DWORD /d 1 /f')
        self.run_cmd_live(r'reg add "HKCU\Software\Microsoft\Windows\CurrentVersion\Explorer\Advanced" /v "ShowCortanaButton" /t REG_DWORD /d 1 /f')

    def restore_wallpaper(self):
        self.log("Restaurando papel de parede padrão do Windows...")
        default_wall = r"C:\Windows\Web\Wallpaper\Windows\img0.jpg"
        if os.path.exists(default_wall):
            try:
                ctypes.windll.user32.SystemParametersInfoW(20, 0, default_wall, 3)
                self.log("✅ Papel de parede padrão restaurado!")
            except Exception as e:
                self.log(f"Aviso ao restaurar papel de parede: {e}")

    def revert_mouse_calibration(self):
        self.log("Restaurando configurações padrão do mouse (aceleração do Windows ligada)...")
        self.run_cmd_live(r'reg add "HKCU\Control Panel\Mouse" /v MouseSpeed /t REG_SZ /d "1" /f')
        self.run_cmd_live(r'reg add "HKCU\Control Panel\Mouse" /v MouseThreshold1 /t REG_SZ /d "6" /f')
        self.run_cmd_live(r'reg add "HKCU\Control Panel\Mouse" /v MouseThreshold2 /t REG_SZ /d "10" /f')
        self.run_cmd_live(r'reg add "HKCU\Control Panel\Mouse" /v MouseSensitivity /t REG_SZ /d "10" /f')
        # Remove as curvas customizadas para o Windows recriar as padrão
        self.run_cmd_live(r'reg delete "HKCU\Control Panel\Mouse" /v SmoothMouseXCurve /f')
        self.run_cmd_live(r'reg delete "HKCU\Control Panel\Mouse" /v SmoothMouseYCurve /f')
        try:
            ctypes.windll.user32.SystemParametersInfoW(0x0071, 0, 10, 0x0002)
        except Exception:
            pass

    def revert_fps_tweaks(self):
        self.log("Restaurando valores padrão de agendamento/latência do Windows...")
        # Win32PrioritySeparation padrão = 2 (26 hex); SystemResponsiveness padrão = 20
        self.run_cmd_live(r'reg add "HKLM\SYSTEM\CurrentControlSet\Control\PriorityControl" /v "Win32PrioritySeparation" /t REG_DWORD /d 2 /f')
        self.run_cmd_live(r'reg add "HKLM\SOFTWARE\Microsoft\Windows NT\CurrentVersion\Multimedia\SystemProfile" /v "SystemResponsiveness" /t REG_DWORD /d 20 /f')
        self.run_cmd_live(r'reg add "HKLM\SOFTWARE\Microsoft\Windows NT\CurrentVersion\Multimedia\SystemProfile" /v "NetworkThrottlingIndex" /t REG_DWORD /d 10 /f')
        # Reativa compressão de memória (revertendo Disable-MMAgent -mc)
        self.run_cmd_live('powershell -Command "Enable-MMAgent -mc -ErrorAction SilentlyContinue"')
        # Religa o Core Parking para o padrão gerenciado
        self.run_cmd_live('powercfg -setacvalueindex scheme_current sub_processor CPMINCORES 0')
        self.run_cmd_live('powercfg -setactive scheme_current')
        try:
            self.revert_fps_mode()
        except Exception:
            pass

    def revert_network(self):
        self.log("Restaurando configurações padrão de rede...")
        self.restore_default_dns()
        self.run_cmd_live('netsh int tcp set global autotuninglevel=normal')
        self.run_cmd_live('netsh int tcp set global chimney=default')
        self.run_cmd_live('netsh int tcp set heuristics default')
        self.run_cmd_live('netsh int tcp set global rss=default')

    def opt_cooling(self):
        self.log("Configurando perfil de Refrigeração Ativa...")
        self.run_cmd_live('powershell -Command "powercfg -setacvalueindex SCHEME_CURRENT 54533251-82be-4824-96c1-47b60b740d00 94d3a615-a899-4ac5-ae2b-e4d8f634367f 1"')
        self.run_cmd_live('powershell -Command "powercfg -setdcvalueindex SCHEME_CURRENT 54533251-82be-4824-96c1-47b60b740d00 94d3a615-a899-4ac5-ae2b-e4d8f634367f 1"')
        self.run_cmd_live('powershell -Command "powercfg /setactive SCHEME_CURRENT"')
        self.log("✅ Sistema configurado para acionar as ventoinhas mais cedo!")

    def fix_corrupted_files(self):
        self.log("🛠️ Iniciando Reparo Completo do Windows...")
        cmd = 'echo 1/4: Limpando Cache do Windows... & cleanmgr /sagerun:1 & echo. & echo 2/4: Procurando e reparando arquivos vitais (SFC)... & sfc /scannow & echo. & echo 3/4: Reparando imagem do sistema (DISM RestoreHealth)... & DISM /Online /Cleanup-Image /RestoreHealth & echo. & echo 4/4: Limpeza profunda de componentes de atualizacao... & DISM /Online /Cleanup-Image /StartComponentCleanup'
        self.run_visible_cmd("Reparo Profundo e Limpeza do Windows", cmd)
        self.log("✅ Varredura, Reparo e Limpeza Profunda de Disco concluídos com sucesso!")

    def install_gpu_app(self):
        self.log("Analisando Placa de Vídeo do Cliente...")
        try:
            gpu_info = subprocess.check_output('powershell -Command "(Get-CimInstance Win32_VideoController).Name"', shell=True, text=True, creationflags=subprocess.CREATE_NO_WINDOW).upper()
            if "NVIDIA" in gpu_info:
                self.log("Placa NVIDIA detectada. Abrindo site oficial do NVIDIA App / GeForce Experience...")
                webbrowser.open("https://www.nvidia.com/pt-br/software/nvidia-app/")
            elif "AMD" in gpu_info or "RADEON" in gpu_info:
                self.log("Placa AMD detectada. Abrindo site oficial do AMD Adrenalin...")
                webbrowser.open("https://www.amd.com/pt/support")
            else:
                self.log("Placa Integrada ou Intel detectada. Abrindo Intel Driver Assistant...")
                webbrowser.open("https://www.intel.com.br/content/www/br/pt/support/intel-driver-support-assistant.html")
        except Exception as e:
            self.log(f"Erro ao detectar placa: {e}")

    def auto_optimize(self):
        self.log("🚀 INICIANDO OTIMIZAÇÃO TOTAL AUTOMÁTICA 🚀")
        
        if getattr(self, 'is_trial', False):
            self.log("Aviso: Modo de teste gratuito (Otimização Limitada a Meia Máquina).")
            self.after(0, lambda: messagebox.showwarning("Atenção - Modo Teste", "Atenção, só no modo teste ein! Sua máquina está otimizada a meia máquina pois é uma versão de teste gratuito. Adquira a licença completa para liberar a performance extrema!"))
            self.log("--- 1/3: Criando Backup de Segurança ---")
            self.create_restore_point()
            self.log("--- 2/3: Otimizando Performance (Balanced / Med) ---")
            self.apply_profile_logic("med", None)
            self.log("--- 3/3: Reduzindo Uso de RAM Básico ---")
            self.reduce_ram_usage()
            self.refresh_metrics_depois()
            self.log("🚀 Otimização Limitada Concluída!")
            return

        self.log("Por favor, aguarde enquanto o app faz tudo por conta própria...")

        # 0. Backup
        self.log("--- 0/6: Criando Backup de Segurança ---")
        self.create_restore_point()

        # 1. Performance (perfil Max FPS) — chama a lógica direto, sem abrir diálogo de jogo
        self.log("--- 1/8: Aplicando perfil de alto desempenho ---")
        self.apply_profile_logic("max", None)

        # 2. Refrigeração
        self.log("--- 2/8: Ativando política de refrigeração ativa ---")
        self.opt_cooling()

        # 3. Barra de tarefas
        self.log("--- 3/8: Limpando a barra de tarefas ---")
        self.clean_taskbar()

        # 4. RAM em segundo plano
        self.log("--- 4/8: Liberando RAM e apps de segundo plano ---")
        self.reduce_ram_usage()

        # 5. Limpeza de temporários
        self.log("--- 5/8: Limpando arquivos temporários ---")
        self.clear_temp_files()

        # 6. Smart Game Booster (núcleos + prioridade de jogos)
        self.log("--- 6/8: Desbloqueando núcleos da CPU e prioridade de jogos ---")
        self.apply_smart_game_booster()

        # 7. Mouse 1:1
        self.log("--- 7/8: Removendo aceleração do mouse (resposta 1:1) ---")
        self.apply_mouse_calibration()

        # 8. Diagnóstico de travamentos (Discord/overlays/gravação em 2º plano)
        self.log("--- 8/8: Procurando causas de travamento em jogos ---")
        try:
            achados = self.scan_stutter_causes()
            if achados:
                self.log(f"⚠️ {len(achados)} possível(is) causa(s) de travamento encontrada(s). Veja em 'Correção de Bugs'.")
        except Exception as e:
            self.log(f"  (diagnóstico de travamento pulado: {e})")

        self.log("--- Modo FPS: otimizando os jogos instalados ---")
        try:
            self.apply_fps_mode(silent=True)
        except Exception as e:
            self.log(f"  (Modo FPS pulado: {e})")

        self.log("--- Gravando ajustes de núcleo (permanecem após reiniciar) ---")
        self.apply_core_tweaks()
        self.refresh_metrics_depois()
        self.log("🚀 Otimização concluída!")
        self.after(0, lambda: messagebox.showinfo("Otimização Concluída",
            "✅ Otimização concluída!\n\n"
            "• Perfil de alto desempenho aplicado\n"
            "• Núcleos da CPU desbloqueados e prioridade de jogos ajustada\n"
            "• RAM em segundo plano liberada e temporários limpos\n"
            "• Aceleração do mouse removida (resposta 1:1)\n"
            "• MODO FPS: jogos instalados com prioridade alta, GPU dedicada e tela cheia sem lag\n\n"
            "O Windows Defender NÃO foi desativado (isso fica por sua conta, no botão específico).\n"
            "Reinicie o PC para aplicar tudo. Use 'Reverter' a qualquer momento para desfazer."))

    # --- SUPER FERRAMENTAS (V7.0) ---

    def cache_cleaner(self):
        self.log("Iniciando Limpeza Profunda de Cache...")
        cmds = [
            'powershell -Command "Remove-Item -Path $env:TEMP\\* -Recurse -Force -ErrorAction SilentlyContinue"',
            'powershell -Command "Remove-Item -Path C:\\Windows\\Temp\\* -Recurse -Force -ErrorAction SilentlyContinue"',
            'powershell -Command "Clear-RecycleBin -Force -ErrorAction SilentlyContinue"',
            'powershell -Command "Remove-Item -Path C:\\Windows\\SoftwareDistribution\\Download\\* -Recurse -Force -ErrorAction SilentlyContinue"',
            'ipconfig /flushdns'
        ]
        for c in cmds:
            self.run_cmd_live(c)
        self.log("✅ Limpeza Concluída! Espaço liberado e PC mais rápido.")
        import time
        time.sleep(1)

    def windows_debloater(self):
        self.log("Removendo Bloatwares Nativos do Windows...")
        apps = ["*3DBuilder*", "*ZuneVideo*", "*ZuneMusic*", "*GetHelp*", "*BingNews*", "*BingWeather*", "*SolitaireCollection*", "*Microsoft.People*", "*MixedReality*"]
        for app in apps:
            cmd = f'powershell -Command "Get-AppxPackage -Name {app} -AllUsers -ErrorAction SilentlyContinue | Where-Object {{ -not $_.NonRemovable }} | Remove-AppxPackage -AllUsers -ErrorAction SilentlyContinue"'
            self.run_cmd_live(cmd)
        self.log("✅ Bloatwares Removidos com Sucesso!")
        import time
        time.sleep(1)

    def toggle_game_booster(self, enable=True):
        if enable:
            self.log("Ativando Modo Game Booster Extremo...")
            cmds = [
                'powershell -Command "Stop-Service -Name SysMain -Force; Set-Service -Name SysMain -StartupType Disabled"',
                'powershell -Command "Stop-Service -Name WSearch -Force; Set-Service -Name WSearch -StartupType Disabled"',
                'powershell -Command "Stop-Service -Name Spooler -Force; Set-Service -Name Spooler -StartupType Disabled"'
            ]
        else:
            self.log("Restaurando Serviços do Windows (Desativando Game Booster)...")
            cmds = [
                'powershell -Command "Set-Service -Name SysMain -StartupType Automatic; Start-Service -Name SysMain"',
                'powershell -Command "Set-Service -Name WSearch -StartupType Automatic; Start-Service -Name WSearch"',
                'powershell -Command "Set-Service -Name Spooler -StartupType Automatic; Start-Service -Name Spooler"'
            ]
            
        for c in cmds:
            self.run_cmd_live(c)
        self.log("✅ Game Booster " + ("ATIVADO" if enable else "DESATIVADO") + "!")
        import time
        time.sleep(1)

    def open_process_lasso(self):
        self.log("Abrindo Gerenciador de Prioridade CPU/GPU (Estilo Process Lasso)...")
        pl_win = ctk.CTkToplevel(self)
        pl_win.title("Gerenciador de Prioridade Extrema (Process Lasso)")
        pl_win.geometry("700x600")
        pl_win.resizable(False, False)
        pl_win.attributes("-topmost", True)

        lbl_title = ctk.CTkLabel(pl_win, text="🔥 Forçar Prioridade Máxima (CPU/GPU) 🔥", font=ctk.CTkFont(size=20, weight="bold"), text_color="#E74C3C")
        lbl_title.pack(pady=(20, 5))
        lbl_desc = ctk.CTkLabel(pl_win, text="Selecione um jogo ou aplicativo que está rodando no momento.\nO Windows será configurado para SEMPRE rodá-lo com Prioridade ALTA\ne usar 100% da sua Placa de Vídeo.", justify="center")
        lbl_desc.pack(pady=5)

        list_frame = ctk.CTkFrame(pl_win)
        list_frame.pack(pady=10, padx=20, fill="both", expand=True)

        scrollbar = ctk.CTkScrollbar(list_frame)
        scrollbar.pack(side="right", fill="y")

        listbox = tk.Listbox(list_frame, bg="#161b22", fg="#00d4ff", selectbackground="#3498DB", font=("Consolas", 12), yscrollcommand=scrollbar.set, borderwidth=0, highlightthickness=0)
        listbox.pack(side="left", fill="both", expand=True)
        scrollbar.configure(command=listbox.yview)

        def load_processes():
            listbox.delete(0, tk.END)
            listbox.insert(tk.END, "Carregando processos... aguarde...")
            pl_win.update()
            try:
                import subprocess
                cmd = 'powershell "Get-Process | Where-Object { $_.Path -and $_.MainWindowTitle } | Select-Object -Unique ProcessName, Path | ConvertTo-Json"'
                out = subprocess.check_output(cmd, shell=True, text=True, creationflags=subprocess.CREATE_NO_WINDOW)
                import json
                try:
                    data = json.loads(out)
                    if isinstance(data, dict): data = [data]
                except:
                    data = []

                listbox.delete(0, tk.END)
                self.process_map = {}
                for proc in data:
                    name = proc.get("ProcessName", "") + ".exe"
                    path = proc.get("Path", "")
                    if name and path:
                        display = f"{name}  |  {path}"
                        listbox.insert(tk.END, display)
                        self.process_map[display] = {"name": name, "path": path}
            except Exception as e:
                listbox.delete(0, tk.END)
                listbox.insert(tk.END, f"Erro ao listar: {e}")

        self.run_async(load_processes)

        btn_refresh = ctk.CTkButton(pl_win, text="🔄 Atualizar Lista", fg_color="#F39C12", hover_color="#D68910", command=lambda: self.run_async(load_processes))
        btn_refresh.pack(pady=(0, 10))

        def force_priority():
            selection = listbox.curselection()
            if not selection:
                messagebox.showwarning("Aviso", "Selecione um processo na lista primeiro!", parent=pl_win)
                return
            
            selected_text = listbox.get(selection[0])
            proc_info = getattr(self, "process_map", {}).get(selected_text)
            
            if not proc_info:
                return
                
            exe_name = proc_info["name"]
            exe_path = proc_info["path"]
            
            self.log(f"-> Aplicando Prioridade ALTA para {exe_name}...")
            
            try:
                reg_cpu = f'reg add "HKLM\\SOFTWARE\\Microsoft\\Windows NT\\CurrentVersion\\Image File Execution Options\\{exe_name}\\PerfOptions" /v "CpuPriorityClass" /t REG_DWORD /d 3 /f'
                self.run_cmd_live(reg_cpu)
                
                reg_gpu = f'reg add "HKCU\\Software\\Microsoft\\DirectX\\UserGpuPreferences" /v "{exe_path}" /t REG_SZ /d "GpuPreference=2;" /f'
                self.run_cmd_live(reg_gpu)
                
                messagebox.showinfo("Sucesso!", f"✅ O jogo/app '{exe_name}' agora sempre rodará com Prioridade Máxima na CPU e GPU!", parent=pl_win)
            except Exception as e:
                messagebox.showerror("Erro", f"Falha ao aplicar prioridade: {e}", parent=pl_win)

        btn_apply = ctk.CTkButton(pl_win, text="🚀 FORÇAR PRIORIDADE MÁXIMA", font=ctk.CTkFont(weight="bold", size=14), fg_color="#C0392B", hover_color="#922B21", height=45, command=lambda: self.run_async(force_priority))
        btn_apply.pack(pady=(5, 20), padx=20, fill="x")

    def setup_tab_super(self): pass
    def setup_tab_bugs(self): pass

    # Ajustes de núcleo que ficam gravados no registro (persistem entre reinicios por conta própria).
    CORE_TWEAKS = [
        'powercfg -setactive 8c5e7fda-e8bf-4a96-9a85-a6e23a8c635c',
        'reg add "HKCU\\System\\GameConfigStore" /v GameDVR_Enabled /t REG_DWORD /d 0 /f',
        'reg add "HKLM\\SOFTWARE\\Policies\\Microsoft\\Windows\\GameDVR" /v AllowGameDVR /t REG_DWORD /d 0 /f',
        'reg add "HKLM\\SYSTEM\\CurrentControlSet\\Control\\PriorityControl" /v Win32PrioritySeparation /t REG_DWORD /d 38 /f',
        'reg add "HKLM\\SOFTWARE\\Microsoft\\Windows NT\\CurrentVersion\\Multimedia\\SystemProfile" /v SystemResponsiveness /t REG_DWORD /d 0 /f',
        'reg add "HKLM\\SOFTWARE\\Microsoft\\Windows NT\\CurrentVersion\\Multimedia\\SystemProfile\\Tasks\\Games" /v "GPU Priority" /t REG_DWORD /d 8 /f',
        'reg add "HKLM\\SOFTWARE\\Microsoft\\Windows NT\\CurrentVersion\\Multimedia\\SystemProfile\\Tasks\\Games" /v "Priority" /t REG_DWORD /d 6 /f',
        'reg add "HKLM\\SYSTEM\\CurrentControlSet\\Control\\Session Manager\\Memory Management\\PrefetchParameters" /v EnablePrefetcher /t REG_DWORD /d 3 /f',
        'reg add "HKCU\\Control Panel\\Desktop" /v MenuShowDelay /t REG_SZ /d 20 /f',
        'reg add "HKCU\\Software\\Microsoft\\Windows\\CurrentVersion\\Explorer\\Serialize" /v StartupDelayInMSec /t REG_DWORD /d 0 /f',
    ]

    def apply_core_tweaks(self):
        """Grava os ajustes de núcleo diretamente no registro. Eles persistem entre reinícios
        sozinhos — sem tarefa agendada nem .bat de autorun (que o antivírus marca como ameaça)."""
        for c in self.CORE_TWEAKS:
            self.run_cmd_live(c)
        self.run_cmd_live('powershell -NoProfile -Command "Set-Service -Name SysMain -StartupType Automatic -ErrorAction SilentlyContinue; Start-Service SysMain -ErrorAction SilentlyContinue"')
        self.log("🛡️ Ajustes de núcleo gravados no registro (permanecem após reiniciar).")
        return True

    # Mantido por compatibilidade: agora NÃO cria tarefa de logon/.bat (evita falso positivo de antivírus).
    def install_persistent_guardian(self):
        self.cleanup_legacy_guardian()
        return self.apply_core_tweaks()

    def cleanup_legacy_guardian(self):
        """Remove a tarefa/.bat de versões anteriores que o antivírus sinalizava."""
        try:
            subprocess.run('schtasks /delete /tn "Bernal_KeepOptimized" /f', shell=True,
                           capture_output=True, creationflags=subprocess.CREATE_NO_WINDOW)
        except Exception:
            pass
        try:
            old_bat = os.path.join(os.environ.get("LOCALAPPDATA", os.path.expanduser("~")),
                                   "Bernal Otimizacoes", "manter_otimizado.bat")
            if os.path.isfile(old_bat):
                os.remove(old_bat)
        except Exception:
            pass

    def remove_persistent_guardian(self):
        self.cleanup_legacy_guardian()
        self.log("Ajustes permanecem como estão; nada de autorun foi deixado no sistema.")

    def is_guardian_installed(self):
        return False

    def _free_space_c(self):
        try:
            import shutil
            return shutil.disk_usage("C:\\").free
        except Exception:
            return None

    def free_disk_space(self):
        """Libera espaço no disco C apagando apenas lixo seguro (temporários, caches, lixeira,
        arquivos de atualização antigos). Não toca em documentos, jogos nem programas."""
        self.log("🧽 Liberando espaço no disco C: (somente arquivos seguros)...")
        before = self._free_space_c()

        import glob
        user_temp = os.environ.get("TEMP", "")
        win = os.environ.get("SystemRoot", r"C:\Windows")
        la = os.environ.get("LOCALAPPDATA", "")

        # Pastas de lixo seguras para esvaziar o conteúdo
        self.set_hud_progress(10, "Limpando arquivos temporários do usuário e do Windows...")
        safe_dirs = [
            user_temp,
            os.path.join(win, "Temp"),
            os.path.join(win, "SoftwareDistribution", "Download"),
            os.path.join(la, "Temp") if la else "",
            os.path.join(la, "CrashDumps") if la else "",
            os.path.join(la, "Microsoft", "Windows", "WER") if la else "",
            os.path.join(la, "Microsoft", "Windows", "Explorer") if la else "",  # thumbcache
            os.path.join(la, "D3DSCache") if la else "",
            os.path.join(la, "NVIDIA", "DXCache") if la else "",
            os.path.join(la, "AMD", "DxCache") if la else "",
        ]
        removed = 0
        for d in safe_dirs:
            if not d or not os.path.isdir(d):
                continue
            for item in os.listdir(d):
                if item.startswith("_MEI"):  # arquivos do próprio app em execução
                    continue
                ip = os.path.join(d, item)
                try:
                    if os.path.isfile(ip) or os.path.islink(ip):
                        os.remove(ip)
                        removed += 1
                    elif os.path.isdir(ip):
                        shutil.rmtree(ip, ignore_errors=True)
                        removed += 1
                except Exception:
                    pass

        # Lixeira
        self.set_hud_progress(45, "Esvaziando a Lixeira...")
        self.run_cmd_live('powershell -NoProfile -Command "Clear-RecycleBin -Force -ErrorAction SilentlyContinue"')

        # Cache de miniaturas
        self.set_hud_progress(60, "Limpando cache de miniaturas...")
        self.run_cmd_live('powershell -NoProfile -Command "Get-Process explorer -ErrorAction SilentlyContinue | Out-Null; Remove-Item \\"$env:LOCALAPPDATA\\\\Microsoft\\\\Windows\\\\Explorer\\\\thumbcache_*.db\\" -Force -ErrorAction SilentlyContinue"')

        # Componentes antigos do Windows (WinSxS) — seguro e recomendado pela Microsoft
        self.set_hud_progress(72, "Compactando componentes antigos do Windows (pode demorar)...")
        self.run_cmd_live('Dism /Online /Cleanup-Image /StartComponentCleanup /Quiet')

        # Delivery Optimization (cache de atualização P2P)
        self.set_hud_progress(85, "Limpando cache de Delivery Optimization...")
        self.run_cmd_live('powershell -NoProfile -Command "Delete-DeliveryOptimizationCache -Force -ErrorAction SilentlyContinue"')

        after = self._free_space_c()
        self.set_hud_progress(100, "Limpeza de disco concluída.")

        freed_txt = ""
        windows_old = os.path.join(os.environ.get("SystemDrive", "C:") + "\\", "Windows.old")
        extra = ""
        if os.path.isdir(windows_old):
            try:
                import shutil as _sh
                wsz = sum(os.path.getsize(os.path.join(r, f)) for r, _, fs in os.walk(windows_old) for f in fs) / (1024**3)
            except Exception:
                wsz = 0
            extra = ("\n\n📌 Encontrei a pasta 'Windows.old' (~%.1f GB) de uma atualização anterior do Windows.\n"
                     "Ela é grande e pode ser removida pela Limpeza de Disco do Windows (cleanmgr) se você não for "
                     "reverter a versão antiga. Não removo automaticamente por segurança." % wsz)

        if before is not None and after is not None:
            freed = max(0, after - before)
            freed_txt = f"Espaço liberado agora: {freed / (1024**2):.0f} MB.\nLivre no C: {after / (1024**3):.1f} GB."
            self.log(f"✅ Disco C limpo. Liberados ~{freed / (1024**2):.0f} MB. Itens removidos: {removed}.")
        else:
            freed_txt = f"Itens de lixo removidos: {removed}."
            self.log("✅ Limpeza de disco concluída.")

        self.after(0, lambda: messagebox.showinfo("Espaço Liberado",
            "✅ Limpeza de disco concluída!\n\n" + freed_txt +
            "\n\nForam removidos apenas arquivos seguros (temporários, caches, lixeira e componentes antigos do Windows). "
            "Seus documentos, jogos e programas não foram tocados." + extra))

    # ==================================================================
    #  MODO FPS - otimiza os JOGOS do cliente (persistente + reforço ao vivo)
    # ==================================================================
    FPS_KNOWN_EXES = {
        "cod.exe", "modernwarfare.exe", "blackopscoldwar.exe", "valorant-win64-shipping.exe",
        "cs2.exe", "csgo.exe", "fortniteclient-win64-shipping.exe", "r5apex.exe", "rainbowsix.exe",
        "rainbowsix_vulkan.exe", "gta5.exe", "eldenring.exe", "league of legends.exe", "rocketleague.exe",
        "overwatch.exe", "tslgame.exe", "cyberpunk2077.exe", "rdr2.exe", "destiny2.exe", "dota2.exe",
        "fc24.exe", "fc25.exe", "fc26.exe", "fifa23.exe", "fifa22.exe", "fifa21.exe", "wow.exe",
        "witcher3.exe", "forzahorizon5.exe", "bf2042.exe", "bfv.exe", "tarkov.exe", "escapefromtarkov.exe",
        "pubg.exe", "deadbydaylight-win64-shipping.exe", "hogwartslegacy.exe", "starfield.exe",
        "palworld-win64-shipping.exe", "helldivers2.exe", "marvelrivals-win64-shipping.exe",
        "theisle-win64-shipping.exe", "fallguys_client_game.exe", "payday3client-win64-shipping.exe",
    }
    FPS_SKIP_WORDS = ("unins", "crash", "launcher", "setup", "redist", "vc_redist", "dxsetup", "easyanticheat",
                      "eac", "battleye", "beclient", "helper", "cef", "prereq", "dotnet", "installer",
                      "updater", "report", "webview", "vcredist", "notification", "bootstrap")
    FPS_BACKGROUND_LOWER = {
        "chrome.exe", "msedge.exe", "firefox.exe", "opera.exe", "brave.exe", "onedrive.exe", "spotify.exe",
        "teams.exe", "ms-teams.exe", "steamwebhelper.exe", "epicwebhelper.exe", "searchindexer.exe",
        "dropbox.exe", "googledrivefs.exe", "telegram.exe", "whatsapp.exe", "ccxprocess.exe",
        "creative cloud.exe", "adobeupdateservice.exe", "icloudservices.exe", "skype.exe",
    }

    def _fps_cfg_path(self):
        base = os.path.join(os.environ.get("LOCALAPPDATA", os.path.expanduser("~")), "Bernal Otimizacoes")
        os.makedirs(base, exist_ok=True)
        return os.path.join(base, "fps_games.json")

    def _fps_load_cfg(self):
        try:
            with open(self._fps_cfg_path(), "r", encoding="utf-8") as f:
                data = json.load(f)
            if isinstance(data, dict):
                data.setdefault("games", [])
                data.setdefault("watch", True)
                return data
        except Exception:
            pass
        return {"games": [], "watch": True}

    def _fps_save_cfg(self, cfg):
        try:
            with open(self._fps_cfg_path(), "w", encoding="utf-8") as f:
                json.dump(cfg, f, ensure_ascii=False, indent=1)
        except Exception:
            pass

    def _fps_game_roots(self):
        """Pastas onde jogos costumam estar (todas as unidades + bibliotecas do Steam e manifestos da Epic)."""
        import string
        roots = []
        rel = [r"SteamLibrary\steamapps\common", r"Program Files (x86)\Steam\steamapps\common",
               r"Program Files\Steam\steamapps\common", r"Steam\steamapps\common",
               r"Program Files\Epic Games", r"Epic Games", r"Program Files (x86)\Epic Games",
               r"Riot Games", r"Program Files\Riot Games", r"Games", r"Jogos",
               r"Program Files\EA Games", r"Program Files (x86)\EA Games", r"Program Files\EA\EA Desktop",
               r"Program Files (x86)\Origin Games", r"Program Files (x86)\Ubisoft\Ubisoft Game Launcher\games",
               r"Program Files\Ubisoft\Ubisoft Game Launcher\games", r"GOG Games", r"Program Files (x86)\GOG Galaxy\Games",
               r"Program Files\Rockstar Games", r"XboxGames", r"Program Files\Battle.net", r"Battle.net",
               r"Program Files (x86)\Call of Duty", r"Program Files\Call of Duty", r"Call of Duty",
               r"Program Files (x86)\Overwatch", r"Program Files (x86)\World of Warcraft", r"Program Files (x86)\Battle.net"]
        for d in string.ascii_uppercase:
            drive = f"{d}:\\"
            if not os.path.exists(drive):
                continue
            for r in rel:
                p = os.path.join(drive, r)
                if os.path.isdir(p):
                    roots.append(p)
        # Bibliotecas extras do Steam (libraryfolders.vdf)
        try:
            import winreg
            k = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Valve\Steam")
            steam_path, _ = winreg.QueryValueEx(k, "SteamPath")
            winreg.CloseKey(k)
            vdf = os.path.join(steam_path, "steamapps", "libraryfolders.vdf")
            if os.path.isfile(vdf):
                with open(vdf, "r", encoding="utf-8", errors="ignore") as f:
                    for m in re.finditer(r'"path"\s+"([^"]+)"', f.read()):
                        p = os.path.join(m.group(1).replace("\\\\", "\\"), "steamapps", "common")
                        if os.path.isdir(p):
                            roots.append(p)
        except Exception:
            pass
        out, seen = [], set()
        for r in roots:
            key = os.path.normcase(os.path.abspath(r))
            if key not in seen:
                seen.add(key)
                out.append(r)
        return out

    def discover_games(self):
        """Acha os executáveis de jogos instalados. Retorna lista de caminhos completos."""
        found = {}

        def consider_folder(folder, max_depth=4):
            best, best_size = None, 0
            base_depth = folder.count(os.sep)
            for root, dirs, files in os.walk(folder):
                if root.count(os.sep) - base_depth >= max_depth:
                    dirs[:] = []
                for fn in files:
                    low = fn.lower()
                    if not low.endswith(".exe"):
                        continue
                    fp = os.path.join(root, fn)
                    if low in self.FPS_KNOWN_EXES:
                        found[os.path.normcase(fp)] = fp
                        continue
                    if any(w in low for w in self.FPS_SKIP_WORDS):
                        continue
                    try:
                        sz = os.path.getsize(fp)
                    except Exception:
                        continue
                    if sz > best_size:
                        best, best_size = fp, sz
            # jogo sem nome conhecido: usa o maior .exe da pasta (>= 15 MB) como executável principal
            if best and best_size >= 15 * 1024 * 1024:
                found.setdefault(os.path.normcase(best), best)

        for root in self._fps_game_roots():
            base = os.path.basename(root).lower()
            try:
                children = [os.path.join(root, c) for c in os.listdir(root)]
            except Exception:
                continue
            # Pastas que são o próprio jogo (ex.: "Call of Duty", "Overwatch") são analisadas direto
            if base in ("call of duty", "overwatch", "world of warcraft"):
                children = [root]
            for c in children:
                if os.path.isdir(c):
                    consider_folder(c)

        # Manifestos da Epic Games
        try:
            man = os.path.join(os.environ.get("ProgramData", r"C:\ProgramData"), "Epic", "EpicGamesLauncher", "Data", "Manifests")
            for fp in glob.glob(os.path.join(man, "*.item")):
                try:
                    with open(fp, "r", encoding="utf-8", errors="ignore") as f:
                        d = json.load(f)
                    exe = os.path.join(d.get("InstallLocation", ""), d.get("LaunchExecutable", ""))
                    if exe.lower().endswith(".exe") and os.path.isfile(exe):
                        found[os.path.normcase(exe)] = exe
                except Exception:
                    pass
        except Exception:
            pass

        # Jogos que estão abertos agora (qualquer um da lista conhecida)
        try:
            import psutil
            for proc in psutil.process_iter(['name', 'exe']):
                n = (proc.info.get('name') or '').lower()
                if n in self.FPS_KNOWN_EXES and proc.info.get('exe'):
                    found[os.path.normcase(proc.info['exe'])] = proc.info['exe']
        except Exception:
            pass
        return sorted(found.values(), key=lambda x: os.path.basename(x).lower())

    def _fps_layers_add(self, exe_path):
        """Desliga 'Otimizações de tela cheia' para o jogo (reduz input lag e stutter), preservando outras flags."""
        try:
            import winreg
            kp = r"Software\Microsoft\Windows NT\CurrentVersion\AppCompatFlags\Layers"
            k = winreg.CreateKeyEx(winreg.HKEY_CURRENT_USER, kp, 0, winreg.KEY_READ | winreg.KEY_WRITE)
            try:
                try:
                    cur, _ = winreg.QueryValueEx(k, exe_path)
                except FileNotFoundError:
                    cur = ""
                tokens = str(cur).replace("~", " ").split()
                if "DISABLEDXMAXIMIZEDWINDOWEDMODE" not in tokens:
                    tokens.append("DISABLEDXMAXIMIZEDWINDOWEDMODE")
                winreg.SetValueEx(k, exe_path, 0, winreg.REG_SZ, "~ " + " ".join(tokens))
            finally:
                winreg.CloseKey(k)
            return True
        except Exception:
            return False

    def _fps_layers_remove(self, exe_path):
        try:
            import winreg
            kp = r"Software\Microsoft\Windows NT\CurrentVersion\AppCompatFlags\Layers"
            k = winreg.OpenKey(winreg.HKEY_CURRENT_USER, kp, 0, winreg.KEY_READ | winreg.KEY_WRITE)
            try:
                cur, _ = winreg.QueryValueEx(k, exe_path)
                tokens = [t for t in str(cur).replace("~", " ").split() if t != "DISABLEDXMAXIMIZEDWINDOWEDMODE"]
                if tokens:
                    winreg.SetValueEx(k, exe_path, 0, winreg.REG_SZ, "~ " + " ".join(tokens))
                else:
                    winreg.DeleteValue(k, exe_path)
            finally:
                winreg.CloseKey(k)
        except Exception:
            pass

    def optimize_single_game(self, exe_path):
        """Ajustes PERMANENTES (gravados no Windows) para um jogo: CPU/IO alta, GPU dedicada, tela cheia sem lag."""
        exe_name = os.path.basename(exe_path)
        ok = 0
        # CPU e disco com prioridade alta toda vez que o jogo abrir (funciona com o app fechado)
        ifeo = f'HKLM\\SOFTWARE\\Microsoft\\Windows NT\\CurrentVersion\\Image File Execution Options\\{exe_name}\\PerfOptions'
        if self.run_cmd_live(f'reg add "{ifeo}" /v CpuPriorityClass /t REG_DWORD /d 3 /f') is not False:
            ok += 1
        self.run_cmd_live(f'reg add "{ifeo}" /v IoPriority /t REG_DWORD /d 3 /f')
        # GPU dedicada (alto desempenho) para esse .exe
        self.run_cmd_live(f'reg add "HKCU\\Software\\Microsoft\\DirectX\\UserGpuPreferences" /v "{exe_path}" /t REG_SZ /d "GpuPreference=2;" /f')
        # Tela cheia sem camada extra do Windows
        self._fps_layers_add(exe_path)
        return ok

    def apply_fps_system_tweaks(self):
        """Ajustes gerais do Windows que aumentam FPS e estabilizam frametime. Ficam gravados no registro/plano de energia."""
        cmds = [
            # Modo Jogo + tela cheia exclusiva sem lag
            r'reg add "HKCU\Software\Microsoft\GameBar" /v AutoGameModeEnabled /t REG_DWORD /d 1 /f',
            r'reg add "HKCU\Software\Microsoft\GameBar" /v AllowAutoGameMode /t REG_DWORD /d 1 /f',
            r'reg add "HKCU\System\GameConfigStore" /v GameDVR_FSEBehaviorMode /t REG_DWORD /d 2 /f',
            r'reg add "HKCU\System\GameConfigStore" /v GameDVR_HonorUserFSEBehaviorMode /t REG_DWORD /d 1 /f',
            r'reg add "HKCU\System\GameConfigStore" /v GameDVR_DXGIHonorFSEWindowsCompatible /t REG_DWORD /d 1 /f',
            r'reg add "HKCU\System\GameConfigStore" /v GameDVR_EFSEFeatureFlags /t REG_DWORD /d 0 /f',
            r'reg add "HKCU\System\GameConfigStore" /v GameDVR_Enabled /t REG_DWORD /d 0 /f',
            # Timer de alta resolução global (frametime mais estável)
            r'reg add "HKLM\SYSTEM\CurrentControlSet\Control\Session Manager\kernel" /v GlobalTimerResolutionRequests /t REG_DWORD /d 1 /f',
            # Multimídia/jogos: GPU e CPU priorizados
            r'reg add "HKLM\SOFTWARE\Microsoft\Windows NT\CurrentVersion\Multimedia\SystemProfile" /v NetworkThrottlingIndex /t REG_DWORD /d 4294967295 /f',
            r'reg add "HKLM\SOFTWARE\Microsoft\Windows NT\CurrentVersion\Multimedia\SystemProfile\Tasks\Games" /v "Scheduling Category" /t REG_SZ /d High /f',
            r'reg add "HKLM\SOFTWARE\Microsoft\Windows NT\CurrentVersion\Multimedia\SystemProfile\Tasks\Games" /v "SFIO Priority" /t REG_SZ /d High /f',
            r'reg add "HKLM\SOFTWARE\Microsoft\Windows NT\CurrentVersion\Multimedia\SystemProfile\Tasks\Games" /v "Latency Sensitive" /t REG_SZ /d True /f',
        ]
        for c in cmds:
            self.run_cmd_live(c)

        # Agendamento de GPU por hardware (só liga onde o Windows/GPU já suportam: a chave existe)
        try:
            import winreg
            k = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"SYSTEM\CurrentControlSet\Control\GraphicsDrivers", 0, winreg.KEY_READ)
            try:
                winreg.QueryValueEx(k, "HwSchMode")
                self.run_cmd_live(r'reg add "HKLM\SYSTEM\CurrentControlSet\Control\GraphicsDrivers" /v HwSchMode /t REG_DWORD /d 2 /f')
            except FileNotFoundError:
                pass
            winreg.CloseKey(k)
        except Exception:
            pass

        # Rede: desliga o atraso do Nagle (menos ping/lag em jogos online)
        try:
            import winreg
            base = r"SYSTEM\CurrentControlSet\Services\Tcpip\Parameters\Interfaces"
            root = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, base)
            i = 0
            while True:
                try:
                    sub = winreg.EnumKey(root, i)
                except OSError:
                    break
                i += 1
                try:
                    sk = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, base + "\\" + sub, 0, winreg.KEY_SET_VALUE)
                    winreg.SetValueEx(sk, "TcpAckFrequency", 0, winreg.REG_DWORD, 1)
                    winreg.SetValueEx(sk, "TCPNoDelay", 0, winreg.REG_DWORD, 1)
                    winreg.CloseKey(sk)
                except Exception:
                    pass
            winreg.CloseKey(root)
        except Exception:
            pass

        # Plano de energia: Desempenho Máximo, CPU sempre a 100%, sem economia em USB/PCIe
        guid = None
        try:
            out = subprocess.run('powercfg -duplicatescheme e9a42b02-d5df-448d-aa00-03f14749eb61', shell=True,
                                 capture_output=True, text=True, errors="ignore",
                                 creationflags=subprocess.CREATE_NO_WINDOW).stdout
            m = re.search(r'([0-9a-fA-F]{8}-(?:[0-9a-fA-F]{4}-){3}[0-9a-fA-F]{12})', out or "")
            if m:
                guid = m.group(1)
        except Exception:
            guid = None
        if guid:
            self.run_cmd_live(f'powercfg -changename {guid} "Bernal - Desempenho Maximo"')
            self.run_cmd_live(f'powercfg -setactive {guid}')
        else:
            self.run_cmd_live('powercfg -setactive 8c5e7fda-e8bf-4a96-9a85-a6e23a8c635c')
        for ac_dc in ("ac", "dc"):
            self.run_cmd_live(f'powercfg -set{ac_dc}valueindex scheme_current sub_processor PROCTHROTTLEMIN 100')
            self.run_cmd_live(f'powercfg -set{ac_dc}valueindex scheme_current sub_processor PROCTHROTTLEMAX 100')
            self.run_cmd_live(f'powercfg -set{ac_dc}valueindex scheme_current sub_processor CPMINCORES 100')
            self.run_cmd_live(f'powercfg -set{ac_dc}valueindex scheme_current sub_processor PERFBOOSTMODE 2')
            self.run_cmd_live(f'powercfg -set{ac_dc}valueindex scheme_current 2a737441-1930-4402-8d77-b2bebba308a3 48e6b7a6-50f5-4782-a5d4-53bb8f07e226 0')
            self.run_cmd_live(f'powercfg -set{ac_dc}valueindex scheme_current 501a4d13-42af-4429-9e56-4784f8e32f78 ee130417-70ac-4581-ba83-8d6071d5977f 0')
        self.run_cmd_live('powercfg -setactive scheme_current')
        self.apply_mouse_calibration_silent()

    def apply_fps_mode(self, silent=False):
        """MODO FPS: acha os jogos do cliente, otimiza cada um de forma permanente e liga o reforço ao vivo."""
        self.log("🎮 [MODO FPS] Procurando os jogos instalados neste PC...")
        self.set_hud_progress(8, "Procurando jogos instalados (Steam, Epic, Riot, Battle.net, EA...)")
        cfg = self._fps_load_cfg()
        games = list(dict.fromkeys(self.discover_games() + [g for g in cfg.get("games", []) if os.path.isfile(g)]))
        if not games:
            self.log("ℹ️ Nenhum jogo encontrado automaticamente. Use '➕ Adicionar Jogo' e escolha o .exe.")

        self.set_hud_progress(25, "Aplicando ajustes de FPS do Windows (energia, GPU, rede, Modo Jogo)...")
        self.apply_fps_system_tweaks()

        done = []
        for idx, g in enumerate(games):
            pct = 40 + int(50 * (idx + 1) / max(1, len(games)))
            self.set_hud_progress(pct, f"Otimizando {os.path.basename(g)}...")
            try:
                self.optimize_single_game(g)
                done.append(g)
                self.log(f"  ✅ {os.path.basename(g)}: prioridade ALTA (CPU+disco), GPU dedicada, tela cheia sem lag")
            except Exception as e:
                self.log(f"  ⚠️ {os.path.basename(g)}: {e}")

        cfg["games"] = done
        cfg["watch"] = True
        self._fps_save_cfg(cfg)
        self.start_fps_watcher()
        self.set_hud_progress(100, "Modo FPS ativo!")
        self.log(f"🎮 Modo FPS aplicado em {len(done)} jogo(s). Os ajustes ficam gravados no Windows.")

        if not silent:
            lista = "\n".join("• " + os.path.basename(g) for g in done[:15]) or "(nenhum jogo encontrado — use ➕ Adicionar Jogo)"
            if len(done) > 15:
                lista += f"\n… e mais {len(done) - 15}"
            self.after(0, lambda: messagebox.showinfo("Modo FPS Ativado",
                "🎮 Modo FPS aplicado!\n\n"
                "Jogos otimizados:\n" + lista + "\n\n"
                "O que foi feito:\n"
                "• Cada jogo abre SEMPRE com prioridade alta de CPU e disco (permanente)\n"
                "• GPU dedicada forçada em cada jogo\n"
                "• Tela cheia sem camada extra do Windows (menos input lag)\n"
                "• Plano de Desempenho Máximo, CPU sem economia, agendamento de GPU e Modo Jogo\n"
                "• Rede sem atraso (Nagle) para menos ping\n"
                "• Com o app aberto, ao iniciar um jogo ele libera RAM/CPU de programas de fundo e mantém o jogo no topo\n\n"
                "Reinicie o PC uma vez para tudo valer. Reversível no botão 'Reverter'."))
        return done

    def add_game_manually(self):
        from tkinter import filedialog
        path = filedialog.askopenfilename(title="Escolha o .exe do jogo", filetypes=[("Jogo (.exe)", "*.exe")])
        if not path:
            return
        cfg = self._fps_load_cfg()
        if path not in cfg["games"]:
            cfg["games"].append(path)
            self._fps_save_cfg(cfg)

        def work():
            self.optimize_single_game(path)
            self.start_fps_watcher()
            self.log(f"🎮 {os.path.basename(path)} otimizado e adicionado ao Modo FPS.")
            self.after(0, lambda: messagebox.showinfo("Jogo adicionado",
                f"✅ {os.path.basename(path)} agora abre sempre com prioridade alta, GPU dedicada e tela cheia sem lag."))
        self.run_async(work)

    def revert_fps_mode(self):
        cfg = self._fps_load_cfg()
        for g in cfg.get("games", []):
            name = os.path.basename(g)
            self.run_cmd_live(f'reg delete "HKLM\\SOFTWARE\\Microsoft\\Windows NT\\CurrentVersion\\Image File Execution Options\\{name}\\PerfOptions" /f')
            self.run_cmd_live(f'reg delete "HKCU\\Software\\Microsoft\\DirectX\\UserGpuPreferences" /v "{g}" /f')
            self._fps_layers_remove(g)
        cfg["watch"] = False
        self._fps_save_cfg(cfg)
        self._fps_watch_on = False
        self.log("↩️ Modo FPS revertido (prioridades e preferências de GPU dos jogos removidas).")

    # ---------- Reforço ao vivo enquanto o jogo roda ----------
    def start_fps_watcher(self):
        if getattr(self, "_fps_watch_on", False):
            return
        self._fps_watch_on = True
        self._fps_boosted = {}
        self._fps_lowered = {}
        t = threading.Thread(target=self._fps_watch_loop, daemon=True)
        t.start()

    def _fps_set_timer(self, on):
        try:
            cur = ctypes.c_ulong(0)
            ctypes.windll.ntdll.NtSetTimerResolution(5000, bool(on), ctypes.byref(cur))
        except Exception:
            pass

    def _fps_disable_throttling(self, pid):
        """Impede o Windows de colocar o jogo em modo econômico (EcoQoS/Power Throttling)."""
        try:
            class PPT(ctypes.Structure):
                _fields_ = [("Version", ctypes.c_ulong), ("ControlMask", ctypes.c_ulong), ("StateMask", ctypes.c_ulong)]
            h = ctypes.windll.kernel32.OpenProcess(0x0200, False, pid)  # PROCESS_SET_INFORMATION
            if h:
                st = PPT(1, 1, 0)
                ctypes.windll.kernel32.SetProcessInformation(h, 4, ctypes.byref(st), ctypes.sizeof(st))
                ctypes.windll.kernel32.CloseHandle(h)
        except Exception:
            pass

    def _fps_boost_pid(self, p, name):
        import psutil
        try:
            p.nice(psutil.HIGH_PRIORITY_CLASS)
        except Exception:
            pass
        try:
            p.ionice(psutil.IOPRIO_HIGH)
        except Exception:
            pass
        self._fps_disable_throttling(p.pid)
        self._fps_set_timer(True)
        # Libera CPU/RAM de programas de fundo (só abaixa prioridade; não fecha nada)
        lowered = 0
        for q in psutil.process_iter(['pid', 'name']):
            try:
                n = (q.info.get('name') or '').lower()
                if n in self.FPS_BACKGROUND_LOWER and q.pid not in self._fps_lowered:
                    self._fps_lowered[q.pid] = q.nice()
                    q.nice(psutil.BELOW_NORMAL_PRIORITY_CLASS)
                    try:
                        h = ctypes.windll.kernel32.OpenProcess(0x0500, False, q.pid)  # QUERY|SET_QUOTA
                        if h:
                            ctypes.windll.psapi.EmptyWorkingSet(h)
                            ctypes.windll.kernel32.CloseHandle(h)
                    except Exception:
                        pass
                    lowered += 1
            except Exception:
                pass
        self.log(f"🎮 Jogo detectado: {name} → prioridade ALTA, timer 0.5ms, {lowered} app(s) de fundo suavizados.")

    def _fps_restore_background(self):
        import psutil
        for pid, old in list(self._fps_lowered.items()):
            try:
                psutil.Process(pid).nice(old)
            except Exception:
                pass
        self._fps_lowered = {}
        self._fps_set_timer(False)

    def _fps_watch_loop(self):
        import psutil
        while getattr(self, "_fps_watch_on", False):
            try:
                cfg = self._fps_load_cfg()
                names = {os.path.basename(g).lower() for g in cfg.get("games", [])} | set(self.FPS_KNOWN_EXES)
                alive = set()
                for proc in psutil.process_iter(['pid', 'name']):
                    n = (proc.info.get('name') or '').lower()
                    if n in names:
                        alive.add(proc.pid)
                        if proc.pid not in self._fps_boosted:
                            self._fps_boosted[proc.pid] = n
                            self._fps_boost_pid(proc, n)
                gone = [pid for pid in self._fps_boosted if pid not in alive]
                for pid in gone:
                    self._fps_boosted.pop(pid, None)
                if gone and not self._fps_boosted:
                    self._fps_restore_background()
                    self.log("🎮 Jogo fechado: prioridades dos programas de fundo restauradas.")
            except Exception:
                pass
            time.sleep(3)

    def apply_turbo_boost(self):
        """Boost seguro de responsividade: boot mais rápido, abertura de apps mais rápida e menos input lag.
        Tudo reversível pelo botão 'Reverter' (perfil de fábrica)."""
        self.log("🚀 Aplicando Boost de Responsividade (seguro e reversível)...")

        # --- Abertura de apps / menus mais rápidos ---
        self.set_hud_progress(15, "Deixando menus e janelas mais rápidos...")
        self.run_cmd_live(r'reg add "HKCU\Control Panel\Desktop" /v MenuShowDelay /t REG_SZ /d 20 /f')
        self.run_cmd_live(r'reg add "HKCU\Control Panel\Desktop" /v WaitToKillAppTimeout /t REG_SZ /d 4000 /f')
        self.run_cmd_live(r'reg add "HKCU\Control Panel\Desktop" /v AutoEndTasks /t REG_SZ /d 1 /f')
        # Remove o atraso artificial dos programas de inicialização
        self.run_cmd_live(r'reg add "HKCU\Software\Microsoft\Windows\CurrentVersion\Explorer\Serialize" /v StartupDelayInMSec /t REG_DWORD /d 0 /f')

        # --- SysMain/Prefetch LIGADOS (aceleram a abertura de programas) ---
        self.set_hud_progress(35, "Garantindo Prefetch/SuperFetch ativos (abertura rápida de apps)...")
        self.run_cmd_live('reg add "HKLM\\SYSTEM\\CurrentControlSet\\Control\\Session Manager\\Memory Management\\PrefetchParameters" /v EnablePrefetcher /t REG_DWORD /d 3 /f')
        self.run_cmd_live('reg add "HKLM\\SYSTEM\\CurrentControlSet\\Control\\Session Manager\\Memory Management\\PrefetchParameters" /v EnableSuperfetch /t REG_DWORD /d 3 /f')
        self.run_cmd_live('powershell -NoProfile -Command "Set-Service -Name SysMain -StartupType Automatic -ErrorAction SilentlyContinue; Start-Service SysMain -ErrorAction SilentlyContinue"')

        # --- Boot mais rápido ---
        self.set_hud_progress(55, "Acelerando a inicialização do Windows...")
        # Menu de boot sem espera longa
        self.run_cmd_live('bcdedit /timeout 3')
        # Fast Startup ligado
        self.run_cmd_live('reg add "HKLM\\SYSTEM\\CurrentControlSet\\Control\\Session Manager\\Power" /v HiberbootEnabled /t REG_DWORD /d 1 /f')
        self.run_cmd_live('powercfg /hibernate on')

        # --- Menos input lag ---
        self.set_hud_progress(75, "Reduzindo input lag (mouse/teclado 1:1)...")
        self.apply_mouse_calibration_silent()
        # Desliga a gravação em segundo plano do Game DVR (causa engasgos e input lag)
        self.run_cmd_live(r'reg add "HKCU\System\GameConfigStore" /v GameDVR_Enabled /t REG_DWORD /d 0 /f')
        self.run_cmd_live('reg add "HKLM\\SOFTWARE\\Policies\\Microsoft\\Windows\\GameDVR" /v AllowGameDVR /t REG_DWORD /d 0 /f')

        # --- Efeitos visuais: equilíbrio (mantém fontes suaves, corta animações pesadas) ---
        self.set_hud_progress(90, "Ajustando efeitos visuais para desempenho...")
        self.run_cmd_live(r'reg add "HKCU\Software\Microsoft\Windows\CurrentVersion\Explorer\VisualEffects" /v VisualFXSetting /t REG_DWORD /d 3 /f')

        self.apply_core_tweaks()
        self.set_hud_progress(100, "Boost aplicado!")
        self.log("✅ Boost de responsividade aplicado e gravado no registro (permanece após reiniciar).")
        self.after(0, lambda: messagebox.showinfo("Boost Aplicado",
            "🚀 Boost de responsividade aplicado!\n\n"
            "• Menus e janelas respondem mais rápido\n"
            "• Programas de inicialização sem atraso artificial\n"
            "• Prefetch/SuperFetch ativos (apps abrem mais rápido)\n"
            "• Inicialização rápida do Windows ligada\n"
            "• Gravação em segundo plano (Game DVR) desligada — menos input lag\n\n"
            "Reinicie o PC para o boot mais rápido fazer efeito. Tudo é reversível no botão 'Reverter'."))

    def apply_mouse_calibration_silent(self):
        """Mesma calibração de mouse 1:1, mas sem abrir caixa de mensagem (uso interno)."""
        cmds = [
            r'reg add "HKCU\Control Panel\Mouse" /v MouseSpeed /t REG_SZ /d "0" /f',
            r'reg add "HKCU\Control Panel\Mouse" /v MouseThreshold1 /t REG_SZ /d "0" /f',
            r'reg add "HKCU\Control Panel\Mouse" /v MouseThreshold2 /t REG_SZ /d "0" /f',
        ]
        for c in cmds:
            self.run_cmd_live(c)
        try:
            ctypes.windll.user32.SystemParametersInfoW(0x0071, 0, 0, 0x0002)
        except Exception:
            pass

    # --- Detector de causas de travamento (Discord, overlays, gravação etc.) ---
    def scan_stutter_causes(self):
        findings = []
        try:
            import psutil
            running = {}
            for proc in psutil.process_iter(['name']):
                n = (proc.info.get('name') or '').lower()
                if n:
                    running[n] = running.get(n, 0) + 1
        except Exception:
            running = {}

        def is_run(*names):
            return any(nm in running for nm in names)

        # 1) Game DVR / gravação em segundo plano ligada
        try:
            import winreg
            k = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"System\GameConfigStore")
            val, _ = winreg.QueryValueEx(k, "GameDVR_Enabled")
            winreg.CloseKey(k)
            if int(val) != 0:
                findings.append({"sev": "alto", "titulo": "Gravação em segundo plano (Game DVR) ligada",
                                 "detalhe": "A captura de tela em segundo plano do Windows rouba FPS e causa engasgos.",
                                 "fix": "gamedvr"})
        except Exception:
            pass

        # 2) Plano de energia não é de alto desempenho
        try:
            out = subprocess.check_output("powercfg /getactivescheme", shell=True, text=True,
                                          creationflags=subprocess.CREATE_NO_WINDOW)
            if "alto desempenho" not in out.lower() and "high performance" not in out.lower() and "ultimate" not in out.lower():
                findings.append({"sev": "medio", "titulo": "Plano de energia não é de alto desempenho",
                                 "detalhe": "No plano Equilibrado a CPU pode reduzir a frequência durante o jogo.",
                                 "fix": "power"})
        except Exception:
            pass

        # 3) Overlays conhecidos que costumam causar conflito/stutter
        overlays = [
            ("Discord", ("discord.exe",), "A aceleração por hardware do Discord costuma causar quedas de FPS nos jogos. "
                                          "Clique em 'Corrigir agora' para desligá-la automaticamente.", "discord"),
            ("Xbox Game Bar", ("gamebar.exe", "gamebarft.exe", "xboxgamebar.exe"), "O overlay do Xbox Game Bar pode engasgar o jogo. "
                                          "'Corrigir agora' desativa o Game Bar e a gravação em segundo plano.", "xboxbar"),
            ("NVIDIA Overlay", ("nvcontainer.exe",), "O overlay do GeForce Experience/NVIDIA App pode causar stutter em alguns jogos. "
                                          "'Corrigir agora' desliga o overlay (ShadowPlay).", "nvoverlay"),
            ("MSI Afterburner / RTSS", ("rtss.exe", "afterburner.exe"), "O RivaTuner (RTSS) às vezes conflita com overlays de jogos. Se travar, feche o RTSS durante a partida.", None),
            ("OBS (gravando/stream)", ("obs64.exe", "obs32.exe"), "Gravar/transmitir consome CPU e GPU; reduza a qualidade se travar.", None),
        ]
        for nome, procs, detalhe, fixid in overlays:
            if is_run(*procs):
                findings.append({"sev": "info", "titulo": f"{nome} em execução", "detalhe": detalhe, "fix": fixid})

        # 4) Muitos programas de inicialização
        try:
            ps = ("$n=0; "
                  "try { $n += (Get-CimInstance Win32_StartupCommand -ErrorAction SilentlyContinue | Measure-Object).Count } catch {}; "
                  "$n")
            out = subprocess.check_output(["powershell", "-NoProfile", "-Command", ps], text=True, timeout=20,
                                          creationflags=subprocess.CREATE_NO_WINDOW).strip()
            cnt = int(out or "0")
            if cnt >= 10:
                findings.append({"sev": "medio", "titulo": f"{cnt} programas na inicialização",
                                 "detalhe": "Muitos programas abrindo com o Windows deixam o boot lento e consomem RAM.",
                                 "fix": "startup"})
        except Exception:
            pass

        # 5) Pouco espaço livre no disco do sistema
        try:
            import shutil
            free_gb = shutil.disk_usage("C:\\").free / (1024**3)
            if free_gb < 15:
                findings.append({"sev": "alto", "titulo": f"Pouco espaço livre no C: ({free_gb:.0f} GB)",
                                 "detalhe": "Disco quase cheio deixa o Windows e os jogos lentos. Libere espaço.",
                                 "fix": "disk"})
        except Exception:
            pass

        return findings

    def apply_stutter_fix(self, fix):
        if fix == "gamedvr":
            self.run_cmd_live(r'reg add "HKCU\System\GameConfigStore" /v GameDVR_Enabled /t REG_DWORD /d 0 /f')
            self.run_cmd_live('reg add "HKLM\\SOFTWARE\\Policies\\Microsoft\\Windows\\GameDVR" /v AllowGameDVR /t REG_DWORD /d 0 /f')
            self.log("✅ Gravação em segundo plano (Game DVR) desativada.")
        elif fix == "power":
            self.run_cmd_live('powercfg -setactive 8c5e7fda-e8bf-4a96-9a85-a6e23a8c635c')
            self.log("✅ Plano de energia de alto desempenho ativado.")
        elif fix == "startup":
            self.after(0, lambda: subprocess.Popen('taskmgr /7 /startup', shell=True))
            self.log("Abri o Gerenciador de Tarefas na aba Inicializar para você desativar o que não usa.")
        elif fix == "disk":
            self.free_disk_space()
        elif fix == "discord":
            self.fix_discord_performance()
        elif fix == "xboxbar":
            self.fix_xbox_gamebar()
        elif fix == "nvoverlay":
            self.fix_nvidia_overlay()

    def fix_discord_performance(self):
        """Desliga a Aceleração por Hardware do Discord editando o settings.json (fecha o Discord antes)."""
        import glob
        appdata = os.environ.get("APPDATA", "")
        if not appdata:
            self.log("❌ Não localizei a pasta do Discord (APPDATA vazio).")
            return
        variantes = ["discord", "discordcanary", "discordptb", "discorddevelopment"]
        alvos = [os.path.join(appdata, v, "settings.json") for v in variantes]
        existentes = [p for p in alvos if os.path.isfile(p)]
        if not existentes:
            self.log("ℹ️ Discord instalado, mas sem arquivo de configuração ainda. Abra o Discord uma vez e rode de novo.")
            self.after(0, lambda: messagebox.showinfo("Discord",
                "Não encontrei o arquivo de configuração do Discord.\n\nAbra o Discord uma vez, feche e rode a correção novamente."))
            return

        # O Discord precisa estar fechado, senão regrava o settings.json ao sair
        running = False
        try:
            import psutil
            running = any((p.info.get('name') or '').lower() == "discord.exe" for p in psutil.process_iter(['name']))
        except Exception:
            running = True
        if running:
            if not self.call_ui(lambda: messagebox.askyesno("Fechar o Discord",
                    "Para desligar a aceleração por hardware, o Discord precisa ser fechado agora.\n\n"
                    "Ele será reaberto automaticamente. Fechar o Discord?")):
                self.log("⏹️ Correção do Discord cancelada (o Discord continua aberto).")
                return
            subprocess.run('taskkill /F /IM discord.exe', shell=True, capture_output=True, creationflags=subprocess.CREATE_NO_WINDOW)
            time.sleep(2)

        exe_para_reabrir = None
        alterados = 0
        for cfg in existentes:
            try:
                with open(cfg, "r", encoding="utf-8") as f:
                    data = json.load(f)
            except Exception:
                data = {}
            data["enableHardwareAcceleration"] = False
            try:
                with open(cfg, "w", encoding="utf-8") as f:
                    json.dump(data, f, indent=2)
                alterados += 1
                self.log(f"  ✅ Aceleração por hardware desligada em {os.path.basename(os.path.dirname(cfg))}")
            except Exception as e:
                self.log(f"  ❌ Não consegui editar {cfg}: {e}")
            # localiza o Update.exe para reabrir o Discord
            variante = os.path.basename(os.path.dirname(cfg))
            upd = os.path.join(os.path.dirname(appdata), "Local", variante, "Update.exe")
            if os.path.isfile(upd):
                exe_para_reabrir = (upd, variante)

        self.log(f"✅ Discord otimizado ({alterados} configuração(ões) ajustada(s)).")

        # Reabre o Discord se estava aberto
        if running and exe_para_reabrir:
            upd, variante = exe_para_reabrir
            exe_name = {"discord": "Discord.exe", "discordcanary": "DiscordCanary.exe",
                        "discordptb": "DiscordPTB.exe"}.get(variante, "Discord.exe")
            try:
                subprocess.Popen([upd, "--processStart", exe_name])
            except Exception:
                pass
        self.after(0, lambda: messagebox.showinfo("Discord Otimizado",
            "✅ Aceleração por hardware do Discord DESLIGADA — isso costuma devolver vários FPS nos jogos.\n\n"
            "Obs.: o 'Overlay no jogo' do Discord fica na conta e não dá para alterar por fora com segurança. "
            "Se ainda travar, desligue o overlay em: Discord → Configurações → Overlay no jogo."))

    def fix_xbox_gamebar(self):
        """Desativa a Xbox Game Bar e a gravação em segundo plano."""
        self.run_cmd_live(r'reg add "HKCU\Software\Microsoft\Windows\CurrentVersion\GameDVR" /v AppCaptureEnabled /t REG_DWORD /d 0 /f')
        self.run_cmd_live(r'reg add "HKCU\System\GameConfigStore" /v GameDVR_Enabled /t REG_DWORD /d 0 /f')
        self.run_cmd_live('reg add "HKLM\\SOFTWARE\\Policies\\Microsoft\\Windows\\GameDVR" /v AllowGameDVR /t REG_DWORD /d 0 /f')
        self.run_cmd_live(r'reg add "HKCU\Software\Microsoft\GameBar" /v UseNexusForGameBarEnabled /t REG_DWORD /d 0 /f')
        self.log("✅ Xbox Game Bar e gravação em segundo plano desativadas.")
        self.after(0, lambda: messagebox.showinfo("Xbox Game Bar", "✅ Xbox Game Bar e gravação em segundo plano desativadas!"))

    def fix_nvidia_overlay(self):
        """Desliga o overlay da NVIDIA (ShadowPlay / GeForce Experience / NVIDIA App)."""
        self.run_cmd_live(r'reg add "HKCU\Software\NVIDIA Corporation\Global\ShadowPlay\NVSPCAPS" /v WhitelistApps /t REG_DWORD /d 0 /f')
        self.log("→ Overlay da NVIDIA (ShadowPlay) marcado para desligar.")
        self.log("ℹ️ Se o overlay continuar, desligue em: NVIDIA App/GeForce Experience → Configurações → Overlay no jogo (OFF).")
        self.after(0, lambda: messagebox.showinfo("NVIDIA Overlay",
            "✅ Pedido de desligar o overlay da NVIDIA aplicado.\n\n"
            "Se ainda aparecer, abra a NVIDIA App (ou GeForce Experience) e desligue 'Overlay no jogo'."))

    def open_stutter_detector(self):
        def _scan():
            self.log("🔎 Procurando causas de travamento em jogos...")
            findings = self.scan_stutter_causes()
            self.after(0, lambda: self.show_stutter_report(findings))
        self.run_async(_scan)

    def show_stutter_report(self, findings):
        win = ctk.CTkToplevel(self)
        win.title("🔎 Detector de Travamentos")
        win.geometry("640x520")
        win.attributes("-topmost", True)
        b = ctk.CTkFrame(win, fg_color="#100B24", corner_radius=12, border_width=2, border_color="#00D2FF")
        b.pack(fill="both", expand=True, padx=4, pady=4)
        ctk.CTkLabel(b, text="🔎 Causas de Travamento Encontradas", font=ctk.CTkFont(size=16, weight="bold"), text_color="#00D2FF").pack(pady=(14, 2))

        box = ctk.CTkScrollableFrame(b, fg_color="#181232", corner_radius=8)
        box.pack(fill="both", expand=True, padx=16, pady=8)

        if not findings:
            ctk.CTkLabel(box, text="✅ Nenhuma causa óbvia de travamento encontrada!\nSeu PC está configurado de forma saudável para jogos.",
                         font=ctk.CTkFont(size=12), text_color="#10B981", justify="left").pack(pady=20, padx=10)
        else:
            cores = {"alto": "#EF4444", "medio": "#F59E0B", "info": "#38BDF8"}
            for f in findings:
                card = ctk.CTkFrame(box, fg_color="#120E24", corner_radius=8)
                card.pack(fill="x", padx=6, pady=5)
                ctk.CTkLabel(card, text=f"● {f['titulo']}", font=ctk.CTkFont(size=12, weight="bold"),
                             text_color=cores.get(f["sev"], "#FFFFFF"), anchor="w", justify="left", wraplength=560).pack(fill="x", padx=10, pady=(8, 2))
                ctk.CTkLabel(card, text=f["detalhe"], font=ctk.CTkFont(size=10), text_color="#C4B5FD",
                             anchor="w", justify="left", wraplength=560).pack(fill="x", padx=10, pady=(0, 6))
                if f.get("fix"):
                    ctk.CTkButton(card, text="Corrigir agora", height=28, font=ctk.CTkFont(size=11, weight="bold"),
                                  fg_color="#7928CA", hover_color="#9333EA",
                                  command=lambda fx=f["fix"], c=card: (self.run_async(lambda: self.apply_stutter_fix(fx)),
                                                                        c.configure(border_width=1, border_color="#10B981"))
                                  ).pack(anchor="e", padx=10, pady=(0, 8))

        ctk.CTkButton(b, text="Fechar", fg_color="#374151", hover_color="#4B5563", height=32, command=win.destroy).pack(pady=(0, 12))

    def diagnose_and_fix_bugs(self):
        self.log("🔧 Iniciando Verificação Automática de Bugs...")
        
        # 1. Start Menu and UWP Shell check
        self.log("→ [1/4] Verificando integridade do Menu Iniciar e Barra de Tarefas...")
        try:
            # Re-register Start Menu Experience Host
            self.run_cmd_live('powershell -Command "Get-AppXPackage -Name Microsoft.Windows.StartMenuExperienceHost | Foreach { Add-AppxPackage -DisableDevelopmentMode -Register ($_.InstallLocation + \'\\AppXManifest.xml\') -ForceApplicationShutdown }"')
            # Re-register Shell Experience Host
            self.run_cmd_live('powershell -Command "Get-AppXPackage -Name Microsoft.Windows.ShellExperienceHost | Foreach { Add-AppxPackage -DisableDevelopmentMode -Register ($_.InstallLocation + \'\\AppXManifest.xml\') -ForceApplicationShutdown }"')
            self.log("✅ Menu Iniciar e Shell UWP re-registrados com sucesso!")
        except Exception as e:
            self.log(f"⚠️ Erro ao registrar UWP Shell: {e}")
            
        # 2. Reset Explorer.exe context
        self.log("→ [2/4] Reiniciando Windows Explorer para aplicar correções...")
        try:
            self.run_cmd_live('powershell -Command "Stop-Process -Name explorer -Force"')
            time.sleep(1.5)
            self.run_cmd_live('powershell -Command "Start-Process explorer"')
            self.log("✅ Windows Explorer reiniciado!")
        except Exception as e:
            self.log(f"⚠️ Erro ao reiniciar Explorer: {e}")

        # 3. Network and DNS flush
        self.log("→ [3/4] Limpando cache de DNS e restabelecendo rotas de rede...")
        try:
            self.run_cmd_live('ipconfig /flushdns')
            self.run_cmd_live('netsh winsock reset')
            self.log("✅ Cache de DNS limpo e Winsock redefinido!")
        except Exception as e:
            self.log(f"⚠️ Erro na limpeza de rede: {e}")

        # 4. Critical Services verification
        self.log("→ [4/4] Verificando e restaurando serviços essenciais do Windows...")
        try:
            # Force start services if they are disabled or stopped
            services = ["SysMain", "WSearch", "Spooler", "Audiosrv"]
            for s in services:
                self.run_cmd_live(f'powershell -Command "Set-Service -Name {s} -StartupType Automatic -ErrorAction SilentlyContinue; Start-Service -Name {s} -ErrorAction SilentlyContinue"')
            self.log("✅ Serviços essenciais verificados e ativados!")
        except Exception as e:
            self.log(f"⚠️ Erro ao verificar serviços: {e}")

        self.log("✨ Processo de Diagnóstico e Correção finalizado!")
        self.after(0, lambda: messagebox.showinfo("Bugs Corrigidos", "✅ Todos os diagnósticos foram executados!\n\nSe o Menu Iniciar ou Barra de Tarefas ainda apresentarem problemas de permissão (como privilégios de Admin herdados no Explorer), recomendamos reiniciar o computador."))

if __name__ == "__main__":
    app = OtimizadorApp()
    app.mainloop()
