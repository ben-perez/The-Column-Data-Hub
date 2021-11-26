

def test_parsed_content_conversion(current_parser, sample_data_service, current_date_strings):
    content = current_parser.parse_articles(current_date_strings)
    df_link, df_article = sample_data_service.convert_to_df(content)
    assert df_link is not None and df_article is not None