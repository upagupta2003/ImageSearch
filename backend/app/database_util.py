import chromadb
from chromadb.config import Settings

from PIL import Image
from util import Utilities

class DatabaseUtilities():
    def __init__(self, collection_name: str):
        Utilities.Load_Env()
        self.host = Utilities.get_env_variable('CHROMA_HOST')
        self.port = Utilities.get_env_variable('CHROMA_PORT')
        self.auth_token = Utilities.get_env_variable('CHROMA_AUTH_TOKEN')
        self.collection_name = collection_name
       
        
    def get_db_client(self):
        return chromadb.HttpClient(host= self.host,
                             settings=Settings(
                                 chroma_client_auth_provider="chromadb.auth.token_authn.TokenAuthClientProvider",
                                 chroma_client_auth_credentials=self.auth_token)
        )
    
    #connect to the database
    def connect_collection(self, collection_name: str):
        """Connect to a specific collection"""
        try:
            return self.client.get_or_create_collection(collection_name)
        except Exception as e:
            raise Exception(f"Error connecting to collection {collection_name}: {str(e)}")

if __name__ == "__main__":
    Utilities.Load_Env
    collection = Utilities.get_env_variable("IMAGE_SEARCH_COLLECTION_NAME")
    db_util = DatabaseUtilities(collection)
    db_util.connect_image_search_collection()
