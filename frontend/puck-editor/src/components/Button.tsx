interface ButtonProps {
  text: string;
  url: string;
  variant: 'primary' | 'secondary' | 'outline';
  alignment: 'left' | 'center' | 'right';
  puck?: { isEditing: boolean };
}

const variantStyles = {
  primary: {
    backgroundColor: '#0d6efd',
    color: '#fff',
    border: 'none',
  },
  secondary: {
    backgroundColor: '#6c757d',
    color: '#fff',
    border: 'none',
  },
  outline: {
    backgroundColor: 'transparent',
    color: '#0d6efd',
    border: '2px solid #0d6efd',
  },
};

const alignmentMap = {
  left: 'flex-start',
  center: 'center',
  right: 'flex-end',
};

export function Button({ text, url, variant, alignment, puck }: ButtonProps) {
  const styles = variantStyles[variant];
  const isEditing = puck?.isEditing;

  return (
    <div
      className="button-block"
      style={{
        display: 'flex',
        justifyContent: alignmentMap[alignment],
        padding: '1rem 0',
      }}
    >
      <a
        href={isEditing ? undefined : url}
        onClick={isEditing ? (e) => e.preventDefault() : undefined}
        className={variant}
        style={{
          ...styles,
          display: 'inline-block',
          padding: '0.75rem 1.5rem',
          borderRadius: '0.375rem',
          textDecoration: 'none',
          fontWeight: 500,
          cursor: isEditing ? 'default' : 'pointer',
        }}
      >
        {text}
      </a>
    </div>
  );
}
