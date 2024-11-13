import numpy as np
from PIL import Image
import requests
from io import BytesIO
from google_utilities import GoogleDriveUtilities
import torch
from transformers import CLIPProcessor, CLIPModel

class ImageProcessor:
    def __init__(self):
        # Load the CLIP model from Hugging Face
        self.model = CLIPModel.from_pretrained('openai/clip-vit-base-patch32')
        # Load the processor used to pre-process the images and make them compatible with the model
        self.processor = CLIPProcessor.from_pretrained("openai/clip-vit-base-patch32")

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
        return google_drive_upload(image)
    
    
    

if __name__ == "__main__":
    image_processor = ImageProcessor()
    print(image_processor.model)
