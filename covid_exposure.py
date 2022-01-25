import os
import requests
from bs4 import BeautifulSoup as bs
import sqlite3

##### START Config #####
db_path = 'covid_expo.db'
webpage = 'https://www.healthywa.wa.gov.au/Articles/A_E/Coronavirus/Locations-visited-by-confirmed-cases'

##### END Config #####

##### START Request and Process Data #####


def request_covid_loc(page):

    req = requests.get(page)
    soup = bs(req.content, 'lxml')
    loc_table = soup.find(class_='locationList')
    loc_rows = loc_table.find_all("div", {'id': 'mobileLocationList'})

    return loc_rows


def parse_covid_loc(loc_html):

    data = []

    for _ in loc_html:
        cols = _.find_all('p')
        cols = [ele.text.strip() for ele in cols]
        cols = [ele.replace('\n', ' ') for ele in cols]
        cols = [ele.replace(u'\xa0', ' ') for ele in cols]
        data.append([ele for ele in cols if ele])

    return data


def print_sites(data):

    for _ in data:
        print(_)

##### END Request and Process Data #####

##### START Database Functions #####
# Create database connection (If table doesnt exist, creates table)


def create_connection(db_file):

    conn = None

    try:
        conn = sqlite3.connect(db_file, isolation_level=None)
    except Exception as e:
        print(f"something went wrong: {e}")

    # create tables if needed
    query = (
        "SELECT count(name) FROM sqlite_master WHERE type='table' AND name='exposures';"
    )

    result = conn.execute(query)

    if result.fetchone()[0] == 1:
        pass
    else:
        print("creating table...")
        table_create = """ CREATE TABLE IF NOT EXISTS exposures (
                            id integer PRIMARY KEY,
                            timedate text,
                            suburb text,
                            location text,
                            updated text,
                            advice text
                        ); """
        conn.execute(table_create)
        conn.commit()

    return conn

# Compare database and new list


def filter_db_expo(dbconn, data):
    new_alerts = []
    alerts_not_added = []

    for i in data:

        if len(i) != 5:
            alerts_not_added.append(i)
        else:
            timedate = i[0]
            suburb = i[1]
            location = i[2]
            updated = i[3]
            advice = i[4]

            query = """SELECT count(id) FROM exposures WHERE 
                    timedate = ? 
                    AND suburb = ?
                    AND location = ?
                    AND updated = ?
                    AND advice = ?;"""

            args = (timedate, suburb, location, updated, advice)
            result = dbconn.execute(query, args)

            if result.fetchone()[0] > 0:
                pass
            else:
                new_alerts.append(i)

    return new_alerts, alerts_not_added

# Add new sites to data base


def add_site(dbconn, new_list):
    for i in new_list:
        timedate = i[0]
        suburb = i[1]
        location = i[2]
        updated = i[3]
        advice = i[4]

        args = (timedate, suburb, location, updated, advice)
        query = f"""INSERT INTO exposures (timedate, suburb, location, updated, advice) 
                    VALUES (?,?,?,?,?) """

        dbconn.execute(query, args)

##### END Database Functions #####


def main():
    # Create connection
    dbconn = create_connection(db_path)

    # Request exposure sites
    sites_html = request_covid_loc(webpage)
    parsed_data = parse_covid_loc(sites_html)
    # print_sites(parsed_data)

    # Check and insert exposure sites to database
    new_sites, not_added = filter_db_expo(dbconn, parsed_data)
    # print(new_sites)
    add_site(dbconn, new_sites)
    print_sites(not_added)

    # # Close connection
    dbconn.commit()
    dbconn.close()
    # print("Program ran to completion")


if __name__ == '__main__':
    main()
