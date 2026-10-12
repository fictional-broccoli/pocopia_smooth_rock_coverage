
# さらさら岩配置最適化ツール

『ぽこ あ ポケモン』のさらさら岩の配置を最適化するローカルツールです。
Python CLI版と、`web/` にあるHTML/JavaScriptブラウザー版を提供します。

本ツールは個人用の計算ツールとして作成したもので、計算結果の正確性やゲーム内での有効性を保証するものではありません。
開発にはCodexを使用しました。
配置の叩き台にして調整して下さい。急ぐ人はメタル掘ってみっちり敷き詰めて。
Agentについてはバックアップのため同梱

## 目的

入力した1次元パターンを指定した行数に展開し、指定した岩の使用上限以内で
すべての乾燥対象をカバーできる配置を探索します。

外部サービスや外部ライブラリは使用しません。Python版はソースコードから実行し、
ブラウザー版は `web/index.html` を開いて利用します。

## 動作環境

- Python 3.10以上
- Python標準ライブラリのみ使用

## 入力形式

`s` は乾燥不要のマス、`d` は乾燥対象のマスです。
さらさら岩は `d` のマスの下に設置するモデルとし、`d` を配置候補にします。

例：

```text
[s][d][s][d][s][d][s]
```

入力したパターンを同じ内容で指定した行数に展開します。
行数を空欄にした場合は既定の10行になります。岩の使用上限は実行時に入力します。

## 実行方法

```bash
python main.py
```

入力例：

```text
配置パターン / Pattern (e.g. [s][d][s][d][s]): [s][d][s][d][s]
繰り返し行数 / Repeated rows (default: 10): 10
さらさら岩の上限 / Smooth Rock limit: 3
```

### ブラウザー版

`web/index.html` をブラウザーで開きます。サーバーの起動や依存パッケージの導入は不要です。
パターン、行数、岩の上限を入力し、配置図・岩の座標・重複回数を確認できます。
「効率を優先する」をオンにすると、全件カバーできる配置の中から
「被覆数合計 ÷ 岩の使用数」を最大化します。同率なら被覆数合計が多い配置、次に岩の数が少ない配置を選びます。
オフの場合は従来どおり、被覆数合計そのものを最大化します。

入力が不正な場合はエラーを表示します。岩の上限が0で乾燥対象がある場合や、
上限以内に全対象をカバーできない場合は、その旨を表示して終了し、部分解は返しません。
乾燥対象がない場合は、岩を使わない空の配置を返します。

成功時は岩の配置、対象の総数、カバー数、重複回数を表示します。

## 計算モデル

- 岩の配置候補は `d` のマスです（岩はそのマスの下に設置する想定）。
- 水平方向は岩を中心にマンハッタン距離5以内のひし形を効果範囲とします。
- 高さ方向は上下4段階まで届くモデルですが、現段階では全マスを同じ高さと仮定します。
- 岩の使用数は指定した上限以下とします。
- 最優先で全 `d` マスをカバーできる配置を探します。
- 全件をカバーできる配置がある場合に限り、各 `d` マスの被覆数の合計を最大化します。
- ブラウザー版では効率チェックにより目的を切り替えられます。オンの場合も全件被覆を必須とし、被覆数合計を岩の使用数で割った値を最大化します。
- この重複回数は乾燥判定頻度の代理指標であり、実際の乾燥時間ではありません。
- パターンの繰り返し行数は実行時に指定でき、空欄の場合は10行です。

これらは本ツールの計算モデルです。ゲーム内の効果範囲、設置条件、乾燥動作との一致は
未確認であり、検証済みのゲーム仕様として扱いません。

## テスト

```bash
python -m unittest -v
```

## 制約

厳密な分枝限定探索を使用するため、候補マスが多い場合は計算時間が増加することがあります。

## English

### Smooth Rock Placement Optimizer

A local tool for optimizing Smooth Rock placements in *Pokémon Pokopia*.
It includes a Python CLI and an HTML/JavaScript browser version under `web/`.
No external service or library is required.

This tool was created for personal use. The accuracy of its calculations and their validity
in the game are not guaranteed. Codex was used during development.

### Purpose

The script expands a one-dimensional pattern into the requested number of rows and searches
for a placement that covers every drying target without exceeding the user-specified stone limit.

### Requirements

- Python 3.10 or later
- Python standard library only

### Input Format

`s` represents a cell that does not need drying, and `d` represents a drying target.
In the calculation model, a Smooth Rock is placed underneath a `d` cell, so only `d` cells
are placement candidates.

Example pattern:

```text
[s][d][s][d][s][d][s]
```

The pattern is repeated for the requested number of rows. Leave the row-count input blank to
use the default of 10 rows. The stone limit is also entered at runtime.

### Running

```bash
python main.py
```

Command-line prompts are displayed in both Japanese and English. Example:

```text
配置パターン / Pattern (e.g. [s][d][s][d][s]): [s][d][s][d][s]
繰り返し行数 / Repeated rows (default: 10): 10
さらさら岩の上限 / Smooth Rock limit: 3
```

### Browser Version

Open `web/index.html` in a browser. No server or dependency installation is required.
Enter the pattern, row count, and stone limit to view the placement grid, stone coordinates,
and overlap score. When **Maximize coverage per rock** is checked, the browser version maximizes
the overlap count divided by the number of stones among full-coverage placements. Ties prefer
a higher overlap count, then fewer stones. When unchecked, it maximizes the overlap count as before.

Invalid input is reported as an error. If drying targets exist but the stone limit is zero,
or if every target cannot be covered within the limit, the script reports that no valid
placement exists and does not return a partial solution. If there are no drying targets,
it returns an empty placement without using any stones.

For a successful placement, the script displays the stone coordinates, target count,
coverage count, and overlap count.

### Calculation Model

- Placement candidates are `d` cells; a stone is modeled as being placed underneath its cell.
- The horizontal effect area is a diamond within Manhattan distance 5 of each stone.
- The modeled vertical reach is up to 4 levels above and below. For now, all cells are assumed to have the same height.
- The number of stones used must not exceed the specified limit.
- The primary requirement is to cover every `d` cell.
- Only among placements that cover every target does the script maximize the sum of coverage counts across all `d` cells.
- In the browser version, the efficiency checkbox switches the objective to overlap count divided by the number of stones, while still requiring full coverage. Ties prefer higher overlap, then fewer stones.
- This overlap count is a proxy for drying-check frequency, not a measure of actual drying time.
- The row repetition count can be entered at runtime; it defaults to 10 when left blank.

These are assumptions used by this tool's calculation model. The in-game effect range,
placement rules, and drying behavior have not been verified and must not be treated as
confirmed game specifications.

### Tests

```bash
python -m unittest -v
```

### Limitations

The script uses exact branch-and-bound search, so runtime may increase when there are many
candidate cells.
