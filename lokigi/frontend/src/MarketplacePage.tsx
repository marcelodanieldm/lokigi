import { useEffect, useState } from 'react';
import { AppGrid, AppDetail, SubscriptionList } from './MarketplaceComponents';

// Fetch apps desde Supabase y API
export function Marketplace() {
  const [apps, setApps] = useState([]);
  const [selectedApp, setSelectedApp] = useState(null);
  const [subscriptions, setSubscriptions] = useState([]);

  useEffect(() => {
    // Cargar apps desde Supabase
    fetch('https://your-supabase-url.supabase.co/rest/v1/apps', {
      headers: {
        'apikey': 'your-supabase-key',
        'Authorization': 'Bearer your-supabase-key',
      },
    })
      .then(res => res.json())
      .then(setApps);
    // Cargar suscripciones
    fetch('/api/user-subscriptions')
      .then(res => res.json())
      .then(setSubscriptions);
  }, []);

  const handleInstall = async () => {
    // Llama API FastAPI para Stripe split
    const res = await fetch('/purchase-addon', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        price: selectedApp.price,
        developer_account: selectedApp.developer_account,
      }),
    });
    const data = await res.json();
    // Redirige a Stripe checkout o muestra modal
    window.open(`https://checkout.stripe.com/pay/${data.client_secret}`);
  };

  return (
    <div className="bg-gray-950 min-h-screen p-8">
      {!selectedApp ? (
        <AppGrid apps={apps} />
      ) : (
        <AppDetail app={selectedApp} onInstall={handleInstall} />
      )}
      <SubscriptionList subscriptions={subscriptions} />
    </div>
  );
}

// Para slots/hooks seguros:
// <iframe src={selectedApp.widget_url} sandbox="allow-scripts allow-same-origin" className="w-full h-96 rounded-xl" />
