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
