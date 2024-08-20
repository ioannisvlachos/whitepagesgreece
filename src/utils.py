import os
import re
import json
import time
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed
import pprint
import glob
import pandas as pd
import random
from typing import List
from datetime import datetime
from keplergl import KeplerGl
from src.data_models import Phone, Name, Address, Subscriber, ItemforMap, ItemforQuery

js_reg = "window.vueData\s=\sJSON.parse\(\'(.*)"

def get_sitemap():
    sitemaps = []
    exported_sitemap = []
    r_list = requests.get('https://www.11888.gr/sitemap.xml').text.split('<loc>')

    for item in r_list:
        rg = re.search('https://www.11888.gr/sitemaps/white_pages/sitemap\d+\.xml|https://www.11888.gr/sitemaps/white_pages/sitemap.xml', item)
        if rg:
            sitemaps.append(rg.group())
    print(f'[*] Length of sitemap {len(sitemaps)}')

    for i in range(len(sitemaps)):
        print(f'- Getting sitemap {i+1}/{len(sitemaps)}')
        r = requests.get(sitemaps[i])
        re_urls = re.compile('<loc>(.*)</loc>').findall(r.text)
        for url in re_urls:
            exported_sitemap.append({'id': re.search('https://www.11888.gr/search/white_pages/(.*)/', url).group(1), 'url': url})
    print(f'[*] Completed downloading sitemap. Contacts: {len(exported_sitemap)}')
    save_sitemap(exported_sitemap)
    return exported_sitemap

def save_sitemap(sitemap):
    with open('sitemap.json', 'w') as ex:
        d = json.dumps(sitemap, ensure_ascii=False, indent=4)
        ex.write(d)

def load_sitemap():
    with open('sitemap.json', 'r') as ex:
        return json.load(ex)

def key_None(value):
    if value==None or value=='null':
        return ''
    else:
        return value    

def get_info(ad):
    r = requests.get(ad)
    d = re.search(js_reg, r.text)
    ad_num = re.search('https://www.11888.gr/search/white_pages/(.*)', ad).group(1)
    js = json.loads(d.group(1)[:-3].encode("utf-8").decode("unicode-escape"))
    try:
        js['name'].update({'str_name':' '.join([key_None(js['name'].get('last','')), key_None(js['name'].get('middle','')), key_None(js['name'].get('first',''))])})
    except Exception:
        return 1
    try:
        if 'municipality' in js['address'].keys():     
            js['address'].update({'str_add':' '.join([key_None(js['address'].get('street1','')), key_None(js['address'].get('number1','')), key_None(js['address'].get('municipality').get('name','')), key_None(js['address'].get('subregion').get('name', '')), key_None(js['address'].get('region').get('name', ''))])})
        elif 'municipality' not in js['address'].keys() and 'region' not in js['address'].keys() and 'subregion' not in js['address'].keys():
            js['address'].update({'str_add':' '.join([key_None(js['address'].get('street1','')), key_None(js['address'].get('number1','')), key_None(js['address'].get('postal_code'))])})
        else:
            js['address'].update({'str_add':' '.join([key_None(js['address'].get('street1','')), key_None(js['address'].get('number1','')), key_None(js['address'].get('subregion').get('name', '')), key_None(js['address'].get('region').get('name', ''))])})
    except Exception as e:
        print(f'Error {e}')
    return {'number': int(ad_num), 'data': js}

def save_json(jsonFile):
    if not os.path.isdir('wp_db'):
        os.mkdir('wp_db')
    with open(os.getcwd() + '/wp_db/' + str(jsonFile['number']) + '.json', 'w') as ex:
        d = json.dumps(jsonFile, ensure_ascii=False, indent=2)
        ex.write(d)

def to_be_downloaded(old_sitemap, new_sitemap):
    old = [int(x['id']) for x in old_sitemap]
    new = [int(x['id']) for x in new_sitemap]
    diff = list(set(new)-set(old))
    for_download = [{'id':str(x), 'url':'https://www.11888.gr/search/white_pages/' + str(x)} for x in diff]
    return for_download

def split_list(lst, chunk_size):
    return [lst[i:i + chunk_size] for i in range(0, len(lst), chunk_size)]

