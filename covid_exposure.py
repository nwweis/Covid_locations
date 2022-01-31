#!/usr/bin/env python3

# Import packages
import os
import sys
import requests
from bs4 import BeautifulSoup as bs
import sqlite3

# Config values
db_path = 'covid_expo.db'
webpage = 'https://www.healthywa.wa.gov.au/Articles/A_E/Coronavirus/Locations-visited-by-confirmed-cases'


def request_covid_loc(page):  # Request locations from webpage

    req = requests.get(page)
    soup = bs(req.content, 'lxml')
    table_body = soup.findChildren('table')[1].findChildren(
        ['tr', 'location-block'])  # Factored code to single line

    return table_body


def parse_covid_loc(table_body):  # Parse locations into text

    data = []

    for row in table_body:
        cols = row.findChildren(
            attrs={'content1', 'content2', 'content3', 'content4', 'content5'})  # Find elements with html tag attrs
        cols = [ele.text.strip().replace('\n', ' ').replace(u'\xa0', ' ')
                for ele in cols]  # Factored element edits to single line
        # cols = [ele.replace('\n', ' ') for ele in cols]
        # cols = [ele.replace(u'\xa0', ' ') for ele in cols]

        data.append([ele for ele in cols if ele])

    return data


# Create database connection (If table doesnt exist, creates table)
def create_connection(db_file):

    conn = None

    try:
        conn = sqlite3.connect(db_file, isolation_level=None)
    except Exception as e:
        print(f"something went wrong: {e}")

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


def filter_db_expo(dbconn, data):  # Compare database and new list

    new_alerts = []
    alerts_not_added = []  # If there is a need for manual input

    for i in data:
        if not i:
            print('Row does not contain data')
        elif len(i) < 5:
            alerts_not_added.append(i)
            print(f"Lenght of list is wrong. \n {i}")
        else:
            if len(i) > 5:
                timedate = '\n'.join(i[:-4])
            else:
                timedate = i[0]
            suburb = i[-4]
            location = i[-3]
            updated = i[-2]
            advice = i[-1]

            args = (timedate, suburb, location, updated, advice)

            query = """SELECT count(id) FROM exposures WHERE 
                    timedate = ? 
                    AND suburb = ?
                    AND location = ?
                    AND updated = ?
                    AND advice = ?;"""

            result = dbconn.execute(query, args)

            if result.fetchone()[0] > 0:
                pass
            else:
                new_alerts.append(args)

    return new_alerts


def add_site(dbconn, new_list):  # Add new sites to data base

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
        print(
            f"New site added: {timedate}, {suburb}, {location}, {updated}, {advice}")

    print(f"{len(new_list)} sites added to database")


def print_sites(dbconn):  # Print all exposure sites
    query = """SELECT * FROM exposures;"""
    result = dbconn.execute(query)

    for i in result:
        print(i)


def check_sites(dbconn):  # Function to check and add exposure sites to db
    # Request exposure sites
    sites_html = request_covid_loc(webpage)
    parsed_data = parse_covid_loc(sites_html)

    # Check and insert exposure sites to database
    new_sites = filter_db_expo(dbconn, parsed_data)
    add_site(dbconn, new_sites)


def main():
    user_input = input("Please select from 'add', 'print' or 'exit': ")

    if user_input == 'exit':
        print('Exit program')
        sys.exit()

    # Create connection
    dbconn = create_connection(db_path)

    if user_input == 'add':
        check_sites(dbconn)

    elif user_input == 'print':
        print_sites(dbconn)

    else:
        print("Wrong input, program terminated")

    # Close connection
    dbconn.commit()
    dbconn.close()


if __name__ == '__main__':
    main()
