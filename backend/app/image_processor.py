import numpy as np
from PIL import Image
import requests
from io import BytesIO
from aws_utilities import S3Utilities
from database_util import DatabaseUtilities
from util import Utilities


class ImageProcessor:
    def __init__(self):
        # Initialize any required ML models or processing tools
        self.db_util = DatabaseUtilities("image_search")
        self.collection = self.db_util.connect_image_search_collection() 
        

    async def process_image_url(self, url: str) -> str:
        """
        Download and process an image from a URL
        Returns: image_id of the processed and stored image
        """
        try:
            # Download image
            response = requests.get(url)
            image = Image.open(BytesIO(response.content))
            
            # Process image (resize, normalize, etc.)
            processed_image = self._preprocess_image(image)
            
            # Generate embeddings and store image
            image_id = self._store_image(processed_image, url)
            
            return image_id
        except Exception as e:
            raise Exception(f"Failed to process image: {str(e)}")

    def _preprocess_image(self, image: Image) -> Image:
        """Preprocess image for consistency"""
        # Resize to standard size
        target_size = (224, 224)
        image = image.resize(target_size)
        
        # Convert to RGB if necessary
        if image.mode != 'RGB':
            image = image.convert('RGB')
            
        return image

    def _store_image(self, image: Image, url: str) -> str:
        """Store image and its metadata, return image_id"""
        # Convert PIL Image to bytes
        img_byte_arr = BytesIO()
        image.save(img_byte_arr, format=image.format or 'JPEG')
        img_byte_arr.seek(0)

        # Create a file-like object with necessary attributes
        image_id = Utilities.generate_uuid()
        img_byte_arr.filename = f"image_{image_id}.jpg"
        img_byte_arr.content_type = 'image/jpeg'

        # Upload to S3 using LocalStack
        s3_utils = S3Utilities()
        _, web_link = s3_utils.upload_to_s3(img_byte_arr)
        
        # Store metadata in ChromaDB
        metadata = {
            "image_id": image_id,
            "source_url": url,
            "width": image.size[0],
            "height": image.size[1],
            "mode": image.mode,
            "path": web_link
        }

        self.collection.add(
            ids=[image_id],
            metadatas=[metadata],
            documents=[url]  # Using URL as the document text for potential searching
        )
        
        return image_id
    

if __name__ == "__main__":
    import asyncio
    
    async def test_image_processing():
        # Test URL - using a stable test image
        test_url = "https://raw.githubusercontent.com/pytorch/pytorch.github.io/master/assets/images/pytorch-logo.png"
        
        try:
            processor = ImageProcessor()
            image_id = await processor.process_image_url(test_url)
            print(f"Successfully processed image. Image ID: {image_id}")
            
            # Verify the image was stored by retrieving its metadata
            results = processor.collection.get(
                ids=[image_id],
                include=["metadatas"]
            )
            
            if results and results['metadatas']:
                print("\nStored Image Metadata:")
                for key, value in results['metadatas'][0].items():
                    print(f"{key}: {value}")
            
        except Exception as e:
            print(f"Error during testing: {str(e)}")

    # Run the test
    asyncio.run(test_image_processing())

    

