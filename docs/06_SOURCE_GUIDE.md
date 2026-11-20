# 資料の読み方と研究へのつなぎ方

第2回に読んだ原論文・補足データと、分野別の抽出文献の確認段階を公開した。[文献カード](../research/notes/)・[DOI別の判定と出典](../research/results/E08/summary.json)

更新日：2026-11-20

## 1. この資料集の役割

「ひとつの仕組みが、見る向きや尺度によってトーラス、波、渦、樹木の分岐として現れるのではないか」という着想を、検討できる問いへ進めるための資料集です。トーラスの実例、似た図が別の仕組みから生じる例、測定・判定方法を一緒に用意しています。

一覧の正本は [sources/catalog.json](../sources/catalog.json) です。24件の一次論文・研究機関の公式解説・公式API仕様を収録しています。各項目の `supports` はその資料で支えられる範囲、`does_not_support` はその資料だけでは進めない推論を記しています。後者は、必ずしも対象の仮説が偽だという意味ではありません。

これは研究を開始するための選定資料であり、系統的レビューを完了したものではありません。収録年の古い研究もあります。最終的な結論を出す前に、被引用論文、追試、訂正、より新しい観測を追加してください。

会話で共有された動画と画像は、**発想と調べる主張を特定する資料**として扱います。科学的根拠として使うときは、映像内の各現象から元の観測・実験・数式へたどります。見た目の重なりが魅力的であることと、同じ生成機構が確認されたことは、それぞれ記録します。

## 2. 最初に読む順序

まず [仮説と用語](02_HYPOTHESES_AND_TERMS.md) で、調べる「トーラス」が何を指すかを選びます。その後、次の順に読むと、資料の役割を混同しにくくなります。

| 順序 | 資料 | この段階で確かめること |
|---|---|---|
| 1 | S001・S002・S003 | 円の投影、幾何学的な曲面、二つの周期を持つ状態空間がどう違うか。 |
| 2 | S005・S006・S007 | 実際の磁場・流体で、どの条件にトーラスや渦輪が現れるか。他の渦の形はあるか。 |
| 3 | S008・S023 | 外形が輪でなくても、測定した集団活動の状態空間にトーラスが現れる例と、その調べ方。 |
| 4 | S009・S011・S012、必要に応じS010 | 木の上下方向の成長や分岐を、輸送、応答、発生機構から調べる。 |
| 5 | S013・S014・S024 | 台風の断面、光円錐、天体の8字のように、似た図に異なる意味がある場合を確認する。 |
| 6 | S015・S016・S017 | 宇宙の空間トポロジーを、局所の渦や宇宙の「中心」と区別して調べる。 |
| 7 | S004・S018 | 非周期運動や反応拡散を比較モデルにし、トーラス仮説が新しく予測する量を探す。 |
| 随時 | S019〜S022 | 本文・書誌情報への正規アクセス方法と、利用できる範囲を確認する。 |

数学の解説で可能性を理解した後は、実例の測定へ戻ります。実例が見つかった後は、その成立条件と、成立しなかった条件を一緒に探します。

## 3. 資料ごとの用途

下表のIDはカタログと対応します。詳細な書誌情報、確認状態、取得できなかった理由、ライセンスのメモはカタログにあります。

