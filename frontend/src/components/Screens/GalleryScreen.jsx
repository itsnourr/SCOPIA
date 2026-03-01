import React, { useState, useEffect, useRef } from "react";
import { Galleria } from "primereact/galleria";
import { Toast } from "primereact/toast";
import { useParams } from "react-router-dom";
import 'primereact/resources/themes/saga-blue/theme.css';
import 'primereact/resources/primereact.min.css';
import 'primeicons/primeicons.css';
import './GalleryScreen.css';

export default function GalleryScreen() {

  const { caseKey } = useParams(); // TODO: refactor caseKey to key
  const [images, setImages] = useState([]);
  const [imageMetadata, setImageMetadata] = useState([]); // (kept for legacy API approach)
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [uploading, setUploading] = useState(false);
  const [uploadError, setUploadError] = useState(null);
  const [uploadSuccess, setUploadSuccess] = useState(false);
  const fileInputRef = useRef(null);
  const toast = useRef(null);

  /*
  ==============================
  OLD BACKEND API APPROACH (COMMENTED OUT)
  ==============================

  const fetchImages = async () => {
    if (!caseKey) {
      setError('No case caseKey provided');
      setLoading(false);
      return;
    }

    try {
      setLoading(true);
      setError(null);

      const listResponse = await fetch(`/api/image/list/${caseKey}`, {
        method: 'GET',
        headers: { 'Content-Type': 'application/json' },
      });

      if (!listResponse.ok) {
        throw new Error(`Failed to fetch image list! status: ${listResponse.status}`);
      }

      const imageListData = await listResponse.json();

      const imageItems = Array.isArray(imageListData)
        ? imageListData.filter(item => item.viewUrl != null)
        : [];

      setImageMetadata(imageItems);

      const imageUrls = imageItems.map(item =>
        item.viewUrl.replace(/^https?:\/\/[^/]+/, '')
      );

      setImages(imageUrls);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };
  */

  /*
  ==============================
  NEW PUBLIC FOLDER APPROACH
  Predictable naming: 1.jpg, 2.jpg, 3.jpg...
  Folder: /public/cases/{caseKey}/images/
  ==============================
  */

  useEffect(() => {
    const loadImages = async () => {
      if (!caseKey) {
        setError("No case key provided");
        setLoading(false);
        return;
      }

      setLoading(true);
      setError(null);

      const MAX_IMAGES = 100; // Safe upper bound
      const validImages = [];

      for (let i = 1; i <= MAX_IMAGES; i++) {
        const url = `/cases/${caseKey}/images/${i}.JPG`;

        try {
          const res = await fetch(url, { method: "HEAD" });
          if (res.ok) {
            validImages.push(url);
          } else {
            break; // Stop when numbering ends
          }
        } catch {
          break;
        }
      }

      setImages(validImages);
      setLoading(false);
    };

    loadImages();
  }, [caseKey]);

  const handleUploadClick = () => {
    fileInputRef.current?.click();
  };

  const handleFileSelect = async (event) => {
    const file = event.target.files[0];
    if (!file || !caseKey) return;

    try {
      setUploading(true);
      setUploadError(null);
      setUploadSuccess(false);

      const formData = new FormData();
      formData.append('file', file);
      formData.append('caseId', caseKey);

      const response = await fetch('/api/image/upload', {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) {
        throw new Error(`Upload failed! status: ${response.status}`);
      }

      setUploadSuccess(true);

      // Optional: reload predictable list
      window.location.reload();

      event.target.value = '';

      setTimeout(() => {
        setUploadSuccess(false);
      }, 3000);

    } catch (err) {
      setUploadError(err.message);
      event.target.value = '';
    } finally {
      setUploading(false);
    }
  };

  const itemTemplate = (item) => (
    <img
      src={item}
      alt="Case"
      style={{ width: '100%', height: '500px', objectFit: 'cover' }}
    />
  );

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

      {/* <h1 className="screen-title" style={{ paddingBottom: "0px", marginBottom: "0px" }}>Gallery</h1> */}

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

        <div>
          <button
            onClick={handleUploadClick}
            className="p-button p-component p-button-primary"
            disabled={uploading}
            style={{ backgroundColor: "grey", color: "white", marginTop: "0px"}}
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

    </div>
  );
}