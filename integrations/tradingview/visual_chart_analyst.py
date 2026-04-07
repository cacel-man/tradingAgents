"""Visual Chart Analyst - Captures TradingView charts and analyzes them with Claude Vision."""

import base64
import json
import os
import re
import subprocess
from pathlib import Path

import anthropic
from dotenv import load_dotenv


TV_MCP_DIR = Path(__file__).resolve().parents[2] / "integrations" / "tradingview-mcp"
TV_CLI = TV_MCP_DIR / "src" / "cli" / "index.js"

_VALID_TICKER = re.compile(r"^[A-Z0-9.\-]{1,20}$")
_VALID_TIMEFRAMES = {"1m", "5m", "15m", "30m", "1h", "2h", "4h", "1D", "1W", "1M"}


def _run_tv(args: list[str], timeout: int = 30) -> dict:
    """Run a tv CLI command and return parsed JSON output."""
    cmd = ["node", str(TV_CLI)] + args
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
    if result.returncode != 0:
        raise RuntimeError(f"tv CLI failed (exit {result.returncode}): {result.stderr.strip()}")
    return json.loads(result.stdout) if result.stdout.strip() else {}


def capture_chart(ticker: str, timeframe: str = "1D") -> Path:
    """Set symbol/timeframe on TradingView and capture a chart screenshot.

    Args:
        ticker: Stock ticker symbol (e.g. "NVDA")
        timeframe: Chart timeframe (e.g. "1D", "1h", "4h", "1W")

    Returns:
        Path to the saved PNG screenshot.
    """
    if not _VALID_TICKER.match(ticker):
        raise ValueError(f"Invalid ticker format: {ticker!r}")
    if timeframe not in _VALID_TIMEFRAMES:
        raise ValueError(f"Invalid timeframe: {timeframe!r}. Must be one of {_VALID_TIMEFRAMES}")

    _run_tv(["symbol", ticker])
    _run_tv(["timeframe", timeframe])
    result = _run_tv(["screenshot", "-r", "chart"], timeout=60)

    if not result.get("success"):
        raise RuntimeError(f"Screenshot capture failed: {result}")

    file_path = result.get("file_path")
    if not file_path:
        raise RuntimeError("Screenshot response missing file_path")
    path = Path(file_path).resolve()
    screenshot_dir = (TV_MCP_DIR / "screenshots").resolve()
    if not path.is_relative_to(screenshot_dir):
        raise ValueError(f"Screenshot path {path} is outside allowed directory {screenshot_dir}")
    if path.suffix.lower() != ".png":
        raise ValueError(f"Unexpected file type: {path.suffix}")
    if not path.exists():
        raise FileNotFoundError(f"Screenshot not found at {path}")
    return path


def analyze_chart(image_path: Path, ticker: str, context: str = "") -> str:
    """Analyze a chart image using Claude Sonnet vision.

    Args:
        image_path: Path to the chart PNG file.
        ticker: Ticker symbol for context.
        context: Optional additional context for the analysis.

    Returns:
        Structured analysis string.
    """
    load_dotenv()
    client = anthropic.Anthropic()

    image_data = base64.standard_b64encode(image_path.read_bytes()).decode("utf-8")

    system_prompt = (
        "You are an expert technical analyst specializing in chart pattern recognition "
        "and visual analysis of financial charts. Analyze the provided TradingView chart "
        "image and provide a detailed technical analysis.\n\n"
        "Structure your response as:\n"
        "## Trend Analysis\n"
        "Overall trend direction and strength.\n\n"
        "## Key Levels\n"
        "Support and resistance levels visible on the chart.\n\n"
        "## Chart Patterns\n"
        "Any recognizable patterns (head & shoulders, flags, wedges, etc.).\n\n"
        "## Indicator Signals\n"
        "Analysis of any visible indicators (moving averages, volume, RSI, etc.).\n\n"
        "## Visual Signal Summary\n"
        "| Signal | Direction | Confidence |\n"
        "|--------|-----------|------------|\n\n"
        "## Recommendation\n"
        "BUY / HOLD / SELL with rationale based purely on visual chart analysis."
    )

    user_content = [
        {
            "type": "image",
            "source": {
                "type": "base64",
                "media_type": "image/png",
                "data": image_data,
            },
        },
        {
            "type": "text",
            "text": f"Analyze this TradingView chart for {ticker}. {context}".strip(),
        },
    ]

    response = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=2000,
        system=system_prompt,
        messages=[{"role": "user", "content": user_content}],
    )

    if not response.content or not hasattr(response.content[0], "text"):
        raise RuntimeError("Unexpected empty or non-text response from Claude API")
    return response.content[0].text


def run_visual_analysis(ticker: str, timeframe: str = "1D") -> dict:
    """Full pipeline: capture chart → analyze with vision.

    Args:
        ticker: Stock ticker symbol.
        timeframe: Chart timeframe.

    Returns:
        Dict with keys: ticker, timeframe, image_path, analysis
    """
    print(f"[Visual Chart Analyst] Capturing {ticker} chart ({timeframe})...")
    image_path = capture_chart(ticker, timeframe)
    print(f"[Visual Chart Analyst] Chart saved: {image_path}")

    print(f"[Visual Chart Analyst] Analyzing chart with Claude Vision...")
    analysis = analyze_chart(image_path, ticker)
    print(f"[Visual Chart Analyst] Analysis complete.")

    return {
        "ticker": ticker,
        "timeframe": timeframe,
        "image_path": str(image_path),
        "analysis": analysis,
    }


if __name__ == "__main__":
    import sys
    ticker = sys.argv[1] if len(sys.argv) > 1 else "NVDA"
    result = run_visual_analysis(ticker)
    print("\n" + "=" * 60)
    print(result["analysis"])
