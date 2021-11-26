from bs4 import BeautifulSoup
from typing import Dict, List, Tuple
from abc import ABC, abstractmethod
from datetime import date, datetime
import dateutil.parser
from requests.models import HTTPError
from requests.sessions import Session
from dataclasses import dataclass
import pandas as pd
from .models.article_section_content import ArticleSectionContent


@dataclass
class RequestConstData:
    base_url : str = "https://thecolumn.co/daily/{0}"
    user_agent : str = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/94.0.4606.81 Safari/537.36"
    story_sections : Tuple[str] = (
                                   "1",
                                   "2",
                                   "3"
                                  )
    section_id_list : Tuple[str] = (
                                    "1",
                                    "2",
                                    "3",
                                    "headlines",
                                    "MOTD"
                                   )
    

class HTMLRequesterBase(ABC):

    @abstractmethod
    def get_html_page(self, date_str : str) -> str:
        pass

class HTMLRequesterBasic(HTMLRequesterBase):

    date_str : str = ""
    request_session : Session = None

    def get_html_page(self, date_str : str) -> str:
        self.date_str = date_str
        url = RequestConstData.base_url.format(self.date_str)
        request_headers = {}
        request_headers["user-agent"] = RequestConstData.user_agent
        response = self.request_session.get(url, headers = request_headers)
        if response.ok:     
            content = response.text
            return content
        else:
            raise HTTPError(f"HTML for {self.date_str} failed to be retrieved")

    def get_html_pages(self, dates : List[str]) -> Dict[str, str]:
        self.request_session = Session()
        results = {}
        for date in dates:
            results[date] = self.get_html_page(date)
        return results

class ParsingStrategy(ABC):

    @abstractmethod
    def parse_for_content(self, content : str) -> Dict[str, dict]:
        pass

class LegacyParsingStrategy(ParsingStrategy):

    html_format_change : date = date(2020, 12, 28)

    def parse_for_content(self, content : str) -> Dict[str, dict]:
        content_soup = BeautifulSoup(content, "lxml")
        content_date = content_soup.find("p").get_text()
        date_dt = dateutil.parser.parse(content_date).date()
        table_tags = content_soup.find_all("table", {"class":"container"})
        count = 0
        expected_article_count = 3
        expected_extra_count = 2
        expected_row_count = 4
        sections = {}
        search_for_articles = True
        search_for_extras = False
        label_list = RequestConstData.section_id_list
        for table_tag in table_tags:
            table_rows = table_tag.find_all("tr")
            if search_for_articles and len(table_rows) == expected_row_count:
                label = label_list[count]
                sections[label] = dict(content=table_tag, is_story=True)
                count += 1
            elif search_for_extras:
                if count < (expected_article_count + expected_extra_count):
                    label = label_list[count]
                    sections[label] = dict(content=table_tag, is_story=False)
                    count += 1
                else:
                    break
            if count == expected_article_count:
                search_for_articles = False
                if date_dt >= self.html_format_change:
                    search_for_extras = True
                else:
                    break
        return sections

class CurrentParsingStrategy(ParsingStrategy):

    def parse_for_content(self, content: str) -> Dict[str, dict]:
        section_ids = RequestConstData.section_id_list
        content_soup = BeautifulSoup(content, "lxml")
        sections = {}
        for section_id in section_ids:
            section_soup = content_soup.find("tr", {"id":section_id})
            section_content = section_soup.find("table", {"class":"container"})
            sections[section_id] = dict(content=section_content, 
                                         is_story=section_id in RequestConstData.story_sections)
        return sections

class WebService:

    parsing_strat : ParsingStrategy
    html_requester : HTMLRequesterBase

    def __init__(self, is_legacy : bool = False):
        self.html_requester = HTMLRequesterBasic()
        if not is_legacy:
            self.parsing_strat = CurrentParsingStrategy()
        else:
            self.parsing_strat = LegacyParsingStrategy()

    def parse_articles(self, dates : List[str]) -> List[ArticleSectionContent]:
        parsed_content_list = []
        article_html_collection = self.html_requester.get_html_pages(dates)
        for date_str, article_html in article_html_collection.items():
            initial_parsed_content = self.parsing_strat.parse_for_content(article_html)
            parsed_content = ArticleSectionContent((date_str, initial_parsed_content))
            parsed_content_list.append(parsed_content)
        return parsed_content_list