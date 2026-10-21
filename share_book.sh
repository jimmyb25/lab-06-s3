#!/bin/bash
set -euo pipefail

#check that all three arguments were given
if [ "$#" -ne 3 ]; then
    echo "Usage: $0 <book_url> <bucket> <expiration_seconds>" >&2
    echo "Example: $0 https://www.gutenberg.org/cache/epub/1342/pg1342.txt secret-tfs8zb 604800" >&2
    exit 1
fi

#grab the actual arguments
URL="$1"
BUCKET="$2"
EXPIRES="$3"

#download book with curl into books/ folder, keeping filename from url
FILE="$(basename "$URL")"
mkdir -p books #handles for the fact that we already have a books folder
curl -fsSL -o "books/$FILE" "$URL"
echo "Downloaded $URL to books/$FILE"

#create bucket with name provided unless already exists
if aws s3 ls "s3://$BUCKET" > /dev/null 2>&1; then
    echo "Bucket $BUCKET already exists"
else
    aws s3 mb "s3://$BUCKET"
fi

#upload the book to be displayed in browser, stay private
aws s3 cp "books/$FILE" "s3://$BUCKET/$FILE" --content-type "text/plain; charset=utf-8"

#presign a url to the book, add expiration, print them
aws s3 presign "s3://$BUCKET/$FILE" --expires-in "$EXPIRES"
