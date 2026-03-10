"""
Plugin-based Tax Engine for multi-region tax calculation.

Supports:
- India GST (CGST + SGST / IGST)
- GCC VAT (5% standard)
- EU VAT (country-specific rates)
"""

from abc import ABC, abstractmethod
from typing import Dict, Optional
from dataclasses import dataclass


@dataclass
class TaxResult:
    """Result of tax calculation."""
    region: str
    tax_rate: float  # Total tax rate percentage
    tax_amount: float
    breakdown: Dict[str, float]  # e.g. {"cgst": 9, "sgst": 9} or {"vat": 5}
    tax_label: str  # Display label, e.g. "GST 18%", "VAT 5%"


class TaxPlugin(ABC):
    """Base interface for all tax plugins."""

    @abstractmethod
    def calculate_tax(self, price: float, product_tax_rate: Optional[float] = None,
                      tax_exempt: bool = False, **kwargs) -> TaxResult:
        pass

    @abstractmethod
    def get_region_code(self) -> str:
        pass


class IndiaGSTPlugin(TaxPlugin):
    """India GST: CGST + SGST (intra-state) or IGST (inter-state)."""

    DEFAULT_RATE = 18.0  # Default GST rate
    RATES = {
        "exempt": 0,
        "low": 5,
        "standard": 12,
        "high": 18,
        "luxury": 28,
    }

    def get_region_code(self) -> str:
        return "india_gst"

    def calculate_tax(self, price: float, product_tax_rate: Optional[float] = None,
                      tax_exempt: bool = False, inter_state: bool = False, **kwargs) -> TaxResult:
        if tax_exempt:
            return TaxResult(region="india_gst", tax_rate=0, tax_amount=0,
                             breakdown={}, tax_label="Tax Exempt")

        rate = product_tax_rate if product_tax_rate is not None else self.DEFAULT_RATE
        tax_amount = price * (rate / 100)

        if inter_state:
            breakdown = {"igst": tax_amount}
            label = f"IGST {rate}%"
        else:
            half = tax_amount / 2
            breakdown = {"cgst": half, "sgst": half}
            label = f"GST {rate}% (CGST {rate/2}% + SGST {rate/2}%)"

        return TaxResult(
            region="india_gst",
            tax_rate=rate,
            tax_amount=round(tax_amount, 2),
            breakdown={k: round(v, 2) for k, v in breakdown.items()},
            tax_label=label
        )


class GCCVATPlugin(TaxPlugin):
    """GCC VAT: Standard 5% for UAE, Saudi, Bahrain, Oman, Kuwait, Qatar."""

    COUNTRY_RATES = {
        "AE": 5.0,   # UAE
        "SA": 15.0,  # Saudi Arabia (increased to 15%)
        "BH": 10.0,  # Bahrain
        "OM": 5.0,   # Oman
        "KW": 0.0,   # Kuwait (no VAT yet)
        "QA": 0.0,   # Qatar (no VAT yet)
    }
    DEFAULT_RATE = 5.0

    def get_region_code(self) -> str:
        return "gcc_vat"

    def calculate_tax(self, price: float, product_tax_rate: Optional[float] = None,
                      tax_exempt: bool = False, country_code: str = "AE", **kwargs) -> TaxResult:
        if tax_exempt:
            return TaxResult(region="gcc_vat", tax_rate=0, tax_amount=0,
                             breakdown={}, tax_label="Tax Exempt")

        rate = product_tax_rate if product_tax_rate is not None else self.COUNTRY_RATES.get(country_code, self.DEFAULT_RATE)
        tax_amount = price * (rate / 100)

        return TaxResult(
            region="gcc_vat",
            tax_rate=rate,
            tax_amount=round(tax_amount, 2),
            breakdown={"vat": round(tax_amount, 2)},
            tax_label=f"VAT {rate}%"
        )


class EUVATPlugin(TaxPlugin):
    """EU VAT: Country-specific rates."""

    COUNTRY_RATES = {
        "DE": 19.0,  # Germany
        "FR": 20.0,  # France
        "IT": 22.0,  # Italy
        "ES": 21.0,  # Spain
        "NL": 21.0,  # Netherlands
        "BE": 21.0,  # Belgium
        "AT": 20.0,  # Austria
        "PT": 23.0,  # Portugal
        "IE": 23.0,  # Ireland
        "FI": 24.0,  # Finland
        "SE": 25.0,  # Sweden
        "DK": 25.0,  # Denmark
        "PL": 23.0,  # Poland
        "CZ": 21.0,  # Czech Republic
        "RO": 19.0,  # Romania
        "HU": 27.0,  # Hungary (highest in EU)
        "GR": 24.0,  # Greece
    }
    DEFAULT_RATE = 20.0

    def get_region_code(self) -> str:
        return "eu_vat"

    def calculate_tax(self, price: float, product_tax_rate: Optional[float] = None,
                      tax_exempt: bool = False, country_code: str = "DE", **kwargs) -> TaxResult:
        if tax_exempt:
            return TaxResult(region="eu_vat", tax_rate=0, tax_amount=0,
                             breakdown={}, tax_label="Tax Exempt")

        rate = product_tax_rate if product_tax_rate is not None else self.COUNTRY_RATES.get(country_code, self.DEFAULT_RATE)
        tax_amount = price * (rate / 100)

        return TaxResult(
            region="eu_vat",
            tax_rate=rate,
            tax_amount=round(tax_amount, 2),
            breakdown={"vat": round(tax_amount, 2)},
            tax_label=f"VAT {rate}%"
        )


# ===== Tax Engine Registry =====

_PLUGINS: Dict[str, TaxPlugin] = {
    "india_gst": IndiaGSTPlugin(),
    "gcc_vat": GCCVATPlugin(),
    "eu_vat": EUVATPlugin(),
}


def get_tax_plugin(region: str) -> TaxPlugin:
    """Get tax plugin by region code."""
    plugin = _PLUGINS.get(region)
    if not plugin:
        raise ValueError(f"Unknown tax region: {region}. Available: {list(_PLUGINS.keys())}")
    return plugin


def calculate_tax(region: str, price: float, product_tax_rate: Optional[float] = None,
                  tax_exempt: bool = False, **kwargs) -> TaxResult:
    """Main entry point: calculate tax for any region."""
    plugin = get_tax_plugin(region)
    return plugin.calculate_tax(price, product_tax_rate, tax_exempt, **kwargs)


def register_tax_plugin(region: str, plugin: TaxPlugin):
    """Register a custom tax plugin."""
    _PLUGINS[region] = plugin
