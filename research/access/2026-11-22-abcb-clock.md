# 2026-11-22 輸送介入と根の時計：公開資料へのアクセス記録

## 1. この記録の範囲

**Berg2021のPrimingRoot原著コード・個体別データ、Santos Teixeira2022のPBSroot原著コードは、今回の追加探索でも取得できていない。** 配布先への接続失敗や検索の無ヒットは、資料や別の公開経路が存在しないことを示さない。今回の作業は公開資料の取得可能性の確認であり、原著モデルの実行、新しい数値解析、原著モデルの再現成功を報告するものではない。

以前のHTTP/HTTPS・大学ホスト別名の取得試行は、[前回のアクセス記録](2026-11-22-reflux-clock.md)に残している。同じ失敗要求を一括して繰り返さず、今回確認した別の入口と、新たなファイル直リンクを以下に記録する。既存の実験結果・コードは変更していない。

Chen et al. (2023), *ABCB-mediated shootward auxin transport feeds into the root clock*, DOI [10.15252/embr.202256271](https://doi.org/10.15252/embr.202256271)、[PMC10074126](https://pmc.ncbi.nlm.nih.gov/articles/PMC10074126/)の本文・付属source dataは通常の公開経路から取得できた。取得記録を第6節に統合した。原著コードが未取得であることと、別の生体研究の公開観測表を取得できたことは分けて記録する。

## 2. 原著と公式配布先の対応

| 原著 | 原著・公式研究室ページが案内する配布先 | 今回の状態 |
|---|---|---|
| van den Berg et al. (2021), *A reflux-and-growth mechanism explains oscillatory patterning of lateral root branching sites*, [DOI:10.1016/j.devcel.2021.07.005](https://doi.org/10.1016/j.devcel.2021.07.005) | [PrimingRoot](http://bioinformatics.bio.uu.nl/khwjtuss/PrimingRoot)。「コードとデータ」を案内 | 本文・補足PDFは前回取得済み。原著コード・個体表は未取得 |
| Santos Teixeira et al. (2022), *Complementary roles for auxin and auxin signalling revealed by reverse engineering lateral root stable prebranch site formation*, [DOI:10.1242/dev.200927](https://doi.org/10.1242/dev.200927)、[PMC9793420](https://pmc.ncbi.nlm.nih.gov/articles/PMC9793420/) | [PBSroot](https://tbb.bio.uu.nl/khwjtuss/PBSroot/)。「図のシミュレーションに必要なコード」を案内 | 公式ディレクトリの検索索引に原版候補のZIP名を確認。ZIP本体は未取得 |

大学の[Source codesページ](https://tbb.bio.uu.nl/khwjtuss/sourcecode.html)の検索索引は、2021年Developmental CellのPrimingRootと2022年DevelopmentのPBSrootを別の項目として挙げている。PBSrootを2021年版の同一コードとして扱わない。

## 3. 今回の追加経路と結果

### 3.1 PBSrootの原版候補アーカイブ

[公式ディレクトリ](https://tbb.bio.uu.nl/khwjtuss/PBSroot/)の検索索引は、`PBSroot.zip`、更新表示`2022-09-08 09:02`、サイズ表示`178K`を掲載している。ここから得たファイル名で、次の公開直リンクを1回要求した。

| 項目 | 記録 |
|---|---|
| URL | <https://tbb.bio.uu.nl/khwjtuss/PBSroot/PBSroot.zip> |
| 要求開始（UTC） | 2026-11-22 05:54:18.841526 |
| 要求終了（UTC） | 2026-11-22 05:54:26.703980 |
| 結果 | `HTTPError: HTTP Error 503: Service Unavailable` |
| 保存したコード | なし |
| アーカイブのハッシュ・内容・ライセンス | 未確認。取得失敗のため推測で補わない |

ディレクトリ自体をブラウズ用取得サービスで開いた際もタイムアウトした。公式一覧の検索索引が読めたことと、ZIPを取得できたことは区別する。

同じ索引には2024–2026年の更新表示を持つ`PBSroot_extended/`、輸送流入係数を変えた名前のkymograph・計算フォルダ、`src/`等もある。ただし索引の更新表示は版の証明ではなく、2022年論文のどの図と対応するかも未確認である。これらを原著データとして取得・分析していない。

### 3.2 著者関連GitHubと公開リポジトリ検索

検索から[ kirstentt/-un-likelyclocks ](https://github.com/kirstentt/-un-likelyclocks)を発見した。READMEはKirsten ten Tusscherによる2026年Plant Cell論文 *The (un)likelihood of clock driven lateral root priming; A modeling exploration* のコードと記載する。**2021年PrimingRootや2022年PBSrootと同一の配布物ではない**。今回は入口の記録に留め、アーカイブ取得・実行を行っていない。

公開APIで`kirstentt`のリポジトリ一覧を取得できた。この一覧には4件（`-un-likelyclocks`、`cambium_static`、`flooding-stress`、`regeneration_rhomboids`）があり、PrimingRoot/PBSrootという名前のリポジトリは含まれていなかった。これは当該アカウントの当該時点の公開一覧についての結果であり、他の作者・別名・非公開資料まで調べたことを意味しない。

| 公開API要求 | 開始・終了（UTC） | 応答 |
|---|---|---|
| <https://api.github.com/users/kirstentt/repos?per_page=100> | 05:54:39.713691–05:54:44.744191 | HTTP 200、22,443 bytes、公開リポジトリ4件 |
| <https://api.github.com/search/repositories?q=PrimingRoot&per_page=10> | 05:55:03.629514–05:55:07.860766 | HTTP 200、`total_count: 0` |
| <https://api.github.com/search/repositories?q=PBSroot&per_page=10> | 05:55:08.861671–05:55:13.213024 | HTTP 200、`total_count: 0` |
| <https://api.github.com/search/repositories?q=%22reflux-and-growth%22&per_page=10> | 05:55:14.213337–05:55:18.781231 | HTTP 200、`total_count: 0` |

一覧応答のSHA-256は`e86fe489655d3e1943c6e007a966dfa4a0b95d34ce475238f3e9ebfa1a253675`。このハッシュはGitHubのAPI応答に対するもので、原著コードのハッシュではない。検索APIはリポジトリ検索であり、認証が必要なGitHub全体のコード検索を実行したものではない。

`PrimingRoot`、`PBSroot`、原著DOI・著者名とGitHub/Zenodoを組み合わせた公開ウェブ検索、大学研究ポータル・学位論文の記載も確認したが、原著と同一と確認できる追加ミラーは見つからなかった。[Utrecht原著ページ](https://research-portal.uu.nl/en/publications/a-reflux-and-growth-mechanism-explains-oscillatory-patterning-of-/)と[UGent原著ページ](https://biblio.ugent.be/publication/8717001)は本文PDFへの入口であり、今回確認できた範囲では個体表や原著コードの別公開URLを提供していない。Zenodo検索の無ヒットも不存在の証明とはしない。

## 4. 現時点で利用できるBerg2021の公開図・時系列

以下は前回取得済みの原著本文・14ページの補足PDFで確認できる資料である。**今回は新しく読み取り値を採点したり、データ点を抽出したりしていない。** 本文・補足の取得URLとハッシュは[前回記録](2026-11-22-reflux-clock.md)を参照。

| 公開箇所 | 得られる情報 | 利用上の限界 |
|---|---|---|
| 原著Fig.1、補足Fig.S1C/D（補足PDF p.3） | auxin供給の低下・reflux設定変更に対応するシミュレーションのauxin分布とkymograph | 図画像であり生の計算時系列ではない。S1Dの色範囲はシミュレーションごとに変更されているため、見た目の色を共通の絶対振幅として比較できない |
| 原著Fig.4、補足Fig.S3（p.5） | 分裂率・meristemサイズ等と周期/空間間隔の関係、伸長率に関するシミュレーション | 公開された既存のモデル出力。コードなしで新しい介入条件を実行したとはいえない |
| 原著Fig.6/7、補足Fig.S4/S5（p.6–8） | 104根の実測分布・相関、4処置の色分け（control 30、GA 26、低BR 31、高BR 17） | 同じ原著データの複数表示であり独立標本を加算しない。個体IDを結ぶ元の表は未取得 |
| 補足Fig.S6A–G（p.9–10） | 18時間の実測kymograph例、成長・部位間隔・周期の測定線、強度traceの例 | 例示1図から全104根の生時系列は復元できない。原著は根ごとに輝度設定を調整し、振幅について結論・解析を行っていないと記すため、群間の実測絶対振幅の比較には不足する |

PrimingRootの実行依存について、原著本文はC++、auxin輸送の半陰的積分、当時の計算時間等を説明する。しかしコード・Makefileを取得していないため、必要なコンパイラ版、外部ライブラリ、実行手順、ライセンスや固定版を確定できない。「C++と記載されている」ことを、この環境でコンパイル・再現可能と確認したことへ読み替えない。

## 5. 記録の保存と次段階

今回の取得ログとGitHub API応答は一時作業ディレクトリ`/tmp/torus-original-code-access-20261122/`に保存した。これは本リポジトリに同梱した原著コード・データではない。主要な試行結果・時刻・API応答のハッシュは上記に転記した。

- 新しいコードを実行していない。別の研究用コードを原著モデルとして置き換えていない。
- 認証回避・著者への連絡は行っていない。
- 原著コードが未取得という制約を維持し、次の研究対象は取得と対応確認のできた生体の輸送介入データから選ぶ。
- Chen2023のsource dataを取得し、表の構造と図との対応を確認した。取得済みの原本と、新しい効果量の解析、原著実験の再現を混同しない。

## 6. Chen2023：本文・付属観測表の取得成功

取得日はすべて2026-11-22。下表の時刻はUTCの要求開始時刻。全URL・HTTP応答・byte数・SHA-256・ZIP内部ファイルのSHA-256は [chen2023_manifest.json](../sources/chen2023_manifest.json) に記載した。通常の匿名GETがHTTP 200で成功し、本文はPDFとして、Excel/ZIPはOOXML・ZIPとして内容を確認した。

| 保存名 | 要求開始UTC | bytes | SHA-256 |
|---|---|---:|---|
| `abcb.pdf` | 05:53:14.434287 | 3,345,899 | `795f822ed3fd37992cbeaa39a13fd3171f1e28d006e60342a08bf1dee669a228` |
| `abcb_appendix.pdf` | 05:54:55.050070 | 3,181,019 | `f6e3e3b03658745f9dc3421d4b0f3b2148c7327ca5918c09af952bcd0a3d4943` |
| `abcb_appendix_data.zip` | 05:54:55.050841 | 11,265,445 | `50372230d93b67ce57600d55ced0de7c20b3e81b3f08eaf8bb2eaf3dbcf114fe` |
| `abcb_fig2.xlsx` | 05:54:55.051698 | 20,644 | `8f12998383b368adeb33db2f0de497bb1f6f1f7c4804863f2286bd4ba789b059` |
| `abcb_fig4.zip` | 05:54:55.052538 | 1,629,448 | `e24bf364680d68a41551b9a480e3b0496c4147d3464ae078d3c0bad82d2d0108` |
| `abcb_fig6.xlsx` | 05:55:07.318103 | 18,327 | `afe491baa0888b5e4f74971bf8cd672c8d29485ee88b892b5c0143d908e8592e` |

本文は[著者所属大学の公開PDF](https://escholarship.org/content/qt7dk806pr/qt7dk806pr_noSplash_cd5a588c61ba6269e9b00b32ce9bfbad.pdf)を利用した。付属資料は[出版社ページのSupplementary Information](https://link.springer.com/article/10.15252/embr.202256271)から得た公開リンクを使用した。出版社の本文previewが購読案内を表示することと、付属source dataが公開ダウンロード可能であることは両立する。購入・認証回避は行っていない。

本文PDFは16ページ、Appendixは17ページ。Fig2/6は各1sheetで、`Figure 2` / `Figure 6`。Fig4のZIPは `Figure 4.xlsx` と6枚のCZI、Appendix ZIPはS1/S2/S3/S4/S6/S8/S9の7 workbooksを含む。Fig4の内部sheetは `Figure 4` で、`4A` はパネル名である。全生ファイルとアクセスログは一時作業先 `/tmp/torus-clock-candidates-20261122/` に保存し、Gitには同梱していない。

原本を変更せず、XMLでsheet・見出し・セル範囲・型・値数を確認し、本文PDF p5/p10の図をrenderして目視照合した。周期の値数がcaption nより多く、振幅も一部でcaption nと違う。根・イベント・batch IDは公開された時計表から回復できない。Fig4Aの3/3/4/3値はpoolされた根の本数を示さず、Chen本文はpool本数・根年齢・assay待機時間を明示していない。測定の意味と正確な抽出範囲は [source構造監査](../notes/chen_2023_source_schema.md) にまとめた。

### 取得できなかった入口と権利

- PMCのブラウズ入口がrobot確認画面を返した経路は、それ以上操作していない。大学PDFと出版社の公開付属資料という別の通常経路を利用した。
- Europe PMCの `https://www.ebi.ac.uk/europepmc/webservices/rest/PMC10074126/fullTextXML` は05:54:21.947324 UTCの試行でHTTP 500。
- `https://www.ncbi.nlm.nih.gov/pmc/utils/oa/oa.fcgi?id=PMC10074126` と `https://pmc.ncbi.nlm.nih.gov/utils/oa/oa.fcgi?id=PMC10074126` は、05:53:14.436205 / 05:54:21.954702 UTCの試行でHTTP 404。API入口の応答は、論文の非存在や非公開を示すものではない。
- PMC公開S3 bucketで `PMC10074126.1/` prefixを調べた応答は0件だった。別版・別入口まで存在しないとは解釈しない。
- 出版社Rights欄では著者copyrightを確認したが、今回の生ファイル群の再配布に適用できる明示ライセンスは確定していない。公開URLへのアクセス、内部読解、派生的な構造メタデータの記録と、生ファイルの再配布は分ける。

本文のData availabilityに外部repositoryへのdepositがないと書かれることは、出版社付属の観測表が存在しないという意味ではない。本記録は「公開図だけ」から一段進んで元の数値表にアクセスできた証拠であり、原著の生体試験を新たに行った証拠ではない。

## 7. E79/E80の取得と再実行

集計に必要な原本はFig.2、Fig.4、Fig.6の3点。本文・Appendixは方法と単位を監査する資料であり、全原本6点を数値計算へ投入するわけではない。既存のPython依存をそろえ、次で公開原本の取得から再実行できる。

```bash
python -m pip install -r experiments/requirements.txt
python -m experiments.run_abcb_clock --cache /tmp/torus-chen2023-cache --out /tmp/torus-abcb-replay
cd /tmp/torus-abcb-replay
sha256sum -c ABCB_CLOCK_SHA256SUMS
```

各ダウンロードは固定したSHA-256に一致する場合だけ採用する。すでに取得済みのcacheだけを使う場合は `--offline`。URLの内容が変わりハッシュが異なる場合は停止し、新版を黙って混ぜない。cacheはGitの作業領域の外に置く。元のxlsx/zipは変更せず、出力は集計結果と対応セル、監査記録、独自の集計図に限る。

空のcacheと出力先を使った通常HTTPSからの再取得で3原本のハッシュが一致し、E79/E80・PNG/SVG・実行記録・SHA一覧の6ファイルが正式結果とバイト一致した。今回の入力・計算検算は23項目。Python 3.12.14、Matplotlib 3.10.8で確認し、異なる描画環境での画像のバイト一致までは保証しない。[実行記録](../results/ABCB_CLOCK_RUN.json)・[結果のハッシュ](../results/ABCB_CLOCK_SHA256SUMS)
