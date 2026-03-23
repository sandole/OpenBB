"""Tests for Symbol type in symbol_helpers.py."""

import pytest
from openbb_core.provider.utils.symbol_helpers import Symbol

# --- Creation and normalization ---


def test_plain_ticker():
    """Test creating a Symbol from a plain ticker."""
    s = Symbol("AAPL")
    assert str(s) == "AAPL"
    assert s.ticker == "AAPL"
    assert s.exchange is None
    assert s.exchange_data is None


def test_share_class_dot():
    """Test creating a Symbol with dot-separated share class."""
    s = Symbol("BRK.A")
    assert str(s) == "BRK.A"
    assert s.ticker == "BRK.A"


def test_share_class_dash_normalizes_to_dot():
    """Test that dash share class separator normalizes to dot."""
    s = Symbol("BRK-A")
    assert str(s) == "BRK.A"
    assert s.ticker == "BRK.A"


def test_exchange_parsing():
    """Test parsing ticker with MIC exchange suffix."""
    s = Symbol("RY:XTSE")
    assert str(s) == "RY"
    assert s.ticker == "RY"
    assert s.exchange == "XTSE"
    assert s.exchange_data is not None
    assert s.exchange_data["mic"] == "XTSE"


def test_exchange_parsing_tokyo():
    """Test parsing ticker with Tokyo exchange."""
    s = Symbol("7203:XTKS")
    assert str(s) == "7203"
    assert s.ticker == "7203"
    assert s.exchange == "XTKS"


def test_exchange_case_insensitive():
    """Test that exchange MIC is case-insensitive."""
    s = Symbol("RY:xtse")
    assert s.exchange == "XTSE"


def test_invalid_exchange_raises():
    """Test that an invalid MIC code raises ValueError."""
    with pytest.raises(ValueError, match="Invalid exchange MIC"):
        Symbol("AAPL:FAKE")


def test_copy_from_symbol():
    """Test creating a Symbol from another Symbol."""
    s1 = Symbol("RY:XTSE")
    s2 = Symbol(s1)
    assert s2.ticker == "RY"
    assert s2.exchange == "XTSE"


def test_whitespace_stripped():
    """Test that whitespace is stripped from input."""
    s = Symbol("  AAPL  ")
    assert s.ticker == "AAPL"


# --- to_provider_format ---


def test_yfinance_share_class():
    """Test yfinance share class conversion (dot to dash)."""
    assert Symbol("BRK.A").to_provider_format("yfinance") == "BRK-A"


def test_yfinance_exchange_suffix():
    """Test yfinance exchange suffix for Toronto."""
    assert Symbol("RY:XTSE").to_provider_format("yfinance") == "RY.TO"


def test_yfinance_tokyo():
    """Test yfinance exchange suffix for Tokyo."""
    assert Symbol("7203:XTKS").to_provider_format("yfinance") == "7203.T"


def test_yfinance_london():
    """Test yfinance exchange suffix for London."""
    assert Symbol("VOD:XLON").to_provider_format("yfinance") == "VOD.L"


def test_yfinance_us_no_suffix():
    """Test yfinance US exchanges get no suffix."""
    assert Symbol("AAPL:XNAS").to_provider_format("yfinance") == "AAPL"
    assert Symbol("AAPL:XNYS").to_provider_format("yfinance") == "AAPL"


def test_yfinance_plain_ticker():
    """Test yfinance with no exchange returns plain ticker."""
    assert Symbol("AAPL").to_provider_format("yfinance") == "AAPL"


def test_sec_share_class():
    """Test SEC share class conversion (dot to dash)."""
    assert Symbol("BRK.A").to_provider_format("sec") == "BRK-A"


def test_fmp_preserves_dots():
    """Test FMP preserves dot share class separator."""
    assert Symbol("BRK.A").to_provider_format("fmp") == "BRK.A"


def test_intrinio_preserves_dots():
    """Test Intrinio preserves dot share class separator."""
    assert Symbol("BRK.A").to_provider_format("intrinio") == "BRK.A"


def test_polygon_preserves_dots():
    """Test Polygon preserves dot share class separator."""
    assert Symbol("BRK.A").to_provider_format("polygon") == "BRK.A"


def test_unknown_provider_returns_ticker():
    """Test unknown provider returns canonical ticker."""
    assert Symbol("BRK.A").to_provider_format("unknown") == "BRK.A"


