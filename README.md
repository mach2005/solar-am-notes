# Solar AM Notes ☀️

メガソーラーのアセットマネジメントを学ぶための個人学習ノートサイトです。
HTML / CSS / JavaScript のみで構成した静的サイトなので、GitHub Pages でそのまま公開できます。

## 構成

## 構成（全13テーマ・4大実務領域）

```
├── index.html            トップページ（体系別ナビ・ドメインフィルター搭載）
├── notes/
│   ├── 【⚡ 現場・技術・O&M】
│   │   ├── electrical.html   01 電気設備（構成・キュービクル・保安）
│   │   ├── om.html           02 O&M（運転保守・予防診断・遠隔監視）
│   │   ├── due-diligence.html 03 ファシリティDD・事故事例診断
│   │   └── denken.html       04 電験・主任技術者実務＆公式本試験
│   ├── 【📈 発電性能分析】
│   │   └── performance.html  05 発電性能分析（PR・損失ウォーターフォール・予実）
│   ├── 【🔋 制度・市場・蓄電池】
│   │   ├── policy.html       06 FIT/FIP・系統用蓄電池・出力制御
│   │   ├── ppa-market.html   07 PPA・電力市場取引・BESS併設
│   │   └── news.html         08 最新ニュース・政策動向（1日4回自動更新）
│   ├── 【⚖️ 金融・法務・事業性】
│   │   ├── finance.html      09 金融・ファイナンス（PF・DSCR/IRRシミュレーター）
│   │   ├── acts.html         10 メガソーラー重要法令詳解＆法令診断
│   │   ├── legal.html        11 契約・保険・土地権原実務
│   │   └── industry.html     12 業界マップ・企業カオスマップ
│   └── 【📖 実務リファレンス】
│       └── glossary.html     13 用語集（70+用語・リアルタイム検索）
└── assets/
    ├── css/style.css     デザイン（ドロップダウンナビ・ドメインバッジ・ダークUI）
    ├── js/main.js        階層型ナビ・トピックフィルター・目次・用語検索
    └── img/              実写スライド解説画像（Gemini Nano Banana 2.1等）
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
