import type { Config } from '@measured/puck';
import { Hero } from '../components/Hero';
import { Text } from '../components/Text';
import { Image } from '../components/Image';
import { TwoColumn } from '../components/TwoColumn';
import { Card } from '../components/Card';
import { Button } from '../components/Button';
import { Spacer } from '../components/Spacer';
import { ImageUploadField } from '../fields/ImageUploadField';

// Define prop types for each component
type HeroProps = {
  title: string;
  subtitle: string;
  backgroundImage: string;
  alignment: 'left' | 'center' | 'right';
  height: 'small' | 'medium' | 'large';
};

type TextProps = {
  content: string;
  alignment: 'left' | 'center' | 'right';
};

type ImageProps = {
  src: string;
  alt: string;
  caption: string;
  width: 'small' | 'medium' | 'large' | 'full';
  alignment: 'left' | 'center' | 'right';
};

type TwoColumnProps = {
  leftWidth: number;
  gap: 'none' | 'small' | 'medium' | 'large';
};

type CardProps = {
  title: string;
  content: string;
  variant: 'default' | 'primary' | 'secondary';
};

type ButtonProps = {
  text: string;
  url: string;
  variant: 'primary' | 'secondary' | 'outline';
  alignment: 'left' | 'center' | 'right';
};

type SpacerProps = {
  height: 'small' | 'medium' | 'large' | 'xlarge';
  showDivider: boolean;
};

// Combined props type
type Props = {
  Hero: HeroProps;
  Text: TextProps;
  Image: ImageProps;
  TwoColumn: TwoColumnProps;
  Card: CardProps;
  Button: ButtonProps;
  Spacer: SpacerProps;
};

export const config: Config<Props> = {
  categories: {
    layout: {
      title: 'Layout',
      components: ['TwoColumn', 'Spacer'],
    },
    content: {
      title: 'Content',
      components: ['Hero', 'Text', 'Image', 'Card', 'Button'],
    },
  },
  components: {
    Hero: {
      label: 'Hero Section',
      fields: {
        title: {
          type: 'text',
          label: 'Title',
        },
        subtitle: {
          type: 'textarea',
          label: 'Subtitle',
        },
        backgroundImage: {
          type: 'custom',
          label: 'Background Image',
          render: ImageUploadField,
        },
        alignment: {
          type: 'radio',
          label: 'Text Alignment',
          options: [
            { label: 'Left', value: 'left' },
            { label: 'Center', value: 'center' },
            { label: 'Right', value: 'right' },
          ],
        },
        height: {
          type: 'radio',
          label: 'Height',
          options: [
            { label: 'Small', value: 'small' },
            { label: 'Medium', value: 'medium' },
            { label: 'Large', value: 'large' },
          ],
        },
      },
      defaultProps: {
        title: 'Welcome',
        subtitle: '',
        backgroundImage: '',
        alignment: 'center',
        height: 'medium',
      },
      render: Hero,
    },
    Text: {
      label: 'Text Block',
      fields: {
        content: {
          type: 'textarea',
          label: 'Content',
        },
        alignment: {
          type: 'radio',
          label: 'Alignment',
          options: [
            { label: 'Left', value: 'left' },
            { label: 'Center', value: 'center' },
            { label: 'Right', value: 'right' },
          ],
        },
      },
      defaultProps: {
        content: 'Enter your text here...',
        alignment: 'left',
      },
      render: Text,
    },
    Image: {
      label: 'Image',
      fields: {
        src: {
          type: 'custom',
          label: 'Image',
          render: ImageUploadField,
        },
        alt: {
          type: 'text',
          label: 'Alt Text',
        },
        caption: {
          type: 'text',
          label: 'Caption',
        },
        width: {
          type: 'radio',
          label: 'Width',
          options: [
            { label: 'Small (25%)', value: 'small' },
            { label: 'Medium (50%)', value: 'medium' },
            { label: 'Large (75%)', value: 'large' },
            { label: 'Full Width', value: 'full' },
          ],
        },
        alignment: {
          type: 'radio',
          label: 'Alignment',
          options: [
            { label: 'Left', value: 'left' },
            { label: 'Center', value: 'center' },
            { label: 'Right', value: 'right' },
          ],
        },
      },
      defaultProps: {
        src: '',
        alt: '',
        caption: '',
        width: 'full',
        alignment: 'center',
      },
      render: Image,
    },
    TwoColumn: {
      label: 'Two Columns',
      fields: {
        leftWidth: {
          type: 'number',
          label: 'Left Column Width (%)',
          min: 20,
          max: 80,
        },
        gap: {
          type: 'radio',
          label: 'Gap Size',
          options: [
            { label: 'None', value: 'none' },
            { label: 'Small', value: 'small' },
            { label: 'Medium', value: 'medium' },
            { label: 'Large', value: 'large' },
          ],
        },
      },
      defaultProps: {
        leftWidth: 50,
        gap: 'medium',
      },
      render: TwoColumn,
    },
    Card: {
      label: 'Card',
      fields: {
        title: {
          type: 'text',
          label: 'Title',
        },
        content: {
          type: 'textarea',
          label: 'Content',
        },
        variant: {
          type: 'radio',
          label: 'Style',
          options: [
            { label: 'Default', value: 'default' },
            { label: 'Primary', value: 'primary' },
            { label: 'Secondary', value: 'secondary' },
          ],
        },
      },
      defaultProps: {
        title: 'Card Title',
        content: 'Card content goes here...',
        variant: 'default',
      },
      render: Card,
    },
    Button: {
      label: 'Button',
      fields: {
        text: {
          type: 'text',
          label: 'Button Text',
        },
        url: {
          type: 'text',
          label: 'Link URL',
        },
        variant: {
          type: 'radio',
          label: 'Style',
          options: [
            { label: 'Primary', value: 'primary' },
            { label: 'Secondary', value: 'secondary' },
            { label: 'Outline', value: 'outline' },
          ],
        },
        alignment: {
          type: 'radio',
          label: 'Alignment',
          options: [
            { label: 'Left', value: 'left' },
            { label: 'Center', value: 'center' },
            { label: 'Right', value: 'right' },
          ],
        },
      },
      defaultProps: {
        text: 'Click Here',
        url: '#',
        variant: 'primary',
        alignment: 'left',
      },
      render: Button,
    },
    Spacer: {
      label: 'Spacer / Divider',
      fields: {
        height: {
          type: 'radio',
          label: 'Height',
          options: [
            { label: 'Small', value: 'small' },
            { label: 'Medium', value: 'medium' },
            { label: 'Large', value: 'large' },
            { label: 'Extra Large', value: 'xlarge' },
          ],
        },
        showDivider: {
          type: 'radio',
          label: 'Show Divider Line',
          options: [
            { label: 'Yes', value: true },
            { label: 'No', value: false },
          ],
        },
      },
      defaultProps: {
        height: 'medium',
        showDivider: false,
      },
      render: Spacer,
    },
  },
};
