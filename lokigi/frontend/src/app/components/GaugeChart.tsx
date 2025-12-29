import { Chart, ArcElement, Tooltip } from "chart.js";
import { useEffect, useRef } from "react";

Chart.register(ArcElement, Tooltip);

export function GaugeChart({ score = 85 }: { score: number }) {
  const canvasRef = useRef<HTMLCanvasElement>(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;
    // Limpia
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    // Gradiente de Rojo a Verde Neón
    const grad = ctx.createLinearGradient(0, 0, canvas.width, 0);
    grad.addColorStop(0, "#FF3B3B");
    grad.addColorStop(0.5, "#FFD600");
    grad.addColorStop(1, "#39FF14");
    // Dibuja arco de fondo
    ctx.lineWidth = 32;
    ctx.beginPath();
    ctx.arc(150, 150, 120, Math.PI, 0, false);
    ctx.strokeStyle = "#222";
    ctx.stroke();
    // Dibuja arco de score
    ctx.beginPath();
    ctx.arc(150, 150, 120, Math.PI, Math.PI + Math.PI * (score / 100), false);
    ctx.strokeStyle = grad;
    ctx.stroke();
    // Dibuja texto
    ctx.font = "bold 48px monospace";
    ctx.fillStyle = score > 80 ? "#39FF14" : score > 60 ? "#FFD600" : "#FF3B3B";
    ctx.textAlign = "center";
    ctx.fillText(`${score}`, 150, 170);
  }, [score]);

  return <canvas ref={canvasRef} width={300} height={200} className="mx-auto" />;
}
