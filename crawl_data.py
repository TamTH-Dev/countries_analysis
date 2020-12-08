import numpy as np
import pandas as pd
import unicodedata
import re

from urllib.request import urlopen
from bs4 import BeautifulSoup
from decimal import Decimal

URL = 'https://en.wikipedia.org/wiki'


def main():
    print()
    print_progress_bar(0, float('inf'), length=80)
    content = get_html_content(
        f'{URL}/List_of_countries_and_dependencies_by_population')
    table = content.find('table', {'class': ['wikitable', 'sortable']})
    rows = table.find_all('tr')
    data_content = []

    print_progress_bar(0, len(rows), length=80)

    for i in range(len(rows)):
        if rows[i]:
            cells = rows[i].find_all('td')

            if len(cells) > 0:
                country_link = cells[0].find('a').get('href')

                if filter_link(country_link):
                    country_name = get_country_name(country_link)
                    country_info = [
                        unicodedata.normalize('NFKD', cell.text).strip() for cell in cells
                    ]
                    additional_details = get_additional_details(country_name)

                    if len(additional_details) == 2:
                        country_info += additional_details
                        data_content.append(country_info)

        print_progress_bar(i, len(rows) - 1, length=80)

    dataset = pd.DataFrame(data_content)

    headers = rows[0].find_all('th')
    headers = [header.get_text().strip('\n') for header in headers]
    headers += ['Total Area', 'Total Nominal GDP']
    headers = headers[1:]
    dataset.columns = headers

    clean_data(dataset)
    # dataset.sample(2)

    dataset.to_csv('Dataset.csv', index=False)


def clean_data(dataset):
    dataset.rename(
        columns={'Country(or dependent territory)': 'Country'}, inplace=True)
    dataset.rename(
        columns={'% of world': 'Percentage of World Population'}, inplace=True)
    dataset.rename(columns={'Total Area': 'Total Area (km2)'}, inplace=True)

    for column in dataset.columns:
        dataset[column] = dataset[column].str.replace(r'\(.*\)', '')
        dataset[column] = dataset[column].str.replace(r'\[.*\]', '')

    dataset['Percentage of World Population'] = dataset['Percentage of World Population'].str.strip(
        '%')
    dataset['Population'] = dataset['Population'].str.replace(',', '')

    dataset['Total Area (km2)'] = dataset['Total Area (km2)'].str.replace(
        ',', '')
    for x in range(len(dataset['Total Area (km2)'])):
        area = dataset.iloc[x]['Total Area (km2)']
        if 'sq mi' in area:
            area = area.split('-')[0]
            area = re.sub(r'[^0-9.]+', '', area)
            area = int(float(area) * 2.58999)
        else:
            area = area.split('-')[0]
            area = re.sub(r'[^0-9.]+', '', area)
            area = int(float(area))
        dataset.iloc[x]['Total Area (km2)'] = area

    dataset['Total Nominal GDP'] = dataset['Total Nominal GDP'].str.replace(
        '$', '')
    for x in range(len(dataset['Total Nominal GDP'])):
        gdp = dataset.iloc[x]['Total Nominal GDP']
        if 'trillion' in dataset.iloc[x]['Total Nominal GDP']:
            gdp = re.sub(r'[^0-9.]+', '', gdp)
            gdp = int(float(gdp) * 1000000000000 * Decimal('1.1'))
        elif 'billion' in dataset.iloc[x]['Total Nominal GDP']:
            gdp = re.sub(r'[^0-9.]+', '', gdp)
            gdp = int(float(gdp) * 1000000000 * Decimal('1.1'))
        elif 'million' in dataset.iloc[x]['Total Nominal GDP']:
            gdp = re.sub(r'[^0-9.]+', '', gdp)
            gdp = int(float(gdp) * 1000000 * Decimal('1.1'))
        else:
            gdp = int(re.sub(r'[^0-9.]+', '', gdp))
        dataset.iloc[x]['Total Nominal GDP'] = gdp

    drop_columns = ['Date', 'Source(official or UN)']
    dataset.drop(drop_columns, axis=1, inplace=True)


def get_html_content(link):
    html = urlopen(link)
    soup = BeautifulSoup(html, 'html.parser')
    return soup


def get_additional_details(country_name):
    try:
        country_page = get_html_content(f'{URL}/{country_name}')
        table = country_page.find('table', {
            'class': ['infobox', 'geography', 'vcard']
        })
        additional_details = []
        does_read_content = False

        if table:
            for tr in table.find_all('tr'):
                if tr.get('class') == ['mergedtoprow'] and not does_read_content:
                    link = tr.find('a')
                    if link and (link.get_text().strip() == 'Area' or
                                 (link.get_text().strip() == 'GDP' and tr.find('span').get_text().strip() == '(nominal)')):
                        does_read_content = True
                elif tr.get('class') == ['mergedrow'] and does_read_content:
                    content = tr.find('td').get_text().strip('\n')

                # if content.find('km2') != -1:
                #     content = content.split(' ')
                #     index = content.index('km2')
                #     content = f'{content[index - 1]}'

                # tri_index = content.find('trillion')
                # if tri_index != -1:
                #     content = content[content.find('$') + 1:tri_index + 8]

                # bi_index = content.find('billion')
                # if bi_index != -1:
                #     content = content[content.find('$') + 1:bi_index + 7]

                    additional_details.append(content)
                    does_read_content = False

        return additional_details

    except Exception as error:
        print(f'Error: {error}')
        return []


def filter_link(link):
    return link.find('Demographics_of') != -1


def get_country_name(link):
    return link[22:]


def print_progress_bar(iteration, total, decimals=1, length=100, fill='█'):
    percent = round(100 * iteration / float(total), 2)
    filled_length = int(length * iteration // total)
    bar = fill * filled_length + '-' * (length - filled_length)
    print(f'\rProgress: |{bar}| {percent}% Completed', end='\r')

    # Print new line on complete
    if iteration == total:
        print()


if __name__ == '__main__':
    main()
