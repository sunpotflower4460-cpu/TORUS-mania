# 2026-11-20 UTC　側根の準備シグナル・発生段階の資料確認

Debian 13 x86_64、Python 3.12.14。NumPy 2.3.5、SciPy 1.17.0、Matplotlib 3.10.8、Pillow 13.0.0、PyMuPDF 1.26.6を使用。原本はローカルの `data/raw/root_clock/` に保存した。Gitには図から自作コードで抽出した値、計算の記録、描き直した比較図を保存した。

| 資料 | 確認できた範囲 |
|---|---|
| [Wachsmanら2020](https://pmc.ncbi.nlm.nih.gov/articles/PMC7758939/) | PMC公開本文、Fig. 2・3の元画像、方法、図の説明。定量入力はFig. 3Cの箱ひげ図。3Cに対応する個体別の観測値は未取得。 |
| [Perianez-Rodriguezら2021](https://pmc.ncbi.nlm.nih.gov/articles/PMC7775764/) | PMCの公開版PDF、補遺PDF、Fig. 1・S2・S3。公開Data file S1・S2のシートはそれぞれ変異マッピングと遺伝子発現。個体別の細胞生産率と周期を照合できる表はこれらにない。 |
| [Xuanら2015](https://pubmed.ncbi.nlm.nih.gov/25959963/) | PubMed抄録。大学の書誌は全文のアクセス制限ありと表示し、取得先からの応答は403または案内HTML。図の数値は使用していない。 [大学の書誌](https://biblio.ugent.be/publication/6864435) |
| [ten Tusscher 2026](https://pmc.ncbi.nlm.nih.gov/articles/PMC13421895/) | PMC公開本文を確認。比較の対象は成長する根を表した計算模型。 |

## 追試で照合する原本

| ローカル名 | 原本 | SHA-256 |
|---|---|---|
| `wachsman_f3.jpg` | [Wachsman Fig. 3](https://cdn.ncbi.nlm.nih.gov/pmc/blobs/84bd/7758939/40e6006dffcc/nihms-1649559-f0003.jpg) | `5648f6afab9948182d38dc82be3017e0982c425e8cb8409a6fd4b99c178f297c` |
| `perianez_article.pdf` | [PMC7775764.1](https://pmc-oa-opendata.s3.amazonaws.com/PMC7775764.1/PMC7775764.1.pdf)の2ページ目のFig. 1E | `77b9b645725ee549d666cdab90431c42eff5cd77149810180547951b575e2d2c` |
| `perianez_sm.pdf` | [補遺PDF](https://pmc-oa-opendata.s3.amazonaws.com/PMC7775764.1/abd4722_SM.pdf)の3ページ目のFig. S2C | `c6681d011aa2a5550a72cb44c840ab7814ebcfd2608132a1e7b63b5f7d04745f` |

計算コードは原本のハッシュと図の位置を照合する。E32は公開したE29の固定予測をローカル入力とする。[固定予測](../results/E29/sealed_predictions.json)・[追試コマンド](../STATUS.md)
