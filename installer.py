import customtkinter as ctk
import os, sys, shutil, threading, subprocess, time

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

INSTALL_DIR  = os.path.join(os.environ.get("LOCALAPPDATA", os.path.expanduser("~")), "Bernal Otimizacoes")
APP_NAME     = "Bernal Otimizações Pro V9.2"
EXE_NAME     = "BernalOtimizacoes.exe"
DESKTOP_PATH = os.path.join(os.path.expanduser("~"), "Desktop")

def create_shortcut(target, shortcut_path):
    """Create a .lnk shortcut using PowerShell (no extra dependencies)."""
    ps = (
        f'$ws = New-Object -ComObject WScript.Shell; '
        f'$sc = $ws.CreateShortcut("{shortcut_path}"); '
        f'$sc.TargetPath = "{target}"; '
        f'$sc.WorkingDirectory = "{os.path.dirname(target)}"; '
        f'$sc.IconLocation = "{target}"; '
        f'$sc.Save()'
    )
    subprocess.run(["powershell", "-Command", ps],
                   creationflags=subprocess.CREATE_NO_WINDOW)

class InstallerApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Setup - Bernal Otimizações V9.2")
        self.geometry("600x450")
        self.resizable(False, False)
        
        self.is_update = os.path.exists(os.path.join(INSTALL_DIR, EXE_NAME))

        # ---- Header ----
        header = ctk.CTkFrame(self, fg_color="#0d1117", corner_radius=0)
        header.pack(fill="x")
        ctk.CTkLabel(header, text="⚡ Bernal Otimizações Pro",
                     font=ctk.CTkFont(size=22, weight="bold"),
                     text_color="#00d4ff").pack(pady=14)
        ctk.CTkLabel(header, text="Assistente de Instalação  •  Versão 9.2 (Oficial)",
                     font=ctk.CTkFont(size=11), text_color="#888").pack(pady=(0, 10))

        # ---- Body ----
        self.body = ctk.CTkFrame(self, fg_color="#161b22", corner_radius=0)
        self.body.pack(fill="both", expand=True)
        self.build_welcome()

        # ---- Footer ----
        footer = ctk.CTkFrame(self, fg_color="#0d1117", corner_radius=0, height=60)
        footer.pack(fill="x", side="bottom")
        footer.pack_propagate(False)
        
        btn_text = "🔄 Atualizar App" if self.is_update else "Instalar  ▶"
        btn_color = "#27AE60" if self.is_update else "#00b4d8"
        btn_hover = "#1E8449" if self.is_update else "#0077b6"
        
        self.btn_action = ctk.CTkButton(footer, text=btn_text,
                                         fg_color=btn_color, hover_color=btn_hover,
                                         font=ctk.CTkFont(size=14, weight="bold"),
                                         width=150, height=36,
                                         command=self.start_install)
        self.btn_action.pack(side="right", padx=20, pady=12)
        self.btn_cancel = ctk.CTkButton(footer, text="Cancelar",
                                         fg_color="#21262d", hover_color="#30363d",
                                         width=100, height=36,
                                         command=self.destroy)
        self.btn_cancel.pack(side="right", pady=12)

    def build_welcome(self):
        for w in self.body.winfo_children():
            w.destroy()

        ctk.CTkLabel(self.body, text="📁  Será instalado em:",
                     font=ctk.CTkFont(size=13), text_color="#ccc").pack(anchor="w", padx=30, pady=(20, 4))

        path_frame = ctk.CTkFrame(self.body, fg_color="#0f3460", corner_radius=8)
        path_frame.pack(fill="x", padx=30)
        ctk.CTkLabel(path_frame, text=INSTALL_DIR,
                     font=ctk.CTkFont(size=12), text_color="#aaa").pack(side="left", padx=12, pady=8)

        ctk.CTkLabel(self.body, text="✅  Criar atalho na Área de Trabalho",
                     font=ctk.CTkFont(size=12), text_color="#aaa").pack(anchor="w", padx=30, pady=(16, 2))
        ctk.CTkLabel(self.body, text="✅  Adicionar ao Menu Iniciar",
                     font=ctk.CTkFont(size=12), text_color="#aaa").pack(anchor="w", padx=30, pady=2)
        ctk.CTkLabel(self.body, text="✅  Executar ao concluir",
                     font=ctk.CTkFont(size=12), text_color="#aaa").pack(anchor="w", padx=30, pady=2)

        # --- Header ---
        self.lbl_title = ctk.CTkLabel(self.body, text="Bernal Otimizações PRO - Setup (V9.2)", font=ctk.CTkFont(size=11), text_color="#00d4ff")
        self.lbl_status = ctk.CTkLabel(self.body, text="",
                                        font=ctk.CTkFont(size=11), text_color="#00d4ff")
        self.lbl_status.pack(anchor="w", padx=30, pady=(18, 2))
        self.progressbar = ctk.CTkProgressBar(self.body, width=490)
        self.progressbar.pack(fill="x", padx=30)
        self.progressbar.set(0)
        self.lbl_status.pack_forget()
        self.progressbar.pack_forget()

    def setstatus(self, msg, val):
        self.lbl_status.configure(text=msg)
        self.progressbar.set(val)
        self.update_idletasks()

    def start_install(self):
        self.btn_action.configure(state="disabled")
        self.btn_cancel.configure(state="disabled")
        self.lbl_status.pack(anchor="w", padx=30, pady=(18, 2))
        self.progressbar.pack(fill="x", padx=30)
        threading.Thread(target=self.do_install, daemon=True).start()

    def do_install(self):
        try:
            self.after(0, lambda: self.setstatus("📂 Criando pasta de instalação...", 0.08))
            os.makedirs(INSTALL_DIR, exist_ok=True)
            time.sleep(0.2)

            # Clean up old version desktop shortcuts
            try:
                for item in os.listdir(DESKTOP_PATH):
                    if item.endswith(".lnk") and ("Bernal Otimiz" in item or "Bernal Otimi" in item):
                        os.remove(os.path.join(DESKTOP_PATH, item))
            except:
                pass

            # Clean up old version Start Menu directories/shortcuts
            try:
                sm_parent_dir = os.path.join(os.environ.get('APPDATA', ''), r'Microsoft\Windows\Start Menu\Programs')
                if os.path.exists(sm_parent_dir):
                    for item in os.listdir(sm_parent_dir):
                        if "Bernal Otimiz" in item:
                            p = os.path.join(sm_parent_dir, item)
                            if os.path.isdir(p):
                                shutil.rmtree(p)
                            else:
                                os.remove(p)
            except:
                pass

            self.after(0, lambda: self.setstatus("📋 Fechando instâncias antigas e copiando arquivos...", 0.25))
            subprocess.run('taskkill /F /IM BernalOtimizacoes.exe', shell=True, capture_output=True, creationflags=subprocess.CREATE_NO_WINDOW)
            time.sleep(1)

            if getattr(sys, 'frozen', False):
                base = sys._MEIPASS
                exe_dir = os.path.dirname(sys.executable)
            else:
                base = os.path.dirname(os.path.abspath(__file__))
                exe_dir = base

            src_app = os.path.join(base, EXE_NAME)
            if not os.path.exists(src_app):
                src_app = os.path.join(exe_dir, EXE_NAME)
            if not os.path.exists(src_app):
                src_app = os.path.join(os.getcwd(), EXE_NAME)
                
            dest_app = os.path.join(INSTALL_DIR, EXE_NAME)
            if os.path.exists(src_app):
                shutil.copy2(src_app, dest_app)
            time.sleep(0.3)

            # --- Copiar Wallpapers Exclusivos ---
            self.after(0, lambda: self.setstatus("🎨 Extraindo Papéis de Parede Gamers...", 0.32))
            wallpapers = [
                "WP_Dark.png", "WP_Light.png", "WP_Fem.png", "Wallpaper_Bernal.png",
                "WP_Ninja.png", "WP_Tactical.png", "WP_Cyber.png", "WP_Aura.png",
                "WP_Futebol.png", "WP_Fifa_Arena.png", "WP_Warzone_Sniper.png",
                "WP_Supercar.png", "WP_Superbike.png", "WP_Cyber_Samurai.png",
                "WP_LastOfUs.png", "WP_LastOfUs_Ellie.png", "WP_LastOfUs_Firefly.png",
                "WP_Retro_Arcade.png", "WP_Retro_Fighter.png",
                "thumb_WP_Dark.png", "thumb_WP_Light.png", "thumb_WP_Fem.png", "thumb_Wallpaper_Bernal.png",
                "thumb_WP_Ninja.png", "thumb_WP_Tactical.png", "thumb_WP_Cyber.png", "thumb_WP_Aura.png",
                "thumb_WP_Futebol.png", "thumb_WP_Fifa_Arena.png", "thumb_WP_Warzone_Sniper.png",
                "thumb_WP_Supercar.png", "thumb_WP_Superbike.png", "thumb_WP_Cyber_Samurai.png",
                "thumb_WP_LastOfUs.png", "thumb_WP_LastOfUs_Ellie.png", "thumb_WP_LastOfUs_Firefly.png",
                "thumb_WP_Retro_Arcade.png", "thumb_WP_Retro_Fighter.png"
            ]
            for wall in wallpapers:
                src_wall = None
                for cand in [os.path.join(base, wall), os.path.join(exe_dir, wall), os.path.join(os.getcwd(), wall)]:
                    if os.path.exists(cand):
                        src_wall = cand
                        break
                if src_wall:
                    dest_wall = os.path.join(INSTALL_DIR, wall)
                    try:
                        shutil.copy2(src_wall, dest_wall)
                    except Exception as e:
                        print(f"Erro ao copiar wallpaper {wall}: {e}")
            time.sleep(0.2)
            
            # --- Copiar arquivos AME pesados ---
            self.after(0, lambda: self.setstatus("📦 Extraindo pacotes AME e Playbooks...", 0.35))
            for extra_file in ["AME-Beta-v0.8.4.exe", "Atlsbook_v0.5.0.apbx", "Revi-PB-26.04.apbx"]:
                src_extra = None
                for cand in [os.path.join(base, extra_file), os.path.join(exe_dir, extra_file), os.path.join(os.getcwd(), extra_file), os.path.join(exe_dir, "Otimizador_Portable", extra_file)]:
                    if os.path.exists(cand):
                        src_extra = cand
                        break
                if src_extra:
                    dest_extra = os.path.join(INSTALL_DIR, extra_file)
                    try:
                        shutil.copy2(src_extra, dest_extra)
                    except Exception as e:
                        print(f"Erro ao copiar extra {extra_file}: {e}")
            time.sleep(0.2)

            # ── Criar desinstalador ──────────────────────────────────────
            self.after(0, lambda: self.setstatus("🗑️ Criando desinstalador...", 0.40))
            uninstall_script = os.path.join(INSTALL_DIR, "Desinstalar.bat")
            uninstall_reg_key = r"HKCU\Software\Microsoft\Windows\CurrentVersion\Uninstall\BernalOtimizacoes"
            desktop_lnk   = os.path.join(DESKTOP_PATH, f"{APP_NAME}.lnk")
            sm_dir        = os.path.join(os.environ.get('APPDATA', ''),
                                         r'Microsoft\Windows\Start Menu\Programs\Bernal Otimizacoes')
            sm_lnk        = os.path.join(sm_dir, f"{APP_NAME}.lnk")

            bat_lines = [
                "@echo off",
                'reg delete "HKCU\\Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\BernalOtimizacoes" /f >nul 2>&1',
                'echo Set objShell = CreateObject^("Wscript.Shell"^) > "%temp%\\msg.vbs"',
                'echo intAnswer = objShell.Popup^("Tem certeza que deseja desinstalar o melhor otimizador do mercado? Seu PC vai voltar a ficar lento e com menos FPS...", 0, "Atenção!", 4 + 48^) >> "%temp%\\msg.vbs"',
                'echo Wscript.Quit intAnswer >> "%temp%\\msg.vbs"',
                'cscript //nologo "%temp%\\msg.vbs"',
                'if errorlevel 7 exit /b',
                '',
                'echo @echo off > "%temp%\\run_uninst.bat"',
                'echo cd /d "%%TEMP%%" >> "%temp%\\run_uninst.bat"',
                'echo timeout /t 2 /nobreak ^>nul >> "%temp%\\run_uninst.bat"',
                'echo color 0b >> "%temp%\\run_uninst.bat"',
                'echo echo ========================================== >> "%temp%\\run_uninst.bat"',
                'echo echo DESINSTALANDO BERNAL OTIMIZACOES PRO... >> "%temp%\\run_uninst.bat"',
                'echo echo ========================================== >> "%temp%\\run_uninst.bat"',
                'echo echo. >> "%temp%\\run_uninst.bat"',
                'echo echo [1/5] Revertendo Plano de Energia para Equilibrado... >> "%temp%\\run_uninst.bat"',
                'echo powercfg -setactive 381b4222-f694-41f0-9685-ff5bb260df2e ^>nul 2^>^&1 >> "%temp%\\run_uninst.bat"',
                'echo echo [2/5] Restaurando Efeitos Visuais do Windows... >> "%temp%\\run_uninst.bat"',
                'echo reg add "HKCU\\Software\\Microsoft\\Windows\\CurrentVersion\\Explorer\\VisualEffects" /v "VisualFXSetting" /t REG_DWORD /d 0 /f ^>nul 2^>^&1 >> "%temp%\\run_uninst.bat"',
                'echo echo [3/5] Reativando Xbox Game DVR e Telemetria... >> "%temp%\\run_uninst.bat"',
                'echo reg add "HKCU\\System\\GameConfigStore" /v "GameDVR_Enabled" /t REG_DWORD /d 1 /f ^>nul 2^>^&1 >> "%temp%\\run_uninst.bat"',
                'echo echo [4/5] Restaurando Servicos Desativados (Spooler, SysMain)... >> "%temp%\\run_uninst.bat"',
                'echo sc config Spooler start= auto ^>nul 2^>^&1 >> "%temp%\\run_uninst.bat"',
                'echo sc start Spooler ^>nul 2^>^&1 >> "%temp%\\run_uninst.bat"',
                'echo sc config SysMain start= auto ^>nul 2^>^&1 >> "%temp%\\run_uninst.bat"',
                'echo sc start SysMain ^>nul 2^>^&1 >> "%temp%\\run_uninst.bat"',
                'echo echo [5/5] Reativando Windows Defender... >> "%temp%\\run_uninst.bat"',
                'echo powershell -Command "Set-MpPreference -DisableRealtimeMonitoring $false" ^>nul 2^>^&1 >> "%temp%\\run_uninst.bat"',
                'echo reg delete "HKLM\\SOFTWARE\\Policies\\Microsoft\\Windows Defender" /v DisableAntiSpyware /f ^>nul 2^>^&1 >> "%temp%\\run_uninst.bat"',
                'echo echo. >> "%temp%\\run_uninst.bat"',
                'echo echo Excluindo arquivos e pastas do aplicativo... >> "%temp%\\run_uninst.bat"',
                f'echo rmdir /s /q "{INSTALL_DIR}" >> "%temp%\\run_uninst.bat"',
                f'echo del /f /q "{desktop_lnk}" >> "%temp%\\run_uninst.bat"',
                f'echo rmdir /s /q "{sm_dir}" >> "%temp%\\run_uninst.bat"',
                'echo reg delete "HKCU\\Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\BernalOtimizacoes" /f >> "%temp%\\run_uninst.bat"',
                'echo echo INICIANDO RESTAURACAO DO SISTEMA (O PC SERA REINICIADO AGORA)... >> "%temp%\\run_uninst.bat"',
                'echo echo x = msgbox^("Desinstalacao concluida! O PC sera reiniciado agora para restaurar o backup de seguranca."^, 48, "Bernal Otimizacoes"^) ^> "%%temp%%\\done.vbs" >> "%temp%\\run_uninst.bat"',
                'echo wscript "%%temp%%\\done.vbs" >> "%temp%\\run_uninst.bat"',
                'echo powershell -Command "Restore-Computer -RestorePoint (Get-ComputerRestorePoint | Where-Object Description -eq \'Instalacao_BernalOtimizacoes\')[-1].SequenceNumber" >> "%temp%\\run_uninst.bat"',
                'echo del "%%~f0" >> "%temp%\\run_uninst.bat"',
                '',
                'powershell -Command "Start-Process \'%temp%\\run_uninst.bat\' -Verb RunAs"',
                'exit'
            ]
            with open(uninstall_script, "w", encoding="utf-8") as f:
                f.write("\r\n".join(bat_lines))
            time.sleep(0.2)

            # ── PERGUNTA DE BACKUP E SYSTEM RESTORE (TELA PISCANDO) ──────────────────────
            import customtkinter as ctk
            import threading
            
            # Precisamos pausar o instalador até a pessoa clicar em "Sim" ou "Não"
            user_agreed = [False]
            dialog_closed = [False]
            
            def show_warning_dialog():
                dialog = ctk.CTkToplevel(self)
                dialog.title("⚠️ AVISO DE SEGURANÇA ⚠️")
                dialog.geometry("550x300")
                dialog.attributes('-topmost', 'true')
                dialog.configure(fg_color="#300000") # Dark red background
                
                # Make it borderless and center
                dialog.overrideredirect(True)
                dialog.update_idletasks()
                x = (dialog.winfo_screenwidth() - 550) // 2
                y = (dialog.winfo_screenheight() - 300) // 2
                dialog.geometry(f"+{x}+{y}")
                
                # Flashing border effect
                def flash_border():
                    if not dialog.winfo_exists(): return
                    current_color = dialog.cget("fg_color")
                    next_color = "#FF0000" if current_color == "#300000" else "#300000"
                    dialog.configure(fg_color=next_color)
                    dialog.after(500, flash_border)
                
                flash_border()
                
                inner_frame = ctk.CTkFrame(dialog, fg_color="#1a1a1a", corner_radius=0)
                inner_frame.pack(fill="both", expand=True, padx=4, pady=4)
                
                ctk.CTkLabel(inner_frame, text="⚠️ ATENÇÃO - BACKUP AUTOMÁTICO ⚠️", font=ctk.CTkFont(size=20, weight="bold"), text_color="#FF3333").pack(pady=(20, 10))
                
                msg = ("O Bernal Otimizações PRO criará um Ponto de Restauração de Segurança antes de instalar.\n\n"
                       "Se pelo acaso você desinstalar o app no futuro, será feito um backup (Restauração do Sistema) "
                       "automaticamente após a desinstalação, e seu PC será reiniciado.\n\n"
                       "Você concorda com estes termos de segurança?")
                
                ctk.CTkLabel(inner_frame, text=msg, font=ctk.CTkFont(size=14, weight="bold"), text_color="white", wraplength=500, justify="center").pack(pady=10)
                
                btn_frame = ctk.CTkFrame(inner_frame, fg_color="transparent")
                btn_frame.pack(pady=20)
                
                def on_yes():
                    user_agreed[0] = True
                    dialog_closed[0] = True
                    dialog.destroy()
                    
                def on_no():
                    user_agreed[0] = False
                    dialog_closed[0] = True
                    dialog.destroy()
                    
                ctk.CTkButton(btn_frame, text="SIM, EU CONCORDO", fg_color="#27AE60", hover_color="#1E8449", font=ctk.CTkFont(weight="bold"), command=on_yes).pack(side="left", padx=10)
                ctk.CTkButton(btn_frame, text="NÃO, CANCELAR", fg_color="#C0392B", hover_color="#922B21", font=ctk.CTkFont(weight="bold"), command=on_no).pack(side="right", padx=10)
                
                self.wait_window(dialog)
            
            self.after(0, show_warning_dialog)
            
            # Wait loop in thread so it doesn't freeze the GUI
            while not dialog_closed[0]:
                time.sleep(0.1)
                
            if not user_agreed[0]:
                self.after(0, lambda: self.setstatus("❌ Instalação cancelada pelo usuário.", 0.0))
                self.after(0, lambda: self.btn_action.configure(state="normal"))
                self.after(0, lambda: self.btn_cancel.configure(state="normal"))
                return
                
            # ── Criar Ponto de Restauração Oculto ───────────────────────
            self.after(0, lambda: self.setstatus("🛡️ Criando Backup de Segurança... (Isso pode demorar alguns minutos!)", 0.30))
            
            # Força o desbloqueio do limite de 1 backup por dia do Windows
            subprocess.run('reg add "HKLM\\Software\\Microsoft\\Windows NT\\CurrentVersion\\SystemRestore" /v "SystemRestorePointCreationFrequency" /t REG_DWORD /d 0 /f', shell=True, creationflags=subprocess.CREATE_NO_WINDOW)
            
            # Habilita e cria o ponto de restauração
            ps_cmd = 'powershell -Command "Enable-ComputerRestore -Drive \'C:\\\'; Checkpoint-Computer -Description \'Instalacao_BernalOtimizacoes\' -RestorePointType \'MODIFY_SETTINGS\'"'
            
            # Wait for the backup to finish!
            subprocess.run(ps_cmd, shell=True, creationflags=subprocess.CREATE_NO_WINDOW)

            # ── Atalho na Área de Trabalho ───────────────────────────────
            self.after(0, lambda: self.setstatus("🖥️ Criando atalho na Área de Trabalho...", 0.55))
            create_shortcut(dest_app, desktop_lnk)
            time.sleep(0.2)

            # ── Menu Iniciar ─────────────────────────────────────────────
            self.after(0, lambda: self.setstatus("📌 Adicionando ao Menu Iniciar...", 0.70))
            os.makedirs(sm_dir, exist_ok=True)
            create_shortcut(dest_app, sm_lnk)
            # Também adiciona na raiz de Programas para exibir diretamente na Área de Início
            sm_root_dir = os.path.join(os.environ.get('APPDATA', ''), r'Microsoft\Windows\Start Menu\Programs')
            if os.path.exists(sm_root_dir):
                create_shortcut(dest_app, os.path.join(sm_root_dir, f"{APP_NAME}.lnk"))
            time.sleep(0.2)

            # ── Registro Windows (Adicionar/Remover Programas) ───────────
            self.after(0, lambda: self.setstatus("📝 Registrando no Windows...", 0.85))
            reg_cmds = [
                f'reg add "HKCU\\Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\BernalOtimizacoes" /v "DisplayName" /t REG_SZ /d "{APP_NAME}" /f',
                f'reg add "HKCU\\Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\BernalOtimizacoes" /v "DisplayVersion" /t REG_SZ /d "9.2" /f',
                f'reg add "HKCU\\Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\BernalOtimizacoes" /v "Publisher" /t REG_SZ /d "Bernal Otimizacoes" /f',
                f'reg add "HKCU\\Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\BernalOtimizacoes" /v "InstallLocation" /t REG_SZ /d "{INSTALL_DIR}" /f',
                f'reg add "HKCU\\Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\BernalOtimizacoes" /v "UninstallString" /t REG_SZ /d "\\"{uninstall_script}\\"" /f',
                f'reg add "HKCU\\Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\BernalOtimizacoes" /v "DisplayIcon" /t REG_SZ /d "\\"{dest_app}\\"" /f',
                f'reg add "HKCU\\Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\BernalOtimizacoes" /v "NoModify" /t REG_DWORD /d 1 /f',
                f'reg add "HKCU\\Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\BernalOtimizacoes" /v "NoRepair" /t REG_DWORD /d 1 /f',
            ]
            for cmd in reg_cmds:
                subprocess.run(cmd, shell=True, creationflags=subprocess.CREATE_NO_WINDOW)
            time.sleep(0.2)

            self.after(0, lambda: self.setstatus("✅ Instalação concluída!", 1.0))
            time.sleep(0.4)
            self.after(0, self.show_done)

        except Exception as e:
            err_msg = str(e)
            print("INSTALL ERROR:", err_msg)
            self.after(0, lambda err=err_msg: self.setstatus(f"❌ Erro: {err}", 0))

    def show_done(self):
        for w in self.winfo_children():
            w.destroy()

        title_text = "Atualização Concluída com Sucesso!" if getattr(self, 'is_update', False) else "Instalação Concluída com Sucesso!"

        ctk.CTkLabel(self, text="🎉",
                     font=ctk.CTkFont(size=52)).pack(pady=(30, 0))
        ctk.CTkLabel(self, text=title_text,
                     font=ctk.CTkFont(size=20, weight="bold"),
                     text_color="#00d4ff").pack(pady=8)
        ctk.CTkLabel(self,
                     text=f"✅ Atalho criado na Área de Trabalho\n✅ Adicionado em Adicionar/Remover Programas\n✅ Desinstalador criado em:\n{INSTALL_DIR}",
                     font=ctk.CTkFont(size=11), text_color="#aaa",
                     justify="center").pack(pady=6)

        btns = ctk.CTkFrame(self, fg_color="transparent")
        btns.pack(pady=16)
        ctk.CTkButton(btns, text="🚀 Abrir Agora",
                      fg_color="#00b4d8", hover_color="#0077b6",
                      font=ctk.CTkFont(size=14, weight="bold"),
                      width=150, height=40,
                      command=self.launch_app).pack(side="left", padx=10)
        ctk.CTkButton(btns, text="Fechar",
                      fg_color="#21262d", hover_color="#30363d",
                      width=100, height=40,
                      command=self.destroy).pack(side="left", padx=10)

    def launch_app(self):
        dest_app = os.path.join(INSTALL_DIR, EXE_NAME)
        subprocess.Popen([dest_app])
        self.destroy()

if __name__ == "__main__":
    app = InstallerApp()
    app.mainloop()
