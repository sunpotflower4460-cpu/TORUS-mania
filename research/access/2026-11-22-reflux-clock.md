# 2026-11-22 — 戻り輸送・成長周期モデルへの公開アクセス

対象：E77・E78の文献確認。記録日・時刻はUTC。外部への連絡、有料取得、認証、アクセス制御の回避は行っていない。取得したPDF・画像・原著本文はGitへ追加しない。

**Berg2021の本文・補足は取得できたが、配布先のC++コードと個体別データは未取得である。今回のE77・E78は原著細胞モデルの完全再現ではない。** 公開リンクが503だったことを、資料が存在しない証拠と解釈しない。

## 1. 取得できた資料

取得終了時刻はローカル保存ファイルのmtimeに基づく。最初の一部のHTTPログには開始時刻を保存していなかったため、mtimeを要求開始時刻としては扱わない。HTTP成功に加えてPDFを開けることを確認した。

| ID | 資料と版 | 状態 | バイト数 | PDFページ | 保存時刻UTC |
|---|---|---|---:|---:|---|
| A1 | Berg2021、大学公開accepted manuscript | HTTP 200、全文・Methods確認 | 905998 | 34 | 2026-11-22 04:33:19 |
| A2 | Berg2021、出版社の補足mmc1 | HTTP 200、図・パラメータ確認 | 14645547 | 14 | 2026-11-22 04:35:12 |
| A3 | van den Berg博士論文、大学公開版 | HTTP 200、対象の第3–4章を確認 | 13652895 | 206 | 2026-11-22 04:35:24 |
| A4 | Mellor2020、PMC公開補足 | HTTP 200、方程式・定常解法確認 | 51245953 | 36 | 2026-11-22 04:38:19 |
| A5 | De Gernier2025、大学公開accepted manuscript | 同日のレビューで取得した実ファイルを再確認 | 2138721 | 27 | 2026-11-22 04:23:47 |
| A6 | De Gernier2025、大学公開補足 | 同日のレビューで取得した実ファイルを再確認 | 2058719 | 20 | 2026-11-22 04:23:47 |

### A1：Berg本文