# --- from_provider_format ---


def test_from_yfinance_share_class():
    """Test parsing yfinance share class format."""
    s = Symbol.from_provider_format("BRK-A", "yfinance")
    assert s.ticker == "BRK.A"
    assert s.exchange is None


def test_from_yfinance_exchange_suffix():
    """Test parsing yfinance exchange suffix."""
    s = Symbol.from_provider_format("RY.TO", "yfinance")
    assert s.ticker == "RY"
    assert s.exchange == "XTSE"


def test_from_yfinance_tokyo():
    """Test parsing yfinance Tokyo suffix."""
    s = Symbol.from_provider_format("7203.T", "yfinance")
    assert s.ticker == "7203"
    assert s.exchange == "XTKS"


def test_from_yfinance_hong_kong():
    """Test parsing yfinance Hong Kong suffix."""
    s = Symbol.from_provider_format("0005.HK", "yfinance")
    assert s.ticker == "0005"
    assert s.exchange == "XHKG"


def test_from_yfinance_no_suffix():
    """Test parsing yfinance ticker with no exchange suffix."""
    s = Symbol.from_provider_format("AAPL", "yfinance")
    assert s.ticker == "AAPL"
    assert s.exchange is None


def test_from_sec_share_class():
    """Test parsing SEC share class format."""
    s = Symbol.from_provider_format("BRK-A", "sec")
    assert s.ticker == "BRK.A"


def test_from_fmp_passthrough():
    """Test FMP format passes through as canonical."""
    s = Symbol.from_provider_format("BRK.A", "fmp")
    assert s.ticker == "BRK.A"


def test_from_default_provider():
    """Test default provider normalizes dash to dot."""
    s = Symbol.from_provider_format("BRK-A", "intrinio")
    assert s.ticker == "BRK.A"


# --- Round-trip ---


def test_yfinance_share_class_roundtrip():
    """Test yfinance share class round-trip conversion."""
    original = Symbol("BRK.A")
    yf_fmt = original.to_provider_format("yfinance")
    assert yf_fmt == "BRK-A"
    restored = Symbol.from_provider_format(yf_fmt, "yfinance")
    assert restored.ticker == "BRK.A"


def test_yfinance_exchange_roundtrip():
    """Test yfinance exchange round-trip conversion."""
    original = Symbol("RY:XTSE")
    yf_fmt = original.to_provider_format("yfinance")
    assert yf_fmt == "RY.TO"
    restored = Symbol.from_provider_format(yf_fmt, "yfinance")
    assert restored.ticker == "RY"
    assert restored.exchange == "XTSE"


def test_sec_roundtrip():
    """Test SEC share class round-trip conversion."""
    original = Symbol("BRK.A")
    sec_fmt = original.to_provider_format("sec")
    assert sec_fmt == "BRK-A"
    restored = Symbol.from_provider_format(sec_fmt, "sec")
    assert restored.ticker == "BRK.A"


# --- str behavior ---


def test_str_returns_ticker():
    """Test str() returns the canonical ticker."""
    assert str(Symbol("AAPL")) == "AAPL"


def test_str_with_exchange_returns_ticker():
    """Test str() returns ticker even when exchange is set."""
    assert str(Symbol("RY:XTSE")) == "RY"


def test_as_dict_key():
    """Test Symbol works as a dict key and matches str keys."""
    d = {Symbol("AAPL"): 100}
    assert d["AAPL"] == 100
    assert d[Symbol("AAPL")] == 100


def test_in_set():
    """Test Symbol works in sets and matches str values."""
    s = {Symbol("AAPL"), Symbol("MSFT")}
    assert "AAPL" in s
    assert Symbol("AAPL") in s


def test_equality_with_str():
    """Test Symbol equality with plain str."""
    assert Symbol("AAPL") == "AAPL"


def test_repr():
    """Test repr output format."""
    assert repr(Symbol("AAPL")) == "Symbol('AAPL')"
    assert repr(Symbol("RY:XTSE")) == "Symbol('RY:XTSE')"


# --- Pydantic integration ---


def test_pydantic_schema_exists():
    """Test that Pydantic core schema method works."""
    schema = Symbol.__get_pydantic_core_schema__(Symbol, None)
    assert schema is not None
