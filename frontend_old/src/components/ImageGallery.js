import React, { useState, useEffect } from 'react';
import { imageApi } from '../services/api';

function ImageGallery({ searchQuery, searchResults }) {
  const [images, setImages] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  // Helper function to get S3 image URL
  const getS3ImageUrl = (s3Path) => {
    // Assuming s3Path is in the format: 's3://bucket-name/path/to/image.jpg'
    if (!s3Path) return '';
    
    // Remove 's3://' prefix and split into bucket and key
    const path = s3Path.replace('s3://', '');
    const [bucket, ...keyParts] = path.split('/');
    const key = keyParts.join('/');
    
    // Construct the public S3 URL
    // Make sure to replace 'your-region' with your actual AWS region
    return `https://${bucket}.s3.your-region.amazonaws.com/${key}`;
  };

  useEffect(() => {
    const fetchImages = async () => {
      setLoading(true);
      try {
        let response;
        if (searchResults) {
          setImages(searchResults);
        } else if (searchQuery) {
          response = await imageApi.searchByText(searchQuery);
          setImages(response.data.results);
        } else {
          response = await imageApi.getAllImages();
          setImages(response.data.images);
        }
        setError(null);
      } catch (error) {
        console.error('Error fetching images:', error);
        setError('Failed to fetch images');
      } finally {
        setLoading(false);
      }
    };

    fetchImages();
  }, [searchQuery, searchResults]);

  if (loading) return <div className="loading">Loading images...</div>;
  if (error) return <div className="error">{error}</div>;
  if (!images.length) return <div className="no-results">No images found</div>;

  return (
    <div className="image-gallery">
      {images.map((image) => (
        <div key={image.id || image._id} className="image-card">
          <img 
            src={getS3ImageUrl(image.s3_path || image.url)} 
            alt={image.title || 'Image'} 
            onError={(e) => {
              e.target.onerror = null;
              e.target.src = '/placeholder-image.png'; // Add a placeholder image
            }}
          />
          <div className="image-info">
            {image.title && <h3>{image.title}</h3>}
            {image.description && <p>{image.description}</p>}
            {image.tags && <p className="tags">Tags: {Array.isArray(image.tags) ? image.tags.join(', ') : image.tags}</p>}
            {image.similarity_score && (
              <p className="similarity">Similarity: {(image.similarity_score * 100).toFixed(2)}%</p>
            )}
          </div>
        </div>
      ))}
    </div>
  );
}

export default ImageGallery;
