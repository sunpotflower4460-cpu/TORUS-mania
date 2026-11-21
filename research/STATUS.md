# 再開メモ　無傷根の横断と胚の力・仕事をE72〜E76で検証

2026-11-21 UTC。第17回 `research/iaa-return-and-embryo-work`（`b55c87c`）を継承し、`research/calibrated-embryo-work-and-root-tip` で実行した。根冠が軸方向の回収に与える影響と無傷根の横断、局所の校正された機械仕事、エネルギー収支と閉路の識別を調べた。同じ天然IAAの一周（H44）と、身体形成に先行する三次元のエネルギー循環（H45）は未判定。[第18回報告](../docs/27_ROOT_CAP_AND_CALIBRATED_WORK_REPORT.md)・[全78主張](claims.json)

| 実験 | 主な結果 |
|---|---|
| [E72](results/E72/summary.json) | ニワトリ神経管の閉鎖中の60分で、対照+84.1 nN、ROCK阻害−54.8 nN（各10胚）。対照の個体別の最大仕事は平均1.026 pJ。 |
| [E73](results/E73/summary.json) | 一つのゼブラフィッシュ胚の仕事率図で、60%の下3分の1の暖色は0、80%では99/251画素。40%は暖色が検出されず、全段階の重心仮説は判定できない。 |
| [E74](results/E74/summary.json) | 無傷根の対向側の90分の下向き／上向きは無添加3.62、添加3.11。別の3時間測定では回収標識がIAA標準と薄層クロマトグラフィー上で一致。 |
| [E75](results/E75/summary.json) | 同じ品種の5 mmの根端片、pH 6の基部向き／根端向きは対照で6.33、根冠切除で0.634。切除後は根端向きが8.66倍。 |
| [E76](results/E76/summary.json) | 同じ境界流束と体積収支で、内部に閉路がある場とない場を構成。3種点の最大帰還誤差は128刻みで1.46×10⁻⁷。 |

