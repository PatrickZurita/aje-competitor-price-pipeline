from __future__ import annotations

import base64
import json
import logging
import uuid
from datetime import UTC, datetime
from decimal import Decimal
from email.message import EmailMessage
from typing import Any

from boto3.dynamodb.conditions import Key
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

from aws_clients import observations_table, s3_client, secrets_client, stepfunctions_client
from config import GOOGLE_SCOPES, TARGET_SITES, load_product_targets, required_env
from domain import AVAILABLE_STOCK, ProductTarget
from extractors import ExtractionError, fetch_html, find_observation

logger = logging.getLogger()
logger.setLevel(logging.INFO)


def json_default(value: Any) -> str:
    if isinstance(value, Decimal):
        return str(value)
    raise TypeError(f"Unsupported JSON value: {type(value)!r}")


def oauth_credentials() -> Credentials:
    secret = secrets_client.get_secret_value(SecretId=required_env("GOOGLE_OAUTH_SECRET_ARN"))
    payload = json.loads(secret["SecretString"])
    return Credentials.from_authorized_user_info(payload, GOOGLE_SCOPES)


def dispatcher(event: dict[str, Any], context: Any) -> dict[str, str]:
    run_id = str(uuid.uuid4())
    payload = {
        "runId": run_id,
        "startedAt": datetime.now(UTC).isoformat(),
        "targets": [
            {**site, "products": [target.__dict__ for target in load_product_targets()]}
            for site in TARGET_SITES
        ],
    }
    response = stepfunctions_client.start_execution(
        stateMachineArn=required_env("STATE_MACHINE_ARN"),
        input=json.dumps(payload),
        name=run_id,
    )
    logger.info("Started pipeline runId=%s executionArn=%s", run_id, response["executionArn"])
    return {"runId": run_id, "executionArn": response["executionArn"]}


def scraper(event: dict[str, Any], context: Any) -> dict[str, Any]:
    run_id = event["runId"]
    target_site = event["target"]
    store = target_site["store"]
    html = fetch_html(target_site["url"])
    observations = []
    failures = []

    for product in target_site["products"]:
        try:
            observation = find_observation(
                run_id=run_id,
                store=store,
                source_url=target_site["url"],
                html=html,
                target=ProductTarget(
                    product_key=product["product_key"],
                    display_name=product["display_name"],
                    match_terms=tuple(product["match_terms"]),
                ),
            )
            observations.append(observation)
        except ExtractionError as error:
            failures.append({"productKey": product["product_key"], "error": str(error)})

    raw_key = f"raw/{run_id}/{store.lower().replace(' ', '-')}.json"
    s3_client.put_object(
        Bucket=required_env("RAW_BUCKET_NAME"),
        Key=raw_key,
        Body=json.dumps(
            {
                "runId": run_id,
                "store": store,
                "sourceUrl": target_site["url"],
                "observations": [observation.__dict__ for observation in observations],
                "failures": failures,
            },
            default=json_default,
        ).encode("utf-8"),
        ContentType="application/json",
        ServerSideEncryption="AES256",
    )

    table = observations_table(required_env("OBSERVATIONS_TABLE_NAME"))
    for observation in observations:
        table.put_item(
            Item={
                "PK": f"RUN#{observation.run_id}",
                "SK": f"OBS#{observation.product_key}#{observation.store}",
                "entityType": "PriceObservation",
                "store": observation.store,
                "productKey": observation.product_key,
                "productName": observation.product_name,
                "pricePen": observation.price_pen,
                "stock": observation.stock,
                "productUrl": observation.product_url,
                "extractedAt": observation.extracted_at,
                "rawKey": raw_key,
            }
        )

    if not observations:
        raise ExtractionError(f"No observations extracted for {store}: {failures}")
    logger.info("Extracted store=%s runId=%s observations=%s", store, run_id, len(observations))
    return {"runId": run_id, "store": store, "observations": len(observations), "rawKey": raw_key}


