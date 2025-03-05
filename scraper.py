import asyncio
from crawl4ai import *
import time
import requests
import json
import pickle

print('running')
async def main():
# await url request
    print('run')
    s = time.time()
    # hosts = get_urls()
    hosts = [
        ("amazon", ["https://www.amazon.com/Hellmanns-Mayonnaise-Condiment-Squeeze-Cage-Free/dp/B091DCC2CH?dib=eyJ2IjoiMSJ9.4ONmHaMWTq1ZHhlXvbCPGauj7swH_JzX45bcACzKBNxV9jmJWPnOyc0b1v46CGHp9OaXikCORs_0qdCVjxScTdiGMAAVSfxlf78w0ngh2q4gGYWEdvjbRBjyZY_8TbhNdZ4In4kBidwii9_p5rxKJZ_sypJe0GRQpdXspjbOIXPZd2qcWWAq4OKMZg4m7MJ34PQRlBGI0bFvyZchtyocDqSwmv7xOJjfYB0Za_dyhRdYt87C8EtQ_JlaOivsyc4j9KzxdBIGlaBSMCy_s7yEpiXp5x3nhX6yIFXUDjXmcHCq4mG-bQyDUoBekapedtjJJbcLYNZGF1nMpLM5JdZN-sGgvoPf2ZaqV9KNsrd6e_jIWDIRPXgeQyPcYwteJ8nV7OWNe0v0tWmEVJ_0LfWg6CoQ0XPDUl963RjRqnij3g5otb394BSUoag1y8En_uGG.fyatwkxFfAD1tAHciWfqTR7MmYkmSQzyWpDvY2JIZOo&dib_tag=se&keywords=mayonnaise&qid=1741154067&sr=8-5"])
    ]
    # convert to 2d list, where each list has urls from different hosts
    url_bursts = []
    hostnames = []
    n_req_per_host = 5
    for hostname, urls in hosts:
        while len(url_bursts) * n_req_per_host < len(urls):
            url_bursts.append([])

        for i, url in enumerate(urls):
            url_bursts[i // n_req_per_host].append(url)
        hostnames.append(hostname)

    htmls = []
    browser_config = BrowserConfig(
        headless=True,
        viewport_width=1920,
        viewport_height=1080,
        browser_type = "firefox"

    )
    async with AsyncWebCrawler(config=browser_config) as crawler:
        for urls in url_bursts:
            # fetch all urls in burst simultaneously
            htmls += await scrape_urls(crawler, urls)
            print(len(htmls))
    
    with open("Skillet.html", 'w') as file:
        file.write(htmls[0])
    # send htmls
    # send_htmls(htmls)

    e = time.time()
    print(f'Time: {e-s}')
    
server_url = 'http://34.232.48.247:5000'
def get_urls():
    get_url = f'{server_url}/getUrls'
    r = requests.get(url = get_url)

    data = r.json()
    hosts = data['urls']

    print(hosts)
    return hosts
def send_htmls(htmls):
    send_url = f'{server_url}/sendhtmls'
    print(send_url)
    html_data = {'htmls': htmls}
    headers = {"Content-Type": "application/json"}
    r = requests.post(url = send_url, data = json.dumps(html_data))
    print(r)



# Function to scrape a list of URLs in sequence
async def scrape_urls(crawler, urls):
    run_config = CrawlerRunConfig(
        verbose=False,
        log_console = True,
        check_robots_txt=False,
        delay_before_return_html=1.0,
        # wait_for_images=True,
        word_count_threshold=1,

        scan_full_page = True,
        magic=False,
        remove_overlay_elements=True,
        screenshot=True,


    )
    results = await crawler.arun_many(urls=urls, config=run_config)
    # You can process the result here (e.g., save to a file or print it)
    for res in results:
        if res.success:
            print(f"{res.url} successfully crawled")
        else:
            print(f"Failed to crawl {res.url}")
    # print(result)
    return [res.html for res in results if res.success]




if __name__ == "__main__":
    asyncio.run(main())
