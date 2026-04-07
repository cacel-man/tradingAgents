# TradingAgents + TradingView MCP 統合

マルチエージェントLLMトレーディング分析フレームワーク + ビジュアルチャートインテリジェンス

[English](README_PROJECT.md) | 日本語

## 背景

本プロジェクトは [TradingAgents](https://github.com/TauricResearch/TradingAgents)（Xiao et al., 2024）をベースにしています。TradingAgentsは、実際のトレーディングファームの構造を模したマルチエージェントフレームワークで、ファンダメンタルアナリスト、センチメント分析、テクニカルアナリスト、トレーダー、リスク管理チームといった専門LLMエージェントが構造化されたディベートを通じて市場を評価します。

この論文のフレームワークを実装した上で、[tradingview-mcp](https://github.com/tradesdontlie/tradingview-mcp) を活用した **Visual Chart Analyst** を追加しました。TradingViewのライブチャートをスクリーンショットとしてキャプチャし、Claudeのビジョン機能で分析します。2つのシステムは並列に実行され、結果はLLMによって統合された1つの投資判断に合成されます。

## アーキテクチャ

```
+-------------------------+     +----------------------------+
|     TradingAgents       |     |   Visual Chart Analyst     |
|     (LangGraph)         |     |   (tradingview-mcp)        |
|                         |     |                            |
|  ファンダメンタル分析    |     |  tv CLI -> チャート画像     |
|  センチメント分析        |     |  -> Claude Sonnet Vision   |
|  ニュース分析            |     |  -> パターン認識           |
|  テクニカル分析          |     |  -> サポート/レジスタンス   |
|  リサーチャーディベート   |     |                            |
|  トレーダー + リスク管理  |     |                            |
+-----------+-------------+     +-------------+--------------+
            |                                 |
            +----------------+----------------+
                             |
                    +--------v--------+
                    |   結果シンセサイザ  |
                    |  (Claude Sonnet)  |
                    +---------+--------+
                              |
                        統合判断
                   (BUY / HOLD / SELL)
```

## 各コンポーネントの役割

### TradingAgents（論文実装）
- **アナリストチーム**: ファンダメンタル、センチメント、ニュース、テクニカルの4専門アナリストが各視点で評価
- **リサーチャーチーム**: 強気派と弱気派がアナリストの分析結果をディベート
- **トレーダーエージェント**: リサーチを統合してトレーディング判断を生成
- **リスク管理**: ポートフォリオリスクを評価し、提案を承認/却下

### Visual Chart Analyst（新規追加）
- Chrome DevTools Protocol経由でTradingViewのライブチャートをキャプチャ
- チャートスクリーンショットをClaude Sonnetに送信しビジョンベース分析
- トレンド、チャートパターン、サポート/レジスタンスを純粋に視覚データから識別
- 既存の定量分析とは独立した第2の視点を提供

### 結果シンセサイザ
- 両分析の一致点と矛盾点を特定
- 確信度に基づいてファンダメンタル vs ビジュアルシグナルを重み付け
- エントリー/エグジットレベル付きの最終アクション提案を生成

## セットアップ

### 前提条件
- Python 3.10+
- Node.js 18+
- TradingView Desktop（有料プラン）-- ビジュアル分析に必要
- APIキー: Anthropic（またはOpenAI）+ Alpha Vantage

### インストール

```bash
git clone https://github.com/cacel-man/tradingAgents.git
cd tradingAgents

# Python環境
uv venv .venv --python 3.13
source .venv/bin/activate
pip install .

# TradingView MCP（ビジュアル分析用）
cd integrations/tradingview-mcp
npm install
cd ../..

# APIキー設定
cp .env.example .env
# .envを編集:
#   ANTHROPIC_API_KEY=sk-ant-...
#   ALPHA_VANTAGE_API_KEY=...
```

### TradingView Desktop セットアップ

デバッグポート付きで起動:
```bash
/Applications/TradingView.app/Contents/MacOS/TradingView --remote-debugging-port=9222
```

アプリでチャートを開き、接続を確認:
```bash
node integrations/tradingview-mcp/src/cli/index.js status
```

## 使い方

### フルモード（TradingAgents + Visual Chart）

両エージェントが並列実行。TradingView Desktopのデバッグポート起動が必要。

```bash
source .venv/bin/activate
python integrations/tradingview/run_integrated_analysis.py --ticker NVDA --date 2026-04-03
```

### TradingAgentsのみ

TradingView Desktop不要。

```bash
python integrations/tradingview/run_integrated_analysis.py --ticker NVDA --date 2026-04-03 --no-visual
```

### Python API

```python
from integrations.tradingview.run_integrated_analysis import run_integrated_analysis

result = run_integrated_analysis(
    ticker="NVDA",
    date="2026-04-03",
    timeframe="1D",
    use_visual=True,
)

print(result["trading_agents_result"])   # マルチエージェント分析
print(result["visual_result"])           # チャートビジョン分析
print(result["integrated_decision"])     # 統合レコメンデーション
```

### CLIオプション

```
--ticker      銘柄ティッカー (デフォルト: NVDA)
--date        TradingAgentsの分析日 (デフォルト: 2026-04-03)
--timeframe   チャート時間足: 1m, 5m, 15m, 1h, 4h, 1D, 1W, 1M (デフォルト: 1D)
--no-visual   ビジュアル分析をスキップ (TradingAgentsのみ実行)
```

## 実行例

```
======================================================================
  Integrated Analysis: NVDA (2026-04-03)
======================================================================
[TradingAgents] Starting analysis for NVDA on 2026-04-03...
[Visual Chart Analyst] Capturing NVDA chart (1D)...
[Visual Chart Analyst] Chart saved: integrations/tradingview-mcp/screenshots/tv_chart_...png
[Visual Chart Analyst] Analyzing chart with Claude Vision...
[Visual Chart Analyst] Analysis complete.
[TradingAgents] Analysis complete.
[Synthesizer] Merging analyses with Claude...

  INTEGRATED DECISION: SELL / UNDERWEIGHT
  - $176.50-177.00へのバウンスでロングポジション解消
  - 残存ロングのストップロス: $172.50
  - 監視: $173以下または$177以上の日足終値
```

## プロジェクト構成

```
.
├── tradingagents/                 # TradingAgentsフレームワーク本体
│   ├── agents/                    # アナリスト、リサーチャー、トレーダー
│   ├── dataflows/                 # Alpha Vantage + yfinanceデータ
│   ├── graph/                     # LangGraphオーケストレーション
│   └── llm_clients/               # マルチプロバイダLLMサポート
├── integrations/
│   ├── tradingview/               # 新規: Visual Chart Analyst
│   │   ├── visual_chart_analyst.py    # チャートキャプチャ + ビジョン分析
│   │   └── run_integrated_analysis.py # 並列実行 + 結果統合
│   └── tradingview-mcp/           # tradingview-mcp (git submodule)
├── cli/                           # インタラクティブCLI
└── .env                           # APIキー（コミット対象外）
```

## LLM設定

デフォルトではAnthropicを使用:

| 役割 | モデル | 用途 |
|------|--------|------|
| 深い思考 | claude-sonnet-4-20250514 | 複雑な推論、ディベート |
| 高速思考 | claude-haiku-4-5-20251001 | 軽量タスク、要約 |
| ビジョン分析 | claude-sonnet-4-20250514 | チャート画像分析 |
| 統合 | claude-sonnet-4-20250514 | 結果の合成 |

TradingAgentsでOpenAIや他のプロバイダを使う場合は、`run_integrated_analysis.py` のconfigを変更してください。

## 参考文献

- **TradingAgents論文**: Xiao, Y., Sun, E., Luo, D., & Wang, W. (2024). TradingAgents: Multi-Agents LLM Financial Trading Framework. [arXiv:2412.20138](https://arxiv.org/abs/2412.20138)
- **TradingAgentsフレームワーク**: [TauricResearch/TradingAgents](https://github.com/TauricResearch/TradingAgents)
- **TradingView MCP**: [tradesdontlie/tradingview-mcp](https://github.com/tradesdontlie/tradingview-mcp)

## 免責事項

本プロジェクトは研究・教育目的です。トレーディングのパフォーマンスはモデル選択、データ品質、市場環境など多くの要因に依存します。金融・投資・トレーディングのアドバイスではありません。
