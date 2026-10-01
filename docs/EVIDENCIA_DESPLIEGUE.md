# Guion de evidencia de despliegue

Guardar las capturas con fecha y `runId` visible dentro de `docs/evidencia/`. No incluir secretos OAuth ni tokens.

1. **CloudFormation:** stack `CREATE_COMPLETE` y pestaña Resources.
2. **Step Functions:** ejecución con los estados ExtractAllStores y GenerateReport; mostrar el `runId`.
3. **S3:** objeto `raw/<runId>/<tienda>.json` y su contenido normalizado, sin credenciales.
4. **DynamoDB:** ítems con `PK = RUN#<runId>` y precio como decimal.
5. **Google Drive/Sheets:** carpetas `YYYY/MM`, archivo `Precios_Comparativos_YYYY_MM_DD` y matriz con columnas solicitadas.
6. **SQS:** provocar una fuente inexistente o un producto sin coincidencia, mostrar mensaje en FailureQueue antes de que Lambda lo procese o el log de procesamiento.
7. **Correo:** mostrar asunto, destinatario `oscar.toledo@ajegroup.com` y `runId`; ocultar cualquier dato sensible.
8. **Costeo:** adjuntar captura/PDF de AWS Pricing Calculator con la región seleccionada.

## Ejecución verificada — 2026-10-01

| Evidencia | Resultado verificable |
| --- | --- |
| Stack | `aje-competitor-prices` actualizado correctamente en `sa-east-1`. |
| Ejecución Step Functions | `9b5a1493-28b8-4e60-8cb5-b4644c544228`, estado `SUCCEEDED`. |
| Objetos S3 | `raw/9b5a1493-28b8-4e60-8cb5-b4644c544228/{flora-y-fauna,dermashop,inkafarma}.json`. |
| DynamoDB | Una observación verificable: **Gel Limpiador CeraVe Espumoso Piel Mixta a Grasa 236 ml**, Dermashop, S/55.92, estado `agotado`. |
| Reporte | [Precios_Comparativos_2026_10_01](https://docs.google.com/spreadsheets/d/1xcgJq4lliF2xuYXbohrU2c4KIrpJAw90ORoXySEyJK0/edit), creado y guardado en Drive. |
| Resiliencia | Flora y Fauna e Inkafarma no tuvieron coincidencia verificable con el producto objetivo; Step Functions agotó los reintentos, SQS entregó los eventos y Notifier Lambda registró dos envíos exitosos. |
| DLQ | Sin mensajes pendientes luego del procesamiento. |

Las capturas finales deben mostrar la fecha y este `runId`, sin revelar tokens OAuth ni valores de secretos.
