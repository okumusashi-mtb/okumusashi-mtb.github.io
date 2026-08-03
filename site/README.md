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

ビルド時間のほとんどは写真 929 枚から WebP 2608 個を生成する処理（キャッシュ無しで約 2 分）。
Astro はこの変換結果を `node_modules/.astro` に貯めるが、CI では `npm ci` が
`node_modules` ごと作り直すため、`actions/cache` で `npm ci` の**後に**復元している。
キーは写真・`package-lock.json`・`astro.config.mjs` のハッシュで、`restore-keys` により
写真を追加しても既存分は再変換されない。写真に変更が無ければビルドは 5 秒程度で終わる。

`astro.config.mjs` の `base` を変えると出力ファイル名のハッシュが全て変わり、
キャッシュが総入れ替えになる（＝そのビルドだけは遅くなる）。

GitHub Actions の Node 20 ランタイムは 2026 年秋に撤廃予定。使っている action は
2026-08 に checkout v7 / setup-node v7 / cache v6 / upload-pages-artifact v5 /
deploy-pages v5 へ更新済み。`upload-pages-artifact` は v4 でドットファイルを
成果物に含めなくなったが、`dist/` に該当が無いため影響しない。

## ホスティングの比較（2026-08 時点）

本番は GitHub Pages。比較のため Firebase Hosting と Cloudflare Pages にも
手動でデプロイした。**どちらも自動デプロイは設定していないので内容は凍結している。**
URL を案内するときは必ず `https://okumusashi-mtb.github.io/` を使うこと。

| URL | 位置づけ |
|---|---|
| <https://okumusashi-mtb.github.io/> | **本番**。`main` への push で自動更新 |
| <https://omcweb.pages.dev/> | Cloudflare Pages（試用、手動） |
| <https://okumusashi-mtb.web.app/> | Firebase Hosting（試用、手動） |

同じ成果物が 3 か所にあるので、検索エンジンから重複コンテンツと見なされないよう
`Base.astro` で canonical タグを出している。`astro.config.mjs` の `site` を基準に
絶対 URL を埋めるため、どこから配信されても正規版 (GitHub Pages) を指す。
ミラーの URL を README や外部に書いても、正規版が優先される。

`404.astro` が無かった頃は、Cloudflare Pages だけが存在しないパスにトップページを
200 で返していた (GitHub Pages と Firebase は既定の 404)。自前の 404 ページを
用意して 3 か所とも揃えてある。404 は `noindex` とし canonical は出さない。

### 1 ページあたりの転送量（実測）

`srcset` と `sizes` からブラウザが選ぶ版を再現して計測した値。全部スクロールした場合。

| ページ | PC 1x | PC 2x / スマホ |
|---|---|---|
| トップ | 0.29 MB | 1.10 MB |
| **活動アーカイブ** | **3.21 MB** | **11.51 MB** |
| 活動詳細（写真 10 枚） | 0.27 MB | 1.10 MB（拡大すると +0.5MB/枚） |

活動アーカイブは 147 件の表紙写真を 1 ページに並べるため突出して重い（`loading="lazy"`
なので、最下部までスクロールした場合の値）。

かつては PC 1x 以外の全端末が 17.25MB を読んでいた。`ActivityCard` の候補が
`[400, 800]` の 2 段しかなく、DPR 2 以上では必ず 800px 版が選ばれていたため。
候補を `[320, 480, 640]` に刻み、`sizes` を実レイアウト（PC でカード 320px、
`max-w-5xl` を 3 列 + `gap-4`）に合わせて 33% 削減した。画質は落としていない。

さらに減らすなら quality を 80 → 70 にすると 9.52MB になるが、精細度より先に
色差成分が粗くなり彩度が落ちて見えるため採用していない。ページ分割や
年の折りたたみも案としてはある。

### 無料枠の比較

最右列は「アーカイブページをスマホで最後までスクロール（11.51MB）」を何回まかなえるか。

