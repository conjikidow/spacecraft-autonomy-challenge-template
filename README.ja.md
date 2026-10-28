# Spacecraft Autonomy Challenge: Template

[![License](https://img.shields.io/badge/license-MIT--0-blue.svg?style=flat)](LICENSE)

[English](README.md) | **日本語**

Spacecraft Autonomy Challenge の戦略を書くなら，ここから始めてください。
戦略はシミュレーション上の宇宙機を運用します。
テレメトリを読み取ってコマンドをスケジュールし，制約を守りながら，宇宙機の Δv を目標値まで増やします。

チャレンジ問題，シミュレータ，`autonomy-challenge` コマンドは，
[`spacecraft-autonomy-challenge-core`](https://github.com/conjikidow/spacecraft-autonomy-challenge-core) パッケージが提供します。
このパッケージは，`pyproject.toml` でリリースタグに固定されています。

## 必要なもの

- Python 3.12 以降
- [uv](https://docs.astral.sh/uv/)

## セットアップ

```sh
uv sync
```

## 戦略の実行

戦略は，`submission/strategy.py` の `MyStrategy` クラスとして書きます。
`nominal` シナリオで実行します。

```sh
uv run autonomy-challenge run submission/strategy.py:MyStrategy
```

このコマンドは，シミュレーションがどのように終了したかと，宇宙機の真の状態から計算した評価指標を出力します。

利用可能なシナリオを一覧表示し，別のシナリオで実行します。

```sh
uv run autonomy-challenge scenarios
uv run autonomy-challenge run submission/strategy.py:MyStrategy --scenario thruster-degradation
```

`--json` を付けると，評価指標を JSON として出力します。

## 戦略の書き方

コードやファイルはすべて `submission/` の下に置いてください。
戦略ファイルのディレクトリがインポートパスの先頭に追加されるため，`submission/strategy.py` から `submission/` 内の他のモジュールをインポートできます。
コードと同じ場所に置いたデータファイルを読むときは，`Path(__file__).parent` を基準にパスを組み立ててください。

必要な Python パッケージは uv で追加します。
たとえば次のようにします。

```sh
uv add numpy
```

## ノートブックでの作業

```sh
uv run marimo edit app.py
```

ノートブックでは，宇宙機，ミッション，戦略 API を確認しながら `submission/strategy.py` を編集し，公開シナリオで実行し，提出物を確認して，評価サーバーに提出できます。

## 提出物の確認

```sh
uv run autonomy-challenge check
```

このコマンドは，`submission/` と `pyproject.toml` をメモリ上で `submission.zip` にまとめ，評価サーバーと同じ方法ですべての公開シナリオで評価します。
各シナリオでは戦略を新しい Python プロセスで起動し，`pyproject.toml` のパッケージのうち足りないものは，この確認のためだけにインストールします。
得点，要約，ケースごとの表を出力します。
`uv run autonomy-challenge pack` は，評価せずに `submission.zip` をファイルに書き出します。

## 評価サーバーへの提出

イベントに評価サーバーがある場合は，運営者からその API の URL（`http://<host>:<port>/api/v1` など）と，必要ならトークンが伝えられます。
`http://<host>:<port>` のようにパスのない URL は `http://<host>:<port>/api/v1` として扱われます。

```sh
export EVALUATION_SERVER_URL=<URL>
export EVALUATION_SERVER_TOKEN=<トークン>
uv run submit.py            # 非公開シナリオでの練習評価：結果を待って表示する
uv run submit.py --final    # 最終提出：受付票を表示する
```

Windows の場合や環境変数を使わない場合は，`--server <URL>` と `--token <トークン>` を指定してください。
練習評価の結果を待つのをやめても，評価はサーバー上で続きます。
あとから `uv run submit.py --status <ID>` で確認できます。
提出者は `git config user.email` と `git config user.name` で識別されます。
`--participant-id` と `--participant-name` で上書きでき，`uv run submit.py --help` ですべてのオプションを確認できます。
ノートブックでは，**Evaluation server** セクションにサーバーの設定を入力します。
練習評価は **Practice on hidden scenarios** セクションから，最終提出は **Submit the final version** セクションから行えます。
URL とトークンは `EVALUATION_SERVER_URL` と `EVALUATION_SERVER_TOKEN` から，メールアドレスと名前は `git config` から，あらかじめ入力されています。

サーバーに順位表がある場合は，`uv run submit.py --board` で，最終提出を受け付けているかどうかと残り時間，公開後の最終順位とともに表示できます。
`--mine` を付けると，自分の練習提出だけを表示します。
ノートブックの **Leaderboard** セクションでも同じものを表示できます。
練習の順位表は，練習評価のすべてのケースではなく，サーバーの固定の練習ケースだけでの得点で順位を付けます。
サーバーがこの得点を返す場合は，練習評価の結果にも **Fixed cases** として表示されます。

## ドキュメント

API とチャレンジについては，core リポジトリのドキュメントを参照してください。
リンク先は，このテンプレートが使用している core のバージョンのドキュメントです。

- [戦略の書き方](https://github.com/conjikidow/spacecraft-autonomy-challenge-core/blob/v1.3.2/docs/strategy.ja.md)：ライフサイクル，`MissionBrief`，`Commander`
- [コマンドとタイムライン](https://github.com/conjikidow/spacecraft-autonomy-challenge-core/blob/v1.3.2/docs/timeline.ja.md)：コマンドの種類と順序規則
- [宇宙機モデル](https://github.com/conjikidow/spacecraft-autonomy-challenge-core/blob/v1.3.2/docs/spacecraft-model.ja.md)：状態，ダイナミクス，テレメトリ
- [シミュレーション](https://github.com/conjikidow/spacecraft-autonomy-challenge-core/blob/v1.3.2/docs/simulation.ja.md)：イベントの順序と終了条件
- [チャレンジ問題](https://github.com/conjikidow/spacecraft-autonomy-challenge-core/blob/v1.3.2/docs/challenge.ja.md)：チャレンジ問題とその公開シナリオ
- [評価](https://github.com/conjikidow/spacecraft-autonomy-challenge-core/blob/v1.3.2/docs/evaluation.ja.md)：シミュレーション後に出力される評価指標
- [コマンドラインツール](https://github.com/conjikidow/spacecraft-autonomy-challenge-core/blob/v1.3.2/README.ja.md#コマンドラインツール)：`run`，`pack`，`check` のオプションと終了ステータス
- [提出アーカイブ](https://github.com/conjikidow/spacecraft-autonomy-challenge-core/blob/v1.3.2/docs/submission.ja.md)：`submission.zip` の内容
- [参加者のパッケージ](https://github.com/conjikidow/spacecraft-autonomy-challenge-core/blob/v1.3.2/docs/dependencies.ja.md)：`pyproject.toml` のパッケージの再現方法
- [得点](https://github.com/conjikidow/spacecraft-autonomy-challenge-core/blob/v1.3.2/docs/scoring.ja.md)：評価ケースと `Suite` の得点の計算方法

## ライセンス

このテンプレートは [MIT-0](LICENSE) ライセンスで提供されているため，著作権表示を残さなくても，これを土台に提出物を作れます。
あなたが追加したファイルはあなたのものであり，どのようにライセンスしても構いません。
