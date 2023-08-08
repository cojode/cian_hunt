import requests
from requests.models import PreparedRequest
from bs4 import BeautifulSoup
import pickle
import os
import click
from multiprocessing import Pool
from geopy.geocoders import Nominatim
import time

url = "https://www.cian.ru/cat.php?deal_type=rent"
params = {
    "currency": 2,
    "engine_version": 2,
    "maxprice": 100000,
    "minarea": 40,
    "foot_min": 45,
    "offer_type": "offices",
    "office_type[0]": 5,
    "only_foot": 2,
    "p": 0,
    "region": 1,
}
end_page = 50

links = []


def parse_data(url, params, dump_path):
    start_page = 1

    data = list()

    click.echo("[INFO] Collecting data: ", color=True)

    with click.progressbar(range(start_page, end_page + 1)) as bar:
        for params["p"] in bar:
            req = PreparedRequest()
            req.prepare_url(url, params)
            response = requests.get(req.url)
            if len(response.history) < 2:
                soup = BeautifulSoup(response.text, 'html.parser')
                soup_links = soup.find_all(
                    'a', attrs={"data-name": "CommercialTitle"}, href=True)
                data.extend([link['href'] for link in soup_links])
            else:
                click.echo("Redirect detected!")
                click.echo(f"{req.url} -> {response.url}")
        print(f"\nThere are {len(data)} offer links collected")
        print(f"Clearing duplicates...")
        data = list(set(data))
        time.sleep(1)
        print(f"Got {len(data)} unique offers")
        print(f"Data collection complete, dumping to {dump_path}")
        pickle.dump(data, open(dump_path, "wb"))


def load_data(dump_path):
    if os.path.exists(dump_path):
        return pickle.load(open(dump_path, "rb"))
    elif click.confirm("There are no dump found, parse one?", default=True):
        parse_data(url, params, dump_path)
        return pickle.load(open(dump_path, "rb"))
    else:
        return None
