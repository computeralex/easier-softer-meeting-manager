import { DropZone } from '@measured/puck';

interface TwoColumnProps {
  leftWidth: number;
  gap: 'none' | 'small' | 'medium' | 'large';
}

const gapMap = {
  none: '0',
  small: '1rem',
  medium: '2rem',
  large: '3rem',
};

export function TwoColumn({ leftWidth, gap }: TwoColumnProps) {
  const rightWidth = 100 - leftWidth;

  return (
    <div
      className="two-column"
      style={{
        display: 'flex',
        gap: gapMap[gap],
      }}
    >
      <div style={{ flex: `0 0 ${leftWidth}%`, minHeight: '100px' }}>
        <DropZone zone="left" />
      </div>
      <div style={{ flex: `0 0 ${rightWidth}%`, minHeight: '100px' }}>
        <DropZone zone="right" />
      </div>
    </div>
  );
}
