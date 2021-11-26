import pytest
import sys

def test_legacy_parsing(legacy_parser, legacy_date_strings):
    result = legacy_parser.parse_articles(legacy_date_strings)
    for value in result:
        assert value.link_content is not None and value.article_content is not None

def test_current_parsing(current_parser, current_date_strings):
    result = current_parser.parse_articles(current_date_strings)
    for value in result:
        assert value.link_content is not None and value.article_content is not None

def test_stress_requests(legacy_parser, large_date_string_list):
    result = legacy_parser.parse_articles(large_date_string_list)
    for value in result:
        assert value.link_content is not None and value.article_content is not None
