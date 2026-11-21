# 第14回の取得と再実行

確認日2026-11-20 UTC。11入力のうち、2件は公開HTMLの最初の結果表を行・列の順で正規化したJSON。残りの9件は公開元のファイルをそのまま検証した。Niwayamaらの表は第13回と同一である。各公開元の利用条件に従い、原図・本文を再配布せず、Gitには抽出座標・再集計値・自作図と取得方法を収めた。[文献別の閲読範囲](../notes/E49_E54_turning_paths_evidence.md)・[取得コード](../../experiments/turning_path_sources.py)

| 使用箇所 | 配布元 | 保存バイト列のSHA-256 |
|---|---|---|
| E49、2方向の切片 | [rashotte_fig3.jpg](https://cdn.ncbi.nlm.nih.gov/pmc/blobs/b135/219050/c90cfa6d2df7/pp1038176003.jpg) | `b1b7e71ab2d0fd7d86517962c114b34fa39365904cb2aed12b1f95b7612bff41` |
| E49、表Iの正規化したセル | [rashotte_table1.json](https://pmc.ncbi.nlm.nih.gov/articles/PMC219050/) | `21a2760d10585d6349c5873531eaefe7110cd8a1c4fc275d4a2a8ca96a404df4` |
| E50、一次根の阻害と対照 | [lewis_fig2.jpg](https://cdn.ncbi.nlm.nih.gov/pmc/blobs/cfe6/1955737/8055e6675458/tpc1901838f02.jpg) | `d5dc325af197a1a8a1e91bb40bb55c0758f481a6e930b0a5fed208e94fa4471e` |
| E50、側根への輸送 | [wu_fig8.jpg](https://cdn.ncbi.nlm.nih.gov/pmc/blobs/b53a/1955722/f3cc8b58ad7c/tpc1901826f08.jpg) | `a54f674f93c58cd78f507f218378b4ef18c6ca67c78be853d06be94539d24950` |
| E50、伸長速度 | [wu_fig9.jpg](https://cdn.ncbi.nlm.nih.gov/pmc/blobs/b53a/1955722/b76eee89a94e/tpc1901826f09.jpg) | `f243548c7f169c3c964c020e1594bcd8e2c7b9d3c92bceb238898dd1ed31f521` |
| E50、表1の正規化したセル | [wu_table1.json](https://pmc.ncbi.nlm.nih.gov/articles/PMC1955722/) | `8f512fd965a45faeccf03a1ed7a8c843a77d42333c41c094c556679fc355abe6` |
| E51、13個体のベクトル | [piv_fields.xlsx](https://journals.plos.org/plosone/article/file?type=supplementary&id=10.1371/journal.pone.0159917.s004) | `71dc8689d8f0ec4c17be5f7bdd1410ce173a69d7239c0728c7861f8ee6fc1a8f` |
| E52、図5cのベクトル記号 | [mittasch.pdf](https://tu-dresden.de/mn/math/wir/ressourcen/dateien/forschung/publikationen/pdf2018/Mittasch2018.pdf?lang=de) | `8c9140c38144481f6defa9e8799ecb3f11efd0c253adca1c87ab001ef9ed9f3e` |
| E53、図4A/Bの高解像度パネル | [kimura.pdf](https://pmc-oa-opendata.s3.amazonaws.com/PMC7521852.1/PMC7521852.1.pdf) | `68faabf7445442200537af00ed9dd7eec735b5dec370732d0bb026c8c5b7dea8` |
| E54、図5Gの個体別角度 | [ng.pdf](https://publikationen.bibliothek.kit.edu/1000168316/152241581) | `b101f3bb7ea5a3e315e8ff529502eb1db2f8b0827fe4d2480f28f42079e92131` |
| E53、本文・公表分母の照合 | [kimura.xml](https://pmc-oa-opendata.s3.amazonaws.com/PMC7521852.1/PMC7521852.1.xml) | `80a8cdd07e16454023757f4d1e416a06bfb9290c09e997dc375e0176f894e345` |

Rashotte・Wuの著作はPMC公開HTMLを閲読した。図はPMCの固定画像から、表1は各ページの `tbl1` 内の最初の表から取得する。表のセルの表示文字を保持し、ページのナビゲーション・動的なヘッダーを除いてハッシュを照合する。欧州PMCの一部のXML・PDFではタイムアウトまたは500が生じたため、実行の依存先は上表で実際に取得できたものとした。Mittasch・Ngは大学公開版の固定PDF、KimuraはPMCの版1のPDFとXMLを用いた。同論文のSupplemental Movieの説明、Mittaschの追加資料、Niwayamaのコード説明とKusakaの大学版PDFは解釈用に確認した。[Mittaschの補遺](https://static-content.springer.com/esm/art%3A10.1038%2Fs41556-017-0032-9/MediaObjects/41556_2017_32_MOESM1_ESM.pdf)・[Kimuraの補遺](https://pmc-oa-opendata.s3.amazonaws.com/PMC7521852.1/mbc-31-1765-s001.pdf)・[Niwayamaのコード説明](https://doi.org/10.1371/journal.pone.0159917.s003)・[Kusakaの原著](https://doi.org/10.1002/cbic.200900289)

## 再実行

リポジトリのルートで次を実行する。既存データを使う場合は同じSHA-256のファイルを `--raw` に指定する。

```bash
python3 -m pip install -r experiments/requirements.txt \
  -r experiments/E29_growth_holdout/requirements.txt \
  -r experiments/E23_nitrate_pin2/requirements.txt
torus_run=$(mktemp -d)
python3 -m experiments.turning_path_sources --raw "$torus_run/raw"
python3 -m experiments.run_turning_paths --raw "$torus_run/raw" \
  --out "$torus_run/results" --log "$torus_run/run.json"
sed "s|research/results/|$torus_run/results/|" research/results/TURNING_PATH_SHA256SUMS | sha256sum -c -
```

Debian 13 x86_64、Python 3.12.14、NumPy 2.3.5、SciPy 1.17.0、Matplotlib 3.10.8、PyMuPDF 1.26.6、Pillow 13.0.0、openpyxl 3.1.5。計算は1プロセスにつき1スレッド。E54の並べ替えは全数列挙し、擬似乱数を使わない。openpyxlから未対応のシート拡張の警告が出るが、読取り専用で数値4列と13シートを検査した。Gitから展開したコードで入力11件を再取得し、数値6件と図2件は初回と一致した。[実行記録](../results/TURNING_PATH_RUN.json)・[SHA-256](../results/TURNING_PATH_SHA256SUMS)
