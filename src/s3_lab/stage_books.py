#!/usr/bin/env python3
"""Store a corpus of books in a public S3 bucket"""
import logging
import os
import sys
import requests
import time
import boto3
import json
from botocore.exceptions import ClientError

logging.basicConfig(level=logging.INFO, format="%(message)s")
log = logging.getLogger(__name__)

s3 = boto3.client("s3", region_name="us-east-1")

# begin defining functions

def parse_args():
    """Parses the arguments from the command line, turning them into a tuple, and rejecting them if they aren't given correctly"""
    log.info('Parsing command line arguments')

    #check if we got the right number of arguments
    if len(sys.argv) != 4:
        log.info("Type it like this: python stage_books.py <list_file> <index_path> <bucket>")
        sys.exit(1)

    #load the arguments to a tuple, return it
    arg_tuple = (sys.argv[1], sys.argv[2], sys.argv[3])
    log.info('Found command line arguments')
    return arg_tuple

def download_books(list_file, dest_dir):
    """Returns a list of the local paths of books to be passed into upload_files"""
    log.info(f'Downloading books to {dest_dir}')
    os.makedirs(dest_dir, exist_ok=True)
    url_list = [line.strip() for line in open(list_file) if line.strip()]

    paths = []
    #loop through all urls, downloading them
    for url in url_list:
        filename = url.rstrip('/').split('/')[-1]
        path = os.path.join(dest_dir, filename)

        #check if the path already exists, skipping if it does
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

    log.info("Download process completed.")
    return paths

def create_bucket(bucket):
    """Tries to create a bucket, returning true if successful, false if failed"""
    #check if the bucket already exists
    try:
        s3.head_bucket(Bucket=bucket)
        log.info(f"Bucket {bucket} already exists")
        return True
    except ClientError:
        log.info(f"Bucket {bucket} not found, creating it")

    #create the bucket now that it's verified it doesn't yet exist
    try:
        # us-east-1: omit LocationConstraint or create_bucket fails
        s3.create_bucket(Bucket=bucket)
        log.info(f"Created bucket: {bucket}")
        return True
    except ClientError as e:
        log.error(f"Error creating bucket {bucket}: {e}")
        return False

def make_public(bucket):
    """Makes the inputted bucket public on AWS"""

    # turn off the Block Public Access within try/except block
    try:
        s3.put_public_access_block(
            Bucket = bucket,
            PublicAccessBlockConfiguration={
                "BlockPublicAcls": False,
                "IgnorePublicAcls": False,
                "BlockPublicPolicy": False,
                "RestrictPublicBuckets": False,
            },
        )
        log.info(f"Turned off Blocking Public Access for bucket {bucket}")
    except ClientError as e:
        log.error(f"Error turning of Block Public Access for bucket {bucket}: {e}")
        return False

    # create the bucket policy letting anyone read the objects
    policy = {
        "Version": "2026-10-19",
        "Statement": [
            {
                "Effect": "Allow",
                "Principal": "*",
                "Action": "s3:GetObject",
                "Resource": f"arn:aws:s3:::{bucket}/*"
            }
        ]
    }

    # actually attach the bucket policy, within a try/except block
    try:
        s3.put_bucket_policy(Bucket=bucket, Policy = json.dumps(policy))
        log.info(f"Successfully attached public read policy to {bucket}")
        return True
    except ClientError as e:
        log.error(f"Error attaching policy to {bucket}: {e}")
        return False

def upload_files(bucket, file_paths):
    """Upload each file listed in file_paths to the bucket, then return the number successfully uploaded"""
    log.info(f"Uploading {len(file_paths)} files to {bucket}")
    uploaded = 0

    # loop through all paths, uploading each one with its file name as the key
    for path in file_paths:
        key = os.path.basename(path)  # e.g. pg1342.txt, not books/pg1342.txt
        try:
            s3.upload_file(
                path,
                bucket,
                key,
                ExtraArgs={"ContentType": "text/plain; charset=utf-8"},
            )
            log.info(f"Uploaded {path} to s3://{bucket}/{key}")
            uploaded += 1
        except (ClientError, boto3.exceptions.S3UploadFailedError) as e:
            log.error(f"Error uploading {path} to {bucket}: {e}")

    log.info(f"Upload process completed: {uploaded} of {len(file_paths)} files uploaded")
    return uploaded


def upload_index(bucket, index_path):
    """Uploads the index page to the bucket as an html file called index.html, returning true if successful"""
    log.info(f"Uploading index page {index_path} to {bucket}")
    key = "index.html"

    # open the local file and upload it, catching a missing file separately
    try:
        with open(index_path, "rb") as f:
            s3.put_object(
                Bucket=bucket,
                Key=key,
                Body=f,
                ContentType="text/html",  # so browsers display it as a web page
            )
        log.info(f"Uploaded {index_path} to s3://{bucket}/{key}")
        return True
    except FileNotFoundError:
        log.error(f"Local file not found: {index_path}")
        return False
    except ClientError as e:
        log.error(f"Error uploading {index_path} to {bucket}: {e}")
        return False


def main():
    """run all of the functions in order, exiting if anything fails"""
    arguments = parse_args()
    
    book_list = download_books(arguments[0],"books")
    if not book_list:
        log.error("No books were downloaded, stopping")
        sys.exit(1)

    if not create_bucket(bucket):
        log.error(f"Could not create bucket {bucket}, stopping")
        sys.exit(1)

    uploaded = upload_files(bucket, file_paths)
    index_ok = upload_index(bucket, index_path)

    url = f"https://{bucket}.s3.amazonaws.com/index.html"
    if uploaded == len(file_paths) and index_ok:
        log.info(f"Success: uploaded {uploaded} books and the index page to {bucket}")
    else:
        log.error(f"Finished with errors: uploaded {uploaded} of {len(file_paths)} books, index page uploaded: {index_ok}")
    log.info(f"Index page: {url}")


if __name__ == "__main__":
    main()