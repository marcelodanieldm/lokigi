'use client';

import { useEffect, useState } from 'react';
import { useLanguageDetection } from '@/hooks/useLanguageDetection';
import { useTranslations } from '@/lib/translations';
interface AnalysisLoaderProps {
  businessName: string;
  onComplete: () => void;
}

type ScanStage = {
  id: number;
  key: string;
  duration: number;
  icon: string;
};

export default function AnalysisLoader({ businessName, onComplete }: AnalysisLoaderProps) {
  const { language } = useLanguageDetection();
  const [currentStage, setCurrentStage] = useState(0);
  const [progress, setProgress] = useState(0);

  // Etapas del análisis técnico (10 segundos total)
  const scanStages: ScanStage[] = [
    { id: 1, key: 'scanning_gmb', duration: 2000, icon: '🔍' },
    { id: 2, key: 'analyzing_competitors', duration: 2000, icon: '📊' },
    { id: 3, key: 'checking_nap', duration: 2000, icon: '📍' },
    { id: 4, key: 'calculating_loss', duration: 2000, icon: '💰' },
    { id: 5, key: 'generating_report', duration: 2000, icon: '📄' },
  ];

  useEffect(() => {
    if (currentStage >= scanStages.length) {
      // Análisis completo
      setTimeout(onComplete, 500);
      return;
    }

    const stage = scanStages[currentStage];
    const progressIncrement = 100 / scanStages.length;
    
    // Animar progreso suavemente
    const progressInterval = setInterval(() => {
      setProgress((prev) => {
        const target = (currentStage + 1) * progressIncrement;
        if (prev >= target) return target;
        return Math.min(prev + 2, target);
      });
    }, 50);

    // Avanzar a siguiente etapa
    const stageTimeout = setTimeout(() => {
      setCurrentStage((prev) => prev + 1);
    }, stage.duration);

    return () => {
      clearInterval(progressInterval);
      clearTimeout(stageTimeout);
    };
  }, [currentStage, scanStages.length, onComplete]);

  const getCurrentStageText = () => {
    if (currentStage >= scanStages.length) {
      return getTranslation(language, 'analysis_complete');
    }
    return getTranslation(language, scanStages[currentStage].key);
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-dark-900 via-dark-800 to-dark-900 p-4">
      <div className="w-full max-w-2xl">
        {/* Logo o Título */}
        <div className="text-center mb-12">
          <h1 className="text-4xl font-bold text-white mb-2">
            Lokigi <span className="text-primary">Score</span>
          </h1>
          <p className="text-gray-400 text-lg">
            {getTranslation(language, 'analyzing_business')}: <span className="text-white font-semibold">{businessName}</span>
          </p>
        </div>

        {/* Radar / Scanner Visual */}
        <div className="relative mb-8">
          <div className="scanner-container">
            <div className="scanner-ring scanner-ring-1"></div>
            <div className="scanner-ring scanner-ring-2"></div>
            <div className="scanner-ring scanner-ring-3"></div>
            <div className="scanner-line"></div>
            
            {/* Centro del radar */}
            <div className="absolute inset-0 flex items-center justify-center">
              <div className="text-6xl animate-pulse">
                {currentStage < scanStages.length ? scanStages[currentStage].icon : '✅'}
              </div>
            </div>
          </div>
        </div>

        {/* Barra de progreso */}
        <div className="mb-8">
          <div className="flex justify-between items-center mb-2">
            <span className="text-sm text-gray-400">
              {getTranslation(language, 'progress')}
            </span>
            <span className="text-sm font-mono text-primary">
              {Math.round(progress)}%
            </span>
          </div>
          <div className="h-2 bg-dark-700 rounded-full overflow-hidden">
            <div 
              className="h-full bg-gradient-to-r from-primary via-cyan-400 to-primary transition-all duration-300 ease-out"
              style={{ width: `${progress}%` }}
            />
          </div>
        </div>

        {/* Etapa actual */}
        <div className="bg-dark-800 border border-dark-700 rounded-lg p-6">
          <div className="flex items-center space-x-3 mb-4">
            <div className="w-2 h-2 bg-primary rounded-full animate-pulse"></div>
            <h3 className="text-primary font-semibold uppercase text-sm tracking-wider">
              {getTranslation(language, 'current_stage')}
            </h3>
          </div>
          <p className="text-white text-lg font-medium">
            {getCurrentStageText()}
          </p>
        </div>

        {/* Lista de etapas completadas */}
        <div className="mt-6 space-y-2">
          {scanStages.map((stage, index) => {
            const isCompleted = index < currentStage;
            const isCurrent = index === currentStage;
            
            return (
              <div
                key={stage.id}
                className={`flex items-center space-x-3 px-4 py-2 rounded-lg transition-all duration-300 ${
                  isCompleted
                    ? 'bg-dark-800/50 text-primary'
                    : isCurrent
                    ? 'bg-dark-800 text-white border border-primary/30'
                    : 'text-gray-600'
                }`}
              >
                <span className="text-xl">{stage.icon}</span>
                <span className="text-sm flex-1">
                  {getTranslation(language, stage.key)}
                </span>
                {isCompleted && (
                  <span className="text-primary">✓</span>
                )}
                {isCurrent && (
                  <div className="flex space-x-1">
                    <span className="w-1 h-1 bg-primary rounded-full animate-bounce" style={{ animationDelay: '0ms' }}></span>
                    <span className="w-1 h-1 bg-primary rounded-full animate-bounce" style={{ animationDelay: '150ms' }}></span>
                    <span className="w-1 h-1 bg-primary rounded-full animate-bounce" style={{ animationDelay: '300ms' }}></span>
                  </div>
                )}
              </div>
            );
          })}
        </div>

        {/* Mensaje técnico (añade credibilidad) */}
        <div className="mt-8 text-center">
          <p className="text-xs text-gray-500 font-mono">
            {getTranslation(language, 'technical_analysis')}
          </p>
        </div>
      </div>

      <style jsx>{`
        .scanner-container {
          position: relative;
          width: 300px;
          height: 300px;
          margin: 0 auto;
        }

        .scanner-ring {
          position: absolute;
          inset: 0;
          border: 2px solid rgba(0, 255, 65, 0.3);
          border-radius: 50%;
          animation: pulse-ring 2s ease-out infinite;
        }

        .scanner-ring-1 {
          animation-delay: 0s;
        }

        .scanner-ring-2 {
          animation-delay: 0.4s;
        }

        .scanner-ring-3 {
          animation-delay: 0.8s;
        }

        .scanner-line {
          position: absolute;
          inset: 20px;
          border-radius: 50%;
          background: conic-gradient(
            from 0deg,
            transparent 0deg,
            transparent 270deg,
            rgba(0, 255, 65, 0.8) 270deg,
            rgba(0, 255, 65, 0.4) 360deg
          );
          animation: rotate-scanner 2s linear infinite;
        }

        @keyframes pulse-ring {
          0% {
            transform: scale(0.95);
            opacity: 1;
          }
          50% {
            transform: scale(1.05);
            opacity: 0.5;
          }
          100% {
            transform: scale(0.95);
            opacity: 1;
          }
        }

        @keyframes rotate-scanner {
          0% {
            transform: rotate(0deg);
          }
          100% {
            transform: rotate(360deg);
          }
        }
      `}</style>
    </div>
  );
}
interface AnalysisLoaderProps {
  businessName: string;
  onComplete: () => void;
}

