"""Utilities for standardizing ticker symbols across providers.

This module provides a Symbol type that inherits from str for type checker compatibility
while providing normalization of ticker symbols and exchange context via MIC codes.

Canonical format uses dot (.) for share class separators and colon (:) for exchange suffix.
Examples: 'AAPL', 'BRK.A', 'RY:XTSE', '7203:XTKS'

References:
    - ISO 10383 MIC codes: https://www.iso20022.org/market-identifier-codes
"""

import json
from pathlib import Path
from typing import Any, TypedDict

from pydantic_core import core_schema


class ExchangeData(TypedDict, total=False):
    """Type definition for exchange data dictionary."""

    mic: str
    acronym: str
    name: str
    city: str
    country: str
    website: str


# Yahoo Finance suffix <-> MIC mapping
_YAHOO_SUFFIX_TO_MIC: dict[str, str] = {
    ".TO": "XTSE",
    ".V": "XTSX",
    ".L": "XLON",
    ".T": "XTKS",
    ".HK": "XHKG",
    ".AX": "XASX",
    ".PA": "XPAR",
    ".DE": "XETR",
    ".MI": "XMIL",
    ".AS": "XAMS",
    ".SW": "XSWX",
    ".KS": "XKRX",
    ".TW": "XTAI",
    ".SA": "BVMF",
    ".MX": "XMEX",
    ".NS": "XNSE",
    ".BO": "XBOM",
}

_MIC_TO_YAHOO_SUFFIX: dict[str, str] = {v: k for k, v in _YAHOO_SUFFIX_TO_MIC.items()}

# US exchanges get no Yahoo suffix
_US_EXCHANGES = {"XNYS", "XNAS", "XASE", "ARCX", "BATS"}

# Provider-specific share class separator (canonical is dot)
_PROVIDER_SHARE_CLASS_SEP: dict[str, str] = {
    "yfinance": "-",
    "sec": "-",
}

# Provider-specific exchange suffix builders
_PROVIDER_EXCHANGE_SUFFIX: dict[str, dict[str, str]] = {
    "yfinance": _MIC_TO_YAHOO_SUFFIX,
}


def _load_exchange_data() -> dict[str, ExchangeData]:
    """Load exchange data from JSON and build MIC lookup.

    Returns a dict mapping uppercase MIC codes to exchange data.
    """
    data_path = Path(__file__).parent / "exchange_data.json"
    with open(data_path, encoding="utf-8") as f:
        data = json.load(f)

    lookup: dict[str, ExchangeData] = {}
    for exchange in data["exchanges"]:
        mic = exchange["mic"].upper()
        lookup[mic] = exchange

    return lookup


# Load once at module import
_EXCHANGE_LOOKUP = _load_exchange_data()


