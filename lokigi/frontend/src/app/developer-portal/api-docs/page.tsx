<main className="min-h-screen bg-white text-corporate-dark flex flex-col items-center py-12 px-4">
  <h1 className="text-4xl font-extrabold mb-8 text-corporate-blue tracking-tight">Documentación de API</h1>
  <section className="w-full max-w-4xl card mb-8">
    {/* Aquí iría la documentación Swagger/Redoc adaptada al nuevo estilo */}
    <div className="prose prose-blue max-w-none">
      {apiDocsContent}
    </div>
  </section>
</main>