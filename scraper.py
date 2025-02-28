import asyncio
from crawl4ai import *
import time
import requests

async def main():
# await url request
    s = time.time()
    hosts = get_urls()
    urls = [
        "https://www.amazon.com/s?k=skillets&crid=J4HH9K8GQZDO&sprefix=skillet%2Caps%2C171"
    ]
    # convert to 2d list, where each list has urls from different hosts
    url_bursts = []
    hostnames = []
    for hostname, urls in hosts:
        while len(url_bursts) < len(urls):
            url_bursts.append([])

        for i, url in enumerate(urls):
            url_bursts[i].append(url)
        hostnames.append(hostname)

    htmls = []
    async with AsyncWebCrawler() as crawler:
        for urls in url_bursts:
            # fetch all urls in burst simultaneously
            htmls += list(await asyncio.gather(*[scrape_url(crawler, url) for url in urls]))

    # send htmls

    e = time.time()
    print(f'Time: {e-s}')
    
server_url = 'http://127.0.0.1'
def get_urls():
    r = requests.get(url = server_url)

    data = r.json()
    hosts = data['urls']

    return hosts
def send_htmls(htmls):
    r = requests.post(url = server_url, data = htmls)
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
    print(result)
    return result




if __name__ == "__main__":
    asyncio.run(main())
