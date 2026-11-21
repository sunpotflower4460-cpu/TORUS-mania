# 第18回の入力と再実行

2026-11-20〜21 UTCに、公開元から本文と入力を確認した。ここに載せた11点を固定し、元の画像・ブックは生資料とした。画像から読み取った表の値は該当する実験のコードに手で転記し、元のページと照合した。[一次資料の確認範囲](../notes/E72_E76_calibrated_formation_evidence.md)・[取得コード](../../experiments/calibrated_formation_sources.py)

| 入力 | 公開元 | SHA-256 |
|---|---|---|
| `neural-main.xlsx` | [Maniou 主図 Source Data](https://static-content.springer.com/esm/art%3A10.1038%2Fs41563-024-01942-9/MediaObjects/41563_2024_1942_MOESM2_ESM.xlsx) | `ded627caf90bf1c66273f705ae1d440c0ef73600276a1cb6c481d8ca35539219` |
| `neural-extended.xlsx` | [Maniou 拡張図 Source Data](https://static-content.springer.com/esm/art%3A10.1038%2Fs41563-024-01942-9/MediaObjects/41563_2024_1942_MOESM3_ESM.xlsx) | `c9b2b414a050e888ff8453eebeccb3cbc2cbe5d1df072da061d74af77592aad0` |
| `epiboly-fig2.jpg` | [Hernández-Vega 図2の極の位置](https://cdn.ncbi.nlm.nih.gov/pmc/blobs/eab0/5210093/eba7249a1b9e/EMBJ-36-25-g003.jpg) | `da94a944875c51add787c02d3c01ac6d79b3b4910d6a655cd7c3cf5773c25d4f` |
| `epiboly-fig4.jpg` | [Hernández-Vega 図4Dの画像](https://cdn.ncbi.nlm.nih.gov/pmc/blobs/eab0/5210093/631c70bb4e97/EMBJ-36-25-g005.jpg) | `3c17de42d5e0490cff002036ddb1efcd3385df3098b2bc7bfe2f6b66e15c2782` |
| `lee-p824.png` | [Lee・Evans 824頁の方法](https://cdn.ncbi.nlm.nih.gov/pmc/blobs/e00c/1064613/7e5513d7337e/plntphys00586-0040.png) | `93463ce88ceb664dfcdceda17edefc65d0efca729bf6d9ce048115521d8f17c3` |
| `lee-p825.png` | [Lee・Evans 825頁の表Iと化学分析](https://cdn.ncbi.nlm.nih.gov/pmc/blobs/e00c/1064613/69f5c37e7f66/plntphys00586-0041.png) | `d4993897bad2008618f10dccb0d03d754dbbda114d2107cfefcab20de642008e` |
| `lee-p826.png` | [Lee・Evans 826頁の表II](https://cdn.ncbi.nlm.nih.gov/pmc/blobs/e00c/1064613/978d944e6f57/plntphys00586-0042.png) | `ac3812fa91464bbe3cced8fde55f49363353d15902f5b58e4e442c291cf19685` |
| `hasenstein-p890.png` | [Hasenstein・Evans 890頁の方法](https://cdn.ncbi.nlm.nih.gov/pmc/blobs/1ef0/1054589/8bac0b9348a3/plntphys00624-0256.png) | `aadd9c67dc91d3a885c21371245a097fea1e7608870bf9b94b678bddbc1f583c` |
| `hasenstein-p891.png` | [Hasenstein・Evans 891頁の方法と結果](https://cdn.ncbi.nlm.nih.gov/pmc/blobs/1ef0/1054589/398483250acb/plntphys00624-0257.png) | `52d045654c49e27aa36a2ddb7424e908b6cb1395dfae4ae09c88f5733eaf916f` |
| `hasenstein-p892.png` | [Hasenstein・Evans 892頁の表I・II](https://cdn.ncbi.nlm.nih.gov/pmc/blobs/1ef0/1054589/f73e4324b6bf/plntphys00624-0258.png) | `ba2af383b55389758bee90fc6597d58bb492b702d0455adf0f7d6ecf4e0e31b2` |
| `hasenstein-p893.png` | [Hasenstein・Evans 893頁の表III](https://cdn.ncbi.nlm.nih.gov/pmc/blobs/1ef0/1054589/2e106b34a5c3/plntphys00624-0259.png) | `e8418c31041f0ff47899f783c073366ee9cea34152b4d96cac0b31971b2e157e` |

拡張図8の手順は公開ワークブックの値を使った。ゼブラフィッシュの仕事率の数値配列は使わず、図4Dから色の位置を抽出した。E76には外部入力がない。E72〜E75の入力は合計約1.1 MiB。[図・表の読取りと制約](../notes/E72_E76_calibrated_formation_evidence.md)

## 再実行

リポジトリのルートから実行する。

```bash
python3 -m pip install -r experiments/requirements.txt \
  -r experiments/E23_nitrate_pin2/requirements.txt \
  -r experiments/E29_growth_holdout/requirements.txt
torus_run=$(mktemp -d)
python3 -m experiments.calibrated_formation_sources --raw "$torus_run/raw"
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MPLBACKEND=Agg \
  python3 -m experiments.run_calibrated_formation --raw "$torus_run/raw" \
    --out "$torus_run/results" --log "$torus_run/run.json"
sed "s|research/results/|$torus_run/results/|" research/results/CALIBRATED_FORMATION_SHA256SUMS | sha256sum -c -
```

Debian 13 x86_64、Python 3.12.14、NumPy 2.3.5、SciPy 1.17.0、Matplotlib 3.10.8、openpyxl 3.1.5、Pillow 13.0.0で検証した。既存の依存関係を用いた。検証ではGitの `747c849` から別のディレクトリへ展開し、11ファイルを公開元から新しく取得した。数値5点・図2点のバイト列が保存版と一致した。実行時間はその都度変わるためハッシュの対象に含めない。[SHA-256](../results/CALIBRATED_FORMATION_SHA256SUMS)・[実行ログ](../results/CALIBRATED_FORMATION_RUN.json)
