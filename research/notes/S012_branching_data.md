# S012　植物5群の分岐データを読み直した結果

Brummer et al. (2021), *Branching principles of animal and plant networks identified by combining extensive data, machine learning and modelling*。2026-11-20 UTCに本文の表1・採取法と著者公開の補足データv1を確認した。樹木で測ったのは外形の枝区間で、木部内の水流や師部内の糖の時間追跡は含まれない。[論文・表1](https://pmc.ncbi.nlm.nih.gov/articles/PMC7879751/)・[出版版](https://doi.org/10.1098/rsif.2020.0624)

**入力と権利。** A. B. Brummerら著者10名による電子補足 *Datasets*, v1、ファイル名 `rsif20200624_si_002.xlsx`、906,739バイト。CC BY 4.0。Figshareに記載された著者・版を帰属先とし、作成した統計は本研究の再集計として示す。SHA-256は `2a5a054cd610e39f0b581bde9595b7696f24a385e7dbb0ece133ef1121fbb6ee`。[データと著者一覧](https://doi.org/10.6084/m9.figshare.13370348.v1)・[版のメタデータ](https://api.figshare.com/v2/articles/13370348/versions/1)・[利用条件](https://creativecommons.org/licenses/by/4.0/)

**自作の再解析。** 植物の5シートを読み、個体内の枝IDと親IDを連結し、子数と全ての径が整合する分岐点に限定した。一つの節に接続する各枝の組で細径/太径を求め、組ごとに同じ重みで平均した。著者の学習器やその特徴量の追試には相当しない。枝径には成長履歴が重なり、同じ木の複数の枝は独立個体ではない。

| 群 | 枝区間 | 採用分岐点 | 径比の平均 |
|---|---:|---:|---:|
| バルサ | 649 | 292 | 0.627 |
| ピニョンマツ | 2,099 | 813 | 0.607 |
| ポンデローサマツ | 312 | 141 | 0.626 |
| 根群 | 1,231 | 374 | 0.625 |
| 樹冠の枝先群 | 914 | 404 | 0.591 |

5群すべての区間総数が論文表1と一致した。根群で1節を子数・対応の不整合により除外した。入力上の端点は除外理由を分けて集計した。対応するE04の有効半径比は格子管の構成則から求めた値で、実物の枝径から流量や木全体の閉路を推定していない。[再解析コード](../../experiments/E04_transport/plant_data.py)・[組数・四分位数と全結果](../results/E04/plant/summary.json)