class Symbol(str):
    """Symbol string type with exchange context and provider format conversion.

    Inherits from str (storing the canonical ticker) for type checker compatibility
    while providing access to exchange data and provider-specific formatting.

    Canonical format:
        - Dot (.) for share class separators: 'BRK.A'
        - Colon (:) for exchange suffix: 'RY:XTSE'

    Accepts:
        - Plain tickers: 'AAPL', 'MSFT'
        - Share classes with dot or dash: 'BRK.A', 'BRK-A'
        - Ticker with MIC exchange: 'RY:XTSE', '7203:XTKS'

    Examples
    --------
    >>> s = Symbol("AAPL")
    >>> str(s)
    'AAPL'
    >>> s.ticker
    'AAPL'
    >>> s.exchange is None
    True

    >>> s = Symbol("BRK-A")
    >>> str(s)
    'BRK.A'
    >>> s.ticker
    'BRK.A'

    >>> s = Symbol("RY:XTSE")
    >>> str(s)
    'RY'
    >>> s.ticker
    'RY'
    >>> s.exchange
    'XTSE'
    """

    _ticker: str
    _exchange: str | None
    _exchange_data_cache: ExchangeData | None

    def __new__(cls, value: Any) -> "Symbol":
        """Create a new Symbol instance.

        Parameters
        ----------
        value : Any
            Symbol input. Accepts plain tickers, share classes (dot or dash),
            and ticker:MIC format for exchange context.

        Returns
        -------
        Symbol
            A Symbol instance storing the canonical ticker as its string value.

        Raises
        ------
        ValueError
            If an exchange MIC code is provided but not found in exchange data.
        """
        if isinstance(value, Symbol):
            instance = super().__new__(cls, value._ticker)
            instance._ticker = value._ticker
            instance._exchange = value._exchange
            instance._exchange_data_cache = value._exchange_data_cache
            return instance

        raw = str(value).strip()
        exchange: str | None = None
        exchange_data_val: ExchangeData | None = None

        # Parse exchange suffix (colon-separated MIC)
        if ":" in raw:
            parts = raw.split(":", 1)
            raw = parts[0]
            mic = parts[1].upper()
            if mic not in _EXCHANGE_LOOKUP:
                raise ValueError(
                    f"Invalid exchange MIC: '{parts[1]}'. "
                    "Must be a valid ISO 10383 MIC code (e.g., 'XTSE', 'XLON')."
                )
            exchange = mic
            exchange_data_val = _EXCHANGE_LOOKUP[mic]

        # Normalize share class separator: dash -> dot
        ticker = raw.replace("-", ".")

        instance = super().__new__(cls, ticker)
        instance._ticker = ticker
        instance._exchange = exchange
        instance._exchange_data_cache = exchange_data_val
        return instance

    @property
    def ticker(self) -> str:
        """The base ticker in canonical format (e.g., 'BRK.A', 'AAPL')."""
        return self._ticker

    @property
    def exchange(self) -> str | None:
        """MIC code of the exchange, if provided (e.g., 'XTSE')."""
        return self._exchange

    @property
    def exchange_data(self) -> ExchangeData | None:
        """Full exchange info from exchange_data.json, if exchange is set."""
        return self._exchange_data_cache

    def to_provider_format(self, provider: str) -> str:
        """Convert canonical symbol to provider-specific format.

        Parameters
        ----------
        provider : str
            Provider name (e.g., 'yfinance', 'sec', 'fmp', 'intrinio', 'polygon').

        Returns
        -------
        str
            The symbol formatted for the specified provider.

        Examples
        --------
        >>> Symbol("BRK.A").to_provider_format("yfinance")
        'BRK-A'
        >>> Symbol("RY:XTSE").to_provider_format("yfinance")
        'RY.TO'
        >>> Symbol("BRK.A").to_provider_format("sec")
        'BRK-A'
        """
        ticker = self._ticker
        p = provider.lower()

        # Apply share class separator
        sep = _PROVIDER_SHARE_CLASS_SEP.get(p)
        if sep:
            ticker = ticker.replace(".", sep)

        # Apply exchange suffix
        if self._exchange and self._exchange not in _US_EXCHANGES:
            suffix_map = _PROVIDER_EXCHANGE_SUFFIX.get(p, {})
            suffix = suffix_map.get(self._exchange, "")
            if suffix:
                ticker = ticker + suffix

        return ticker

    @classmethod
    def from_provider_format(cls, raw: str, provider: str) -> "Symbol":
        """Parse a provider-specific symbol string into a canonical Symbol.

        Parameters
        ----------
        raw : str
            The symbol string in provider-specific format.
        provider : str
            Provider name (e.g., 'yfinance', 'sec', 'fmp').

        Returns
        -------
        Symbol
            A Symbol instance with canonical ticker and exchange context.

        Examples
        --------
        >>> Symbol.from_provider_format("BRK-A", "yfinance")
        Symbol('BRK.A')
        >>> Symbol.from_provider_format("RY.TO", "yfinance")
        Symbol('RY:XTSE')
        """
        raw = raw.strip()
        p = provider.lower()

        if p == "yfinance":
            return cls._from_yfinance(raw)
        if p == "sec":
            return cls._from_sec(raw)
        if p == "fmp":
            return cls._from_fmp(raw)

        # Default: treat as canonical (dash -> dot normalization)
        return cls(raw)

    @classmethod
    def _from_yfinance(cls, raw: str) -> "Symbol":
        """Parse Yahoo Finance format symbol."""
        # Check for exchange suffix (e.g., RY.TO, 7203.T)
        # Must check longest suffixes first to avoid false matches
        for suffix, mic in sorted(
            _YAHOO_SUFFIX_TO_MIC.items(), key=lambda x: len(x[0]), reverse=True
        ):
            if raw.upper().endswith(suffix.upper()):
                ticker = raw[: -len(suffix)]
                # Dash -> dot for share classes in the ticker part
                ticker = ticker.replace("-", ".")
                return cls(f"{ticker}:{mic}")

        # No exchange suffix -> US stock, normalize share class
        return cls(raw.replace("-", "."))

    @classmethod
    def _from_sec(cls, raw: str) -> "Symbol":
        """Parse SEC format symbol (dash-separated share classes)."""
        return cls(raw.replace("-", "."))

    @classmethod
    def _from_fmp(cls, raw: str) -> "Symbol":
        """Parse FMP format symbol."""
        # FMP uses dots for share classes, same as canonical
        return cls(raw)

    def __repr__(self) -> str:
        """Return a string representation of the Symbol."""
        if self._exchange:
            return f"Symbol('{self._ticker}:{self._exchange}')"
        return f"Symbol('{self._ticker}')"

    @classmethod
    def __get_pydantic_core_schema__(cls, _source_type: Any, _handler: Any) -> Any:
        """Return the Pydantic core schema for validation."""
        return core_schema.no_info_after_validator_function(
            cls,
            core_schema.str_schema(),
        )
