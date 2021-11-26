from abc import ABC, abstractmethod
from typing import Dict, List
from datetime import datetime
import pandas as pd

class ArticleSectionContentBase(ABC):

    @abstractmethod
    def prep_content(self):
        pass

    @abstractmethod
    def extract_info(self):
        pass

class ArticleSectionContent(ArticleSectionContentBase):

    __raw_content : tuple
    __cleaned_content : List[tuple]
    link_content : List[dict]
    article_content : List[dict]

    def __init__(self, content : tuple):
        self.__raw_content = content
        self.prep_content()

    def prep_content(self):
        self.__cleaned_content = []
        date_str, date_content = self.__raw_content
        self.__cleaned_content = [(date_str, section_id, section_content) for (section_id, section_content) in date_content.items()]
        self.extract_info()
    
    def extract_info(self):
        content_with_link_info = []
        content_with_article_info = []
        for entry in self.__cleaned_content:
            date_key, section_id, section_content = entry
            date_ts = datetime.strptime(date_key, "%m%d%Y").date()
            if section_content["is_story"]:
                table_rows = section_content["content"].find_all("tr")
                title_row, article_row = table_rows[-2:]
                hyperlink_list = article_row.find_all("a")
                article_text = " ".join(list(title_row.stripped_strings) + list(article_row.stripped_strings))
            else:
                hyperlink_list = section_content["content"].find_all("a")
                article_text = " ".join(list(section_content["content"].stripped_strings))
            for hyperlink in hyperlink_list:
                link_href = hyperlink.get("href")
                link_text = hyperlink.get_text()
                link_content_entry = dict(Date=date_ts, SectionId=section_id, LinkHref=link_href, LinkText=link_text)
                content_with_link_info.append(link_content_entry)
            article_content_entry = dict(Date=date_ts, SectionId=section_id, SectionText=article_text, SectionTextLength=len(article_text))
            content_with_article_info.append(article_content_entry)
        self.link_content = content_with_link_info
        self.article_content = content_with_article_info