| ID | 資料への入口 | 研究での使い方 |
|---|---|---|
| S001 | [Strang / MIT：Motion Along a Curve](https://ocw.mit.edu/ans7870/textbooks/Strang/Edited/Calculus/12.1-12.2.pdf) | 円運動の座標と螺旋を確認する。正弦波から元の立体を一意に逆算できるか、別のモデルと比較する。 |
| S002 | [MIT：トーラスのパラメータ表示](https://math.mit.edu/~larsh/teaching/F2007/handouts/lectures_31-38.pdf) | 曲面の定義を固定する。検索索引では式を確認したが、本文の直接取得は未達。 |
| S003 | [MIT：Introduction to Strange Attractors](https://ocw.mit.edu/courses/12-006j-nonlinear-dynamics-chaos-fall-2022/mit12_006jf22_lec19.pdf) | 二つの角度で状態を表すモデル、周期と準周期の違いを調べる。 |
| S004 | [Lorenz：Deterministic Nonperiodic Flow](https://journals.ametsoc.org/view/journals/atsc/20/2/1520-0469_1963_020_0130_dnf_2_0_co_2.xml) | 秩序ある決定論的方程式でも非周期の運動が生じる比較例。二葉の外観だけでトーラス判定しない。 |
| S005 | [DOE：Tokamaks](https://www.energy.gov/science/doe-explainstokamaks) | トロイダル・ポロイダル磁場の実用例。装置による境界条件も説明変数に含める。 |
| S006 | [Borisovほか：渦輪の追越し運動](https://doi.org/10.1088/0169-5983/46/3/031415) | 複数の輪の相互作用を調べる入口。数値解析と実験の証拠を分ける。 |
| S007 | [Kleckner & Irvine：Knotted vortices](https://www.nature.com/articles/nphys2560) | 結び目やリンクを持つ実験渦を比較する。渦芯とその周囲の管と流れ全体を区別する。 |
| S008 | [Gardnerほか：格子細胞のトーラス](https://www.nature.com/articles/s41586-021-04268-7) | 神経集団活動のトーラス構造。現実のデータで「形を越えた共通構造」を調べる重要な入口。 |
| S009 | [Virginia Tech / Richmond：Botany](https://www.pubs.ext.vt.edu/ANR/ANR-10/ANR-10.html) | 木部・師部、供給源と受容先、蒸散を確認する。個体の内外を含む物質収支を考える。 |
| S010 | [Liほか：根のオーキシン応答](https://pmc.ncbi.nlm.nih.gov/articles/PMC7612300/) | 拮抗する細胞応答を具体的な経路と測定量で扱う。 |
| S011 | [Hajnýほか：Auxin canalization](https://pmc.ncbi.nlm.nih.gov/articles/PMC7116426/) | 流れと発生パターンの関係を、分子機構の実験から検討する。 |
| S012 | [Brummerほか：動植物の分岐原理](https://pmc.ncbi.nlm.nih.gov/articles/PMC7879751/) | 分野間の共通性と違いを、枝の寸法やモデルで比較する。 |
| S013 | [NOAA：Tropical Cyclone Structure](https://www.noaa.gov/jetstream/tropical/tropical-cyclone-introduction/tropical-cyclone-structure) | 目、眼壁、上昇、流入・流出を対応づける。断面図だけで全流線が閉じると仮定しない。 |
| S014 | [Einstein Online：Spacetime](https://www.einstein-online.info/en/spacetime/) | 砂時計状の光円錐の軸と意味を確認する。時間軸を空間の上下軸に読み替えない。 |
| S015 | [Planck：宇宙の幾何とトポロジー](https://arxiv.org/abs/1502.01593) | 三次元トーラスなどの宇宙モデルを、CMBの観測に照らす研究を読む。 |
| S016 | [COMPACT：Circle searchesの制約](https://arxiv.org/abs/2211.02603) | 観測者の位置や空間の種類によって制約がどう変わるかを調べる。訂正版の版を固定する。 |
| S017 | [NASA / John Mather：Big Bang Q&A](https://science.nasa.gov/mission/webb/big-bang-q-and-a/) | 宇宙膨張を、空間内の一点からの爆発と混同しないための基礎解説。 |
| S018 | [Pearson：Complex Patterns in a Simple System](https://arxiv.org/abs/patt-sol/9304003) | 反応拡散から複雑な模様が生じる比較モデル。形と生成原因を切り分ける。 |
| S019 | [PMC：For Developers](https://pmc.ncbi.nlm.nih.gov/tools/developers/) | 全文を自動取得できる公式経路を選ぶ。 |
| S020 | [NCBI：BioC API](https://www.ncbi.nlm.nih.gov/research/bionlp/APIs/BioC-PMC/) | 対象コレクションの本文をXML/JSONで取得する仕様。 |
| S021 | [arXiv API User's Manual](https://info.arxiv.org/help/api/user-manual.html) | 論文の検索、ID、版、メタデータを取得する仕様。 |
| S022 | [Crossref REST API](https://www.crossref.org/documentation/retrieve-metadata/rest-api/) | DOIから書誌・更新情報を照合する。全文取得とは区別する。 |
| S023 | [Bauer：Ripser](https://arxiv.org/abs/1908.02518) | 点群の持続的ホモロジーを計算する手法。分析条件の依存性を確認する。 |
| S024 | [NASA：Two Worlds, Two Analemmas](https://science.nasa.gov/image-article/apod-2025-june-21-two-worlds-two-analemmas/) | 同じ時刻に記録した太陽位置の模様を、地軸の傾き・軌道離心率と結びつける。地球と火星も比較する。 |

## 4. 実データと解析コードへの導線

### 格子細胞のトーラス：S008

この論文は、物体の外形ではなく、神経集団の活動を記述した空間にトーラス構造を見いだした研究です。「同じ構造が違う姿で現れる」という問いを、測定と解析で具体化する候補になります。ただし、この結果が扱う集団と実験条件の範囲を保って読みます。[論文](https://www.nature.com/articles/s41586-021-04268-7)

論文の Data availability と Code availability は、次の同じ公開先を指定しています。

- [著者が指定するFigshare：Toroidal topology of population activity in grid cells](https://figshare.com/articles/dataset/Toroidal_topology_of_population_activity_in_grid_cells/16764508)
- [PMC掲載版](https://pmc.ncbi.nlm.nih.gov/articles/PMC8810387/)
- [Figshareの当該レコードAPI](https://api.figshare.com/v2/articles/16764508)

今回確認できたのは、論文の検索索引に記載された共有先までです。Natureの直接取得はcookie redirect、PMCはCAPTCHA、Figshareのページは403となり、Figshare APIも取得できませんでした。**データとコードを入手・実行した状態ではありません。** 到達できる環境で正規のURLを開き、ファイル一覧、サイズ、版、ライセンスを先に確認します。

最初の再現では、対象セッションと図を一つ選び、論文の前処理と解析を合わせます。次に、シャッフルデータ、サンプリング数、ノイズ、距離の定義を変えた対照を追加します。この手順は本研究の提案であり、今回すでに再現できた結果ではありません。

### 分岐ネットワーク：S012

[論文](https://pmc.ncbi.nlm.nih.gov/articles/PMC7879751/) の補助資料は [Figshareコレクション DOI 10.6084/m9.figshare.c.5238488](https://doi.org/10.6084/m9.figshare.c.5238488) へ案内されています。動物と植物を同じ測定指標で比較する入口です。

本文にある補助資料への導線を確認しました。個別データファイルは未ダウンロードです。論文本体のCC BY 4.0と、補助資料それぞれの利用条件は分けて確認します。

### 点群解析：S023

[Ripser公式ページ](https://ripser.org/) と [公式リポジトリ](https://github.com/Ripser/ripser) から実装へ進めます。今回の準備ではダウンロード・インストール・実行をしていません。使用時はコードの版とライセンスを記録します。

トーラスを期待して解析する場合も、球面、円、ランダム点群など同じ規模・同じノイズの比較対象を用意します。持続的ホモロジーが示す穴の情報と、対象を作った物理法則は別の主張として評価します。この対照設計は [研究プロトコル](04_RESEARCH_PROTOCOL.md) と合わせて実装します。

## 5. 「似ている」の次に確認すること

### 正弦波、トーラス、準周期

[S001](https://ocw.mit.edu/ans7870/textbooks/Strang/Edited/Calculus/12.1-12.2.pdf) は円運動と座標の関係、[S003](https://ocw.mit.edu/courses/12-006j-nonlinear-dynamics-chaos-fall-2022/mit12_006jf22_lec19.pdf) は二つの周期を持つ状態空間を調べる資料です。前者だけでは三次元の物体を特定できません。後者では、二つの角度を独立に変えられるモデルなのか、測定中の一本の軌道なのかを明記します。

有限時間の数値計算だけで周波数比が厳密に無理数であると証明しないようにします。補助教材 [MIT / Rosales 2024 P-set 07 §3](https://math.mit.edu/classes/18.353J/PSetAnswers/AnswerPSet_2024_07.pdf) は、Lissajous図と有限精度の関係を考える手がかりになります。

### 木の根と枝、輸送の往復

[S009](https://www.pubs.ext.vt.edu/ANR/ANR-10/ANR-10.html) の木部・師部の説明を起点に、何の物質が、どこからどこへ、どの条件で動くかを記録します。上下に通路があることだけでは、同じ物質が閉じたトーラス状経路を通るとは確定しません。

[S011](https://pmc.ncbi.nlm.nih.gov/articles/PMC7116426/) と [S012](https://pmc.ncbi.nlm.nih.gov/articles/PMC7879751/) に対し、提案するトーラスモデルが、枝の角度、直径比、成長応答などのどの観測量を追加で予測するかを問いかけます。既存機構と共存する上位の記述を提案する場合も、その対応関係を式または測定可能な規則にします。

### 砂時計、光円錐、宇宙

[S014](https://www.einstein-online.info/en/spacetime/) の光円錐は、出来事の因果関係を表す時空の図です。画像に砂時計の形があっても、それだけで三次元空間の流れを描いているとは判断できません。

[S015](https://arxiv.org/abs/1502.01593) と [S016](https://arxiv.org/abs/2211.02603) の空間トポロジーは、局所的な流体の渦とは異なる検証対象です。非検出は、論文で試したモデル・サイズ・観測条件の範囲で読みます。制約が残ることを存在の証明にせず、非検出を全可能性の排除にもしません。

### 動画に現れる8字や幾何模様

[S024](https://science.nasa.gov/image-article/apod-2025-june-21-two-worlds-two-analemmas/) は、地球の太陽アナレンマと火星での異なる形を説明しています。画像ごとに観測地点、撮影時刻、期間、座標系を確認すると、「どの見方なら何が現れるか」という問いを具体化できます。

この解説で、動画に出る月の軌跡や惑星の幾何模様まで確認済みにはしません。キルリアン写真やフェロセル画像も、元の装置条件と一次測定を追えていない限り、トーラスの物理的実在を実証した資料として数えません。原典が見つかるまでは未確認の検討項目として残します。

## 6. アクセス状態をどう読むか

| カタログの値 | 確認したこと | まだ意味しないこと |
|---|---|---|
| `web_verified` | 一次・公式ページやPDFの本文または対象箇所をWebで確認した。 | 全文読了、Codexのシェルからの到達、PDF保存、API成功、追試完了。 |
| `metadata_verified` | 書誌、要旨、検索索引の対象記述を確認した。 | 直接本文が読めたこと、図・方法・全結論の精査。 |
| `not_checked` | まだ確認していない。 | 不存在、誤り、仮説の否定。 |

API仕様を読めたことと、個々の論文をそのAPIで取得できたことも区別します。カタログの `automated_access_url` は公式仕様に沿った取得先で、成功の記録ではありません。実行ごとの結果は [アクセス方法](07_ACCESS_GUIDE.md) のCLIで別に残せます。

今回の資料整備では、論文全文・図・動画・研究データをリポジトリに複製していません。公式PDFをWebで閲覧したという表示は、PDFファイルの保存まで意味しません。別途、S001のMIT公式PDFだけはCLIの動作確認で一時取得し、サイズとSHA-256を記録しました。S012のBioC取得はHTTP 429で停止しています。詳細は[準備の検証記録](../research/PREPARATION_VALIDATION.json)を参照してください。公開閲覧、API取得、再配布の可否は、それぞれ確認します。

### 2026年のPMC変更

[PMCの開発者向け案内](https://pmc.ncbi.nlm.nih.gov/tools/developers/) が指定する自動取得経路を使います。[旧OA Web Serviceは2026-08-25に廃止](https://pmc.ncbi.nlm.nih.gov/tools/oa-service/) と案内されているため、旧 `oa.fcgi` を新しいアクセス手段に採用していません。

[BioC公式仕様](https://www.ncbi.nlm.nih.gov/research/bionlp/APIs/BioC-PMC/) にある書式は次のとおりです。

```text
https://www.ncbi.nlm.nih.gov/research/bionlp/RESTful/pmcoa.cgi/BioC_[format]/[ID]/[encoding]
```

対象コレクション、ID、形式と文字コードを確認して取得します。公開されている全PMC論文を無条件に取得できる仕組みではありません。本文が得られない場合も、DOI・PMCIDと閲覧用URLを保って次の環境へ引き継ぎます。

## 7. 読んだ資料を証拠へ変える記録

論文を一つ読んだら、次の項目を短く残します。「トーラスに言及している論文の件数」を、そのまま普遍性の証拠の強さにしないためです。

| 項目 | 記録する内容 |
|---|---|
| 仮説 | どの主張・どの範囲を評価するか。 |
| 資料 | S番号、DOI、版、参照した節・図・表、確認日。 |
| 証拠の種類 | 観測、操作実験、数値実験、数学的導出、教育的説明のどれか。 |
| 対象 | 物体の表面、渦芯、場、状態空間、空間全体など、何のトポロジーか。 |
| 条件 | 境界、駆動、散逸、スケール、測定・前処理条件。 |
| 結果 | 実際に測定・導出された量と不確かさ。 |
| 限界 | この資料では決められないこと、代替モデル。 |
| 反対方向の確認 | 同じ条件でトーラスにならない例と、比較の公平さ。 |
| アクセス | 本文・データ・コードを本当に取得したか。未取得なら理由。 |
| 次の予測 | まだ見ていない対象に対し、モデルから何を予測できるか。 |

普遍性を評価するときは、選んだ例だけでなく、どの母集団から何件を調べたかも残します。トーラスが成立する条件を明確にすること、別の構造との関係を定義すること、ある範囲で共通の方程式を示すことのいずれも、有意義な研究結果になり得ます。

