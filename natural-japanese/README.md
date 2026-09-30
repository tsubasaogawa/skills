# Natural Japanese

日本語の社内文書、技術文書、記事を自然で読みやすく書く・直す・採点するスキル。設計、執筆、静的検知、判断台帳による点検、収束までを一つの工程として定める。

## Origin

Forked from https://github.com/coji/natural-japanese (skills/natural-japanese, v1.5.0, MIT License).
Grateful thanks.

このリポジトリの japanese-tech-writing の規範をマージし、両者が衝突する箇所は japanese-tech-writing 側を優先している。取り込み元と優先順位は `SKILL.md` の frontmatter (`metadata.merged-from`) に記録している。

短文の否定→肯定対句、判断を方向で言う比喩動詞、読点による溜め強調、スライドの「誰が、何を、どうした」復元テストの規範と `references/examples.md` の事例 4 は、Kiminori Yokoi「[AI臭い文章とは何なのか](https://speakerdeck.com/nasuvitz/ai-kusai-bunshou-toha-nanina-no-ka)」(2026-09-28 豊洲会) の指摘と具体例を取り込んだもの。

## Usage

```text
/natural-japanese write full 調査レポートの下書きを書いて
/natural-japanese score quick draft.md
このメモ、AI っぽいので直して
```

引数は `[write|score] [quick|full|exp] [対象ファイルや依頼内容]`。省略時は依頼内容から推定する。

## Scripts

`scripts/` の静的検知は `uv run` で実行する。依存 (sudachipy など) はスクリプトの inline metadata から自動解決される。

```console
uv run scripts/lint.py --json <file>
uv run scripts/lint.py --reading-load <file>
uv run scripts/outline.py <file>
uv run scripts/terms.py <file>
```

`scripts/semantic.py` は torch と sentence-transformers に依存する実験的な opt-in 検出器で、初回に約 1 GB のモデルをダウンロードする。

## License

MIT。原著作者 coji の著作権表示を `LICENSE` に残している。
