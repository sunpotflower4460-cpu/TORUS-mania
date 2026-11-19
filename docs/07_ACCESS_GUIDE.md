# 資料へのアクセス方法

更新日：2026-11-20。対象は `sources/catalog.json` に登録した公開資料です。

このリポジトリには、資料の索引、独自の短い要約、一次資料へのリンク、取得履歴を残すCLIを用意しています。論文の全文、動画本体、有料サービスの資格情報は同梱しません。資料を取得できたことと、その内容が仮説を支持することは別々に記録します。

## 1. 最初に、ネットワークなしで使う

Python 3.10以上があれば動きます。追加パッケージ、APIキー、新規の有料契約は不要です。リポジトリのルートで実行します。

```bash
python scripts/research_access.py list
python scripts/research_access.py show S001
python scripts/research_access.py list --json
python scripts/research_access.py search-url 'toroidal vortex branching' --provider arxiv
```

`S001` はIDの指定例です。まず `list` と `show` で、実際に読む資料のID、URL、支持できる主張、支持できない主張を確認してください。

`list --domain 分野名` はカタログの `domain` と一致する資料だけを表示します。分野名は `list --json` で確認できます。

`search-url` はURLを表示するだけです。ブラウザを開かず、検索も送信しません。生成したリンクを利用可能なブラウザや検索ツールへ渡します。

```bash
python scripts/research_access.py search-url 'quasiperiodic motion invariant torus' --provider arxiv
python scripts/research_access.py search-url 'auxin canalization feedback' --provider pubmed
python scripts/research_access.py search-url 'toroidal topology universe' --provider crossref
python scripts/research_access.py search-url 'vortex ring counterexample topology' --provider google-scholar
```

arXivとCrossrefは、少数の検索結果を返す公開APIのURLを生成します。PubMedとGoogle Scholarは閲覧用の検索ページです。Google Scholarの自動スクレイピングやCAPTCHA回避は行いません。

## 2. その実行環境で到達できるか確かめる

```bash
python scripts/research_access.py check --limit 3 --timeout 15
python scripts/research_access.py check --ids S001 S002 --limit 2
```

`check` はHEADリクエストだけを送り、HTTPヘッダを確認します。既定の上限は3資料、リクエスト間隔は最低3秒です。本文を取得しないため、成功は `reachable_headers_only` と記録します。

HEADを受け付けないサイトでは `method_not_supported` になります。CLIは勝手にGETへ切り替えません。本文を読む目的が明確で、公開取得の条件を満たす場合に、次節の `fetch` を個別に実行してください。

索引の `access_status: web_verified` は、準備時に検索・閲覧ツールで確認できたという意味です。**別のCodex環境のシェルからも接続できる保証ではありません。** CLIの実行結果は索引を自動で書き換えず、別の履歴に保存します。

## 3. 必要な資料だけ取得する

```bash
python scripts/research_access.py fetch S001 --timeout 15
python scripts/research_access.py fetch S001 --out data/raw --max-mb 10
```

明示した1資料だけをGETします。取得先は `automated_access_url` があれば優先し、それ以外は `open_access_url`、`url` を使います。ただしPMC記事については、後述のBioCに切り替えます。

既定の上限は10 MiBです。応答の `Content-Length` と実際に受信したバイト数を両方確認します。ファイルの先頭も検査し、PDFを名乗る応答にHTMLの案内ページが含まれていた場合、PDFとして保存しません。PDFの識別はファイルの先頭に基づくもので、全ページの正常性や本文の意味まで検証したことにはなりません。

保存先は `data/raw/S001.pdf`、`.html`、`.xml`、`.json`、`.txt` のいずれかです。同じファイルは既定で上書きしません。取り直しが必要な場合だけ、`--overwrite` を指定します。

取得した本文は、研究者が実際に開いて内容・版・著者・図・ライセンスを確認します。CLIは `full_text_reviewed: false` のまま記録します。要旨や入口ページだけを読んだ場合も、全文確認済みにはしません。

### PMC記事は専用APIを使う

PMC公式の開発者向け案内は、本文の自動取得経路をPMC Cloud、OAI-PMH、E-Utilities、BioCに限定しています。一般の論文HTMLをまとめてスクレイピングする経路は使いません。

- 公式案内：https://pmc.ncbi.nlm.nih.gov/tools/developers/
- BioCの仕様：https://www.ncbi.nlm.nih.gov/research/bionlp/APIs/BioC-PMC/
- BioCベースURL：https://www.ncbi.nlm.nih.gov/research/bionlp/RESTful/pmcoa.cgi

本CLIは、PMCIDまたはPMC記事URLから次の取得URLを作ります。

```text
https://www.ncbi.nlm.nih.gov/research/bionlp/RESTful/pmcoa.cgi/BioC_xml/PMC7116426/unicode
```

BioCの対象コレクションに含まれない記事や、APIから本文を取得できない場合は、`api_no_document` などとして記録します。**PMCで閲覧可能であること、API取得可能であること、再配布可能であることは同じではありません。** 全文が得られない場合も、書誌情報と閲覧用URLは索引に残します。

旧PMC OA Web Serviceは2026-08-25に廃止されたと公式に告知されています。このCLIは旧 `oa.fcgi` を使用しません。

- 廃止告知：https://pmc.ncbi.nlm.nih.gov/tools/oa-service/
- 現行OAI-PMH案内：https://pmc.ncbi.nlm.nih.gov/tools/oai/
- 現行OAI-PMHベースURL：https://pmc.ncbi.nlm.nih.gov/api/oai/v1/mh/

