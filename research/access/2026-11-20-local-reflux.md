# 2026-11-20 UTC　内皮と根の伸長の資料確認

Debian 13 x86_64、Python 3.12.14。NumPy 2.3.5、SciPy 1.17.0、Matplotlib 3.10.8、OpenPyXL 3.1.5、Pillow 13.0.0。公開全文、図、出版社の図データを取得できた。本文、元画像、元ワークブックは `data/raw/local_reflux/` に保存した。

| 資料 | 確認範囲 |
|---|---|
| [Marhavý et al. 2013](https://pmc.ncbi.nlm.nih.gov/articles/PMC3545298/) | 公開全文、Fig. 2〜5、本文にある時刻。個体別のデータは用いていない。 |
| [Marhavý et al. 2016](https://pmc.ncbi.nlm.nih.gov/articles/PMC4762431/) | 公開全文、Fig. 2〜6、本文の集計値。図の20は除去イベント数。 |
| [Vermeer et al. 2014](https://pubmed.ncbi.nlm.nih.gov/24408432/) | PubMed抄録で内皮の体積・形の変化を照合した。本文や数値は解析に用いていない。 |
| [Li et al. 2021](https://www.nature.com/articles/s41586-021-04037-6)・[PMC著者稿](https://pmc.ncbi.nlm.nih.gov/articles/PMC7612300/) | 出版社の図・図注と3ワークブック、著者稿で方法を照合。電極の比較は著者稿のExtended Data Fig. 1iと確定版の2cが対応する。 |

| ローカル名 | 公開元 | SHA-256 |
|---|---|---|
| `m13_f2.jpg` | [Fig. 2](https://cdn.ncbi.nlm.nih.gov/pmc/blobs/4191/3545298/39a8a79bd4a3/emboj2012303f2.jpg) | `6c8ea7438a09f076d47df6cace06bea80f4156b02f2b3cd5c1910a44b00cd839` |
| `m13_f3.jpg` | [Fig. 3](https://cdn.ncbi.nlm.nih.gov/pmc/blobs/4191/3545298/67c87ff286a1/emboj2012303f3.jpg) | `08d8b60940c494254537814f341baa643054fbdaa21f56fbad07d39d508f2b25` |
| `m13_f4.jpg` | [Fig. 4](https://cdn.ncbi.nlm.nih.gov/pmc/blobs/4191/3545298/779a927a2390/emboj2012303f4.jpg) | `ac2c5204d18318ef6f513d5367475961ea4dcb83793c874355a47e03e26355aa` |
| `m16_f6.jpg` | [Fig. 6](https://cdn.ncbi.nlm.nih.gov/pmc/blobs/1fff/4762431/567c1e2c187a/471f06.jpg) | `fb648543b2da52024ace0a3e541da071b5822f08b0c2c4c08e177896372b9a98` |
| `li_fig1.png` | [Fig. 1](https://media.springernature.com/full/springer-static/image/art%3A10.1038%2Fs41586-021-04037-6/MediaObjects/41586_2021_4037_Fig1_HTML.png) | `ff38151d9492579203313253905017b1ca5f7a35289aea82633d25d11f982512` |
| `li_f1.xlsx` | [Fig. 1の図データ](https://static-content.springer.com/esm/art%3A10.1038%2Fs41586-021-04037-6/MediaObjects/41586_2021_4037_MOESM8_ESM.xlsx) | `9f3dd97802ffca9b4e58a9255a1cd9da8fc89c99e1318fa676f4c299c298cee6` |
| `li_f2.xlsx` | [Fig. 2の図データ](https://static-content.springer.com/esm/art%3A10.1038%2Fs41586-021-04037-6/MediaObjects/41586_2021_4037_MOESM9_ESM.xlsx) | `8fda1a14473035b931ce1f826182001a412c0136bea1ce2066f709854a600de7` |
| `li_ext2.xlsx` | [Extended Data Fig. 2の図データ](https://static-content.springer.com/esm/art%3A10.1038%2Fs41586-021-04037-6/MediaObjects/41586_2021_4037_MOESM13_ESM.xlsx) | `0ba797314b6bfe8e4766db5e9e3440e5961c06651178c5b182a11eb291e921a0` |

Gitで配布するのは、読み取った集計値・算出した指標・自作の図・コード。原本は公開元から取得する。2016年のPMC掲載ページはCC BY-NC 4.0を表示した。[読取り・単位の照合](../notes/E24_E26_root_tissue_evidence.md)・[追試](../STATUS.md)
