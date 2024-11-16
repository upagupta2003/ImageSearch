# ImageSearch Backend

A powerful image search engine backend built with FastAPI, leveraging state-of-the-art AI models for image processing and similarity search.

## Features

- Image processing and storage with automatic captioning
- Text-based image search using natural language
- Similar image search using image URLs or uploads
- Vector similarity search using ChromaDB
- S3-compatible storage integration
- Automatic image feature extraction and embedding generation

## Architecture

The backend is built using:
- FastAPI for the REST API
- ChromaDB for vector storage and similarity search
- LocalStack/S3 for image storage
- Hugging Face Transformers for AI models

## AI Models Used

### 1. CLIP (Contrastive Language-Image Pre-training)
- Model: `openai/clip-vit-base-patch32`
- Purpose: Generates unified embeddings for both images and text
- Why: CLIP excels at understanding both visual and textual content in a shared embedding space, making it perfect for:
  - Cross-modal similarity search
  - Finding images based on text descriptions
  - Finding similar images

### 2. BLIP (Bootstrapping Language-Image Pre-training)
- Model: `Salesforce/blip-image-captioning-base`
- Purpose: Automatic image captioning and description generation
- Why: BLIP provides high-quality, contextual image descriptions that:
  - Enhance search capabilities
  - Improve metadata quality
  - Enable better natural language understanding of image content

## API Endpoints

### Images
- `POST /images/add` - Add new image via URL
- `GET /images/list` - List all indexed images
- `DELETE /images/delete` - Remove image from index

### Search
- `POST /images/search/text` - Search images using text
- `POST /image/search/url` - Find similar images using URL
- `POST /images/search/image` - Find similar images using upload

## Setup

1. Install dependencies: available in pyproject.toml using poetry.
2. Run the app with `python backend/app/main.py`


