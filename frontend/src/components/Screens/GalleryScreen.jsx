import React, { useState, useEffect, useRef } from "react";
import { Galleria } from "primereact/galleria";
import { Toast } from "primereact/toast";
import { useParams } from "react-router-dom";
import 'primereact/resources/themes/saga-blue/theme.css';
import 'primereact/resources/primereact.min.css';
import 'primeicons/primeicons.css';
import './GalleryScreen.css';

export default function GalleryScreen() {

  const { caseKey } = useParams(); 
  const [images, setImages] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const [uploading, setUploading] = useState(false);
  const [uploadError, setUploadError] = useState(null);
  const [uploadSuccess, setUploadSuccess] = useState(false);

  const fileInputRef = useRef(null);
  const toast = useRef(null);

  /**
   * Fetch images from backend
   */
  const fetchImages = async () => {
    if (!caseKey) {
      setError("No case key provided");
      setLoading(false);
      return;
    }

    try {
      setLoading(true);
      setError(null);

      const response = await fetch(`http://localhost:8443/api/image/list/${caseKey}`);

      if (!response.ok) {
        throw new Error(`Failed to fetch images (status: ${response.status})`);
      }

      const data = await response.json();

      // Extract view URLs (strip domain if present)
      const imageUrls = (data || [])
        .filter(item => item.viewUrl)
        .map(item =>
          "http://localhost:8443" + item.viewUrl
        );

      setImages(imageUrls);

    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  /**
   * Load images on mount / case change
   */
  useEffect(() => {
    fetchImages();
  }, [caseKey]);

  /**
   * Trigger file input
   */
  const handleUploadClick = () => {
    fileInputRef.current?.click();
  };

  /**
   * Upload image
   */
  const handleFileSelect = async (event) => {
    const file = event.target.files[0];
    if (!file || !caseKey) return;

    try {
      setUploading(true);
      setUploadError(null);
      setUploadSuccess(false);

      const formData = new FormData();
      formData.append("file", file);
      formData.append("caseId", caseKey);

      const response = await fetch("http://localhost:8443/api/image/upload", {
        method: "POST",
        body: formData,
      });

      if (!response.ok) {
        throw new Error(`Upload failed (status: ${response.status})`);
      }

      setUploadSuccess(true);

      // Refresh images without reloading page
      await fetchImages();

      // Reset input
      event.target.value = "";

      setTimeout(() => {
        setUploadSuccess(false);
      }, 3000);

    } catch (err) {
      setUploadError(err.message);
      event.target.value = "";
    } finally {
      setUploading(false);
    }
  };

  /**
   * Galleria item
   */
  const itemTemplate = (item) => (
    <img
      src={item}
      alt="Case"
      style={{ width: '100%', height: '500px', objectFit: 'cover' }}
    />
  );

  /**
   * Thumbnail
   */
  const thumbnailTemplate = (item) => (
    <img
      src={item}
      alt="Thumbnail"
      style={{ width: '100%', height: '100px', objectFit: 'cover' }}
    />
  );

  return (
    <div className="p-4">

      <Toast ref={toast} />

      {uploadSuccess && (
        <p className="text-green-500 mb-2">Image uploaded successfully!</p>
      )}

      {uploadError && (
        <p className="text-red-500 mb-2">Upload error: {uploadError}</p>
      )}

      {loading && <p>Loading images...</p>}

      {error && (
        <p className="text-red-500">Error: {error}</p>
      )}

      {!loading && !error && images.length === 0 && (
        <p>No images found for this case.</p>
      )}

      {!loading && !error && images.length > 0 && (
        <div style={{ transform: 'scale(0.7)', marginTop: "-80px", marginBottom: "-80px" }}>
          <Galleria
            value={images}
            circular
            showThumbnails
            numVisible={5}
            item={itemTemplate}
            thumbnail={thumbnailTemplate}
            className="custom-galleria"
            style={{ maxWidth: '900px', margin: 'auto' }}
          />
        </div>
      )}

      <div className="flex justify-between items-center mb-4">

        <button
          onClick={handleUploadClick}
          className="p-button p-component p-button-primary"
          disabled={uploading}
          style={{ backgroundColor: "grey", color: "white" }}
        >
          {uploading ? "Uploading..." : "Upload Image"}
        </button>

        <input
          type="file"
          ref={fileInputRef}
          style={{ display: "none" }}
          accept="image/*"
          onChange={handleFileSelect}
        />

      </div>

    </div>
  );
}