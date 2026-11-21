# 第16回の公開原本の取得と再実行

確認日2026-11-20 UTC。リポジトリには出典、コード、数値、計算で作った図を収めた。原著、掲載図、動画、元の追跡ZIP、ワークブック、体積像は下記の公開元から取得する。Asaiら、Kunzら、Bragantiniらの論文にはCC BY 4.0の表示がある。外部にあるアーカイブは下の取得コードで読む。[一次資料の確認範囲](../notes/E61_E66_embryo_history_evidence.md)・[固定した入力](../../experiments/embryo_history_sources.py)

| 測定 | 配布元 | 入力SHA-256 |
|---|---|---|
| E61、Asaiらの本文XML | [PMC11087055.1](https://pmc-oa-opendata.s3.amazonaws.com/PMC11087055.1/PMC11087055.1.xml) | `f75208516dfe062b2739fa13ec55d7f6f28434eef363978ffab6410289074f3d` |
| E61、渦中心間距離の図 | [図1補足1](https://pmc-oa-opendata.s3.amazonaws.com/PMC11087055.1/elife-89948-fig1-figsupp1.jpg) | `25d0b94cf87c5db24a0a51477b2d3aa94114efad16380997a48863f442e6aae7` |
| E62、Shahらの可視化の系列 | [Cell Flow Navigatorの表示データ](https://imb-dev.gitlab.io/cell-flow-navigator/prepareData/data.json?temp6) | `f8afb07fb79eedda03825996b59ee2b45653f2a1f3fb1c6f31dde9aed7c09a3a` |
| E62、全胚の追跡を収めた配布ZIP | [Virtual Embryo Zooの追跡](https://public.czbiohub.org/royerlab/zoo/Zebrafish/tracks_zebrafish_bundle.zarr.zip) | `5660b35e36dc1fd123bd13bbff0d4bb8dd316bf7b8abfbfbc47bc31208647f06` |
| E65、論文図4の追跡版 | [InTRACKtive配布ディレクトリ](https://public.czbiohub.org/royerlab/ultrack/inTRACKtive/Sparse_Embryo_tracks_with_hex_bundle.zarr/) | `f9bab4a47270512c6379492f07fb47c0edb077c9cc0cd402b4dca5625778b46b` |
| E66、体積像の固定領域を含む31時点 | [成長中のゼブラフィッシュ、OME Zarr](https://public.czbiohub.org/royerlab/ultrack/zebrafish_embryo.ome.zarr/) | `8ec7f00ba8adcc7f59de3870d6c0e23c73d9da2a15226f11a451c9b044460ff7` |
| E63、Kunzらの公開表 | [PMC10241863.1のSource Data](https://pmc-oa-opendata.s3.amazonaws.com/PMC10241863.1/41467_2023_38988_MOESM9_ESM.zip) | `737b3bb8ddc009e03e9e21fc50661ea4f8ba9b5b9b5de2ef0c9cb574a2c1216a` |
| E63、勾配の単位を読む原著図 | [図1](https://cdn.ncbi.nlm.nih.gov/pmc/blobs/6142/10241863/52c29f7b16cf/41467_2023_38988_Fig1_HTML.jpg) | `d9e83de488807f8818696f1920201595fa66be81538fc2ba591a11703dc70228` |

E65とE66は公開されたZarrの必要な部分を読み、固定の順序・時刻で照合用のZIPを作る。E65は点と逆引きのアーカイブ、E66はレベル2のチャネル0・第1のZ区画の308〜338時点とメタデータを取る。ほかの原本と合わせ、取得量は約450 MiB。E61の関連TIFFを閲覧できたが、描画済みの速度ベクトルと流線であり、数値表は得られなかった。E63のZIPは出版社版とPMC版を照合し、ハッシュが同一だった。E64は前回の測定を動機とする数理模型で、実行に公開原本は使わない。[Zarrの取得コード](../../experiments/E65_crosscheck_returns/archive.py)・[画像の取得コード](../../experiments/E66_image_only_track/archive.py)・[Asaiらの図3の補足](https://pmc-oa-opendata.s3.amazonaws.com/PMC11087055.1/elife-89948-fig3-data1.tif)・[Kunzらの出版社版Source Data](https://static-content.springer.com/esm/art%3A10.1038%2Fs41467-023-38988-3/MediaObjects/41467_2023_38988_MOESM9_ESM.zip)

## 再実行

リポジトリのルートで次を実行する。取得済みの原本を使う場合は、各ファイルの保存名とSHA-256を固定した入力の表とそろえる。

```bash
python3 -m pip install -r experiments/requirements.txt \
  -r experiments/requirements-embryo-history.txt
torus_run=$(mktemp -d)
python3 -m experiments.embryo_history_sources --raw "$torus_run/raw"
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MPLBACKEND=Agg \
  python3 -m experiments.run_embryo_history --raw "$torus_run/raw" \
    --out "$torus_run/results" --log "$torus_run/run.json"
sed "s|research/results/|$torus_run/results/|" research/results/EMBRYO_HISTORY_SHA256SUMS | sha256sum -c -
```

実行環境はDebian 13 x86_64、Python 3.12.14、NumPy 2.3.5、SciPy 1.17.0、Matplotlib 3.10.8、openpyxl 3.1.5、numcodecs 0.16.5。E63の標本再抽出の乱数種は631120、E64の読み取りの乱数種は641120。[実行ログ](../results/EMBRYO_HISTORY_RUN.json)・[SHA-256](../results/EMBRYO_HISTORY_SHA256SUMS)
