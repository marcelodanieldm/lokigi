import React from 'react';

// Card de App
export function AppCard({ app }) {
  return (
    <div className="bg-gray-800 rounded-xl shadow-lg p-4 flex flex-col items-center text-white hover:ring-2 ring-lime-400 transition">
      <img src={app.icon} alt={app.name} className="w-16 h-16 mb-2" />
      <div className="font-bold text-lg mb-1">{app.name}</div>
      <div className="text-sm text-gray-400 mb-1">{app.author}</div>
      <div className="flex items-center mb-1">
        <span className="text-yellow-400 mr-1">★</span>{app.rating}
      </div>
      <div className="text-lime-400 font-semibold">${app.price}</div>
    </div>
  );
}

// Grid de Apps
export function AppGrid({ apps }) {
  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-6">
      {apps.map(app => <AppCard key={app.id} app={app} />)}
    </div>
  );
}

// Página de Detalle
export function AppDetail({ app, onInstall }) {
  return (
    <div className="bg-gray-900 rounded-xl p-6 text-white max-w-2xl mx-auto">
      <div className="flex gap-4">
        <img src={app.icon} alt={app.name} className="w-20 h-20" />
        <div>
          <div className="font-bold text-2xl mb-1">{app.name}</div>
          <div className="text-gray-400 mb-2">{app.author}</div>
          <div className="flex items-center mb-2">
            <span className="text-yellow-400 mr-1">★</span>{app.rating}
          </div>
          <div className="text-lime-400 font-semibold text-xl mb-2">${app.price}</div>
        </div>
      </div>
      <div className="mt-4 mb-4">
        <div className="mb-2 font-semibold">Capturas de pantalla:</div>
        <div className="flex gap-2">
          {app.screenshots.map((src, i) => (
            <img key={i} src={src} alt="screenshot" className="w-32 h-20 rounded-lg" />
          ))}
        </div>
      </div>
      <div className="mb-4 text-gray-300">{app.description}</div>
      <button
        className="bg-lime-400 text-black font-bold py-2 px-6 rounded-lg hover:bg-lime-500 transition"
        onClick={onInstall}
      >Instalar ahora</button>
    </div>
  );
}

// Gestión de Suscripciones
export function SubscriptionList({ subscriptions }) {
  return (
    <div className="bg-gray-900 rounded-xl p-6 text-white max-w-xl mx-auto mt-8">
      <div className="font-bold text-xl mb-4">Tus Add-ons Activos</div>
      <ul>
        {subscriptions.map(sub => (
          <li key={sub.id} className="flex justify-between items-center mb-2">
            <span>{sub.name}</span>
            <span className="text-lime-400 font-semibold">${sub.price}/mes</span>
          </li>
        ))}
      </ul>
    </div>
  );
}
