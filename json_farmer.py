from bs4 import BeautifulSoup
import re
import time

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
            print(list_item.prettify())
            span = list_item.find("a", class_="a-color-tertiary")
            category.append(soup_to_text(span))
    except Exception as e:
        category.append([f"Error When Attempting To Parse Category: {e}"])

    print(category)
    right_col = main_container.find(id="rightCol" )
    center_col = main_container.find(id="centerCol")
    left_col = main_container.find(id = "leftCol")
    print(len(right_col.find_all('div')))
    print(len(center_col.find_all('div')))
    print(len(left_col.find_all('div')))
    p_title = center_col.find(id="productTitle")
    rating = center_col.find(id="acrPopover")
    
    info_json['PTitle'] = soup_to_text(p_title)
    # table information
    tables = center_col.find_all('tbody')
    
    t_dicts = [tbody_to_dict(table) for table in tables]
    print(t_dicts)
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
    depth_cards = center_col.find_all(id=re.compile(r"^depthInfoCard_\d+$"))

    # for c in depth_cards:
        # print(c)
    # print(depth_cards[0].prettify())
    print(f"N depth cards: {len(depth_cards)}")

    product_details = main_container.find_all(id='detailBullets_feature_div')
    for details in product_details:
        for detail in details.find_all(class_ = 'a-list-item'):
            spans = [soup_to_text(span) for span in detail.find_all("span")]
            info_json[spans[0]] = spans[1]


    try:
        prod_details = soup.find(id="prodDetails")

        tables = prod_details.find_all('tbody')
        
        t_dicts = [tbody_to_dict(table) for table in tables]
        print(t_dicts)
    except Exception:
        pass

    print(info_json)


# Print or use the filtered HTML

def create_json():
    pass

html = None
with open('Skillet.html', 'r') as file:
    html = file.read()
s = time.time()
filter_divs(html)
e = time.time()


print(f'Time: {e-s}')
