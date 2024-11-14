from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional
from image_processor import ImageProcessor
from search_engine import SearchEngine
import uvicorn

app = FastAPI(title="ImageSearch API")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

image_processor = ImageProcessor()
search_engine = SearchEngine()

@app.post("/images/add")
async def add_image(image_url: str):
    """Add an image to the index using its URL"""
    try:
        image_id = await image_processor.process_image_url(image_url)
        return {"status": "success", "image_id": image_id}
    except Exception as e:
        return {"status": "error", "message": str(e)}

@app.post("/images/search/text")
async def search_by_text(query: str):
    """Search images using natural language text"""
    results = await search_engine.text_search(query)
    return {"results": results}

@app.post("/images/search/similar")
async def search_similar_images(
    image: Optional[UploadFile] = File(None),
    image_url: Optional[str] = None
):
    """Search for similar images using an uploaded image or URL"""
    if image:
        results = await search_engine.image_search(image)
    elif image_url:
        results = await search_engine.url_search(image_url)
    else:
        return {"error": "Either image or image_url must be provided"}
    
    return {"results": results}

@app.delete("/images/delete")
async def delete_image(image_id: str):
    """Delete an image from the index"""
    await search_engine.delete_image(image_id)
    return {"status": "success"}


if __name__ == "__main__":
    
    uvicorn.run(app="main:app", host="0.0.0.0", port=8000, reload=True)