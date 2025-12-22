'use client';

import { useState } from 'react';
import { useLanguageDetection } from '@/hooks/useLanguageDetection';
import { useTranslations } from '@/lib/translations';

interface HeroSectionProps {
  onStartAnalysis: (businessName: string) => void;
}

export default function HeroSection({ onStartAnalysis }: HeroSectionProps) {
  const { language } = useLanguageDetection();
  const { t } = useTranslations(language);
  const [businessName, setBusinessName] = useState('');

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (businessName.trim()) {
      onStartAnalysis(businessName.trim());
    }
  };

  return (
    <section className="relative min-h-screen flex items-center justify-center px-4 overflow-hidden">
      {/* Animated grid background */}
      <div className="absolute inset-0 grid-background opacity-30" />
      
      {/* Gradient orbs */}
      <div className="absolute top-20 left-10 w-96 h-96 bg-neon-500/20 rounded-full blur-3xl animate-pulse-slow" />
      <div className="absolute bottom-20 right-10 w-96 h-96 bg-cyber-blue/20 rounded-full blur-3xl animate-pulse-slow" style={{ animationDelay: '1s' }} />
      
      <div className="relative z-10 max-w-5xl mx-auto text-center">
        {/* Social Proof Badge */}
        <div className="inline-flex items-center gap-2 px-4 py-2 bg-dark-800 border border-neon-500/30 rounded-full mb-8 animate-fade-in">
          <div className="w-2 h-2 bg-neon-500 rounded-full animate-pulse" />
          <span className="text-sm text-gray-400">{t('proof.analyzed')}</span>
        </div>

        {/* Headline */}
        <h1 className="text-5xl md:text-7xl font-bold mb-6 leading-tight">
          <span className="text-white">{t('hero.headline').split(' ').slice(0, -3).join(' ')}</span>{' '}
          <span className="text-neon-glow">{t('hero.headline').split(' ').slice(-3).join(' ')}</span>
        </h1>

        {/* Subheadline */}
        <p className="text-xl md:text-2xl text-gray-400 mb-12 max-w-3xl mx-auto">
          {t('hero.subheadline')}
        </p>

        {/* Input Form */}
        <form onSubmit={handleSubmit} className="max-w-2xl mx-auto mb-6">
          <div className="relative group">
            {/* Neon border effect */}
            <div className="absolute -inset-1 bg-gradient-to-r from-neon-500 to-cyber-blue rounded-lg blur opacity-25 group-hover:opacity-50 transition duration-300" />
            
            <div className="relative flex flex-col md:flex-row gap-4 bg-dark-800 p-2 rounded-lg border border-dark-600">
              <input
                type="text"
                value={businessName}
                onChange={(e) => setBusinessName(e.target.value)}
                placeholder={t('input.placeholder')}
                className="flex-1 bg-dark-700 text-white px-6 py-4 rounded-lg border-2 border-transparent focus:border-neon-500 focus:outline-none transition-all duration-300 placeholder-gray-500"
                required
              />
              <button
                type="submit"
                className="btn-primary whitespace-nowrap"
              >
                {t('hero.cta')}
              </button>
            </div>
          </div>
        </form>

        {/* Trust Badge */}
        <p className="text-gray-500 text-sm">
          {t('hero.trustBadge')}
        </p>

        {/* Features Grid */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mt-20">
          {[1, 2, 3].map((num) => (
            <div key={num} className="card card-hover text-left">
              <div className="w-12 h-12 bg-neon-500/10 rounded-lg flex items-center justify-center mb-4 border border-neon-500/30">
                <span className="text-2xl text-neon-500 font-mono font-bold">{`0${num}`}</span>
              </div>
              <h3 className="text-xl font-bold mb-2 text-white">
                {t(`features.${num}.title`)}
              </h3>
              <p className="text-gray-400">
                {t(`features.${num}.desc`)}
              </p>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
