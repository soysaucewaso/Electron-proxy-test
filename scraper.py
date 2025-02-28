import asyncio
from crawl4ai import *
import time
import requests
import json

print('running')
async def main():
# await url request
    print('run')
    s = time.time()
    hosts = get_urls()
    urls = [
        "https://www.amazon.com/s?k=skillets&crid=J4HH9K8GQZDO&sprefix=skillet%2Caps%2C171"
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
    async with AsyncWebCrawler() as crawler:
        for urls in url_bursts:
            # fetch all urls in burst simultaneously
            htmls += list(await asyncio.gather(*[scrape_url(crawler, url) for url in urls]))
            print(htmls)

    # send htmls
    send_htmls(htmls)

    e = time.time()
    print(f'Time: {e-s}')
    
server_url = 'http://3.220.232.5:5000'
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
async def scrape_url(crawler, url):
    run_config = CrawlerRunConfig(
        verbose=False,
        check_robots_txt=False
    )
    result = await crawler.arun(url=url, config=run_config)
    # You can process the result here (e.g., save to a file or print it)
    print(f"Scraped: {url}")
    print(type(result))
    # print(result)
    return result.html




if __name__ == "__main__":
    asyncio.run(main())
