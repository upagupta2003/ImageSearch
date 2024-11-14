import numpy as np
from PIL import Image
import requests
from io import BytesIO
from aws_utilities import S3Utilities
from database_util import DatabaseUtilities
from util import Utilities
import torch
from transformers import CLIPProcessor, CLIPModel


class ImageProcessor:
    def __init__(self):
        # Load the CLIP model from Hugging Face
        self.model = CLIPModel.from_pretrained('openai/clip-vit-base-patch32')
        # Load the processor used to pre-process the images and make them compatible with the model
        self.processor = CLIPProcessor.from_pretrained("openai/clip-vit-base-patch32")
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
        
    def extract_image_features(self, image: Image) -> torch.Tensor:
        """
        Extract features from an image using CLIP model
        Args:
            image: PIL Image object
        Returns:
            torch.Tensor: Normalized image embeddings
        """
        # Preprocess the image using CLIP's processor
        inputs = self.processor(images=image, return_tensors="pt", padding=True)
        
        # Extract features using the model
        with torch.no_grad():
            image_features = self.model.get_image_features(**inputs)
            # Normalize the features
            image_features = image_features / image_features.norm(dim=-1, keepdim=True)
            
        return image_features.squeeze(0).tolist()

    def _preprocess_image(self, image: Image, text = None) -> Image:
        """Preprocess image for consistency"""
        
        # Initialize embeddings
        image_embeddings = None
        text_embeddings = None
        
        # Process the image if provided
        if image is not None:
            image_embeddings = self.extract_image_features(image)
            image_embeddings = image_embeddings / image_embeddings.norm(dim=-1, keepdim=True)

        # Process the text if provided
        if text is not None:
            text_inputs = self.modelprocessor(text=[text], return_tensors="pt", padding=True)
            with torch.no_grad():
                text_outputs =self.model.get_text_features(**text_inputs)
                text_embeddings = text_outputs / text_outputs.norm(dim=-1, keepdim=True)
                text_embeddings = text_embeddings.squeeze(0).tolist()

        # Combine the embeddings if both image and text are provided, and normalize
        if image_embeddings is not None and text_embeddings is not None:
            combined_embeddings = (image_embeddings + torch.tensor(text_embeddings)) / 2
            combined_embeddings = combined_embeddings / combined_embeddings.norm(dim=-1, keepdim=True)
            return combined_embeddings.tolist()

        # Return only image or text embeddings if one of them is provided
        return image_embeddings.tolist() if text_embeddings is None else text_embeddings

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
            documents=[url] 
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

    

if __name__ == "__main__":
    image_processor = ImageProcessor()
    print(image_processor.model)
