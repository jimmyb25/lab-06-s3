#!/usr/bin/env python3
"""Store a corpus of books in a public S3 bucket"""
import logging
import os
import sys
import requests
import time
import boto3
from botocore.exceptions import ClientError

logging.basicConfig(level=logging.INFO, format="%(message)s")
log = logging.getLogger(__name__)

s3 = boto3.client("s3", region_name="us-east-1")

# practice-<USER>: bucket names must be globally unique across all of AWS
#bucket_name = f"practice-{os.environ.get('USER', 'unknown')}"
#log.info(f"{bucket_name}")

def parse_args():
    """Parses the arguments from the command line, turning them into a tuple, and rejecting them if they aren't given correctly"""
    log.info('Parsing command line arguments')
    if len(sys.argv) != 4:
        log.info("Type it like this: python stage_books.py <list_file> <index_path> <bucket>")
        sys.exit(1)
    arg_tuple = (sys.argv[1], sys.argv[2], sys.argv[3])
    log.info('Found command line arguments')
    return arg_tuple

def download_books(list_file, dest_dir):
    """Returns a list of the local paths of books to be passed into upload_files"""
    log.info(f'Downloading books to {dest_dir}')
    os.makedirs(dest_dir, exist_ok=True)
    url_list = [line.strip() for line in open(list_file) if line.strip()]

    paths = []
    for url in url_list:
        filename = url.rstrip('/').split('/')[-1]
        path = os.path.join(dest_dir, filename)

        if os.path.exists(path):
            log.info(f'Already downloaded {path}, skipping')
            paths.append(path)
            continue

        try:
            response = requests.get(url, timeout=30)
            response.raise_for_status()
            open(path, "wb").write(response.content)
            log.info(f"Downloaded {url} to {path}")
            paths.append(path)
        except requests.RequestException as e:
            log.error(f'Error on {url}: {e}')

        time.sleep(1) # keep request speed low

    return paths
#try:
#    # us-east-1: omit LocationConstraint or create_bucket fails
#    s3.create_bucket(Bucket=bucket_name)
#    log.info(f"Created bucket: {bucket_name}")
#except ClientError as e:
#    log.error(f"Error creating bucket {bucket_name}: {e}")