from bs4.element import ResultSet
import pandas as pd
import os
from zipfile import ZipFile
from bs4 import BeautifulSoup
from pandas.core.base import DataError
import requests
import sqlite3
from datetime import datetime
from . import transform_data

def get_article_click_data(folder_path : str) -> pd.DataFrame:
    article_click_files = os.listdir(folder_path)
    article_click_df_list = list()

    for article_click_file in article_click_files:
        article_click_file_path = folder_path + "/" + article_click_file
        article_click_df = pd.read_excel(article_click_file_path)
        article_click_df["Source"] = article_click_file.strip(".xlsx")
        article_click_df_list.append(article_click_df)

    article_click_df_cons = pd.concat(article_click_df_list)
    article_click_df_cons = article_click_df_cons[article_click_df_cons["Clicks"].isna() == False].reset_index(drop=True)
    article_click_df_cons["Date"] = article_click_df_cons["Source"].apply(lambda source_date_str: datetime.strptime(source_date_str,"%m%d%Y"))
    article_click_df_cons.set_index("Date", inplace=True)
    article_click_df_cons = transform_data.add_date_component_columns(article_click_df_cons)
    return article_click_df_cons

def get_article_content(article_date : str) -> ResultSet:
    html_file_path = "data/raw/articles/{0}.html".format(article_date)

    with open(html_file_path, "rb") as html_file:
        url_soup = BeautifulSoup(html_file)

    table_tags = url_soup.find_all("table", {"class":"container"})
    return table_tags

def write_article_to_file(article_date : str, headers : dict = {"user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/94.0.4606.81 Safari/537.36"}):
    url_endpoint_template = "https://thecolumn.co/daily/{0}"
    html_file_path = "data/raw/articles/{0}.html".format(article_date)
    url = url_endpoint_template.format(article_date)
    url_response = requests.get(url, headers=headers)

    with open(html_file_path, "wb") as html_file:
        html_file.write(url_response.content)

def get_article_content_by_section(article_date : str) -> tuple:
    date_dt = datetime.strptime(article_date,"%m%d%Y")
    format_change_date = datetime(2020, 12, 28)
    html_file_path = "data/raw/articles/{0}.html".format(article_date)

    with open(html_file_path, "rb") as html_file:
        url_soup = BeautifulSoup(html_file)

    table_tags = url_soup.find_all("table", {"class":"container"})
    count = 0
    expected_article_count = 3
    expected_extra_count = 2
    expected_row_count = 4
    sections = dict()
    links = dict()
    search_for_articles = True
    search_for_extras = False

    for table_tag in table_tags:
        table_rows = table_tag.find_all("tr")

        if search_for_articles and len(table_rows) == expected_row_count:
            sections[count] = table_tag
            links[count] = table_tag.find_all("a")
            count += 1

        elif search_for_extras:
            if count < (expected_article_count + expected_extra_count):
                sections[count] = table_tag
                links[count] = table_tag.find_all("a")
                count += 1
            else:
                break
        
        if count == expected_article_count:
            search_for_articles = False
            if date_dt >= format_change_date:
                search_for_extras = True
            else:
                break

    return sections, links

def get_summary_data(file_path : str) -> pd.DataFrame:
    summary_df = pd.read_excel(file_path, parse_dates=True, index_col="Date/Time")
    summary_df = transform_data.add_date_component_columns(summary_df)
    return summary_df

def get_email_subjectline_text(article_date : str) -> str:
    html_file_path = "data/raw/articles/{0}.html".format(article_date)

    with open(html_file_path, "rb") as html_file:
        url_soup = BeautifulSoup(html_file)

    gmail_div = url_soup.find_all("div", {"class":"Gmail"})[0]
    subjectline_div = gmail_div.findNextSibling()
    subjectline_text = subjectline_div.get_text().replace("\n","").strip()
    return subjectline_text