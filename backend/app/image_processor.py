import numpy as np
from PIL import Image
import requests
from io import BytesIO
from aws_utilities import S3Utilities
from database_util import DatabaseUtilities
from util import Utilities
import torch
from transformers import CLIPProcessor, CLIPModel, BlipProcessor, BlipForConditionalGeneration


class ImageProcessor:
    def __init__(self):
        # Load the CLIP model from Hugging Face
        self.model = CLIPModel.from_pretrained('openai/clip-vit-base-patch32')
        # Load the processor used to pre-process the images and make them compatible with the model
        self.processor = CLIPProcessor.from_pretrained("openai/clip-vit-base-patch32")
        self.blip_processor = BlipProcessor.from_pretrained("Salesforce/blip-image-captioning-base")
        self.blip_model = BlipForConditionalGeneration.from_pretrained("Salesforce/blip-image-captioning-base")
        self.db_util = DatabaseUtilities("image_search")
        self.collection = self.db_util.connect_image_search_collection()
        # Create separate collections for image and text embeddings
        self.image_collection = self.db_util.connect_collection("image_collection")
        self.text_collection = self.db_util.connect_collection("text_collection")

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
            #processed_image = self._preprocess_image(image)
            
            # Generate description
            description = self.generate_description(image)
            
            # Generate embeddings and store image
            image_id = self._store_image(image, url, description)
            
            return image_id
        except Exception as e:
            raise Exception(f"Failed to process image: {str(e)}")
    
    def generate_description(self, image: Image) -> str:
        try:
            # Ensure image is in RGB mode
            if image.mode != 'RGB':
                image = image.convert('RGB')
            
            # Use BLIP to generate description
            inputs = self.blip_processor(image, return_tensors="pt")
            
            with torch.no_grad():
                output = self.blip_model.generate(**inputs, max_new_tokens=50)
                description = self.blip_processor.decode(output[0], skip_special_tokens=True)
            
            return description
            
        except Exception as e:
            print(f"Error details: {str(e)}")
            raise Exception(f"Failed to generate description: {str(e)}")
        
        
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
            
        return image_features

    def _preprocess_image(self, image: Image, text = None):
        """Preprocess image and text separately"""
        image_embeddings = None
        text_embeddings = None
        
        # Process the image if provided
        if image is not None:
            image_embeddings = self.extract_image_features(image)
            image_embeddings = image_embeddings.squeeze(0).tolist()

        # Process the text if provided
        if text is not None:
            text_inputs = self.processor(text=[text], return_tensors="pt", padding=True)
            with torch.no_grad():
                text_outputs = self.model.get_text_features(**text_inputs)
                text_embeddings = text_outputs / text_outputs.norm(dim=-1, keepdim=True)
                text_embeddings = text_embeddings.squeeze(0).tolist()

        return image_embeddings, text_embeddings

    def _store_image(self, image: Image, url: str, description: str) -> str:
        """Store image and its metadata in separate collections"""
        try:
            # Generate embeddings
            image_embeddings, text_embeddings = self._preprocess_image(image, description)
            
            # Download original image again for storage
            response = requests.get(url)
            image_bytes = BytesIO(response.content)
            
            # Generate ID and prepare for S3
            image_id = Utilities.generate_uuid()
            image_bytes.filename = f"image_{image_id}.jpg"
            image_bytes.content_type = 'image/jpeg'

            # Upload to S3
            s3_utils = S3Utilities()
            web_link = s3_utils.upload_to_s3(image_bytes)
            
            # Create metadata
            metadata = {
                "image_id": image_id,
                "source_url": url,
                "width": image.size[0],
                "height": image.size[1],
                "description": description,
                "mode": image.mode,
                "path": web_link
            }

            # Store in image collection
            if image_embeddings:
                self.image_collection.add(
                    ids=[image_id],
                    metadatas=[metadata],
                    embeddings=[image_embeddings],
                    documents=[url]
                )
            
            # Store in text collection
            if text_embeddings:
                self.text_collection.add(
                    ids=[image_id],
                    embeddings=[text_embeddings],
                    documents=[description]
                )
            
            return image_id
        except Exception as e:
            raise Exception(f"Error storing image: {str(e)}")
        
    
  
    
    

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
