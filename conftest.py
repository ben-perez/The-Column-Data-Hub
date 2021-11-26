import pytest
import sys
from app_service.web_service import WebService
from app_service.data_service import DataService

@pytest.fixture
def legacy_date_strings():
    return [
        "07202020",
        "01152021",
        "04162021"
    ]

@pytest.fixture
def current_date_strings():
    return [
        "10272021",
        "10292021",
        "11052021"
    ]

@pytest.fixture
def large_date_string_list():
    large_date_string_list_file = "data/tests/date_str_stress_test.txt"
    with open(large_date_string_list_file, "r") as date_string_file:
        large_date_string_list = [line.replace("\n", "") for line in date_string_file.readlines()]
    return large_date_string_list

@pytest.fixture
def legacy_parser():
    return WebService(is_legacy=True)

@pytest.fixture
def current_parser():
    return WebService()

@pytest.fixture
def sample_data_service():
    return DataService()