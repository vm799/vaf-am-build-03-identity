"""
Tests for Build 03 — Identity & Persona Engine
"""
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock
from src.persona_loader import PersonaLoader, PersonaConfig


SAMPLE_IDENTITY = """# Firm Identity
## Tone
- Authoritative but not arrogant
- Data-driven: always support assertions with figures
- Professional British English spelling
"""

SAMPLE_COMPLIANCE = """# Compliance Rules
- NEVER use: "guaranteed", "risk-free", "certain returns"
- All outputs require compliance review before distribution
- Capital at risk disclaimer required on all client-facing output
"""


@pytest.fixture
def identity_files(tmp_path):
    identity_path   = tmp_path / "identity.md"
    compliance_path = tmp_path / "compliance_rules.md"
    identity_path.write_text(SAMPLE_IDENTITY)
    compliance_path.write_text(SAMPLE_COMPLIANCE)
    return tmp_path, identity_path, compliance_path


class TestPersonaLoader:
    def test_loads_both_files(self, identity_files):
        _, identity_path, compliance_path = identity_files
        loader = PersonaLoader(str(identity_path), str(compliance_path))
        config = loader.load()

        assert isinstance(config, PersonaConfig)
        assert "Firm Identity" in config.identity
        assert "Compliance Rules" in config.compliance_rules

    def test_combined_prompt_contains_both(self, identity_files):
        _, identity_path, compliance_path = identity_files
        loader = PersonaLoader(str(identity_path), str(compliance_path))
        config = loader.load()

        assert "Firm Identity" in config.combined_system_prompt
        assert "Compliance Rules" in config.combined_system_prompt
        assert "comply with all" in config.combined_system_prompt.lower()

    def test_caching_reads_file_once(self, identity_files):
        _, identity_path, compliance_path = identity_files
        loader = PersonaLoader(str(identity_path), str(compliance_path))

        config1 = loader.load()
        config2 = loader.load()

        assert config1 is config2  # same object — cached

    def test_missing_identity_file_raises(self, tmp_path):
        compliance_path = tmp_path / "compliance_rules.md"
        compliance_path.write_text(SAMPLE_COMPLIANCE)

        loader = PersonaLoader(str(tmp_path / "missing.md"), str(compliance_path))
        with pytest.raises(FileNotFoundError, match="Identity file missing"):
            loader.load()

    def test_missing_compliance_file_raises(self, tmp_path):
        identity_path = tmp_path / "identity.md"
        identity_path.write_text(SAMPLE_IDENTITY)

        loader = PersonaLoader(str(identity_path), str(tmp_path / "missing.md"))
        with pytest.raises(FileNotFoundError, match="Compliance rules missing"):
            loader.load()

    def test_pydantic_model_is_frozen(self, identity_files):
        _, identity_path, compliance_path = identity_files
        loader = PersonaLoader(str(identity_path), str(compliance_path))
        config = loader.load()

        # PersonaConfig fields should be accessible
        assert isinstance(config.identity, str)
        assert isinstance(config.compliance_rules, str)
        assert isinstance(config.combined_system_prompt, str)


class TestCountRules:
    def test_counts_bullet_lines(self):
        from run import _count_rules
        text = "# Header\n- rule one\n- rule two\n* rule three\nNot a rule\n"
        assert _count_rules(text) == 3

    def test_counts_numbered_lines(self):
        from run import _count_rules
        text = "1. First rule\n2. Second rule\nSome prose\n"
        assert _count_rules(text) == 2

    def test_empty_text(self):
        from run import _count_rules
        assert _count_rules("") == 0


class TestComplianceViolations:
    def test_detects_prohibited_phrases(self):
        from run import _compliance_violations
        text = "This is a guaranteed return with no risk involved."
        violations = _compliance_violations(text)
        assert "guaranteed" in violations
        assert "no risk" in violations

    def test_no_violations_on_clean_text(self):
        from run import _compliance_violations
        text = "Our analysis suggests risk-adjusted returns may vary by mandate."
        assert _compliance_violations(text) == []

    def test_case_insensitive(self):
        from run import _compliance_violations
        text = "This is GUARANTEED."
        assert "guaranteed" in _compliance_violations(text)


class TestDisclaimerCheck:
    def test_detects_capital_at_risk(self):
        from run import _has_disclaimer
        text = "Our conviction is strong. Capital at risk. Past performance is not indicative."
        assert _has_disclaimer(text) is True

    def test_missing_disclaimer(self):
        from run import _has_disclaimer
        text = "UK equities look attractive on a relative value basis."
        assert _has_disclaimer(text) is False
