import pandas as pd
import numpy as np
from bs4 import BeautifulSoup
from bs4.element import Tag

def add_date_component_columns(df : pd.DataFrame) -> pd.DataFrame:
    df["Month"] = df.index.month
    df["Day"] = df.index.day
    df["Year"] = df.index.year
    df["Week"] = df.index.isocalendar().week
    df["Weekday"] = df.index.weekday
    return df

def extract_url_info(url_series : pd.Series) -> pd.Series:
    url_info_extract_regex_pattern = "(\w{4,}\.?){1,}(\.\w{2,}){1}"
    extracted_url_info = url_series.str.extract(url_info_extract_regex_pattern)
    column_renamings = {0:"Domain", 1:"Extension"}
    extracted_url_info.rename(columns=column_renamings, inplace=True)
    return extracted_url_info

def form_text_from_article(article : Tag) -> str:
    strings = list()

    for string in article.stripped_strings:
        strings.append(string)

    string_complete = " ".join(strings)
    return string_complete

def get_article_subtitles(article : Tag) -> str:
    subtitle_strings = ""
    for subtitle in article.find_all("strong"):
        subtitle_strings += (" " + subtitle.get_text())
    return subtitle_strings

def form_url_date(idx) -> str:
    
    if idx.month < 10:
        month_str = "0{0}".format(idx.month)
    else:
        month_str = str(idx.month)

    if idx.day < 10:
        day_str = "0{0}".format(idx.day)
    else:
        day_str = str(idx.day)
    
    year_str = str(idx.year)
    full_date_str = month_str + day_str + year_str
    return full_date_str

def parse_article_section_content(article_section : Tag) -> str:
    stop_points = article_section.find_all("strong")
    stop_point_text = [stop_point.get_text() for stop_point in stop_points]
    _, _, article_section_text = article_section.get_text().partition(stop_point_text[0])
    
    for text in stop_point_text[1:]:
        start_pos = article_section_text.index(text)
        end_pos = start_pos + len(text)
        stop_point = article_section_text[start_pos:end_pos]
        article_section_text = article_section_text.replace(stop_point, " ")
    
    return article_section_text.replace("\n","").strip()

def get_article_section_data(article_section_list : dict, link_info : dict) -> pd.DataFrame:
    article_section_data = list()

    for date in article_section_list.keys():
        article_sections = article_section_list[date]

        for article_number in article_sections.keys():
            article_section = article_sections[article_number]
            section_text = parse_article_section_content(article_section)
            link_count = len(link_info[date][article_number])
            new_data_entry = (date, article_number, section_text, link_count)
            article_section_data.append(new_data_entry)

    article_section_df_columns = ["Date", "ArticleNumber", "SectionText", "LinkCount"]
    article_section_df = pd.DataFrame(columns = article_section_df_columns, data = article_section_data, dtype=str)
    article_section_df.LinkCount = article_section_df.LinkCount.astype(dtype = int)
    article_section_df.ArticleNumber = article_section_df.ArticleNumber.astype(dtype = np.int64)
    article_section_df["SectionArticleLength"] = article_section_df.SectionText.str.len()
    return article_section_df

def get_link_info_data(link_info : dict) -> pd.DataFrame:
    link_info_df_data = list()

    for date in link_info.keys():
        link_collection = link_info[date]

        for article_number in link_collection.keys():
            new_entries = [(date, article_number, link.get_text(), link.get("href")) 
                            for link in link_collection[article_number]]
            link_info_df_data += new_entries

    link_info_df_columns = ["Date", "ArticleNumber", "LinkText", "LinkHref"]
    link_info_df = pd.DataFrame(columns=link_info_df_columns, data=link_info_df_data)
    return link_info_df

def get_click_link_data(click_data : pd.DataFrame, link_info_data : pd.DataFrame) -> pd.DataFrame:
    link_click_df = link_info_data.merge(click_data, 
                                         left_on=["Date","LinkHref"],
                                         right_on=["Date","Link"],
                                         how="inner")
    link_click_df.drop(labels=["Source", "LinkHref"], 
                       axis=1, 
                       inplace=True)
    link_click_df.Date = link_click_df.Date.astype(dtype=np.datetime64)
    #link_click_df.rename(columns={"Date_y":"Date"}, inplace=True)
    #link_click_df.set_index("Date", drop=True, inplace=True)
    return link_click_df
