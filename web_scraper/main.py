import argparse, os
from concurrent.futures import ThreadPoolExecutor, wait
from time import time
from tqdm import tqdm
from scraper import connect_to_url, get_driver, get_text_to_save, write_to_file, get_filename, BASE_DIR, get_error_text
import requests


def get_text_via_selenium(url, headless):
    browser = get_driver(headless)
    try:
        if connect_to_url(browser, url):
            html = browser.page_source
            return get_text_to_save(url, html)
        else:
            raise Exception("Error connecting to " + url)
    except Exception as e:
        return ""
    finally:
        browser.close()
        browser.quit()


def get_text_via_requests(url):
    try:
        resp = requests.get(url, verify=False)
        html = resp.text
        return get_text_to_save(url, html)
    except Exception as e:
        return ""


def run_process(url, headless, use_selenium):
    filename = get_filename(url)
    if os.path.isfile(filename):
        return

    if use_selenium:
        text = get_text_via_selenium(url, headless)
    else:
        text = get_text_via_requests(url)

    if text and len(text) > 0:
        write_to_file(filename, text)
    else:
        write_to_file(filename, get_error_text(url))



def init_argparse() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    parser.add_argument("-e", "--headless", dest="headless", help="headless?", default=False, action='store_true')
    parser.add_argument("-c", "--concurrent", dest="concurrent", help="concurrent?", default=False, action='store_true')
    parser.add_argument("-u", "--urlfilename", dest="urlfilename", help="url filename")
    parser.add_argument("-s", "--skip", dest="skip", type=int, default=0)
    parser.add_argument("-m", "--max-to-scrape", type=int, default=None)
    parser.add_argument("--skip-existing", default=False, action="store_true")
    parser.add_argument("--use-selenium", default=False, action="store_true")
    return parser


def _get_existing_filenames():
    from pathlib import Path
    return set(os.listdir(Path(BASE_DIR).joinpath("output")))


def _get_hashed_filenames(urls):
    return [os.path.basename(get_filename(url)) for url in urls]


def get_untried_urls(urls):
    existing_filenames = _get_existing_filenames()
    hashes = _get_hashed_filenames(urls)
    urls_and_hashes = list(zip(urls, hashes))
    untried_urls = [url for (url, url_hash) in filter(lambda x: x[1] not in existing_filenames, urls_and_hashes)]
    print("URLS UNTRIED", len(untried_urls))
    return untried_urls


def read_urls_file(urlfilename):
    with open(urlfilename, 'r') as fin:
        return [url.strip() for url in fin]


def reorder_urls_file(urlfilename):
    urls = read_urls_file(urlfilename)
    urls_and_hashes = list(zip(urls, _get_hashed_filenames(urls)))
    existing_filenames = _get_existing_filenames()
    urls_and_hashes.sort(key=lambda x: int(x[1] in existing_filenames), reverse=True)
    urls = [x[0] for x in urls_and_hashes]
    with open(urlfilename, 'w') as fout:
        fout.write("\n".join(urls))


def get_urls_to_scrape(urlfilename, skip_existing, skip, max_to_scrape):
    urls = read_urls_file(urlfilename)
    if skip_existing:
        urls_to_scrape = get_untried_urls(urls)
    else:
        urls_to_scrape = urls[skip:]
    if max_to_scrape:
        urls_to_scrape = urls_to_scrape[:max_to_scrape]
    print("URLs to scrape", len(urls_to_scrape))
    return urls_to_scrape


if __name__ == "__main__":
    parser = init_argparse()
    args = parser.parse_args()
    skip = args.skip
    print("SKIP", skip)
    # set variables
    start_time = time()
    urls_to_scrape = get_urls_to_scrape(args.urlfilename, args.skip_existing, args.skip, args.max_to_scrape)
    if args.concurrent:
        print("fast mode")
        # scrape and crawl
        with ThreadPoolExecutor(10) as executor:
            _ = [executor.submit(run_process, url, args.headless, args.use_selenium) for url in urls_to_scrape]
    else:
        print("slow mode")
        for url in tqdm(urls_to_scrape):
            run_process(url, args.headless, args.use_selenium)
    # reorder_urls_file(args.urlfilename)
    end_time = time()
    elapsed_time = end_time - start_time
    print(f"Elapsed run time: {elapsed_time} seconds")
