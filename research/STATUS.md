# 再開メモ　先にある流れと器官の形成のE16〜E18まで実行済み

更新2026-11-20 UTC。`research/flow-before-form` はE13〜E15の `research/dynamic-circulation`（`57f16ab`）を継承する。発生前の局所の力や組織の伸びやすさが後の器官の位置に影響する命題（H17）を公表実験で支持した。先行するトーラス状の流れが成長先を変える命題（H18）は登録した材料モデルの範囲で支持した。生体の三次元の閉循環を変えたときの器官の形成は未判定。[第5回報告](../docs/14_FLOW_BEFORE_FORM_REPORT.md)・[全18主張の台帳](claims.json)

## 第5回の結果と追試

| 実験 | 再開に使うもの | 判定 |
|---|---|---|
| E16 | [図の数値](results/E16/summary.json)・[胚の文献カード](notes/E16_developmental_forces.md) | 右側刺激で心臓が右寄りになる率は69.4〜71.4%、左側刺激で7.8%。公表図の各整数候補、中央の個体を含む割合、試行内相関を推定できない限界を保存。 |
| E17 | [格子・時間刻みの比較](results/E17/summary.json)・[断面図](results/morphogenesis_figures/flow_and_growth.png) | 先行する運動エネルギー密度を保ち、流れを反転すると取り込みの重心が円筒半径の33.7%ずれた。成長した材料に輪候補は現れなかった。 |
| E18 | [植物の再集計](results/E18/summary.json)・[文献カード](notes/E18_plant_organ_placement.md) | 曲げた側の側根や、伸びやすさを変えた位置の葉で、対照より発生しやすい。根の戻り輸送はタンパク質の位置から推定された。 |

事前登録は `5db08ae` と `49d83c3`、計算の版は `aff8ebb`、最終集計・描画は `66c5f47`。Debian 13 x86_64、Python 3.12.14、NumPy 2.3.5、SciPy 1.17.0、Matplotlib 3.10.8、図の再抽出にPillow 13.0.0。乱数種なし。Gitから展開したコードで、E17の3条件を3プロセス・各数値ライブラリ1スレッドで再計算し、約331秒。全件で31の校正・収支チェックを通過し、成果物11点がバイト単位で一致した。既存単体テストは22件通過。[実行ログ](results/MORPHOGENESIS_RUN.json)・[SHA-256](results/MORPHOGENESIS_SHA256SUMS)

追試はリポジトリのルートで実行する。E16の図読取り値とE18の表・本文の数値を固定入力にした。再集計とE17の計算はネット不要。[固定した図読取り](../experiments/E16_developmental_intervention/figure_readings.json)・[植物の入力](../experiments/E18_organ_placement/published_values.json)

```bash
python3 -m pip install -r experiments/requirements.txt Pillow==13.0.0
run_dir=$(mktemp -d)
python3 -m experiments.run_morphogenesis --out "$run_dir/results" --log "$run_dir/run.json"
sed "s|research/results/|$run_dir/results/|" research/results/MORPHOGENESIS_SHA256SUMS | sha256sum -c -
```

E16の図を元画像から読むときは[取得記録](access/2026-11-20-morphogenesis.md)のJPEGを取得し、
`python3 -m experiments.E16_developmental_intervention.read_figure data/raw/morphogenesis/djenoune_fig4.jpg --out /tmp/torus-form-reading.json`。
E17の `fields.npz` に規格化した子午面の座標・流れ・供給源・種・形成前後の資源分布・成長後の材料・積算取り込みがある。行は半径、列は高さ。対照の並び順と各時刻の積算収支は同じフォルダのJSONにある。

次に区別する問いは、閉じた循環があるときの固有の効果。同じ供給量と初期形のもとで戻り経路を変え、三次元の流れと後の器官の位置を同じ対象で追う。植物では既知の根端の戻り輸送が候補になる。[第5回報告](../docs/14_FLOW_BEFORE_FORM_REPORT.md)

## 第4回の結果と追試

第4回は `research/dynamic-circulation` がE09〜E12の `research/energy-principle`（`d6335dd`）を継承した。渦度と受動磁場の共通輸送（H15）と、輪の動く境界のエネルギー交換（H16）を登録条件で支持した。[第4回報告](../docs/13_DYNAMIC_CIRCULATION_REPORT.md)

