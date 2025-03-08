from bs4 import BeautifulSoup
import re
import time
import collections
from openai import OpenAI
import datetime
import pandas as pd

def soup_to_text(span, key=False):
    txt = " ".join(cleaner(span.text).split())
    if key:
        return key_cleaner(txt)
    else:
        return txt

def cleaner(s):
    return re.sub(r'[\u200e|\u200f]', ' ', s)

def key_cleaner(s):
    return s.strip().lower()

# allow long rows gets first 2 vals from row
# otherwise skips
def tbody_to_dict(tbody, allow_long_rows=False):
    # table body
    d = {}
    # table row
    for tr in tbody.find_all("tr"):
        try:
            # table header
            th = tr.find("th")
            if th is not None:
                td = tr.find("td")
                d[soup_to_text(th, key=True)] = soup_to_text(td)
                continue

            tds = [td for td in tr.find_all("td")]
            if len(tds) < 2 or (len(tds) > 2 and not allow_long_rows):
                continue
            d[soup_to_text(tds[0], key=True)] = soup_to_text(tds[1])
        except Exception:
            pass
    return d

def filter_divs(html):
    # will have same keys for each product
    structured_json = {}

    details_json = {}

    soup = BeautifulSoup(html, "lxml")

# Example: Keep only the first half of <div> elements
    # divs = soup.find_all("div")
    main_container = soup.find(id="dp-container")

    if main_container is None:
        print("Not a product")
        return

    # fill in columns which don't require html
    structured_json['Scrape Date'] = str(datetime.datetime.today())

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
    structured_json['Category'] = "\\".join(category)

    right_col = main_container.find(id="rightCol" )
    center_col = main_container.find(id="centerCol")
    left_col = main_container.find(id = "leftCol")
    # print(len(right_col.find_all('div')))
    # print(len(center_col.find_all('div')))
    # print(len(left_col.find_all('div')))
    thumbnail = left_col.find('img', id='landingImage')
    structured_json['Thumbnail'] = thumbnail['src']

    p_title = center_col.find(id="productTitle")
    structured_json['Title'] = soup_to_text(p_title)
    try:
        ratings_row = center_col.find('div', id = 'averageCustomerReviews_feature_div')
        rating = ratings_row.find('span', id="acrPopover")
        stars = rating['title'].split(' ')[0]

        n_ratings = soup_to_text(ratings_row.find('span', id="acrCustomerReviewText"))
    except:
        stars = 'N/A'
        n_ratings = 0

    structured_json['Stars'] = stars
    structured_json['N_Ratings'] = n_ratings
    # price
    buy_options = right_col.find_all(id=re.compile(r'^\w+AccordionRow_?\d*$'))
    for offer in buy_options[:1]:
        apexOffer = offer.find(id="apex_offerDisplay_desktop") 
        price = apexOffer.find("span", class_ = "a-offscreen")
        structured_json['Price'] = soup_to_text(price)

        availability = offer.find("div", id="availability").find("span")
        structured_json['Availability'] = soup_to_text(availability)

    # thumbnail


    # product description
    p_descript = main_container.find("div", id="productDescription")
    descript = soup_to_text(p_descript.find('span'))
    structured_json['Description'] = descript
    # curr_container = None
    # descript = main_container
    # while descript is not None:
    #     curr_container = descript
    #     descript = curr_container.find("div", id="productDescription_feature_div")


    

    # table information
    tables = center_col.find_all('tbody')
    
    for table in tables:
        # merge / union
        details_json |= tbody_to_dict(table)

    # product facts
    try:
        product_facts_container = center_col.find(id="productFactsDesktopExpander")

        details_title = product_facts_container.find(class_='product-facts-title')
        sibling_list = details_title.find_next_sibling()

        for list_item in sibling_list.find_all('li'):
            spans = [soup_to_text(span) for span in list_item.find_all("span", class_="a-color-base")]
            details_json[key_cleaner(spans[0])] = spans[1]
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
            details_json[key_cleaner(spans[0])] = spans[1]


    try:
        prod_details = main_container.find(id="prodDetails")

        tables = prod_details.find_all('tbody')
        
        for table in tables:
            details_json |= tbody_to_dict(table)
    except Exception:
        pass

    # product comparison
    product_comparison = main_container.find('div', id="product-comparison_feature_div")
    try:
        table = product_comparison.find('tbody')
        details_json |= tbody_to_dict(table, allow_long_rows=True)
    except Exception:
        pass

    # append additional common products to structured_json
    additional_keys = ['Product Dimensions', 'Item Weight', 'Country of Origin', 'Number of Pieces', 'Batteries required', 'Brand', 'UPC', 'Number of Items', 'Manufacturer', 'ASIN', 'Best Sellers Rank']

    delete_keys = ['customer reviews']

    for key in additional_keys:
        cleaned_key = key_cleaner(key)
        if cleaned_key in details_json:
            structured_json[key] = details_json[cleaned_key]
            del details_json[cleaned_key]
        else:
            structured_json[key] = None

    for key in delete_keys:
        del details_json[key_cleaner(key)]

    # clean details json
    new_details_json = {}
    for key in details_json:
        if key != '':
            new_details_json[key] = details_json[key]
        

    return structured_json, new_details_json


