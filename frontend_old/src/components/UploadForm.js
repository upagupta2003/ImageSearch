import React, { useState } from 'react';
import axios from 'axios';

function UploadForm() {
  const [formData, setFormData] = useState({
    title: '',
    description: '',
    tags: '',
    file: null
  });

  const handleInputChange = (e) => {
    const { name, value } = e.target;
    setFormData({
      ...formData,
      [name]: value
    });
  };

  const handleFileChange = (e) => {
    setFormData({
      ...formData,
      file: e.target.files[0]
    });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    const data = new FormData();
    data.append('title', formData.title);
    data.append('description', formData.description);
    data.append('tags', formData.tags.split(',').map(tag => tag.trim()));
    data.append('image', formData.file);

    try {
      await axios.post('http://localhost:5000/api/images/upload', data, {
        headers: {
          'Content-Type': 'multipart/form-data'
        }
      });
      
      // Reset form
      setFormData({
        title: '',
        description: '',
        tags: '',
        file: null
      });
      
      alert('Image uploaded successfully!');
    } catch (error) {
      console.error('Error uploading image:', error);
      alert('Error uploading image');
    }
  };

  return (
    <form onSubmit={handleSubmit} className="upload-form">
      <div>
        <label htmlFor="title">Title:</label>
        <input
          type="text"
          id="title"
          name="title"
          value={formData.title}
          onChange={handleInputChange}
          required
        />
      </div>
      
      <div>
        <label htmlFor="description">Description:</label>
        <textarea
          id="description"
          name="description"
          value={formData.description}
          onChange={handleInputChange}
          required
        />
      </div>
      
      <div>
        <label htmlFor="tags">Tags (comma-separated):</label>
        <input
          type="text"
          id="tags"
          name="tags"
          value={formData.tags}
          onChange={handleInputChange}
          required
        />
      </div>
      
      <div>
        <label htmlFor="file">Image:</label>
        <input
          type="file"
          id="file"
          onChange={handleFileChange}
          accept="image/*"
          required
        />
      </div>
      
      <button type="submit">Upload Image</button>
    </form>
  );
}

export default UploadForm;
