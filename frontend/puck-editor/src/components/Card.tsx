interface CardProps {
  title: string;
  content: string;
  variant: 'default' | 'primary' | 'secondary';
}

const variantStyles = {
  default: {
    border: '1px solid #dee2e6',
    backgroundColor: '#fff',
  },
  primary: {
    border: '2px solid #0d6efd',
    backgroundColor: '#fff',
  },
  secondary: {
    border: '1px solid #dee2e6',
    backgroundColor: '#f8f9fa',
  },
};

export function Card({ title, content, variant }: CardProps) {
  const styles = variantStyles[variant];

  return (
    <div
      className={`card-block ${variant}`}
      style={{
        ...styles,
        borderRadius: '0.5rem',
        padding: '1.5rem',
        margin: '1rem 0',
      }}
    >
      {title && (
        <h3 style={{ margin: '0 0 1rem', fontSize: '1.25rem' }}>{title}</h3>
      )}
      <div>
        {content.split('\n').map((line, index) => (
          <p key={index} style={{ margin: index === 0 ? 0 : '0.5rem 0 0' }}>
            {line}
          </p>
        ))}
      </div>
    </div>
  );
}
