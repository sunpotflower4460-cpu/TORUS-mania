# 2026-11-20 UTC　発生・形態形成の資料アクセス

| 資料 | 到達範囲と扱い |
|---|---|
| Djenoune et al. 2023 | [PMC公開著者版](https://pmc.ncbi.nlm.nih.gov/articles/PMC9939240/)の本文とFig. 4 JPEG。補足Fig. S11への通常のPMCリンクはPDFの代わりにHTMLを返し、出版社の補足PDFはHTTP 403。補足の結論は本文の記述まで。独立した個体や試行別のカウントは使用していない。 |
| Nonaka et al. 2002 | [出版社](https://www.nature.com/articles/nature00849)の抄録・図の案内と[著者の研究所資料](https://www.nibb.ac.jp/nibb50th/pdf/30-157.pdf)。原論文の表の定量再解析は未実施。 |
| Supatto et al. 2008、Sampaio et al. 2014、Montenegro-Johnson et al. 2016 | 公開本文、または対象実験を含む学位論文を閲読。生体の粒子追跡と、モデルから得る三次元流線を照合。元の個体別速度場は今回の入力に用いていない。[出典の詳細](../notes/E16_developmental_forces.md) |
| Ditengou et al. 2008、Richter et al. 2009、Pien et al. 2001 | PMCの本文・図の説明を閲読。Pienの公開PDFのTable 1とPMCの表を照合。Ditengouの補足PDFの通常リンクはHTMLを返し、PINの輸送ループの照合範囲は本文まで。[出典の詳細](../notes/E18_plant_organ_placement.md) |

## 入力を確認し直す場合

Djenoune et al. の[公表Fig. 4 JPEG](https://cdn.ncbi.nlm.nih.gov/pmc/blobs/08ff/9939240/8b4eeafb05d5/nihms-1870894-f0004.jpg) は746×1050、SHA-256 `5ab6850534d67aebb2cf7b1be8cf7b33f18036e3452685e22a0a46f56ee51865`。色の境界を抽出した数値入力をリポジトリに保存した。画像そのものは `data/raw/morphogenesis/` 内。Pien et al. の照合に用いた[公開PDF](https://www.uv.mx/personal/tcarmona/files/2016/08/Pien-et-al-2001.pdf) のSHA-256は `ae1c5aa75d9e6e1d65f0c3751597c1ad22913f6401d85d058566d4997494ec83`。各資料の本文・図版はGitで再配布していない。[再開・追試手順](../STATUS.md)
