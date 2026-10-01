from decimal import Decimal
import unittest

from extractors import find_observation, parse_price
from domain import ProductTarget


class ExtractorTests(unittest.TestCase):
    def test_extracts_json_ld_product(self) -> None:
        html = """
        <script type="application/ld+json">
          {"@context":"https://schema.org", "@type":"Product", "name":"CeraVe Gel Limpiador 236 ml",
           "url":"https://example.test/cerave", "offers":{"price":"55.92", "availability":"https://schema.org/InStock"}}
        </script>
        """
        target = ProductTarget(
            product_key="cerave-gel-limpiador-236ml",
            display_name="CeraVe Gel Limpiador 236 ml",
            match_terms=("cerave", "gel", "limpiador", "236"),
        )

        observation = find_observation(
            run_id="run-1", store="Dermashop", source_url="https://example.test", html=html, target=target
        )

        self.assertEqual(observation.price_pen, Decimal("55.92"))
        self.assertEqual(observation.stock, "disponible")
        self.assertEqual(observation.product_url, "https://example.test/cerave")

    def test_parses_peruvian_decimal_comma(self) -> None:
        self.assertEqual(parse_price("S/ 55,92"), Decimal("55.92"))

    def test_extracts_dermashop_product_card(self) -> None:
        html = """
        <article class="card--product">
          <a href="/products/cerave-gel-limpiador">Product</a>
          <h3 class="card__title">Gel Limpiador CeraVe Espumoso Piel Mixta a Grasa 236 ml</h3>
          <span class="price__current">Precio de venta S/ 55.92</span>
          <span class="price__no-variant">Agotado</span>
        </article>
        """
        target = ProductTarget(
            product_key="cerave-gel-limpiador-236ml",
            display_name="CeraVe Gel Limpiador 236 ml",
            match_terms=("cerave", "gel", "limpiador", "236"),
        )

        observation = find_observation(
            run_id="run-1", store="Dermashop", source_url="https://dermashop.pe", html=html, target=target
        )

        self.assertEqual(observation.price_pen, Decimal("55.92"))
        self.assertEqual(observation.stock, "agotado")
        self.assertEqual(observation.product_url, "https://dermashop.pe/products/cerave-gel-limpiador")
