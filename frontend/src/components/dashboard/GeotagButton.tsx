'use client';

import { useState, useRef } from 'react';
import { MapPin, Upload, X, CheckCircle, Loader2, Download } from 'lucide-react';

interface GeotagButtonProps {
  businessName: string;
  businessAddress?: string;
  orderId: number;
}

interface GeotagResult {
  latitude: number;
  longitude: number;
  address: string;
  files_processed: number;
}

export default function GeotagButton({ businessName, businessAddress, orderId }: GeotagButtonProps) {
  const [isOpen, setIsOpen] = useState(false);
  const [loading, setLoading] = useState(false);
  const [selectedFiles, setSelectedFiles] = useState<File[]>([]);
  const [result, setResult] = useState<GeotagResult | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files) {
      const files = Array.from(e.target.files);
      setSelectedFiles(files);
    }
  };

  const handleGeotagPhotos = async () => {
    if (selectedFiles.length === 0) {
      alert('Por favor selecciona al menos una foto');
      return;
    }

    setLoading(true);
    try {
      const formData = new FormData();
      formData.append('business_name', businessName);
      if (businessAddress) {
        formData.append('business_address', businessAddress);
      }
      selectedFiles.forEach(file => {
        formData.append('files', file);
      });

      const response = await fetch(
        `${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/dashboard/orders/${orderId}/geotag-photos`,
        {
          method: 'POST',
          body: formData,
        }
      );

      if (!response.ok) throw new Error('Error al geoetiquetar fotos');

      const data = await response.json();
      setResult(data);
      
      // Descargar el archivo ZIP con las fotos geoetiquetadas
      if (data.download_url) {
        window.open(data.download_url, '_blank');
      }
    } catch (error) {
      console.error('Error:', error);
      alert('Error al geoetiquetar fotos');
    } finally {
      setLoading(false);
    }
  };

  const removeFile = (index: number) => {
    setSelectedFiles(prev => prev.filter((_, i) => i !== index));
  };

  return (
    <>
      {/* Trigger Button */}
      <button
        onClick={() => setIsOpen(true)}
        className="btn-primary w-full flex items-center justify-center gap-2"
      >
        <MapPin className="w-5 h-5" />
        📍 Geotag Fotos
      </button>

      {/* Modal */}
      {isOpen && (
        <div className="fixed inset-0 bg-black/80 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-dark-800 border border-neon-500/30 rounded-2xl max-w-2xl w-full max-h-[90vh] overflow-y-auto">
            {/* Header */}
            <div className="sticky top-0 bg-dark-800 border-b border-neon-500/30 p-6 flex items-center justify-between">
              <div>
                <h2 className="text-2xl font-bold text-white flex items-center gap-2">
                  <MapPin className="w-6 h-6 text-neon-500" />
                  Geotag de Fotos
                </h2>
                <p className="text-gray-400 text-sm mt-1">
                  Añade coordenadas GPS automáticamente a tus fotos
                </p>
              </div>
              <button
                onClick={() => setIsOpen(false)}
                className="w-10 h-10 bg-gray-800 hover:bg-gray-700 rounded-lg flex items-center justify-center transition-colors"
              >
                <X className="w-5 h-5 text-gray-400" />
              </button>
            </div>

            {/* Content */}
            <div className="p-6 space-y-6">
              {!result ? (
                <>
                  {/* Info Card */}
                  <div className="bg-cyber-blue/10 border border-cyber-blue/30 rounded-lg p-4">
                    <h3 className="text-sm font-bold text-cyber-blue mb-2">¿Qué hace esta herramienta?</h3>
                    <ul className="text-sm text-gray-300 space-y-1">
                      <li>• Obtiene coordenadas GPS de la dirección del negocio</li>
                      <li>• Inyecta metadata EXIF con lat/long en cada foto</li>
                      <li>• Google reconoce estas fotos como tomadas en el negocio</li>
                      <li>• Mejora ranking local en Google Maps</li>
                    </ul>
                  </div>

                  {/* Business Info */}
                  <div className="card">
                    <p className="text-sm text-gray-400 mb-1">Negocio:</p>
                    <p className="text-white font-bold">{businessName}</p>
                    {businessAddress && (
                      <>
                        <p className="text-sm text-gray-400 mt-3 mb-1">Dirección:</p>
                        <p className="text-gray-300 text-sm">{businessAddress}</p>
                      </>
                    )}
                  </div>

                  {/* File Upload */}
                  <div className="card">
                    <h3 className="text-sm font-bold text-white mb-3">Seleccionar Fotos</h3>
                    
                    <input
                      ref={fileInputRef}
                      type="file"
                      accept="image/jpeg,image/jpg,image/png"
                      multiple
                      onChange={handleFileSelect}
                      className="hidden"
                    />
                    
                    <button
                      onClick={() => fileInputRef.current?.click()}
                      className="btn-secondary w-full flex items-center justify-center gap-2"
                    >
                      <Upload className="w-5 h-5" />
                      Seleccionar Fotos (JPG, PNG)
                    </button>

                    {/* Selected Files */}
                    {selectedFiles.length > 0 && (
                      <div className="mt-4 space-y-2">
                        <p className="text-sm text-gray-400">
                          {selectedFiles.length} foto{selectedFiles.length > 1 ? 's' : ''} seleccionada{selectedFiles.length > 1 ? 's' : ''}
                        </p>
                        <div className="space-y-2 max-h-48 overflow-y-auto">
                          {selectedFiles.map((file, index) => (
                            <div
                              key={index}
                              className="bg-dark-900 p-3 rounded-lg flex items-center justify-between border border-gray-700"
                            >
                              <div className="flex items-center gap-3">
                                <div className="w-12 h-12 bg-gray-800 rounded flex items-center justify-center">
                                  <Upload className="w-5 h-5 text-gray-500" />
                                </div>
                                <div>
                                  <p className="text-sm text-white font-medium">{file.name}</p>
                                  <p className="text-xs text-gray-500">
                                    {(file.size / 1024 / 1024).toFixed(2)} MB
                                  </p>
                                </div>
                              </div>
                              <button
                                onClick={() => removeFile(index)}
                                className="w-8 h-8 bg-danger-500/20 hover:bg-danger-500/30 rounded flex items-center justify-center transition-colors"
                              >
                                <X className="w-4 h-4 text-danger-500" />
                              </button>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>

                  {/* Process Button */}
                  <button
                    onClick={handleGeotagPhotos}
                    disabled={loading || selectedFiles.length === 0}
                    className="btn-primary w-full flex items-center justify-center gap-2"
                  >
                    {loading ? (
                      <>
                        <Loader2 className="w-5 h-5 animate-spin" />
                        Procesando...
                      </>
                    ) : (
                      <>
                        <MapPin className="w-5 h-5" />
                        Geoetiquetar Fotos
                      </>
                    )}
                  </button>
                </>
              ) : (
                /* Success Result */
                <div className="space-y-4">
                  <div className="bg-neon-500/10 border border-neon-500/30 rounded-lg p-6 text-center">
                    <CheckCircle className="w-16 h-16 text-neon-500 mx-auto mb-4" />
                    <h3 className="text-xl font-bold text-white mb-2">
                      ✅ Fotos Geoetiquetadas
                    </h3>
                    <p className="text-gray-400 mb-4">
                      {result.files_processed} foto{result.files_processed > 1 ? 's' : ''} procesada{result.files_processed > 1 ? 's' : ''} correctamente
                    </p>
                    
                    <div className="bg-dark-900 p-4 rounded-lg border border-gray-700 text-left">
                      <p className="text-sm text-gray-400 mb-1">📍 Coordenadas GPS:</p>
                      <p className="text-neon-500 font-mono font-bold">
                        {result.latitude}, {result.longitude}
                      </p>
                      <p className="text-xs text-gray-500 mt-2">{result.address}</p>
                    </div>
                  </div>

                  <div className="card">
                    <h3 className="text-sm font-bold text-white mb-2">Próximos pasos:</h3>
                    <ul className="text-sm text-gray-300 space-y-1">
                      <li>✅ Las fotos se descargaron automáticamente</li>
                      <li>📤 Súbelas a Google My Business</li>
                      <li>🎯 Google verificará las coordenadas</li>
                      <li>📈 Mejorará el ranking local del negocio</li>
                    </ul>
                  </div>

                  <button
                    onClick={() => {
                      setResult(null);
                      setSelectedFiles([]);
                    }}
                    className="btn-secondary w-full"
                  >
                    Procesar más fotos
                  </button>
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </>
  );
}
