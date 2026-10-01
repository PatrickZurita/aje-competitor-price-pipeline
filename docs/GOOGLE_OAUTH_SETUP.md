# Configuración de Google OAuth

Este paso permite dos requerimientos reales: crear el Google Sheet en Drive y enviar una alerta a `oscar.toledo@ajegroup.com` desde la cuenta Google de Patrick. No requiere ninguna credencial de AJE.

## Preparación única

1. En Google Cloud Console, crear o seleccionar un proyecto propio.
2. Habilitar Google Drive API, Google Sheets API y Gmail API.
3. Configurar la pantalla de consentimiento OAuth como **External** y agregar la cuenta Google de Patrick como usuario de prueba, si el proyecto permanece en modo Testing.
4. Crear una credencial OAuth de tipo **Desktop app** y descargarla como `credentials.json`.
5. Guardar el archivo solo en `local-secrets/credentials.json`. Esa ruta está ignorada por Git.
6. Ejecutar el script local de autorización. Se abrirá el navegador para consentir los tres permisos.

```bash
mkdir -p local-secrets
./.venv/bin/python scripts/authorize_google.py \
  --client-secrets local-secrets/credentials.json \
  --output local-secrets/google-oauth.json
```

El resultado contiene un refresh token. No debe copiarse en el README, Git, chat ni capturas.

## Carga segura a AWS

Después de iniciar sesión con `aws login --profile aje-test`, crear el secreto desde el archivo local:

```bash
aws secretsmanager create-secret \
  --name aje-competitor-prices/google-oauth \
  --secret-string file://local-secrets/google-oauth.json \
  --profile aje-test --region sa-east-1
```

Copiar solamente el ARN que devuelve el comando para el parámetro `GoogleOAuthSecretArn` del despliegue.

## Verificación

La primera corrida debe crear o reutilizar las carpetas `YYYY/MM` en el Drive configurado, crear el spreadsheet y, al provocar un fallo controlado, mandar el correo desde la cuenta autorizada a Oscar.
