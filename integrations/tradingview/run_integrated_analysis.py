"""Integrated analysis: TradingAgents + Visual Chart Analyst in parallel."""

import sys
import os
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

# Ensure project root is on path
PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))

from dotenv import load_dotenv

load_dotenv(PROJECT_ROOT / ".env")

import anthropic
from tradingagents.graph.trading_graph import TradingAgentsGraph
from tradingagents.default_config import DEFAULT_CONFIG
from integrations.tradingview.visual_chart_analyst import run_visual_analysis


def run_trading_agents(ticker: str, date: str, config: dict) -> str:
    """Run TradingAgents analysis and return the decision text."""
    print(f"[TradingAgents] Starting analysis for {ticker} on {date}...")
    ta = TradingAgentsGraph(debug=False, config=config)
    _, decision = ta.propagate(ticker, date)
    print(f"[TradingAgents] Analysis complete.")
    return decision


def run_visual_analyst(ticker: str, timeframe: str = "1D") -> str:
    """Run Visual Chart Analyst and return the analysis text."""
    result = run_visual_analysis(ticker, timeframe)
    return result["analysis"]


def synthesize_results(
    ticker: str,
    trading_agents_result: str,
    visual_result: str,
) -> str:
    """Synthesize both analyses into a final integrated decision."""
    print("[Synthesizer] Merging analyses with Claude...")

    client = anthropic.Anthropic()

    prompt = f"""You are a senior portfolio manager. You have received two independent analyses for {ticker}:

## Analysis 1: Multi-Agent Fundamental/Technical Analysis (TradingAgents)
{trading_agents_result}

## Analysis 2: Visual Chart Analysis (TradingView Chart Vision)
{visual_result}

---

Synthesize these two analyses into a single, cohesive investment recommendation. Structure your response as:

## Agreement & Conflicts
Where do the two analyses agree? Where do they conflict?

## Integrated Technical View
Combined technical picture from both quantitative indicators and visual chart patterns.

## Confidence Assessment
How much more (or less) confident are you given both perspectives?

## Final Integrated Decision
**BUY / HOLD / SELL** with:
- Position sizing recommendation
- Entry/exit levels
- Key risk factors
- Monitoring triggers

Be specific and actionable. If the analyses conflict, explain which you weight more heavily and why."""

    response = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=3000,
        messages=[{"role": "user", "content": prompt}],
    )

    if not response.content or not hasattr(response.content[0], "text"):
        raise RuntimeError("Unexpected empty or non-text response from Claude API")
    return response.content[0].text


def run_integrated_analysis(
    ticker: str = "NVDA",
    date: str = "2026-04-03",
    timeframe: str = "1D",
    use_visual: bool = True,
) -> dict:
    """Run full integrated analysis pipeline.

    Args:
        ticker: Stock ticker symbol.
        date: Analysis date for TradingAgents.
        timeframe: Chart timeframe for visual analysis.
        use_visual: If False, skip visual analysis (for when TradingView isn't running).

    Returns:
        Dict with trading_agents_result, visual_result (if used), and integrated_decision.
    """
    config = DEFAULT_CONFIG.copy()
    config["llm_provider"] = "anthropic"
    config["deep_think_llm"] = "claude-sonnet-4-20250514"
    config["quick_think_llm"] = "claude-haiku-4-5-20251001"
    config["backend_url"] = None

    results = {}

    if use_visual:
        # Run both in parallel
        with ThreadPoolExecutor(max_workers=2) as executor:
            futures = {
                executor.submit(run_trading_agents, ticker, date, config): "trading_agents",
                executor.submit(run_visual_analyst, ticker, timeframe): "visual",
            }
            for future in as_completed(futures):
                key = futures[future]
                try:
                    results[key] = future.result()
                except Exception as e:
                    print(f"[ERROR] {key} failed: {e}")
                    results[key] = f"Analysis failed: {e}"
    else:
        # TradingAgents only
        results["trading_agents"] = run_trading_agents(ticker, date, config)

    output = {
        "ticker": ticker,
        "date": date,
        "trading_agents_result": results.get("trading_agents", "Not available"),
    }

    if use_visual and "visual" in results:
        output["visual_result"] = results["visual"]
        # Synthesize if both succeeded
        if not results["trading_agents"].startswith("Analysis failed") and \
           not results["visual"].startswith("Analysis failed"):
            output["integrated_decision"] = synthesize_results(
                ticker, results["trading_agents"], results["visual"]
            )
        else:
            output["integrated_decision"] = "Synthesis skipped due to partial failure."
    else:
        output["integrated_decision"] = results.get("trading_agents", "No result")

    return output


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Integrated TradingAgents + Visual Chart Analysis")
    parser.add_argument("--ticker", default="NVDA", help="Stock ticker (default: NVDA)")
    parser.add_argument("--date", default="2026-04-03", help="Analysis date (default: 2026-04-03)")
    parser.add_argument("--timeframe", default="1D", help="Chart timeframe (default: 1D)")
    parser.add_argument(
        "--no-visual", action="store_true",
        help="Skip visual analysis (use when TradingView Desktop is not running)",
    )
    args = parser.parse_args()

    print("=" * 70)
    print(f"  Integrated Analysis: {args.ticker} ({args.date})")
    print("=" * 70)

    result = run_integrated_analysis(
        ticker=args.ticker,
        date=args.date,
        timeframe=args.timeframe,
        use_visual=not args.no_visual,
    )

    print("\n" + "=" * 70)
    print("  TRADINGAGENTS RESULT")
    print("=" * 70)
    print(result["trading_agents_result"])

    if "visual_result" in result:
        print("\n" + "=" * 70)
        print("  VISUAL CHART ANALYSIS")
        print("=" * 70)
        print(result["visual_result"])

    print("\n" + "=" * 70)
    print("  INTEGRATED DECISION")
    print("=" * 70)
    print(result["integrated_decision"])
