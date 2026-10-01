from __future__ import annotations

import json
import re
import ssl
from gzip import decompress as gzip_decompress
from datetime import UTC, datetime
from decimal import Decimal, InvalidOperation
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urljoin
from urllib.request import Request, urlopen

import certifi
from bs4 import BeautifulSoup

from domain import PriceObservation, ProductTarget


class ExtractionError(RuntimeError):
    pass


def utc_now() -> str:
    return datetime.now(UTC).isoformat()


def normalize_text(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", value.lower()).strip()


def fetch_html(url: str, timeout_seconds: int = 15) -> str:
    request = Request(
        url,
        headers={
            "User-Agent": "AJE-CompetitorPriceMonitor/1.0 (technical assessment)",
            "Accept-Language": "es-PE,es;q=0.9",
        },
    )
    try:
        ssl_context = ssl.create_default_context(cafile=certifi.where())
        with urlopen(request, timeout=timeout_seconds, context=ssl_context) as response:
            if response.status >= 400:
                raise ExtractionError(f"HTTP {response.status} from {url}")
            body = response.read()
            if response.headers.get("Content-Encoding", "").lower() == "gzip":
                body = gzip_decompress(body)
            return body.decode("utf-8", errors="replace")
    except HTTPError as error:
        raise ExtractionError(f"HTTP {error.code} from {url}") from error
    except URLError as error:
        raise ExtractionError(f"Network error from {url}: {error.reason}") from error


def parse_price(value: Any) -> Decimal | None:
    if value is None:
        return None
    cleaned = str(value).replace("S/", "").replace("PEN", "").strip()
    cleaned = cleaned.replace(" ", "")
    # Competitor sites may represent PEN decimals as either 55.92 or 55,92.
    # Preserve the decimal separator instead of turning 55,92 into 5592.
    if "," in cleaned and "." not in cleaned:
        cleaned = cleaned.replace(",", ".")
    else:
        cleaned = cleaned.replace(",", "")
    match = re.search(r"\d+(?:\.\d{1,2})?", cleaned)
    if not match:
        return None
    try:
        return Decimal(match.group())
    except InvalidOperation:
        return None


def walk_json(value: Any) -> list[dict[str, Any]]:
    if isinstance(value, dict):
        nested = [value]
        for child in value.values():
            nested.extend(walk_json(child))
        return nested
    if isinstance(value, list):
        nested: list[dict[str, Any]] = []
        for child in value:
            nested.extend(walk_json(child))
        return nested
    return []


def json_ld_products(html: str) -> list[dict[str, Any]]:
    soup = BeautifulSoup(html, "html.parser")
    products: list[dict[str, Any]] = []
    for script in soup.select('script[type="application/ld+json"]'):
        try:
            payload = json.loads(script.get_text(strip=True))
        except json.JSONDecodeError:
            continue
        for candidate in walk_json(payload):
            product_type = candidate.get("@type")
            if product_type == "Product" or (
                isinstance(product_type, list) and "Product" in product_type
            ):
                products.append(candidate)
    return products


def stock_from_availability(value: str | None) -> str:
    normalized = (value or "").lower()
    if "instock" in normalized or "in stock" in normalized:
        return "disponible"
    if "outofstock" in normalized or "out of stock" in normalized:
        return "agotado"
    return "desconocido"


def stock_from_text(value: str) -> str:
    normalized = normalize_text(value)
    if "agotado" in normalized or "sin stock" in normalized:
        return "agotado"
    if "muy pocas unidades" in normalized:
        return "muy pocas unidades"
    if "pocas unidades" in normalized:
        return "pocas unidades"
    return "disponible"


def find_dermashop_card_observation(
    *, run_id: str, store: str, source_url: str, html: str, target: ProductTarget
) -> PriceObservation | None:
    soup = BeautifulSoup(html, "html.parser")
    for card in soup.select(".card--product"):
        title = card.select_one(".card__title")
        if title is None:
            continue
        name = title.get_text(" ", strip=True)
        normalized_name = normalize_text(name)
        if not all(normalize_text(term) in normalized_name for term in target.match_terms):
            continue
        price_node = card.select_one(".price__current")
        price = parse_price(price_node.get_text(" ", strip=True) if price_node else None)
        if price is None:
            continue
        link = card.find("a", href=True)
        return PriceObservation(
            run_id=run_id,
            store=store,
            product_key=target.product_key,
            product_name=name,
            price_pen=price,
            stock=stock_from_text(card.get_text(" ", strip=True)),
            product_url=urljoin(source_url, str(link["href"]) if link else source_url),
            extracted_at=utc_now(),
        )
    return None


def find_observation(
    *, run_id: str, store: str, source_url: str, html: str, target: ProductTarget
) -> PriceObservation:
    for product in json_ld_products(html):
        name = str(product.get("name", ""))
        normalized_name = normalize_text(name)
        if not all(normalize_text(term) in normalized_name for term in target.match_terms):
            continue

        offers = product.get("offers", {})
        if isinstance(offers, list):
            offers = offers[0] if offers else {}
        price = parse_price(offers.get("price"))
        if price is None:
            continue
        return PriceObservation(
            run_id=run_id,
            store=store,
            product_key=target.product_key,
            product_name=name,
            price_pen=price,
            stock=stock_from_availability(offers.get("availability")),
            product_url=str(product.get("url") or source_url),
            extracted_at=utc_now(),
        )

    if store == "Dermashop":
        card_observation = find_dermashop_card_observation(
            run_id=run_id,
            store=store,
            source_url=source_url,
            html=html,
            target=target,
        )
        if card_observation is not None:
            return card_observation

    raise ExtractionError(
        f"No structured product match for {target.product_key} in {store}; "
        "review the site's extractor or product configuration"
    )