const LOADING_STAGES = [
  'loading.visibility',
  'loading.competitors',
  'loading.reviews',
  'loading.photos',
  'loading.ranking',
];

export default function AnalysisLoader({ businessName, onComplete }: AnalysisLoaderProps) {
  const { language } = useLanguageDetection();
  const { t } = useTranslations(language);
  const [currentStage, setCurrentStage] = useState(0);
  const [progress, setProgress] = useState(0);

  useEffect(() => {
    // Simulate analysis progress
    const stageInterval = setInterval(() => {
      setCurrentStage((prev) => {
        if (prev >= LOADING_STAGES.length - 1) {
          clearInterval(stageInterval);
          setTimeout(onComplete, 1000);
          return prev;
        }
        return prev + 1;
      });
    }, 2000);

    // Smooth progress bar
    const progressInterval = setInterval(() => {
      setProgress((prev) => {
        if (prev >= 100) return 100;
        return prev + 1;
      });
    }, 100);

    return () => {
      clearInterval(stageInterval);
      clearInterval(progressInterval);
    };
  }, [onComplete]);

  return (
    <div className="fixed inset-0 bg-dark-900/95 backdrop-blur-md flex items-center justify-center z-50 px-4">
      <div className="max-w-2xl w-full">
        {/* Scanner Frame */}
        <div className="relative card border-2 border-neon-500/50 overflow-hidden">
          {/* Scanning line animation */}
          <div className="scanner-line" />
          
          {/* Header */}
          <div className="text-center mb-8 pt-8">
            <h2 className="text-3xl font-bold text-white mb-2">
              {t('input.analyzing')}
            </h2>
            <p className="text-neon-500 text-xl font-mono">
              "{businessName}"
            </p>
          </div>

          {/* Radar/Scanner Visualization */}
          <div className="relative w-48 h-48 mx-auto mb-8">
            {/* Outer rings */}
            <div className="absolute inset-0 border-2 border-neon-500/20 rounded-full animate-ping" />
            <div className="absolute inset-4 border-2 border-neon-500/30 rounded-full animate-pulse" />
            <div className="absolute inset-8 border-2 border-neon-500/40 rounded-full" />
            
            {/* Center dot */}
            <div className="absolute inset-0 flex items-center justify-center">
              <div className="w-4 h-4 bg-neon-500 rounded-full animate-pulse shadow-lg shadow-neon-500/50" />
            </div>

            {/* Rotating scanner beam */}
            <div className="absolute inset-0 animate-spin" style={{ animationDuration: '3s' }}>
              <div className="absolute top-1/2 left-1/2 w-1 h-24 bg-gradient-to-t from-neon-500 to-transparent origin-bottom -translate-x-1/2" />
            </div>
          </div>

          {/* Loading Stages */}
          <div className="space-y-4 mb-8">
            {LOADING_STAGES.map((stage, index) => (
              <div
                key={stage}
                className={`flex items-center gap-3 transition-all duration-500 ${
                  index <= currentStage ? 'opacity-100' : 'opacity-30'
                }`}
              >
                {index < currentStage ? (
                  <div className="w-6 h-6 bg-neon-500 rounded-full flex items-center justify-center">
                    <svg className="w-4 h-4 text-dark-900" fill="currentColor" viewBox="0 0 20 20">
                      <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                    </svg>
                  </div>
                ) : index === currentStage ? (
                  <div className="w-6 h-6 border-2 border-neon-500 rounded-full animate-spin border-t-transparent" />
                ) : (
                  <div className="w-6 h-6 border-2 border-dark-600 rounded-full" />
                )}
                <span
                  className={`text-sm font-mono ${
                    index <= currentStage ? 'text-gray-300' : 'text-gray-600'
                  }`}
                >
                  {t(stage)}
                </span>
              </div>
            ))}
          </div>

          {/* Progress Bar */}
          <div className="relative h-2 bg-dark-700 rounded-full overflow-hidden">
            <div
              className="absolute inset-y-0 left-0 bg-gradient-to-r from-neon-500 to-cyber-blue transition-all duration-300 ease-out"
              style={{ width: `${progress}%` }}
            />
            <div className="absolute inset-y-0 left-0 w-full bg-gradient-to-r from-transparent via-white/30 to-transparent animate-pulse" />
          </div>

          {/* Progress Percentage */}
          <div className="text-center mt-4 pb-4">
            <span className="text-neon-500 font-mono text-2xl font-bold">
              {progress}%
            </span>
          </div>
        </div>

        {/* Tech Info */}
        <div className="mt-4 text-center">
          <p className="text-gray-500 text-sm font-mono">
            {'>'} AI-Powered Analysis Engine v2.0
            <span className="inline-block w-2 h-4 bg-neon-500 ml-1 animate-pulse" />
          </p>
        </div>
      </div>
    </div>
  );
}
