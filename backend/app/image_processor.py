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
        """Preprocess image for consistency"""
        
        # Initialize embeddings
        image_embeddings = None
        text_embeddings = None
        
        # Process the image if provided
        if image is not None:
            image_embeddings = self.extract_image_features(image)
            # Keep as tensor until final conversion
            image_embeddings = image_embeddings.squeeze(0)

        text = self.generate_description(image)    

        # Process the text if provided
        if text is not None:
            text_inputs = self.processor(text=[text], return_tensors="pt", padding=True)
            with torch.no_grad():
                text_outputs = self.model.get_text_features(**text_inputs)
                text_embeddings = text_outputs / text_outputs.norm(dim=-1, keepdim=True)
                text_embeddings = text_embeddings.squeeze(0)

        # Combine the embeddings if both image and text are provided
        if image_embeddings is not None and text_embeddings is not None:
            combined_embeddings = (image_embeddings + text_embeddings) / 2
            combined_embeddings = combined_embeddings / torch.norm(combined_embeddings)
            return combined_embeddings.tolist()

        # Convert to list at the end
        if image_embeddings is not None:
            return image_embeddings.tolist()
        if text_embeddings is not None:
            return text_embeddings.tolist()

    def _store_image(self, image: Image, url: str, description: str) -> str:
        """Store image and its metadata, return image_id"""
        try:
            # Generate embeddings first
            embeddings = self._preprocess_image(image, description)
            
            # Download original image again for storage
            response = requests.get(url)
            image_bytes = BytesIO(response.content)
            
            # Create a file-like object with necessary attributes
            image_id = Utilities.generate_uuid()
            image_bytes.filename = f"image_{image_id}.jpg"
            image_bytes.content_type = 'image/jpeg'

            # Upload to S3 using LocalStack
            s3_utils = S3Utilities()
            web_link = s3_utils.upload_to_s3(image_bytes)
            
            # Store metadata and embeddings in ChromaDB
            metadata = {
                "image_id": image_id,
                "source_url": url,
                "width": image.size[0],
                "height": image.size[1],
                "description": description,
                "mode": image.mode,
                "path": web_link
            }

            self.collection.add(
                ids=[image_id],
                metadatas=[metadata],
                embeddings=[embeddings],  # Add embeddings here
                documents=[url] 
            )
            
            return image_id
        except Exception as e:
            raise Exception(f"Error storing image: {str(e)}")
    
    def get_image_by_id(self, image_id: str):
        return self.db_util.get_image_by_id(image_id)
    
  
    
    

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
