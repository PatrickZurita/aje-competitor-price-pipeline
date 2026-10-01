# Guion de presentación — 30 minutos

## 1. Problema y criterio de éxito — 3 min

> La solución monitorea un conjunto pequeño y explícito de productos dermo-cosméticos en tres competidores. Cada corrida debe conservar evidencia, continuar aunque una fuente falle, notificar fallas y dejar una matriz de comparación en Google Drive.

- Éxito no significa asumir precios: significa publicar solamente observaciones cuya equivalencia y precio se pudieron verificar.
- La lista de productos está versionada en `src/product_targets.json` para evitar comparaciones engañosas por similitud de texto.

## 2. Arquitectura — 5 min

Mostrar `arquitectura.drawio`.

> EventBridge dispara una Lambda dispatcher. Esta inicia Step Functions Standard, que procesa una tienda por vez. Cada extractor persiste el resultado normalizado en DynamoDB y evidencia cruda en S3. Al final se construye el Sheet. Los errores terminales llegan a SQS y una Lambda notificadora usa Gmail API.

- Step Functions **Standard**: trazabilidad visual, reintentos, historial y mejor defensa para un flujo operacional.
- `MaxConcurrency: 1`: protege a las fuentes externas y hace más fácil interpretar una corrida inicial.
- SQS desacopla el fallo de extracción del envío de correo; una DLQ protege los avisos que no se puedan entregar.

## 3. Modelo de datos y API de integración — 4 min

> DynamoDB agrupa los datos por corrida: `PK = RUN#<runId>` y `SK = OBS#<productKey>#<store>`. Así el reporte consulta únicamente una ejecución y cada observación conserva URL, fecha, stock, precio decimal y clave del JSON en S3.

- S3 conserva el payload normalizado por tienda: `raw/<runId>/<store>.json`.
- Google Sheets representa las columnas requeridas: producto/categoría, tienda, precio PEN, stock, URL y alerta de menor precio.
- La alerta se asigna solo entre observaciones equivalentes y disponibles; no se declara un “menor precio” si faltan comparables válidos.

## 4. Resiliencia, seguridad e IaC — 5 min

> La infraestructura está declarada en SAM/CloudFormation. El stack crea roles de mínimo privilegio, bucket privado cifrado, DynamoDB on-demand, SQS cifrado, DLQ y trazabilidad X-Ray.

- Reintentos exponenciales: 3 intentos de extracción antes de enviar a SQS.
- Secretos: refresh token de Google únicamente en AWS Secrets Manager; nunca en Git, variables de entorno ni capturas.
- El extractor utiliza timeout, user-agent identificable y validación TLS; no intenta evadir bloqueos, CAPTCHA ni controles de los sitios.
- Para producción cambiaría la autenticación CLI con root por IAM Identity Center o rol con privilegio mínimo.

## 5. Demostración de la ejecución real — 5 min

Mostrar en este orden: Step Functions, S3, DynamoDB, Sheet, log del notificador.

- Corrida: `9b5a1493-28b8-4e60-8cb5-b4644c544228`.
- Estado final: `SUCCEEDED`.
- S3: tres JSON, uno por fuente.
- Observación verificable: **Gel Limpiador CeraVe Espumoso Piel Mixta a Grasa 236 ml**, Dermashop, **S/55.92**, stock **agotado**.
- Las fuentes Flora y Fauna e Inkafarma no devolvieron una coincidencia validable para ese producto; agotaron reintentos, se publicaron dos eventos de fallo y el notificador los procesó correctamente.

Frase clave:

> Prefiero declarar un dato no comparable antes que presentar un precio inferido como si fuera evidencia comercial.

## 6. Pruebas y corrección encontrada — 3 min

> Ejecuté pruebas unitarias para JSON-LD, formato decimal peruano y la tarjeta HTML de Dermashop. El preflight también genera el paquete Linux, valida el template CloudFormation y confirma identidad AWS.

- Mencionar que durante la prueba se encontró un defecto de empaquetado: el `CodeUri` global no generaba un ZIP Lambda válido para las funciones.
- Se corrigió declarando `CodeUri` explícitamente en cada función, se redesplegó y se ejecutó nuevamente el pipeline con éxito.
- Esto demuestra diagnóstico, no ocultamiento de errores.

## 7. Trade-offs y siguientes mejoras — 3 min

- Implementar extractores por tienda más robustos y contract tests de HTML/JSON para detectar cambios de catálogo.
- Añadir cola de agregación para un correo consolidado por corrida cuando el volumen crezca.
- Añadir métricas/alertas de fuentes sin coincidencia, tasa de error y duración de corrida.
- Para una cobertura comercial completa, acordar un catálogo canónico y reglas de equivalencia SKU/EAN con la Gerencia Comercial.

## Preguntas que es probable que hagan

**¿Por qué Gmail y no SES?**

En una cuenta AWS nueva, SES suele estar en sandbox y no garantiza enviar inmediatamente a un destinatario externo no verificado. Gmail API, con OAuth del propietario y `gmail.send`, permite cumplir la notificación solicitada; el refresh token está cifrado en Secrets Manager.

**¿Por qué DynamoDB y S3?**

DynamoDB da consultas simples y económicas por corrida para el reporte. S3 preserva la evidencia de extracción para auditoría y troubleshooting. Separa la lectura operacional de la evidencia cruda.

**¿Por qué no usar Lambda para toda la orquestación?**

Step Functions hace visibles los reintentos, los fallos por tienda y el paso de reporte. Reduce lógica de control manual en código y mejora la operación.

**¿Cómo evitas declarar un menor precio incorrecto?**

Comparo solo elementos con el mismo `productKey` y estado disponible. Si el producto no es equivalente o no está disponible, se conserva el registro pero no se usa para la alerta.
