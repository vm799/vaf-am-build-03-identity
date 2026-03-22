# BUILD 03 — Identity & Persona Files
**VAF AM Series | Day: Tuesday | Build Time: ~1 hour**
*Built with Claude AI + Anthropic Agents | Asset Management*

## WHAT THIS BUILDS
Two Markdown files — `identity.md` + `compliance_rules.md` — that define your firm's voice, tone, regulatory language, and prohibited phrases. Loaded into every agent as system context. Demo shows same prompt producing fundamentally different output with/without identity files.

## QUICK START
```bash
git clone https://github.com/vm799/vaf-am-build-03
cd vaf-am-build-03 && cp .env.example .env && uv sync
uv run python run.py   # shows output with vs without identity files
```

## CORE CODE
```python
# src/persona_loader.py
"""VAF AM Build 03 — Identity & Persona Files
Built by Vaishali Mehmi using Claude AI + Anthropic Agents"""
from pathlib import Path
from pydantic import BaseModel

class PersonaConfig(BaseModel):
    identity: str
    compliance_rules: str
    combined_system_prompt: str

class PersonaLoader:
    def __init__(self,
                 identity_path="identity_files/identity.md",
                 compliance_path="identity_files/compliance_rules.md"):
        self._identity_path    = Path(identity_path)
        self._compliance_path  = Path(compliance_path)
        self._cache: PersonaConfig | None = None

    def load(self) -> PersonaConfig:
        if self._cache:
            return self._cache
        if not self._identity_path.exists():
            raise FileNotFoundError(f"Identity file missing: {self._identity_path}")
        identity    = self._identity_path.read_text(encoding="utf-8")
        compliance  = self._compliance_path.read_text(encoding="utf-8")
        combined    = f"{identity}\n---\n{compliance}\n---\nEvery response must comply with all rules above."
        self._cache = PersonaConfig(identity=identity, compliance_rules=compliance,
                                    combined_system_prompt=combined)
        return self._cache
```

## COLOSSUS QA CHECKLIST
- [ ] PersonaLoader cached — files read once per session
- [ ] Missing file raises clear FileNotFoundError (not silent failure)
- [ ] Compliance rules validated on load (warn if disclaimer section missing)
- [ ] Identity files contain only templates with [PLACEHOLDER] markers — no real firm data