| 実験 | 再開に使うもの | 主な結果 |
|---|---|---|
| E13 | [7条件の数値](results/E13/)・[式と文献](notes/E13_flux_and_mhd.md) | 無拡散の渦度・磁場は移動断面に99.97%を保った。速い磁気拡散で38.12%。輪は初期条件に与え、磁場からの反作用を省いた。 |
| E14 | [2パルス・2格子の収支](results/E14/)・[輸送定理と光の重心](notes/E14_energy_transport.md) | 形の続く真空パルスでエネルギーは移動境界を両向きに通る。円形噴流で渦度とエネルギー密度の形が異なり、粘性と圧力も収支に寄与した。 |
| E15 | [再集計した数値と曲線](results/E15/)・[公開配列の出典](notes/E15_collision_piv.md) | 衝突後の乱流エネルギーが広がった。前半の二次モーメントの直線は後半の予測で一定値に劣った。交差項の比は元の量から符号つきで再計算した。 |

第4回事前登録は `520fb53`、追加観測は `19136d4`、光重心の解析対照は `a5e0e18`。最終計算・描画は `4b39db8`。Debian 13 x86_64、Python 3.12.14、NumPy 2.3.5、SciPy 1.17.0、Matplotlib 3.10.8。E15のHDF5読取りだけh5py 3.15.1を追加した。すべて決定論的で乱数種を用いていない。GPUを使わず各数値ライブラリ1スレッド、3プロセスまでで追試した。Gitから新規に展開したコードで約174秒、53項目の校正・収支チェックを通過し、26個の数値と図の成果物が初回とバイト単位で一致した。[実行ログ](results/DYNAMICS_RUN.json)・[成果物のSHA-256](results/DYNAMICS_SHA256SUMS)・[図](results/dynamics_figures/)

追試はリポジトリのルートで実行する。データを既に取得した場合は同じファイルを `--raw` で指定できる。取得が必要な場合はZenodoの版固定URLから3ファイルを保存する。[取得記録・原本のハッシュ](access/2026-11-20-dynamics.md)

```bash
python3 -m pip install -r experiments/requirements.txt -r experiments/E15_collision_data/requirements.txt
mkdir -p data/raw/dynamics
for source_file in Fig1B_Energy_spreading.h5 Fig4B_energy_distribution.h5 Fig5A_kymograph.h5; do
  curl --fail --location --retry 2 \
    "https://zenodo.org/api/records/18380405/files/$source_file/content" \
    -o "data/raw/dynamics/$source_file" || exit 1
done
run_dir=$(mktemp -d)
python3 -m experiments.run_dynamics --raw data/raw/dynamics \
  --out "$run_dir/results" --log "$run_dir/run.json"
sed "s|research/results/|$run_dir/results/|" research/results/DYNAMICS_SHA256SUMS | sha256sum -c -
```

E13の配列は `flux` が時刻×4断面×場、`flux_diffusion_rate` は面の縁の積分から求めた時刻変化。`energy`、`dissipation_power`、`stretching_power` は時刻×場。場の順序と単位は各JSONにある。E14の各 `fine_moving` などは蓄積と積算した流出入・散逸、収支残差を `budget_columns` 順に持つ。光の時間は q₁/c、エネルギーはJSON記載の倍率でSI単位に変換できる。E15の `observables.npz` は幅の時系列と前半で学習した予測、3装置の符号つき分解を、JSONの列順に持つ。元データと分解の範囲は[出典カード](notes/E15_collision_piv.md)に記録した。

新しい実測課題は、同期した三次元速度・磁場、または電磁場の時空間計測から、移動境界での流束を直接照合すること。渦輪同士の衝突では、集合平均に入る前の個別試行で境界・流束・交換の回復を測り、再形成の持続時間を衝突条件と対照する。[研究報告](../docs/13_DYNAMIC_CIRCULATION_REPORT.md)

## 第3回の結果と残る証拠

