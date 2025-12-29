```tsx
<main className="min-h-screen bg-white text-corporate-dark flex flex-col items-center py-12 px-4">
  <h1 className="text-4xl font-extrabold mb-8 text-corporate-blue tracking-tight">Gestión de API Keys</h1>
  <section className="w-full max-w-3xl card mb-8">
    {/* Aquí iría la gestión de claves: generar, revocar, listar */}
    <div className="text-gray-700">{apiKeySummary}</div>
    <div className="mt-4">
      <CTAButton onClick={onGenerate} label="Generar nueva clave" />
    </div>
    <ul className="list-disc pl-6 text-gray-700 mt-4">
      {apiKeys.map((key, i) => (
        <li key={i}>{key}</li>
      ))}
    </ul>
  </section>
</main>
```