import argparse, re, os
from concurrent.futures import ThreadPoolExecutor, wait
from time import sleep, time
from tqdm import tqdm
from scraper import connect_to_url, get_driver, get_text_to_save, parse_html, write_to_file, get_filename


def run_process(url, headless):
    if os.path.isfile(get_filename(url)):
        return

    browser = get_driver(headless)

    if connect_to_url(browser, url):
        html = browser.page_source
        text = get_text_to_save(url, html)
        write_to_file(url, text)
    else:
        pass
        # print("Error connecting to Wikipedia")
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
    if args.concurrent:
        print("fast mode")
        futures = []

        # scrape and crawl
        with ThreadPoolExecutor() as executor:
            with open(args.urlfilename, 'r') as fin:
                for url in fin:
                    url = url.strip()
                    futures.append(
                        executor.submit(run_process, url, args.headless)
                    )
        wait(futures)
    else:
        print("slow mode")
        with open(args.urlfilename, 'r') as fin:
            for url in tqdm(list(fin)):
                url = url.strip()
                run_process(url, args.headless)
    end_time = time()
    elapsed_time = end_time - start_time
    print(f"Elapsed run time: {elapsed_time} seconds")
