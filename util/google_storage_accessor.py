import argparse
from sefaria.google_storage_manager import GoogleStorageManager


def access_file(mode, local_path, remote_path):
    bucket, blob = GoogleStorageManager.get_bucket_and_filename_from_url(remote_path)
    if mode == "upload":
        GoogleStorageManager.upload_file(local_path, blob, bucket)
    elif mode == "download":
        download = GoogleStorageManager.get_filename(blob, bucket)
        with open(local_path, "wb") as fout:
            fout.write(download.getbuffer())


def get_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('mode', help='can be either "upload" or "download"')
    parser.add_argument('local_path', help="absolute path to file on local machine")
    parser.add_argument('remote_path', help="assumed to be of the form gs://<bucket>/<blob>")
    return parser.parse_args()


if __name__ == '__main__':
    args = get_args()
    access_file(args.mode, args.local_path, args.remote_path)
