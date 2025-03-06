from bs4 import BeautifulSoup
import re
import time
import collections
from openai import OpenAI

def soup_to_text(span):
    return " ".join(cleaner(span.text).split())

def cleaner(s):
    return re.sub(r'[\u200e|\u200f]', ' ', s)
def tbody_to_dict(tbody):
    # table body
    d = {}
    # table row
    for tr in tbody.find_all("tr"):
        try:
            # table header
            th = tr.find("th")
            if th is not None:
                td = tr.find("td")
                d[soup_to_text(th)] = soup_to_text(td)
                continue

            tds = [td for td in tr.find_all("td")]
            if len(tds) != 2:
                continue
            d[soup_to_text(tds[0])] = soup_to_text(tds[1])
        except Exception:
            pass
    return d

def filter_divs(html):
    info_json = {}
    soup = BeautifulSoup(html, "lxml")

# Example: Keep only the first half of <div> elements
    # divs = soup.find_all("div")
    main_container = soup.find(id="dp-container")

    if main_container is None:
        print("Not a product")
        return

    # get category at top
    breadcrumbs = main_container.find(id="desktop-breadcrumbs_feature_div")


    # skip dividers
    category = []
    try:
        for list_item in breadcrumbs.find_all('li')[::2]:
            span = list_item.find("a", class_="a-color-tertiary")
            category.append(soup_to_text(span))
    except Exception as e:
        category.append([f"Error When Attempting To Parse Category: {e}"])

    right_col = main_container.find(id="rightCol" )
    center_col = main_container.find(id="centerCol")
    left_col = main_container.find(id = "leftCol")
    # print(len(right_col.find_all('div')))
    # print(len(center_col.find_all('div')))
    # print(len(left_col.find_all('div')))

    p_title = center_col.find(id="productTitle")
    rating = center_col.find(id="acrPopover")
    
    info_json['PTitle'] = soup_to_text(p_title)

    # table information
    tables = center_col.find_all('tbody')
    
    for table in tables:
        # merge / union
        info_json |= tbody_to_dict(table)

    try:
        product_facts_container = center_col.find(id="productFactsDesktopExpander")

        details_title = product_facts_container.find(class_='product-facts-title')
        sibling_list = details_title.find_next_sibling()

        for list_item in sibling_list.find_all('li'):
            spans = [soup_to_text(span) for span in list_item.find_all("span", class_="a-color-base")]
            info_json[spans[0]] = spans[1]
    except Exception:
        pass


    # depth card table
    # depth_cards = center_col.find_all(id=re.compile(r"^depthInfoCard_\d+$"))
    # print(f"N depth cards: {len(depth_cards)}")

    # product details near the bottom
    product_details = main_container.find_all(id='detailBullets_feature_div')
    for details in product_details:
        for detail in details.find_all(class_ = 'a-list-item'):
            spans = [soup_to_text(span) for span in detail.find_all("span")]
            info_json[spans[0]] = spans[1]


    try:
        prod_details = soup.find(id="prodDetails")

        tables = prod_details.find_all('tbody')
        
        for table in tables:
            info_json |= tbody_to_dict(table)
    except Exception:
        pass

    return info_json, category

def category_list_to_str(c):
    return "\\\\".join(c)

def create_table_schema(cat, jsons):
    openai = OpenAI(
            base_url="https://api.deepinfra.com/v1/openai",
            )
    system_msg_content = f"You will be given a few JSONS representing products of category [{cat}]. Use the jsons to make a newline-separated list of the keys which a user might want to use to filter out irrelevant products. If multiple keys have the same meaning, (e.g. Memory and RAM), combine them into a single backslash-seperated row. Don't include any key in multiple rows. Remove rows which only appear in 40% or less of JSONs. Only include the key, remove all values. Don't provide any text other than the list"
    user_msg_content = f"{jsons}"
    chat_completion = openai.chat.completions.create(
    model="meta-llama/Meta-Llama-3.1-8B-Instruct",
    messages=[{"role": "system", "content": system_msg_content},
              {"role": "user", "content": user_msg_content}],
)

    result = chat_completion.choices[0].message.content
    return result

s = time.time()
# with open(f'Skillet.html', 'r') as file:
#     html = file.read()
#     j, c = filter_divs(html)
#     print(c)
#     print(j)

html = None
jsons_by_category = collections.defaultdict(list)
for i in range(5):
    with open(f'Z{i}.html', 'r') as file:
        html = file.read()

        json, c = filter_divs(html)
        c_str = category_list_to_str(c)
        jsons_by_category[c_str].append(json)

most_popular = [(len(jsons), cat, jsons) for cat, jsons in jsons_by_category.items()]
most_popular.sort(reverse=True)
_, cat, jsons = most_popular[0]

print(jsons[1])
schema = create_table_schema(cat, jsons)
print(schema)

for row in schema.split('\n'):
    print('\n')
    for key in row.split('\\'):
        key = key.strip()
        print(f'KEY: {key}')
        vals = ''
        for i, j in enumerate(jsons):
            if key in j:
                vals += j[key] + f'\\{i}\\'
        print(vals)

e = time.time()
print(f'Time: {e-s}')
