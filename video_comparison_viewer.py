import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import cv2
import numpy as np
from PIL import Image, ImageTk
import threading
import time
import os
import subprocess
import platform
from tkinterdnd2 import DND_FILES, TkinterDnD

class VideoPlayer:
    def __init__(self, video_path, position, size):
        self.video_path = video_path
        self.position = position  # (x, y)
        self.size = size  # (width, height)
        self.cap = cv2.VideoCapture(video_path)
        self.frame_count = int(self.cap.get(cv2.CAP_PROP_FRAME_COUNT))
        self.fps = self.cap.get(cv2.CAP_PROP_FPS)
        self.current_frame = 0
        self.is_playing = False
        
    def get_frame(self, frame_number=None):
        if frame_number is not None:
            self.cap.set(cv2.CAP_PROP_POS_FRAMES, frame_number)
            self.current_frame = frame_number
        
        ret, frame = self.cap.read()
        if ret:
            # フレームをリサイズ
            frame = cv2.resize(frame, self.size)
            # BGRからRGBに変換
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            return frame
        return None
    
    def release(self):
        self.cap.release()

class VideoComparisonApp:
    def __init__(self, root):
        self.root = root
        self.root.title("動画比較ビューア")
        self.root.state('zoomed')  # Windowsで最大化
        # self.root.attributes('-zoomed', True)  # Linuxの場合はこちらを使用
        
        self.videos = []
        self.video_players = []
        self.is_playing = False
        self.current_frame = 0
        self.max_frames = 0
        
        self.setup_ui()
        self.setup_drag_drop()
        self.setup_keyboard_bindings()
        
        # ウィンドウサイズ変更イベントをバインド
        self.root.bind('<Configure>', self.on_window_resize)
        
    def setup_ui(self):
        # メインフレーム
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # コントロールパネル
        control_frame = ttk.Frame(main_frame)
        control_frame.pack(fill=tk.X, pady=(0, 10))
        
        # ファイル選択ボタン
        ttk.Button(control_frame, text="動画を選択", 
                  command=self.select_videos).pack(side=tk.LEFT, padx=(0, 10))
        
        # レイアウト設定
        ttk.Label(control_frame, text="レイアウト:").pack(side=tk.LEFT, padx=(10, 5))
        self.layout_var = tk.StringVar(value="2x2")
        layout_combo = ttk.Combobox(control_frame, textvariable=self.layout_var,
                                   values=["1x1", "1x2", "1x3", "2x1", "2x2", "2x3", "3x1", "3x2", "3x3"],
                                   width=10, state="readonly")
        layout_combo.pack(side=tk.LEFT, padx=(0, 10))
        layout_combo.bind("<<ComboboxSelected>>", self.update_layout)
        
        # 再生コントロール
        ttk.Button(control_frame, text="再生/停止", 
                  command=self.toggle_playback).pack(side=tk.LEFT, padx=(10, 5))
        
        # 再生速度調整
        ttk.Label(control_frame, text="速度:").pack(side=tk.LEFT, padx=(10, 5))
        self.speed_var = tk.DoubleVar(value=1.0)
        speed_combo = ttk.Combobox(control_frame, textvariable=self.speed_var,
                                  values=[0.25, 0.5, 0.75, 1.0, 1.25, 1.5, 2.0, 3.0, 4.0],
                                  width=8, state="readonly")
        speed_combo.pack(side=tk.LEFT, padx=(0, 10))
        
        # 保存ボタン
        ttk.Button(control_frame, text="動画保存", 
                  command=self.save_video).pack(side=tk.LEFT, padx=(10, 5))
        
        # フレームスライダー
        self.frame_var = tk.IntVar()
        self.frame_scale = ttk.Scale(control_frame, from_=0, to=100, 
                                    variable=self.frame_var, orient=tk.HORIZONTAL,
                                    command=self.seek_frame, length=200)
        self.frame_scale.pack(side=tk.LEFT, padx=(10, 5))
        
        # フレーム表示ラベル
        self.frame_label = ttk.Label(control_frame, text="Frame: 0/0")
        self.frame_label.pack(side=tk.LEFT, padx=(10, 5))
        
        # キーボード操作説明
        help_label = ttk.Label(control_frame, text="[左右←→キー: フレーム送り | Spaceキー: 再生/停止]", 
                              font=("Arial", 8), foreground="black", background="white")
        help_label.pack(side=tk.LEFT, padx=(5, 0))
        
        # 動画表示エリア
        self.canvas_frame = ttk.Frame(main_frame)
        self.canvas_frame.pack(fill=tk.BOTH, expand=True)
        
        self.canvas = tk.Canvas(self.canvas_frame, bg="black")
        self.canvas.pack(fill=tk.BOTH, expand=True)
        
        # ドラッグ&ドロップ用のラベル
        self.drop_label = ttk.Label(self.canvas, 
                                   text="動画ファイルをここにドラッグ&ドロップするか、\n「動画を選択」ボタンをクリックしてください",
                                   font=("Arial", 14), foreground="white", background="black")
        self.drop_label.place(relx=0.5, rely=0.5, anchor=tk.CENTER)
        
        # 進捗表示用ウィジェット
        self.progress_frame = None
        self.progress_bar = None
        self.progress_label = None
        
    def setup_keyboard_bindings(self):
        # キーボードイベントをバインド（フォーカスを確保するため）
        self.root.bind('<Key>', self.on_key_press)
        self.root.focus_set()  # ルートウィンドウにフォーカスを設定
        
        # キャンバスクリック時にもフォーカスを設定
        self.canvas.bind('<Button-1>', lambda e: self.root.focus_set())
    
    def setup_drag_drop(self):
        # ドラッグ&ドロップの設定
        self.canvas.drop_target_register(DND_FILES)
        self.canvas.dnd_bind('<<Drop>>', self.on_drop)
    
    def on_key_press(self, event):
        if not self.video_players or self.max_frames == 0:
            return
        
        key = event.keysym
        
        if key == 'Left':
            # 左キー：1フレーム戻る
            new_frame = max(0, self.current_frame - 1)
            self.current_frame = new_frame
            self.frame_var.set(new_frame)
            self.update_frame_display()
            
        elif key == 'Right':
            # 右キー：1フレーム進む
            new_frame = min(self.max_frames - 1, self.current_frame + 1)
            self.current_frame = new_frame
            self.frame_var.set(new_frame)
            self.update_frame_display()
            
        elif key == 'space':
            # スペースキー：再生/停止
            self.toggle_playback()
            return 'break'  # デフォルトの動作を防ぐ
    
    def on_window_resize(self, event):
        # ウィンドウサイズが変更された時の処理
        if event.widget == self.root and self.video_players:
            # 少し遅延させてレイアウトを更新（連続的なリサイズイベントを避けるため）
            self.root.after(100, self.update_layout)
        
    def on_drop(self, event):
        files = self.root.tk.splitlist(event.data)
        video_files = [f for f in files if f.lower().endswith(('.mp4', '.avi', '.mov', '.mkv', '.wmv', '.flv'))]
        if video_files:
            self.load_videos(video_files)
        
    def select_videos(self):
        files = filedialog.askopenfilenames(
            title="動画ファイルを選択",
            filetypes=[
                ("動画ファイル", "*.mp4 *.avi *.mov *.mkv *.wmv *.flv"),
                ("すべてのファイル", "*.*")
            ]
        )
        if files:
            self.load_videos(files)
    
    def load_videos(self, video_paths):
        # 既存の動画プレイヤーをクリーンアップ
        for player in self.video_players:
            player.release()
        self.video_players.clear()
        
        self.videos = video_paths
        self.drop_label.place_forget()  # ドロップラベルを非表示
        
        # レイアウトを更新
        self.update_layout()
        
        messagebox.showinfo("読み込み完了", f"{len(video_paths)}個の動画を読み込みました")
    
    def update_layout(self, event=None):
        if not self.videos:
            return
        
        layout = self.layout_var.get()
        rows, cols = map(int, layout.split('x'))
        
        # キャンバスのサイズを強制的に更新
        self.canvas.update_idletasks()
        canvas_width = self.canvas.winfo_width()
        canvas_height = self.canvas.winfo_height()
        
        # サイズが取得できない場合は少し待つ
        if canvas_width <= 1 or canvas_height <= 1:
            self.root.after(50, self.update_layout)
            return
        
        # 各動画のサイズを計算（マージンを考慮）
        margin = 2  # 動画間のマージン
        video_width = (canvas_width - margin * (cols - 1)) // cols
        video_height = (canvas_height - margin * (rows - 1)) // rows
        
        # 動画プレイヤーを再初期化
        for player in self.video_players:
            player.release()
        self.video_players.clear()
        
        # キャンバスをクリアしてオブジェクト参照をリセット
        self.canvas.delete("all")
        if hasattr(self, 'canvas_objects'):
            self.canvas_objects.clear()
        if hasattr(self, 'photo_refs'):
            self.photo_refs.clear()
        
        self.max_frames = 0
        
        # 新しい動画プレイヤーを作成
        for i, video_path in enumerate(self.videos[:rows * cols]):
            row = i // cols
            col = i % cols
            
            x = col * (video_width + margin)
            y = row * (video_height + margin)
            
            player = VideoPlayer(video_path, (x, y), (video_width, video_height))
            self.video_players.append(player)
            
            # 最大フレーム数を更新
            self.max_frames = max(self.max_frames, player.frame_count)
        
        # スライダーの範囲を更新
        self.frame_scale.configure(to=self.max_frames - 1 if self.max_frames > 0 else 0)
        self.update_frame_display()
    
    def toggle_playback(self):
        self.is_playing = not self.is_playing
        if self.is_playing:
            self.play_videos()
    
    def play_videos(self):
        if not self.is_playing or not self.video_players:
            return
        
        start_time = time.time()
        base_fps = 30
        speed_multiplier = self.speed_var.get()
        frame_interval = 1.0 / (base_fps * speed_multiplier)
        
        def play_loop():
            frame_counter = 0
            while self.is_playing and self.current_frame < self.max_frames:
                self.update_frame_display()
                self.current_frame += 1
                self.frame_var.set(self.current_frame)
                
                # フレームレート調整（速度に応じて）
                frame_counter += 1
                elapsed = time.time() - start_time
                expected_time = frame_interval * frame_counter
                sleep_time = expected_time - elapsed
                if sleep_time > 0:
                    time.sleep(sleep_time)
        
        threading.Thread(target=play_loop, daemon=True).start()
    
    def seek_frame(self, value):
        self.current_frame = int(float(value))
        self.update_frame_display()
    
    def update_frame_display(self):
        if not self.video_players:
            return
        
        # 画像参照リストを初期化
        if not hasattr(self, 'photo_refs'):
            self.photo_refs = []
        
        # 必要に応じてリストを拡張
        while len(self.photo_refs) < len(self.video_players):
            self.photo_refs.append(None)
        
        # キャンバスオブジェクトIDリストを初期化
        if not hasattr(self, 'canvas_objects'):
            self.canvas_objects = []
            # 初回はcanvasをクリア
            self.canvas.delete("all")
        
        # 必要に応じてリストを拡張
        while len(self.canvas_objects) < len(self.video_players) * 2:  # 画像とテキスト用
            self.canvas_objects.append(None)
        
        for i, player in enumerate(self.video_players):
            frame = player.get_frame(self.current_frame)
            if frame is not None:
                # PILイメージに変換
                pil_image = Image.fromarray(frame)
                photo = ImageTk.PhotoImage(pil_image)
                
                # 参照を保持
                self.photo_refs[i] = photo
                
                x, y = player.position
                
                # 画像の更新または作成
                img_index = i * 2  # 画像用インデックス
                text_index = i * 2 + 1  # テキスト用インデックス
                
                if self.canvas_objects[img_index] is None:
                    # 新規作成
                    self.canvas_objects[img_index] = self.canvas.create_image(x, y, anchor=tk.NW, image=photo)
                else:
                    # 既存のオブジェクトを更新
                    self.canvas.itemconfig(self.canvas_objects[img_index], image=photo)
                    self.canvas.coords(self.canvas_objects[img_index], x, y)
                
                # ファイル名テキストの処理
                filename = os.path.basename(player.video_path)
                text_x = x + player.size[0] // 2
                text_y = y + player.size[1] - 20
                font_size = max(8, min(16, player.size[0] // 30))
                
                if self.canvas_objects[text_index] is None:
                    # 新規作成
                    self.canvas_objects[text_index] = self.canvas.create_text(
                        text_x, text_y, text=filename, fill="white", 
                        font=("Arial", font_size), anchor=tk.CENTER
                    )
                else:
                    # 既存のテキストを更新
                    self.canvas.itemconfig(self.canvas_objects[text_index], 
                                         text=filename, font=("Arial", font_size))
                    self.canvas.coords(self.canvas_objects[text_index], text_x, text_y)
        
        # フレーム情報を更新
        self.frame_label.config(text=f"Frame: {self.current_frame}/{self.max_frames}")
    
    def save_video(self):
        if not self.video_players:
            messagebox.showwarning("警告", "保存する動画がありません")
            return
        
        # 1つ目のファイル名から自動的に出力ファイル名を生成
        first_video_path = self.videos[0]
        base_name = os.path.splitext(os.path.basename(first_video_path))[0]
        output_dir = os.path.dirname(first_video_path)
        
        # 再生速度をファイル名に追加
        speed = self.speed_var.get()
        if speed == 1.0:
            speed_suffix = ""
        else:
            speed_suffix = f"_x{speed}".replace(".", "p")  # ドットをpに置換（ファイル名対応）
        
        output_filename = f"{base_name}_comparison{speed_suffix}.mp4"
        output_path = os.path.join(output_dir, output_filename)
        
        # 進捗ウィンドウを表示
        self.show_progress_window()
        
        # 保存処理を別スレッドで実行
        threading.Thread(target=self._save_video_process, args=(output_path,), daemon=True).start()
    
    def show_progress_window(self):
        # 進捗表示ウィンドウ
        self.progress_frame = tk.Toplevel(self.root)
        self.progress_frame.title("動画保存中")
        self.progress_frame.geometry("400x120")
        self.progress_frame.resizable(False, False)
        self.progress_frame.transient(self.root)
        self.progress_frame.grab_set()
        
        # 中央に配置
        self.progress_frame.geometry("+%d+%d" % (
            self.root.winfo_rootx() + 50,
            self.root.winfo_rooty() + 50
        ))
        
        # 進捗ラベル
        self.progress_label = ttk.Label(self.progress_frame, text="動画保存を準備中...", 
                                       font=("Arial", 12))
        self.progress_label.pack(pady=20)
        
        # 進捗バー
        self.progress_bar = ttk.Progressbar(self.progress_frame, length=350, mode='determinate')
        self.progress_bar.pack(pady=10)
        
        # キャンセルボタン（今回は実装しないが、将来の拡張用）
        # ttk.Button(self.progress_frame, text="キャンセル").pack(pady=10)
    
    def update_progress(self, current, total, message=""):
        if self.progress_bar and self.progress_label:
            progress_percent = (current / total) * 100
            self.progress_bar['value'] = progress_percent
            
            if message:
                self.progress_label.config(text=message)
            else:
                self.progress_label.config(text=f"保存中... {current}/{total} フレーム ({progress_percent:.1f}%)")
            
            self.progress_frame.update()
    
    def close_progress_window(self):
        if self.progress_frame:
            self.progress_frame.destroy()
            self.progress_frame = None
            self.progress_bar = None
            self.progress_label = None
    
    def _save_video_process(self, output_path):
        try:
            # 進捗更新
            self.root.after(0, lambda: self.update_progress(0, self.max_frames, "動画の初期化中..."))
            
            # 現在のキャンバスサイズを取得
            self.canvas.update_idletasks()
            canvas_width = self.canvas.winfo_width()
            canvas_height = self.canvas.winfo_height()
            
            # 再生速度を取得
            speed_multiplier = self.speed_var.get()
            
            # VideoWriterを初期化（固定30FPS）
            output_fps = 30
            fourcc = cv2.VideoWriter_fourcc(*'mp4v')
            out = cv2.VideoWriter(output_path, fourcc, output_fps, (canvas_width, canvas_height))
            
            # 速度に応じたフレーム処理の計算
            if speed_multiplier >= 1.0:
                # 高速再生：フレームをスキップ
                frame_step = speed_multiplier  # 例：2倍速なら2フレームごと
                total_output_frames = int(self.max_frames / speed_multiplier)
            else:
                # 低速再生：フレームを複製
                frame_step = 1
                frame_repeat = int(1 / speed_multiplier)  # 例：0.5倍速なら各フレームを2回
                total_output_frames = self.max_frames * frame_repeat
            
            output_frame_count = 0
            
            if speed_multiplier >= 1.0:
                # 高速再生の処理
                for i in range(total_output_frames):
                    frame_num = int(i * frame_step)
                    if frame_num >= self.max_frames:
                        break
                    
                    # 進捗更新
                    if output_frame_count % 10 == 0:
                        progress = output_frame_count / total_output_frames
                        self.root.after(0, lambda p=progress: self.update_progress(int(p * total_output_frames), total_output_frames))
                    
                    # 合成フレームを作成
                    combined_frame = np.zeros((canvas_height, canvas_width, 3), dtype=np.uint8)
                    
                    for player in self.video_players:
                        frame = player.get_frame(frame_num)
                        if frame is not None:
                            x, y = player.position
                            w, h = player.size
                            
                            # フレームを配置
                            combined_frame[y:y+h, x:x+w] = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
                            
                            # ファイル名を描画
                            filename = os.path.basename(player.video_path)
                            text_x = x + w // 2
                            text_y = y + h - 10
                            
                            # テキストサイズを計算（動的にスケール調整）
                            font = cv2.FONT_HERSHEY_SIMPLEX
                            font_scale = min(w, h) / 400
                            font_scale = max(0.3, min(1.0, font_scale))
                            thickness = max(1, int(font_scale * 2))
                            text_size = cv2.getTextSize(filename, font, font_scale, thickness)[0]
                            
                            # テキストの背景を描画（可読性向上）
                            bg_x1 = text_x - text_size[0] // 2 - 5
                            bg_y1 = text_y - text_size[1] - 5
                            bg_x2 = text_x + text_size[0] // 2 + 5
                            bg_y2 = text_y + 5
                            cv2.rectangle(combined_frame, (bg_x1, bg_y1), (bg_x2, bg_y2), (0, 0, 0), -1)
                            
                            # テキストを描画
                            text_x_adjusted = text_x - text_size[0] // 2
                            cv2.putText(combined_frame, filename, (text_x_adjusted, text_y), 
                                       font, font_scale, (255, 255, 255), thickness, cv2.LINE_AA)
                    
                    out.write(combined_frame)
                    output_frame_count += 1
            else:
                # 低速再生の処理
                for frame_num in range(self.max_frames):
                    # 進捗更新
                    if output_frame_count % 10 == 0:
                        progress = frame_num / self.max_frames
                        self.root.after(0, lambda p=progress: self.update_progress(int(p * self.max_frames), self.max_frames))
                    
                    # 合成フレームを作成
                    combined_frame = np.zeros((canvas_height, canvas_width, 3), dtype=np.uint8)
                    
                    for player in self.video_players:
                        frame = player.get_frame(frame_num)
                        if frame is not None:
                            x, y = player.position
                            w, h = player.size
                            
                            # フレームを配置
                            combined_frame[y:y+h, x:x+w] = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
                            
                            # ファイル名を描画
                            filename = os.path.basename(player.video_path)
                            text_x = x + w // 2
                            text_y = y + h - 10
                            
                            # テキストサイズを計算（動的にスケール調整）
                            font = cv2.FONT_HERSHEY_SIMPLEX
                            font_scale = min(w, h) / 400
                            font_scale = max(0.3, min(1.0, font_scale))
                            thickness = max(1, int(font_scale * 2))
                            text_size = cv2.getTextSize(filename, font, font_scale, thickness)[0]
                            
                            # テキストの背景を描画（可読性向上）
                            bg_x1 = text_x - text_size[0] // 2 - 5
                            bg_y1 = text_y - text_size[1] - 5
                            bg_x2 = text_x + text_size[0] // 2 + 5
                            bg_y2 = text_y + 5
                            cv2.rectangle(combined_frame, (bg_x1, bg_y1), (bg_x2, bg_y2), (0, 0, 0), -1)
                            
                            # テキストを描画
                            text_x_adjusted = text_x - text_size[0] // 2
                            cv2.putText(combined_frame, filename, (text_x_adjusted, text_y), 
                                       font, font_scale, (255, 255, 255), thickness, cv2.LINE_AA)
                    
                    # フレームを複数回書き込み（低速効果）
                    for _ in range(frame_repeat):
                        out.write(combined_frame)
                        output_frame_count += 1
            
            # 保存完了
            out.release()
            
            # 最終進捗更新
            if speed_multiplier >= 1.0:
                self.root.after(0, lambda: self.update_progress(total_output_frames, total_output_frames, "保存完了！"))
            else:
                self.root.after(0, lambda: self.update_progress(self.max_frames, self.max_frames, "保存完了！"))
            
            # 少し待ってから進捗ウィンドウを閉じる
            self.root.after(1000, self.close_progress_window)
            
            # メインスレッドでメッセージを表示
            speed_text = f" (速度: {speed_multiplier}x)" if speed_multiplier != 1.0 else ""
            self.root.after(1500, lambda: self.show_completion_and_open(output_path, speed_text))

        except Exception as e:
            # エラーハンドリング
            self.root.after(0, self.close_progress_window)
            self.root.after(100, lambda: messagebox.showerror("保存エラー", f"動画の保存中にエラーが発生しました:\n{str(e)}"))
            print(f"保存エラー: {e}")
    
    def __del__(self):
        # クリーンアップ
        for player in self.video_players:
            player.release()

    def show_completion_and_open(self, output_path, speed_text):
        # 保存完了メッセージを表示
        result = messagebox.askyesno("保存完了", 
                                    f"動画を保存しました{speed_text}:\n{output_path}\n\n保存した動画を開きますか？")
        
        if result:
            self.open_video_file(output_path)

    def open_video_file(self, file_path):
        try:
            system = platform.system()
            if system == "Windows":
                subprocess.run(['start', file_path], shell=True, check=True)
            elif system == "Darwin":  # macOS
                subprocess.run(['open', file_path], check=True)
            else:  # Linux
                subprocess.run(['xdg-open', file_path], check=True)
        except Exception as e:
            messagebox.showerror("エラー", f"動画を開けませんでした:\n{str(e)}")

def main():
    root = TkinterDnD.Tk()
    app = VideoComparisonApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()