import requests
from bs4 import BeautifulSoup as bs
import sqlite3


def request_covid_loc(page):
    req = requests.get(page)
    soup = bs(req.content)
    loc_table = soup.find(class_='locationList')
    loc_rows = loc_table.find_all("div", {'id': 'mobileLocationList'})
    return loc_rows


def parse_covid_loc(loc_html):
    data = []
    for _ in loc_html:
        cols = _.find_all('p')
        cols = [ele.text.strip() for ele in cols]
        cols = [ele.replace('\n', ' ') for ele in cols]
        data.append([ele for ele in cols if ele])
    return data


def print_sites(data):
    for _ in data:
        print(_)


def main():
    webpage = 'https://www.healthywa.wa.gov.au/Articles/A_E/Coronavirus/Locations-visited-by-confirmed-cases'
    sites_html = request_covid_loc(webpage)
    parsed_data = parse_covid_loc(sites_html)
    print_sites(parsed_data)


if __name__ == '__main__':
    main()
