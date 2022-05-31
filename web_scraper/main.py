import argparse, os
from concurrent.futures import ThreadPoolExecutor, wait
from time import time
from tqdm import tqdm
from scraper import connect_to_url, get_driver, get_text_to_save, write_to_file, get_filename


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
    return parser


if __name__ == "__main__":
    parser = init_argparse()
    args = parser.parse_args()

    # set variables
    start_time = time()
    with open(args.urlfilename, 'r') as fin:
        urls = [url.strip() for url in fin]
    if args.concurrent:
        print("fast mode")
        futures = []

        # scrape and crawl
        with ThreadPoolExecutor(max_workers=50) as executor:
            for url in urls:
                futures.append(
                    executor.submit(run_process, url, args.headless)
                )
        wait(futures)
    else:
        print("slow mode")
        for url in tqdm(urls):
            run_process(url, args.headless)
    end_time = time()
    elapsed_time = end_time - start_time
    print(f"Elapsed run time: {elapsed_time} seconds")