def drive_folder_id(drive: Any, parent_id: str, name: str) -> str:
    query = (
        f"name = '{name}' and mimeType = 'application/vnd.google-apps.folder' "
        f"and '{parent_id}' in parents and trashed = false"
    )
    result = drive.files().list(q=query, fields="files(id, name)").execute()
    if result.get("files"):
        return result["files"][0]["id"]
    created = drive.files().create(
        body={"name": name, "mimeType": "application/vnd.google-apps.folder", "parents": [parent_id]},
        fields="id",
    ).execute()
    return created["id"]


def report(event: dict[str, Any], context: Any) -> dict[str, str]:
    run_id = event["runId"]
    table = observations_table(required_env("OBSERVATIONS_TABLE_NAME"))
    observations = []
    query = table.query(KeyConditionExpression=Key("PK").eq(f"RUN#{run_id}"))
    observations.extend(query.get("Items", []))
    while "LastEvaluatedKey" in query:
        query = table.query(
            KeyConditionExpression=Key("PK").eq(f"RUN#{run_id}"),
            ExclusiveStartKey=query["LastEvaluatedKey"],
        )
        observations.extend(query.get("Items", []))
    if not observations:
        raise RuntimeError(f"No observations available for run {run_id}")

    lowest_by_product: dict[str, Decimal] = {}
    for item in observations:
        if item["stock"].lower() not in AVAILABLE_STOCK:
            continue
        price = item["pricePen"]
        current = lowest_by_product.get(item["productKey"])
        if current is None or price < current:
            lowest_by_product[item["productKey"]] = price

    rows = [["Producto / Categoría", "Tienda", "Precio (PEN)", "Stock", "URL del producto", "Menor precio alerta"]]
    for item in sorted(observations, key=lambda value: (value["productKey"], value["pricePen"])):
        alert = "MEJOR PRECIO" if item["pricePen"] == lowest_by_product.get(item["productKey"]) else "-"
        rows.append([
            item["productName"],
            item["store"],
            str(item["pricePen"]),
            item["stock"],
            item["productUrl"],
            alert,
        ])

    credentials = oauth_credentials()
    drive = build("drive", "v3", credentials=credentials, cache_discovery=False)
    sheets = build("sheets", "v4", credentials=credentials, cache_discovery=False)
    now = datetime.now(UTC)
    root_folder = required_env("GOOGLE_DRIVE_ROOT_FOLDER_ID")
    year_folder = drive_folder_id(drive, root_folder, now.strftime("%Y"))
    month_folder = drive_folder_id(drive, year_folder, now.strftime("%m"))
    title = now.strftime("Precios_Comparativos_%Y_%m_%d")
    spreadsheet = sheets.spreadsheets().create(body={"properties": {"title": title}}, fields="spreadsheetId,spreadsheetUrl").execute()
    spreadsheet_id = spreadsheet["spreadsheetId"]
    sheets.spreadsheets().values().update(
        spreadsheetId=spreadsheet_id,
        range="A1",
        valueInputOption="USER_ENTERED",
        body={"values": rows},
    ).execute()
    existing = drive.files().get(fileId=spreadsheet_id, fields="parents").execute()
    drive.files().update(
        fileId=spreadsheet_id,
        addParents=month_folder,
        removeParents=",".join(existing.get("parents", [])),
        fields="id, webViewLink",
    ).execute()
    logger.info("Generated report runId=%s spreadsheetId=%s", run_id, spreadsheet_id)
    return {"runId": run_id, "spreadsheetUrl": spreadsheet["spreadsheetUrl"]}


def notifier(event: dict[str, Any], context: Any) -> dict[str, int]:
    credentials = oauth_credentials()
    gmail = build("gmail", "v1", credentials=credentials, cache_discovery=False)
    sent = 0
    for record in event["Records"]:
        payload = json.loads(record["body"])
        message = EmailMessage()
        message["To"] = required_env("NOTIFICATION_RECIPIENT")
        message["Subject"] = f"[AJE] Fallo en monitoreo de precios - corrida {payload.get('runId', 'desconocida')}"
        message.set_content(json.dumps(payload, indent=2, ensure_ascii=False, default=json_default))
        encoded = base64.urlsafe_b64encode(message.as_bytes()).decode("utf-8")
        gmail.users().messages().send(userId="me", body={"raw": encoded}).execute()
        sent += 1
    logger.info("Sent failure notifications=%s", sent)
    return {"sent": sent}
