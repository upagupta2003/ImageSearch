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

@app.post("/image/search/url/")
async def search_similar_image_url(image_url: str):
    try:
        results = await search_engine.url_search(image_url)

        return {"results": results}
    except Exception as e:
        return {"status": "error", "message":str(e)}

@app.post("/images/search/image/")
async def search_similar_images(
    image: UploadFile ):
    """Search for similar images using an uploaded image or URL"""
    results = await search_engine.image_search(image)
    return {"results": results}

@app.get("/images/list")
async def get_all_images():
    try:
        images = await search_engine.get_all_images()
        return{"status": "success", "images": images}
    except Exception as e:
        return{"status": "error", "message":str(e)}


@app.delete("/images/delete")
async def delete_image(image_id: str):
    """Delete an image from the index"""
    await search_engine.delete_image(image_id)
    return {"status": "success"}



if __name__ == "__main__":
    
    uvicorn.run(app="main:app", host="0.0.0.0", port=8999, reload=True)