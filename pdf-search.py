import os
import json
from pathlib import Path
import sqlite3
import time
import tkinter as tk
from tkinter import messagebox, ttk, filedialog
import threading
from queue import Queue
from typing import List, Dict, Optional
import re
import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

class Settings:
    def __init__(self):
        # アプリケーションと同じディレクトリにlast_config_path.jsonというファイルで
        # 最後に使用した設定ファイルのパスを保存
        self.last_config_path_file = Path(__file__).parent / "last_config_path.json"
        
        # 最後に使用した設定ファイルのパスを読み込む
        self.settings_file = self._get_last_settings_path()
        
        # 設定ファイルから設定内容を読み込む
        self.settings = self._load_settings()

    def _get_last_settings_path(self) -> Path:
        """最後に使用した設定ファイルのパスを取得"""
        if self.last_config_path_file.exists():
            try:
                with open(self.last_config_path_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    last_path = data.get("last_settings_path")
                    if last_path and Path(last_path).exists():
                        return Path(last_path)
            except Exception as e:
                print(f"前回の設定ファイルパスの読み込みに失敗: {e}")
        
        # デフォルトのパス（アプリケーションと同じディレクトリ）
        return Path(__file__).parent / "settings.json"
    
    def _save_last_settings_path(self):
        """使用した設定ファイルのパスを保存"""
        try:
            with open(self.last_config_path_file, 'w', encoding='utf-8') as f:
                json.dump({"last_settings_path": str(self.settings_file)}, f, ensure_ascii=False, indent=4)
        except Exception as e:
            print(f"設定ファイルパスの保存に失敗: {e}")

    def load_settings_from_file(self, file_path: str) -> bool:
        """指定されたファイルから設定を読み込む"""
        file_path = Path(file_path)
        if file_path.exists():
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    self.settings = json.load(f)
                self.settings_file = file_path
                self._save_last_settings_path()  # 読み込んだパスを記録
                return True
            except Exception as e:
                print(f"設定ファイルの読み込みに失敗: {e}")
                return False
        return False

    def save_settings_to_file(self, file_path: str) -> bool:
        """現在の設定を指定されたファイルに保存"""
        try:
            file_path = Path(file_path)
            # 設定ファイルのディレクトリが存在しない場合は作成
            os.makedirs(file_path.parent, exist_ok=True)
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(self.settings, f, ensure_ascii=False, indent=4)
            
            # 保存したパスを現在の設定ファイルとして記録
            self.settings_file = file_path
            self._save_last_settings_path()
            return True
        except Exception as e:
            print(f"設定ファイルの保存に失敗: {e}")
            return False

    def _load_settings(self) -> Dict:
        """設定ファイルから設定を読み込む"""
        if self.settings_file.exists():
            try:
                with open(self.settings_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                print(f"設定ファイルの読み込みに失敗: {e}")
                return self._get_default_settings()
        return self._get_default_settings()

    def _get_default_settings(self) -> Dict:
        """デフォルト設定を返す"""
        return {
            "pdf_folder": "",
            "db_folder": "",
            "exclude_patterns": ['除外したいテキスト1…', '除外したいテキスト2…'],
            "include_subfolders_index": False
        }

    def save_settings(self):
        """現在の設定を現在のファイルパスに保存"""
        try:
            # 設定ファイルのディレクトリが存在しない場合は作成
            os.makedirs(self.settings_file.parent, exist_ok=True)
            with open(self.settings_file, 'w', encoding='utf-8') as f:
                json.dump(self.settings, f, ensure_ascii=False, indent=4)
            # 保存したパスを記録
            self._save_last_settings_path()
        except Exception as e:
            print(f"設定ファイルの保存に失敗: {e}")

    def get_setting(self, key: str):
        """設定値を取得"""
        return self.settings.get(key)

    def update_setting(self, key: str, value):
        """設定値を更新"""
        self.settings[key] = value
        self.save_settings()
        
class ConfigDialog(tk.Toplevel):
    def __init__(self, parent, settings: Settings, callback=None):
        super().__init__(parent)
        self.settings = settings
        self.callback = callback
        self.title("フォルダー設定")
        self.geometry("600x650")  # ウィンドウの高さを増やす
        self.resizable(True, True)
        
        # モーダルダイアログとして表示
        self.transient(parent)
        self.grab_set()
        
        self._create_widgets()
        
        # 画面中央に表示
        self.update_idletasks()
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        x = (screen_width - self.winfo_width()) // 2
        y = (screen_height - self.winfo_height()) // 2
        self.geometry(f"+{x}+{y}")
        
        # 設定が空の場合でも、ダイアログを閉じられるようにする（初回起動時に設定画面を表示しない）
        self.protocol("WM_DELETE_WINDOW", self.destroy)

    def _create_widgets(self):
        main_frame = ttk.Frame(self, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # PDFフォルダー設定
        pdf_frame = ttk.LabelFrame(main_frame, text="PDF検索フォルダー", padding="5")
        pdf_frame.pack(fill=tk.X, pady=5)

        self.pdf_path_var = tk.StringVar(value=self.settings.get_setting("pdf_folder"))
        pdf_entry = ttk.Entry(pdf_frame, textvariable=self.pdf_path_var)
        pdf_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))

        ttk.Button(pdf_frame, text="参照", command=self._browse_pdf_folder).pack(side=tk.RIGHT)

        # データベースフォルダー設定
        db_frame = ttk.LabelFrame(main_frame, text="インデックスDBフォルダー", padding="5")
        db_frame.pack(fill=tk.X, pady=5)

        self.db_path_var = tk.StringVar(value=self.settings.get_setting("db_folder"))
        db_entry = ttk.Entry(db_frame, textvariable=self.db_path_var)
        db_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))

        ttk.Button(db_frame, text="参照", command=self._browse_db_folder).pack(side=tk.RIGHT)

        # 除外パターン設定
        exclude_frame = ttk.LabelFrame(main_frame, text="検索除外テキスト（ファイル名）", padding="5")
        exclude_frame.pack(fill=tk.BOTH, expand=True, pady=5)

        # リストボックスと入力部分を含むフレーム
        pattern_container = ttk.Frame(exclude_frame)
        pattern_container.pack(fill=tk.BOTH, expand=True, pady=5)

        # リストボックスとスクロールバー
        self.exclude_listbox = tk.Listbox(pattern_container, height=6)
        self.exclude_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        scrollbar = ttk.Scrollbar(pattern_container, orient=tk.VERTICAL, command=self.exclude_listbox.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.exclude_listbox.configure(yscrollcommand=scrollbar.set)

        # 現在の除外パターンを表示
        for pattern in self.settings.get_setting("exclude_patterns"):
            self.exclude_listbox.insert(tk.END, pattern)

        # パターン編集用のフレーム
        edit_frame = ttk.Frame(exclude_frame)
        edit_frame.pack(fill=tk.X, pady=5)

        # 新規パターン入力欄
        self.new_pattern_var = tk.StringVar()
        ttk.Entry(edit_frame, textvariable=self.new_pattern_var).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))

        # ボタン
        ttk.Button(edit_frame, text="追加", command=self._add_pattern).pack(side=tk.LEFT, padx=2)
        ttk.Button(edit_frame, text="削除", command=self._remove_pattern).pack(side=tk.LEFT, padx=2)

        # サブフォルダー検索設定（インデックス作成用）のみ残す
        subfolder_frame_index = ttk.Frame(main_frame)
        subfolder_frame_index.pack(fill=tk.X, pady=5)

        self.include_subfolders_index_var = tk.BooleanVar(
            value=self.settings.get_setting("include_subfolders_index")
        )
        ttk.Checkbutton(
            subfolder_frame_index,
            text="サブフォルダーにもインデックスを作成する",
            variable=self.include_subfolders_index_var
        ).pack(side=tk.LEFT)

        # 説明テキスト
        help_text = """
・PDFフォルダー: 検索対象のPDFファイルが格納されているフォルダーを選択してください。
・インデックスDBフォルダー: 検索用のインデックスファイルを保存するフォルダーを選択してください。
・検索除外テキスト: ファイル名にこれらのテキストが含まれる場合、検索対象から除外されます。
※ 共有フォルダーのパスは、\\\\サーバー名\\フォルダー名 の形式で入力することもできます。
"""
        help_label = ttk.Label(main_frame, text=help_text, wraplength=550, justify=tk.LEFT)
        help_label.pack(fill=tk.X, pady=10, side=tk.BOTTOM)  # side=tk.BOTTOMを追加

        # ボタンフレーム
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=10)

        # 保存ボタンとキャンセルボタン
        ttk.Button(button_frame, text="保存", command=self._save_settings).pack(side=tk.RIGHT, padx=5)
        ttk.Button(button_frame, text="キャンセル", command=self.destroy).pack(side=tk.RIGHT)
        
        # 保存先指定ボタンを追加
        ttk.Button(button_frame, text="名前を付けて保存", command=self._save_settings_as).pack(side=tk.LEFT, padx=5)
            
    def _browse_pdf_folder(self):
        folder = filedialog.askdirectory(initialdir=self.pdf_path_var.get())
        if folder:
            self.pdf_path_var.set(folder)

    def _browse_db_folder(self):
        folder = filedialog.askdirectory(initialdir=self.db_path_var.get())
        if folder:
            self.db_path_var.set(folder)

    def _add_pattern(self):
        """除外パターンを追加"""
        pattern = self.new_pattern_var.get().strip()
        if pattern:
            self.exclude_listbox.insert(tk.END, pattern)
            self.new_pattern_var.set("")

    def _remove_pattern(self):
        """選択された除外パターンを削除"""
        selection = self.exclude_listbox.curselection()
        if selection:
            self.exclude_listbox.delete(selection)

    def _save_settings_as(self):
        """設定を別名で保存"""
        file_path = filedialog.asksaveasfilename(
            title="設定ファイルを保存",
            defaultextension=".json",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
            initialdir=os.path.dirname(str(self.settings.settings_file))
        )
        
        if file_path:
            # 現在の設定内容を更新
            self._update_settings_data()
            # 指定されたパスに保存
            if self.settings.save_settings_to_file(file_path):
                messagebox.showinfo("成功", f"設定を保存しました: {file_path}")
                
                if self.callback:
                    self.callback()
                
                self.destroy()
            else:
                messagebox.showerror("エラー", "設定の保存に失敗しました")

    def _save_settings(self):
        """設定を保存"""
        # 設定の更新
        self._update_settings_data()
        
        # 現在のパスに保存
        if self.settings.save_settings():
            if self.callback:
                self.callback()
            
            self.destroy()
        else:
            messagebox.showerror("エラー", "設定の保存に失敗しました")
    
    def _update_settings_data(self):
        """UI入力からsettingsオブジェクトのデータを更新"""
        pdf_folder = self.pdf_path_var.get()
        db_folder = self.db_path_var.get()

        # 除外パターンの取得
        exclude_patterns = list(self.exclude_listbox.get(0, tk.END))

        # 設定の更新
        self.settings.update_setting("pdf_folder", pdf_folder)
        self.settings.update_setting("db_folder", db_folder)
        self.settings.update_setting("exclude_patterns", exclude_patterns)
        self.settings.update_setting("include_subfolders_index", self.include_subfolders_index_var.get())

        if self.callback:
            self.callback()
        
        self.destroy()

