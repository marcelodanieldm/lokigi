```tsx
<main className="min-h-screen bg-white text-corporate-dark flex flex-col items-center py-12 px-4">
  <h1 className="text-4xl font-extrabold mb-8 text-corporate-blue tracking-tight">Consumo de API</h1>
  <section className="w-full max-w-4xl card mb-8">
    {/* Aquí irían los gráficos de consumo y detalles */}
    <div className="text-gray-700">{usageSummary}</div>
    <div className="mt-4">
      <UsageCharts data={usageData} />
    </div>
  </section>
</main>
```