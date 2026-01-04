import { useState, useRef } from 'react';

interface ImageUploadFieldProps {
  value: string;
  onChange: (value: string) => void;
  field: {
    label?: string;
  };
}

export function ImageUploadField({ value, onChange }: ImageUploadFieldProps) {
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const { uploadUrl, csrfToken } = window.PUCK_CONFIG;

  const handleFileSelect = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    setUploading(true);
    setError(null);

    const formData = new FormData();
    formData.append('file', file);

    try {
      const response = await fetch(uploadUrl, {
        method: 'POST',
        headers: {
          'X-CSRFToken': csrfToken,
        },
        body: formData,
      });

      const result = await response.json();

      if (result.success) {
        onChange(result.url);
      } else {
        setError(result.error || 'Upload failed');
      }
    } catch (err) {
      setError('Upload failed. Please try again.');
    } finally {
      setUploading(false);
    }
  };

  const handleClear = () => {
    onChange('');
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
      {value ? (
        <div style={{ position: 'relative' }}>
          <img
            src={value}
            alt="Uploaded"
            style={{
              width: '100%',
              maxHeight: '150px',
              objectFit: 'cover',
              borderRadius: '4px',
              border: '1px solid #e1e1e1',
            }}
          />
          <button
            onClick={handleClear}
            style={{
              position: 'absolute',
              top: '4px',
              right: '4px',
              background: 'rgba(0,0,0,0.6)',
              color: 'white',
              border: 'none',
              borderRadius: '50%',
              width: '24px',
              height: '24px',
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              fontSize: '14px',
            }}
            title="Remove image"
          >
            ×
          </button>
        </div>
      ) : null}

      <div style={{ display: 'flex', gap: '8px' }}>
        <input
          ref={fileInputRef}
          type="file"
          accept="image/*"
          onChange={handleFileSelect}
          disabled={uploading}
          style={{ display: 'none' }}
          id="puck-image-upload"
        />
        <button
          onClick={() => fileInputRef.current?.click()}
          disabled={uploading}
          style={{
            flex: 1,
            padding: '8px 12px',
            background: '#f0f0f0',
            border: '1px solid #d1d1d1',
            borderRadius: '4px',
            cursor: uploading ? 'wait' : 'pointer',
            fontSize: '13px',
          }}
        >
          {uploading ? 'Uploading...' : value ? 'Change Image' : 'Upload Image'}
        </button>
      </div>

      {error && (
        <div style={{ color: '#dc3545', fontSize: '12px' }}>
          {error}
        </div>
      )}

      {/* Fallback URL input */}
      <input
        type="text"
        value={value}
        onChange={(e) => onChange(e.target.value)}
        placeholder="Or paste image URL..."
        style={{
          padding: '6px 8px',
          border: '1px solid #d1d1d1',
          borderRadius: '4px',
          fontSize: '12px',
        }}
      />
    </div>
  );
}
