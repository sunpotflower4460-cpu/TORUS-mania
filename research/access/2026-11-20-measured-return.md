# 第13回の資料アクセスと追試

2026-11-20 UTC。国立国会図書館デジタルコレクションの2本の原著PDF、PMCにある原著の図2枚、PLOSの数値ワークブック2件と立体撮影の公表図1枚に到達し、解析コードを展開した別ディレクトリでも公開元から取り直した。下表のSHA-256は取得したバイト列に対する値。Gitには書誌、図の読取り位置、コード、再集計した数値と自作図を保存した。[文献と閲読範囲](../notes/E44_E48_measured_return_evidence.md)・[取得コード](../../experiments/measured_return_sources.py)

| 使用箇所 | 取得した原本 | SHA-256 |
|---|---|---|
| E44 無傷根の本文・図 | [vicia76.pdf](https://dl.ndl.go.jp/view/prepareDownload?contentNo=1&itemId=info%3Andljp%2Fpid%2F10767156) | `bd3b7ae2f0737fe2fc85f40a3719af8155fee765f89f492733c37b6f8b8165ef` |
| E44 根片の本文・図 | [vicia78.pdf](https://dl.ndl.go.jp/view/prepareDownload?contentNo=1&itemId=info%3Andljp%2Fpid%2F10767564) | `cef13427ec1faa271969dc1ec5462fa0527cb6e72ec7acb577c1263501c7f099` |
| E45 根、図5 | [ruzicka5.jpg](https://cdn.ncbi.nlm.nih.gov/pmc/blobs/5836/2890796/604eb15e5c4a/pnas.1005878107fig05.jpg) | `4d5685bf3a526bd195143b49f6af515b08611ecbfb45b8957de5e501e093743e` |
| E45 胚軸、図3 | [liu3.jpg](https://cdn.ncbi.nlm.nih.gov/pmc/blobs/6b11/3320201/b502f507f0e0/PP_191288_gs_f3.jpg) | `9e477a0128f01c9ca0baab9000165847911ebce6deef302ebcc455de1f4091fe` |
| E46 S1 Dataset、各細胞の縦断面のベクトル | [piv_fields.xlsx](https://journals.plos.org/plosone/article/file?type=supplementary&id=10.1371/journal.pone.0159917.s004) | `71dc8689d8f0ec4c17be5f7bdd1410ce173a69d7239c0728c7861f8ee6fc1a8f` |
| E48 三次元撮影の図3、原寸PNG | [niwayama3.png](https://journals.plos.org/plosone/article/figure/image?size=large&id=info:doi/10.1371/journal.pone.0159917.g003) | `c739ec22d568c988b744327a125ed61d907cb82aab8f09539a6f9a448bbda0af` |
| E47 S1 Data、図の元となる個体別の値 | [oocyte.xlsx](https://journals.plos.org/plosbiology/article/file?type=supplementary&id=10.1371/journal.pbio.3001376.s007) | `b9b35776e7300b4ff4a4df783a4a74a6971b9aaf870ad69caa4c8259e3cc1a57` |

NDLの2点は収載された原著のページ画像。1976年の図4と本文の距離は転記し、1978年の図3・8は解像度・測定座標・目盛を保存した。PMC掲載図では本文の供給物と母数を確認した。PLOSの2研究は公開全文と図説明を照合した。速度表を開くとopenpyxlが未対応の拡張部分について警告する。表への書き戻しは行わず、数値列、標本数、座標の有限性、図の平均値との対応を各資料に応じて検査した。一次資料のライセンスと利用条件は各公開元を参照。

## 取得と再実行

リポジトリのルートで次を実行する。ネットワークが必要なのは依存パッケージと原本を取得するとき。すでに取得した原本は同じ名前・同じSHA-256で読み込める。

```bash
python3 -m pip install -r experiments/requirements.txt \
  -r experiments/E29_growth_holdout/requirements.txt \
  -r experiments/E23_nitrate_pin2/requirements.txt
torus_run=$(mktemp -d)
python3 -m experiments.measured_return_sources --raw "$torus_run/raw"
python3 -m experiments.run_measured_return --raw "$torus_run/raw" \
  --out "$torus_run/results" --log "$torus_run/run.json"
sed "s|research/results/|$torus_run/results/|" research/results/MEASURED_RETURN_SHA256SUMS | sha256sum -c -
```

実行環境はDebian 13 x86_64、Python 3.12.14、NumPy 2.3.5、SciPy 1.17.0、Matplotlib 3.10.8、Pillow 13.0.0、PyMuPDF 1.26.6、openpyxl 3.1.5。数値計算は各プロセス1スレッド。E47の個体再標本化は乱数種470013、8,000回。公開元から取得し直した原本7点を検証し、数値5点と図2点が保存版にバイト単位で一致した。[全ステップの実行ログ](../results/MEASURED_RETURN_RUN.json)・[結果のSHA-256](../results/MEASURED_RETURN_SHA256SUMS)
