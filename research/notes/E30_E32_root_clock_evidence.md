# E30〜E32　側根の準備と発生を調べた一次資料

確認日2026-11-20 UTC。準備帯に現れる発光ピーク、主根に残る予定部位、始原細胞のマーカー、初回分裂以降の原基と出現側根を区別して確認した。E29の生産率は根の伸長速度を成熟皮層細胞の長さで割った値。各試験の根長あたりの部位数から、この生産率やシグナルの周期を逆算できない。[E29の実測照合](../../docs/18_REFLUX_GROWTH_REPORT.md)

| 一次資料と閲読段階 | 原著で観察・計算したこと | 本研究での扱い |
|---|---|---|
| Guy Wachsmanら（2020）“Cell wall remodeling and vesicle trafficking mediate the root clock in Arabidopsis”、公開全文、Fig. 2・3。 [DOI](https://doi.org/10.1126/science.abb7250)・[PMC](https://pmc.ncbi.nlm.nih.gov/articles/PMC7758939/) | 小胞輸送関連のgnom184の表現型、抑制変異の効果、BFAへの応答、ペクチン分布や修飾の変化を調べた。BFAには複数のARF-GEF標的がある。 | Fig. 3CのCLE44発光で標識した予定部位の箱の線を再抽出。縦軸に従い主根1 cmあたりを使用。中央値約5.92→0→3.08（野生型、gnom184、抑制変異を重ねた株）。組織内のどの方向の移動が変わったかは図から決まらない。 |
| Juan Perianez-Rodriguezら（2021）“An auxin-regulable oscillatory circuit drives the root clock in Arabidopsis”、公開本文と補遺、Fig. 1・S2・S3。 [DOI](https://doi.org/10.1126/sciadv.abd4722)・[PMC](https://pmc.ncbi.nlm.nih.gov/articles/PMC7775764/) | iaa18/potent変異株では準備帯のDR5発光が持続し、予定部位が不規則になる。変異型の誘導で始原細胞マーカー陽性細胞が増える。通常培地の変異株では初回分裂後の原基・側根が少なく、別条件のオーキシン添加による形成も原著は報告する。ARF7/IAA18を含む回路をモデル化した。 | Fig. 1Eを軸の切れ目の上下で別に較正。補足Fig. S2Cでは群ごとの発生日数別の平均を読んだ。別の群の細胞数と器官数を割った進行率は求めない。分子回路の関与と、細胞ごとの自己持続振動の確証は区別する。 |
| Wei Xuanら（2015）“Root Cap-Derived Auxin Pre-patterns the Longitudinal Axis of the Arabidopsis Root”、PubMed抄録。 [DOI](https://doi.org/10.1016/j.cub.2015.03.046)・[PubMed](https://pubmed.ncbi.nlm.nih.gov/25959963/) | 抄録では、根冠に由来するオーキシンが根の周期的な準備シグナルの振幅を変え、予定部位の成立に関わると報告。 | 振幅が変わる候補がある根拠として使う。原著の個体データや振幅の数値は取得していない。E32の残存確率・該当する弱い振幅・ノイズは仮定。 |
| Kirsten H. ten Tusscher（2026）“The (un)likelihood of clock-driven lateral root priming; a modeling exploration”、公開本文。 [DOI](https://doi.org/10.1093/plcell/koag213)・[PMC](https://pmc.ncbi.nlm.nih.gov/articles/PMC13421895/) | 単一細胞および一次元の成長中の細胞列を計算。伸長領域で振動が起きても、進入する細胞に位相差と位相の記憶を作る仕組みがなければ周期的な空間配置に結び付きにくい。 | 成長と輸送から組織全体で信号が出る説明と、細胞が自律的に振動する説明を比較する際の制約。今回の介入に加えて確認した計算。 |

E30・E31には、同一個体での伸長速度、成熟皮層細胞長、弱いものを含む準備シグナルの時系列を照合できる表がない。E29の係数の外部検証、候補となる戻り経路の選択的な介入、同じ分子の外層から中心への再到達は未実施。次に比較する量は、同じ根で測る準備信号の時刻と振幅、予定部位の保持、初回分裂時刻、側根の出現、標識再到達量である。[取得範囲と原本](../access/2026-11-20-root-clock.md)・[第10回報告](../../docs/19_ROOT_CLOCK_REPORT.md)
