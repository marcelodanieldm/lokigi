```tsx
<main className="min-h-screen bg-white text-corporate-dark flex flex-col items-center py-12 px-4">
  <h1 className="text-4xl font-extrabold mb-8 text-corporate-blue tracking-tight">Reseñas de Clientes</h1>
  <section className="w-full max-w-3xl card mb-8">
    {/* Aquí irían las reseñas */}
    <div className="text-gray-700">{reviewsSummary}</div>
    <ul className="list-disc pl-6 text-gray-700 mt-4">
      {reviews.map((review, i) => (
        <li key={i}>{review}</li>
      ))}
    </ul>
  </section>
</main>
```