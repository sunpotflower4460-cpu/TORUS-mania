# 再開メモ　E01〜E08の登録試験を実行済み

更新2026-11-20 UTC/JST。研究ブランチ `research/e03-e08` は、初回E01・E02の `research/e01-e02-calibration`（`81459c4`）を継承する。本文と全数値は[第2回報告](../docs/11_SECOND_RESEARCH_REPORT.md)、全12主張の判定と証拠の種類は[主張台帳](claims.json)にある。

## 何を引き継ぐか

| ID | 保存したもの | 判定に残る範囲 |
|---|---|---|
| E01・E02 | 円運動・直線振動の投影、二位相・再帰・同期の校正。[第1回](../docs/10_FIRST_RESEARCH_REPORT.md) | 独立二位相の状態空間、見かけの波形から物体の形は決まらない |
| E03 | [既知解・実空間の渦と粒子](results/E03/summary.json)、[軸対称円筒](results/E03/cylinder/summary.json)、[くびれと整合したランダム場](results/E03/observers/summary.json) | 同じ渦輪から輪状渦度とくびれを得た。無渦の解析流にもくびれが出た。H03は部分支持 |
| E04 | [144構成と全切断](results/E04/)、[植物5群・5,205区間の再集計](results/E04/plant/summary.json) | 木で全量供給可能。植物の根・枝の成長法則は未同定 |
| E05 | [位相への介入と6条件の二輪](results/E05/) | 同期・共有外力・直接作用を識別。H06は相互作用に限る部分支持 |
| E06 | [静止からの噴流8条件と円形追加格子](results/E06/) | 細格子の輪候補には仮定した出口と検出閾値が効く。低閾値の両格子は不一致 |
| E07 | [事前予測と参照解](results/E07/) | 小信号の合成水路で共通式の予測が通った。独立な実測ターゲット0件 |
| E08 | [凍結した5検索](results/E08/ranking.json)、[現象名20件の採否・根拠と集計](results/E08/summary.json) | 採択16件、8件で対象の形を判定可能。理論論文のモデルと実測を区別。自然そのものの頻度は未測定 |

H01・H02は条件内支持、H03・H06は部分支持、H04・H05・H07・H08・H09・H10は全体として未決、H11・H12の一般推論には反例がある。H09のうち「無損傷の端子間輸送には閉路が必須」という限定命題は不支持。独立した外部データセットの再集計は植物1件。E07の評価用合成データとは別に数えた。[根拠台帳](../docs/03_EVIDENCE_LEDGER.md)

## 再現に必要な入力と版

- 第2回事前登録 `12222c9`、E07未見評価の設計 `d4d2c4f`、参照計算前に封印した圧力予測 `7e279f5`。軸対称計算の登録 `5705077`、くびれ・ランダム場 `094418b`、円形噴流の格子追加 `f92373e`。追加観測が既存結果のどこを見た後かを各票に記した。[登録票](registrations/)
- 最終計算コード `3fb98c2`、Debian 13 x86_64、Python 3.12.14、NumPy 2.3.5、SciPy 1.17.0、Matplotlib 3.10.8。外部ソルバー・GPUは使用していない。E08は保存済みの順位とDOI別判定で追試できる。植物ワークブックは別取得。[パッケージ版](../experiments/requirements.txt)・[入力の帰属](notes/S012_branching_data.md)・[アクセス記録](access/2026-11-20-second.md)
- 最終版をGitから別ディレクトリへ展開し、空の結果ディレクトリに25プロセスで全計算・集計・描画を再実行した。各終了コード0、校正・収支等70項目すべて合格。CPU計340.8秒、壁時計の合計341.7秒、最大ピーク常駐181.6 MiB。生成した64ファイルは初回の同版成果物とバイト単位で一致した。ハッシュ一覧65件には凍結した検索順位入力1件も含む。比較用の時計・リソース情報自体は決定論的な成果に数えない。[実測ログ](results/SECOND_RUN.json)・[SHA-256一覧](results/SECOND_SHA256SUMS)

## 第2回の追試

以下はLinuxのリポジトリルートで実行する。初めてこの環境で追試する場合、上記バージョンのライブラリと、次の公開ワークブックが必要。すでに同じSHA-256の原本がある場合は取得を省ける。文献検索や動画視聴は再計算の入力に含まれない。

```bash
mkdir -p data/raw/second
curl --fail --location https://ndownloader.figshare.com/files/25763342 -o data/raw/second/branching.xlsx
sha256sum data/raw/second/branching.xlsx
sha256sum -c research/results/SECOND_SHA256SUMS
export MPLBACKEND=Agg OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1
run_dir=$(mktemp -d)
python3 -m experiments.run_second --workbook data/raw/second/branching.xlsx \
    --out "$run_dir/results" --log "$run_dir/run.json" --code-id "$(git rev-parse HEAD)"
python3 - "$run_dir/results" <<'PY'
from hashlib import sha256
from pathlib import Path
import sys
expected = Path("research/results")
count = 0
for line in (expected/"SECOND_SHA256SUMS").read_text().splitlines():
    digest, filename = line.split(maxsplit=1)
    relative = Path(filename).relative_to(expected)
    if str(relative) == "E08/ranking.json":
        continue  # frozen input in this checkout
    data = (Path(sys.argv[1])/relative).read_bytes()
    if sha256(data).hexdigest() != digest:
        raise SystemExit(f"Different output: {relative}")
    count += 1
print(f"{count} generated files match")
PY
```

