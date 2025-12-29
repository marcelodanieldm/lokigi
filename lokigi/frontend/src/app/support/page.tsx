<main className="min-h-screen bg-white text-corporate-dark flex flex-col items-center py-12 px-4">
  <h1 className="text-4xl font-extrabold mb-8 text-corporate-blue tracking-tight">Soporte y Ayuda</h1>
  <section className="w-full max-w-3xl card mb-8">
    <h2 className="text-2xl font-bold text-corporate-blue mb-2">Preguntas Frecuentes</h2>
    <ul className="list-disc pl-6 text-gray-700">
      {/* Aquí irían las preguntas frecuentes */}
      {faqs.map((faq, i) => (
        <li key={i}>{faq}</li>
      ))}
    </ul>
  </section>
  <section className="w-full max-w-3xl card mb-8">
    <h2 className="text-2xl font-bold text-corporate-blue mb-2">Contacto</h2>
    <div className="text-gray-700">Para soporte personalizado, escribe a <a href="mailto:soporte@lokigi.com" className="text-corporate-blue underline">soporte@lokigi.com</a></div>
  </section>
</main>