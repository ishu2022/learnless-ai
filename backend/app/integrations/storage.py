"""S3-compatible object storage (MinIO locally, AWS S3 later).

boto3 is synchronous, so calls are pushed to a thread to keep the event loop free.
Only the endpoint/credentials change when moving to real S3.
"""

import asyncio
import logging
from functools import lru_cache

import boto3
from botocore.client import Config
from botocore.exceptions import ClientError

from app.core.config import get_settings

logger = logging.getLogger(__name__)


@lru_cache
def get_s3_client():
    s = get_settings()
    return boto3.client(
        "s3",
        endpoint_url=s.s3_endpoint_url,
        aws_access_key_id=s.minio_root_user,
        aws_secret_access_key=s.minio_root_password,
        region_name="us-east-1",
        config=Config(
            signature_version="s3v4",
            s3={"addressing_style": "path"},
            connect_timeout=2,
            read_timeout=2,
            retries={"max_attempts": 0},
        ),
    )


def _bucket_reachable_sync() -> None:
    get_s3_client().head_bucket(Bucket=get_settings().minio_bucket)


async def check_bucket() -> None:
    """Raises if the storage service or the bucket is unreachable."""
    await asyncio.to_thread(_bucket_reachable_sync)


def _ensure_bucket_sync() -> None:
    client = get_s3_client()
    bucket = get_settings().minio_bucket
    try:
        client.head_bucket(Bucket=bucket)
    except ClientError as exc:
        if exc.response.get("Error", {}).get("Code") in ("404", "NoSuchBucket", "NotFound"):
            client.create_bucket(Bucket=bucket)
            logger.info("Created storage bucket '%s'", bucket)
        else:
            raise


async def ensure_bucket() -> None:
    """Create the bucket on startup if missing. Never crashes the app."""
    try:
        await asyncio.to_thread(_ensure_bucket_sync)
    except Exception:
        logger.warning("Could not verify/create storage bucket on startup", exc_info=True)
