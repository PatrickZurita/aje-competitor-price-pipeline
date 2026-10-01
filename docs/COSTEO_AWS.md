# Estimación AWS para el MVP

La calculadora AWS debe completarse con la región real del despliegue antes de la presentación. Este documento deja los supuestos auditables y evita prometer un importe exacto que depende de la región y del consumo.

## Supuesto de carga

| Recurso | Estimación mensual | Supuesto |
|---|---:|---|
| Corridas | 30 | Una corrida diaria. |
| Extracciones Lambda | 90 | Tres tiendas por corrida. |
| Lambda de reporte | 30 | Una por corrida. |
| Lambda notificadora | 0 a 30 | Solo ante fallos. |
| Step Functions Standard | Aproximadamente 15 transiciones por corrida | Dispatcher, Map, extractor, reintentos/eventos de salida y reporte. |
| DynamoDB | Menos de 1 000 lecturas/escrituras | Lista corta de productos. |
| S3 | Menos de 10 MB | JSON de evidencia, no HTML completo. |
| SQS | Menos de 100 mensajes | Solo fallos terminales y reintentos. |

## Servicios incluidos en la calculadora

1. AWS Lambda: 512 MB, 30 segundos máximos, menos de 200 invocaciones mensuales.
2. Step Functions Standard: 450 transiciones mensuales como aproximación inicial.
3. DynamoDB on-demand: menos de 1 000 solicitudes mensuales.
4. S3 Standard: menos de 10 MB almacenados y menos de 1 000 solicitudes.
5. SQS Standard: menos de 100 solicitudes mensuales.
6. EventBridge Scheduler/Rule: una ejecución diaria.
7. Secrets Manager: un secreto OAuth.
8. CloudWatch: logs y trazas; aplicar retención corta para el MVP.

## Justificación de costo

Es una carga muy pequeña y programada. El gasto marginal más predecible será el secreto de Secrets Manager y, según la región, el almacenamiento/retención de logs; las ejecuciones de cómputo y mensajería son mínimas. La calculadora se presenta como una estimación, no como un compromiso de costo fijo.

## Evidencia requerida

Guardar una captura o PDF del resultado de [AWS Pricing Calculator](https://calculator.aws/) en `docs/evidencia/` y registrar la región seleccionada.
