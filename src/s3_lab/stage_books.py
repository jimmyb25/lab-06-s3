#!/usr/bin/env python3
"""Store a corpus of books in a public S3 bucket"""
import logging
import os

import boto3
from botocore.exceptions import ClientError

logging.basicConfig(level=logging.INFO, format="%(message)s")
log = logging.getLogger(__name__)

s3 = boto3.client("s3", region_name="us-east-1")

# practice-<USER>: bucket names must be globally unique across all of AWS
#bucket_name = f"practice-{os.environ.get('USER', 'unknown')}"
#log.info(f"{bucket_name}")

def parse_args():
    if len(sys.argv) != 4:
        log.info("Type it like this: python stage_books.py <list_file> <index_path> <bucket>")
        sys.exit(1)
    arg_tuple = (sys.argv[1], sys.argv[2], sys.argv[3])
    return arg_tuple

def download_books(list_file, dest_dir):
    print(1+1)




try:
    # us-east-1: omit LocationConstraint or create_bucket fails
    s3.create_bucket(Bucket=bucket_name)
    log.info(f"Created bucket: {bucket_name}")
except ClientError as e:
    log.error(f"Error creating bucket {bucket_name}: {e}")