登録は `61c5f24`、本集計前の資料の構造と採点の追記は `89882c1`、実装は `b68987c`、図の調整は `52e0ed5`、力積の単位換算をそろえた再実行版は `747c849`。Gitから展開したコードで公開入力11点を新しく取得し、数値5点と図2点をバイト単位で照合した。今回の検算18項目、既存テスト22件、過去17組215項目のSHA-256を確認した。[公開原本と再実行](access/2026-11-20-calibrated-formation.md#再実行)・[実行ログ](results/CALIBRATED_FORMATION_RUN.json)・[SHA-256](results/CALIBRATED_FORMATION_SHA256SUMS)

**再開後に判定すること。** H44は無傷の同じ根で、内側から根端と外層を順に通り元へ戻る標識を回収する。根冠の介入は切断と接触面の影響を照合し、残留、外部からの混入、抱合型からの再生成を分ける。H45は最初に閉鎖や被包の終点を具体的な形で定める。閉鎖や被包が進む前の同一胚で三次元速度と圧力・応力から機械エネルギー流束を復元する。境界の出入りと局所の仕事を照合し、閉路の操作と同程度の仕事を加えた条件で、その後の形を比較する。[二つの仮説の次の判定](../docs/27_ROOT_CAP_AND_CALIBRATED_WORK_REPORT.md#二つの仮説の次の判定)

## 引き継いだ第17回

2026-11-20 UTC。第16回の `research/whole-embryo-paths-and-root-labels`（`e794299`）を引き継ぎ、`research/iaa-return-and-embryo-work` で検証。無傷根の同一IAAの一周（H44）と、三次元トーラス状の機械エネルギー循環による身体形成の先導（H45）は未判定。[第17回報告](../docs/26_IAA_REENTRY_AND_EMBRYO_WORK_REPORT.md)・[全73主張](claims.json)

| 実験 | 結果 |
|---|---|
| [E67](results/E67/summary.json) | レベル1の像で前向き13/31時点、逆向き3時点。緩めた前向きは31時点まで続いたが、最後に出発点から40.8単位離れ、一周の判定は通らなかった。 |
| [E68](results/E68/summary.json) | トウモロコシ根片から外へ出た標識が再び取り込まれるとする公開抄録を確認。別の図8では根冠付き先端の¹⁴C不足24.5%、根冠なし2.8%。 |
| [E69](results/E69/summary.json) | 胚帯の伸長開始時の光介入後15分で、長さは対照1.71、増加1.36、抑制1.29。原著の対照との差は増加p=0.06、抑制p=0.02。 |
| [E70](results/E70/summary.json) | 三次元で物質を通さない同じ面でも、粘性0.001 Pa sで5.24×10⁻¹⁷ Wのエネルギーが入り内部散逸と一致。無粘性で0 W。 |
| [E71](results/E71/summary.json) | 4分後の抽出物で標識の約92%はIAA標準と同じ位置のピーク。生重量と切片で中心柱・皮層の取込みの比較方向が変わる。 |

登録は `ed4041e`、`ee1e5ca`、`956ad93`。平均線の途切れに対する読み方を `d24a4d4` で記録。実装は `f520536` と `5930ac6`。Gitから展開した場所で6入力を再取得し、公開体積像33ファイルはハッシュの合うコピーを使った。数値5点と図2点のSHA-256が一致し、今回の検証17項目・既存のテスト22件・過去16組208項目を確認した。[公開原本と再実行](access/2026-11-20-iaa-embryo-work.md#再実行)・[実行ログ](results/IAA_EMBRYO_WORK_RUN.json)・[SHA-256](results/IAA_EMBRYO_WORK_SHA256SUMS)

**再開後に判定すること。** H44は、無傷の根で標識の二つ以上の位置を確認できる測定を使い、内側の開始・根端・外層・内側への最初の帰還を一つの経路に対応させる。残留、外部からの再供給、局所合成や代謝からの再生成を対照にする。H45は観察の始点より後に現れる形を一つ指定し、同じ胚で力学的な流束と閉路、内部駆動、仕事と散逸を計測する。閉路を変えたとき、同じ程度の入力仕事の対照と後の形を比べる。[検証の範囲と未判定](../docs/26_IAA_REENTRY_AND_EMBRYO_WORK_REPORT.md#二つの仮説の判定)

## 引き継いだ第16回

更新2026-11-20 UTC。第15回の `research/particle-return-and-auxin-balance`（`4601ecb`）から `research/whole-embryo-paths-and-root-labels` を作業した。根で同じ天然IAAが一周するH44と、形が成立する前の三次元トーラス状エネルギー循環が形を先導するH45は未判定。外部張力による体軸変化、三次元の細胞の帰還候補、根の通過と抱合の履歴を検証した。[第16回報告](../docs/25_EMBRYO_RETURNS_AND_ROOT_LABELS_REPORT.md)・[全68主張](claims.json)

| 実験 | 結果 |
|---|---|
| [E61](results/E61/summary.json) | 表面の逆向きの渦が優勢になっても、4胚で元の原条は元の位置で伸びた。分裂停止下には渦と短い原条が共存。渦間隔の表示のばらつきを標準偏差とするとp値は原著と一致しない。 |
| [E62](results/E62/summary.json) | ゼブラフィッシュ1胚の連続10時点以上の283,972区間のうち115本で三次元の帰還候補。帰還半径を半分にすると20本。 |
| [E63](results/E63/summary.json) | 外部張力を保つと後の収束速度は11.90 µm/時低下。別装置では+17.28から−19.06 µm/時。膜試料の押し込みで始点の力から増えた分の仕事は開始日3.32 µJ、2日目1.14 µJ。 |
| [E64](results/E64/summary.json) | 経路65%・過去に抱合30%を同じ回収集団で測った模型の下限は35%、上限は65%。読み違い10%ずつの500件の同時読み取りでは、真の40%と55%の区間が分かれた。 |
| [E65](results/E65/summary.json) | 同じ撮影の二つ目の追跡版で、緩い照合では同じ形の帰還が6本。厳しい照合は0本で、時間をずらした対照も0本。 |
| [E66](results/E66/summary.json) | E65で最も大きく離れた候補の31時点を画像で追うと、開始位置から3時点で途切れた。 |

E61〜E64の登録は `f4223ca`、図と原データの制約を `5382da5` で追記。E65は `c89e574`、E66は `bcb44a0` で分析前に登録した。実装は `5145d13`、最終の図は `00748bf`。公開原本8件を新しい場所に取得し、Gitから展開したコードを実行した。数値結果と候補一覧7点、図2点のSHA-256を照合した。今回の判定と計算条件の確認は23項目、既存ユニットテスト22件と過去の15組199項目を確認済み。[取得と再実行](access/2026-11-20-embryo-history.md#再実行)・[実行ログ](results/EMBRYO_HISTORY_RUN.json)・[SHA-256](results/EMBRYO_HISTORY_SHA256SUMS)

**次に判定すること。** H44は残留と標識交換を校正し、同じ標識が根端と外層を経て内側へ最初に戻る割合を測る。経路と抱合の履歴を対応させるか、測定した周辺割合から保守的な下限を出して、遊離のままの一周の検証へ進む。H45は帰還候補を元の高解像度または疎な別チャネルで確認する。力が後の形に作用する段階では、同じ胚で圧力・応力による仕事と軌道を計測し、閉路の変更と、投入仕事をそろえた対照で後の形を比較する。[二つの仮説の現在地](../docs/25_EMBRYO_RETURNS_AND_ROOT_LABELS_REPORT.md#二つの仮説の現在地)

## 引き継いだ第15回

更新2026-11-20 UTC。第14回の `research/turning-paths-and-axis`（`415df70`）から `research/particle-return-and-auxin-balance` を作業した。根での同一IAAの一周（H44）と、形を先導する三次元のトーラス状エネルギー循環（H45）は未判定。今回の目的は、実時間の追跡と、化学信号から判断できる範囲を確認すること。[第15回報告](../docs/24_PARTICLE_RETURN_AND_AUXIN_REPORT.md)・[全62主張](claims.json)

## 第15回の結果と追試

| 実験 | 結果 |
|---|---|
| [E55](results/E55/summary.json) | 地上部を切った根に投与した¹⁴C–IAAの8時間後。根端の表示信号では遊離IAAの窓が3.29%、酸化型とその糖抱合体の窓は合計50.5%。 |
| [E56](results/E56/summary.json) | 地上部を除いた根の先端0〜0.5 mmの標識新生IAA／非標識IAAは0.51。無傷苗の1.01と比較。 |
| [E57](results/E57/summary.json) | 洗出し10分後のFRETの上昇分は10分投与で約47%残り、1時間投与で基線より下がった。 |
| [E58](results/E58/summary.json) | 1胚の7つの1分区間で中央と外側の長軸方向の中央値は逆向き。60秒以上の追跡27本は出発点から5 µmに届かず、一周の検査に十分な軌跡は0本。 |
| [E59](results/E59/summary.json) | 平面切断で12秒後に切断から遠ざかる変位が1.47 µm増え、弧状切断では30秒後の前進が1.74 µm減った。 |
| [E60](results/E60/summary.json) | 6時間後、標識の抱合体から遊離したIAAは野生型20.62、加水分解に関わる変異株0.405 pmol/g。 |

初回の登録は `981dc50`、E58の折り返しと追跡条件を `0739ab3` で補足。一次の追跡後に追加した追跡時間の検査は `62d83b0`。E59の公表図を見た時刻の指定と、E60の数値抽出前の登録は `a81faeb`。E59の凡例の映り込みを修正した最終コードは `65d8909`。公開元から9件を取り直し、Gitから展開したコードで数値6点と図2点のSHA-256が一致。検証27項目、既存テスト22件、過去14組191項目を確認した。[実行ログ](results/PARTICLE_RETURN_RUN.json)・[原本と再実行](access/2026-11-20-particle-return.md#再実行)・[SHA-256](results/PARTICLE_RETURN_SHA256SUMS)

**次の判定に必要な観測。** H44は内側で付けた標識の根端・外層通過と同じ内側への最初の帰還を対応させ、その間に生成された抱合型・酸化型・遊離型を測る。H45は同じ胚の体積時系列を使い、観測時間を一周に足る長さにする。初回分裂の前の粒子の三次元位置、圧力・粘性の仕事、流路を変えた後の娘細胞の位置を対応させる。構造が動いて流れを作る場合も同じ測定で採点する。[今回の限界](../docs/24_PARTICLE_RETURN_AND_AUXIN_REPORT.md#二つの仮説の現在地)

## 引き継いだ第14回

更新2026-11-20 UTC。第13回の `research/measured-return-and-polarity`（`02edd10`）を継承し、`research/turning-paths-and-axis` で解析した。H45のうち、分裂前に流れで既存の極性を動かすと娘細胞の大小が現れる側が変わることを実測で支持できる。同じ天然IAAの一周（H44）と、全機械エネルギーの三次元トーラス状の循環による身体形成（H45）は未判定。[第14回報告](../docs/23_TURNING_PATHS_AND_AXIS_REPORT.md)・[全56主張](claims.json)

## 第14回の結果と追試

| 実験 | 結果と再開点 |
|---|---|
| [E49](results/E49/summary.json) | 根端向きの標識パルスは10分供給＋50分洗出し後に8〜10 mmまで。別試料から順路・初到達時刻を合成しない。 |
| [E50](results/E50/summary.json) | 一次根で2方向を別々に弱められた。mdr1側根の伸長は外部IAAで約6.1〜6.3 mm/日へ回復。原基数と伸びを区別した。 |
| [E51](results/E51/summary.json) | 軸流の対向と両端の径流の反転が両側でそろう個体は2/6と3/7。中央部のみの対向より成立範囲が狭い。 |
| [E52](results/E52/summary.json) | 12個の一細胞胚で、極性を90度未満回した9個は通常に、超えた3個は逆向きに分裂。間の角度と仕事の測定が残る。 |
| [E53](results/E53/summary.json) | 第2減数分裂後期に複合体の位置から予測した後端は167/172個が的中。侵入側固定は161/172個。稀な逆側群では10/11個が的中した。 |
| [E54](results/E54/summary.json) | 娘細胞P1では正味の流れを打ち消す対照と一方向の照射で処置後のPAR-2軸の差は37.4度。全身の形成との対応は未測定。 |

E49〜E53の登録 `1ae8c73`、図3Bが一時点の空間分布であることとE51の採点範囲の補足 `f5ad77c`、娘細胞の対照の登録 `d607632`、コードと初回の結果 `e399376`。Gitから展開して11入力を取り直し、数値6点と図2点のSHA-256が一致した。今回の26項目、既存の22テスト、過去13組183項目を検証済み。[再取得と再実行](access/2026-11-20-turning-paths.md#再実行)・[実行ログ](results/TURNING_PATH_RUN.json)・[SHA-256](results/TURNING_PATH_SHA256SUMS)

**次の判定。** H44は根端・外層通過の記録をもつ遊離IAAの初回帰還率を、方向別の輸送欠損、補完、別経路、外部供給と同じ試料系で比較する。H45は最初の分裂の向きと大小を終点に、同じ胚の事前の三次元速度、圧力・粘性の仕事、経路を変えて投入仕事を照合した条件を対応させる。第14回で見つけた因果関係は既存極性の再配置で、卵殻や初期極性の成立は別の問いである。[識別点と既存の測定](../docs/23_TURNING_PATHS_AND_AXIS_REPORT.md#二つの未判定に残った識別点)

## 引き継いだ第13回

更新2026-11-20 UTC。第12回のブランチ `research/path-history-and-formation` の `2f5feca` を継承した。現在は `research/measured-return-and-polarity`。同一の天然IAAの一周（H44）と身体形成に先立つエネルギー循環（H45）は未判定。局所的な経路に関する新しい実測はH46〜H50に記録した。[第13回報告](../docs/22_MEASURED_RETURN_AND_POLARITY_REPORT.md)・[全50主張](claims.json)

## 第13回の結果と追試

| 実験 | 今回の判断 |
|---|---|
| [E44](results/E44/summary.json) | ソラマメ根片の中心部への介入で、5時間の根端向き標識量は対照の34%、地上部向きは117%。別試料で両方向の回収物を化学分離し、無傷根の時間別の組織局在も照合した。 |
| [E45](results/E45/summary.json) | シロイヌナズナ根端に標識IBAを与えると、分離した2成分中のIAAは根端から0.4〜2.4 mmで36.0%、2.4〜4.4 mmで89.3%。同種の胚軸では遊離の標識IAAが運ばれた量の質量分析がある。 |
| [E46](results/E46/summary.json) | 外側の測定から保留した内部の逆流を予測。基本条件で、線虫胚6/6とマウス卵母細胞6/7が両対照より小さい誤差。マウス1個では速度ゼロの予測が優った。 |
| [E47](results/E47/summary.json) | マウス卵母細胞の後の紡錘体位置は皮質への2系列の介入で変わった。早期流速から後の運動を予測する当初の時間窓は欠測。追加窓の介入群は8/29個で、そのうち再配置した表現型は1個。 |
| [E48](results/E48/summary.json) | 線虫胚の三次元撮影に由来する一横断面は全12角区間で中心後端向き、外側前端向き。エネルギー換算は仮定密度と表示された軸速度成分の範囲。 |

登録は `1773213`、E46の流量の釣合いとE47の欠測時の時間窓を予測採点前に追記した版は `3ef456f`、E48の数値抽出前の登録は `3810a71`。解析コードと保存結果は `037eb02`。Gitから展開したコードで公開原本7点を取り直し、空の出力先で数値5点・図2点がバイト単位で一致した。検証25項目、既存のテスト22件、過去12組176項目のハッシュも照合済み。[実行ログ](results/MEASURED_RETURN_RUN.json)・[SHA-256](results/MEASURED_RETURN_SHA256SUMS)・[依存、原本と一括再実行](access/2026-11-20-measured-return.md#取得と再実行)

**次の識別点。** H44ではソラマメとシロイヌナズナ、根と胚軸を明示し、同じ根の内側で標識したIAAのうち、根端・外層通過を記録し、元の領域で遊離状態として回収される割合を比べる。H45では形成する対象と時刻を先に固定し、同一胚の全三次元速度、圧力・応力からの仕事、循環を変えた後の位置や形がそろう資料を採点する。E46とE48は同一研究の2方向の観測で、E47は別研究・すでにある紡錘体の配置が対象。[次に判定できる測定](../docs/22_MEASURED_RETURN_AND_POLARITY_REPORT.md#二つの未判定を動かす測定)・[一次資料の対応表](notes/E44_E48_measured_return_evidence.md)

## 引き継いだ第12回

更新2026-11-20 UTC。E33〜E38を記録した `2e0659d` を継承した。今回、同じ分子の帰還、胚の局所的な形成、三次元の流れとエネルギーの経路を比較した。[第12回報告](../docs/21_PATH_HISTORY_AND_FORMATION_REPORT.md)・[全45主張の台帳](claims.json)

## 第12回の結果と追試

| 実験 | 主な結果 |
|---|---|
| [E39](results/E39/summary.json) | 根の公表化学測定から蛍光誘導体と遊離2,4-Dを別々に抽出。3時間で後者は両者の合計の約5.7%と5.4%。 |
| [E40](results/E40/summary.json) | 普通の標識では全時刻を通じて区別できない帰路を、外層を通った履歴で判別。通過場所の取り違え2%で、基本条件の初回帰還は投入量の6.88%と0.14%。 |
| [E41](results/E41/summary.json) | 細胞質流を弱めた卵母細胞で早期の後端の指標が確認され、後期には局在が広がった。部分補完群の極細胞は図で52.8%、孵化は全胚の0.8%。 |
| [E42](results/E42/summary.json) | 胚単位の公開データ。脊索切除で内腔中心の移動速度は−0.440 µm/分、頂端幅の前後差は−4.05 µm。内腔の形状比には幅のある区間が残った。 |
| [E43](results/E43/summary.json) | 三次元の定常流の局所エネルギーをそろえても材料の分布の向きが変わった。資源の帰路を切ると材料量は92.27%から24.14%になり、補充で閉路の結果を再現できた。 |

実験登録は `a55ca44` と `8105345`。原著図表の数値を抽出する前にE41の評価項目とE42の集計単位を `319fd68` で追記した。計算の版は `81350a3`。Gitから展開したコードで公開原本4件を再取得し、5つの数値結果と図2点がバイト単位で一致した。今回の検証21項目、既存テスト22件、過去の11組169項目のハッシュも確認した。[実行ログ](results/PATH_FORMATION_RUN.json)・[今回のSHA-256](results/PATH_FORMATION_SHA256SUMS)

原本の版、ワークブックのハッシュ、一括取得コマンドは取得記録にある。既設の環境がない場合は依存を入れて実行する。[取得と再実行](access/2026-11-20-path-and-formation.md#取得と再実行)

```bash
python3 -m pip install -r experiments/requirements.txt \
  -r experiments/E29_growth_holdout/requirements.txt \
  -r experiments/E23_nitrate_pin2/requirements.txt
run_dir=$(mktemp -d)
python3 -m experiments.run_path_formation --out "$run_dir/results" --log "$run_dir/run.json"
sed "s|research/results/|$run_dir/results/|" research/results/PATH_FORMATION_SHA256SUMS | sha256sum -c -
```

上の手順は `data/raw/path_and_formation/` に原本を置く場合。別の場所は `--raw` で指定する。H44の判定には、天然IAAの化学形と外層を通った履歴を同じ根で記録し、内部の別経路や局所の補充と比較する。H45の判定には、形成する器官を定め、出現前の三次元の流れと仕事の収支、循環経路を選択的に変えたあとの形を同じ計画で追う。[測定と対照](../docs/21_PATH_HISTORY_AND_FORMATION_REPORT.md#二つの仮説を次に判定する測定)

## 引き継いだ第11回

E30〜E32の `131260e` を継承した。E33〜E38で、他の生体試験と流体の測定に対象を広げた。[第11回報告](../docs/20_RETURN_AND_ENERGY_REPORT.md)

## 第11回の結果と追試

| 実験 | 主な結果 |
|---|---|
| [E33](results/E33/summary.json) | 表皮で誘導したあと中心柱で読んだDR5の蛍光は、NPAで誘導単独の2.4%、1-NOAで88.2%。内側から外側では1-NOAで29.7%。 |
| [E34](results/E34/summary.json) | 別の公開試験で野生型だけを参照し、4系統の周期を採点。対数RMSEは二待ち時間0.084、固定距離0.274、固定周期0.541。 |
| [E35](results/E35/summary.json) | 変異型の根の分岐数は野生型の穂木で中央値14→48。通常光の糖1→3%で主根長0.93→1.71 cm、出現側根密度の中央値は約0。 |
| [E36](results/E36/summary.json) | オリフィスの比は終盤5/5が0.33±0.05。時間変化する装置の終盤は約0.254。オリフィスの3図から算出し直すと0.383（中央値）。 |
| [E37](results/E37/summary.json) | 圧力・電気・化学ポテンシャルに共通する線形網の仕事率を照合。外部から供給のない受動閉路では、初期エネルギーを与えても定常の流束はゼロ。 |
| [E38](results/E38/summary.json) | 67株の公表データ。第I段階の記録法間の処置効果差は+0.875細胞、2反復内の個体単位での再標本化で95%区間+0.255〜+1.490。 |

E33〜E37の登録は `692e185`、E38の登録は `999c6d9`。E38は表の対応を診断した後、違いのある2株を除く感度分析を追記。計算の版は `44c9176`。新しい作業場所で原本11点を取得し、数値・図9点を再現。検証23項目、既存のテスト22件、過去のハッシュ160項目も照合済み。[実行ログ](results/RETURN_ENERGY_RUN.json)・[SHA-256](results/RETURN_ENERGY_SHA256SUMS)

既設のPython環境がない場合は次で依存をそろえる。追試に使う原本の版・URL・一括取得コマンドは取得記録にある。E34の固定待ち時間は既存のE29の予測ファイルから読む。[取得と再実行](access/2026-11-20-return-and-energy.md#原本を一括で取得する)

```bash
python3 -m pip install -r experiments/requirements.txt \
  -r experiments/E29_growth_holdout/requirements.txt \
  -r experiments/E23_nitrate_pin2/requirements.txt
run_dir=$(mktemp -d)
python3 -m experiments.run_return_energy --out "$run_dir/results" --log "$run_dir/run.json"
sed "s|research/results/|$run_dir/results/|" research/results/RETURN_ENERGY_SHA256SUMS | sha256sum -c -
```

上の実行は `data/raw/root_and_vortex/` に原本がある場合。別の保存先を使う場合は `--raw` で指定する。次に研究を進める際は、同じ根の成熟皮層細胞長・伸長速度と弱い信号を含む周期をそろえ、外側を経た同じ標識の内側への再到達を比較する。物理側では同時刻・同じ境界の速度計測から循環・力積・エネルギーをそろえ、駆動履歴を入力にして別条件の係数を予測する。[第11回報告](../docs/20_RETURN_AND_ENERGY_REPORT.md)

第10回では小胞輸送の介入と側根予定部位（H30）、オーキシン応答と初回分裂以降の進行（H31）を確認した。同じ周期の一部が弱まる場合と、周期が変動して長くなる場合で、同じ部位の配列が生じることを模型で示した（H32）。[第10回報告](../docs/19_ROOT_CLOCK_REPORT.md)

## 第10回の結果と追試

| 実験 | 主な結果 |
|---|---|
| [E30](results/E30/summary.json) | WachsmanらFig. 3Cの予定部位は主根1 cmあたり中央値5.92→約0→3.08（野生型、gnom184、抑制変異を加えた株）。図の中央値の差の読取り幅は最大±0.47。 |
| [E31](results/E31/summary.json) | 変異型IAA18の誘導により始原細胞マーカー陽性数が対照約19、低用量約32、高用量約765。別の試験の吸水12日後の原基・側根は野生型約29、変異株ほぼ0。 |
| [E32](results/E32/summary.json) | 同じ約1.83時間の周期で半数だけが予定部位として残ると、部位の間隔は平均3.66時間。変動する遅い対照と全時刻が一致する。候補時刻が既知で弱い振幅0.35の場合、感度80%以上かつ誤検出5%以下にはノイズの標準偏差が約0.141以下。 |

最初の登録 `6f571d7` と、図を開いた後の読取り単位・試験の補足を区別して記録した。実装と結果の版は `b16bef8`。Gitから展開したコードで約4.9秒で計算し、数値と図5点がバイト単位で一致。今回の検証9項目、既存テスト22件、過去のハッシュ155項目を確認した。[実行ログ](results/ROOT_CLOCK_RUN.json)・[SHA-256](results/ROOT_CLOCK_SHA256SUMS)

[取得記録](access/2026-11-20-root-clock.md)の3ファイルと、既刊図の高生産側を読む前に固定した[予測ファイル](results/E29/sealed_predictions.json)を使う。再取得ではコードが3原本のSHA-256を照合する。環境を変えた場合は数値の条件と誤差も確認する。

```bash
python3 -m pip install -r experiments/requirements.txt -r experiments/E29_growth_holdout/requirements.txt
mkdir -p data/raw/root_clock
curl --fail --location https://cdn.ncbi.nlm.nih.gov/pmc/blobs/84bd/7758939/40e6006dffcc/nihms-1649559-f0003.jpg \
  -o data/raw/root_clock/wachsman_f3.jpg
torus_pmc='https://pmc-oa-opendata.s3.amazonaws.com/PMC7775764.1'
curl --fail --location "$torus_pmc/PMC7775764.1.pdf" -o data/raw/root_clock/perianez_article.pdf
curl --fail --location "$torus_pmc/abd4722_SM.pdf" -o data/raw/root_clock/perianez_sm.pdf
run_dir=$(mktemp -d)
python3 -m experiments.run_root_clock --out "$run_dir/results" --log "$run_dir/run.json"
sed "s|research/results/|$run_dir/results/|" research/results/ROOT_CLOCK_SHA256SUMS | sha256sum -c -
```

次は同じ根の伸長と成熟皮層細胞長を測って生産率を照合し、弱いピークも含む信号の時系列と、予定部位・初回分裂・側根の対応を追う。戻り輸送の候補を調べるには、前向きの輸送と成長をそろえながら、外層を通った標識が中心へ戻る時刻を測る。独立した局所供給と、信号の振幅やその後の発生だけが変わる場合を対照にする。E30・E31からは同じ根の生産率と周期を組にして得られず、E29の係数の外部検証は未実施。[判別条件](../docs/19_ROOT_CLOCK_REPORT.md#戻り輸送と分岐を結ぶための観測)

第9回では原形質連絡を含む根端モデル（H27）、戻りと成長の待ち時間を合わせたモデル（H28）、高い細胞生産率への数値予測（H29）を検討した。局所の内皮と周鞘の作用と、根端の戻りは異なる空間の候補として記録する。[第9回報告](../docs/18_REFLUX_GROWTH_REPORT.md)

## 第9回の結果と追試

| 実験 | 主な結果 |
|---|---|
| [E27](results/E27/summary.json) | MellorらのFig. 2Jで原形質連絡を加えると、規格化蛍光の誤差は3系統で約62〜76%減少。2介入の蛍光変化はモデルと同方向。 |
| [E28](results/E28/summary.json) | 投入標識の20%が初めて戻るまで1.26規格化時間。成長率を0.5→1.5にすると頻度0.190→0.386、間隔2.63→3.89。成長依存の独立供給は同じ頻度と間隔を再現する。 |
| [E29](results/E29/summary.json) | 低生産側で調整した予測を `59c2856` で固定。高生産側の頻度50点・間隔48点の対数RMSEは、二待ち時間式0.336・0.375、固定周期0.380・0.474、固定間隔0.391・0.410。 |

登録は `95aaf1b`、図の低生産側から計算した事前予測は `59c2856`、採点・図の最終計算は `55c48d5`。Gitから展開したコードと空の出力先で約4.6秒で再計算し、数値と図6点、検証9項目、既存テスト22件を照合した。前回までのハッシュ149項目も確認した。E13とE23の訂正は `eb3dbaf`。E13の再計算は7条件、数値が以前と一致し、6つのNPZもバイト単位で一致。E21〜E23を再実行し、著者表記を変えたE23の図のみ更新した。[実行ログ](results/REFLUX_GROWTH_RUN.json)・[今回のSHA-256](results/REFLUX_GROWTH_SHA256SUMS)

追試には、[原本の取得記録](access/2026-11-20-reflux-growth.md)の3 JPEGと大学版PDFが要る。公開済みの予測は出力先とは別の場所から読み、再生成した予測と一致した場合にのみ高生産側を採点する。

```bash
python3 -m pip install -r experiments/requirements.txt -r experiments/E29_growth_holdout/requirements.txt
mkdir -p data/raw/reflux_growth
torus_cdn='https://cdn.ncbi.nlm.nih.gov/pmc/blobs/64f6/7132777'
curl --fail --location "$torus_cdn/82245338738c/develop-147-181669-g2.jpg" -o data/raw/reflux_growth/mellor_fig2.jpg
curl --fail --location "$torus_cdn/087276e63c38/develop-147-181669-g4.jpg" -o data/raw/reflux_growth/mellor_fig4.jpg
curl --fail --location "$torus_cdn/abf436973a0c/develop-147-181669-g5.jpg" -o data/raw/reflux_growth/mellor_fig5.jpg
curl --fail --location \
  'https://dspace.library.uu.nl/bitstream/handle/1874/413557/1_s2.0_S153458072100561X_main.pdf?sequence=1' \
  -o data/raw/reflux_growth/berg_uu_alt.pdf
run_dir=$(mktemp -d)
python3 -m experiments.run_reflux_growth --out "$run_dir/results" --log "$run_dir/run.json"
sed "s|research/results/|$run_dir/results/|" research/results/REFLUX_GROWTH_SHA256SUMS | sha256sum -c -
```

E29の [seal](results/E29/sealed_predictions.json) に低生産側の点・各式の係数と予測列、[採点](results/E29/summary.json) に高い側の点と誤差がある。原著の個体データ・コードの公開先は未取得。次の判定には、同じ根で細胞生産率を照合してから選択的に戻りの経路を変え、標識の再到達と準備シグナルの時刻、出現した側根を測る。局所補充で同じ応答が得られる場合の説明も事前に残す。[第9回報告](../docs/18_REFLUX_GROWTH_REPORT.md)

第8回では内皮のPIN3と初回分裂への進行（H24）、分裂開始と分裂方向の違い（H25）、培地の化学ポテンシャルと伸長（H26）を公表資料の再解析で条件内支持した。[第8回報告](../docs/17_LOCAL_REFLUX_REPORT.md)

## 第8回の結果と追試

| 実験 | 主な結果 |
|---|---|
| [E24](results/E24/summary.json) | 始原細胞から初回分裂まで103→206分（野生型→pin3）。内皮にPIN3を戻すと初回分裂に達した部位の密度3.86→7.15部位/cm。 |
| [E25](results/E25/summary.json) | 内皮の1細胞を除くと輸送阻害下でも分裂が起きた。NAA追加で通常株の垂直分裂が0.50→2.25回/除去イベント。原著本文と図で大きさに差がある。 |
| [E26](results/E26/summary.json) | 培地pH 6.15で伸長−34.6%、pH 5.10で+20.4%。酸性後の洗浄中は基線を下回った。別の電極測定で8本の対応した正味H⁺流入28.08→38.62 nmol/(m²·s)。 |

事前登録の版は `ae00a60`、E26の追加照合は `950ebe6`、最終計算は `a5546a8`。Debian 13 x86_64、Python 3.12.14、NumPy 2.3.5、SciPy 1.17.0、Matplotlib 3.10.8、OpenPyXL 3.1.5、Pillow 13.0.0。Gitから展開したコードで空の出力先に約2.2秒で再計算。検証11項目、成果物6点のハッシュ、元図から再抽出した読み値、既存テスト22件、前回までのハッシュ143項目が通った。[実行ログ](results/LOCAL_REFLUX_RUN.json)・[SHA-256](results/LOCAL_REFLUX_SHA256SUMS)

E24・E25は[固定した図の読み値](../experiments/local_reflux_readings.json)を使用する。E26の3ワークブックとFig. 1画像は、[原本のリンクとハッシュ](access/2026-11-20-local-reflux.md)の名前で取得する。次はリポジトリのルートからの追試。

```bash
python3 -m pip install -r experiments/requirements.txt -r experiments/E26_proton_growth/requirements.txt
mkdir -p data/raw/local_reflux
torus_source='https://static-content.springer.com/esm/art%3A10.1038%2Fs41586-021-04037-6/MediaObjects'
curl --fail --location "$torus_source/41586_2021_4037_MOESM8_ESM.xlsx" -o data/raw/local_reflux/li_f1.xlsx
curl --fail --location "$torus_source/41586_2021_4037_MOESM9_ESM.xlsx" -o data/raw/local_reflux/li_f2.xlsx
curl --fail --location "$torus_source/41586_2021_4037_MOESM13_ESM.xlsx" -o data/raw/local_reflux/li_ext2.xlsx
curl --fail --location \
  'https://media.springernature.com/full/springer-static/image/art%3A10.1038%2Fs41586-021-04037-6/MediaObjects/41586_2021_4037_Fig1_HTML.png' \
  -o data/raw/local_reflux/li_fig1.png
run_dir=$(mktemp -d)
python3 -m experiments.run_local_reflux --out "$run_dir/results" --log "$run_dir/run.json"
sed "s|research/results/|$run_dir/results/|" research/results/LOCAL_REFLUX_SHA256SUMS | sha256sum -c -
```

E24・E25の読み値を元図から再現するには、取得記録の4つのJPEGを保存して `python3 -m experiments.local_reflux_reading --out "$run_dir/readouts.json"`。E26の `traces.json` は同一時刻の平均、標本標準偏差、根の数。Fig. 1bの伸長は図とシートで約2倍の差があり、相対変化を使用。原本にない点は欠測として保持した。[研究で使った図](results/local_reflux_figures/)・[単位の照合](notes/E24_E26_root_tissue_evidence.md)

次は始原細胞の周鞘と隣の内皮で同じ標識を追い、内向きの輸送の変更が局所の再流入と初回分裂の所要時間をどれだけ変えるかを確かめる。内皮の変形と独立した局所補充を比較の対照にする。三次元のエネルギー循環に進むには同じ試料で膜の両側と、方向をもつ流束を測る必要がある。[判別条件](../docs/17_LOCAL_REFLUX_REPORT.md#戻り経路の仮説を前に進める観測)

第7回では、方向性のあるオーキシン輸送と側根形成の関与（H21）、外層から中心への再流入を介入で識別できる条件（H22）、硝酸後のPIN2による側根密度の応答差（H23）を指定した範囲で支持した。[第7回報告](../docs/16_AUXIN_TRANSPORT_REPORT.md)

## 第7回の結果と追試

| 実験 | 資料 | 主な結果 |
|---|---|---|
| E21 | [二方向の輸送と補充](results/E21/summary.json)・[文献・訂正](notes/E21_polar_auxin_and_branching.md) | 公式訂正のfmolを使用。別々に行った標識試験で両方向に移動。阻害し続けた条件でオーキシン補充により約0.48本/mmの側根が出現。 |
| E22 | [標識の時系列と収支](results/E22/)・[図](results/auxin_figures/tracer_reentry.png) | 同じ定常量を与えた3経路のうち、外層→中心を切って差が出たのは外層を経る閉路。基本条件で投入量の14.88%、弱い戻りでは1.18%。 |
| E23 | [公開シートの再集計](results/E23/summary.json)・[図](results/auxin_figures/nutrient_contrasts.png) | 硝酸への密度応答は野生型が欠損型より3回とも大きかった。野生型の主根も短くなり、照合できた個体の本数差は+1.0、+0.9、−0.7本/個体。 |

事前登録はE21 `a578400`、E22 `fd7306f`、E23 `30a248d`。計算・図の版は `8fdd684`。Debian 13 x86_64、Python 3.12.14、NumPy 2.3.5、SciPy 1.17.0、Matplotlib 3.10.8、OpenPyXL 3.1.5、Pillow 13.0.0。乱数なし。Gitから展開したコードと空の出力先で再実行し、4.1秒で14項目の校正・原本照合を通過。出力7点と元画像から読み直した数値が一致した。既存単体テスト22件と従来の6つのハッシュ一覧も確認済み。[実行ログ](results/AUXIN_RUN.json)・[SHA-256](results/AUXIN_SHA256SUMS)

追試はリポジトリのルートで実行する。E21は表・図の固定入力を使い、E22は登録した率でモデルを解く。E23にはPMCの公開ワークブック2つが必要。同じ版の原本がある場合は `--raw` で指定できる。[取得リンクと原本のハッシュ](access/2026-11-20-auxin.md)

```bash
python3 -m pip install -r experiments/requirements.txt -r experiments/E23_nitrate_pin2/requirements.txt Pillow==13.0.0
mkdir -p data/raw/auxin
for file in EMBR-22-e51813-s007.xlsx EMBR-22-e51813-s002.xlsx; do
  curl --fail --location --retry 2 "https://pmc-oa-opendata.s3.amazonaws.com/PMC8447600.1/$file" \
    -o "data/raw/auxin/$file" || exit 1
done
run_dir=$(mktemp -d)
python3 -m experiments.run_auxin_transport --raw data/raw/auxin \
  --out "$run_dir/results" --log "$run_dir/run.json"
sed "s|research/results/|$run_dir/results/|" research/results/AUXIN_SHA256SUMS | sha256sum -c -
```

元図からE21の平均を抽出する場合は[取得記録](access/2026-11-20-auxin.md)のJPEGを `data/raw/auxin/casimiro_fig3.jpg` に保存する。`python3 -m experiments.E21_auxin_evidence.read_figure data/raw/auxin/casimiro_fig3.jpg --out "$run_dir/casimiro.json"` の出力を[固定入力](../experiments/E21_auxin_evidence/figure_values.json)と比較する。

E22の `responses.npz` は各経路の時刻、中心・根先・外層の量、損失、二つの戻り方ごとの積算量を含む。E23は各図の群、反復、処置の要約と、長さと密度を同じ行から照合した結果を保存した。次は生体で外層を通った標識の再流入だけを測り、主根の伸びと分岐候補の初期状態を記録した上で、後の側根の位置と数を予測する。[判別条件](../docs/16_AUXIN_TRANSPORT_REPORT.md#次に何を測れば支持が進むか)

## 第6回の結果と追試

第6回では、同じ初期供給と流速で閉路が取り込みを増やす条件（H19）を計算で支持した。側根の位置は曲げの影響を受け、1曲がり1本の予測は図の未使用条件に合わなかった（H20）。[第6回報告](../docs/15_RETURN_PATH_REPORT.md)

| 実験 | 資料 | 主な結果 |
|---|---|---|
| E19 | [512セルの比較](results/E19/grid512/summary.json)・[図](results/return_path_figures/uptake.png) | 外部供給1で閉路89.13%、開路59.34%。戻り途中で失われる条件で差0.16ポイント。開路に予測した戻り量を補充した対照で時系列が一致。 |
| E20 | [図と表の再集計](results/E20/summary.json)・[取得範囲](notes/E20_lateral_root_controls.md) | 側根の出現位置が曲げで偏った。6時間で調整した一定式の未使用7条件のRMSE0.86本/日、1曲がり1本は3.74本/日。本数差の目安+0.5本は元の表では除外できない。 |

主登録 `501f4d9`、図の追加登録 `8837d48`、最終計算と図 `816f382`。Python 3.12.14、NumPy 2.3.5、SciPy 1.17.0、Matplotlib 3.10.8、元図読取りPillow 13.0.0。乱数種なし。Gitから展開した別環境で全入口を再実行し、4.2秒で15項目の校正・収支チェックを通過。数値と図9点がバイト単位で一致し、前回までのハッシュと既存単体テスト22件も通過した。[実行ログ](results/RETURN_PATH_RUN.json)・[SHA-256](results/RETURN_PATH_SHA256SUMS)

追試はリポジトリのルートで実行する。E20の計算は公開図から得た固定入力を使う。[図の読取り](../experiments/E20_bending_controls/figure_values.json)・[原表の数値](../experiments/E20_bending_controls/published_table.json)

```bash
python3 -m pip install -r experiments/requirements.txt Pillow==13.0.0
run_dir=$(mktemp -d)
python3 -m experiments.run_return_paths --out "$run_dir/results" --log "$run_dir/run.json"
sed "s|research/results/|$run_dir/results/|" research/results/RETURN_PATH_SHA256SUMS | sha256sum -c -
```

図を再抽出する場合は[アクセス記録](access/2026-11-20-return-paths.md)のJPEGを取得し、
`python3 -m experiments.E20_bending_controls.read_figure data/raw/return_paths/kircher_fig4.jpg --out /tmp/torus-return-reading.json`。
E19の `histories.npz` はケース名をキーに、時刻・各地点の累積取り込み・流路にある量・損失・排出・外部供給・累積で戻った量・収支残差を持つ。積算の戻り量は同じ資源の再利用を含み、外部供給に加算しない。

次の判別は、流量を保って戻り資源だけを変えたとき、二巡目の到達と受け取り部の反応が予測と合うか。植物では分岐候補のマーカーを先に測り、曲げによる位置の選択と新しい発生部位の追加を数える。[第6回報告](../docs/15_RETURN_PATH_REPORT.md)

## 第5回の結果と追試

第5回では、H17の先行する物理的な作用と器官位置を公表実験で、H18のトーラス状流れと資源を介した成長位置を材料モデルで支持した。[第5回報告](../docs/14_FLOW_BEFORE_FORM_REPORT.md)

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
