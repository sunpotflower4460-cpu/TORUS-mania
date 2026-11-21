# 第15回の資料取得と再実行

確認日2026-11-20 UTC。以下の公開入力9件を取得し、作業用ディレクトリと、Gitから展開した追試用ディレクトリでSHA-256を検証した。リポジトリにはコード、読み取った座標・数値、自作図を収めた。公開原図、動画、原著PDF、ワークブックは取得先を記録した。[一次資料の範囲](../notes/E55_E60_particle_return_evidence.md)・[取得コード](../../experiments/particle_return_sources.py)

| 該当する測定 | 原本の配布先 | 取得したバイト列のSHA-256 |
|---|---|---|
| E55、放射能を分けた図5 | [pencikfig5.jpg](https://cdn.ncbi.nlm.nih.gov/pmc/blobs/e73b/3877806/6c6e17c9dcc5/pc_114421_f5.jpg) | `df72091dca01dd4a70a7959bd4ac9577decc27dcb4db1b4a82e0f769265a633a` |
| E55、酸化型の質量分析図6 | [pencikfig6.jpg](https://cdn.ncbi.nlm.nih.gov/pmc/blobs/e73b/3877806/5e9e3a0ad073/pc_114421_f6.jpg) | `404bd0c877f9e21a189b23944f620dbfe1a3722ab92e7ec37e4d87eb219019dc` |
| E56、根を区切った測定図4 | [ljungfig4.jpg](https://cdn.ncbi.nlm.nih.gov/pmc/blobs/eddd/1087988/c116f3fab1b6/tpc1701090f04.jpg) | `e7af7e5cd36fc3342cd28eaa08fd2942b5e9c4b7f390d2f9d47b3ed45cc6742c` |
| E56、根の細胞型と新生IAAの図5 | [petersfig5.jpg](https://cdn.ncbi.nlm.nih.gov/pmc/blobs/790e/2714926/6f32ebe032f9/tpc2101659f05.jpg) | `c5c0e1c857d14622308435b31c3f8c78288f7d646ab31fd6f837497745d2e5cb` |
| E57、洗出しと重力向きの図がある原著PDF | [auxsen.pdf](https://www.nature.com/articles/s41586-021-03425-2.pdf) | `540255a7e2b7f72d0f09e9dbd734830808fe8babee63d5e73e209bb38a213671` |
| E58、213フレームのS1 Movie | [granule-plane.mov](https://journals.plos.org/plosone/article/file?type=supplementary&id=10.1371/journal.pone.0159917.s006) | `dbcbdbcc5cdecdf56b5ce43ca00ab8b7a26524f6737a7b5acdc8b685a76b3930` |
| E58、立体撮影の可視化S3 Movie | [granule-volume.avi](https://journals.plos.org/plosone/article/file?type=supplementary&id=10.1371/journal.pone.0159917.s008) | `9579a53bb2730a8178e7af2ef363a86c4651fee4e546675db39b625911d98aac` |
| E59、切断後の変位の図5 | [wufig-5.png](https://media.springernature.com/full/springer-static/image/art%3A10.1038%2Fs41567-023-02223-z/MediaObjects/41567_2023_2223_Fig5_HTML.png) | `9e81e6c8e191ec1b411b3adde644f5f399597511a28becb916db856b7f982080` |
| E60、図3bに対応するSource Data | [hayashi-source.xlsx](https://static-content.springer.com/esm/art%3A10.1038%2Fs41467-021-27020-1/MediaObjects/41467_2021_27020_MOESM4_ESM.xlsx) | `4fe8d692c09ece8409debc663cd964de2acb90ea54beaa3097ffe9a7a7508de6` |

E57のZenodoには生画像の大きなZIPがある。今回は刊行された図の太い平均線を採点し、生の画像系列は取り込んでいない。E58のS1 Movieは再生用の10 fpsと元の時間刻み2秒を区別した。S3 Movieでは粒子ごとの奥行きを復元する追加の情報が得られなかった。Wuらの出版社版は全著者データの入手方法を著者への問い合わせとしている。原著本文はNeedleman Labが公開した版で確認し、図5は出版社の原寸PNGから取得した。Hayashiらのワークブックは出版社とPMCの版1の両方で同じハッシュだった。[AuxSenの原画像の索引](https://doi.org/10.5281/zenodo.4524537)・[Needleman Labの文献ページ](https://needleman.seas.harvard.edu/publications/)・[HayashiらのPMC版のワークブック](https://pmc-oa-opendata.s3.amazonaws.com/PMC8608799.1/41467_2021_27020_MOESM4_ESM.xlsx)

## 再実行

リポジトリのルートから実行する。動画の読取りには端末の `ffmpeg` と `ffprobe` を用いる。次のコマンドは公開元に接続する。すでに取得した原本を使うときは同じ名前とハッシュで読み込める。

```bash
python3 -m pip install -r experiments/requirements.txt \
  -r experiments/E29_growth_holdout/requirements.txt \
  -r experiments/E23_nitrate_pin2/requirements.txt \
  -r experiments/E58_granule_paths/requirements.txt
torus_run=$(mktemp -d)
python3 -m experiments.particle_return_sources --raw "$torus_run/raw"
python3 -m experiments.run_particle_return --raw "$torus_run/raw" \
  --out "$torus_run/results" --log "$torus_run/run.json"
sed "s|research/results/|$torus_run/results/|" research/results/PARTICLE_RETURN_SHA256SUMS | sha256sum -c -
```

実行環境はDebian 13 x86_64、Python 3.12.14、NumPy 2.3.5、SciPy 1.17.0、Matplotlib 3.10.8、PyMuPDF 1.26.6、Pillow 13.0.0、openpyxl 3.1.5、OpenCV 4.13.0、FFmpeg 7.1.5。数値処理は各プロセス1スレッド。合成動画の乱数種は582026。E59の図の前半を読み直した版から再取得・再実行し、数値6点と図2点をバイト単位で照合した。[実行ログ](../results/PARTICLE_RETURN_RUN.json)・[SHA-256](../results/PARTICLE_RETURN_SHA256SUMS)
