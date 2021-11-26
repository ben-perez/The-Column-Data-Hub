from dataclasses import dataclass
from os import environ
import pandas as pd
from abc import ABC, abstractmethod
from typing import List, Tuple
from app_service.models.article_section_content import ArticleSectionContentBase

class DataFrameServiceBase(ABC):

    @abstractmethod
    def convert(self, parsed_content : List[ArticleSectionContentBase]) -> Tuple[pd.DataFrame]:
        pass

class DataFrameService(DataFrameServiceBase):

    df_link : pd.DataFrame
    df_article : pd.DataFrame

    def convert(self, content_list : List[ArticleSectionContentBase]) -> Tuple[pd.DataFrame]:
        consolidated_link_content = []
        consolidated_article_content = []
        for content in content_list:
            consolidated_link_content += content.link_content
            consolidated_article_content += content.article_content
        self.df_link = df_link_content = pd.DataFrame(consolidated_link_content)
        self.df_article = df_article_content = pd.DataFrame(consolidated_article_content)
        return (df_link_content, df_article_content)

class SQLQueryStrategy(ABC):

    @abstractmethod
    def create_query(self, *args : Tuple[str]) -> str:
        pass

    @abstractmethod
    def connect(self):
        pass

class SQLQueryManager(SQLQueryStrategy):

    def create_query(self, *args : Tuple[str]) -> str:
        return ""

    def connect(self):
        pass

class DataService:

    sql_service : SQLQueryStrategy
    df_service : DataFrameServiceBase

    def __init__(self):
        self.sql_service = SQLQueryManager()
        self.df_service = DataFrameService()

    def convert_to_df(self, parsed_content : List[ArticleSectionContentBase]) -> Tuple[pd.DataFrame]:
        df_link, df_article = self.df_service.convert(parsed_content)
        return df_link, df_article