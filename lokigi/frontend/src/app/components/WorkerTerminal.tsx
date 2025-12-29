import React from "react";

export type WorkerTask = {
  id: string;
  review: string;
  aiProposal: string;
};

type Props = {
  tasks: WorkerTask[];
  onApprove: (id: string) => void;
  onRegenerate: (id: string, tone: "formal" | "friendly") => void;
};

const neon = "#39FF14";

export const WorkerTerminal: React.FC<Props> = ({ tasks, onApprove, onRegenerate }) => (
  <div className="bg-black min-h-screen flex flex-col items-center py-8 px-2">
    <div className="w-full max-w-3xl space-y-4">
      {tasks.map((task) => (
        <div
          key={task.id}
          className="flex items-stretch rounded-lg border border-neutral-800 bg-neutral-900 shadow-lg transition-all hover:scale-[1.01] group"
        >
          {/* Reseña Cliente */}
          <div className="flex-1 p-4 border-r border-neutral-800 font-mono text-neutral-200 text-sm flex items-center">
            <span>{task.review}</span>
          </div>
          {/* Propuesta IA */}
          <div className="flex-1 p-4 font-mono text-green-300 text-sm flex items-center bg-neutral-950">
            <span>{task.aiProposal}</span>
          </div>
          {/* Acciones */}
          <div className="flex flex-col justify-center gap-2 p-4 bg-black">
            <button
              className="font-mono text-black text-xs font-bold py-2 px-4 rounded-lg mb-1 transition-all shadow-md outline-none focus:ring-2 focus:ring-green-400"
              style={{ background: neon, boxShadow: `0 0 8px 1px ${neon}` }}
              onClick={() => onApprove(task.id)}
            >
              Aprobar y Publicar
            </button>
            <button
              className="font-mono text-green-300 border border-green-400 text-xs py-2 px-4 rounded-lg transition-all hover:bg-neutral-900 focus:ring-2 focus:ring-green-400"
              onClick={() => onRegenerate(task.id, "formal")}
            >
              Regenerar Formal
            </button>
            <button
              className="font-mono text-green-300 border border-green-400 text-xs py-2 px-4 rounded-lg transition-all hover:bg-neutral-900 focus:ring-2 focus:ring-green-400"
              onClick={() => onRegenerate(task.id, "friendly")}
            >
              Regenerar Amigable
            </button>
          </div>
        </div>
      ))}
    </div>
    {/* Micro-interacciones CSS */}
    <style>{`
      .group:hover .font-mono { color: ${neon}; }
      button:active { transform: scale(0.97); }
      button:focus { outline: none; box-shadow: 0 0 0 2px ${neon}; }
    `}</style>
  </div>
);

export default WorkerTerminal;
