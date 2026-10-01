# Cobertura real de las fuentes

## Resultado de validación inicial

El 1 de octubre de 2026 se validaron las tres URLs con una única petición HTTP por fuente y TLS verificado.

| Fuente | Resultado | Implicación |
|---|---|---|
| Flora y Fauna | La página VTEX responde y muestra tarjetas de cuidado corporal. El producto CeraVe configurado no aparece en esa URL. | Requiere un producto equivalente que exista en esa categoría o una URL de producto acordada. |
| Dermashop | La página responde y contiene una tarjeta para CeraVe Gel Limpiador Espumoso 236 ml a S/ 55.92, marcado agotado durante la consulta. | El extractor específico de tarjetas funciona y conserva el estado de stock. |
| Inkafarma | La página responde como SPA Angular; el HTML inicial no trae productos, precios ni stock. | Requiere integrar el endpoint público de catálogo que consume la aplicación, o una fuente/URL de producto renderizada autorizada. |

## Decisión del MVP

La configuración declara un producto objetivo y cada tienda intenta obtener una observación equivalente. Si la fuente no ofrece el producto o no expone un catálogo procesable, la Lambda falla de manera explícita después de sus reintentos, Step Functions registra el contexto y SQS dispara el correo solicitado.

Esto es preferible a inventar precios, usar equivalencias no verificadas o intentar eludir protecciones de los sitios. El reporte se genera con las observaciones válidas; los fallos quedan visibles como evidencia operacional.

## Siguiente incremento

Para cobertura completa de tres tiendas, el responsable funcional debe confirmar uno de estos criterios:

1. SKU/EAN o lista de productos equivalentes realmente vendidos por las tres tiendas.
2. Una URL de producto por tienda para cada producto comparado.
3. Autorización de integración con las APIs públicas/documentadas de cada competidor, respetando sus términos de uso y rate limits.
