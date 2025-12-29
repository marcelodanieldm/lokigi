<main className="min-h-screen bg-white text-corporate-dark flex flex-col items-center justify-center px-4">
  <h1 className="text-5xl font-extrabold mb-6 text-corporate-blue tracking-tight text-center">Lokigi: Control Total de tu Presencia Local</h1>
  <p className="text-lg text-gray-700 mb-8 max-w-2xl text-center">
    Plataforma SaaS para gestión, auditoría y crecimiento de negocios locales. Seguridad, velocidad y control para empresas modernas.
  </p>
  <div className="flex flex-col sm:flex-row gap-4 mb-8">
    <Link href="/dashboard" className="btn btn-primary">Ir al Dashboard</Link>
    <Link href="/developer-portal" className="btn">API & Integraciones</Link>
  </div>
  <section className="w-full max-w-4xl card mb-8">
    <h2 className="text-2xl font-bold text-corporate-blue mb-2">¿Por qué Lokigi?</h2>
    <ul className="list-disc pl-6 text-gray-700">
      <li>Multi-tenant, seguro y escalable</li>
      <li>Integración con Supabase, Stripe, Zapier, Make.com</li>
      <li>Automatización QA y analítica avanzada</li>
      <li>Soporte para equipos y agencias</li>
    </ul>
  </section>
  <section className="w-full max-w-4xl card mb-8">
    <h2 className="text-2xl font-bold text-corporate-blue mb-2">Funcionalidades Clave</h2>
    <div className="grid grid-cols-1 sm:grid-cols-2 gap-6">
      <div className="flex items-center gap-3">
        <ShieldCheckIcon className="w-8 h-8 text-corporate-blue" />
        <span>Auditoría de reputación y visibilidad</span>
      </div>
      <div className="flex items-center gap-3">
        <ChartBarIcon className="w-8 h-8 text-corporate-blue" />
        <span>Panel de control premium</span>
      </div>
      <div className="flex items-center gap-3">
        <KeyIcon className="w-8 h-8 text-corporate-blue" />
        <span>API pública y gestión de claves</span>
      </div>
      <div className="flex items-center gap-3">
        <UsersIcon className="w-8 h-8 text-corporate-blue" />
        <span>Multiusuario y roles avanzados</span>
      </div>
    </div>
  </section>
</main>