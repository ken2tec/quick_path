import os
import sys
import subprocess
import configparser
import msvcrt
import re
import time
import socket
import ctypes
from ctypes import wintypes

import sqlite3

def enable_vt_mode():
    # VT100 モードの有効化を試みる (Windows 10以降)
    kernel32 = ctypes.windll.kernel32
    hOut = kernel32.GetStdHandle(-11)
    if hOut == -1: return False
    mode = wintypes.DWORD()
    if not kernel32.GetConsoleMode(hOut, ctypes.byref(mode)): return False
    mode.value |= 0x0004
    return kernel32.SetConsoleMode(hOut, mode) != 0

VT_SUPPORTED = enable_vt_mode()

def print_colored(text, is_highlight=False):
    # ハイライト表示（青背景・白文字）を行う
    if VT_SUPPORTED:
        if is_highlight:
            print(f"\033[44m\033[37m > {text.ljust(65)} \033[0m")
        else:
            print(f"   {text.ljust(65)}")
    else:
        # 古い Windows (Server 2012 R2等) 用のフォールバック
        kernel32 = ctypes.windll.kernel32
        hOut = kernel32.GetStdHandle(-11)
        if is_highlight:
            # 0x1F: 背景青(0x10) + 文字白(0x0F)
            kernel32.SetConsoleTextAttribute(hOut, 0x1F)
            print(f" > {text.ljust(65)}")
            kernel32.SetConsoleTextAttribute(hOut, 0x07) # 元に戻す (白文字・黒背景)
        else:
            print(f"   {text.ljust(65)}")

def get_config_path():
    if getattr(sys, 'frozen', False):
        full_path = sys.executable
    else:
        full_path = os.path.abspath(__file__)
    pg_name = os.path.basename(full_path).split('.')[0]
    return os.path.join(os.path.dirname(full_path), f"{pg_name}.ini")

def get_db_path():
    # exe と同一フォルダの sqlite db パス
    dir_path = os.path.dirname(os.path.abspath(sys.executable if getattr(sys, 'frozen', False) else __file__))
    return os.path.join(dir_path, "quick_path.db")

