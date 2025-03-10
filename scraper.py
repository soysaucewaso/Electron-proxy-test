import asyncio
import fake_http_header.data
from crawl4ai import *
import time
import requests
import json
import websockets
import re
import collections
import json_farmer
import link_classifier
import tensorflow as tf

        

server_url = 'wss://k3eheoj7zd.execute-api.us-east-1.amazonaws.com/development'
print('running')
async def main():
# await url request
    print('run')
    s = time.time()
    hosts = await get_urls()
    # with open('jsons/balms.json', 'r') as file:
    #     p_urls = json.load(file)

    # print(len(p_urls))
    # hosts = [
    #     ("amazon", p_urls)
    # ]
    # convert to 2d list, where each list has urls from different hosts
    url_bursts = []
    hostnames = []
    n_req_per_host = 5
    for hostname, urls in hosts:
        print(hostname)
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
        browser_type = "chromium",
        text_mode = True,
    )
    async with AsyncWebCrawler(config=browser_config) as crawler:
        for urls in url_bursts:
            # fetch all urls in burst simultaneously
            htmls += (await scrape_urls(crawler, urls))
            print(len(htmls))
    
    new_urls = set()
    jsons_by_category = collections.defaultdict(list)
    for url, html in htmls:
        s_json, d_json, absolute_urls = json_farmer.filter_divs(html)

        for u in absolute_urls:
            new_urls.add(u)
        if s_json is None or d_json is None:
            continue

        c_str = s_json['Category']
        jsons_by_category[c_str].append((url, s_json, d_json))

    loaded_model = tf.keras.models.load_model("Link_Classifier.h5")
    good_urls = []
    for url in new_urls:
        pred, prob = link_classifier.classify_url(loaded_model, url)
        if pred == 1:
            good_urls.append(url)

    print(len(new_urls))
    print(len(good_urls))
    # with open(f'Skillet.html', 'w') as file:
    #     file.write(htmls[0])
    # for i, html in enumerate(htmls):
    #     with open(f"htmls/Z{i}.html", 'w') as file:
    #         file.write(html)
    # send htmls
    # send_htmls(htmls)

    e = time.time()
    print(f'Time: {e-s}')
    
async def get_urls():
    async with websockets.connect(server_url) as ws:
        msg = {
            'action': 'GetSQSBatch',
            # 'data':'hi'
        }

        await ws.send(json.dumps(msg))
        response = await ws.recv()
    urls = json.loads(response)
    hosts = collections.defaultdict(list)
    for url in urls:
        match = re.search(r"https?://(?:www\.)?([^/]+)", url)
        host = match.group(1) if match else ''
        hosts[host].append(url)

    return [(h, us) for (h, us) in hosts.items()]
        
    # get_url = f'{server_url}/GetSQSBatch'
    # r = requests.get(url = get_url)
    #
    # data = r.json()
    # print(r)
    # hosts = data['urls']

    # return hosts
def send_htmls(htmls):
    send_url = f'{server_url}/sendhtmls'
    print(send_url)
    html_data = {'htmls': htmls}
    headers = {"Content-Type": "application/json"}
    response = requests.post(url = send_url, data = json.dumps(html_data))
    print(r)




# Function to scrape a list of URLs in sequence
async def scrape_urls(crawler, urls):
    run_config = CrawlerRunConfig(
        verbose=False,
        log_console = False,
        check_robots_txt=False,
        delay_before_return_html=1.0,
        # wait_for_images=True,
        word_count_threshold=1,

        scan_full_page = True,
        magic=False,
        remove_overlay_elements=True,


    )
    results = await crawler.arun_many(urls=urls, config=run_config)
    # You can process the result here (e.g., save to a file or print it)
    for res in results:
        if res.success:
            print(f"{res.url} successfully crawled")
        else:
            print(f"Failed to crawl {res.url}")
    # print(result)
    return [(urls[i], res.html) for (i, res) in enumerate(results) if res.success]




if __name__ == "__main__":
    asyncio.run(main())
