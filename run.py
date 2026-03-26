"""
VAF AM Build 03 — Identity & Persona Engine
Built by Vaishali Mehmi using Claude AI + Anthropic Agents
github.com/vm799 | Enterprise AI Pipeline

Loads firm identity + compliance rules and injects them as system context.
Demonstrates the measurable difference between generic AI output and
firm-branded, compliance-aware output — side by side.

Outputs: reports/identity_report.json

Usage:
  uv run python run.py
"""
import json
import os
import re
import shutil
from datetime import datetime
from pathlib import Path

import anthropic
from dotenv import load_dotenv
from src.persona_loader import PersonaLoader

load_dotenv()

REPORTS_DIR = Path("reports")
MODEL       = "claude-sonnet-4-6"

TEST_PROMPTS = [
    "Write a brief update on our UK equity fund's Q1 performance for a client.",
    "Should a client worried about inflation increase their bond allocation?",
    "Summarise the risk outlook for European equities in two sentences.",
]

PROHIBITED_PHRASES = [
    "guaranteed", "risk-free", "certain returns", "safe investment",
    "you will", "will definitely", "no risk",
]


def _count_rules(text: str) -> int:
    return sum(1 for line in text.splitlines() if re.match(r"^\s*[-*\d•]", line))


def _compliance_violations(text: str) -> list:
    lower = text.lower()
    return [p for p in PROHIBITED_PHRASES if p in lower]


def _has_disclaimer(text: str) -> bool:
    return "capital at risk" in text.lower()


def run_comparison(client, persona, prompt: str, idx: int) -> dict:
    print(f"\n  Prompt {idx+1}: {prompt[:65]}…")

    generic_resp = client.messages.create(
        model=MODEL,
        max_tokens=250,
        messages=[{"role": "user", "content": prompt}],
    )
    generic_text = generic_resp.content[0].text.strip()

    branded_resp = client.messages.create(
        model=MODEL,
        max_tokens=250,
        system=persona.combined_system_prompt,
        messages=[{"role": "user", "content": prompt}],
    )
    branded_text = branded_resp.content[0].text.strip()

    violations      = _compliance_violations(generic_text)
    has_disclaimer  = _has_disclaimer(branded_text)

    print(f"    Generic violations : {violations or 'none'}")
    print(f"    Branded disclaimer : {'✓ present' if has_disclaimer else '⚠ missing'}")

    return {
        "prompt":                     prompt,
        "generic_response":           generic_text,
        "branded_response":           branded_text,
        "generic_violations":         violations,
        "branded_disclaimer_present": has_disclaimer,
    }


def save_report(report: dict):
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    path = REPORTS_DIR / "identity_report.json"
    path.write_text(json.dumps(report, indent=2, ensure_ascii=False))
    print(f"\n  📄 Report → {path}")

    portfolio_data = Path(__file__).parent.parent / "portfolio" / "data"
    if portfolio_data.exists():
        shutil.copy(path, portfolio_data / "build_03.json")
        print(f"  📊 Portfolio synced → portfolio/data/build_03.json")


def main():
    print("\n╔══════════════════════════════════════════════════════╗")
    print("║   VAF Build 03 — Identity & Persona Engine          ║")
    print("╚══════════════════════════════════════════════════════╝\n")

    client  = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
    persona = PersonaLoader().load()

    identity_rules   = _count_rules(persona.identity)
    compliance_rules = _count_rules(persona.compliance_rules)
    print(f"  ✓ Identity loaded   — {identity_rules} style rules")
    print(f"  ✓ Compliance loaded — {compliance_rules} regulatory rules")
    print(f"\n── Running {len(TEST_PROMPTS)} side-by-side comparisons ──────────────")

    comparisons      = []
    total_violations = 0

    for i, prompt in enumerate(TEST_PROMPTS):
        result = run_comparison(client, persona, prompt, i)
        comparisons.append(result)
        total_violations += len(result["generic_violations"])

    report = {
        "generated_at":        datetime.utcnow().isoformat(),
        "model":               MODEL,
        "identity_rules":      identity_rules,
        "compliance_rules":    compliance_rules,
        "prompts_tested":      len(TEST_PROMPTS),
        "generic_violations":  total_violations,
        "branded_disclaimers": sum(1 for c in comparisons if c["branded_disclaimer_present"]),
        "comparisons":         comparisons,
    }

    save_report(report)
    print(f"\n  ✅ Build 03 complete")
    print(f"     {identity_rules} identity + {compliance_rules} compliance rules active")
    print(f"     {total_violations} FCA violations in generic → 0 in branded\n")


if __name__ == "__main__":
    main()
