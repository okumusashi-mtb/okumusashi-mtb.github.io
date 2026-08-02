# site/ — 奥武蔵マウンテンバイク友の会 ウェブサイト

会の活動記録を公開するウェブサイト（<https://okumusashi-mtb.github.io/>）のソース。
Astro + Tailwind CSS の静的サイトで、リポジトリの活動データ（`../calendar/`）から
トップ・活動一覧・活動詳細・会について のページを生成する。

## 何が見られる

- **トップ**: 会の紹介、最近の活動、Google カレンダー（今後の予定）の埋め込み
- **活動アーカイブ**: 全活動を年別に一覧（種別フィルタ付き）。写真の無い活動は会のロゴを表示
- **活動詳細**: お知らせ／報告ごとの本文（段落・字下げを保持）と写真（クリックで拡大・前後送り）
- **会について**: 会の説明・活動エリア

## データの出どころ

- 活動・記事・写真リンク: `../calendar/events/` と `../calendar/sources/blog/`（canonical データ）
- 写真の実体: `src/assets/photos/`（`scripts/fetch-photos.mjs` でブログから取り込み済み。ビルド時に WebP 最適化）
- 今後の予定カレンダー: Google カレンダー `okumusashi.mtb@gmail.com` の公開埋め込み（ブラウザがライブ読み込み）

## 開発・ビルド

Node は nodenv 管理、`../.node-version` = 22.22.2（Astro 7 は Node ≥22.12 が必要）。
リポジトリ直下の `make` が便利：

```bash
make site-dev      # ローカルで開発表示（http://localhost:4321/）
make site-build    # 本番ビルド（site/dist/ に出力）
make site-photos   # 不足している写真をブログから取り込む
```

`site/` 内で直接 `npm run dev` / `npm run build` / `npx vitest run` も可。

## 公開（デプロイ）

`main` に push すると GitHub Actions（`../.github/workflows/deploy-site.yml`）が
Node 22.22.2 でビルドし、GitHub Pages（ルート `/` 配信）へ自動公開する。
リポジトリ名が `okumusashi-mtb.github.io` であることがルート配信の条件なので、
名前を変えると公開 URL がサブパスに落ちる。

ビルド時間のほとんどは写真 929 枚から WebP 2488 個を生成する処理（キャッシュ無しで約 2 分）。
Astro はこの変換結果を `node_modules/.astro` に貯めるが、CI では `npm ci` が
`node_modules` ごと作り直すため、`actions/cache` で `npm ci` の**後に**復元している。
キーは写真・`package-lock.json`・`astro.config.mjs` のハッシュで、`restore-keys` により
写真を追加しても既存分は再変換されない。写真に変更が無ければビルドは 5 秒程度で終わる。

`astro.config.mjs` の `base` を変えると出力ファイル名のハッシュが全て変わり、
キャッシュが総入れ替えになる（＝そのビルドだけは遅くなる）。

### Firebase Hosting（試用、本番ではない）

比較のため Firebase Hosting へ手動で 1 度デプロイした。設定はリポジトリ直下の
`firebase.json` と `.firebaserc`（プロジェクト `okumusashi-mtb`）。

```bash
make site-build
firebase deploy --only hosting --project okumusashi-mtb
```

**自動デプロイは設定していない**ので、`https://okumusashi-mtb.web.app/` の内容は
最後に手動デプロイした時点で止まっている。公開しているのは GitHub Pages 側なので、
URL を案内するときは `https://okumusashi-mtb.github.io/` を使うこと。

常用しない理由は無料枠の転送量。Spark プランの上限は **360MB/日**で、しかも超過時は
課金ではなく配信停止になる。このサイトは写真 1 枚が 500KB 前後あり、活動詳細ページを
数十回表示しただけで到達する。GitHub Pages は 100GB/月（ソフトリミット）なので桁が違う。
Firebase に寄せるなら Blaze プランへの変更が前提。

止めるときは `firebase hosting:disable`（URL は残り「Site Not Found」を返す。
再開は再デプロイのみ）。

## 主な構成

| 場所 | 内容 |
|---|---|
| `src/data/activities.ts` | 活動データ層（events×archive を記事 URL で結合、写真名の解決、slug 生成） |
| `src/lib/photos.ts` | 取り込み済み写真の解決（`getPhoto`） |
| `src/components/` | `ActivityCard` / `PhotoGrid` / `Lightbox` など |
| `src/pages/` | `index` / `activities`（一覧・`[slug]` 詳細）/ `about` |
| `src/layouts/Base.astro` | 共通レイアウト |
| `src/assets/photos/` | 取り込んだ写真（ビルドで WebP 最適化） |
| `scripts/fetch-photos.mjs` | ブログ画像の取り込み |
| `src/data/activities.test.ts` | データ層のテスト（vitest） |

全体像（この保管庫の目的やカレンダーとの関係）は、リポジトリ直下の `../README.md` を参照。
