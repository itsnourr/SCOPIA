import React, { useState, useEffect, useRef } from "react";
import { Galleria } from "primereact/galleria";
import { Toast } from "primereact/toast";
import { useParams } from "react-router-dom";
import 'primereact/resources/themes/saga-blue/theme.css';
import 'primereact/resources/primereact.min.css';
import 'primeicons/primeicons.css';
import './GalleryScreen.css';

export default function GalleryScreen() {

  const { id } = useParams(); // TODO: refactor id to key
  const [images, setImages] = useState([]);
  const [imageMetadata, setImageMetadata] = useState([]); // Store image metadata with filepath
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [uploading, setUploading] = useState(false);
  const [uploadError, setUploadError] = useState(null);
  const [uploadSuccess, setUploadSuccess] = useState(false);
  const fileInputRef = useRef(null);
  const toast = useRef(null);

  const fetchImages = async () => {
    if (!id) {
      setError('No case ID provided');
      setLoading(false);
      return;
    }

    try {
      setLoading(true);
      setError(null);

      const listResponse = await fetch(`/api/image/list/${id}`, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
        },
      });

      if (!listResponse.ok) {
        throw new Error(`Failed to fetch image list! status: ${listResponse.status}`);
      }

      const imageListData = await listResponse.json();
      console.log('Image list API response:', imageListData);

      const imageItems = Array.isArray(imageListData)
        ? imageListData.filter(item => item.viewUrl != null)
        : [];

      // Store metadata for error handling
      setImageMetadata(imageItems);

      const imageUrls = imageItems.map(item => {
        // Convert full URL to proxy path to avoid SSL/CORS issues
        // viewUrl: "https://localhost:8443/api/image/view/3" -> "/api/image/view/3"
        return item.viewUrl.replace(/^https?:\/\/[^/]+/, '');
      });

      console.log('Image URLs to display:', imageUrls);
      setImages(imageUrls);
    } catch (err) {
      console.error('Error fetching images:', err);
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchImages();
  }, [id]);


  const handleUploadClick = () => {
    fileInputRef.current?.click();
  };

  const handleFileSelect = async (event) => {
    const file = event.target.files[0];

    if (!file) {
      return;
    }

    if (!id) {
      setUploadError('No case ID available');
      return;
    }

    try {
      setUploading(true);
      setUploadError(null);
      setUploadSuccess(false);

      // Create FormData to send file and caseId
      const formData = new FormData();
      formData.append('file', file);
      formData.append('caseId', id);

      // Upload file to API
      const response = await fetch('/api/image/upload', {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) {
        throw new Error(`Upload failed! status: ${response.status}`);
      }

      const result = await response.json();
      console.log('Upload successful:', result);

      setUploadSuccess(true);

      // Refresh images list after successful upload
      await fetchImages();

      // Reset file input
      event.target.value = '';

      // Clear success message after 3 seconds
      setTimeout(() => {
        setUploadSuccess(false);
      }, 3000);
    } catch (err) {
      console.error('Error uploading file:', err);
      setUploadError(err.message);
      event.target.value = '';
    } finally {
      setUploading(false);
    }
  };

  const handleImageError = async (event, imageUrl) => {
    // Try to fetch the image to check the status code
    try {
      const response = await fetch(imageUrl, { method: 'HEAD' });

      if (response.status === 403) {
        // Find the image metadata by matching the URL
        const imageItem = imageMetadata.find(item => {
          const proxyPath = item.viewUrl.replace(/^https?:\/\/[^/]+/, '');
          return proxyPath === imageUrl;
        });

        const filepath = imageItem?.filepath || 'unknown';

        toast.current?.show({
          severity: 'error',
          summary: 'Image Tampering Detected',
          detail: `Image with path "${filepath}" has been tampered with, contact your administrator`,
          life: 5000
        });
      }
    } catch (err) {
      // If we can't check the status, still try to show the error if it's likely a 403
      const imageItem = imageMetadata.find(item => {
        const proxyPath = item.viewUrl.replace(/^https?:\/\/[^/]+/, '');
        return proxyPath === imageUrl;
      });

      if (imageItem) {
        toast.current?.show({
          severity: 'error',
          summary: 'Image Tampering Detected',
          detail: `Image with path "${imageItem.filepath || 'unknown'}" has been tampered with, contact your administrator`,
          life: 5000
        });
      }
    }
  };

  // Main image template
  const itemTemplate = (item) => {
    return (
      <img
        src={item}
        alt="Case"
        style={{ width: '100%', height: '500px', objectFit: 'cover' }}
        onError={(e) => handleImageError(e, item)}
      />
    );
  };

  // Thumbnail template (optional, required for display in many PrimeReact versions)
  const thumbnailTemplate = (item) => {
    return (
      <img
        src={item}
        alt="Thumbnail"
        style={{ width: '100%', height: '100px', objectFit: 'cover' }}
        onError={(e) => handleImageError(e, item)}
      />
    );
  };

  return (
    <div className="p-4">
      <Toast ref={toast} />
      <div className="flex justify-between items-center mb-4">
        <h1 className="text-3xl font-semibold">Gallery</h1>
        <div>
          <button
            onClick={handleUploadClick}
            className="p-button p-component p-button-primary"
            disabled={uploading}
          >
            {uploading ? 'Uploading...' : 'Upload Image'}
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

      {uploadSuccess && (
        <p className="text-green-500 mb-2">Image uploaded successfully!</p>
      )}
      {uploadError && (
        <p className="text-red-500 mb-2">Upload error: {uploadError}</p>
      )}

      {loading && <p>Loading images...</p>}

      {error && <p className="text-red-500">Error loading images: {error}</p>}

      {!loading && !error && images.length === 0 && (
        <p>No images found for this case.</p>
      )}

      {!loading && !error && images.length > 0 && (
        <Galleria
          value={images}
          circular
          showThumbnails
          numVisible={5}
          item={itemTemplate}
          thumbnail={thumbnailTemplate}
          className="custom-galleria"
          style={{ maxWidth: '800px', margin: 'auto' }}
        />
      )}
    </div>
  );
}