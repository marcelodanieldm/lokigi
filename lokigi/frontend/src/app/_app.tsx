// _app.tsx para Next.js (estructura tradicional)
import type { AppProps } from 'next/app';
import GlobalLayout from './GlobalLayout';
import '../styles/globals.css';

export default function MyApp({ Component, pageProps }: AppProps) {
  return (
    <GlobalLayout>
      <Component {...pageProps} />
    </GlobalLayout>
  );
}

// Documentación:
// - Coloca este archivo en frontend/src/app/_app.tsx o frontend/src/pages/_app.tsx según tu estructura.
// - Asegúrate de que GlobalLayout y los componentes estén correctamente importados.
// - El layout global aplica ExitIntentModal y SocialProofWidget a toda la app.
