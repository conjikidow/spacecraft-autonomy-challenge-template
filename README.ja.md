# Spacecraft Operations Challenge: Submission Template

[![License](https://img.shields.io/badge/license-MIT--0-blue.svg?style=flat)](LICENSE)

[English](README.md) | **日本語**

Spacecraft Operations Challenge の戦略を書くなら，ここから始めてください。
戦略はシミュレーション上の宇宙機を運用します。
テレメトリを読み取ってコマンドをスケジュールし，制約を守りながら，宇宙機の Δv を目標値まで増やします。

チャレンジ問題，シミュレータ，`spacecraft-ops-challenge` コマンドは，
[`spacecraft-operations-challenge-core`](https://github.com/conjikidow/spacecraft-operations-challenge-core) パッケージが提供します。
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
uv run spacecraft-ops-challenge run submission/strategy.py:MyStrategy
```

このコマンドは，シミュレーションがどのように終了したかと，宇宙機の真の状態から計算した評価指標を出力します。

利用可能なシナリオを一覧表示し，別のシナリオで実行します。

```sh
uv run spacecraft-ops-challenge scenarios
uv run spacecraft-ops-challenge run submission/strategy.py:MyStrategy --scenario thruster-degradation
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

## ドキュメント

API とチャレンジについては，core リポジトリのドキュメントを参照してください。
リンク先は，このテンプレートが使用している core のバージョンのドキュメントです。

- [戦略の書き方](https://github.com/conjikidow/spacecraft-operations-challenge-core/blob/v0.1.2/docs/strategy.ja.md)：ライフサイクル，`MissionBrief`，`Commander`
- [コマンドとタイムライン](https://github.com/conjikidow/spacecraft-operations-challenge-core/blob/v0.1.2/docs/timeline.ja.md)：コマンドの種類と順序規則
- [宇宙機モデル](https://github.com/conjikidow/spacecraft-operations-challenge-core/blob/v0.1.2/docs/spacecraft-model.ja.md)：状態，ダイナミクス，テレメトリ
- [シミュレーション](https://github.com/conjikidow/spacecraft-operations-challenge-core/blob/v0.1.2/docs/simulation.ja.md)：イベントの順序と終了条件
- [チャレンジ問題](https://github.com/conjikidow/spacecraft-operations-challenge-core/blob/v0.1.2/docs/challenge.ja.md)：チャレンジ問題とその公開シナリオ
- [評価](https://github.com/conjikidow/spacecraft-operations-challenge-core/blob/v0.1.2/docs/evaluation.ja.md)：シミュレーション後に出力される評価指標
- [コマンドラインツール](https://github.com/conjikidow/spacecraft-operations-challenge-core/blob/v0.1.2/README.ja.md#コマンドラインツール)：オプションと終了ステータス

## ライセンス

このテンプレートは [MIT-0](LICENSE) ライセンスで提供されているため，著作権表示を残さなくても，これを土台に提出物を作れます。
あなたが追加したファイルはあなたのものであり，どのようにライセンスしても構いません。