全実行の入口は[run_second.py](../experiments/run_second.py)。円形噴流の基本群は `python3 -m experiments.E06_jet.run --case circle --out /tmp/jet`、6 m箱での格子追加は同じモジュールの `--refine-circle`。E07は `predict` の出力を同じ場所で `run` が参照する。事前予測の履歴は `git show 7e279f5:research/results/E07/predictions.json`。E08順位は再現用の入力で、現在のAPI順位を取得して比較する場合のみ `python3 -m experiments.E08_survey.fetch /tmp/new-ranking.json` を使う。版の異なる環境ではハッシュとともに軸上誤差・収支・閾値別の結果も比較する。

### 出力の読み方

- E03・E05・E06のJSONは `rows` に0.125秒ごとの位置・速度/圧力/渦度の極値、最大成分の穴・空洞・境界接触、運動エネルギーを持つ。速度 m/s、渦度 s⁻¹、箱の圧力は密度1 kg/m³で空間平均を0とした値（Pa）。渦核は軸方向位置・半径・RMS幅の順、距離はm。NPZ断面の行列はx,zの順で、キーの末尾は積分ステップ番号。E05の位相NPZは別形式で、時刻・結合条件・初期種・介入・系・位相成分の順。
- E04の `networks.npz` に候補点・辺・伝導度と40切断×4指標、E07に規格化圧力161時刻×7×7、E08にDOI単位の判定・アクセス段階・理由を保存。[科学図3点](results/figures/)
- 論文本文・動画・ワークブックはGit配布に含めていない。外部入力のありか・SHA-256・ライセンスは[文献カード](notes/)に記録した。

## 次に判別力のある観測

1. H03のくびれを、時間分解した実測速度から固定流量で求める。圧力・渦度・粒子のどれを同じ流れに割り当てられるかを確認する。
2. H05・H08では、閉路の有無を独立に操作した水路の圧力応答、または損傷前後の植物成長を、測定前に予測できる候補式と対にする。今回のE07の参照場で再調整して成功例を増やさない。
3. H07・H10の外部評価には分野別の自然標本の抽出枠、または動的宇宙モデルに固有の可観測量が必要。動画2本はフレームとの原図照合が残る。[動画の追跡](../docs/08_VIDEO_NOTES.md)

## 初回E01・E02の再現コマンドと出力

リポジトリのルートで実行する。実測環境はPython 3.12.14、[再現環境の依存パッケージと版](../experiments/requirements.txt)は既設。資料の再取得、外部サービス、GPUは不要。最初のテスト19件にはサードパーティのライブラリは不要で、次の3件は角の折返し・再帰の数え方・密度格子の端点を検査する。

```bash
python3 scripts/research_access.py --help
python3 scripts/research_access.py list
python3 -m unittest discover -s tests -v
python3 -m unittest experiments.E02_phase_space.test_observations -v
export MPLBACKEND=Agg OPENBLAS_NUM_THREADS=1
python3 -m experiments.E01_projection.run --pilot
python3 -m experiments.E01_projection.run
python3 -m experiments.E02_phase_space.run --pilot
python3 -m experiments.E02_phase_space.run
sha256sum -c research/results/SHA256SUMS
```

各コマンドは既定の結果保存先を更新し、判定失敗時は非ゼロで終了する。別ディレクトリを使う場合は各runに `--out` で出力先を指定できる。同一環境・新規に展開したコードだけの作業場所で、結果9ファイルがバイト単位で一致した。環境が変わると描画や浮動小数点の末尾は変わり得るので、その場合はJSONの誤差・対照も確認する。

### 数値と表示の読み方

| 保存先 | 内容 |
|---|---|
| [E01の全試行](results/E01/summary.json)・[予備](results/E01/pilot/summary.json) | 初期位相、R、刻み、正弦誤差、周波数成分、各投影の1・2秒後の初期点からの距離、全表面の幅と判定。 |
| [E01の観測列](results/E01/observations.npz) | 例えば `base_128/t_s`、`base_128/circle/xyz_m` は時刻と3列の位置、`base_128/circle/vy_m_s` は着色前の符号付き速度。 |
| [E02の全試行](results/E02/summary.json)・[予備](results/E02/pilot/summary.json) | 比・結合・雑音・種、観測窓ごとの回転数比、位相差・再帰・密度、解析解との誤差。再帰なしは初回時刻がnull。 |
| [E02の観測列](results/E02/observations.npz) | `t_128_s` が時刻。例として `three_halves_128/` 以下の `phase_rad` は折り返し前の2つのモデル位相、`observed_rad` は観測位相、`wave` は各成分の正弦、`delta_rad` は観測位相差。 `return_distance_rad` は初期観測からの周期距離、`entry` の列はε=0.02, 0.05 radの順。 `density_8s` と `density_80s` は格子ごとの標本数（行が位相1、列が位相2）。 |
| [実行ログ](results/RUN.json)・[検証用ハッシュ](results/SHA256SUMS) | 4実行の開始時刻、終了コード、壁時計時間・CPU時間・ピーク常駐メモリ。各summaryには実行コードのSHA-256もある。 |

NPZは `numpy.load` で開ける。次は元の計算結果を読み、カメラと対応する時刻だけを変えて別図を出力する例。角度は度、時刻は秒で、最も近い保存標本を指す。

```bash
python3 -m experiments.E01_projection.figures research/results/E01/observations.npz /tmp/torus-another-view.png --time 1 --azimuth 35
```
