# 2026-11-20 UTC　標識の化学形と発生の原本

Debian 13 x86_64、Python 3.12.14。NumPy 2.3.5、SciPy 1.17.0、Matplotlib 3.10.8、Pillow 13.0.0、PyMuPDF 1.26.6、OpenPyXL 3.1.5。原本は `data/raw/path_and_formation/` に置いた。Gitに保存したのは自作の計算・抽出・要約と図。公開のPDF、写真、ワークブックは元の提供先から入手する。[実行記録](../results/PATH_FORMATION_RUN.json)

| ローカル名 | 取得先 | SHA-256 |
|---|---|---|
| `fluora.pdf` | [大学公開のPařízkováらの論文](https://eprints.whiterose.ac.uk/id/eprint/172333/7/nph.17183%20%281%29.pdf) | `41deaad34df8776a6bfa40151b5089ec066ecfd5016c83290b5b21897df7a98a` |
| `lu_fig3.jpg` | [Luら Fig. 3](https://cdn.ncbi.nlm.nih.gov/pmc/blobs/d9f7/6168253/d93f499eddb6/JCB_201709174_Fig3.jpg) | `681f53c244211b84259f96ff62beb0dcd067268499b20ca0ee10cebe7df8497b` |
| `lu_fig4.jpg` | [Luら Fig. 4](https://cdn.ncbi.nlm.nih.gov/pmc/blobs/d9f7/6168253/042f427943e1/JCB_201709174_Fig4.jpg) | `3ce39bb1af2b07d51544a1b0cedc3b771f2bb0cb63ef4eff97e00f4e55044e74` |
| `kv_archive.zip` | [MannaらのDryad v3、版373722](https://datadryad.org/api/v2/versions/373722/download) | 時刻でZIP全体が変わり得るので、内部の5ファイルを照合 |

| Dryad ZIP内のファイル | SHA-256 |
|---|---|
| `lumen-shape-data-experiments.xlsx` | `d9dffce544e4a09dbfffd97a005eb6d263d71fe46b7207e42adc65e5d50fba14` |
| `lumen-speed-data-experiments.xlsx` | `c0b748dc13a916238a10bd4ad1febdf738b2be3235afcb9a89df19e245ad7e5e` |
| `lumen-shape-data-simulation.xlsx` | `4feaf0568bf8d358fb10cbfbe5beab0d7cedb9e086189152c6b7a3ad411e94e1` |
| `lumen-speed-data-simulation.xlsx` | `b790bbbbe1e73c5158218bda82fe8782af0274ce853610f54d6bb1a72b20fec6` |
| `KV_cell_apical_width_data_Fig_4C-D.xlsx` | `460d01badd552c757f02024de3ff9f76bef5a90163ba0c67312d2207c77cc162` |

Pařízkováらは出版社と補遺の取得先が端末から403。大学版PDFの6ページ目から本文と測定図を確認した。LuらはPMCの全文・元図・Table 1を確認。Fig. 3の分母と読み取り範囲、Fig. 4Cの印字値とTable 1の印字値をコードに記録した。Duttaらの本文は出版社で読めた。実測と計算の配列については著者への問い合わせ方式と記載があり、今回の計算には使っていない。DryadのデータはCC0 1.0で、公開アーカイブは約48 MB。解析には5つのワークブックだけを使う。Wu、Supatto、Nonakaの資料は比較と研究範囲の確認に用いた。[LuらのPMC](https://pmc.ncbi.nlm.nih.gov/articles/PMC6168253/)・[Dryad書誌](https://doi.org/10.5061/dryad.w9ghx3g2h)・[文献メモ](../notes/E39_E43_path_and_formation_evidence.md)

## 取得と再実行

リポジトリのルートで、[再開メモ](../STATUS.md)の依存パッケージを準備した後に実行する。

```bash
torus_raw=$(mktemp -d)
torus_lu='https://cdn.ncbi.nlm.nih.gov/pmc/blobs/d9f7/6168253'
curl --fail --location 'https://eprints.whiterose.ac.uk/id/eprint/172333/7/nph.17183%20%281%29.pdf' -o "$torus_raw/fluora.pdf"
curl --fail --location "$torus_lu/d93f499eddb6/JCB_201709174_Fig3.jpg" -o "$torus_raw/lu_fig3.jpg"
curl --fail --location "$torus_lu/042f427943e1/JCB_201709174_Fig4.jpg" -o "$torus_raw/lu_fig4.jpg"
curl --fail --location 'https://datadryad.org/api/v2/versions/373722/download' -o "$torus_raw/kv_archive.zip"
run_dir=$(mktemp -d)
python3 -m experiments.run_path_formation --raw "$torus_raw" --out "$run_dir/results" --log "$run_dir/run.json"
sed "s|research/results/|$run_dir/results/|" research/results/PATH_FORMATION_SHA256SUMS | sha256sum -c -
```
