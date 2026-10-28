"""Upload only validated forward bytes using a dedicated bucket-scoped S3 key.

Invoked by stage_forward_snapshot after both validators, under its lock/deadline.
Never takes credentials on the command line or uses ambient AWS credentials.
"""

import hashlib
import os
import re
import sys
from pathlib import Path

BUCKET = "backtest-badger-forward"
KEY = "forward-v1.json"
CACHE_CONTROL = "public, max-age=60, must-revalidate"
MAX_BYTES = 64 * 1024


def client():
    import boto3
    from botocore.config import Config

    account = os.environ["R2_ACCOUNT_ID"]
    if not re.fullmatch(r"[a-f0-9]{32}", account):
        raise ValueError("Invalid R2 account identity.")
    return boto3.client(
        "s3",
        endpoint_url=f"https://{account}.r2.cloudflarestorage.com",
        region_name="auto",
        aws_access_key_id=os.environ["R2_ACCESS_KEY_ID"],
        aws_secret_access_key=os.environ["R2_SECRET_ACCESS_KEY"],
        config=Config(
            signature_version="s3v4",
            connect_timeout=5,
            read_timeout=10,
            retries={"total_max_attempts": 1},
            s3={"addressing_style": "path"},
            request_checksum_calculation="when_required",
            response_checksum_validation="when_required",
        ),
    )


def publish(path, s3):
    body = path.read_bytes()
    if not 0 < len(body) <= MAX_BYTES:
        raise ValueError("Invalid snapshot size.")
    s3.put_object(
        Bucket=BUCKET,
        Key=KEY,
        Body=body,
        ContentType="application/json",
        CacheControl=CACHE_CONTROL,
        StorageClass="STANDARD",
    )
    # Verify object storage acknowledgement with exact bytes before advancing
    # private last-success. Public HTTPS/CORS is checked independently.
    response = s3.get_object(Bucket=BUCKET, Key=KEY)
    with response["Body"] as stream:
        stored = stream.read(MAX_BYTES + 1)
    if (
        stored != body
        or response["ContentType"] != "application/json"
        or response["CacheControl"] != CACHE_CONTROL
    ):
        raise ValueError("R2 readback mismatch.")
    return hashlib.sha256(body).hexdigest()


def main():
    try:
        if len(sys.argv) != 2:
            raise ValueError("Expected one validated candidate.")
        digest = publish(Path(sys.argv[1]), client())
    except Exception:
        # SDK exceptions can include request/credential details. Journal only a
        # fixed failure category; parent preserves the previous private snapshot.
        sys.exit("R2 publication/readback failed; remote acknowledgement uncertain.")
    print(f"R2 object bytes verified sha256={digest}")


if __name__ == "__main__":
    main()
