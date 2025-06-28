
from dotenv import load_dotenv 
from pymongo import MongoClient
import os

class MongoDBHandler:
    def __init__(self):
        load_dotenv()
        self.connection_string = os.environ.get("MONGODB_CONNECTION_STRING")
        self.client = MongoClient(self.connection_string)
        self.db = self.client['newsfilter_db']
        self.collection = self.db['newsfilter_news']

    def article_exists(self, title):
        return self.collection.find_one({"title": title}) is not None

    def save_article(self, article):
        if not self.article_exists(article['title']):
            self.collection.insert_one(article)
            print(f"Saved new article: {article['title']}")
            return True
        else:
            print(f"Article already exists: {article['title']}")
            return False