#!/usr/bin/env /usr/bin/python3
"""
upload_images.py — resize photos and upload to Cloudflare R2 for sailingoroboro.com

Usage:
    /usr/bin/python3 upload_images.py <source_folder> <r2_prefix> [--dry-run]

    source_folder  directory of JPEG/HEIC/PNG photos to upload
    r2_prefix      R2 key prefix, e.g. "azores"  → stored as azores/filename.jpg
    --dry-run      resize only, do not upload; prints what would be uploaded

Examples:
    /usr/bin/python3 upload_images.py ~/Desktop/azores-picks azores
    /usr/bin/python3 upload_images.py ~/Desktop/azores-picks azores --dry-run

Each photo is:
  1. Resized to max 1600px on the long edge, JPEG quality 85 (Pillow)
  2. Uploaded to the R2 bucket under <r2_prefix>/<filename>.jpg
  3. Printed as a ready-to-paste markdown image tag with R2 public URL

Environment variables required (never commit these):
    R2_ACCOUNT_ID         — found in Cloudflare dashboard → R2 → Overview
    R2_ACCESS_KEY_ID      — R2 API token "Access Key ID"
    R2_SECRET_ACCESS_KEY  — R2 API token "Secret Access Key"

To create an R2 API token:
  Cloudflare dashboard → R2 → Manage R2 API Tokens → Create API Token
  Permissions: Object Read & Write
  Copy the Access Key ID and Secret Access Key — they are shown only once.
  Store them in your shell profile or a .env file (never commit).
"""

import os
import sys
import tempfile
from pathlib import Path

try:
    import boto3
    from botocore.config import Config
except ImportError:
    sys.exit("boto3 not installed. Run: /usr/bin/pip3 install boto3")

try:
    from PIL import Image
    import pillow_heif
    pillow_heif.register_heif_opener()
except ImportError:
    try:
        from PIL import Image
    except ImportError:
        sys.exit("Pillow not installed. Run: /usr/bin/pip3 install Pillow pillow-heif")

R2_BUCKET    = 'oroboro-media'
R2_PUBLIC_BASE = 'https://pub-7f7d07c430fd4c3eb11a4e6eae938ce3.r2.dev/'
MAX_LONG_EDGE  = 1600
JPEG_QUALITY   = 85
SUPPORTED_EXTS = {'.jpg', '.jpeg', '.png', '.heic', '.heif', '.webp', '.tiff', '.tif'}


def resize_to_jpeg(src_path: Path, tmp_dir: Path) -> Path:
    """Resize image to MAX_LONG_EDGE and save as JPEG. Returns path to temp file."""
    with Image.open(src_path) as img:
        img = img.convert('RGB')
        w, h = img.size
        if max(w, h) > MAX_LONG_EDGE:
            scale = MAX_LONG_EDGE / max(w, h)
            img = img.resize((int(w * scale), int(h * scale)), Image.LANCZOS)
        out_name = src_path.stem.lower().replace(' ', '-') + '.jpg'
        out_path = tmp_dir / out_name
        img.save(out_path, 'JPEG', quality=JPEG_QUALITY, optimize=True)
    return out_path


def get_r2_client():
    account_id = os.environ.get('R2_ACCOUNT_ID', '').strip()
    access_key = os.environ.get('R2_ACCESS_KEY_ID', '').strip()
    secret_key = os.environ.get('R2_SECRET_ACCESS_KEY', '').strip()
    if not all([account_id, access_key, secret_key]):
        sys.exit(
            "Missing R2 credentials. Set environment variables:\n"
            "  export R2_ACCOUNT_ID=...\n"
            "  export R2_ACCESS_KEY_ID=...\n"
            "  export R2_SECRET_ACCESS_KEY=..."
        )
    endpoint = f'https://{account_id}.r2.cloudflarestorage.com'
    return boto3.client(
        's3',
        endpoint_url=endpoint,
        aws_access_key_id=access_key,
        aws_secret_access_key=secret_key,
        config=Config(signature_version='s3v4'),
        region_name='auto',
    )


def main():
    args = sys.argv[1:]
    dry_run = '--dry-run' in args
    args = [a for a in args if a != '--dry-run']

    if len(args) < 2:
        print(__doc__)
        sys.exit(1)

    source_dir = Path(args[0]).expanduser()
    prefix     = args[1].strip('/')

    if not source_dir.is_dir():
        sys.exit(f"Source folder not found: {source_dir}")

    photos = sorted(
        p for p in source_dir.iterdir()
        if p.suffix.lower() in SUPPORTED_EXTS and not p.name.startswith('.')
    )
    if not photos:
        sys.exit(f"No supported image files found in {source_dir}")

    print(f"Found {len(photos)} photos in {source_dir}")
    print(f"Prefix : {prefix}/")
    print(f"Dry run: {dry_run}\n")

    r2 = None if dry_run else get_r2_client()

    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)
        results = []
        for photo in photos:
            print(f"  {photo.name} → ", end='', flush=True)
            try:
                resized = resize_to_jpeg(photo, tmp_path)
                size_kb = resized.stat().st_size // 1024
                key = f"{prefix}/{resized.name}"
                public_url = R2_PUBLIC_BASE + key

                if not dry_run:
                    r2.upload_file(
                        str(resized), R2_BUCKET, key,
                        ExtraArgs={'ContentType': 'image/jpeg'}
                    )
                    print(f"{resized.name} ({size_kb} KB) → uploaded")
                else:
                    print(f"{resized.name} ({size_kb} KB) → [dry run, not uploaded]")

                results.append((photo.name, resized.name, public_url))
            except Exception as e:
                print(f"ERROR: {e}")

    print(f"\n── Markdown snippets ({'dry run — URLs are final but files not uploaded' if dry_run else 'ready to paste'}) ──")
    for orig, resized_name, url in results:
        print(f"![caption]({prefix}/{resized_name})")

    print(f"\n── Full img tags ──")
    for orig, resized_name, url in results:
        print(f'<img src="{url}" alt="">')

    print(f"\nDone. {len(results)}/{len(photos)} processed.")


if __name__ == '__main__':
    main()
