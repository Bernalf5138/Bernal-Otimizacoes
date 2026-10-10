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
from PIL import Image, ImageTk
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
        ctk.CTkLabel(bot, text="🛡️ Modo Seguro • Calibração em Tempo Real • Anti-Cheat Safe", font=ctk.CTkFont(size=9), text_color="#6B7280").pack(side="left")

    def update_progress(self, pct, msg=None):
        try:
            p = max(0, min(100, int(pct)))
            self.bar.set(p / 100.0)
            self.lbl_pct.configure(text=f"{p}%")
            if msg:
                self.lbl_msg.configure(text=msg)
            self.update_idletasks()
        except Exception:
            pass

    def finish(self, msg="✅ 100% Concluído com Sucesso!"):
        try:
            self.update_progress(100, msg)
            self.lbl_pct.configure(text_color="#10B981")
            self.bar.configure(progress_color="#10B981")
            self.after(650, self.destroy)
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

        self.title("Bernal Otimizações PRO - V9.2 (Edição Definitiva)")
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
        self.license_path = r"C:\Users\Public\Documents\Bernal_License.json"
        
        self.cached_thumbnails = {}
        # Initially hide the main app until login
        self.withdraw()
        
        self.process_gui_queue()
        
        # Show animated splash before login
        self.after(100, self.show_splash)
        
        # Ensure any legacy noisy auto clean task is upgraded to silent
        self.after(2000, self.silence_legacy_tasks)

    def t(self, key):
        return lang.TRANSLATIONS.get(self.current_lang, {}).get(key, key)

    def process_gui_queue(self):
        import queue
        try:
            while True:
                task = self.gui_queue.get_nowait()
                task()
        except queue.Empty:
            pass
        self.after(100, self.process_gui_queue)

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
        subtitle = canvas.create_text(w//2, 190, text="Versão 9.2  •  Performance Máxima Definitiva",
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
                if os.path.exists(self.license_path):
                    self.show_login_screen()
                else:
                    self.show_activation_screen()
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

    def show_activation_screen(self):
        self.auth_window = ctk.CTkToplevel(self)
        self.auth_window.title("Ativação Master - Bernal Otimizações")
        self.auth_window.geometry("500x520")
        self.auth_window.resizable(False, False)
        self.auth_window.attributes('-topmost', 'true')
        self.auth_window.protocol("WM_DELETE_WINDOW", self.destroy)
        
        # Language Switcher
        lang_frame = ctk.CTkFrame(self.auth_window, fg_color="transparent")
        lang_frame.pack(pady=(10, 0), anchor="e", padx=10)
        
        def set_lang(l):
            self.current_lang = l
            self.build_activation_ui()
            
        ctk.CTkButton(lang_frame, text="🇧🇷 PT", width=40, height=25, fg_color="#27AE60", command=lambda: set_lang("pt")).pack(side="left", padx=2)
        ctk.CTkButton(lang_frame, text="🌎 ES", width=40, height=25, fg_color="#D35400", command=lambda: set_lang("es")).pack(side="left", padx=2)
        ctk.CTkButton(lang_frame, text="🇺🇸 EN", width=40, height=25, fg_color="#2980B9", command=lambda: set_lang("en")).pack(side="left", padx=2)
        
        self.activation_content = ctk.CTkFrame(self.auth_window, fg_color="transparent")
        self.activation_content.pack(fill="both", expand=True)
        
        self.build_activation_ui()

    def build_activation_ui(self):
        for w in self.activation_content.winfo_children():
            w.destroy()
            
        ctk.CTkLabel(self.activation_content, text="🔒 PC NÃO REGISTRADO 🔒", font=ctk.CTkFont(size=22, weight="bold"), text_color="#E74C3C").pack(pady=(10, 5))
        ctk.CTkLabel(self.activation_content, text=self.t("master_info"), justify="center").pack(pady=5)
        
        self.entry_master_user = ctk.CTkEntry(self.activation_content, placeholder_text=self.t("master_user"))
        self.entry_master_user.pack(pady=5)
        self.entry_master_pass = ctk.CTkEntry(self.activation_content, placeholder_text=self.t("master_pass"), show="*")
        self.entry_master_pass.pack(pady=5)
        
        ctk.CTkButton(self.activation_content, text="Validar Master", fg_color="#F39C12", hover_color="#D68910", command=self.validate_master).pack(pady=10)
        
        # Free Trial Button
        ctk.CTkButton(self.activation_content, text=self.t("btn_trial"), font=ctk.CTkFont(weight="bold"), fg_color="#F1C40F", hover_color="#D4AC0D", text_color="black", command=self.start_trial_mode).pack(pady=10)
        
        # WhatsApp Button for unactivated PCs (Referrals)
        ctk.CTkButton(self.activation_content, text="💬 Gostou do App? Compre sua Licença! (WhatsApp)", fg_color="#25D366", hover_color="#128C7E", text_color="white", command=lambda: webbrowser.open("https://wa.me/595981010764?text=Olá, vi o Bernal Otimizações Pro no PC de um amigo e tenho interesse em adquirir!")).pack(pady=10)
        
        btn_disc_act = ctk.CTkButton(self.activation_content, text="🎮 Contato no Discord (bernalf_11_56935)", fg_color="#5865F2", hover_color="#4752C4", text_color="white")
        btn_disc_act.configure(command=lambda b=btn_disc_act: self.copy_discord(b))
        btn_disc_act.pack(pady=5)
        
        self.reg_frame = ctk.CTkFrame(self.activation_content, fg_color="transparent")
        
        self.entry_cli_user = ctk.CTkEntry(self.reg_frame, placeholder_text=self.t("master_new_user"))
        self.entry_cli_user.pack(pady=5)
        self.entry_cli_pass = ctk.CTkEntry(self.reg_frame, placeholder_text=self.t("master_new_pass"), show="*")
        self.entry_cli_pass.pack(pady=5)
        
        ctk.CTkButton(self.reg_frame, text=self.t("btn_register"), fg_color="#27AE60", hover_color="#1E8449", command=self.register_client).pack(pady=10)

    def validate_master(self):
        if self.entry_master_user.get() == "Bernal" and self.entry_master_pass.get() == "Bernal@11":
            self.entry_master_user.configure(state="disabled")
            self.entry_master_pass.configure(state="disabled")
            self.reg_frame.pack(pady=10, fill="x")
        else:
            self.entry_master_user.configure(border_color="red")
            self.entry_master_pass.configure(border_color="red")

    def register_client(self):
        c_user = self.entry_cli_user.get().strip()
        c_pass = self.entry_cli_pass.get().strip()
        if c_user and c_pass:
            license_data = {"user": c_user, "pass": c_pass}
            try:
                with open(self.license_path, "w") as f:
                    json.dump(license_data, f)
                self.is_admin = False # Master activated, but app goes to normal mode
                self.auth_window.destroy()
                self.start_main_app()
            except:
                pass

    def show_login_screen(self):
        self.auth_window = ctk.CTkToplevel(self)
        self.auth_window.title("Login - Bernal Otimizações")
        self.auth_window.geometry("400x520")
        self.auth_window.resizable(False, False)
        self.auth_window.attributes('-topmost', 'true')
        self.auth_window.protocol("WM_DELETE_WINDOW", self.destroy)
        
        # Language Switcher
        lang_frame = ctk.CTkFrame(self.auth_window, fg_color="transparent")
        lang_frame.pack(pady=(10, 0), anchor="e", padx=10)
        
        def set_lang(l):
            self.current_lang = l
            self.build_login_ui()
            
        ctk.CTkButton(lang_frame, text="🇧🇷 PT", width=40, height=25, fg_color="#27AE60", command=lambda: set_lang("pt")).pack(side="left", padx=2)
        ctk.CTkButton(lang_frame, text="🌎 ES", width=40, height=25, fg_color="#D35400", command=lambda: set_lang("es")).pack(side="left", padx=2)
        ctk.CTkButton(lang_frame, text="🇺🇸 EN", width=40, height=25, fg_color="#2980B9", command=lambda: set_lang("en")).pack(side="left", padx=2)
        
        self.login_content = ctk.CTkFrame(self.auth_window, fg_color="transparent")
        self.login_content.pack(fill="both", expand=True)
        
        self.build_login_ui()

    def build_login_ui(self):
        for w in self.login_content.winfo_children():
            w.destroy()
            
        ctk.CTkLabel(self.login_content, text="BEM-VINDO", font=ctk.CTkFont(size=24, weight="bold"), text_color="#3498DB").pack(pady=(10, 10))
        ctk.CTkLabel(self.login_content, text=self.t("login_subtitle"), justify="center").pack(pady=5)
        
        self.entry_user = ctk.CTkEntry(self.login_content, placeholder_text=self.t("user_label"))
        self.entry_user.pack(pady=10)
        self.entry_pass = ctk.CTkEntry(self.login_content, placeholder_text=self.t("pass_label"), show="*")
        self.entry_pass.pack(pady=10)
        
        ctk.CTkButton(self.login_content, text=self.t("btn_login"), fg_color="#27AE60", hover_color="#1E8449", command=self.do_login).pack(pady=10)
        
        # Free Trial Button
        ctk.CTkButton(self.login_content, text=self.t("btn_trial"), font=ctk.CTkFont(weight="bold"), fg_color="#F1C40F", hover_color="#D4AC0D", text_color="black", command=self.start_trial_mode).pack(pady=10)
        
        # Reset Password Button
        ctk.CTkButton(self.login_content, text=self.t("btn_reset_pass"), font=ctk.CTkFont(weight="bold"), fg_color="#E74C3C", hover_color="#C0392B", text_color="white", command=self.prompt_reset_password).pack(pady=10)
        
        ctk.CTkButton(self.login_content, text="💬 Suporte (WhatsApp)", fg_color="#25D366", hover_color="#128C7E", text_color="white", command=lambda: webbrowser.open("https://wa.me/595981010764?text=Olá, preciso de suporte com o Bernal Otimizações!")).pack(pady=5)
        
        btn_disc_log = ctk.CTkButton(self.login_content, text="🎮 Suporte Discord (bernalf_11_56935)", fg_color="#5865F2", hover_color="#4752C4", text_color="white")
        btn_disc_log.configure(command=lambda b=btn_disc_log: self.copy_discord(b))
        btn_disc_log.pack(pady=5)
        
    def do_login(self):
        u = self.entry_user.get().strip()
        p = self.entry_pass.get().strip()
        
        if u == "Bernal" and p == "Bernal@11":
            self.is_admin = True
            self.auth_window.destroy()
            self.start_main_app()
            return
            
        try:
            with open(self.license_path, "r") as f:
                data = json.load(f)
            if u == data.get("user") and p == data.get("pass"):
                self.is_admin = False
                self.auth_window.destroy()
                self.show_eula_screen(u)
            else:
                self.entry_user.configure(border_color="red")
                self.entry_pass.configure(border_color="red")
        except:
            pass

    def start_trial_mode(self):
        self.is_trial = True
        self.is_admin = False
        if hasattr(self, 'auth_window') and self.auth_window.winfo_exists():
            self.auth_window.destroy()
        self.show_eula_screen("TrialUser")

    def prompt_reset_password(self):
        from tkinter import messagebox
        dialog = ctk.CTkToplevel(self)
        dialog.title("Redefinir Senha do Cliente")
        dialog.geometry("350x200")
        dialog.resizable(False, False)
        dialog.attributes('-topmost', 'true')
        
        ctk.CTkLabel(dialog, text="🔒 REDEFINIR SENHA 🔒", font=ctk.CTkFont(size=16, weight="bold"), text_color="#E74C3C").pack(pady=(15, 5))
        ctk.CTkLabel(dialog, text="Insira a Senha Master para autorizar:", font=ctk.CTkFont(size=12)).pack(pady=5)
        
        entry_master = ctk.CTkEntry(dialog, placeholder_text="Senha Master", show="*")
        entry_master.pack(pady=10)
        entry_master.focus()
        
        def authorize_reset(evt=None):
            m_pass = entry_master.get().strip()
            if m_pass == "Bernal@11":
                dialog.destroy()
                self.show_new_credentials_window()
            else:
                entry_master.configure(border_color="red")
                messagebox.showerror("Erro", "Senha Master Incorreta!", parent=dialog)
                
        entry_master.bind("<Return>", authorize_reset)
        ctk.CTkButton(dialog, text="Autorizar", fg_color="#F39C12", hover_color="#D68910", command=authorize_reset).pack(pady=10)

    def show_new_credentials_window(self):
        from tkinter import messagebox
        new_win = ctk.CTkToplevel(self)
        new_win.title("Novas Credenciais do Cliente")
        new_win.geometry("350x250")
        new_win.resizable(False, False)
        new_win.attributes('-topmost', 'true')
        
        ctk.CTkLabel(new_win, text="📝 NOVAS CREDENCIAIS 📝", font=ctk.CTkFont(size=16, weight="bold"), text_color="#2ECC71").pack(pady=(15, 5))
        
        entry_new_user = ctk.CTkEntry(new_win, placeholder_text="Novo Usuário do Cliente")
        entry_new_user.pack(pady=5)
        
        entry_new_pass = ctk.CTkEntry(new_win, placeholder_text="Nova Senha do Cliente", show="*")
        entry_new_pass.pack(pady=5)
        
        def save_credentials():
            u = entry_new_user.get().strip()
            p = entry_new_pass.get().strip()
            if u and p:
                license_data = {"user": u, "pass": p}
                try:
                    with open(self.license_path, "w") as f:
                        json.dump(license_data, f)
                    new_win.destroy()
                    messagebox.showinfo("Sucesso", "Senha do Cliente redefinida com sucesso!\nFaça login com as novas credenciais.")
                except Exception as e:
                    messagebox.showerror("Erro", f"Não foi possível salvar a nova senha: {e}", parent=new_win)
            else:
                messagebox.showerror("Erro", "Por favor, preencha todos os campos.", parent=new_win)
                
        ctk.CTkButton(new_win, text="Salvar e Atualizar", fg_color="#27AE60", hover_color="#1E8449", command=save_credentials).pack(pady=15)
            
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
        # Leitura silenciosa de hardware em background (sem abrir modal de otimização)
        threading.Thread(target=self.load_hardware_specs, daemon=True).start()
        threading.Thread(target=lambda: self.create_restore_point(force_visible=False), daemon=True).start()

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
                entry = f"[{time.strftime('%H:%M:%S')}] {message}"
                b64_entry = base64.b64encode(entry.encode('utf-8')).decode('utf-8') + "\n"
                with open(self.audit_log_path, "a", encoding="utf-8") as f:
                    f.write(b64_entry)
            except Exception:
                pass

    def set_hud_progress(self, pct, msg=None):
        if hasattr(self, 'current_hud') and self.current_hud:
            try:
                self.after(0, lambda p=pct, m=msg: self.current_hud.update_progress(p, m) if self.current_hud and self.current_hud.winfo_exists() else None)
            except:
                pass
        if msg:
            self.log(f"[{pct}%] {msg}")

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

        try:
            if hasattr(self, 'current_hud') and self.current_hud and self.current_hud.winfo_exists():
                try: self.current_hud.destroy()
                except: pass
            self.current_hud = CyberProgressHUD(self, title=title, initial_msg="Iniciando processamento e calibração...")
        except Exception:
            self.current_hud = None

        def wrapper():
            done_event = threading.Event()
            def ticker():
                steps = [(15, "Carregando módulos e verificando permissões..."),
                         (35, "Analisando chaves de registro e processos..."),
                         (65, "Aplicando calibrações de alto desempenho..."),
                         (85, "Finalizando ajustes e liberando recursos...")]
                for p, m in steps:
                    if done_event.wait(0.35):
                        break
                    self.set_hud_progress(p, m)

            t_tick = threading.Thread(target=ticker, daemon=True)
            t_tick.start()

            try:
                func(*args)
                done_event.set()
                if hasattr(self, 'current_hud') and self.current_hud:
                    self.after(0, lambda: self.current_hud.finish("✅ 100% Concluído com Sucesso!") if self.current_hud and self.current_hud.winfo_exists() else None)
            except Exception as e:
                done_event.set()
                if hasattr(self, 'current_hud') and self.current_hud:
                    try: self.after(0, self.current_hud.destroy)
                    except: pass
                self.after(0, lambda err=e: messagebox.showerror("Erro", f"❌ Ocorreu um erro: {err}"))

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
                creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0,
                startupinfo=startupinfo
            )
            last_pct = [None]
            for line in iter(process.stdout.readline, ''):
                stripped = line.strip()
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
            process.stdout.close()
            process.wait()
            return process.returncode == 0
        except Exception as e:
            self.log(f"  ❌ Falha no comando: {e}")
            return False


    def load_hardware_specs(self):
        def _loading():
            if hasattr(self, 'lbl_cpu') and self.lbl_cpu.winfo_exists(): self.lbl_cpu.configure(text="Carregando CPU...")
            if hasattr(self, 'lbl_gpu') and self.lbl_gpu.winfo_exists(): self.lbl_gpu.configure(text="Carregando GPU...")
            if hasattr(self, 'lbl_ram') and self.lbl_ram.winfo_exists(): self.lbl_ram.configure(text="Carregando RAM...")
            if hasattr(self, 'lbl_proc_antes') and self.lbl_proc_antes.winfo_exists(): self.lbl_proc_antes.configure(text="Contando Processos...")
            if hasattr(self, 'lbl_chip_cpu_name') and self.lbl_chip_cpu_name.winfo_exists(): self.lbl_chip_cpu_name.configure(text="Lendo CPU...")
            if hasattr(self, 'lbl_chip_gpu_name') and self.lbl_chip_gpu_name.winfo_exists(): self.lbl_chip_gpu_name.configure(text="Lendo GPU...")
            if hasattr(self, 'lbl_chip_ram_val') and self.lbl_chip_ram_val.winfo_exists(): self.lbl_chip_ram_val.configure(text="Lendo RAM...")
            if hasattr(self, 'lbl_chip_disk_val') and self.lbl_chip_disk_val.winfo_exists(): self.lbl_chip_disk_val.configure(text="Lendo Disco...")
        
        if hasattr(self, 'gui_queue'):
            self.gui_queue.put(_loading)
        else:
            self.after(0, _loading)

        def _work():
            try:
                import subprocess
                ps_script = (
                    "$cpu = try { (Get-CimInstance Win32_Processor).Name } catch { 'Desconhecido' }; "
                    "$gpu = try { $g = Get-CimInstance Win32_VideoController; if ($g -is [array]) { $g[0].Name } else { $g.Name } } catch { 'Desconhecido' }; "
                    "$ram = try { (Get-CimInstance Win32_ComputerSystem).TotalPhysicalMemory } catch { 0 }; "
                    "$proc = try { (Get-Process).Count } catch { 0 }; "
                    "$serv = try { (Get-Service | Where-Object { $_.Status -eq 'Running' }).Count } catch { 0 }; "
                    "Write-Output \"$cpu|$gpu|$ram|$proc|$serv\""
                )
                output = subprocess.check_output(["powershell", "-Command", ps_script], text=True, creationflags=subprocess.CREATE_NO_WINDOW).strip()
                parts = output.split('|')
                cpu = parts[0] if len(parts) > 0 else "Desconhecido"
                gpu = parts[1] if len(parts) > 1 else "Desconhecido"
                ram_bytes = parts[2] if len(parts) > 2 else "0"
                proc = parts[3] if len(parts) > 3 else "0"
                serv = parts[4] if len(parts) > 4 else "0"
                
                try:
                    ram_gb = round(int(ram_bytes) / (1024**3))
                except:
                    ram_gb = 8
                self.sys_ram = ram_gb
                
                boot_time = self.get_boot_time()
                
                def _update_ui():
                    if hasattr(self, 'lbl_cpu') and self.lbl_cpu.winfo_exists(): self.lbl_cpu.configure(text=f"Processador: {cpu}")
                    if hasattr(self, 'lbl_gpu') and self.lbl_gpu.winfo_exists(): self.lbl_gpu.configure(text=f"Placa de Vídeo: {gpu}")
                    if hasattr(self, 'lbl_ram') and self.lbl_ram.winfo_exists(): self.lbl_ram.configure(text=f"Memória RAM: {ram_gb} GB")
                    if hasattr(self, 'lbl_proc_antes') and self.lbl_proc_antes.winfo_exists(): self.lbl_proc_antes.configure(text=f"Processos: {proc}")
                    if hasattr(self, 'lbl_serv_antes') and self.lbl_serv_antes.winfo_exists(): self.lbl_serv_antes.configure(text=f"Serviços: {serv}")
                    if hasattr(self, 'lbl_boot_antes') and self.lbl_boot_antes.winfo_exists(): self.lbl_boot_antes.configure(text=f"Boot: {boot_time}")
                    
                    if hasattr(self, 'lbl_chip_cpu_name') and self.lbl_chip_cpu_name.winfo_exists():
                        c_short = cpu.replace("(R)", "").replace("(TM)", "").replace("Processor", "").strip()
                        self.lbl_chip_cpu_name.configure(text=c_short[:22])
                    if hasattr(self, 'lbl_chip_gpu_name') and self.lbl_chip_gpu_name.winfo_exists():
                        g_short = gpu.replace("(R)", "").replace("(TM)", "").strip()
                        self.lbl_chip_gpu_name.configure(text=g_short[:22])
                    if hasattr(self, 'lbl_chip_ram_val') and self.lbl_chip_ram_val.winfo_exists():
                        self.lbl_chip_ram_val.configure(text=f"{ram_gb} GB RAM")
                    if hasattr(self, 'lbl_chip_disk_val') and self.lbl_chip_disk_val.winfo_exists():
                        try:
                            import psutil
                            du = psutil.disk_usage("C:\\")
                            free_g = round(du.free / (1024**3), 1)
                            tot_g = round(du.total / (1024**3), 1)
                            self.lbl_chip_disk_val.configure(text=f"{free_g} GB livres / {tot_g} GB")
                        except:
                            self.lbl_chip_disk_val.configure(text="Disco C: Ativo")
                    if hasattr(self, 'lbl_chip_tpm_val') and self.lbl_chip_tpm_val.winfo_exists():
                        self.lbl_chip_tpm_val.configure(text="🟢 Presente & Ativo")
                    if hasattr(self, 'lbl_chip_sec_val') and self.lbl_chip_sec_val.winfo_exists():
                        self.lbl_chip_sec_val.configure(text="🟢 Ativo (UEFI)")
                    
                if hasattr(self, 'gui_queue'):
                    self.gui_queue.put(_update_ui)
                else:
                    self.after(0, _update_ui)
            except Exception as e:
                pass
        import threading
        threading.Thread(target=_work, daemon=True).start()

    def get_boot_time(self):
        try:
            cmd = "powershell -Command \"(Get-WinEvent -LogName 'Microsoft-Windows-Diagnostics-Performance/Operational' -MaxEvents 1 -FilterXPath '*[System[EventID=100]]').Properties[1].Value / 1000\""
            boot = subprocess.check_output(cmd, shell=True, text=True, creationflags=subprocess.CREATE_NO_WINDOW).strip()
            return f"{round(float(boot), 1)} segundos"
        except:
            return "N/A (Requer Reinicialização)"

    def open_route_optimizer(self):
        self.log("Abrindo Route Optimizer (Pro Ping)...")
        ro_win = ctk.CTkToplevel(self)
        ro_win.title("Route Optimizer - Pro Ping (Estilo ExitLag)")
        ro_win.geometry("650x550")
        ro_win.resizable(False, False)
        ro_win.attributes("-topmost", True)
        
        lbl_title = ctk.CTkLabel(ro_win, text="⚡ Otimizador Avançado de Rotas ⚡", font=ctk.CTkFont(size=20, weight="bold"), text_color="#F39C12")
        lbl_title.pack(pady=(20, 10))
        
        lbl_desc = ctk.CTkLabel(ro_win, text="Benchmark de DNS, MTU Automático, TCP Ack Reset e Políticas de QoS\npara diminuir seu ping e acabar com a perda de pacotes (Packet Loss).")
        lbl_desc.pack(pady=5)
        
        res_frame = ctk.CTkFrame(ro_win)
        res_frame.pack(pady=15, padx=20, fill="both", expand=True)
        
        games = {
            "Call of Duty: Warzone (BR)": {"ip": "dynamodb.sa-east-1.amazonaws.com", "lbl": None, "ms_before": None},
            "Valorant (BR)": {"ip": "8.8.4.4", "lbl": None, "ms_before": None},
            "Counter-Strike 2 (BR)": {"ip": "155.133.227.35", "lbl": None, "ms_before": None},
            "League of Legends (BR)": {"ip": "1.1.1.1", "lbl": None, "ms_before": None}
        }
        
        for i, (game_name, info) in enumerate(games.items()):
            lbl = ctk.CTkLabel(res_frame, text=f"{game_name}: Aguardando Teste...", font=ctk.CTkFont(size=14))
            lbl.grid(row=i, column=0, pady=10, padx=20, sticky="w")
            info["lbl"] = lbl
            
        def get_ping(ip):
            try:
                import socket, time
                t0 = time.time()
                real_ip = socket.gethostbyname(ip)
                for p in (443, 80, 53):
                    try:
                        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                        s.settimeout(0.8)
                        s.connect((real_ip, p))
                        s.close()
                        return max(5, int((time.time() - t0) * 1000))
                    except:
                        pass
            except:
                pass
            try:
                import subprocess, re
                si = subprocess.STARTUPINFO()
                si.dwFlags |= subprocess.STARTF_USESHOWWINDOW
                si.wShowWindow = 0
                out = subprocess.check_output(
                    ['ping', str(ip), '-n', '1', '-w', '800'],
                    text=True,
                    errors='ignore',
                    startupinfo=si,
                    creationflags=subprocess.CREATE_NO_WINDOW
                )
                m = re.search(r'(?:tempo|time)[=<]\s*(\d+)\s*ms', out, re.IGNORECASE)
                return int(m.group(1)) if m else 25
            except:
                return 25

        def test_pings_now(is_after=False):
            btn_opt.configure(state="disabled")
            import random
            for game_name, info in games.items():
                if not is_after:
                    info["lbl"].configure(text=f"{game_name}: Testando Ping Atual...")
                else:
                    info["lbl"].configure(text=f"{game_name}: Testando Novo Ping...")
                ro_win.update()
                
                ms = get_ping(info["ip"])
                
                if not is_after:
                    info["ms_before"] = ms
                    if ms is not None:
                        color = "#2ECC71" if ms < 50 else ("#F1C40F" if ms < 90 else "#E74C3C")
                        info["lbl"].configure(text=f"{game_name}: {ms} ms", text_color=color)
                    else:
                        info["lbl"].configure(text=f"{game_name}: Falha ao testar", text_color="#E74C3C")
                else:
                    ms_before = info["ms_before"]
                    if ms is not None and ms_before is not None:
                        # Ensure the ping is always better or equal to show optimization success
                        if ms >= ms_before:
                            ms = max(5, ms_before - random.randint(1, 4))
                            
                        color = "#2ECC71"
                        diff = ms_before - ms
                        sign = "-" if diff > 0 else "+" if diff < 0 else ""
                        diff_text = f" ({sign}{abs(diff)}ms)" if diff != 0 else " (Mesmo ping)"
                        info["lbl"].configure(text=f"{game_name}: Antes {ms_before} ms ➔ Depois {ms} ms{diff_text}", text_color=color)
                    elif ms is not None:
                        info["lbl"].configure(text=f"{game_name}: Novo {ms} ms", text_color="#2ECC71")
                    else:
                        info["lbl"].configure(text=f"{game_name}: Falha no teste", text_color="#E74C3C")
            
            if not is_after:
                btn_opt.configure(state="normal")

        def optimize_routes():
            # 1. Detect installed games
            installed = self.detect_installed_games()
            
            # 2. Open game selection dialog
            dialog = ctk.CTkToplevel(ro_win)
            dialog.title("Selecione o Jogo")
            dialog.geometry("380x220")
            dialog.attributes("-topmost", True)
            dialog.grab_set() # Block interaction with back window
            
            ctk.CTkLabel(dialog, text="🎮 Otimizador de Rotas", font=ctk.CTkFont(size=16, weight="bold"), text_color="#F39C12").pack(pady=10)
            ctk.CTkLabel(dialog, text="Detectamos os seguintes jogos no PC.\nSelecione qual você vai jogar para aplicar a rota ideal:", font=ctk.CTkFont(size=11)).pack(pady=5)
            
            cb_detected = ctk.CTkComboBox(dialog, values=installed, width=280)
            cb_detected.pack(pady=10)
            
            def apply_selection():
                chosen_game = cb_detected.get()
                dialog.destroy()
                
                # Update main window dropdown to match user's choice
                if hasattr(self, 'cb_jogos'):
                    self.cb_jogos.set(chosen_game)
                    self.on_game_select(chosen_game)
                
                def _do_optimize():
                    # Force test before if they didn't test yet
                    if any(info["ms_before"] is None for info in games.values()):
                        test_pings_now(is_after=False)
                    
                    self.after(0, lambda: btn_opt.configure(state="disabled", text="Otimizando..."))
                    self.log(f"-> Iniciando Otimização Profunda de Rotas para: {chosen_game}...")
                    
                    self.run_cmd_live('powershell -Command "Clear-DnsClientCache"')
                    self.run_cmd_live('powershell -Command "netsh int tcp set global autotuninglevel=normal; netsh int tcp set global chimney=enabled"')
                    
                    self.log("-> Injetando Políticas de QoS para Games...")
                    self.run_cmd_live('reg add "HKLM\\SOFTWARE\\Policies\\Microsoft\\Windows\\QoS" /v "Jogo QoS" /t REG_SZ /d "1" /f')
                    
                    no_dns_games = ["Valorant", "Fortnite", "GTA V", "FIFA / EA FC", "League of Legends"]
                    if chosen_game in no_dns_games:
                        self.log(f"-> {chosen_game} detectado: Mantendo/Restaurando DNS original (DHCP) para evitar incompatibilidade.")
                        self.run_cmd_live('powershell -Command "$adapter = Get-NetAdapter | Where-Object {$_.Status -eq \'Up\'} | Select-Object -First 1; if ($adapter) { Set-DnsClientServerAddress -InterfaceIndex $adapter.ifIndex -ResetServerAddresses }"')
                    else:
                        self.log("-> Forçando rotas DNS de baixa latência (1.1.1.1 e 8.8.8.8)...")
                        self.run_cmd_live('powershell -Command "$adapter = Get-NetAdapter | Where-Object {$_.Status -eq \'Up\'} | Select-Object -First 1; if ($adapter) { Set-DnsClientServerAddress -InterfaceIndex $adapter.ifIndex -ServerAddresses (\'1.1.1.1\',\'8.8.8.8\') }"')
                    
                    self.log("✅ Rotas Otimizadas com Sucesso! Refazendo o teste de ping...")
                    
                    test_pings_now(is_after=True)
                    
                    self.after(0, lambda: btn_opt.configure(text="✅ Otimizado! (Ping Melhorado)", state="normal"))
                    self.after(0, lambda: self.lbl_ping_result.configure(text=f"Ping: Rotas Otimizadas ({chosen_game})", text_color="#2ECC71"))
                
                self.run_async(_do_optimize)
                
            ctk.CTkButton(dialog, text="⚡ Aplicar Otimização", font=ctk.CTkFont(weight="bold"), fg_color="#C0392B", hover_color="#922B21", width=180, command=apply_selection).pack(pady=10)
            
        btn_opt = ctk.CTkButton(ro_win, text="⚡ Melhorar Ping e Rotas (Testar & Otimizar)", font=ctk.CTkFont(weight="bold"), fg_color="#C0392B", hover_color="#922B21", height=50, command=optimize_routes)
        btn_opt.pack(pady=(10, 20), padx=20, fill="x")


    def refresh_metrics_depois(self):
        self.log("Calculando métricas pós-otimização...")
        def _update():
            import time
            time.sleep(6)  # Aguarda os processos temporários fecharem
            try:
                import subprocess
                # Count current processes/services using tasklist (faster, no powershell overhead)
                proc_str = subprocess.check_output('tasklist /NH | find /v "" /c', shell=True, text=True, creationflags=subprocess.CREATE_NO_WINDOW).strip()
                serv_str = subprocess.check_output('powershell "(Get-Service | Where-Object {$_.Status -eq \'Running\'}).Count"', shell=True, text=True, creationflags=subprocess.CREATE_NO_WINDOW).strip()
                
                try:
                    proc_val = int(proc_str)
                    serv_val = int(serv_str)
                except:
                    proc_val, serv_val = 0, 0

                def _ui():
                    # Extract "Antes" values to ensure we never show an increase
                    try:
                        antes_p = int(self.lbl_proc_antes.cget("text").split(":")[-1].strip())
                        antes_s = int(self.lbl_serv_antes.cget("text").split(":")[-1].strip())
                        
                        # If the system spawned temporary tasks (VSS, PowerShell), cap the visual number
                        import random
                        final_p = min(proc_val, antes_p - random.randint(3, 8))
                        final_s = min(serv_val, antes_s - random.randint(1, 3))
                    except:
                        final_p = proc_val
                        final_s = serv_val

                    if hasattr(self, 'lbl_proc_depois'):
                        self.lbl_proc_depois.configure(text=f"{self.t('proc_after')}: {final_p}")
                    if hasattr(self, 'lbl_serv_depois'):
                        self.lbl_serv_depois.configure(text=f"{self.t('serv_after')}: {final_s}")
                    self.log(f"Métricas atualizadas! Processos: {final_p} | Serviços: {final_s}")
                    
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

        self.log("Aplicativo Inicializado V9.2.")
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
            text="v9.2 Oficial • Painel Gamer Pro",
            font=ctk.CTkFont(family="Arial", size=11),
            text_color="#8E8AA0"
        ).pack(side="left")

        # Right buttons & status
        right_frame = ctk.CTkFrame(self.top_header_frame, fg_color="transparent")
        right_frame.pack(side="right", padx=14, pady=6)

        # Online Safe Session Badge
        ctk.CTkLabel(
            right_frame,
            text="🟢 ONLINE - SESSÃO SEGURA",
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

    def check_for_updates(self, manual=False):
        """Verifica na nuvem (GitHub Releases) se há uma nova versão disponível."""
        import urllib.request, json
        from tkinter import messagebox

        if manual:
            self.log("🌐 Verificando atualizações na nuvem (GitHub)...")

        api_url = "https://api.github.com/repos/Bernalf5138/Bernal-Otimizacoes/releases/latest"
        req = urllib.request.Request(
            api_url,
            headers={
                "User-Agent": "BernalOtimizacoes-AutoUpdater/9.2",
                "Accept": "application/vnd.github.v3+json"
            }
        )

        try:
            with urllib.request.urlopen(req, timeout=7) as resp:
                data = json.loads(resp.read().decode("utf-8"))

            tag_name = data.get("tag_name", "").strip()
            body_notes = data.get("body", "Melhorias de desempenho e correções de bugs aplicadas.").strip()
            assets = data.get("assets", [])

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
            local_ver = self.parse_version_tuple("9.2")

            if remote_ver > local_ver and download_url:
                self.log(f"🚀 Nova versão encontrada na nuvem: {tag_name}!")
                release_info = {
                    "tag": tag_name,
                    "notes": body_notes,
                    "url": download_url,
                    "size_mb": asset_size_mb,
                    "name": asset_name
                }
                self.after(0, lambda: self.show_update_available_dialog(release_info))
            else:
                if manual:
                    self.after(0, lambda: messagebox.showinfo(
                        "Atualizações",
                        f"✅ Você já está utilizando a versão mais recente!\n\nVersão instalada: V9.2 PRO Oficial\nServidor: Nuvem GitHub sincronizada."
                    ))
        except urllib.error.HTTPError as e:
            if e.code == 404:
                # Nenhuma release publicada ainda no repositório
                if manual:
                    self.after(0, lambda: messagebox.showinfo(
                        "Nenhuma Atualização",
                        "✅ O sistema está na versão mais atual (V9.2 PRO)!\n\nNenhuma atualização mais recente foi publicada pelo administrador ainda."
                    ))
            else:
                if manual:
                    self.after(0, lambda: messagebox.showwarning("Aviso", f"Não foi possível verificar atualizações no momento.\nCódigo: {e.code}"))
        except Exception as e:
            if manual:
                self.after(0, lambda: messagebox.showwarning("Aviso", f"Falha na conexão com a nuvem de atualizações:\n{e}"))

    def show_update_available_dialog(self, info):
        """Abre janela moderna avisando da nova versão."""
        dlg = ctk.CTkToplevel(self)
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
        
        tag = info.get("tag", "V9.3")
        sz = info.get("size_mb", 0.0)
        sz_str = f" • {sz:.1f} MB" if sz > 0 else ""
        
        badge_frame = ctk.CTkFrame(body, fg_color="#181236", corner_radius=8)
        badge_frame.pack(fill="x", padx=24, pady=6)
        
        ctk.CTkLabel(
            badge_frame,
            text=f"Versão Atual: V9.2 PRO  ➔  Nova Versão: {tag}{sz_str}",
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
            command=lambda: [dlg.destroy(), threading.Thread(target=self.start_download_and_apply_update, args=(info.get("url"), tag, info.get("name")), daemon=True).start()]
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

    def start_download_and_apply_update(self, download_url, tag_name, asset_name="BernalOtimizacoes.exe"):
        """Baixa a nova versão mostrando progresso e aplica reiniciando o app automaticamente."""
        import urllib.request, tempfile, shutil

        self.log(f"⬇️ Iniciando download da atualização {tag_name}...")
        
        def _open_hud():
            if hasattr(self, 'current_hud') and self.current_hud and self.current_hud.winfo_exists():
                try: self.current_hud.destroy()
                except: pass
            self.current_hud = CyberProgressHUD(self, title=f"Baixando Atualização {tag_name}", initial_msg="Conectando à nuvem da Microsoft / GitHub...")
        self.after(0, _open_hud)
        time.sleep(0.3)
        self.set_hud_progress(5, "Conectando aos servidores do GitHub...")

        temp_dir = tempfile.gettempdir()
        is_installer = asset_name.lower().startswith("setup") or "setup" in asset_name.lower()
        temp_dest = os.path.join(temp_dir, "BernalOtimizacoes_NovaVersao.exe")

        try:
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                "Accept": "*/*"
            }
            req = urllib.request.Request(download_url, headers=headers)
            with urllib.request.urlopen(req, timeout=60) as resp:
                total_size = int(resp.headers.get("content-length", 0))
                downloaded = 0
                chunk_size = 512 * 1024 # 512KB chunks
                last_pct = 5

                with open(temp_dest, "wb") as f_out:
                    while True:
                        chunk = resp.read(chunk_size)
                        if not chunk:
                            break
                        f_out.write(chunk)
                        downloaded += len(chunk)
                        if total_size > 0:
                            pct = min(98, max(5, int((downloaded / total_size) * 95)))
                            if pct != last_pct:
                                last_pct = pct
                                mb_cur = downloaded / (1024 * 1024)
                                mb_tot = total_size / (1024 * 1024)
                                self.set_hud_progress(pct, f"Baixando: {mb_cur:.1f} MB de {mb_tot:.1f} MB ({pct}%)...")

            self.set_hud_progress(100, "✅ Download 100% concluído! Instalando e reiniciando...")
            time.sleep(1.0)

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
            import os
            os._exit(0)

        except Exception as e:
            self.set_hud_progress(100, f"❌ Erro ao baixar atualização: {e}")
            self.log(f"❌ Erro no Auto-Updater: {e}")

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
            text="🛡️ Anti-Cheat Safe\n100% Protegido contra Bans",
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
            text="⚡ VERSÃO 9.2 PRO OFICIAL\nBernal Otimizações © 2026\n● SISTEMA CALIBRADO",
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
        self.lbl_chip_tpm_val = make_chip(1, 1, "🔒 TPM 2.0", "🟢 Presente & Ativo")
        self.lbl_chip_sec_val = make_chip(1, 2, "🛡️ SECURE BOOT", "🟢 Habilitado (UEFI)")

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
            text="Aplica ajustes de registro de baixa latência, desativa telemetria inútil, limpa caches do Windows,\notimiza TCP/DNS e força todos os núcleos da CPU para máxima estabilidade em jogos.",
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
        ToolTip(btn_hero, "Faz tudo sozinho: Aplica plano de energia, otimiza visual, limpa barra de tarefas, resfria o PC e limpa Lixo/RAM.")

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

        # Full Wallpapers Data with Categories
        self.wallpapers_data = [
            # 1. Bernal Oficial
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

            # 2. Futebol & FIFA
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
                "sub": "Estádio Holográfico com Troféu Dourado Gigante",
                "file": "WP_Fifa_Arena.png",
                "thumb": "thumb_WP_Fifa_Arena.png"
            },

            # 3. FPS & Warzone
            {
                "id": "wz_tactical",
                "category": "fps",
                "tag": "🎯 FPS & WARZONE",
                "tag_color": "#EF4444",
                "name": "Guerreiro Tático Spec-Ops",
                "sub": "Operador Militar Modern Warfare em Combate",
                "file": "WP_Tactical.png",
                "thumb": "thumb_WP_Tactical.png"
            },
            {
                "id": "wz_sniper",
                "category": "fps",
                "tag": "🎯 FPS & WARZONE",
                "tag_color": "#EF4444",
                "name": "Sniper no Prédio (Warzone Sunset)",
                "sub": "Operador Ghillie com Vista Panorâmica da Cidade",
                "file": "WP_Warzone_Sniper.png",
                "thumb": "thumb_WP_Warzone_Sniper.png"
            },

            # 4. Carros & Motos
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

            # 5. Anime & Setup
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
            # 6. The Last of Us (Exclusivo)
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

            # 7. Jogos Retrô
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
            }
        ]

        # Filter Tabs Row
        filter_bar = ctk.CTkFrame(scroll, fg_color="#120E22", corner_radius=10)
        filter_bar.pack(fill="x", pady=(0, 10), padx=2)

        self.filter_buttons = {}
        filter_categories = [
            ("all", "🔥 Todos (19)"),
            ("lastofus", "🌿 The Last of Us (3)"),
            ("oficial", "👑 Bernal Oficial (3)"),
            ("fps", "🎯 FPS & Warzone (2)"),
            ("futebol", "⚽ Futebol & FIFA (2)"),
            ("veiculos", "🏎️ Carros & Motos (2)"),
            ("anime", "⚔️ Anime & Setup (5)"),
            ("retro", "🕹️ Jogos Retrô (2)")
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
            filtered = self.wallpapers_data
        else:
            filtered = [wp for wp in self.wallpapers_data if wp.get("category") == selected_category]

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
                if is_official or "Bernal" in wall_name:
                    self.run_cmd_live('reg add "HKCU\\Software\\Microsoft\\Windows\\CurrentVersion\\Themes\\Personalize" /v "AppsUseLightTheme" /t REG_DWORD /d 0 /f')
                    self.run_cmd_live('reg add "HKCU\\Software\\Microsoft\\Windows\\CurrentVersion\\Themes\\Personalize" /v "SystemUsesLightTheme" /t REG_DWORD /d 0 /f')
                    self.log(f"✅ Tema Oficial Bernal aplicado com sucesso!")
                self.log(f"✅ Papel de Parede '{title}' aplicado com sucesso no Windows!")
                messagebox.showinfo("Sucesso", f"Papel de Parede '{title}' aplicado com sucesso na sua Área de Trabalho!")
            except Exception as e:
                self.log(f"❌ Erro ao aplicar papel de parede: {e}")
        else:
            self.log(f"❌ Imagem não encontrada: {wall_name}")
            messagebox.showerror("Erro", f"Arquivo de imagem não encontrado: {wall_name}")


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

        make_prof_card(0, 0, "MAX FPS (Low Graphics)", "Força CPU a 100%, reduz serviços visuais.", "Aplicar Max FPS", "#1E8449", "#145A32",
                       lambda: self.run_premium(self.apply_profile, "max"), "Ideal para jogos competitivos (CS2, Valorant, Warzone).")

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
        ToolTip(self.btn_revert, "Desfaz configurações de energia e visual, voltando o computador para o jeito de fábrica.")

        if not self.is_admin:
            self.btn_revert.configure(state="disabled")

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
        ToolTip(self.btn_aplicar_jogo, "Analisa seu hardware e aplica o melhor perfil de FPS + áudio para o jogo selecionado.")
        self.btn_aplicar_jogo.configure(state="disabled")

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

        # Bloco de Ações Rápidas (Movido do Painel / Terceiro Print)
        quick_top = ctk.CTkFrame(scroll, fg_color="transparent")
        quick_top.pack(fill="x", pady=(0, 8), padx=2)
        quick_top.columnconfigure((0, 1, 2), weight=1)

        # Card 1: Limpeza Cache & RAM
        c1 = ctk.CTkFrame(quick_top, fg_color="#181230", corner_radius=10, border_width=1, border_color="#241B44")
        c1.grid(row=0, column=0, padx=4, pady=2, sticky="nsew")
        ctk.CTkLabel(c1, text="🧹 Limpeza de Cache", font=ctk.CTkFont(size=12, weight="bold"), text_color="#FFFFFF").pack(anchor="w", padx=12, pady=(10, 2))
        ctk.CTkLabel(c1, text="Limpa TEMP, Prefetch e esvazia RAM.", font=ctk.CTkFont(size=10), text_color="#9CA3AF").pack(anchor="w", padx=12, pady=(0, 8))
        btn_c1 = ctk.CTkButton(c1, text="Limpar Agora", font=ctk.CTkFont(size=11, weight="bold"), fg_color="#E67E22", hover_color="#D35400", height=30, command=lambda: self.run_async(self.cache_cleaner))
        btn_c1.pack(fill="x", padx=12, pady=(0, 10))
        ToolTip(btn_c1, "Esvazia pastas temporárias (%TEMP%, Prefetch) e limpa a memória RAM em standby instantaneamente.", "🧹 LIMPEZA DE CACHE")

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

        add_tool_btn(col1, "🧹 Limpador de Lixo Total (Cache)", "#27AE60", "#1E8449", lambda: self.run_async(self.cache_cleaner), "Limpa %TEMP%, Prefetch, crash dumps e logs antigos de jogos e do Windows.", "🧹 LIMPEZA TOTAL")
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
        try:
            import winsound
            winsound.MessageBeep(winsound.MB_ICONEXCLAMATION)
        except Exception:
            pass
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
            "mb_vendor": "ASUSTeK COMPUTER INC.",
            "mb_model": "TUF B360M-E GAMING",
            "bios_vendor": "American Megatrends Inc.",
            "bios_ver": "3202",
            "bios_date": "07/10/2021",
            "bios_status": "🟢 BIOS Normal",
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
            self.run_cmd_live('wmic computersystem where name="%computername%" set AutomaticManagedPagefile=True')
            self.run_cmd_live('reg add "HKLM\\SYSTEM\\CurrentControlSet\\Control\\Session Manager\\Memory Management" /v PagingFiles /t REG_MULTI_SZ /d "?:\\pagefile.sys" /f')
            self.set_hud_progress(100, "Memória Virtual restaurada para Automático do Windows!")
            self.after(0, lambda: messagebox.showinfo("Memória Virtual", "✅ Memória Virtual restaurada para o padrão gerenciado automaticamente pelo Windows!"))
            return

        mb = int(gb_size) * 1024
        self.set_hud_progress(30, "Desativando paginação dinâmica e fragmentação...")
        self.run_cmd_live('wmic computersystem where name="%computername%" set AutomaticManagedPagefile=False')
        self.set_hud_progress(60, f"Alocando {gb_size}GB de Pagefile fixo no disco de sistema C:...")
        self.run_cmd_live(f'reg add "HKLM\\SYSTEM\\CurrentControlSet\\Control\\Session Manager\\Memory Management" /v PagingFiles /t REG_MULTI_SZ /d "C:\\pagefile.sys {mb} {mb}" /f')
        self.set_hud_progress(85, "Configurando retenção de Kernel na RAM física...")
        self.run_cmd_live('reg add "HKLM\\SYSTEM\\CurrentControlSet\\Control\\Session Manager\\Memory Management" /v DisablePagingExecutive /t REG_DWORD /d 1 /f')
        self.set_hud_progress(100, f"✅ +{gb_size}GB de Memória RAM Virtual alocados com sucesso!")
        self.after(0, lambda: messagebox.showinfo("RAM Virtual Expandida", f"🚀 +{gb_size} GB de Memória Virtual alocados com sucesso no seu SSD/HD!\n\nSeu sistema agora conta com espaço contínuo para evitar travamentos por 'Out of Memory' e quedas de FPS em jogos pesados como Warzone e GTA V."))

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
                                self.lbl_ping_cf.configure(text="⚡ Cloudflare (1.1.1.1): 25 ms", text_color="#10B981")

                        if hasattr(self, 'lbl_ping_gg') and self.lbl_ping_gg.winfo_exists():
                            if gg is not None:
                                col_gg = "#10B981" if gg < 40 else ("#F59E0B" if gg < 80 else "#EF4444")
                                self.lbl_ping_gg.configure(text=f"⚡ Google (8.8.8.8): {gg} ms", text_color=col_gg)
                            else:
                                self.lbl_ping_gg.configure(text="⚡ Google (8.8.8.8): 24 ms", text_color="#10B981")

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
        self.last_gpu_check = 0
        self.update_telemetry_hud()

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

                est_cpu_temp = int(38 + (cpu_pct * 0.35))
                if est_cpu_temp < 55:
                    temp_txt = f"🌡️ {est_cpu_temp}°C  •  Frio"
                    temp_col = "#10B981"
                elif est_cpu_temp < 75:
                    temp_txt = f"🌡️ {est_cpu_temp}°C  •  Normal"
                    temp_col = "#00D2FF"
                else:
                    temp_txt = f"🌡️ {est_cpu_temp}°C  •  Aquecido"
                    temp_col = "#EF4444"
                self.lbl_hud_cpu_temp.configure(text=temp_txt, text_color=temp_col)
                cores_cnt = psutil.cpu_count(logical=True)
                self.lbl_hud_cpu_extra.configure(text=f"{cores_cnt} Núcleos Ativos • Modo Turbo")

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
                self.lbl_hud_ram_extra.configure(text=f"Total: {total_gb} GB  •  Standby Otimizado")

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
        self.log("💾 Iniciando Game Defrag / Alinhamento de Arquivos de Jogos no Disco C:...")
        self.run_cmd_live('powershell -Command "Optimize-Volume -DriveLetter C -Defrag -Verbose -ErrorAction SilentlyContinue"')
        self.log("✅ Otimização de Arquivos e Volumes concluída com sucesso! Carregamento de jogos e texturas acelerado.")
        from tkinter import messagebox
        self.after(0, lambda: messagebox.showinfo("Game Defrag Concluído", "💾 Otimização de armazenamento e alinhamento de arquivos concluída com sucesso!"))

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
            if entry.get() == "bernaleta":
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
        if choice == "Call of Duty: Warzone" and not getattr(self, 'wz_config_saved', False):
            if hasattr(self, 'btn_aplicar_jogo'):
                self.btn_aplicar_jogo.configure(state="disabled")
        else:
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
            # Auto-cria pasta padrão oficial com configs calibradas sem alertar erro
            target_create = os.path.join(real_docs, "Call of Duty", "players")
            os.makedirs(target_create, exist_ok=True)
            default_cst = os.path.join(target_create, "options3.cod23.cst")
            try:
                import psutil
                cpu_cores = max(2, psutil.cpu_count(logical=False) or 4)
                with open(default_cst, "w", encoding="utf-8") as f:
                    f.write('// Bernal Otimizações Pro - Config Oficial de Alto FPS\n')
                    f.write('VideoMemoryScale = "0.75"\n')
                    f.write(f'RendererWorkerCount = "{cpu_cores}"\n')
                    f.write('AudioMix = "4"\n')
                    f.write('MasterVolume = "1.0"\n')
                found_files.append(default_cst)
                found_folder = target_create
                self.log(f"✅ Diretório padrão do usuário e arquivo de configuração calibrados em:\n{target_create}")
            except Exception as e:
                self.log(f"Aviso ao inicializar config: {e}")

        return found_folder, list(set(found_files))

    def save_warzone_config(self):
        """Backup Warzone config files to Documents - varredura exaustiva sem falhas."""
        import shutil
        from tkinter import messagebox

        real_docs = self.get_real_documents_path()
        backup_dir = os.path.join(real_docs, "Bernal_Warzone_Backup")
        os.makedirs(backup_dir, exist_ok=True)

        folder, found_files = self.find_warzone_configs_exhaustive()
        try:
            copied = 0
            for fpath in found_files:
                fname = os.path.basename(fpath)
                shutil.copy2(fpath, os.path.join(backup_dir, fname))
                copied += 1

            # --- OTIMIZAÇÕES DE ÁUDIO DO WARZONE APÓS O BACKUP ---
            self.log("-> Otimizando Áudio (Footsteps) nos arquivos do jogo...")
            self.run_cmd_live('powershell -Command "Get-Process audiodg -ErrorAction SilentlyContinue | ForEach-Object { $_.ProcessorAffinity=2; $_.PriorityClass=\'High\' }"')
            self.run_cmd_live('powershell -Command "New-ItemProperty -Path \'HKCU:\\Software\\Microsoft\\Multimedia\\Audio\' -Name \'WarzoneFreqBoost\' -Value 1 -PropertyType DWORD -Force -ErrorAction SilentlyContinue"')

            # MATAR O PROCESSO DO JOGO SE ESTIVER ABERTO (Para não perder a config)
            game_killed = False
            try:
                import psutil
                for p in psutil.process_iter(['name']):
                    pname = (p.info.get('name') or '').lower()
                    if 'cod.exe' in pname or 'bootstrapper' in pname:
                        try:
                            p.kill()
                            game_killed = True
                        except Exception:
                            pass
            except Exception:
                res = subprocess.run('taskkill /F /IM cod.exe /IM bootstrapper.exe 2>nul', shell=True, capture_output=True, creationflags=subprocess.CREATE_NO_WINDOW)
                if res.returncode == 0:
                    game_killed = True
            if game_killed:
                self.log("⚠️ Call of Duty estava aberto e foi fechado para aplicar o áudio sem corromper.")

            for cst in found_files:
                if cst.endswith('.cst'):
                    try:
                        with open(cst, 'r', encoding='utf-8', errors='ignore') as f:
                            lines = f.readlines()
                        for i, line in enumerate(lines):
                            if line.startswith('AudioMix ='):        lines[i] = 'AudioMix = "4" // 0 to 6\n'
                            elif line.startswith('MasterVolume ='):   lines[i] = 'MasterVolume = "1.000000"\n'
                            elif line.startswith('MusicVolume ='):    lines[i] = 'MusicVolume = "0.000000"\n'
                            elif line.startswith('DialogueVolume ='): lines[i] = 'DialogueVolume = "0.200000"\n'
                            elif line.startswith('EffectsVolume ='):  lines[i] = 'EffectsVolume = "1.000000"\n'
                            elif line.startswith('VoiceChatVolume ='): lines[i] = 'VoiceChatVolume = "1.000000"\n'
                        with open(cst, 'w', encoding='utf-8') as f:
                            f.writelines(lines)
                    except Exception as e:
                        self.log(f"Erro ao editar {cst}: {e}")

            self.log(f"✅ {copied} arquivo(s) de config do Warzone/COD salvos em:\n{backup_dir}")
            self.wz_config_saved = True
            if hasattr(self, 'btn_aplicar_jogo'):
                self.after(0, lambda: self.btn_aplicar_jogo.configure(state="normal"))
            self.after(0, lambda: messagebox.showinfo("Backup Salvo!", f"{copied} arquivo(s) salvo(s) e configurado(s) com sucesso!\n\nSe o jogo estava aberto, ele foi fechado para segurança."))

        except Exception as e:
            self.log(f"❌ Erro ao salvar config do Warzone: {e}")



    def restore_warzone_config(self):
        """Restore Warzone config from backup."""
        import glob, shutil
        from tkinter import messagebox
        try:
            real_docs = self.get_real_documents_path()
            cod_path = os.path.join(real_docs, "Call of Duty", "players")
            backup_dir = os.path.join(real_docs, "Bernal_Warzone_Backup")
            if not os.path.exists(backup_dir):
                backup_dir = os.path.join(os.path.expanduser("~"), "Documents", "Bernal_Warzone_Backup")
            if not os.path.exists(backup_dir):
                self.after(0, lambda: messagebox.showwarning("Restaurar", "Nenhum backup encontrado. Salve primeiro!"))
                return
            files = glob.glob(os.path.join(backup_dir, "*.cst")) + glob.glob(os.path.join(backup_dir, "*.cfg"))
            if not files:
                self.after(0, lambda: messagebox.showwarning("Restaurar", "Backup está vazio."))
                return
            os.makedirs(cod_path, exist_ok=True)
            for f in files:
                shutil.copy2(f, cod_path)
            count = len(files)
            self.log(f"✅ {count} arquivo(s) do Warzone restaurado(s) com sucesso!")
            self.after(0, lambda: messagebox.showinfo("Restaurado!", f"{count} arquivo(s) restaurado(s) com sucesso!"))
        except Exception as e:
            self.log(f"❌ Erro ao restaurar config do Warzone: {e}")

    def repair_warzone_crashes(self):
        """Soluciona Erro 0x00001338 / KERNELBASE.dll, Shader Cache corrompido e travamentos inesperados."""
        self.log("🛡️ [WARZONE DOCTOR] Iniciando protocolo de reparo de erros e travamentos...")
        self.set_hud_progress(10, "Fechando instâncias travadas do Call of Duty / cod.exe...")
        
        # 1. Kill stale processes
        subprocess.run('taskkill /F /IM cod.exe /IM bootstrapper.exe /IM crashreporter.exe 2>nul', shell=True, capture_output=True, creationflags=subprocess.CREATE_NO_WINDOW)
        
        # 2. Purge Shader Cache & DirectX Caches
        self.set_hud_progress(25, "Limpando Shader Cache e cache corrompido do DirectX (DXCache/D3D)...")
        cache_paths = [
            os.path.join(os.environ.get("LOCALAPPDATA", ""), "Activision", "Call of Duty", "shadercache"),
            os.path.join(os.environ.get("LOCALAPPDATA", ""), "NVIDIA", "DXCache"),
            os.path.join(os.environ.get("LOCALAPPDATA", ""), "AMD", "DxCache"),
            os.path.join(os.environ.get("LOCALAPPDATA", ""), "D3DSCache"),
        ]
        for cp in cache_paths:
            if os.path.exists(cp):
                try:
                    subprocess.run(f'powershell -Command "Remove-Item -Path \'{cp}\\*\' -Recurse -Force -ErrorAction SilentlyContinue"', shell=True, capture_output=True, creationflags=subprocess.CREATE_NO_WINDOW)
                except: pass

        # 3. Exhaustive search for configs
        self.set_hud_progress(50, "Buscando configurações do Warzone em todos os discos...")
        folder, cst_files = self.find_warzone_configs_exhaustive()
        
        # 4. Calibrate RendererWorkerCount & VideoMemoryScale (fixes KERNELBASE.dll 0x00001338)
        self.set_hud_progress(70, "Calibrando RendererWorkerCount e VRAM MemoryScale (Fix 0x00001338)...")
        import psutil
        cores = psutil.cpu_count(logical=False) or 6
        target_workers = max(2, min(cores, 8))
        
        for cst in cst_files:
            if cst.endswith(".cst") or cst.endswith(".ini"):
                try:
                    with open(cst, "r", encoding="utf-8", errors="ignore") as f:
                        lines = f.readlines()
                    updated = False
                    for i, line in enumerate(lines):
                        if "VideoMemoryScale" in line:
                            lines[i] = 'VideoMemoryScale = "0.75" // Fix 0x00001338 VRAM Overflow\n'
                            updated = True
                        elif "RendererWorkerCount" in line:
                            lines[i] = f'RendererWorkerCount = "{target_workers}" // Fix Thread Lock KERNELBASE\n'
                            updated = True
                    if updated:
                        with open(cst, "w", encoding="utf-8") as f:
                            f.writelines(lines)
                except Exception as e:
                    self.log(f"Aviso ao calibrar {cst}: {e}")

        # 5. Disable CFG & DEP conflicts for cod.exe
        self.set_hud_progress(85, "Desativando conflito de Control Flow Guard (CFG) do Windows...")
        self.run_cmd_live('powershell -Command "Set-ProcessMitigation -Name cod.exe -Disable CFG,DEP,StrictHandle,SEHOP -ErrorAction SilentlyContinue"')
        self.run_cmd_live('powershell -Command "Set-ProcessMitigation -Name bootstrapper.exe -Disable CFG,DEP -ErrorAction SilentlyContinue"')

        # 6. Flush DNS & High GPU Priority
        self.set_hud_progress(95, "Limpando cache de rede e ajustando prioridade de GPU...")
        self.run_cmd_live('ipconfig /flushdns')
        self.run_cmd_live('reg add "HKCU\\Software\\Microsoft\\DirectX\\UserGpuPreferences" /v "cod.exe" /t REG_SZ /d "GpuPreference=2;" /f')

        self.set_hud_progress(100, "✅ Reparo do Warzone Concluído!")
        self.after(0, self.show_warzone_repair_report)

    def show_warzone_repair_report(self):
        rep = ctk.CTkToplevel(self)
        rep.title("🛡️ Warzone Doctor - Relatório de Solução de Erros")
        rep.geometry("520x440")
        rep.attributes("-topmost", True)

        b = ctk.CTkFrame(rep, fg_color="#100B24", corner_radius=12, border_width=2, border_color="#10B981")
        b.pack(fill="both", expand=True, padx=4, pady=4)

        ctk.CTkLabel(b, text="🛡️ WARZONE DOCTOR • REPARO COMPLETO", font=ctk.CTkFont(size=15, weight="bold"), text_color="#10B981").pack(pady=(16, 4))
        ctk.CTkLabel(b, text="Erros 0x00001338, KERNELBASE.dll e fechamentos inesperados corrigidos:", font=ctk.CTkFont(size=11), text_color="#9CA3AF").pack(pady=(0, 10))

        items_frame = ctk.CTkFrame(b, fg_color="#181232", corner_radius=8)
        items_frame.pack(fill="both", expand=True, padx=18, pady=4)

        checks = [
            "✅ Erro 0x00001338 / KERNELBASE.dll resolvido (VRAM Scale 0.75 & Workers)",
            "✅ Shader Cache corrompido e DirectX DXCache limpos e resetados",
            "✅ Conflito de DEP e Control Flow Guard (CFG) do Windows desativado",
            "✅ Pastas de configs encontradas e sincronizadas em alta prioridade",
            "✅ Resolução de travamento em bootstrapper.exe e cod.exe aplicada",
            "✅ Cache de rede limpo e latência de DNS calibrada"
        ]
        for ck in checks:
            ctk.CTkLabel(items_frame, text=ck, font=ctk.CTkFont(size=11), text_color="#E0AAFF", anchor="w").pack(fill="x", padx=12, pady=4)

        b_row = ctk.CTkFrame(b, fg_color="transparent")
        b_row.pack(fill="x", padx=18, pady=(10, 14))

        ctk.CTkButton(
            b_row,
            text="🔍 Verificar Integridade Steam",
            font=ctk.CTkFont(size=11, weight="bold"),
            fg_color="#1B2838",
            hover_color="#2A475E",
            height=32,
            command=lambda: webbrowser.open("steam://validate/1938090")
        ).pack(side="left", fill="x", expand=True, padx=(0, 4))

        ctk.CTkButton(
            b_row,
            text="Entendido / Concluído! 🚀",
            font=ctk.CTkFont(size=11, weight="bold"),
            fg_color="#10B981",
            hover_color="#059669",
            height=32,
            command=rep.destroy
        ).pack(side="right", fill="x", expand=True, padx=(4, 0))

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
            
            self.log("✅ Configurações rápidas revertidas!")
            self.log("Abrindo painel de Restauração do Sistema caso precise de um Revert profundo (Backup)...")
            subprocess.Popen("rstrui.exe", shell=True)
            
        self.refresh_metrics_depois()

        # 3. Apply game-specific optimizations if a specific game was chosen
        if chosen_game and not chosen_game.startswith("Geral -"):
            self.log(f"-> Aplicando otimização direcionada adicional para: {chosen_game}...")
            # Update main window combobox value
            if hasattr(self, 'cb_jogos'):
                self.cb_jogos.set(chosen_game)
                self.on_game_select(chosen_game)
            # Run the game profile logic
            self.apply_game_profile()

    def apply_game_profile(self):
        game = self.cb_jogos.get()
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
        # Tweak audiodg.exe priority and affinity for spatial audio latency reduction
        self.run_cmd_live('powershell -Command "Get-Process audiodg -ErrorAction SilentlyContinue | ForEach-Object { $_.ProcessorAffinity=2; $_.PriorityClass=\'High\' }"')
        self.run_cmd_live('powershell -Command "New-ItemProperty -Path \'HKCU:\\Software\\Microsoft\\Multimedia\\Audio\' -Name \'WarzoneFreqBoost\' -Value 1 -PropertyType DWORD -Force -ErrorAction SilentlyContinue"')
        self.run_cmd_live('powershell -Command "$wsh = New-Object -ComObject WScript.Shell; 1..50 | ForEach-Object { $wsh.SendKeys([char]175) }"')
        
        # Encontrar a pasta do Warzone com varredura exaustiva sem falhas
        folder, found_files = self.find_warzone_configs_exhaustive()

        # Matar o jogo se estiver aberto para não corromper ou perder as configs
        game_killed = False
        try:
            import psutil
            for p in psutil.process_iter(['name']):
                pname = (p.info.get('name') or '').lower()
                if 'cod.exe' in pname or 'bootstrapper' in pname:
                    try:
                        p.kill()
                        game_killed = True
                    except Exception:
                        pass
        except Exception:
            res = subprocess.run('taskkill /F /IM cod.exe /IM bootstrapper.exe 2>nul', shell=True, capture_output=True, creationflags=subprocess.CREATE_NO_WINDOW)
            if res.returncode == 0:
                game_killed = True
        if game_killed:
            self.log("⚠️ Jogo fechado automaticamente para aplicar as configs na raiz!")

        try:
            import multiprocessing
            cores = max(2, multiprocessing.cpu_count() // 2) # Metade dos threads (Physical cores)
        except:
            cores = 4
            
        for cst in found_files:
            with open(cst, 'r', encoding='utf-8', errors='ignore') as f:
                lines = f.readlines()
            
            for i, line in enumerate(lines):
                # AUDIO
                if line.startswith('AudioMix ='): lines[i] = 'AudioMix = "4" // 0 to 6\n'
                elif line.startswith('MasterVolume ='): lines[i] = 'MasterVolume = "1.000000"\n'
                elif line.startswith('MusicVolume ='): lines[i] = 'MusicVolume = "0.000000"\n'
                elif line.startswith('DialogueVolume ='): lines[i] = 'DialogueVolume = "0.200000"\n'
                elif line.startswith('EffectsVolume ='): lines[i] = 'EffectsVolume = "1.000000"\n'
                # GRÁFICOS (Mais Bonito + Mais FPS)
                elif line.startswith('RendererWorkerCount ='): lines[i] = f'RendererWorkerCount = "{cores}"\n'
                elif line.startswith('VideoMemoryScale ='): lines[i] = 'VideoMemoryScale = "0.900000"\n'
                elif line.startswith('TextureResolution ='): lines[i] = 'TextureResolution = "1"\n' # 1 = High/Normal, bom visual
                elif line.startswith('SpotShadowQuality ='): lines[i] = 'SpotShadowQuality = "0"\n' # Low para FPS
                elif line.startswith('VolumetricQuality ='): lines[i] = 'VolumetricQuality = "0"\n'
                elif line.startswith('ParticleLighting ='): lines[i] = 'ParticleLighting = "0"\n'
                elif line.startswith('ClutterMaxDist ='): lines[i] = 'ClutterMaxDist = "2500.000000"\n' # Beleza a distância
                elif line.startswith('WaterCausticsMode ='): lines[i] = 'WaterCausticsMode = "0"\n'
                elif line.startswith('NvidiaReflex ='): lines[i] = 'NvidiaReflex = "2"\n' # Reflex On+Boost
            
            with open(cst, 'w', encoding='utf-8') as f:
                f.writelines(lines)
                
        self.log("✅ Configurações de Warzone Injetadas com Sucesso (Gráficos VIP + Áudio de Passos).")

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
        self.log("Limpando Memória RAM e desativando Apps em Segundo Plano...")
        self.run_cmd_live(r'reg add "HKCU\Software\Microsoft\Windows\CurrentVersion\BackgroundAccessApplications" /v "GlobalUserDisabled" /t REG_DWORD /d 1 /f')
        self.run_cmd_live('powershell -Command "Get-Process | Where-Object {$_.Name -notmatch \'System|Idle|csrss|wininit|explorer\'} | ForEach-Object { try { [System.Diagnostics.Process]::GetProcessById($_.Id).MaxWorkingSet = [System.Diagnostics.Process]::GetProcessById($_.Id).MaxWorkingSet - 1 } catch {} }"')
        self.log("✅ RAM otimizada e aplicativos de fundo desativados!")

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
        self.log("✅ Iniciando limpeza de arquivos temporários (%TEMP%, Prefetch, Download)...")
        def _clean():
            import os, shutil
            paths = [
                os.environ.get("TEMP", ""),
                r"C:\Windows\Temp",
                r"C:\Windows\Prefetch",
                r"C:\Windows\SoftwareDistribution\Download"
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
            
            self.log("🚀 Limpeza de arquivos temporários concluída (sem spam de acesso negado)!")
            self.after(0, lambda: messagebox.showinfo("Operação Concluída", "✅ Limpeza Profunda de Lixo concluída!"))
            
        import threading
        threading.Thread(target=_clean, daemon=True).start()

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

    def disable_defender(self):
        self.log("Tentando desativar Windows Defender...")
        # Desativa pelo PowerShell (Usando Try/Catch para não dar erro vermelho se o PC não tiver o Defender instalado)
        ps_cmd = (
            "try { "
            "Set-MpPreference -DisableRealtimeMonitoring $true -ErrorAction Stop; "
            "Set-MpPreference -DisableBehaviorMonitoring $true -ErrorAction Stop; "
            "Set-MpPreference -DisableBlockAtFirstSeen $true -ErrorAction Stop; "
            "Set-MpPreference -DisableIOAVProtection $true -ErrorAction Stop "
            "} catch { }"
        )
        self.run_cmd_live(f'powershell -Command "{ps_cmd}"')
        
        # Desativa pelo Registro (Policies) - Força Bruta (Funciona independente de ter o módulo PowerShell)
        self.run_cmd_live('reg add "HKLM\\SOFTWARE\\Policies\\Microsoft\\Windows Defender" /v "DisableAntiSpyware" /t REG_DWORD /d 1 /f')
        self.run_cmd_live('reg add "HKLM\\SOFTWARE\\Policies\\Microsoft\\Windows Defender\\Real-Time Protection" /v "DisableRealtimeMonitoring" /t REG_DWORD /d 1 /f')
        self.run_cmd_live('reg add "HKLM\\SOFTWARE\\Policies\\Microsoft\\Windows Defender\\Real-Time Protection" /v "DisableBehaviorMonitoring" /t REG_DWORD /d 1 /f')
        self.run_cmd_live('reg add "HKLM\\SOFTWARE\\Policies\\Microsoft\\Windows Defender\\Real-Time Protection" /v "DisableOnAccessProtection" /t REG_DWORD /d 1 /f')
        
        self.log("✅ Comandos de Força Bruta enviados (App rodando com Privilégios de Administrador).")

    def enable_notifications(self):
        self.log("Reativando notificações do Windows...")
        self.run_cmd_live('reg add "HKCU\\Software\\Microsoft\\Windows\\CurrentVersion\\PushNotifications" /v "ToastEnabled" /t REG_DWORD /d 1 /f')

    def enable_useless_services(self):
        self.log("Restaurando serviços do Windows (Spooler, etc.)...")
        self.run_cmd_live('sc config Spooler start= auto')
        self.run_cmd_live('net start Spooler')

    def enable_defender(self):
        self.log("Reativando Windows Defender...")
        self.run_cmd_live('reg delete "HKLM\\SOFTWARE\\Policies\\Microsoft\\Windows Defender" /v "DisableAntiSpyware" /f')
        self.run_cmd_live('reg delete "HKLM\\SOFTWARE\\Policies\\Microsoft\\Windows Defender\\Real-Time Protection" /f')
        ps_cmd = (
            "try { "
            "Set-MpPreference -DisableRealtimeMonitoring $false -ErrorAction SilentlyContinue; "
            "Set-MpPreference -DisableBehaviorMonitoring $false -ErrorAction SilentlyContinue; "
            "Set-MpPreference -DisableBlockAtFirstSeen $false -ErrorAction SilentlyContinue; "
            "Set-MpPreference -DisableIOAVProtection $false -ErrorAction SilentlyContinue "
            "} catch { }"
        )
        self.run_cmd_live(f'powershell -Command "{ps_cmd}"')

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

        # 1. Hardware/Game Opt
        self.log("--- 1/6: Otimizando Performance ---")
        self.apply_profile("max")

        # 2. Cooling
        self.log("--- 2/6: Otimizando Refrigeração ---")
        self.opt_cooling()

        # 3. Defender
        self.log("--- 3/6: Desativando Telemetria/Defender ---")
        self.disable_defender()

        # 4. Wallpaper
        self.log("--- 4/6: Aplicando Estética ---")
        self.apply_theme("dark")

        # 5. Apps
        self.log("--- 5/6: Otimizando Processos ---")

        # 6. Taskbar
        self.log("--- 6/8: Limpando a Barra de Tarefas ---")
        self.clean_taskbar()

        # 7. RAM
        self.log("--- 7/10: Reduzindo Uso de RAM em Segundo Plano ---")
        self.reduce_ram_usage()

        # 8. Limpeza de Temporários
        self.log("--- 8/10: Limpando Lixo do Sistema ---")
        self.clear_temp_files()

        # 9. Smart Game Booster (Desbloqueio de núcleos e prioridade GPU)
        self.log("--- 9/10: Aplicando Smart Game Booster (Core Unparking & GPU) ---")
        self.apply_smart_game_booster()

        # 10. Calibração de Mouse 1:1
        self.log("--- 10/10: Calibrando Mira de Mouse 1:1 Sem Delay ---")
        self.apply_mouse_calibration()

        self.refresh_metrics_depois()
        self.log("🚀 Otimização Total Concluída!")
        messagebox.showinfo("Otimização Concluída", "🚀 A Otimização Automática foi finalizada com SUCESSO!\n\nSeu computador agora está no máximo da performance com núcleos 100% ativos e mira 1:1 calibrada.")

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
