# 動画比較ビューア (Video Comparison Viewer)

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.7+](https://img.shields.io/badge/python-3.7+-blue.svg)](https://www.python.org/downloads/)

複数の動画を同時に再生・比較できるPythonアプリケーションです。異なる動画を並べて表示し、同期再生や保存機能を提供します。

![Video Comparison Viewer Demo](docs/demo.gif)
*複数動画の同時比較表示例*

## 特徴

- **複数動画の同時再生**: 最大9個の動画を同時に表示・再生
- **柔軟なレイアウト**: 1x1から3x3まで9種類のレイアウトに対応
- **ドラッグ&ドロップ対応**: 動画ファイルを直接ドロップして読み込み
- **再生速度調整**: 0.25倍から4倍まで再生速度を変更可能
- **フレーム単位の操作**: キーボードでフレーム送り・戻しが可能
- **動画保存**: 比較表示の状態で新しい動画として保存
- **キーボードショートカット**: 直感的な操作が可能

## 必要な環境

### Python バージョン
- Python 3.7以上

### 必要なライブラリ
```bash
pip install opencv-python pillow numpy tkinterdnd2
```

または、requirements.txtがある場合：
```bash
pip install -r requirements.txt
```

## インストール

1. **リポジトリをクローン**
```bash
git clone https://github.com/Romihi/video_comparison_viewer.git
cd video_comparison_viewer
```

2. **必要なライブラリをインストール**
```bash
pip install -r requirements.txt
```

3. **アプリケーションを実行**
```bash
python video_comparison.py
```

## 使い方

### 基本操作

1. **動画の読み込み**
   - 「動画を選択」ボタンをクリックして動画ファイルを選択
   - または、動画ファイルを直接アプリケーションウィンドウにドラッグ&ドロップ

2. **レイアウトの変更**
   - レイアウトドロップダウンから表示形式を選択（1x1～3x3）

3. **再生制御**
   - 「再生/停止」ボタンまたはスペースキーで再生制御
   - 速度ドロップダウンで再生速度を調整
   - フレームスライダーで任意の位置にジャンプ

### キーボードショートカット

| キー | 機能 |
|------|------|
| `Space` | 再生/停止 |
| `←` | 1フレーム戻る |
| `→` | 1フレーム進む |

### 動画保存

1. 「動画保存」ボタンをクリック
2. 現在の表示状態（レイアウト、速度設定）で新しい動画ファイルが作成されます
3. 保存完了後、作成された動画を直接開くことができます

## サポートされているファイル形式

- MP4 (.mp4)
- AVI (.avi)
- MOV (.mov)
- MKV (.mkv)
- WMV (.wmv)
- FLV (.flv)

## 機能詳細

### レイアウトオプション
- **1x1**: 単一動画表示
- **1x2, 1x3**: 横並び表示
- **2x1, 3x1**: 縦並び表示
- **2x2**: 2×2グリッド表示
- **2x3, 3x2**: 矩形グリッド表示
- **3x3**: 3×3グリッド表示（最大9動画）

### 再生速度オプション
- 0.25x, 0.5x, 0.75x (スロー再生)
- 1.0x (通常速度)
- 1.25x, 1.5x, 2.0x, 3.0x, 4.0x (高速再生)

### 保存機能
- 表示中の全動画を1つの動画ファイルに結合
- 各動画のファイル名をオーバーレイ表示
- 設定した再生速度を反映した動画を出力
- 進捗表示付きの保存プロセス

## トラブルシューティング

### よくある問題

1. **アプリケーションが起動しない**
   - 必要なライブラリがインストールされているか確認
   - Python 3.7以上がインストールされているか確認

2. **動画が読み込めない**
   - サポートされているファイル形式か確認
   - ファイルが破損していないか確認
   - OpenCVでサポートされているコーデックか確認

3. **保存に失敗する**
   - 保存先ディレクトリに書き込み権限があるか確認
   - 十分なディスク容量があるか確認

### 動作環境
- **Windows**: 推奨（最大化機能対応）
- **Linux**: 対応（一部UI調整が必要な場合があります）
- **macOS**: 基本対応

## ライセンス

このプロジェクトは [MITライセンス](LICENSE) の下で公開されています。

## 貢献

バグ報告や機能要望は、[GitHub Issues](https://github.com/Romihi/video_comparison_viewer/issues) までお願いします。

プルリクエストも歓迎しています！以下の手順で貢献してください：

1. このリポジトリをフォーク
2. 機能ブランチを作成 (`git checkout -b feature/amazing-feature`)
3. 変更をコミット (`git commit -m 'Add some amazing feature'`)
4. ブランチにプッシュ (`git push origin feature/amazing-feature`)
5. プルリクエストを作成

## サポート

問題が発生した場合は、以下の方法でサポートを受けられます：

- [GitHub Issues](https://github.com/Romihi/video_comparison_viewer/issues) でバグ報告や質問
- [GitHub Discussions](https://github.com/Romihi/video_comparison_viewer/discussions) で一般的な議論や質問

## 作者

[@Romihi](https://github.com/Romihi)

## 更新履歴

### v1.0.0
- 初回リリース
- 複数動画同時再生機能
- レイアウト変更機能
- 動画保存機能
- キーボードショートカット対応