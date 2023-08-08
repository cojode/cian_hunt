import requests
import json
from bs4 import BeautifulSoup
from multiprocessing import Pool
from geopy.geocoders import Nominatim
import click
import pandas as pd


def replace_reduction(street):
    for word, replacement in {"ул.": "улица", "пер.": "переулок",
                              "ш.": "шоссе", "просп.": "проспект"}.items():
        street = street.replace(word, replacement)
    return street


def grab_address(link):
    html = requests.get(link).text
    soup = BeautifulSoup(html, 'html.parser')

    price_elements = soup.find('div', attrs={"data-name": "PriceInfo"})
    if price_elements:
        price = price_elements.find('div').get_text()
    else:
        price = None

    address_parts = soup.find_all('a', attrs={"data-name": "AddressItem"})
    try:
        street = address_parts[3].get_text()
        street = replace_reduction(street)
        apartament = address_parts[4].get_text()
        town = address_parts[0].get_text()
        area = address_parts[2].get_text()
    except IndexError:
        return (None, None, price)
    complete_address = ", ".join([street, apartament, town])
    return (complete_address[:1].upper() + complete_address[1:], area.replace("р-н ", ""), price)


def address_to_geocode(address):
    geolocator = Nominatim(user_agent="Tester")
    location = geolocator.geocode(address)
    if location:
        return (location.latitude, location.longitude)
    else:
        return None


def geocode_to_status(geocode):
    if not geocode:
        return None
    latitude, longtitude = geocode
    url = f"https://opp-api.ozon.ru/map/geo-object/by-point/{latitude}/{longtitude}"
    return json.loads(requests.get(url).text)


def solved_status(status):
    if not status:
        return "unknown"
    if "RecommendedZone" in status['items']:
        if status['items']['RecommendedZone'][0]['info']['fill'] == "#255AF6":
            return "blue zone"
        if status['items']['RecommendedZone'][0]['info']['fill'] == "#1DAE40":
            return "green zone"
    return "white zone"


def get_area_density(area):
    if not area:
        return None
    density_table_path = "data/density.csv"
    df = pd.read_csv(density_table_path)
    area = area.lower()
    row = df.loc[df['area'] == area]
    if row.empty:
        return None
    return row.iloc[0]['density']


def scrolling_process(links):
    solved_offers = []
    with click.progressbar(links) as bar:
        for link in bar:
            address, area, price = grab_address(link)
            geocode = address_to_geocode(address)
            raw_status = geocode_to_status(geocode)
            status = solved_status(raw_status)
            density = get_area_density(area)
            solved_offers.append(
                {"offer": link, "address": address, "price": price, "status": status, "density": density})

    report_path = "report.xlsx"
    df = pd.DataFrame(data=solved_offers)
    df.to_excel(report_path, index=False)
    click.echo(f"Offer scrolling complete, results saved to {report_path}")
