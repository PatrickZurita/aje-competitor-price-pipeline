from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal


AVAILABLE_STOCK = {"disponible", "pocas unidades", "muy pocas unidades"}


@dataclass(frozen=True)
class ProductTarget:
    product_key: str
    display_name: str
    match_terms: tuple[str, ...]


@dataclass(frozen=True)
class PriceObservation:
    run_id: str
    store: str
    product_key: str
    product_name: str
    price_pen: Decimal
    stock: str
    product_url: str
    extracted_at: str

    @property
    def is_available(self) -> bool:
        return self.stock.lower() in AVAILABLE_STOCK