def init_db():
    db_path = get_db_path()
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS sync_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            executed_at TEXT,
            label TEXT,
            command TEXT,
            output TEXT,
            hostname TEXT,
            cwd TEXT
        )
    ''')
    # 既存テーブルがある場合のカラム追加 (移行対応)
    try:
        cursor.execute("ALTER TABLE sync_history ADD COLUMN hostname TEXT")
    except: pass
    try:
        cursor.execute("ALTER TABLE sync_history ADD COLUMN cwd TEXT")
    except: pass
    
    conn.commit()
    conn.close()

def load_config():
    ini_path = get_config_path()
    config = configparser.ConfigParser()
    config.optionxform = str # キーの大文字小文字を保持
    if not os.path.exists(ini_path):
        print(f"Error: Config not found: {ini_path}")
        return [], {}, {}
    try:
        config.read(ini_path, encoding='utf-8-sig')
        # パスを OS 標準形式に正規化 (\ と / の混在を解消)
        paths = [(k, os.path.normpath(v)) for k, v in config['Paths'].items()]
        
        # セクションごとに辞書を作成
        commands = {}
        if 'Commands' in config:
            for key, val in config['Commands'].items():
                label, cmd = val.split(',', 1) if ',' in val else (val, val)
                commands[key] = (label.strip(), cmd.strip())
        
        sync_commands = {}
        if 'SyncCommands' in config:
            for key, val in config['SyncCommands'].items():
                label, cmd = val.split(',', 1) if ',' in val else (val, val)
                sync_commands[key] = (label.strip(), cmd.strip())
                
        return paths, commands, sync_commands
    except Exception as e:
        print(f"Error loading config: {e}")
        return [], {}, {}

def resolve_placeholders(raw_cmd, path_val, label):
    # 1. {path} の置換 (既存仕様の維持：大文字小文字無視)
    final_cmd = re.compile(re.escape('{path}'), re.IGNORECASE).sub(lambda m: f'"{path_val}"', raw_cmd)
    
    # 2. ユーザー定義パラメタ {{name}} の抽出
    # 二重中括弧 {{ }} で囲まれた非中括弧文字列を対象とする
    placeholders = re.findall(r'\{\{([^{}]+)\}\}', raw_cmd)
    
    # 重複排除
    unique_params = []
    for p in placeholders:
        if p not in unique_params:
            unique_params.append(p)
            
    if unique_params:
        print(f"\n--- パラメータ入力: {label} ---")
        try:
            for p in unique_params:
                # パラメタ名を表示して入力を促す
                val = input(f" {p} > ").strip()
                # 該当する全ての {{p}} を入力値で置換 (大文字小文字無視)
                pattern = re.compile(re.escape(f'{{{{{p}}}}}'), re.IGNORECASE)
                final_cmd = pattern.sub(lambda m: val, final_cmd)
        except KeyboardInterrupt:
            print("\n 中断されました。")
            return None
        print("-" * 30)
    
    return final_cmd

def run_action(action, path, commands, sync_commands):
    try:
        # パスを正規化
        path = os.path.normpath(path)
        # アクション実行時の基準ディレクトリ (ファイルなら親、ディレクトリならそのまま)
        dir_path = os.path.dirname(path) if os.path.isfile(path) else path
        
        if action == 'e':
            os.startfile(dir_path)
        elif action == 't':
            # start を介さず直接 wt コマンドを叩く（GUIアプリならすぐに制御が戻る）
            # creationflags と DEVNULL 指定により、一瞬の黒窓すら出ないように徹底
            subprocess.run(f'wt -d "{dir_path}"', shell=True, creationflags=subprocess.CREATE_NO_WINDOW, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        elif action == 'c':
            subprocess.run(['powershell', '-Command', f'Set-Clipboard -Value "{path}"'], shell=True, creationflags=subprocess.CREATE_NO_WINDOW)
            
        elif action in commands:
            # [Commands]セクション（非同期起動：GUIアプリ等が即座に制御を返すことを想定）
            label, raw_cmd = commands[action]
            final_cmd = resolve_placeholders(raw_cmd, path, label)
            if final_cmd is None: return False
            
            # start コマンドを介さず、直接 subprocess.run でアプリを非表示(CREATE_NO_WINDOW)かつバックグラウンド的に起動
            subprocess.run(final_cmd, shell=True, cwd=dir_path, creationflags=subprocess.CREATE_NO_WINDOW, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            
        elif action in sync_commands:
            # [SyncCommands]セクション（同期実行 & クリップボードコピー）
            label, raw_cmd = sync_commands[action]
            final_cmd = resolve_placeholders(raw_cmd, path, label)
            if final_cmd is None: return False
            
            print(f"\nExecuting Sync: {final_cmd}")
            # 同期実行中も余計な窓が出ないよう設定
            res = subprocess.run(final_cmd, shell=True, capture_output=True, text=True, encoding='cp932', cwd=dir_path, stdin=subprocess.DEVNULL, creationflags=subprocess.CREATE_NO_WINDOW)
            output = (res.stdout or "") + (res.stderr or "")
            subprocess.run(['powershell', '-Command', '$Input | Out-String | Set-Clipboard'], input=output, text=True, shell=True, creationflags=subprocess.CREATE_NO_WINDOW)
            
            # DB への保存
            try:
                conn = sqlite3.connect(get_db_path())
                cursor = conn.cursor()
                hostname = socket.gethostname()
                cursor.execute(
                    "INSERT INTO sync_history (executed_at, label, command, output, hostname, cwd) VALUES (?, ?, ?, ?, ?, ?)",
                    (time.strftime("%Y-%m-%d %H:%M:%S"), label, final_cmd, output, hostname, dir_path)
                )
                conn.commit()
                conn.close()
            except Exception as db_e:
                print(f"DB Logging Error: {db_e}")

            print("Output copied to clipboard and logged to DB.")
            time.sleep(1)
            
        return True
    except Exception as e:
        print(f"\nExecution Error: {e}")
        return False

def get_dir_items(dir_path):
    try:
        items = []
        # ディレクトリ内の項目を取得して「名前, フルパス」のリストにする
        for entry in os.scandir(dir_path):
            items.append((f"{'[' if entry.is_dir() else ' '} {entry.name}", entry.path))
        # 名前順にソート (ディレクトリを優先)
        return sorted(items, key=lambda x: (not x[0].startswith('['), x[0].lower()))
    except Exception as e:
        print(f"Error: {e}")
        return []

def show_history():
    # 履歴を表示して選択、コピーする
    try:
        conn = sqlite3.connect(get_db_path())
        cursor = conn.cursor()
        cursor.execute("SELECT id, executed_at, label, command, output, hostname, cwd FROM sync_history ORDER BY id DESC LIMIT 100")
        rows = cursor.fetchall()
        conn.close()
    except Exception as e:
        print(f"DB Error: {e}")
        time.sleep(2)
        return

    if not rows:
        print("\nNo history found.")
        time.sleep(1)
        return

    h_idx = 0
    while True:
        os.system('cls')
        print("=" * 75)
        print(" SYNC COMMAND HISTORY (Up/Down: Select, [c]: Copy, [f]: File, [q]: Back)")
        print("=" * 75)
        
        for i, (hid, ts, label, cmd, out, host, cwd) in enumerate(rows[:25]): # 直近25件表示
            prefix = f"[{host}]"
            line_text = f"{prefix.ljust(12)} [{ts}] {label.ljust(15)} | {cmd[:25]}..."
            print_colored(line_text, is_highlight=(i == h_idx))
        
        print("-" * 75)
        if h_idx < len(rows):
            _, ts, label, cmd, out, host, cwd = rows[h_idx]
            print(f" Host: {host}")
            print(f" Dir : {cwd}")
            print(f" Cmd : {cmd}")
        
        key = msvcrt.getch()
        if key in (b'\x00', b'\xe0'):
            sub_key = msvcrt.getch()
            if sub_key == b'H': h_idx = (h_idx - 1) % len(rows)
            elif sub_key == b'P': h_idx = (h_idx + 1) % len(rows)
        else:
            try: char = key.decode('utf-8').lower()
            except: continue
            if char == 'q' or char == '\x1b': # q or ESC
                break
            elif char == 'c': # Copy to clipboard
                output = rows[h_idx][4]
                subprocess.run(['powershell', '-Command', '$Input | Out-String | Set-Clipboard'], input=output, text=True, shell=True, creationflags=subprocess.CREATE_NO_WINDOW)
                print("\n[CLIPBOARD] Selected output copied.")
                time.sleep(1)
                break
            elif char == 'f': # Output to file
                output = rows[h_idx][4]
                print(f"\n--- Output to File (ANSI Encoding) ---")
                filename = input(" Enter filename (e.g. log.txt): ").strip()
                if not filename:
                    print(" Cancelled.")
                    time.sleep(1)
                    continue
                
                # 実行ファイルと同一フォルダに保存
                dir_path = os.path.dirname(os.path.abspath(sys.executable if getattr(sys, 'frozen', False) else __file__))
                out_path = os.path.join(dir_path, filename)
                
                try:
                    with open(out_path, 'w', encoding='cp932', errors='replace') as f_out:
                        f_out.write(output)
                    print(f" [SUCCESS] Saved to: {filename}")
                except Exception as e:
                    print(f" [ERROR] Failed to save: {e}")
                
                time.sleep(1)
                break

def main():
    os.system('') 
    enable_vt_mode() # ANSI カラーを確実に有効化
    init_db() # DB初期化
    config_paths, commands, sync_commands = load_config()
    if not config_paths:
        input("\nPress Enter to exit..."); return

    current_paths = config_paths
    history = [] # 階層移動の履歴 (リスト, 選択インデックス)
    idx = 0
    start_idx = 0

    while True:
        os.system('cls')
        curr_name, curr_path = current_paths[idx]

        # 表示対象の状態（ディレクトリかどうか）を確認
        is_dir = os.path.isdir(curr_path) or curr_name == "[ .. ]"
        enter_label = "Enter" if is_dir else "Run"
        
        print("=" * 75)
        menu_line = f"[Enter]:{enter_label} [e]:Explore [t]:Terminal [c]:Copy"
        for k, (label, _) in commands.items():
            menu_line += f" [{k}]:{label}"
        for k, (label, _) in sync_commands.items():
            menu_line += f" [{k}]:{label}"
        print(f" {menu_line} [h]:History [q]:Quit")
        print("=" * 75)
        
        # スクロール窓の制御: idx が表示範囲外に出たら窓をずらす
        window_size = 25
        if idx < start_idx:
            start_idx = idx
        elif idx >= start_idx + window_size:
            start_idx = idx - window_size + 1

        # current_paths を表示 (スライスして表示)
        visible_items = current_paths[start_idx : start_idx + window_size]
        for i, (name, _) in enumerate(visible_items):
            current_i = start_idx + i
            print_colored(name, is_highlight=(current_i == idx))
        
        # 残り行の埋め合わせ (リストが短い場合にUIを維持)
        if len(visible_items) < window_size:
            for _ in range(window_size - len(visible_items)):
                print(" " * 75)
        
        print("-" * 75)
        print(f" Target: {curr_name}")
        print(f" Path  : {curr_path}")

        key = msvcrt.getch()
        if key in (b'\x00', b'\xe0'):
            sub_key = msvcrt.getch()
            if sub_key == b'H': idx = (idx - 1) % len(current_paths)
            elif sub_key == b'P': idx = (idx + 1) % len(current_paths)
        else:
            try: char = key.decode('utf-8').lower()
            except: continue
            
            if char == 'q':
                break
            elif char == 'h':
                show_history()
            elif char in ('e', 't', 'c') or char in commands or char in sync_commands:
                run_action(char, curr_path, commands, sync_commands)
            elif char == '\r': # Enter
                if curr_name == "[ .. ]":
                    # 履歴から戻る
                    current_paths, idx = history.pop()
                    start_idx = 0 # スクロールを戻す
                elif os.path.isdir(curr_path):
                    # ディレクトリなら中に入る
                    items = get_dir_items(curr_path)
                    if items:
                        history.append((current_paths, idx))
                        current_paths = [("[ .. ]", os.path.dirname(curr_path))] + items
                        idx = 0
                        start_idx = 0 # スクールのリセット
                else:
                    # ファイルなら Explore (既存挙動)
                    run_action('e', curr_path, commands, sync_commands)

if __name__ == "__main__":
    main()