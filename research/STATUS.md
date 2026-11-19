# 再開メモ　E01・E02完了

更新 2026-11-20 JST（実行日2026-11-19 UTC）。研究ブランチは `research/e01-e02-calibration`。出発点は `37e7f7a`、事前登録は `2647189`、計算コードは `08a061b`、成果の固定は `5e49cb4`。コード固定後の `d7c81b2` では実験用テストの配置だけを変更した。

## 引き継ぐ判断

E01の同一観測（R1）、E02の二位相の表現（R2）に限ってH01・H02を `analytic_baseline` から `supported_within_scope` に更新した。H11・H12は一般推論の反例を記録し、従来の判定を維持した。H03–H10はopen。循環単位同士の関係に関して測れた量は、選んだ二振動子モデルの位相差・同期までである。[第1回研究報告](../docs/10_FIRST_RESEARCH_REPORT.md)・[主張台帳](claims.json)

- E01は6運動×2設定×2刻み。上面だけでトーラスと誤認した対照は4面中2面、正面を加えると0面。円と直線ばねのyは一致し、xでは区別できた。
- E02は10条件×2刻み×2観測窓。無結合の3/2は2秒で再帰。99/70と√2指定はともに80秒で全256区画に入った。主閾値0.02 radでの標本上の再帰回数は前者1、後者0。連続モデルの標本間の近接は報告本文に示した。
- 予備試行はE01で8項目・E02で25項目、本試行は32・78項目を照合し、失敗0。予備試行と本試行には重複した設定がある。これらの項目数は独立な自然現象の標本数としては用いない。
- 文献カードは索引8件と追加の輸送網研究1件。回転、面の幾何、二周期、磁場、実在の渦、神経の集団活動、植物輸送、宇宙位相の出典・閲読箇所を記録した。外部データの再解析、動画の直接視聴、E03–E08の実行は未実施。[カード](notes/)・[今回のアクセス](access/2026-11-20.md)

## 再現コマンド

リポジトリのルートで実行する。実測環境はPython 3.12.14、[必要な2パッケージと版](../experiments/requirements.txt)は既設。資料の再取得、外部サービス、GPUは不要。最初のテスト19件にはサードパーティのライブラリは不要で、次の3件は角の折返し・再帰の数え方・密度格子の端点を検査する。

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

## 次の識別試験

1. **E03 A。** 渦輪の半径・核幅・循環と比較用の無流動、一方向流、せん断、局所回転を登録する。同じ場から速度・渦度・粒子通過を求め、中心や輪がどの量に現れるかを比べる。発散残差・境界収支・刻み依存を先に評価する。与えた輪を自発生成に数えない。
2. **E04。** 同じ材料量・供給消費で固定需要・変動需要と損傷を比べ、独立閉路数と未供給量を測る。グラフの迂回路、物質の周回、T²面を別々に記録する。E07の共通方程式はまだ定まっていない。
3. **E08。** 頻度測定の分野、採択期間、現象名での抽出、重複・欠測、形の基準を新規抽出より先に登録する。今回読んだ目的選択資料は頻度用の分母に入れない。

初回本試行の壁時計時間はE01が3.23秒、E02が2.92秒。ピーク常駐はそれぞれ約95.6、87.6 MiB。実験はすべて終了した。S002の取得上限による停止とその解決、動画や論文ページへの未達はアクセス記録を参照。文献カード・数値を読むために、取得できなかったURLや準備時のBioCリクエストを再試行する必要はない。
