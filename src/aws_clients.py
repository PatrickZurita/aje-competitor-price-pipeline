from __future__ import annotations

import boto3
from botocore.config import Config

AWS_CONFIG = Config(
    retries={"total_max_attempts": 2, "mode": "standard"},
    connect_timeout=5,
    read_timeout=15,
)

s3_client = boto3.client("s3", config=AWS_CONFIG)
secrets_client = boto3.client("secretsmanager", config=AWS_CONFIG)
stepfunctions_client = boto3.client("stepfunctions", config=AWS_CONFIG)


def observations_table(table_name: str):
    return boto3.resource("dynamodb", config=AWS_CONFIG).Table(table_name)
