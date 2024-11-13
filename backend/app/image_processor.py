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
        return google_drive_upload(image)
    
    
    

if __name__ == "__main__":
    image_processor = ImageProcessor()
    print(image_processor.model)
