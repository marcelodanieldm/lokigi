'use client';

import { useState } from 'react';
import { useLanguageDetection } from '@/hooks/useLanguageDetection';
import { useTranslations } from '@/lib/translations';

interface LeadCaptureFormProps {
  businessName: string;
  onSubmit: (email: string, phone: string) => void;
  isLoading?: boolean;
}

export default function LeadCaptureForm({ businessName, onSubmit, isLoading = false }: LeadCaptureFormProps) {
  const { language } = useLanguageDetection();
  const { t } = useTranslations(language);
  const [email, setEmail] = useState('');
  const [phone, setPhone] = useState('');

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    onSubmit(email, phone);
  };

  return (
    <div className="fixed inset-0 bg-dark-900/98 backdrop-blur-sm flex items-center justify-center z-50 px-4 animate-fade-in">
      <div className="max-w-md w-full">
        {/* Alert Icon with Pulse */}
        <div className="flex justify-center mb-6">
          <div className="relative">
            <div className="absolute inset-0 bg-danger-500/20 rounded-full blur-xl animate-pulse" />
            <div className="relative w-20 h-20 bg-gradient-to-br from-danger-500 to-warning-500 rounded-full flex items-center justify-center border-4 border-dark-800">
              <svg className="w-10 h-10 text-white" fill="currentColor" viewBox="0 0 20 20">
                <path fillRule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
              </svg>
            </div>
          </div>
        </div>

        {/* Card */}
        <div className="card border-2 border-danger-500/30">
          {/* Header */}
          <div className="text-center mb-6">
            <h2 className="text-2xl font-bold text-white mb-2">
              {t('form.title')}
            </h2>
            <p className="text-gray-400">
              {t('form.subtitle')}
            </p>
            <p className="text-neon-500 font-mono mt-2 text-sm">
              {businessName}
            </p>
          </div>

          {/* Form */}
          <form onSubmit={handleSubmit} className="space-y-4">
            {/* Email */}
            <div>
              <label htmlFor="email" className="block text-sm font-medium text-gray-300 mb-2">
                {t('form.email')} *
              </label>
              <div className="relative group">
                <div className="absolute -inset-1 bg-neon-500/20 rounded-lg blur opacity-0 group-focus-within:opacity-100 transition duration-300" />
                <input
                  id="email"
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  className="input-cyber w-full relative"
                  placeholder="seu@email.com"
                  required
                  disabled={isLoading}
                />
              </div>
            </div>

            {/* Phone */}
            <div>
              <label htmlFor="phone" className="block text-sm font-medium text-gray-300 mb-2">
                {t('form.phone')}
              </label>
              <div className="relative group">
                <div className="absolute -inset-1 bg-neon-500/20 rounded-lg blur opacity-0 group-focus-within:opacity-100 transition duration-300" />
                <input
                  id="phone"
                  type="tel"
                  value={phone}
                  onChange={(e) => setPhone(e.target.value)}
                  className="input-cyber w-full relative"
                  placeholder="+55 11 99999-9999"
                  disabled={isLoading}
                />
              </div>
            </div>

            {/* Submit Button */}
            <button
              type="submit"
              disabled={isLoading}
              className="btn-primary w-full disabled:opacity-50 disabled:cursor-not-allowed relative overflow-hidden"
            >
              {isLoading ? (
                <span className="flex items-center justify-center gap-2">
                  <div className="w-5 h-5 border-2 border-dark-900 border-t-transparent rounded-full animate-spin" />
                  {t('input.analyzing')}
                </span>
              ) : (
                t('form.submit')
              )}
            </button>
          </form>

          {/* Privacy Notice */}
          <p className="text-xs text-gray-500 text-center mt-6">
            {t('form.privacy')}
          </p>
        </div>

        {/* Decorative Elements */}
        <div className="absolute top-0 left-0 w-full h-px bg-gradient-to-r from-transparent via-danger-500 to-transparent" />
        <div className="absolute bottom-0 left-0 w-full h-px bg-gradient-to-r from-transparent via-danger-500 to-transparent" />
      </div>
    </div>
  );
}
