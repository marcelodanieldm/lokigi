<main className="min-h-screen bg-white text-corporate-dark flex flex-col items-center py-12 px-4">
  <h1 className="text-4xl font-extrabold mb-8 text-corporate-blue tracking-tight">Resultados de Auditoría</h1>
  <section className="w-full max-w-3xl card mb-8">
    {/* Aquí irían los resultados detallados de la auditoría */}
    <div className="text-gray-700">{auditSummary}</div>
  </section>
  <section className="w-full max-w-3xl card mb-8">
    <h2 className="text-2xl font-bold text-corporate-blue mb-2">Recomendaciones</h2>
    <ul className="list-disc pl-6 text-gray-700">
      {/* Aquí irían las recomendaciones */}
      {recommendations.map((rec, i) => (
        <li key={i}>{rec}</li>
      ))}
    </ul>
  </section>
</main>