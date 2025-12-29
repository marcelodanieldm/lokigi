import React, { useState } from "react";
import WorkerTerminal, { WorkerTask } from "@/app/components/WorkerTerminal";

const initialTasks: WorkerTask[] = [
  {
    id: "1",
    review: "La pizza estaba deliciosa y el servicio fue rápido.",
    aiProposal: "¡Gracias por tu reseña! Nos alegra que hayas disfrutado la pizza y el servicio."
  },
  {
    id: "2",
    review: "O atendimento foi excelente, mas achei o ambiente barulhento.",
    aiProposal: "Agradecemos seu feedback! Vamos trabalhar para melhorar o ambiente."
  },
  {
    id: "3",
    review: "Great food but the wait was too long.",
    aiProposal: "Thank you for your review! We'll work on reducing wait times."
  }
];

export default function WorkerPage() {
  const [tasks, setTasks] = useState<WorkerTask[]>(initialTasks);
  const [removing, setRemoving] = useState<string | null>(null);

  const handleApprove = async (id: string) => {
    setRemoving(id);
    // Simulación de publicación en backend
    await fetch("/api/worker/approve", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ id })
    });
    setTimeout(() => {
      setTasks((prev) => prev.filter((t) => t.id !== id));
      setRemoving(null);
    }, 400);
  };

  const handleRegenerate = async (id: string, tone: "formal" | "friendly") => {
    const task = tasks.find(t => t.id === id);
    if (!task) return;
    // Lógica de tono para backend
    const toneMap = { formal: "Professional", friendly: "Casual" };
    const res = await fetch("/api/worker/generate-replies", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        reviews: [task.review],
        temperature: 0.7,
        tone: toneMap[tone],
        lang: "es"
      })
    });
    const data = await res.json();
    setTasks(prev => prev.map(t => t.id === id ? { ...t, aiProposal: data.suggestions[0] } : t));
  };
  return (
    <div>
      <WorkerTerminal
        tasks={tasks}
        onApprove={handleApprove}
        onRegenerate={handleRegenerate}
      />
      <style>{`
        .group[removing="true"] {
          opacity: 0;
          transform: translateX(40px) scale(0.95);
          transition: all 0.4s cubic-bezier(.4,2,.6,1);
        }
      `}</style>
      <script dangerouslySetInnerHTML={{
        __html: `
          document.querySelectorAll('.group').forEach(el => {
            if (el.getAttribute('data-id') === '${removing}') {
              el.setAttribute('removing', 'true');
            } else {
              el.removeAttribute('removing');
            }
          });
        `
      }} />
    </div>
  );
}
