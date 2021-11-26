from app_service.web_service import WebService
from app_service.data_service import DataService

def main():
    #dates = ["07202020","07212020","07222020","07232020"]
    dates = ["10272021","10292021","11052021"]
    web_service = WebService()
    content = web_service.parse_articles(dates)
    df_converter = DataService()
    df_link_content, df_article_content = DataService.convert_to_df(content)
    print(content)

if __name__ == "__main__":
    main()