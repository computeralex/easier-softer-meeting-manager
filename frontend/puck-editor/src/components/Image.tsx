interface ImageProps {
  src: string;
  alt: string;
  caption: string;
  width: 'small' | 'medium' | 'large' | 'full';
  alignment: 'left' | 'center' | 'right';
}

const widthMap = {
  small: '25%',
  medium: '50%',
  large: '75%',
  full: '100%',
};

const alignmentMap = {
  left: 'flex-start',
  center: 'center',
  right: 'flex-end',
};

export function Image({ src, alt, caption, width, alignment }: ImageProps) {
  if (!src) {
    return (
      <div
        className="image-block"
        style={{
          display: 'flex',
          justifyContent: alignmentMap[alignment],
        }}
      >
        <div
          style={{
            width: widthMap[width],
            minWidth: '150px',
            height: '150px',
            backgroundColor: '#e9ecef',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            color: '#6c757d',
            borderRadius: '0.25rem',
          }}
        >
          Add image URL
        </div>
      </div>
    );
  }

  return (
    <figure
      className="image-block"
      style={{
        display: 'flex',
        flexDirection: 'column',
        alignItems: alignmentMap[alignment],
        margin: '1rem 0',
      }}
    >
      <img
        src={src}
        alt={alt}
        style={{
          width: widthMap[width],
          maxWidth: '100%',
          height: 'auto',
          borderRadius: '0.25rem',
        }}
      />
      {caption && (
        <figcaption style={{ marginTop: '0.5rem', color: '#6c757d', fontSize: '0.875rem' }}>
          {caption}
        </figcaption>
      )}
    </figure>
  );
}
