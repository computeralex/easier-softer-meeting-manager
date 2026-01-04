import { Fragment } from 'react';

interface TextProps {
  content: string;
  alignment: 'left' | 'center' | 'right';
}

export function Text({ content, alignment }: TextProps) {
  // Convert newlines to paragraphs for better formatting
  const paragraphs = content.split('\n\n').filter(p => p.trim());

  return (
    <div className="text-block" style={{ textAlign: alignment }}>
      {paragraphs.length > 0 ? (
        paragraphs.map((para, index) => (
          <p key={index} style={{ marginBottom: '1rem' }}>
            {para.split('\n').map((line, lineIndex) => (
              <Fragment key={lineIndex}>
                {line}
                {lineIndex < para.split('\n').length - 1 && <br />}
              </Fragment>
            ))}
          </p>
        ))
      ) : (
        <p style={{ color: '#999' }}>Enter your text...</p>
      )}
    </div>
  );
}