| 実験 | 保存したもの | 判定 |
|---|---|---|
| E09 | 充実トーラス・厚い殻・薄い殻・切断、3格子、零断面流束の対照。[数値](results/E09/summary.json) | 閉経路が循環の自由度を決め、同じ幾何係数が流体の運動エネルギーと静磁場エネルギーに現れる。 |
| E10 | 公開測定4研究の図読取り。他の装置仕様からの17点の磁場予測、3つのMEMSコイル、超流動の回転率と8設定の持続率。[採点](results/E10/summary.json)・[出典](notes/E10_energy_observations.md) | 磁場と循環の持続は支持。コイル全体・回転率の事前精度は未達。生データによる再解析1件（第2回の植物）とは件数を分けた。 |
| E11 | 局所の機械エネルギー収支と真空Maxwellパルスの電磁エネルギー・ポインティング流束。[流体](results/E11/fluid/summary.json)・[光](results/E11/light/summary.json) | 渦度と運動エネルギーの形が異なった。光の解析解に電磁エネルギーの輪も成立。実測流束の入力は未取得。 |
| E12 | 別設定で、断面から三次元の形を予測。パルス24/24、円形噴流16/16、スリット比較8/8。[全採点](results/E12/) | 実空間の形の予測に支持。異分野で同じ時間発展方程式が成り立つかは未判定。 |

第3回から残るのは、コイル全体の磁気エネルギーを測るための外部場データ、超流動の実効半径と回転率の独立な校正、枝の成長と同時に物質・エネルギー収支を測るデータ。宇宙の動的な構造にはモデル固有な観測予測が必要。[文献・アクセス記録](access/2026-11-20-energy.md)

## 第3回の追試

事前登録は `eb5fbce`、公開図の追加照合は `a043401`、断面から輪を予測する追加登録は `1aa5387`。数値コードと図を `fe0e9c8` のGit履歴から別の場所に展開し、24校正項目と16個の成果物を照合した。[実行ログ](results/ENERGY_RUN.json)・[SHA-256](results/ENERGY_SHA256SUMS)

リポジトリのルートで既存のPython依存を使う。公表図からの読取値は固定入力なので、計算だけならネット接続・PDFは不要。

```bash
out_dir=$(mktemp -d)
python3 -m experiments.run_energy --out "$out_dir/results" --log "$out_dir/log.json"
sha256sum -c research/results/ENERGY_SHA256SUMS
python3 - "$out_dir/results" <<'PY'
from hashlib import sha256
from pathlib import Path
import sys

expected = Path("research/results")
replay = Path(sys.argv[1])
count = 0
for line in (expected / "ENERGY_SHA256SUMS").read_text().splitlines():
    digest, name = line.split(maxsplit=1)
    path = Path(name).relative_to(expected)
    if sha256((replay / path).read_bytes()).hexdigest() != digest:
        raise SystemExit(f"Different output: {path}")
    count += 1
print(f"{count} generated files match")
PY
```

図そのものから再抽出する場合は、文献カードと読取りコードに書いた版のKumar arXiv v3 PDFとVinitskiyのFig. 4 JPEGを取得する。ローカルで `python3 -m experiments.E10_energy_observations.read_figures --raw data/raw/energy --out /tmp/torus-energy-figures.json`。PyMuPDF 1.26.6、Pillow 13.0.0を使用。材料諸元と手で読んだ図の値はソース名を付けて同じディレクトリに記録した。[固定図入力](../experiments/E10_energy_observations/figure_values.json)・[固定表入力](../experiments/E10_energy_observations/table_values.json)

### エネルギーの出力

- E09のJSONの係数は、各方向の周回値を1とした場の二乗ノルム（m）。E10は磁場、磁気エネルギー密度、インダクタンス、回転率・持続率の元の単位を保持する。
- E11の流体NPZの `budget` は時刻、内部の蓄積、外向き積算流束、積算散逸、残差、箱全体のエネルギーの順。光のNPZの各場は規格化し、出力JSONに時間・エネルギー・電力のSI換算を記した。
- E12のJSONの各行に一断面の予測、三次元判定、閾値、時刻、格子がある。「合格」は対応する数値校正の範囲であり、実測が予測と一致しなかった試験も残した。[図](results/energy_figures/)

## 第2回までの結果

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

## 第2回実施時の次の観測

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