class PDFSearchSystem:
    def __init__(self, settings: Settings):
        self.settings = settings
        self.folder_path = self.settings.get_setting("pdf_folder")
        self.db_path = Path(self.settings.get_setting("db_folder")) / "pdf_index.db"
        self.exclude_patterns = self.settings.get_setting("exclude_patterns")
        self.include_subfolders_index = self.settings.get_setting("include_subfolders_index")
        self.base_path = Path(self.folder_path)
        self.indexing_complete = threading.Event()
        self.indexing_progress = {
            "total": 0, 
            "current": 0,
            "status": "インデックス作成の準備中..."  # 状態メッセージを追加
        }
        # クエリ結果のキャッシュを追加
        self._query_cache = {}
        self._cache_timeout = 300  # 5分

    def _normalize_text(self, text: str) -> str:
        """抽出したテキストを正規化"""
        if not text:
            return ""
            
        text = re.sub(r'\r\n|\r|\n', '\n', text)
        text = re.sub(r'\s+', ' ', text)
        text = text.translate(str.maketrans('０１２３４５６７８９', '0123456789'))
        text = text.replace('〜', '～').replace('−', '-')
        
        return text.strip()

    def _extract_context(self, content: str, query: str, exact_match: bool) -> str:
        """検索結果のコンテキストを抽出"""
        if exact_match:
            match = re.search(f".{{0,100}}{re.escape(query)}.{{0,100}}", content)
            if match:
                return match.group(0)
        else:
            if " OR " in query.upper():
                keywords = [k.strip() for k in query.split(" OR ")]
            else:
                keywords = query.split()
            
            contexts = []
            for keyword in keywords:
                match = re.search(f".{{0,100}}{re.escape(keyword)}.{{0,100}}", content)
                if match:
                    contexts.append(match.group(0))
            
            return "\n...\n".join(contexts) if contexts else content[:200]
        
        return content[:200]
    
    def should_exclude_file(self, file_path: Path) -> bool:
        """ファイルを検索対象から除外すべきかを判定"""
        filename = file_path.stem.lower()
        return any(pattern.lower() in filename for pattern in self.exclude_patterns)

    def search(self, query: str, exact_match: bool = False, include_subfolders: bool = False) -> List[Dict]:
        """PDFの検索を実行"""
        # キャッシュキーの生成
        cache_key = f"{query}_{exact_match}_{include_subfolders}"
        
        # 有効なキャッシュがあれば使用
        cached_result = self._query_cache.get(cache_key)
        if cached_result and time.time() - cached_result['time'] < self._cache_timeout:
            return cached_result['results']

        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        
        try:
            # SQLクエリの作成
            if exact_match:
                # 1語の場合は前後にスペースが追加済みのqueryをそのまま使用
                sql = """
                    SELECT file_path, content, last_modified 
                    FROM pdf_contents 
                    WHERE content LIKE ?
                """
                params = [f"%{query}%"]
            else:
                if " OR " in query.upper():
                    keywords = [k.strip() for k in query.split(" OR ")]
                    query_parts = " OR ".join([f"content LIKE ?" for _ in keywords])
                    params = [f"%{k}%" for k in keywords]
                else:
                    keywords = query.split()
                    query_parts = " AND ".join([f"content LIKE ?" for _ in keywords])
                    params = [f"%{k}%" for k in keywords]
                
                sql = f"""
                    SELECT file_path, content, last_modified 
                    FROM pdf_contents 
                    WHERE {query_parts}
                """

            # サブフォルダー設定に基づいてパスのフィルタリング
            if not include_subfolders:
                # サブフォルダーを含まない場合、ベースフォルダー直下のファイルのみを対象とする
                sql += " AND file_path NOT LIKE ?"
                base_path_str = str(Path(self.folder_path)).replace('\\', '\\\\') + "\\\\%\\\\"
                params.append(base_path_str)

            sql += " LIMIT 1000"
            
            cursor.execute(sql, params)
            results = []
            for file_path, content, last_modified in cursor.fetchall():
                # ファイルパスのチェック（サブフォルダー設定とファイル名除外パターンに基づく）
                path_obj = Path(file_path)
                if (include_subfolders or path_obj.parent == Path(self.folder_path)) and \
                   not self.should_exclude_file(path_obj):  # 除外パターンのチェックを追加
                    context = self._extract_context(content, query, exact_match)
                    results.append({
                        "file_path": file_path,
                        "file_name": path_obj.name,
                        "context": context,
                        "last_modified": time.strftime('%Y-%m-%d %H:%M:%S', 
                                                     time.localtime(last_modified))
                    })
            # 結果をキャッシュ
            self._query_cache[cache_key] = {
                'time': time.time(),
                'results': results
            }
            return results
            
        finally:
            conn.close()

