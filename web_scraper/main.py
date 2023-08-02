import argparse, os
from concurrent.futures import ThreadPoolExecutor, wait
from time import time
from tqdm import tqdm
from scraper import connect_to_url, get_driver, get_text_to_save, write_to_file, get_filename, BASE_DIR


def run_process(url, headless):
    filename = get_filename(url)
    if os.path.isfile(filename):
        return

    browser = get_driver(headless)
    try:
        if connect_to_url(browser, url):
            html = browser.page_source
            text = get_text_to_save(url, html)
            if len(text) != 0:
                write_to_file(filename, text)
        else:
            pass
            # print("Error connecting to Wikipedia")
    finally:
        browser.close()
        browser.quit()


def init_argparse() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    parser.add_argument("-e", "--headless", dest="headless", help="headless?", default=False, action='store_true')
    parser.add_argument("-c", "--concurrent", dest="concurrent", help="concurrent?", default=False, action='store_true')
    parser.add_argument("-u", "--urlfilename", dest="urlfilename", help="url filename")
    parser.add_argument("-s", "--skip", dest="skip", default=0)
    return parser


def reorder_urls_file(urlfilename, urls):
    from pathlib import Path
    hashed_filenames = [os.path.basename(get_filename(url)) for url in urls]
    existing_files = set(os.listdir(Path(BASE_DIR).joinpath("output")))
    urls_and_hashes = list(zip(urls, hashed_filenames))
    urls_and_hashes.sort(key=lambda x: int(x[1] in existing_files), reverse=True)
    urls = [x[0] for x in urls_and_hashes]
    with open(urlfilename, 'w') as fout:
        fout.write("\n".join(urls))


if __name__ == "__main__":
    parser = init_argparse()
    args = parser.parse_args()
    skip = int(args.skip)
    print("SKIP", skip)
    # set variables
    start_time = time()
    with open(args.urlfilename, 'r') as fin:
        urls = [url.strip() for url in fin]
        urls_to_scrape = urls[skip:]
    print("URLs to scraper", len(urls_to_scrape))
    if args.concurrent:
        print("fast mode")
        # scrape and crawl
        with ThreadPoolExecutor(15) as executor:
            _ = [executor.submit(run_process, url, args.headless) for url in urls_to_scrape]
            #wait(futures)
    else:
        print("slow mode")
        for url in tqdm(urls_to_scrape):
            run_process(url, args.headless)
    reorder_urls_file(args.urlfilename, urls)
    end_time = time()
    elapsed_time = end_time - start_time
    print(f"Elapsed run time: {elapsed_time} seconds")
