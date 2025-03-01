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
        self.db_util = DatabaseUtilities()
        self.s3_util = S3Utilities()
        # Initialize collections
        self.image_collection = self.db_util.connect_collection("image_collection")
        self.text_collection = self.db_util.connect_collection("text_collection")

    async def get_all_images(self):
        """Retrieve all images from the collection"""
        try:
            # Use image collection as primary source
            collection = self.image_collection
            
            # Get the total count of images
            total_count = collection.count()
            
            if total_count == 0:
                return {
                    'status': 'success',
                    'images': [],
                }
            
            results = collection.get()
            
            # Format the results
            images = []
            if results and 'ids' in results:
                for idx, image_id in enumerate(results['ids']):
                    metadata = results['metadatas'][idx] if 'metadatas' in results else {}
                    s3_link = metadata.get('path', '')
                    description = metadata.get('description','')

                    images.append({ 
                        "id": image_id, 
                        "s3_link": s3_link,
                        "description": description
                    })
            
            return images
            
        except Exception as e:
            print(f"Error retrieving images: {str(e)}")

    async def text_search(self, query: str) -> Dict:
        """Search images using natural language text"""
        try:
            # Get text embeddings
            image_processor = ImageProcessor()
            _, text_embeddings = image_processor._preprocess_image(None, query)
            
            # First search in text collection
            text_results = self.text_collection.query(
                query_embeddings=[text_embeddings],
                n_results=100,
                include=['distances']  # Removed 'metadatas' since it's not needed
            )
            
            # Get matching image IDs from text search 
            results = []
            if text_results['ids']:
                matching_ids = text_results['ids'][0]
                
                # Get corresponding image details from image collection
                image_details = self.image_collection.get(
                    ids=matching_ids,
                    include=['metadatas']
                )
                
                # Combine results using only ids and distances from text_results
                for i in range(len(matching_ids)):
                    similarity_score = 1 - float(text_results['distances'][0][i])
                    if similarity_score >= 0.5:
                        image_metadata = image_details['metadatas'][i] if image_details['metadatas'] else {}
                        results.append({
                            'id': matching_ids[i],
                            'metadata': image_metadata,
                            's3_url': image_metadata.get('path'),
                            'similarity_score': round(similarity_score * 100, 2)
                        })
            
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
        """Search for similar images using an image URL"""
        try:
            # Download and process the image from URL
            image_processor = ImageProcessor()
            response = requests.get(image_url)
            if response.status_code != 200:
                raise Exception(f"Failed to download image from URL: {image_url}")
                
            search_image = Image.open(BytesIO(response.content))
            
            # Get image embeddings
            image_embeddings, _ = image_processor._preprocess_image(search_image, None)
            
            # Search in image collection
            search_results = self.image_collection.query(
                query_embeddings=[image_embeddings],
                n_results=100,
                include=['metadatas', 'documents', 'distances']
            )
            
            # Rest of the processing remains the same
            results = []
            if search_results['ids']:
                for i in range(len(search_results['ids'][0])):
                    similarity_score = 1 - float(search_results['distances'][0][i])
                    if similarity_score >= 0.8:
                        results.append({
                            'id': search_results['ids'][0][i],
                            'metadata': search_results['metadatas'][0][i],
                            's3_url': search_results['metadatas'][0][i].get('path'),
                            'similarity_score': round(similarity_score * 100, 2)
                        })
            
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

    async def delete_image(self, image_id: str) -> Dict:
        """Delete an image from both collections and S3"""
        try:
            # Get the image metadata from image collection
            results = self.image_collection.get(
                ids=[image_id],
                include=['metadatas']
            )
            
            if not results or not results['metadatas']:
                raise Exception(f"Image with ID {image_id} not found in database")
            
            # Get S3 path and delete from S3
            s3_path = results['metadatas'][0].get('path')
            if not s3_path:
                raise Exception(f"S3 path not found for image {image_id}")
            
            filename = s3_path.split('/')[-1]
            self.s3_util.s3_client.delete_object(
                Bucket=self.s3_util.bucket_name,
                Key=filename
            )
            
            # Delete from both collections
            self.image_collection.delete(ids=[image_id])
            self.text_collection.delete(ids=[image_id])
            
            return {
                'status': 'success',
                'message': f'Image {image_id} successfully deleted from S3 and both collections',
                'deleted_id': image_id
            }
            
        except Exception as e:
            print(f"Error deleting image: {str(e)}")
            return {
                'status': 'error',
                'message': str(e),
                'deleted_id': None
            }