def download_data(js, sample=False):
    counter = 1
    if sample == False:
        list_to_be_downloaded = split_list(js, 1000)
    else:
        randNum = random.randint(0,len(js))
        list_to_be_downloaded = split_list(js[randNum:randNum+1000], 100)    

    for item in list_to_be_downloaded:
        print(f'- Getting chunk {counter}/{len(list_to_be_downloaded)}..')
        with ThreadPoolExecutor(max_workers=12) as tpe:
            futures = [tpe.submit(get_info, ad['url']) for ad in item]
        for future in as_completed(futures):
            try:
                save_json(future.result())
            except Exception as e:
                print(f'[--] Error {e} saving file')
                continue
        counter += 1


def getDb(path: str) -> List[str]:
    return glob.glob(path + '/*.json')


def getSubsPhones(js: dict) -> List[Phone]:
    return [Phone(number=item['number'], provider=item['provider'], type=item['type']) for item in js['data']['phones']]


def getSubsNameOnly(js: dict) -> Name:
    name_data = js['data']['name']
    return Name(first_name=name_data['first'], middle_name=name_data.get('middle'), last_name=name_data['last'], str_name=name_data['str_name'])


def getSubsAddressOnly(js: dict) -> Address:
    address_data = js['data']['address']
    return Address(
        street1=address_data['street1'],
        number1=address_data['number1'],
        street2=address_data.get('street2'),
        number2=address_data.get('number2'),
        municipality=address_data.get('municipality', {}).get('name'),
        subregion=address_data.get('subregion', {}).get('name'),
        region=address_data.get('region', {}).get('name'),
        str_add=address_data['str_add']
    )


def getSubsAllData(jsonFile: str) -> Subscriber:
    with open(jsonFile) as f:
        js = json.load(f)

    name = getSubsNameOnly(js)
    phones = getSubsPhones(js)
    address = getSubsAddressOnly(js)
    coords = js['data']['address']['location']
    subscriber = Subscriber(name=name, phones=phones, address=address, coords=coords)
    
    # Access individual attributes of the Name object
    name_dict = {
        'first_name': name.first_name,
        'middle_name': name.middle_name,
        'last_name': name.last_name,
        'str_name': name.str_name
    }
    
    # Create a custom dictionary representation for the Subscriber object
    subscriber_dict = {
        'name': name_dict,
        'phones': [phone.__dict__ for phone in phones],
        'address': address.__dict__,
        'coords': coords
    }
    return subscriber_dict


def load_map_config():
    with open('custom_config.json', 'r') as cc:
        custom_config = json.loads(cc.read())
    return custom_config


def getMapSubsPhones(js: dict):
    return [item['number'] for item in js['phones']]


def getMapSubsNameOnly(js: dict):
    return "%s" % (js['name']['str_name'])
   

def getMapSubsAddressOnly(js: dict):
    return "%s" % (js['address']['str_add'])


def userInput() -> str:
    req_data = input('Insert phone number..')
    return req_data

def prepareQueryItem(req_data: dict) -> ItemforQuery:
    qname = req_data['name']
    qaddress = req_data['address']
    qphone = req_data['phone']
    query = ItemforQuery(name=qname, address= qaddress, phone=qphone)
    print(query)
    return query

def prepareMapItem(tuple_val: tuple) -> ItemforMap:
    # Initialize empty lists to store attribute lists
    names_list = []
    phones_list = []
    addresses_list = []
    latitudes = []
    longitudes = []

    for val in tuple_val:
        req_number = val[0]
        name = getMapSubsNameOnly(val[1])
        phone = getMapSubsPhones(val[1])
        address = getMapSubsAddressOnly(val[1])
        lat = float(val[1]['coords']['lat'])
        lon = float(val[1]['coords']['lon'])
        my_item = ItemforMap(name=name, phone=phone, address=address, latitude=lat, longitude=lon)

        # Append data to respective lists
        names_list.append(my_item.name)
        phones_list.append(req_number)
        addresses_list.append(my_item.address)
        latitudes.append(my_item.latitude)
        longitudes.append(my_item.longitude)

    # Create the dictionary
    result_dict = {
        'name': names_list,  # Each attribute is directly in the dictionary
        'phone': phones_list,
        'address': addresses_list,
        'latitude': latitudes,
        'longitude': longitudes
    }

    return result_dict

def exportMap(result_dict:dict) -> None:
    df = pd.DataFrame(result_dict)
    # Create a KeplerGl map object
    map_ = KeplerGl(height=800)
    # Add the DataFrame to the map
    map_.add_data(data=df, name='info')
    # Load map config
    map_.config = load_map_config()
    # Export to HTML
    map_.save_to_html(file_name="static/index.html", read_only = True)



    
