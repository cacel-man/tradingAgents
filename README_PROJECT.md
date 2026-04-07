# TradingAgents + TradingView MCP Integration

Multi-agent LLM trading analysis framework with visual chart intelligence.

## Background

This project builds on [TradingAgents](https://github.com/TauricResearch/TradingAgents) (Xiao et al., 2024), a multi-agent trading framework that mirrors real-world trading firm dynamics. The original paper proposes specialized LLM agents -- fundamental analysts, sentiment experts, technical analysts, traders, and risk managers -- that collaboratively evaluate market conditions through structured debates.

We implemented the TradingAgents framework and extended it with a **Visual Chart Analyst** powered by [tradingview-mcp](https://github.com/tradesdontlie/tradingview-mcp), which captures live TradingView charts and analyzes them using Claude's vision capabilities. The two systems run in parallel and their outputs are synthesized into a single integrated decision.

## Architecture

```
+-------------------------+     +----------------------------+
|     TradingAgents       |     |   Visual Chart Analyst     |
|     (LangGraph)         |     |   (tradingview-mcp)        |
|                         |     |                            |
|  Fundamental Analyst    |     |  tv CLI -> chart screenshot |
|  Sentiment Analyst      |     |  -> Claude Sonnet Vision   |
|  News Analyst           |     |  -> pattern recognition    |
|  Technical Analyst      |     |  -> support/resistance     |
|  Researcher Debate      |     |                            |
|  Trader + Risk Mgmt     |     |                            |
+-----------+-------------+     +-------------+--------------+
            |                                 |
            +----------------+----------------+
                             |
                    +--------v--------+
                    | Result Synthesizer|
                    | (Claude Sonnet)   |
                    +---------+--------+
                              |
                     Integrated Decision
                    (BUY / HOLD / SELL)
```

## What Each Component Does

### TradingAgents (Paper Implementation)
- **Analyst Team**: 4 specialized analysts evaluate fundamentals, sentiment, news, and technical indicators
- **Researcher Team**: Bull and bear researchers debate the analysts' findings
- **Trader Agent**: Synthesizes research into a trading decision
- **Risk Management**: Evaluates portfolio risk and approves/rejects proposals

### Visual Chart Analyst (New)
- Captures live TradingView charts via Chrome DevTools Protocol
- Sends chart screenshots to Claude Sonnet for vision-based analysis
- Identifies trends, patterns, support/resistance levels purely from visual data
- Provides a second, independent perspective on market conditions

### Result Synthesizer
- Merges both analyses, identifying agreements and conflicts
- Weights fundamental vs. visual signals based on confidence
- Produces a final actionable recommendation with entry/exit levels

## Setup

### Prerequisites
- Python 3.10+
- Node.js 18+
- TradingView Desktop (paid subscription) -- for visual analysis
- API keys: Anthropic (or OpenAI) + Alpha Vantage

### Installation

```bash
git clone https://github.com/cacel-man/tradingAgents.git
cd tradingAgents

# Python environment
uv venv .venv --python 3.13
source .venv/bin/activate
pip install .

# TradingView MCP (for visual analysis)
cd integrations/tradingview-mcp
npm install
cd ../..

# API keys
cp .env.example .env
# Edit .env with your keys:
#   ANTHROPIC_API_KEY=sk-ant-...
#   ALPHA_VANTAGE_API_KEY=...
```

### TradingView Desktop Setup

Launch with debug port enabled:
```bash
/Applications/TradingView.app/Contents/MacOS/TradingView --remote-debugging-port=9222
```

Open a chart in the app, then verify connection:
```bash
node integrations/tradingview-mcp/src/cli/index.js status
```

## Usage

### Full Mode (TradingAgents + Visual Chart)

Both agents run in parallel. Requires TradingView Desktop running with debug port.

```bash
source .venv/bin/activate
python integrations/tradingview/run_integrated_analysis.py --ticker NVDA --date 2026-04-03
```

### TradingAgents Only

No TradingView Desktop required.

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

print(result["trading_agents_result"])   # Multi-agent analysis
print(result["visual_result"])           # Chart vision analysis
print(result["integrated_decision"])     # Synthesized recommendation
```

### CLI Options

```
--ticker      Stock ticker symbol (default: NVDA)
--date        Analysis date for TradingAgents (default: 2026-04-03)
--timeframe   Chart timeframe: 1m, 5m, 15m, 1h, 4h, 1D, 1W, 1M (default: 1D)
--no-visual   Skip visual analysis (TradingAgents only)
```

## Example Output

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
  - Exit long positions on bounce toward $176.50-177.00
  - Stop loss for remaining longs: $172.50
  - Monitor: Daily closes below $173 or above $177
```

## Project Structure

```
.
├── tradingagents/                 # Original TradingAgents framework
│   ├── agents/                    # Analyst, researcher, trader agents
│   ├── dataflows/                 # Alpha Vantage + yfinance data
│   ├── graph/                     # LangGraph orchestration
│   └── llm_clients/               # Multi-provider LLM support
├── integrations/
│   ├── tradingview/               # New: Visual Chart Analyst
│   │   ├── visual_chart_analyst.py    # Chart capture + vision analysis
│   │   └── run_integrated_analysis.py # Parallel execution + synthesis
│   └── tradingview-mcp/           # tradingview-mcp (git submodule)
├── cli/                           # Interactive CLI
└── .env                           # API keys (not committed)
```

## LLM Configuration

The integration uses Anthropic by default:

| Role | Model | Purpose |
|------|-------|---------|
| Deep thinking | claude-sonnet-4-20250514 | Complex reasoning, debates |
| Quick thinking | claude-haiku-4-5-20251001 | Fast tasks, summarization |
| Vision analysis | claude-sonnet-4-20250514 | Chart image analysis |
| Synthesis | claude-sonnet-4-20250514 | Result integration |

To use OpenAI or other providers for TradingAgents, modify the config in `run_integrated_analysis.py`.

## References

- **TradingAgents Paper**: Xiao, Y., Sun, E., Luo, D., & Wang, W. (2024). TradingAgents: Multi-Agents LLM Financial Trading Framework. [arXiv:2412.20138](https://arxiv.org/abs/2412.20138)
- **TradingAgents Framework**: [TauricResearch/TradingAgents](https://github.com/TauricResearch/TradingAgents)
- **TradingView MCP**: [tradesdontlie/tradingview-mcp](https://github.com/tradesdontlie/tradingview-mcp)

## Disclaimer

This project is for research and educational purposes only. Trading performance depends on many factors including model choice, data quality, and market conditions. This is not financial, investment, or trading advice.
