import React from 'react';

interface ImageGalleryProps {
  images: Array<{ url: string; caption?: string }>;
  columns?: number;
}

const ImageGallery: React.FC<ImageGalleryProps> = ({ images, columns = 3 }) => {
  return (
    <div className="image-gallery" style={{ gridTemplateColumns: `repeat(${columns}, 1fr)` }}>
      {images.map((image, index) => (
        <div key={index} className="image-gallery-item">
          <img src={image.url} alt={image.caption || `Image ${index + 1}`} />
          {image.caption && <p className="image-caption">{image.caption}</p>}
        </div>
      ))}
    </div>
  );
};

export default ImageGallery;
