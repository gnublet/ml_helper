"""Downloads images to folder using the flickr API

Attributes:
    input_args (TYPE): Description
    max_number (TYPE): Description
    parser (TYPE): Description
    pic_urls (TYPE): Description
    search (TYPE): Description
    url_base (str): Description

TODO: 
consider passing parameters as dictionaries to clean up code
add verbose argument for print statements, flesh out other arguments (suffix, etc)
"""
import requests
import os
import sys
import toml
import argparse

parser = argparse.ArgumentParser()
parser.add_argument('search', 
                    action='store',
                    help='search term')
parser.add_argument('-n', 
                    action='store', 
                    dest='max_number',
                    default = 5, 
                    help='max nmber of results to return')
parser.add_argument('-f', 
                    action='store', 
                    dest='file_root',
                    default = '/home/kevin/Downloads/flickr/', 
                    help='folder root location to save images')
parser.add_argument('-s', 
                    action='store', 
                    dest='sort_by',
                    default = 'relevance', 
                    help='sort by filed (date-posted-desc, date-taken-desc, interestingness-desc, relvance, etc)')

input_args  = parser.parse_args()
search      = input_args.search
max_number  = input_args.max_number
file_root   = input_args.file_root
sort_by     = input_args.sort_by
print(input_args)

# url_base = 'https://api.flickr.com/'

def call_url(search, sort_by, page=1, method='flickr.photos.search', per_page = 500):
    """makes call to flickr method (default is photo search)
    
    Args:
        search (str, optional): search term
        page (int, optional): pagination
        method (str, optional): flickr method
    
    Returns:
        dict (json): raw json response for flickr method call
    """
    params = {
        'format': 'json',
        'nojsoncallback': 1,
        'text': search,
        'page': page,
        'per_page': per_page,  # max = 500
        'sort': sort_by, # this script defaults to relevance, API defaults to date-posted-desc which is inaccurate (ex. boys)
        'safe_search': 3 # 1: safe, 2: moderate, 3: restricted
    }
    print(params)
    # params = {}
    # params['format'] = 'json'
    # params['nojsoncallback'] = 1
    # params['text'] = search
    # params['page'] = page
    # params['per_page'] = 5 # max: 500
    # params['safe_search'] = 3 # 1: safe, 2: moderate, 3: restricted

    # load api key from toml config file
    with open('flickr_config.toml', 'r') as config_file:
        config_dictionary = toml.load(config_file)
        if 'api_key' in config_dictionary:
            params['api_key'] = config_dictionary['api_key']
        else:
            print('api key failed to load. Do you have toml installed?')
            quit()
    
    url = 'https://api.flickr.com/services/rest/?method=' + method
    return requests.get(url, params=params).json()

def get_picture(farm, server_id, pid, psecret, suffix = None):
    """construct url for picture
    
    Args:
        farm (str): Description
        server_id (str): Description
        pid (str): Description
        psecret (str): Description
        suffix (str, optional): optional sizing parameters
    
    Returns:
        str: url
    """
    if suffix is None:
        url = f"https://farm{farm}.staticflickr.com/{server_id}/{pid}_{psecret}.jpg"
    elif suffix in ['s','q','t','m','n','z','c','b','h','k','o']:
        url = f"https://farm{farm}.staticflickr.com/{server_id}/{pid}_{psecret}_{suffix}.jpg"
    else:
        url = None

    return url

def save_images(search, max_number, sort_by, file_root, sub_directory=None):
    """Save images to directory
    
    Args:
        search (str): search term
        max_number (int, optional): max number of results to return
        file_root (str, optional): place to put your photos
        sub_directory (None, optional): sub_directory
    
    Returns:
        list: list of photo urls
    """

    # If directory doesn't exist, create it
    if sub_directory is None:
        sub_directory = search
    directory = file_root + sub_directory
    if not os.path.exists(directory):
        os.makedirs(directory)

    max_results_per_page = 500
    num_pages = int(max_number)//max_results_per_page+1
    # print(num_pages)
    
    photos = []
    for i in range(1,num_pages+1):
        if i == num_pages:
            results = call_url(search, sort_by, i, 'flickr.photos.search', max_number % max_results_per_page)
        else:
            results = call_url(search, sort_by, i, 'flickr.photos.search')
        photos += results['photos']['photo']
    # print(photos)
    pic_urls = []
    for photo in photos:
        pic_urls.append(get_picture(photo['farm'], photo['server'], photo['id'], photo['secret']))

    if len(pic_urls) > 0:
        for index, pic_url in enumerate(pic_urls):
            response = requests.get(pic_url, stream=True)
            response.raise_for_status()
            with open(directory+ '/' + f'{index:05}.jpg' ,'wb') as handle:
                for block in response.iter_content(1024):
                    handle.write(block)
    return pic_urls

pic_urls = save_images(search, max_number, sort_by, file_root)


