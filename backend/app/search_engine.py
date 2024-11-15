from typing import List, Dict, Optional
from fastapi import UploadFile
from PIL import Image
from io import BytesIO
from database_util import DatabaseUtilities
from image_processor import ImageProcessor
from aws_utilities import S3Utilities
import requests

class SearchEngine:
    def __init__(self):
        # Initialize database connection
        self.db_util = DatabaseUtilities(collection_name="image_search")
        self.s3_util = S3Utilities()

    async def get_all_images(self):
        """
        Retrieve all images from the collection with optional pagination
        Args:
            limit: Optional maximum number of images to return
            offset: Optional number of images to skip (for pagination)
        Returns:
            dict: Dictionary containing images data and total count
        """
        try:
            collection = self.db_util.connect_image_search_collection()
            
            # Get the total count of images
            total_count = collection.count()
            
            # If no images, return early
            if total_count == 0:
                return {
                    'status': 'success',
                    'images': [],
                    }
            
            # Get all image IDs (or subset if limit is provided)
            results = collection.get()
            
            # Format the results
            images = []
            if results and 'ids' in results:
                for idx, image_id in enumerate(results['ids']):
                    metadata = results ['metadatas'][idx] if 'metadatas' in results else {}
                    s3_link = metadata.get('path', '')

                    images.append({ 
                        "id": image_id, 
                        "s3_link": s3_link 
                    })
            
            return images
            
        except Exception as e:
            print(f"Error retrieving images: {str(e)}")
        

    async def text_search(self, query: str) -> Dict:
        """
        Search images using natural language text
        Args:
            query: Text query to search for similar images
        Returns:
            Dict containing search results with similarity scores above 80%, ranked by similarity
        """
        try:
            # Get text embeddings using ImageProcessor's CLIP model
            image_processor = ImageProcessor()
            text_embeddings = image_processor._get_text_embeddings(query)
            
            # Connect to the collection
            collection = self.db_util.connect_image_search_collection()
            
            # Search for similar images using cosine similarity
            search_results = collection.query(
                query_embeddings=[text_embeddings],
                n_results=100,  # Increased to ensure we get all relevant matches
                include=['metadatas', 'documents', 'distances']
            )
            
            # Filter, format and rank results (similarity > 80%)
            results = []
            if search_results['ids']:
                for i in range(len(search_results['ids'][0])):
                    similarity_score = 1 - float(search_results['distances'][0][i])
                    if similarity_score >= 0.8:  # 80% threshold
                        results.append({
                            'id': search_results['ids'][0][i],
                            'metadata': search_results['metadatas'][0][i],
                            's3_url': search_results['metadatas'][0][i].get('path'),
                            'similarity_score': round(similarity_score * 100, 2)  # Convert to percentage
                        })
            
            # Sort results by similarity score in descending order
            results.sort(key=lambda x: x['similarity_score'], reverse=True)
            
            return {
                'status': 'success',
                'results': results,
                'total_results': len(results)
            }
            
        except Exception as e:
            print(f"Error in text search: {str(e)}")
            return {
                'status': 'error',
                'message': str(e),
                'results': [],
                'total_results': 0
            }
    
    

    async def url_search(self, image_url: str) -> Dict:
        """
        Search for similar images using an image URL
        Args:
            image_url: URL of the image to search with
        Returns:
            Dict containing search results with similarity scores above 80%, ranked by similarity
        """
        try:
            # Download and process the image from URL
            image_processor = ImageProcessor()
            
            # Download image from URL
            response = requests.get(image_url)
            if response.status_code != 200:
                raise Exception(f"Failed to download image from URL: {image_url}")
                
            search_image = Image.open(BytesIO(response.content))
            
            # Get image embeddings
            search_embeddings = image_processor._preprocess_image(search_image)
            
            # Connect to the collection
            collection = self.db_util.connect_image_search_collection()
            
            # Search for similar images using cosine similarity
            search_results = collection.query(
                query_embeddings=[search_embeddings],
                n_results=100,  # Increased to ensure we get all relevant matches
                include=['metadatas', 'documents', 'distances']
            )
            
            # Filter, format and rank results (similarity > 80%)
            results = []
            if search_results['ids']:
                for i in range(len(search_results['ids'][0])):
                    similarity_score = 1 - float(search_results['distances'][0][i])
                    if similarity_score >= 0.8:  # 80% threshold
                        results.append({
                            'id': search_results['ids'][0][i],
                            'metadata': search_results['metadatas'][0][i],
                            's3_url': search_results['metadatas'][0][i].get('path'),
                            'similarity_score': round(similarity_score * 100, 2)  # Convert to percentage
                        })
            
            # Sort results by similarity score in descending order
            results.sort(key=lambda x: x['similarity_score'], reverse=True)
            
            return {
                'status': 'success',
                'results': results,
                'total_results': len(results)
            }
            
        except Exception as e:
            print(f"Error in URL search: {str(e)}")
            return {
                'status': 'error',
                'message': str(e),
                'results': [],
                'total_results': 0
            }

    async def image_search(self, image: UploadFile) -> Dict:
        """
        Search for similar images using an uploaded image
        Args:
            image: UploadFile object containing the uploaded image
        Returns:
            Dict containing search results with similarity scores above 80%, ranked by similarity
        """
        try:
            # Read and convert uploaded file to PIL Image
            image_content = await image.read()
            search_image = Image.open(BytesIO(image_content))
            
            # Process the image and get embeddings
            image_processor = ImageProcessor()
            search_embeddings = image_processor._preprocess_image(search_image)
            
            
            # Connect to the collection
            collection = self.db_util.connect_image_search_collection()
            
            # Search for similar images using cosine similarity
            search_results = collection.query(
                query_embeddings=[search_embeddings],
                n_results=100,  # Increased to ensure we get all relevant matches
                include=['metadatas', 'documents', 'distances']
            )
            
            # Filter, format and rank results (similarity > 80%)
            results = []
            if search_results['ids']:
                for i in range(len(search_results['ids'][0])):
                    similarity_score = 1 - float(search_results['distances'][0][i])
                    if similarity_score >= 0.8:  # 80% threshold
                        results.append({
                            'id': search_results['ids'][0][i],
                            'metadata': search_results['metadatas'][0][i],
                            's3_url': search_results['metadatas'][0][i].get('path'),
                            'similarity_score': round(similarity_score * 100, 2)  # Convert to percentage
                        })
            
            # Sort results by similarity score in descending order
            results.sort(key=lambda x: x['similarity_score'], reverse=True)
            
            return {
                'status': 'success',
                'results': results,
                'total_results': len(results)
            }
            
        except Exception as e:
            print(f"Error in image search: {str(e)}")
            return {
                'status': 'error',
                'message': str(e),
                'results': [],
                'total_results': 0
            }
            
    async def delete_image(self, image_id: str) -> Dict:
        """
        Delete an image from both ChromaDB and S3
        Args:
            image_id: ID of the image to delete
        Returns:
            Dict containing status of the deletion operation
        """
        try:
            # First, get the image metadata from ChromaDB to get the S3 path
            collection = self.db_util.connect_image_search_collection()
            results = collection.get(
                ids=[image_id],
                include=['metadatas']
            )
            
            if not results or not results['metadatas']:
                raise Exception(f"Image with ID {image_id} not found in database")
            
            # Get S3 filename from metadata
            s3_path = results['metadatas'][0].get('path')
            if not s3_path:
                raise Exception(f"S3 path not found for image {image_id}")
            
            # Extract filename from the S3 URL
            filename = s3_path.split('/')[-1]
            
            # Delete from S3
            s3_utils = S3Utilities()
            s3_utils.s3_client.delete_object(
                Bucket=s3_utils.bucket_name,
                Key=filename
            )
            
            # Delete from ChromaDB
            collection.delete(
                ids=[image_id]
            )
            
            return {
                'status': 'success',
                'message': f'Image {image_id} successfully deleted from both S3 and ChromaDB',
                'deleted_id': image_id
            }
            
        except Exception as e:
            print(f"Error deleting image: {str(e)}")
            return {
                'status': 'error',
                'message': str(e),
                'deleted_id': None
            }