# Registry Path（日本語）

[XeFM](https://github.com/crftwr/xefm) 用の Windows 専用拡張機能です。Windows レジストリを `reg://` URI の仮想フォルダーとして開き、キーと値を XeFM 内で閲覧できます。

- XeFM **1.12.0 以降**が必要です（拡張マニフェストの `min_xefm`）。
- **Windows 専用**です。
- レジストリの一覧・値の読み取りは読み取り専用です。キーや値を作成・変更・削除する機能はありません。
- 拡張機能に追加の Python パッケージは必要ありません。

## インストール

XeFM のコマンドラインで次を実行します。

```text
xefm ext install github:SinisterSoftware/xefm-registry-path
```

インストール後、XeFM の **Tools ▸ Reload Configuration** を実行するか、XeFM を再起動してください。

## レジストリを開く

XeFM で `reg://` URI をパスとして開きます。ルートを開くと、次のハイブが表示されます。

| URI の例 | 説明 |
|---|---|
| `reg://HKEY_CLASSES_ROOT` | ファイルの種類や COM などに関する登録 |
| `reg://HKEY_CURRENT_USER` | 現在のユーザーの設定 |
| `reg://HKEY_LOCAL_MACHINE` | コンピューター全体の設定 |
| `reg://HKEY_USERS` | ユーザープロファイルの設定 |
| `reg://HKEY_CURRENT_CONFIG` | 現在のハードウェア構成 |

キー名は URI のパス要素として `/` で区切ります。たとえば `HKEY_CURRENT_USER\Software` を開くには、次の URI を指定します。

```text
reg://HKEY_CURRENT_USER/Software
```

その下のキーも同じ形式で続けられます（例: `reg://HKEY_CURRENT_USER/Software/Microsoft`）。表示されるキーはフォルダー、値はファイルとして扱われます。値名が空の既定値は `(Default)` と表示されます。値名に `/` が含まれる場合は、パス区切りと区別するため `∕` と表示されます。

## 一覧と値の表示

レジストリ内の一覧には、通常の名前に加えて **Registry type** と **Registry data** の列が表示されます。

- キーの型列は `<KEY>`、値の型列は `SZ`、`DWORD`、`BINARY` などです（`REG_` 接頭辞を省いた表示）。
- データ列は値のプレビューです。長いデータは先頭 60 文字までに省略記号を付けて表示します。
- 複数文字列値はプレビューでは ` | ` 区切り、バイナリ値は空白区切りの 16 進数、整数値は 16 進数と 10 進数で表示します。
- 値をファイルとして開くと、内容をテキストで確認できます。先頭行に `REG_SZ` や `REG_DWORD` などの型が表示され、その後に値データが続きます。複数文字列値は改行区切り、整数値は 10 進数と 16 進数、バイナリ値は空白区切りの 16 進数で表示されます。

## regedit でキーを開く

拡張機能の **Open the current registry key in regedit** アクション（推奨キー: **Alt-Shift-Q**）を実行すると、現在のキーを Windows のレジストリ エディターで開きます。値の行にカーソルがある場合は、その値を含む親キーを開きます。

このアクションは、移動先を指定するためにユーザーの `HKEY_CURRENT_USER\Software\Microsoft\Windows\CurrentVersion\Applets\Regedit` にある `LastKey` を設定してから `regedit.exe` を起動します。したがって、`reg://` の閲覧自体は読み取り専用ですが、このアクションはレジストリ エディターのナビゲーション設定を書き換えます。起動した regedit は通常どおり編集可能です。レジストリ エディターの起動時に Windows の確認や権限昇格が求められることがあります。

この拡張機能は `LastKey` に `コンピューター` を含むパスを設定します。Windows の表示言語などの環境によっては、regedit が指定されたキーを開かずに起動する場合があります。

## 制限とトラブルシューティング

- XeFM 1.12.0 未満、または Windows 以外では使用できません。
- Windows のアクセス許可などでキーを読み取れない場合、そのキーの内容が一覧に表示されないことがあります。XeFM で見えないことは、キーが存在しないことを意味するとは限りません。
- `regedit` アクションがキー内で動作しない場合は、まず `reg://` のパスを開いてから実行してください。regedit が起動しても目的のキーに移動しない場合は、Windows の表示言語やアクセス許可の影響も考えられます。
- この拡張機能はレジストリ値を XeFM 上で編集しません。変更が必要な場合は、対象を確認したうえで Windows のレジストリ エディターを使用してください。レジストリの変更は Windows やアプリケーションの動作に影響することがあります。
