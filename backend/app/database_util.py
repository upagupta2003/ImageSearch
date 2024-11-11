import chromadb
from chromadb.config import Settings
from PIL import Image

class DatabaseUtilities():
    def __init__(self, collection_name: str):
        self.collection_name = collection_name
        
    def get_db_client(self):
        return chromadb.client()
    
    #connect to the database
    def connect_image_search_collection(self):
        db_client = self.get_db_client()
        return db_client.create_collection(name=self.collection_name)
    

if __name__ == "__main__":
    db_util = DatabaseUtilities(IMAGE_SEARCH_COLLECTION_NAME)
    db_util.connect_image_search_collection()

