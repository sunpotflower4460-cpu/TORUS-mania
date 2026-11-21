# 2026-11-20 UTC　根の公開測定と渦輪の資料アクセス

Debian 13 x86_64、Python 3.12.14、NumPy 2.3.5、SciPy 1.17.0、Matplotlib 3.10.8、Pillow 13.0.0、PyMuPDF 1.26.6、OpenPyXL 3.1.5。計算で使う11の原本は `data/raw/root_and_vortex/` に置いた。別の空の作業場所でも同じURLから取得し、数値と図を照合した。原本の画像や論文は配布物に含めていない。[実行記録](../results/RETURN_ENERGY_RUN.json)

| ローカル名 | 取得先 | SHA-256 |
|---|---|---|
| `yang_source.xlsx` | [HuらのSource Data](https://static-content.springer.com/esm/art%3A10.1038%2Fs41467-021-21802-3/MediaObjects/41467_2021_21802_MOESM12_ESM.xlsx) | `dc62b28a11ae34eb29084a8944f14714ebb6fe183146494432989fa34100410e` |
| `degern_article.pdf` | [De Gernierらの公開版PDF](https://biblio.ugent.be/publication/01K47A0QNA2VHHET9FD517S20G/file/01K47CJF9R1X89CRS2EQVDNXRH.pdf) | `4e713e031c5fdd820a0f1c5d5e6c5d95609661b2ae5b5078a0f9f66ca32e4ff9` |
| `degern_supplement.pdf` | [同補遺PDF](https://biblio.ugent.be/publication/01K47A0QNA2VHHET9FD517S20G/file/01K47CPPCZDZ6GK9Q2DTNWX610.pdf) | `edd903540832cd25c2c9910f0f120c765d65d578ac5bde081e265111885ddb27` |
| `duan_f3.jpg` | [DuanらのFig. 3](https://cdn.ncbi.nlm.nih.gov/pmc/blobs/0601/8133581/326c8e14f147/kiaa032f3.jpg) | `d21b6979c8ee9b8ab04cd1b95e8fc34953e24391b7738eafa9a9a5d8bbd20bd5` |
| `duan_f6.jpg` | [DuanらのFig. 6](https://cdn.ncbi.nlm.nih.gov/pmc/blobs/0601/8133581/4faa493f59d5/kiaa032f6.jpg) | `92025d81d6873904bc538d5a7029ac44902b87f835797b4e0b65cb304b49e3ce` |
| `limbourg_f16.jpg` | [Limbourg・NedićのFig. 16](https://static.cambridge.org/binary/version/id/urn:cambridge.org:id:binary-alt:20211102033654-41747-optimisedImage-S0022112021000367_fig16.jpg) | `52d52c82b86514fceed86bb4d09365e7d5d4d3b60b7db9008714f49c3f485f1d` |
| `limbourg_f17.jpg` | [同Fig. 17](https://static.cambridge.org/binary/version/id/urn:cambridge.org:id:binary-alt:20211102033654-65203-optimisedImage-S0022112021000367_fig17.jpg) | `f9cc74e3df3e554c4a9bf67ef527cd390aafdb2ccd07156b3dcb2c3c53859f6f` |
| `limbourg_f18.jpg` | [同Fig. 18](https://static.cambridge.org/binary/version/id/urn:cambridge.org:id:binary-alt:20211102033654-81147-optimisedImage-S0022112021000367_fig18.jpg) | `41df849f7d6c4f5d2f4664d9ac83f07425347451647618972c20ba24ec532738` |
| `limbourg_f19.jpg` | [同Fig. 19](https://static.cambridge.org/binary/version/id/urn:cambridge.org:id:binary-alt:20211102033654-12139-optimisedImage-S0022112021000367_fig19.jpg) | `76623770ff18c0c432de944217f8844afef1596ce4d9da58f4ac7152e75598e4` |
| `baskaran_f7.png` | [Baskaran・MullenersのFig. 7](https://static.cambridge.org/binary/version/id/urn:cambridge.org:id:binary:20220630140740282-0747:S2633425922000095:S2633425922000095_fig7.png) | `89bcfcf5a4ac0f63a1f53794aefa6cb2e6fc253a6ad4ec3d61dab19f4d891b83` |
| `dry_files_zip.zip` | [Dryad版443502のZIP](https://datadryad.org/api/v2/versions/443502/download) | 生成時刻でZIP全体の値が変わり得るため、下の2 CSVを照合 |

| ZIP内のファイル名 | SHA-256 |
|---|---|
| `SourceData1a_LRdvp_LRlevel_dryad.csv` | `d1ad3c16382cd944896587933d638e152b4b5a0c8369ae342a70330b06a8b3b9` |
| `SourceData1b_LRdvp_seedlinglevel_dryad.csv` | `5671a838ccad67aa236a68f189955b08255c2e2292057cfcef044961d59fc0ad` |

Huらの論文はCC BY 4.0。E33の出力は、ワークブックのFig. 5cと5eの指定範囲の抽出値を平均・相対値・出典とともに収録した再解析。Dryadのメタデータはバージョン8、CC0 1.0。個別ダウンロードの応答が403になる場合があり、公開の版別ZIPから取得した。Maranasらの全文はPMCで確認した。[Hu et al.](https://doi.org/10.1038/s41467-021-21802-3)・[CC BY 4.0](https://creativecommons.org/licenses/by/4.0/)・[MaranasらのPMC](https://pmc.ncbi.nlm.nih.gov/articles/PMC13334086/)

De Gernierらの出版社版HTMLは端末から403、大学の書誌と公開PDF2点は到達した。Limbourg・NedićのPDF経路はHTMLを返したため、著者の共有版本文の拡大図を用いた。両流体研究の元の速度スナップショットの対応は未取得。Kircher・Schopfer 2023は抄録を確認し、出版社の全文は端末から403。van den Bergら2021のモデルの公開先は、研究室の新旧の案内先ともこの実行環境から503だった。[Limbourg・Nedićの本文](https://www.cambridge.org/core/journals/journal-of-fluid-mechanics/article/formation-of-an-orificegenerated-vortex-ring/B9F8E5CB0B396AEB19D79D3EA509E02B/share/3cc03a7cf444df9dc14565406cd3845174a7388b)・[これまでの取得記録](2026-11-20-reflux-growth.md)

## 原本を一括で取得する

リポジトリのルートで[再開メモ](../STATUS.md)の依存パッケージを準備した後に実行する。各コードに固定した公開URLを使う。実行時に原本またはZIP内CSVのハッシュを照合する。

```bash
torus_raw=$(mktemp -d)
python3 - "$torus_raw" <<'PY'
from pathlib import Path
import subprocess
import sys
from experiments.E33_directional_response.run import URL as hu
from experiments.E34_root_period_transfer.run import SOURCES as growth
from experiments.E35_shoot_root_resources.run import SOURCES as plant
from experiments.E36_vortex_energy_transfer.run import SOURCES as vortex
from experiments.E38_founder_reporters.run import URL as dryad

out = Path(sys.argv[1])
sources = {"yang_source.xlsx": hu, "dry_files_zip.zip": dryad}
sources.update({name: url for name, (url, _) in {**growth, **plant, **vortex}.items()})
for name, url in sources.items():
    subprocess.run(["curl", "--fail", "--location", url, "-o", str(out/name)], check=True)
PY
run_dir=$(mktemp -d)
python3 -m experiments.run_return_energy --raw "$torus_raw" --out "$run_dir/results" --log "$run_dir/run.json"
sed "s|research/results/|$run_dir/results/|" research/results/RETURN_ENERGY_SHA256SUMS | sha256sum -c -
```
