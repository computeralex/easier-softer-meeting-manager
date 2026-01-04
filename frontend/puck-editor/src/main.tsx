import { StrictMode } from 'react';
import ReactDOM from 'react-dom/client';
import { Puck, Data, usePuck } from '@measured/puck';
import '@measured/puck/puck.css';
import { config } from './config/puck-config';
import './styles.css';

declare global {
  interface Window {
    PUCK_CONFIG: {
      pageId: number | null;
      initialData: Data;
      saveUrl: string;
      csrfToken: string;
      backUrl: string;
      uploadUrl: string;
    };
  }
}

function SaveButton({ onSave }: { onSave: (data: Data) => void }) {
  const { appState } = usePuck();

  return (
    <button
      onClick={() => onSave(appState.data)}
      style={{
        padding: '8px 16px',
        background: '#4a6fa5',
        color: 'white',
        border: '1px solid #4a6fa5',
        borderRadius: '4px',
        cursor: 'pointer',
        fontSize: '14px',
        fontWeight: 500,
        lineHeight: '1.5',
      }}
    >
      Save
    </button>
  );
}

function App() {
  const { initialData, saveUrl, csrfToken, backUrl } = window.PUCK_CONFIG;

  const handleSave = async (data: Data) => {
    try {
      const response = await fetch(saveUrl, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-CSRFToken': csrfToken,
        },
        body: JSON.stringify(data),
      });

      if (response.ok) {
        const result = await response.json();
        if (result.redirect) {
          window.location.href = result.redirect;
        }
      } else {
        alert('Failed to save page. Please try again.');
      }
    } catch (error) {
      console.error('Save error:', error);
      alert('Failed to save page. Please try again.');
    }
  };

  const handleCancel = () => {
    if (confirm('Discard unsaved changes?')) {
      window.location.href = backUrl;
    }
  };

  return (
    <Puck
      config={config}
      data={initialData}
      overrides={{
        headerActions: () => (
          <>
            <button
              onClick={handleCancel}
              style={{
                padding: '8px 16px',
                marginRight: '8px',
                background: 'transparent',
                border: '1px solid #ccc',
                borderRadius: '4px',
                cursor: 'pointer',
                fontSize: '14px',
                fontWeight: 500,
                lineHeight: '1.5',
              }}
            >
              Cancel
            </button>
            <SaveButton onSave={handleSave} />
          </>
        ),
      }}
    />
  );
}

const rootElement = document.getElementById('puck-root');
if (rootElement) {
  ReactDOM.createRoot(rootElement).render(
    <StrictMode>
      <App />
    </StrictMode>
  );
}