def import_pdf_module(search_system):
    """PDFモジュールのインポートとインデックス作成を別スレッドで実行"""
    try:
        import pdfplumber
        from pypdf import PdfReader

        def extract_text_from_pdf(pdf_path: Path) -> str:
            """複数の方法を組み合わせてPDFからテキストを抽出"""
            content = ""
            
            try:
                with pdfplumber.open(pdf_path) as pdf:
                    for page in pdf.pages:
                        text = page.extract_text(layout=True)
                        if text:
                            content += text + "\n"
                        
                        tables = page.extract_tables()
                        for table in tables:
                            for row in table:
                                content += " ".join([str(cell) for cell in row if cell]) + "\n"
                            
            except Exception as e:
                print(f"pdfplumber failed for {pdf_path}: {e}")
                
                try:
                    reader = PdfReader(pdf_path)
                    for page in reader.pages:
                        text = page.extract_text()
                        if text:
                            content += text + "\n"
                except Exception as e:
                    print(f"PyPDF also failed for {pdf_path}: {e}")
                    return ""

            return search_system._normalize_text(content)

        def should_exclude_file(file_path: Path) -> bool:
            """ファイルを検索対象から除外すべきかを判定"""
            return search_system.should_exclude_file(file_path)  # クラスのメソッドを使用

        def setup_database():
            """データベースとテーブルの初期設定"""
            os.makedirs(os.path.dirname(search_system.db_path), exist_ok=True)
            conn = sqlite3.connect(str(search_system.db_path))
            cursor = conn.cursor()
            
            try:
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS pdf_contents (
                        id INTEGER PRIMARY KEY,
                        file_path TEXT UNIQUE,
                        content TEXT,
                        last_modified REAL,
                        created_at REAL,
                        updated_at REAL
                    )
                ''')
                
                cursor.execute('''
                    CREATE INDEX IF NOT EXISTS idx_content 
                    ON pdf_contents(content)
                ''')
                
                conn.commit()
            finally:
                conn.close()
        def index_pdfs():
            """PDFファイルのインデックス作成（差分更新）"""
            conn = sqlite3.connect(str(search_system.db_path))
            cursor = conn.cursor()
            
            try:
                # PDFファイルのリストアップ
                if search_system.include_subfolders_index:
                    pdf_files = list(Path(search_system.folder_path).glob("**/*.pdf"))
                else:
                    pdf_files = list(Path(search_system.folder_path).glob("*.pdf"))
                
                # インデックス作成開始を表示
                search_system.indexing_progress["status"] = "インデックスをサーチ中。既存のインデックス分は検索できます。..."
                search_system.indexing_progress["total"] = len(pdf_files)
                search_system.indexing_progress["current"] = 0
                
                # トランザクションを開始
                with conn:
                    for pdf_path in pdf_files:
                        search_system.indexing_progress["current"] += 1
                        
                        if should_exclude_file(pdf_path):
                            continue

                        last_modified = os.path.getmtime(pdf_path)
                        
                        cursor.execute(
                            "SELECT last_modified FROM pdf_contents WHERE file_path = ?", 
                            (str(pdf_path),)
                        )
                        result = cursor.fetchone()
                        
                        if not result or result[0] < last_modified:
                            try:
                                content = extract_text_from_pdf(pdf_path)
                                if not content:
                                    continue
                                    
                                current_time = time.time()
                                if result:
                                    cursor.execute('''
                                        UPDATE pdf_contents 
                                        SET content = ?, last_modified = ?, updated_at = ?
                                        WHERE file_path = ?
                                    ''', (content, last_modified, current_time, str(pdf_path)))
                                else:
                                    cursor.execute('''
                                        INSERT INTO pdf_contents 
                                        (file_path, content, last_modified, created_at, updated_at)
                                        VALUES (?, ?, ?, ?, ?)
                                    ''', (str(pdf_path), content, last_modified, current_time, current_time))
                            
                            except Exception as e:
                                print(f"Error processing {pdf_path}: {e}")
            finally:
                conn.close()

        # データベースのセットアップを実行
        setup_database()
        # インデックス作成を開始
        index_pdfs()
        
    except Exception as e:
        print(f"Error in background indexing: {e}")
    finally:
        search_system.indexing_complete.set()

def main():
    """メインアプリケーション"""
    root = tk.Tk()
    root.title("PDF検索システム")
    root.geometry("1000x700")

    # メインフレーム
    main_frame = tk.Frame(root, padx=20, pady=20)
    main_frame.pack(expand=True, fill='both')

    # 進捗表示フレーム
    progress_frame = tk.Frame(main_frame)
    progress_frame.pack(fill='x', pady=(0, 10))
    progress_label = tk.Label(progress_frame, text="インデックスサーチの準備中...", fg="blue")
    progress_label.pack(fill='x')

    # 設定説明フレーム
    config_help_frame = tk.Frame(main_frame)
    config_help_frame.pack(fill='x', pady=(0, 10))
    config_help_text = """設定について:
    
・「設定」メニューから、PDFフォルダー、インデックスDBフォルダー、検索除外パターンなどを設定できます。
・設定ファイルは任意の場所に保存でき、次回起動時に自動的に読み込まれます。
・初めて使用する場合や設定に問題がある場合は、メニューから「設定を編集」を選択してください。
"""
    tk.Label(config_help_frame, text=config_help_text, justify=tk.LEFT).pack(anchor='w')

    # 検索説明フレーム
    help_frame = tk.Frame(main_frame)
    help_frame.pack(fill='x', pady=(0, 10))
    help_text = """検索のヒント:
    
・  スペース区切りで複数ワードでのあいまい検索ができます。（例：機器 故障）
・  "Terminal block" などスペースを含むワードを検索するときは、「完全一致検索」にチェックを入れてください。
・  1語だけを検索したいときも、「完全一致検索」にチェックを入れてください。
・  文字やスペースの全角、半角は区別されます。
・  英単語の大文字小文字は区別されません。
・  検索結果のファイル名を選択して、ダブルクリックするか、Enterキーを押すと、PDFファイルが開きます。
"""
    tk.Label(help_frame, text=help_text, justify=tk.LEFT).pack(anchor='w')

    # 検索フレーム
    search_frame = tk.Frame(main_frame)
    search_frame.pack(fill='x', pady=(0, 10))

    tk.Label(search_frame, text="検索語:").pack(side='left')
    search_entry = tk.Entry(search_frame)
    search_entry.pack(side='left', expand=True, fill='x', padx=(5, 5))

    # 検索オプション
    option_frame = tk.Frame(main_frame)
    option_frame.pack(fill='x', pady=(0, 10))
    
    exact_match_var = tk.BooleanVar()
    tk.Checkbutton(option_frame, text="完全一致検索", 
                   variable=exact_match_var).pack(side='left', padx=(5, 5))

    include_subfolders_search_var = tk.BooleanVar()
    tk.Checkbutton(option_frame, text="サブフォルダーも検索する", 
                   variable=include_subfolders_search_var).pack(side='left', padx=(5, 5))

    # 結果表示用のペインウィンドウ
    paned = ttk.PanedWindow(main_frame, orient=tk.HORIZONTAL)
    paned.pack(expand=True, fill='both')

    # 左側：ファイル名リスト
    list_frame = tk.Frame(paned)
    paned.add(list_frame, weight=1)

    # 検索件数表示ラベル
    result_count_label = tk.Label(list_frame, text="", anchor='w')
    result_count_label.pack(fill='x')

    # ファイル名リストボックス
    file_listbox = tk.Listbox(list_frame, width=50)
    file_listbox.pack(side='left', fill='both', expand=True)
    
    list_scrollbar = tk.Scrollbar(list_frame, command=file_listbox.yview)
    list_scrollbar.pack(side='right', fill='y')
    file_listbox.configure(yscrollcommand=list_scrollbar.set)

    # 右側：詳細表示
    detail_frame = tk.Frame(paned)
    paned.add(detail_frame, weight=2)

    detail_text = tk.Text(detail_frame, wrap=tk.WORD)
    detail_text.pack(side='left', fill='both', expand=True)
    
    detail_scrollbar = tk.Scrollbar(detail_frame, command=detail_text.yview)
    detail_scrollbar.pack(side='right', fill='y')
    detail_text.configure(yscrollcommand=detail_scrollbar.set)

    # 検索結果を保存する辞書
    results_dict = {}

    def update_progress():
        """インデックス作成の進捗を更新"""
        if not search_system.indexing_complete.is_set():
            current = search_system.indexing_progress["current"]
            total = search_system.indexing_progress["total"]
            status = search_system.indexing_progress["status"]
        
            if total > 0:
                subfolder_text = "（サブフォルダーを含む）" if search_system.include_subfolders_index else ""
                progress_text = f"{status}{subfolder_text} ({current}/{total})"
            else:
                progress_text = status
                
            progress_label.config(text=progress_text)
            progress_label.update()
            
            progress_frame.pack(fill='x', pady=(0, 10))
            root.update_idletasks()
            root.after(1000, update_progress)
        else:
            progress_frame.pack_forget()

    def save_results():
        """検索結果のファイル名一覧をテキストファイルとして保存"""
        if not results_dict:
            messagebox.showwarning("警告", "保存する検索結果がありません")
            return
            
        search_word = search_entry.get()
        first_word = re.split(r'[\s,、。]', search_word)[0]
        safe_word = re.sub(r'[\\/:*?"<>|]', '', first_word)[:20]
        
        desktop_path = os.path.join(os.path.expanduser("~"), "Desktop")
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        filename = f"検索結果_{safe_word}_{timestamp}.txt"
        filepath = os.path.join(desktop_path, filename)
        
        try:
            with open(filepath, "w", encoding="utf-8") as f:
                for result in results_dict.values():
                    f.write(f"{result['file_name']}\n")
            messagebox.showinfo("成功", f"検索結果を保存しました:\n{filepath}")
        except Exception as e:
            messagebox.showerror("エラー", f"ファイルの保存に失敗しました: {e}")

    def open_selected_pdf(event=None):
        """選択されたPDFファイルを開く"""
        selection = file_listbox.curselection()
        if not selection:
            return
            
        selected_index = selection[0]
        selected_result = results_dict.get(selected_index)
        
        if selected_result:
            pdf_path = selected_result['file_path']
            try:
                os.startfile(pdf_path)
            except Exception as e:
                messagebox.showerror("エラー", f"PDFファイルを開けませんでした: {e}")

    def show_file_details(event=None):
        """選択されたファイルの詳細を表示"""
        selection = file_listbox.curselection()
        if not selection:
            return
            
        selected_index = selection[0]
        selected_result = results_dict.get(selected_index)
        
        if selected_result:
            detail_text.delete('1.0', tk.END)
            detail_text.insert(tk.END, f"ファイル: {selected_result['file_path']}\n")
            detail_text.insert(tk.END, f"最終更新: {selected_result['last_modified']}\n")
            detail_text.insert(tk.END, f"\nコンテキスト:\n{selected_result['context']}\n")

    def perform_search():
        """検索を実行"""
        original_query = search_entry.get()
        if not original_query:
            messagebox.showwarning("警告", "検索語を入力してください")
            return
        
        # 完全一致検索で1語の場合、前後にスペースを追加（内部処理用）
        query = original_query
        if exact_match_var.get():
            # スペースで分割して単語数をカウント（連続スペースは1つとして扱う）
            words = [w for w in query.split() if w]
            if len(words) == 1:  # 1語の場合のみ
                query = f" {words[0]} "  # 元の入力形式に関係なく、必ずスペースを追加
        
        start_time = time.time()
        file_listbox.delete(0, tk.END)
        detail_text.delete('1.0', tk.END)
        results_dict.clear()
        
        results = search_system.search(
            query, 
            exact_match=exact_match_var.get(),
            include_subfolders=include_subfolders_search_var.get()
        )

        if not results:
            result_count_label.config(text="検索結果が見つかりませんでした。")
            return
        
        search_time = time.time() - start_time
        result_count_label.config(text=f"検索結果: {len(results)}件 ({search_time:.2f}秒)")
        
        for i, result in enumerate(results):
            file_listbox.insert(tk.END, result['file_name'])
            results_dict[i] = result

    def clear_search_entry():
        """検索窓の入力値をクリア"""
        search_entry.delete(0, tk.END)

    def start_indexing_after_config():
        """検索システムの初期化とインデックス作成の開始"""
        nonlocal search_system
        search_system = PDFSearchSystem(settings)
        
        # 設定が空の場合は設定画面を表示
        if not settings.get_setting("pdf_folder") or not settings.get_setting("db_folder"):
            messagebox.showinfo("設定が必要です", "PDFフォルダーとインデックスDBフォルダーを設定してください。")
            config_dialog = ConfigDialog(root, settings, callback=start_indexing_after_config)
            return
            
        progress_label.config(text="インデックス作成の準備中...")
        progress_label.update()
        import_thread = threading.Thread(target=lambda: import_pdf_module(search_system))
        import_thread.daemon = True
        import_thread.start()
        root.after(100, update_progress)

    # 設定の初期化
    settings = Settings()
    search_system = None

    # 初回起動時も含め自動的に設定読み込みとインデックス作成を開始
    start_indexing_after_config()

    # メニューバーの作成
    menubar = tk.Menu(root)
    root.config(menu=menubar)

    # 設定メニュー
    settings_menu = tk.Menu(menubar, tearoff=0)
    menubar.add_cascade(label="設定", menu=settings_menu)
    settings_menu.add_command(
        label="設定を編集", 
        command=lambda: ConfigDialog(root, settings, callback=start_indexing_after_config)
    )
    
    # 設定ファイル関連のメニュー項目
    settings_menu.add_separator()
    settings_menu.add_command(
        label="設定ファイルを開く",
        command=lambda: load_settings_file()
    )
    
    settings_menu.add_command(
        label="名前を付けて設定を保存",
        command=lambda: save_settings_as()
    )

    # 設定ファイルを開く
    def load_settings_file():
        file_path = filedialog.askopenfilename(
            title="設定ファイルを開く",
            defaultextension=".json",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
            initialdir=os.path.dirname(str(settings.settings_file))
        )
        
        if file_path:
            if settings.load_settings_from_file(file_path):
                messagebox.showinfo("成功", f"設定ファイルを読み込みました: {file_path}")
                start_indexing_after_config()
            else:
                messagebox.showerror("エラー", "設定ファイルの読み込みに失敗しました")

    # 設定を別名で保存
    def save_settings_as():
        file_path = filedialog.asksaveasfilename(
            title="設定ファイルを保存",
            defaultextension=".json",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
            initialdir=os.path.dirname(str(settings.settings_file))
        )
        
        if file_path:
            if settings.save_settings_to_file(file_path):
                messagebox.showinfo("成功", f"設定ファイルを保存しました: {file_path}")
                # 保存後、その設定ファイルを使用する
                start_indexing_after_config()
            else:
                messagebox.showerror("エラー", "設定ファイルの保存に失敗しました")

    # 検索ボタンと保存ボタンと削除ボタン
    button_frame = tk.Frame(search_frame)
    button_frame.pack(side='left', padx=(5, 0))
    
    tk.Button(button_frame, text="検索", command=perform_search).pack(side='left', padx=(0, 5))
    tk.Button(button_frame, text="結果を保存", command=save_results).pack(side='left', padx=(0, 5))
    tk.Button(button_frame, text="削除", command=clear_search_entry).pack(side='left')

    # バインディング
    search_entry.bind('<Return>', lambda event: perform_search())
    file_listbox.bind('<Return>', open_selected_pdf)
    file_listbox.bind('<Double-Button-1>', open_selected_pdf)
    file_listbox.bind('<<ListboxSelect>>', show_file_details)

    root.mainloop()

if __name__ == "__main__":
    main()