# 第17回の入力と再実行

確認日2026-11-20 UTC。著者が公開した画像・論文・抄録の入手先を記す。元画像、掲載ページ、PDF、元の抄録は生資料として扱い、結果には独自の数値と図を収めた。[出典確認](../notes/E67_E71_iaa_embryo_work_evidence.md)・[取得コード](../../experiments/iaa_embryo_sources.py)

| 入力 | 配布元 | SHA-256 |
|---|---|---|
| E67 体積像レベル1、308〜338時点 | [Biohub OME Zarr](https://public.czbiohub.org/royerlab/ultrack/zebrafish_embryo.ome.zarr/) | `31a5754f35645f7724c5395ab011b2685f9c6594cb31e94645daf5aa3fa6c3fb` |
| E68 Kerk 図8の画像 | [PMC58929 図8](https://cdn.ncbi.nlm.nih.gov/pmc/blobs/b50e/58929/a900412691c8/pp0305901008.jpg) | `28e2d8e75f7941ecfb22a5ef09aea263e95a12064570216dd625e3348ddfcdff` |
| E68 Wilkinsの抄録 | [Europe PMCのレコード](https://www.ebi.ac.uk/europepmc/webservices/rest/search?query=EXT_ID:24477304&format=json&resultType=core) | `046316ac5c733880bde9dadad3f8dc34384423c0ecc3378eb48f40e3a8bc2cf2` |
| E69 Herrera-Perezの刊行PDF | [APS Harvest](https://harvest.aps.org/v2/journals/articles/10.1103/PRXLife.1.013004/fulltext) | `af4349605f415574e4e193c6b37b6a6346174dc7c7a438b1013216a31fce0b78` |
| E71 Martin・Piletの892頁 | [PMC1075445 892頁](https://cdn.ncbi.nlm.nih.gov/pmc/blobs/9365/1075445/6b5575234008/plntphys00603-0182.png) | `8e76b9ea9e74f1d22aa882aaa9864809a8038b44490e6afcf287920b5c3b3aeb` |
| E71 同893頁、表I | [PMC1075445 893頁](https://cdn.ncbi.nlm.nih.gov/pmc/blobs/9365/1075445/6f8bc8d6d53a/plntphys00603-0183.png) | `26fd2cecbecda488c82b2066ba05ff7a844f75a77923b008d67e041db4a25c8a` |
| E71 同894頁 | [PMC1075445 894頁](https://cdn.ncbi.nlm.nih.gov/pmc/blobs/9365/1075445/0b4ed5fe704b/plntphys00603-0184.png) | `2060a541955b92012255b60b17a21fa949b1125aee08b9762d4f8bdd70cdd490` |

E67のSHA-256は、Zarrのメタデータ2ファイルと31時点の圧縮画像を固定順に列挙したSHA-256一覧のハッシュ。チャネル0の最初のZ区画のみで、容量は約1.25 GiB。E62・E65の保存結果から同じ候補を取得する。新しいディレクトリでコードを展開した追試では、体積像33ファイルはハッシュが一致した取得済みのコピーを使い、他の6ファイルを公開元から取り直した。Europe PMCの生の応答は整形が変わるため、論文ID、DOI、刊行年、抄録本文を同じ順・表記で保存しハッシュを求めた。E70は解析式だけを入力とする。[画像の取得](../../experiments/E67_half_resolution/archive.py)・[前回の追跡版](2026-11-20-embryo-history.md)

## 再実行

リポジトリのルートで実行する。必要容量は約1.3 GiB。画像の取得済みのディレクトリを再利用するときは、下記の作業場所の `raw/level1` に置く。

```bash
python3 -m pip install -r experiments/requirements.txt \
  -r experiments/requirements-embryo-history.txt \
  -r experiments/E29_growth_holdout/requirements.txt
torus_run=$(mktemp -d)
python3 -m experiments.iaa_embryo_sources --raw "$torus_run/raw"
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MPLBACKEND=Agg \
  python3 -m experiments.run_iaa_embryo_work --raw "$torus_run/raw" \
    --out "$torus_run/results" --log "$torus_run/run.json"
sed "s|research/results/|$torus_run/results/|" research/results/IAA_EMBRYO_WORK_SHA256SUMS | sha256sum -c -
```

検証した環境はDebian 13 x86_64、Python 3.12.14、NumPy 2.3.5、SciPy 1.17.0、Matplotlib 3.10.8、PyMuPDF 1.26.6、Pillow 13.0.0、numcodecs 0.16.5。作業開始時にメモリの空き16 GiBと領域の空き27 GiBを確認した。資料索引、公開データの取得、画像の数値化、単体テストがこの環境で使えた。[実行ログ](../results/IAA_EMBRYO_WORK_RUN.json)・[結果のSHA-256](../results/IAA_EMBRYO_WORK_SHA256SUMS)
