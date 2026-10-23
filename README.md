# Solar AM Notes ☀️

メガソーラーのアセットマネジメントを学ぶための個人学習ノートサイトです。
HTML / CSS / JavaScript のみで構成した静的サイトなので、GitHub Pages でそのまま公開できます。

## 構成

```
├── index.html            トップページ
├── notes/
│   ├── performance.html  01 発電性能分析
│   ├── om.html           02 O&M
│   ├── policy.html       03 FIT/FIP・電力市場・出力制御
│   ├── finance.html      04 ファイナンス
│   ├── electrical.html   05 電気設備
│   ├── legal.html        06 法令・契約
│   └── glossary.html     07 用語集
└── assets/
    ├── css/style.css     デザイン（色・レイアウト）
    ├── js/main.js        ナビ・目次・用語検索などの動き
    └── img/hero.jpg      トップ画像
```

## ノートの追加方法

1. `notes/` にある既存ページ（例：`om.html`）をコピーして新しいファイルを作る
2. `<body data-page="…">` の値を新しいIDに変更
3. `assets/js/main.js` 冒頭の `PAGES` 配列に1行追加（メニューと前後リンクに自動反映）
4. 本文の `<section id="…"><h2>…</h2>…</section>` を書き換える（目次は自動生成）

## GitHub Pages での公開

1. GitHub でリポジトリを作成し、このフォルダの内容を push
2. リポジトリの **Settings → Pages** を開く
3. **Source: Deploy from a branch**、**Branch: `main` / `(root)`** を選んで Save
4. 数分後に `https://<ユーザー名>.github.io/<リポジトリ名>/` で閲覧可能

## 注意

制度・法令は改正されます。実務では必ず最新の一次情報を確認してください。
