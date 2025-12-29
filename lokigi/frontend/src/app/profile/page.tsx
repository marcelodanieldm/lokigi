```tsx
<main className="min-h-screen bg-white text-corporate-dark flex flex-col items-center py-12 px-4">
  <h1 className="text-4xl font-extrabold mb-8 text-corporate-blue tracking-tight">Perfil de Usuario</h1>
  <section className="w-full max-w-3xl card mb-8">
    {/* Aquí iría la información del usuario y opciones de configuración */}
    <div className="text-gray-700">{userInfo}</div>
    <div className="mt-4">
      <CTAButton onClick={onEdit} label="Editar perfil" />
    </div>
  </section>
</main>
```