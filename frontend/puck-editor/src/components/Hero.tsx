interface HeroProps {
  title: string;
  subtitle: string;
  backgroundImage: string;
  alignment: 'left' | 'center' | 'right';
  height: 'small' | 'medium' | 'large';
}

const heightMap = {
  small: '200px',
  medium: '350px',
  large: '500px',
};

export function Hero({ title, subtitle, backgroundImage, alignment, height }: HeroProps) {
  const hasBackground = !!backgroundImage;

  return (
    <section
      className={`hero-section ${hasBackground ? 'has-background' : ''}`}
      style={{
        backgroundImage: hasBackground ? `url(${backgroundImage})` : undefined,
        backgroundColor: hasBackground ? undefined : '#f8f9fa',
        textAlign: alignment,
        minHeight: heightMap[height],
        display: 'flex',
        flexDirection: 'column',
        justifyContent: 'center',
      }}
    >
      <h1>{title}</h1>
      {subtitle && <p>{subtitle}</p>}
    </section>
  );
}
