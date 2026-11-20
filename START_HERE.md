# TORUS-mania — 研究開始案内

## 目的

「トーラスが至るところに存在する共通原理と言えるか」を調べる。発案者は、木・渦・波などが単に似ているという指摘をしているのではない。**ひとつの動的な仕組みの異なる現れであり、その単体がトーラス的な循環、世界がそれら同士の関係なのではないか**、という仮説を研究したい。

最初の仕事は、この強い問いを維持しつつ、判定可能な小さい問いへ分けること。

## 読む順序

1. [AGENTS.md](AGENTS.md)
2. [会話の整理](docs/01_CONVERSATION_SUMMARY.md)
3. [仮説と用語](docs/02_HYPOTHESES_AND_TERMS.md)
4. [根拠台帳](docs/03_EVIDENCE_LEDGER.md)
5. [研究手順](docs/04_RESEARCH_PROTOCOL.md)・[実験計画](docs/05_EXPERIMENT_PLAN.md)
6. [資料案内](docs/06_SOURCE_GUIDE.md)・[アクセスガイド](docs/07_ACCESS_GUIDE.md)
7. [動画メモ](docs/08_VIDEO_NOTES.md)
8. [Codexへの依頼文](docs/09_CODEX_BRIEF.md)

## 現在の再開地点

E01〜E15は登録した条件で実行済み。共通の流束発展則、輪を追う領域のエネルギー収支、八つの渦輪を衝突させた公開PIVの再集計まで進んだ。これまでに閉経路のエネルギー原理、渦・分岐・波の比較も報告した。[第4回報告](docs/13_DYNAMIC_CIRCULATION_REPORT.md)・[第3回報告](docs/12_ENERGY_RESEARCH_REPORT.md)・[渦・分岐を扱った第2回](docs/11_SECOND_RESEARCH_REPORT.md)・[再実行と現在の判断](research/STATUS.md)

## 準備時点での最初の作業

まずローカルで、追加インストールなしに資料索引を読む。

```bash
python3 scripts/research_access.py --help
python3 scripts/research_access.py list
python3 -m unittest discover -s tests -v
```

ネットワークの有無、外部ブラウズ、文献取得、動画確認の能力は別々に確認する。利用できない機能があっても、既存の資料カードと実験設計を読む作業は進められる。詳細コマンドはアクセスガイドを優先する。

次に、文献で主張の範囲を確認し、E01（投影）とE02（状態空間）から最小実験を開始する。E01・E02は解析的な正解があるため、描画・測定・再現手順の校正に使う。ここが通っても宇宙仮説を支持したと判定しない。

## 研究開始時の準備と計画

| 準備時に用意した内容 | 準備時に計画した作業 |
|---|---|
| 会話の意図、仮説台帳、用語の区別 | 新たな数理的導出・仮説の修正 |
| 出典付きの資料索引、公開アクセス案内 | 論文本文の精読、データ取得・ライセンス確認 |
| 2本の動画のメタデータと限定的解析メモ | 重要フレーム・字幕の直接照合、図の原典追跡 |
| 実験の目的・対照・測定項目・停止条件 | 本研究のシミュレーション実装・実行 |
| 取得補助スクリプトとオフライン検証 | 実行環境からの各取得先への到達確認 |

## 続けるときの保存先

- 文献カード：`research/notes/`
- 実験コード：`experiments/E01_.../` のように実験IDごと
- 実験結果：`research/results/`（条件、乱数種、コード版、数値、図、限界を一緒に）
- 生資料：`data/raw/`（既定でGitに含めない）
- アクセス記録：`research/access/`
- 再開メモ：`research/STATUS.md`（初回は `research/templates/research-status.md` から作成）

物理の結論が出ないことは、作業失敗ではない。何を支持し、何が未決定で、どの観測なら区別できるかが残れば研究は進んでいる。
