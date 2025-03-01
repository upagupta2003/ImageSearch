import streamlit as st
import requests
import json
from PIL import Image
import io

# Constants
API_BASE_URL = "http://localhost:8999"  # Update with your API URL

def upload_image_url():
    """Add an image to the index using URL"""
    url = st.text_input("Enter image URL")
    if url and st.button("Upload Image"):
        response = requests.post(f"{API_BASE_URL}/images/add", params={"image_url": url})
        if response.status_code == 200:
            st.success("Image uploaded successfully!")
            st.json(response.json())
        else:
            st.error("Failed to upload image")

def search_by_text():
    """Search images using text query"""
    query = st.text_input("Enter search query")
    if query and st.button("Search"):
        response = requests.post(f"{API_BASE_URL}/images/search/text", params={"query": query})
        if response.status_code == 200:
            results = response.json().get("results", {}).get("results", [])
            display_results(results)
        else:
            st.error("Search failed")

def search_by_url():
    """Search using image URL"""
    url = st.text_input("Enter image URL for similarity search")
    if url and st.button("Search Similar Images"):
        response = requests.post(f"{API_BASE_URL}/image/search/url/", params={"image_url": url})
        if response.status_code == 200:
            results = response.json().get("results", [])
            display_results(results)
        else:
            st.error("Search failed")

def display_results(results):
    """Display search results in a grid"""
    if not results:
        st.write("No results found")
        return

    # Create columns for grid display
    cols = st.columns(3)
    for idx, result in enumerate(results):
        col = cols[idx % 3]
        with col:
            # Display image
            s3_url = result.get('s3_url')
            if s3_url:
                st.image(s3_url, use_column_width=True)
            
            # Display metadata
            similarity = result.get('similarity_score', 0)
            st.write(f"Similarity: {similarity}%")
            
            # Display description if available
            metadata = result.get('metadata', {})
            if 'description' in metadata:
                st.write(f"Description: {metadata['description']}")
            
            # Add delete button
            if st.button(f"Delete", key=f"delete_{result['id']}"):
                delete_image(result['id'])

def delete_image(image_id):
    """Delete an image from the index"""
    response = requests.delete(f"{API_BASE_URL}/images/delete", params={"image_id": image_id})
    if response.status_code == 200:
        st.success("Image deleted successfully!")
        st.experimental_rerun()
    else:
        st.error("Failed to delete image")

def view_all_images():
    """Display all images in the database"""
    response = requests.get(f"{API_BASE_URL}/images/list")
    if response.status_code == 200:
        images = response.json()
        display_results(images)
    else:
        st.error("Failed to fetch images")

def main():
    st.title("Image Search Engine")
    
    # Sidebar navigation
    page = st.sidebar.selectbox(
        "Choose a function",
        ["Upload Image", "Text Search", "Image URL Search", "View All Images"]
    )
    
    # Main content
    if page == "Upload Image":
        st.header("Upload Image")
        upload_image_url()
    
    elif page == "Text Search":
        st.header("Search by Text")
        search_by_text()
    
    elif page == "Image URL Search":
        st.header("Search by Image URL")
        search_by_url()
    
    elif page == "View All Images":
        st.header("All Images")
        view_all_images()

if __name__ == "__main__":
    main()