| | 転送量 | 超過時 | サイト容量 | ファイル数 | 換算 |
|---|---|---|---|---|---|
| **Cloudflare Pages** | 記載なし（実質無制限） | — | 記載なし | 20,000 | 事実上無制限 |
| **GitHub Pages**（本番） | 100GB/月（ソフト） | 警告 | **1GB** | — | 約 290 回/日 |
| **Netlify** | 300 クレジット ≒ 15GB/月 | 停止 | 記載なし | — | 約 43 回/日 |
| **Firebase** Spark | **360MB/日** | **配信停止** | 10GB | — | 約 31 回/日 |
| **Vercel** Hobby | 100GB/月 | 停止 | **CLI 100MB** | 15,000 | — |

- **Vercel はデプロイ自体が不可**。Hobby は CLI アップロードが 100MB までで、
  537MB の `dist/` は送れない。加えて Hobby は Git 組織所有のリポジトリに接続できない
- **Netlify も Firebase 並みに厳しい**。15GB/月 は乗り換え先として意味がない
- **移行するなら Cloudflare Pages**。ただし現状 GitHub Pages で困っていない

### いつ移行を検討するか

GitHub Pages の**サイト容量 1GB は明示的な上限**で、超えると公開できない。
写真は直近 7 年で年 110〜130 枚増えており（ビルド出力で年 +70MB）、
現在 537MB から**約 7 年で到達**する。その時が移行の検討時期。

なお移行しても GitHub **リポジトリ**側の制約は残る（写真の原本 451MB がコミット済みで、
削除しても git 履歴からは消えない）。ただしリポジトリの 1GB は単なる推奨値で、
実質的な天井である 5GB までは現在のペースで約 80 年ある。
つまり移行によって「7 年後のハードな壁」が「遠い先の推奨値」に変わる。

### Firebase Hosting

設定はリポジトリ直下の `firebase.json` と `.firebaserc`（プロジェクト `okumusashi-mtb`）。

```bash
make site-build
firebase deploy --only hosting --project okumusashi-mtb
```

止めるときは `firebase hosting:disable`（URL は残り「Site Not Found」を返す。
再開は再デプロイのみ）。

### Cloudflare Pages

プロジェクト名 `omcweb`（アカウントは `kaz@utashiro.com`）。設定ファイルは不要で、
`wrangler` から出力ディレクトリを直接送る。

```bash
npm install -g wrangler && nodenv rehash   # 初回のみ
wrangler login                             # 初回のみ（ブラウザ認証）
make site-build
wrangler pages deploy site/dist --project-name omcweb --branch main
```

2811 ファイルのアップロードで 34 秒。デプロイ直後の 20 秒ほどは一部のパスが
522 を返すことがあるが、エッジへの伝播が終われば解消する。

`firebase.json` の `Cache-Control` 設定は Cloudflare には効かない。同等のことを
するなら `public/_headers`（ビルド出力にそのままコピーされる）に書く。
本番にするなら GitHub 連携で自動デプロイに切り替えること。

## 主な構成

| 場所 | 内容 |
|---|---|
| `src/data/activities.ts` | 活動データ層（events×archive を記事 URL で結合、写真名の解決、slug 生成） |
| `src/lib/photos.ts` | 取り込み済み写真の解決（`getPhoto`） |
| `src/components/` | `ActivityCard` / `PhotoGrid` / `Lightbox` など |
| `src/pages/` | `index` / `activities`（一覧・`[slug]` 詳細）/ `about` / `404` |
| `src/layouts/Base.astro` | 共通レイアウト（canonical タグ、`noindex` 指定） |
| `src/assets/photos/` | 取り込んだ写真（ビルドで WebP 最適化） |
| `scripts/fetch-photos.mjs` | ブログ画像の取り込み |
| `src/data/activities.test.ts` | データ層のテスト（vitest） |

全体像（この保管庫の目的やカレンダーとの関係）は、リポジトリ直下の `../README.md` を参照。
