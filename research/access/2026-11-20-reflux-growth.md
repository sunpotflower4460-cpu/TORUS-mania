# 2026-11-20 UTC　根端の戻り・成長・準備部位の資料確認

Debian 13 x86_64、Python 3.12.14。NumPy 2.3.5、SciPy 1.17.0、Matplotlib 3.10.8、Pillow 13.0.0、PyMuPDF 1.26.6。公開全文、元図、大学のリポジトリにある論文PDFを確認した。PDFと元画像はローカルの `data/raw/reflux_growth/` に保存した。

| 資料 | 確認できた範囲 |
|---|---|
| [Mellorら2020](https://pmc.ncbi.nlm.nih.gov/articles/PMC7132777/) | 公開本文、Fig. 2、4、5の元図、方法と予測された流束の説明。再集計には掲載図の要約値を使用。 |
| [van den Bergら2021](https://doi.org/10.1016/j.devcel.2021.07.005) | 大学公開PDFの本文・方法・Fig. 7。出版社のHTMLは実行環境から403。論文が案内する研究室の[データ・コードの公開先](http://bioinformatics.bio.uu.nl/khwjtuss/PrimingRoot)はHTTPS・HTTPとも503で、個体別データと元コードは未取得。 |
| [Vegaら2021](https://pubmed.ncbi.nlm.nih.gov/34357701/) | E23のDOIと筆頭著者を照合。従来の2ワークブックと同じ論文。 |

| ローカル名 | 原本 | SHA-256 |
|---|---|---|
| `mellor_fig2.jpg` | [Mellor Fig. 2](https://cdn.ncbi.nlm.nih.gov/pmc/blobs/64f6/7132777/82245338738c/develop-147-181669-g2.jpg) | `671ebc7a23b167bbb36981bf5995f52008a1ff77ac834605ce95e1172a004f8b` |
| `mellor_fig4.jpg` | [Mellor Fig. 4](https://cdn.ncbi.nlm.nih.gov/pmc/blobs/64f6/7132777/087276e63c38/develop-147-181669-g4.jpg) | `f0b858b420915308ab5c5f74fa17ab0313c637a3d16c9ea4e37da7e0ffbc8305` |
| `mellor_fig5.jpg` | [Mellor Fig. 5](https://cdn.ncbi.nlm.nih.gov/pmc/blobs/64f6/7132777/abf436973a0c/develop-147-181669-g5.jpg) | `8509cb6f9975d36eba51b6496a456e4b4fc88efb1afb0046ea54171aa0d5c29a` |
| `berg_uu_alt.pdf` | [Utrecht Universityの公開PDF](https://dspace.library.uu.nl/bitstream/handle/1874/413557/1_s2.0_S153458072100561X_main.pdf?sequence=1) | `04905086dc09cd7bd03deda7a9123e31914e869ee398e8e1c665340f81708196` |

E29はPDFの13ページ目の埋め込み画像を使う。数値予測を固定するまでは図の高生産側のマーカーの縦座標を読んでいない。原本を再配布せず、抽出値・較正・式・採点コードをGitで保存した。[文献の扱い](../notes/E27_E29_root_reflux_literature.md)・[追試](../STATUS.md)
