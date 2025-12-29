// frontend/src/app/dashboard/premium/page.tsx
import PremiumControlTower from "@/app/components/PremiumControlTower";
import { useEffect, useState } from "react";
import { createClient } from "@supabase/supabase-js";

const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL;
const supabaseKey = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY;
const supabase = createClient(supabaseUrl, supabaseKey);

export default function PremiumDashboardPage() {
  const [points, setPoints] = useState([]);
  const [alerts, setAlerts] = useState([]);
  const [roi, setRoi] = useState({ amount: 0, currency: 'USD' });

  useEffect(() => {
    // Fetch puntos de visibilidad y ROI desde Supabase
    async function fetchPointsAndROI() {
      // Puntos: tabla 'visibility_points' {lat, lon, dominance}
      const { data: pointsData } = await supabase.from('visibility_points').select('*');
      setPoints(pointsData || []);
      // ROI: tabla 'roi_tracker' {amount, currency}
      const { data: roiData } = await supabase.from('roi_tracker').select('*').single();
      if (roiData) setRoi(roiData);
    }
    // Fetch alertas desde backend
    async function fetchAlerts() {
      // Simulación: snapshots de 3 competidores
      const snapshots = [
        {
          name: "Pizzeria Napoli",
          history: [
            { date: "2025-11", rating: 4.2, reviews: 120, photos: 30 },
            { date: "2025-12", rating: 4.5, reviews: 145, photos: 42, tags: "Navidad" }
          ]
        },
        {
          name: "Pizza Roma",
          history: [
            { date: "2025-11", rating: 4.0, reviews: 80, photos: 20 },
            { date: "2025-12", rating: 4.1, reviews: 100, photos: 22 }
          ]
        },
        {
          name: "Pizza Brasil",
          history: [
            { date: "2025-11", rating: 4.3, reviews: 90, photos: 25 },
            { date: "2025-12", rating: 4.6, reviews: 130, photos: 35 }
          ]
        }
      ];
      const res = await fetch("/api/alert-radar", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ snapshots, country: "AR", lang: "es" })
      });
      const json = await res.json();
      // Mapear a formato del feed
      setAlerts((json.alerts || []).map((text, i) => ({ text, type: 'danger', date: new Date().toISOString().slice(0, 10) })));
    }
    fetchPointsAndROI();
    fetchAlerts();
  }, []);

  return <PremiumControlTower points={points} alerts={alerts} roi={roi} />;
}
