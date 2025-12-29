```tsx
<main className="min-h-screen bg-white text-corporate-dark flex flex-col items-center py-12 px-4">
  <h1 className="text-4xl font-extrabold mb-8 text-corporate-blue tracking-tight">Preguntas Frecuentes</h1>
  <section className="w-full max-w-3xl card mb-8">
    <ul className="list-disc pl-6 text-gray-700">
      {/* Aquí irían las preguntas frecuentes */}
      {faqs.map((faq, i) => (
        <li key={i}>{faq}</li>
      ))}
    </ul>
  </section>
</main>
```