def create_table_schema(cat, jsons):
    openai = OpenAI(
            base_url="https://api.deepinfra.com/v1/openai",
            )
    system_msg_content = f"""
        You will be given JSONS representing products of category [{cat}].
        Use the jsons to make a newline-separated list of the keys which a user might want to use to filter out irrelevant products.
        If multiple keys have the same meaning, (e.g. Memory and RAM), combine them into a single backslash-seperated row. 
        Don't include any key in multiple rows. 
        Remove rows which only appear in 40% or less of JSONs. 
        Only include keys, remove all values.
        Don't provide any text other than the list
        """
    jsons = [str(json) for json in jsons]
    user_msg_content = f"{'\n\n'.join(jsons)}"
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

# LLM schema
jsons_by_category = collections.defaultdict(list)
for i in range(1, 10):
    with open(f'Z{i}.html', 'r') as file:
        html = file.read()

        s_json, d_json = filter_divs(html)
        c_str = s_json['Category']
        jsons_by_category[c_str].append((s_json, d_json))

most_popular = [(len(jsons), cat, jsons) for cat, jsons in jsons_by_category.items()]
most_popular.sort(reverse=True)
_, cat, jsons = most_popular[0]

s_jsons = [j[0] for j in jsons]
d_jsons = [j[1] for j in jsons]
schema = create_table_schema(cat, d_jsons)

for key in s_jsons[0]:
    print(f'{key}\t{s_jsons[0][key]}')

print('\n\n')

for key in d_jsons[0]:
    print(key)


print('\n\n')
print(schema)
#
# for row in schema.split('\n'):
#     print('\n')
#     for key in row.split('\\'):
#         key = key.strip()
#         print(f'KEY: {key}')
#         vals = ''
#         for i, j in enumerate(jsons):
#             if key in j:
#                 vals += j[key] + f'\\{i}\\'
#         print(vals)


jsons = []
for _, js in jsons_by_category.items():
    for j in js:
        jsons.append(j)

# csv
# keys = collections.defaultdict(int)
# for i in range(len(jsons)):
#     jsons[i] = {key.strip().lower(): v for key, v in jsons[i].items()}
#     for key in jsons[i]:
#         keys[key] += 1
#
# filtered_keys = {}
# for key, count in keys.items():
#     if count == len(jsons):
#         filtered_keys[key] = []
#
# additional = ['Product Dimensions', 'Item Weight', 'Country of Origin', 'Number of Pieces', 'Batteries required', 'Brand', 'UPC', 'Manufacturer', 'Best Sellers Rank', 'ASIN',]
#
# for key in additional:
#     filtered_keys[key.strip().lower()] = []
#
# for j in jsons:
#     for key in filtered_keys:
#         if key in j:
#             filtered_keys[key].append(j[key])
#         else:
#             filtered_keys[key].append(None)
#
# print(filtered_keys)



e = time.time()
print(f'Time: {e-s}')
