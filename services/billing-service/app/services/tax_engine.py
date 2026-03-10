"""
Plugin-based Tax Engine — India GST, GCC VAT, EU VAT.
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class TaxResult:
    region: str
    tax_rate: float
    tax_amount: float
    breakdown: Dict[str, float] = field(default_factory=dict)
    tax_label: str = ""


class TaxPlugin(ABC):
    @abstractmethod
    def calculate_tax(self, price: float, product_tax_rate: Optional[float] = None,
                      tax_exempt: bool = False, **kwargs) -> TaxResult:
        pass

    @abstractmethod
    def get_region_code(self) -> str:
        pass


class IndiaGSTPlugin(TaxPlugin):
    """India GST: CGST+SGST intra-state or IGST inter-state."""
    DEFAULT_RATE = 18.0
    SLAB_RATES = [0, 5, 12, 18, 28]

    def get_region_code(self) -> str:
        return "india_gst"

    def _snap_to_slab(self, rate: float) -> float:
        return min(self.SLAB_RATES, key=lambda s: abs(s - rate))

    def calculate_tax(self, price: float, product_tax_rate: Optional[float] = None,
                      tax_exempt: bool = False, inter_state: bool = False, **kwargs) -> TaxResult:
        if tax_exempt or price <= 0:
            return TaxResult("india_gst", 0, 0, {}, "Tax Exempt")
        rate = self._snap_to_slab(product_tax_rate if product_tax_rate is not None else self.DEFAULT_RATE)
        tax_amount = price * (rate / 100)
        if inter_state:
            breakdown = {"igst": round(tax_amount, 2)}
            label = f"IGST {rate}%"
        else:
            half = round(tax_amount / 2, 2)
            breakdown = {"cgst": half, "sgst": half}
            label = f"GST {rate}% (CGST {rate/2}% + SGST {rate/2}%)"
        return TaxResult("india_gst", rate, round(tax_amount, 2), breakdown, label)


class GCCVATPlugin(TaxPlugin):
    """GCC VAT: UAE 5%, Saudi 15%, Bahrain 10%, others 5%."""
    COUNTRY_RATES = {
        "AE": 5.0,   # UAE
        "SA": 15.0,  # Saudi Arabia
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
        if tax_exempt or price <= 0:
            return TaxResult("gcc_vat", 0, 0, {}, "VAT Exempt")
        rate = product_tax_rate if product_tax_rate is not None else \
               self.COUNTRY_RATES.get(country_code.upper(), self.DEFAULT_RATE)
        tax_amount = price * (rate / 100)
        return TaxResult("gcc_vat", rate, round(tax_amount, 2),
                         {"vat": round(tax_amount, 2)}, f"VAT {rate}%")


class EUVATPlugin(TaxPlugin):
    """EU VAT: per-country standard rates with OSS support."""
    COUNTRY_RATES = {
        "DE": 19.0, "FR": 20.0, "GB": 20.0, "IT": 22.0, "ES": 21.0,
        "NL": 21.0, "BE": 21.0, "PL": 23.0, "SE": 25.0, "DK": 25.0,
        "NO": 25.0, "FI": 24.0, "AT": 20.0, "PT": 23.0, "GR": 24.0,
        "CZ": 21.0, "HU": 27.0, "RO": 19.0, "SK": 20.0, "SI": 22.0,
        "LU": 17.0, "IE": 23.0, "HR": 25.0, "BG": 20.0, "EE": 22.0,
        "LV": 21.0, "LT": 21.0, "MT": 18.0, "CY": 19.0,
    }
    DEFAULT_RATE = 20.0
    REDUCED_CATEGORIES = {"food", "books", "medicine", "children"}

    def get_region_code(self) -> str:
        return "eu_vat"

    def calculate_tax(self, price: float, product_tax_rate: Optional[float] = None,
                      tax_exempt: bool = False, country_code: str = "DE",
                      product_category: str = "", **kwargs) -> TaxResult:
        if tax_exempt or price <= 0:
            return TaxResult("eu_vat", 0, 0, {}, "VAT Exempt")
        if product_tax_rate is not None:
            rate = product_tax_rate
        else:
            rate = self.COUNTRY_RATES.get(country_code.upper(), self.DEFAULT_RATE)
            if any(cat in product_category.lower() for cat in self.REDUCED_CATEGORIES):
                rate = max(5.0, rate * 0.5)
        tax_amount = price * (rate / 100)
        return TaxResult("eu_vat", rate, round(tax_amount, 2),
                         {"vat": round(tax_amount, 2)}, f"VAT {rate}% ({country_code})")


class TaxEngine:
    """Central tax engine — selects plugin by region and calculates tax."""
    _plugins: Dict[str, TaxPlugin] = {}

    def __init__(self):
        for plugin in [IndiaGSTPlugin(), GCCVATPlugin(), EUVATPlugin()]:
            self._plugins[plugin.get_region_code()] = plugin

    def get_plugin(self, region: str) -> TaxPlugin:
        plugin = self._plugins.get(region)
        if not plugin:
            raise ValueError(f"Unsupported tax region: {region}. "
                             f"Supported: {list(self._plugins.keys())}")
        return plugin

    def calculate(self, price: float, region: str, product_tax_rate: Optional[float] = None,
                  tax_exempt: bool = False, **kwargs) -> TaxResult:
        return self.get_plugin(region).calculate_tax(
            price=price, product_tax_rate=product_tax_rate,
            tax_exempt=tax_exempt, **kwargs
        )

    def calculate_invoice_tax(self, items: List[Dict], region: str,
                               inter_state: bool = False, country_code: str = "IN") -> Dict:
        """Calculate total tax for a list of invoice items."""
        total_subtotal = 0.0
        total_tax = 0.0
        total_cgst = 0.0
        total_sgst = 0.0
        total_igst = 0.0
        total_vat = 0.0

        for item in items:
            price = item.get("price_per_unit", 0) * item.get("quantity", 1)
            discount = price * (item.get("discount_pct", 0) / 100)
            taxable = price - discount
            total_subtotal += taxable

            result = self.calculate(
                price=taxable,
                region=region,
                product_tax_rate=item.get("gst_percentage") or item.get("tax_rate"),
                tax_exempt=item.get("tax_exempt", False),
                inter_state=inter_state,
                country_code=country_code,
            )
            total_tax += result.tax_amount
            total_cgst += result.breakdown.get("cgst", 0)
            total_sgst += result.breakdown.get("sgst", 0)
            total_igst += result.breakdown.get("igst", 0)
            total_vat += result.breakdown.get("vat", 0)

        return {
            "subtotal": round(total_subtotal, 2),
            "tax_total": round(total_tax, 2),
            "cgst": round(total_cgst, 2),
            "sgst": round(total_sgst, 2),
            "igst": round(total_igst, 2),
            "vat": round(total_vat, 2),
            "total": round(total_subtotal + total_tax, 2),
        }


# Singleton instance
tax_engine = TaxEngine()