PMC記事の個別ライセンスは、取得後も確認が必要です。論文の全文をGitへ追加する操作は、本CLIにはありません。

## 4. 取得履歴の読み方

既定の履歴は `research/access/access-log.jsonl` です。1回の試行が1行のJSONになり、資料ID、実行日時（UTC）、元URL、実際の接続先、HTTP方式・ステータス、Content-Type、取得量、失敗理由などを保存します。ファイルを保存できたときは、そのパスとSHA-256も記録します。

| 状態 | 意味と次の行動 |
|---|---|
| `reachable_headers_only` | HEADに応答した。本文は読めていない。 |
| `payload_saved` | 応答データを保存した。研究者による本文確認は別に必要。 |
| `network_error` / `timeout` | ネットワーク経路、DNS、プロキシ、証明書、タイムアウトなど。資料の不存在を意味しない。 |
| `access_denied` / `authentication_required` | アクセスを拒否された。サイト側制限か実行環境側制限かは、この記録だけでは断定しない。 |
| `challenge_or_access_gate` | 応答にCAPTCHAやアクセス制限らしい文言がある。自動判定は疑いの検出であり、回避はしない。 |
| `not_found_at_url` / `gone_at_url` | そのURLが404/410を返した。別の版・DOI・著者原稿まで不存在とは言わない。 |
| `method_not_supported` | HEADを受け付けなかった。本文の有無は未確認。 |
| `rate_limited` | 429。`retry_after` を記録して処理を停止する。別のURLやアカウントに切り替えて制限を回避しない。 |
| `api_no_document` | BioCから文書を得られなかった。対象コレクションやAPI状態を確認する。 |
| `too_large` | 指定した取得上限を超える。必要性を確認してから上限を変更する。 |
| `output_exists` | 保存済みファイルを保護して停止した。必要時だけ明示的に上書きする。 |

履歴の保存先を変える場合は `--report パス` を指定します。CLIは自動再試行を行いません。429の待機時間などはサービスの案内に従い、人または実行担当が再開を判断します。

終了コードは、`0` がコマンド成功、`1` が到達確認・取得の未達、`2` が入力・索引・ローカル設定の問題です。ネットワーク未達を、研究仮説の否定や資料の不存在として数えないでください。

## 5. 別のCodex環境へ引き継ぐ際の確認

1. このリポジトリを取得し、`list` と `show` が動くか確認する。
2. 利用できる検索・閲覧ツール、シェルのネットワーク制限を実際に確認する。
3. `check --limit 1` を実行し、その環境の結果を記録する。
4. 読む順番を決め、必要な資料のみ個別取得する。
5. 見られない資料には代替URLや著者公開版を探し、未確認部分はそのまま残す。

ChatGPT側で利用できたGitHub、Web検索、vidIQなどのコネクタが、別のCodex環境にも自動で引き継がれるとは限りません。本CLIはそれらを呼び出さず、公開HTTP(S)と標準ライブラリだけを使います。環境固有の接続設定や権限を、このリポジトリから変更することもありません。

### 動画を扱う場合

動画のURL・タイトル、字幕、画面上の図、ナレーションの主張を区別します。この準備作業で動画解析サービスを使って得た内容は、そのサービスによる解析であり、研究担当者自身によるフレーム確認とは分けて記録します。

次のCodex環境で映像を取得できない場合は、利用可能な公式字幕、ユーザーが提供したスクリーンショットや短い引用、公開ページの説明を使います。字幕だけで視覚的な形や運動を確認したことにはしません。認証・有料化・第三者サービスのクレジット消費が必要なら、すでに与えられている権限と予算の範囲を確認します。本CLIに動画ダウンロードや有料解析は含みません。

動画は着想と主張を特定する資料です。物理現象の実証や、共通原理の検証は、対応する一次資料・観測・再現実験で進めます。

## 6. APIと索引の公式入口

| 入口 | 用途 | 公式資料 |
|---|---|---|
| DOI / Crossref | 書誌情報、出版情報、更新・ライセンス情報への手がかり。全文を保証しない。 | https://www.crossref.org/documentation/retrieve-metadata/rest-api/ |
| arXiv API | 論文の検索・メタデータ。査読済みかどうかは別途確認。 | https://info.arxiv.org/help/api/user-manual.html |
| PMC Developers | 自動取得できる経路と対象範囲。 | https://pmc.ncbi.nlm.nih.gov/tools/developers/ |
| BioC | 対象コレクションの機械可読本文。 | https://www.ncbi.nlm.nih.gov/research/bionlp/APIs/BioC-PMC/ |
| NCBI E-Utilities | PubMed/PMCなどのプログラム向けアクセス。 | https://www.ncbi.nlm.nih.gov/books/NBK25501/ |

APIごとの利用条件や制限は更新されます。大量取得を追加する前に、その時点の公式案内を読み直してください。現在のCLIは検索URLの作成と少数資料の個別アクセスに限定しています。

## 7. 検証

```bash
python -m unittest discover -s tests -v
```

テストはすべてオフラインです。外部サーバーをモックし、HEADの本文非取得、アクセス拒否と404の区別、タイムアウト、429、HTML/PDFの判別、容量上限、上書き保護、パストラバーサル、BioCの空応答、既定の件数制限を確認します。テスト合格は外部サイトの稼働保証ではありません。
