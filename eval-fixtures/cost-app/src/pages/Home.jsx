import theme from '../theme.js';
import t from '../i18n/index.js';

export function Home({ onCreateOrder }) {
  return (
    <main style={{ padding: theme.spacing * 3 }}>
      <h1>{t('home.title')}</h1>
      <button style={{ background: theme.colorPrimary }} onClick={onCreateOrder}>
        {t('home.submit')}
      </button>
    </main>
  );
}
