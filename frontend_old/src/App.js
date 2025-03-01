import React, { useState } from 'react';
import ImageGallery from './components/ImageGallery';
import SearchBar from './components/SearchBar';
import ImageUrlSearch from './components/ImageUrlSearch';
import ImageUploadSearch from './components/ImageUploadSearch';
import './App.css';

function App() {
  const [searchResults, setSearchResults] = useState(null);
  const [searchQuery, setSearchQuery] = useState('');

  const handleSearch = (query) => {
    setSearchQuery(query);
    setSearchResults(null);
  };

  const handleSearchResults = (results) => {
    setSearchResults(results);
    setSearchQuery('');
  };

  return (
    <div className="App">
      <header className="App-header">
        <h1>Image Search</h1>
      </header>
      <main>
        <SearchBar onSearch={handleSearch} />
        <ImageUrlSearch onSearchResults={handleSearchResults} />
        <ImageUploadSearch onSearchResults={handleSearchResults} />
        <ImageGallery 
          searchQuery={searchQuery} 
          searchResults={searchResults}
        />
      </main>
    </div>
  );
}

export default App;
