import { useEffect, useState } from 'react';

export type Language = 'pt' | 'es' | 'en';

interface LanguageDetectionResult {
  language: Language;
  country: string | null;
  detectedFrom: 'browser' | 'ip' | 'default';
}

// Mapeo de códigos de idioma del navegador a nuestros códigos
const LANGUAGE_MAP: Record<string, Language> = {
  'pt': 'pt',
  'pt-BR': 'pt',
  'pt-PT': 'pt',
  'es': 'es',
  'es-ES': 'es',
  'es-MX': 'es',
  'es-AR': 'es',
  'es-CO': 'es',
  'es-CL': 'es',
  'en': 'en',
  'en-US': 'en',
  'en-GB': 'en',
};

// Mapeo de países a idiomas
const COUNTRY_LANGUAGE_MAP: Record<string, Language> = {
  'BR': 'pt',
  'PT': 'pt',
  'AR': 'es',
  'MX': 'es',
  'CO': 'es',
  'CL': 'es',
  'ES': 'es',
  'US': 'en',
  'GB': 'en',
  'CA': 'en',
};

/**
 * Hook para detectar automáticamente el idioma del usuario
 * Prioridad: 1) Browser language, 2) Backend IP detection, 3) Default (en)
 */
export function useLanguageDetection(): LanguageDetectionResult {
  const [result, setResult] = useState<LanguageDetectionResult>({
    language: 'en',
    country: null,
    detectedFrom: 'default',
  });

  useEffect(() => {
    detectLanguage();
  }, []);

  const detectLanguage = async () => {
    // 1. Intentar detectar del navegador primero (más rápido)
    const browserLang = detectBrowserLanguage();
    if (browserLang) {
      setResult({
        language: browserLang,
        country: null,
        detectedFrom: 'browser',
      });
      return;
    }

    // 2. Si no se detectó del navegador, consultar backend para detección por IP
    try {
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/detect-language`, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
        },
      });

      if (response.ok) {
        const backendLang = response.headers.get('X-Detected-Language');
        const backendCountry = response.headers.get('X-Detected-Country');
        
        if (backendLang && ['pt', 'es', 'en'].includes(backendLang)) {
          setResult({
            language: backendLang as Language,
            country: backendCountry,
            detectedFrom: 'ip',
          });
          return;
        }
      }
    } catch (error) {
      console.warn('IP-based language detection failed:', error);
    }

    // 3. Default: inglés
    setResult({
      language: 'en',
      country: null,
      detectedFrom: 'default',
    });
  };

  return result;
}

/**
 * Detecta idioma desde las preferencias del navegador
 */
function detectBrowserLanguage(): Language | null {
  if (typeof window === 'undefined') return null;

  const browserLangs = navigator.languages || [navigator.language];
  
  for (const lang of browserLangs) {
    // Buscar coincidencia exacta
    if (LANGUAGE_MAP[lang]) {
      return LANGUAGE_MAP[lang];
    }
    
    // Buscar coincidencia por código base (ej: 'pt' en 'pt-BR')
    const baseLang = lang.split('-')[0];
    if (LANGUAGE_MAP[baseLang]) {
      return LANGUAGE_MAP[baseLang];
    }
  }

  return null;
}

/**
 * Obtiene idioma desde localStorage (preferencia manual del usuario)
 */
export function getStoredLanguage(): Language | null {
  if (typeof window === 'undefined') return null;
  const stored = localStorage.getItem('lokigi-language');
  return stored && ['pt', 'es', 'en'].includes(stored) ? stored as Language : null;
}

/**
 * Guarda preferencia de idioma en localStorage
 */
export function setStoredLanguage(language: Language): void {
  if (typeof window === 'undefined') return;
  localStorage.setItem('lokigi-language', language);
}
