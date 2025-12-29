```tsx
return (
    <div className="card bg-white text-corporate-dark border border-corporate-gray p-6 mb-6">
      <h2 className="text-2xl font-bold text-corporate-blue mb-4">Panel de Tareas</h2>
      <div className="mb-2 text-gray-700">{summary}</div>
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
        <div>
          <span className="font-semibold">Tareas activas:</span> <span className="text-corporate-blue">{activeTasks}</span>
        </div>
        <div>
          <span className="font-semibold">Completadas:</span> <span className="text-corporate-blue">{completedTasks}</span>
        </div>
      </div>
    </div>
  );
```