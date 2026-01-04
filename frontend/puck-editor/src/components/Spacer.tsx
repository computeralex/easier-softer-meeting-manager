interface SpacerProps {
  height: 'small' | 'medium' | 'large' | 'xlarge';
  showDivider: boolean;
}

const heightMap = {
  small: '1rem',
  medium: '2rem',
  large: '3rem',
  xlarge: '5rem',
};

export function Spacer({ height, showDivider }: SpacerProps) {
  if (showDivider) {
    return (
      <div
        className="spacer-block"
        style={{
          height: heightMap[height],
          display: 'flex',
          alignItems: 'center',
        }}
      >
        <hr
          className="divider-block"
          style={{
            width: '100%',
            border: 'none',
            borderTop: '1px solid #dee2e6',
            margin: 0,
          }}
        />
      </div>
    );
  }

  return (
    <div
      className="spacer-block"
      style={{ height: heightMap[height] }}
    />
  );
}
