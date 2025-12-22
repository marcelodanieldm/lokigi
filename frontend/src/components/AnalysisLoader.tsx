'use client';

import { useEffect, useState } from 'react';
import { useLanguageDetection } from '@/hooks/useLanguageDetection';
import { useTranslations } from '@/lib/translations';

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
