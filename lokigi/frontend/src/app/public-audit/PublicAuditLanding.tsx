import { useEffect, useState } from "react";

export default function PublicAuditLanding({ loss = 1200, currency = "USD", competitors = [] }) {
  // competitors: [{ name, score }]
  const [progress, setProgress] = useState(0);
  const [showHero, setShowHero] = useState(false);

  useEffect(() => {
    if (progress < 100) {
      const t = setTimeout(() => setProgress(progress + 10), 80);
      return () => clearTimeout(t);
    } else {
      setTimeout(() => setShowHero(true), 400);
    }
  }, [progress]);

  return (
    <div className="min-h-screen bg-gray-950 text-white font-mono flex flex-col items-center justify-center p-0">
      {/* Efecto de carga */}
      {!showHero && (
        <div className="flex flex-col items-center justify-center h-screen w-full">
          <span className="text-lg text-gray-300 mb-4">Verificando seguridad de tu perfil...</span>
          <div className="w-64 h-3 bg-gray-800 rounded-full overflow-hidden">
            <div className="h-full bg-[#39FF14] transition-all duration-300" style={{ width: `${progress}%` }} />
          </div>
          <span className="mt-2 text-xs text-gray-500">{progress}%</span>
        </div>
      )}
      {/* Hero de Impacto */}
      {showHero && (
        <div className="flex flex-col items-center justify-center w-full px-4 pt-16">
          <h1 className="text-2xl font-extrabold text-[#39FF14] mb-4 text-center">Tu negocio está perdiendo aproximadamente</h1>
          <span className="text-5xl font-black text-[#FF3B3B] mb-6">{loss.toLocaleString()} {currency}</span>
          <div className="w-full max-w-md mt-8">
            <h2 className="text-lg text-[#39FF14] mb-2">Comparativa con tu competencia</h2>
            <div className="space-y-3">
              {competitors.map((c, i) => (
                <BarAnim key={i} name={c.name} score={c.score} delay={i * 120} />
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

function BarAnim({ name, score, delay }) {
  const [visible, setVisible] = useState(false);
  useEffect(() => {
    const onScroll = () => {
      setVisible(true);
    };
    setTimeout(onScroll, 400 + delay);
    return () => {};
  }, [delay]);
  return (
    <div className="flex items-center gap-2">
      <span className="text-xs text-gray-400 w-20 truncate">{name}</span>
      <div className="flex-1 h-4 bg-gray-800 rounded-full overflow-hidden">
        <div
          className="h-full bg-[#39FF14] transition-all duration-700"
          style={{ width: visible ? `${score}%` : "0%" }}
        />
      </div>
      <span className="text-xs text-[#39FF14] ml-2">{score}</span>
    </div>
  );
}