- 公開元：[Ghent University](https://biblio.ugent.be/publication/8717001)
- 要求URL：<https://biblio.ugent.be/publication/8717001/file/8717002.pdf>
- 最終URL：<https://backoffice.biblio.ugent.be/download/8717001/8717002>
- SHA-256：`83a9c7d2af218b18d5945e04ca223f394810ce76c1913436d10b000d79c8d7bc`
- 大学メタデータではaccepted manuscriptが公開され、別の出版版は大学向けアクセスとされる。今回は公開accepted版を利用。再配布ライセンスの個別確定はしていない。

### A2：Berg補足

- URL：<https://ars.els-cdn.com/content/image/1-s2.0-S153458072100561X-mmc1.pdf>
- SHA-256：`9359b942101d1e6248981952ed24d4f4d2cc67a3e9ee9acf81ef4ccbe01f06ba`
- Fig.S1–S7、パラメータ表、測定方法図を含む。本文accepted版の補足番号と一部異なるので、文献メモでは取得した補足に印刷された番号を用いた。
- 出版社の公開取得が成功した段階。Gitへの再配布権は別途確認が必要。

### A3：著者博士論文

- 要求URL：<https://dspace.library.uu.nl/bitstream/handle/1874/420792/T%20%20van%20den%20Berg%20-%20thesis.pdf?sequence=1>
- 最終URL：<https://dspace.library.uu.nl/server/api/core/bitstreams/04f773be-6820-463a-9cbd-01576ef2b2b3/content>
- SHA-256：`db3bf832c31f89237d2172452bb1ad3c9968e667c6e300d76ddf8fb5a0990e32`
- 第3章はBerg2021に対応。第4章は同じ実験データの再解析と明記される（PDF p.100）。別の独立生体データとして追加しない。論文の全文複製やコードの取得とは別段階。

### A4：Mellor補足

- URL：<https://pmc-oa-opendata.s3.amazonaws.com/PMC7132777.1/develop-147-181669-s1.pdf>
- SHA-256：`0ef964c94f1eef7b1c8f0d9a21192de7ce17978dad772b80cd83fadd80b480d9`
- 先に30MBの読取り上限で中断。HEADで`Content-Length = 51245953`を確認し、2026-11-22 04:38:11 UTCに開始した二回目の要求で全体を取得した。中断時の部分バイト列のハッシュは完全なPDFのハッシュとして使用しない。
- 補足pp.S1–S5にOpenAlea系のPython実装、輸送方程式、線形系の定常解法が記載される。コードの全文・原著ソースコードへの配布URLは、この補足からは確認できなかった。コードが非公開だとは断定しない。
- PMCの公開ファイルへの取得成功。個別ライセンスを照合した再配布は未実施。

### A5・A6：De Gernier本文・補足

- 本文URL：<https://biblio.ugent.be/publication/01K47A0QNA2VHHET9FD517S20G/file/01K47CJF9R1X89CRS2EQVDNXRH.pdf>
- 本文SHA-256：`4e713e031c5fdd820a0f1c5d5e6c5d95609661b2ae5b5078a0f9f66ca32e4ff9`
- 補足URL：<https://biblio.ugent.be/publication/01K47A0QNA2VHHET9FD517S20G/file/01K47CPPCZDZ6GK9Q2DTNWX610.pdf>
- 補足SHA-256：`edd903540832cd25c2c9910f0f120c765d65d578ac5bde081e265111885ddb27`
- 今回は同日取得済みの実ファイルを再精読し、ハッシュを再計算した。再HTTP取得したと記録しない。
- 本文p.21のData availabilityは著者への合理的な依頼による提供を案内する。公開個体別データのURLはそこで示されない。補足Table S5にはImageJマクロがあり、入力画像から根Label、ピークID、時刻等を出力する。**マクロが読めることと、その入力画像・出力CSVを取得したことは別**。原画像・CSVは未取得、著者への依頼はしていない。再配布ライセンスの個別確定は未実施。

## 2. 原著コード・個体データの入口と今回の失敗

Berg2021のData and Code Availabilityは、コードとデータを次の大学ディレクトリで公開すると記載する。大学のsourcecodeページの検索索引にもPrimingRoot-codeが載っている。実際の取得要求は下表の結果となった。

| 2026-11-22 UTCに要求したURL | 結果 | 段階 |
|---|---|---|
| <http://bioinformatics.bio.uu.nl/khwjtuss/PrimingRoot> | HTTP 503 | コード・個体表とも未取得 |
| <https://bioinformatics.bio.uu.nl/khwjtuss/PrimingRoot> | HTTP 503 | 同上 |
| <https://bioinformatics.bio.uu.nl/khwjtuss/PrimingRoot/> | HTTP 503 | 同上 |
| <https://theory.bio.uu.nl/khwjtuss/PrimingRoot/> | HTTP 503 | 公式大学ホストの別名を試したが未取得 |
| <https://bioinformatics.bio.uu.nl/khwjtuss/sourcecode.html> | HTTP 503 | 実ページ取得失敗。検索索引は取得できた |
| <https://theory.bio.uu.nl/khwjtuss/sourcecode.html> | HTTP 503 | 同上 |
| <https://tbb.bio.uu.nl/khwjtuss/PrimingRoot> | HTTP 503、開始04:39:46 UTC | 後続論文が使う公式ホスト名でも未取得 |

最初の6件は日付は確認できるが、要求開始の時分秒はログに残していない。取得していないコードの版・ハッシュ・ライセンス・実行結果を推定で埋めない。検索で原著と同一と確認できるGitHubミラーは見つけられなかったが、ミラーの不存在を証明したわけではない。

## 3. 関連コードの確認

| 関連資料 | 確認できたこと | 実取得・使い分け |
|---|---|---|
| Santos Teixeira et al. 2022、[PMC9793420](https://pmc.ncbi.nlm.nih.gov/articles/PMC9793420/) | Data availabilityに[大学PBSroot](https://tbb.bio.uu.nl/khwjtuss/PBSroot)を記載。成長モデルに信号の保持過程を加えた後続研究 | 2026-11-22 04:39:46 UTCのGETは503。コード未取得・未実行。Berg2021の同一版として扱わない |
| Band2021、[DOI 10.1111/nph.17517](https://doi.org/10.1111/nph.17517) | 出版社索引に5.1KBのPython補足`nph17517-sup-0001-NotesS1.py`を記載 | 出版社の補足URLを試したが403。これはレビュー中の簡易例で、Mellor2020の全根モデルのソースではない |
| De Gernier2025、A6 | Table S5のImageJマクロ本文を実際に読める | 取得済みのPDF内。実行・抽出コードの再配布はしていない。root Labelとpeak ID等の対応仕様は確認できる |

Band補足の試行URL：<https://nph.onlinelibrary.wiley.com/doi/suppl/10.1111/nph.17517/supinfo/nph17517-sup-0001-notess1.py>。開始2026-11-22 04:39:46 UTC。ファイル名は出版社の索引に基づき、補足URLの形式を組み立てたため、403からファイルの不存在は判断できない。

## 4. その他の失敗・未完了を残す

| URL | 結果と扱い |
|---|---|
| <https://journals.biologists.com/dev/article-pdf/147/6/dev181669/1971608/dev181669.pdf> | 403。Mellor本文PDFをこの経路では取得できず |
| <https://nottingham-repository.worktribe.com/preview/4045636/dev181669.full.pdf> | 403。大学リポジトリ経由も取得できず |
| <https://www.ncbi.nlm.nih.gov/research/bionlp/RESTful/pmcoa.cgi/BioC_xml/PMC7132777/unicode> | 429。連続再試行せず終了 |
| <https://www.ebi.ac.uk/europepmc/webservices/rest/PMC7132777/fullTextXML> | 500。XML取得できず |
| <https://pmc-oa-opendata.s3.amazonaws.com/PMC7132777.1/develop-147-181669.pdf> | 推定した本文ファイル名では404（開始04:38:11 UTC）。本文が存在しないという意味ではない |
| <https://ars.els-cdn.com/content/image/1-s2.0-S153458072100561X-mmc2.pdf> | 推定した追加補足PDF名では404。mmc1は取得成功。別の拡張子の補足動画等の有無はこの試行では判断しない |

以上はすべて2026-11-22 UTCの要求。Mellor本文の一部は公開検索索引で読めたが、今回確認した線形モデル・定常解という判断は、実取得したA4の方程式・解法に基づく。

## 5. 権利・再現・保存の段階

1. **所在確認**：論文・大学・出版社のURL、公式のコード案内を確認した。
2. **取得・読取り**：A1–A6のPDFを開き、今回の論点に必要な箇所を読んだ。原著PDFの全文精読と、すべての掲載結果の検証は同義ではない。
3. **データ・コード取得**：Bergの原著C++コード・個体表、De Gernierの原画像・個体CSVは未取得。Mellorの全根モデルソースは今回確認できなかった。
4. **実行・再現**：原著コードのビルド・実行、原著の全図再現は未実施。E77・E78はこのリポジトリの登録済み簡約模型と既存データの追解析である。
5. **再配布**：PDF・図・第三者コードはGitに含めない。リンク、書誌、独自要約、取得結果とハッシュのみを記録する。公開閲覧の成功を、無条件の再配布許諾として扱わない。

作業中の実ファイルは`/tmp/torus-model-access-20261122/`（A1–A4）と`/tmp/torus-root-review-20261122/`（A5–A6）。一時保存先は永続の配布先ではない。将来の再取得では、上記URL・取得版・ハッシュを照合する。

原著が記す典型的なBergモデルの計算は、6日間の成長を24–36コアのワークステーションで約24時間かけるもの（A1 p.27）。コード取得後も、依存と許諾、最小条件、計算予算を先に確認する。今回はその計算を開始していない。
