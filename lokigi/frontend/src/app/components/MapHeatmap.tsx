import { MapContainer, TileLayer, CircleMarker, Tooltip } from "react-leaflet";
import "leaflet/dist/leaflet.css";

export default function MapHeatmap({ points = [] }) {
  // points: [{lat, lon, dominance}]
  return (
    <MapContainer center={[-34.6, -58.4]} zoom={13} scrollWheelZoom={false} className="w-full h-full rounded-b-xl">
      <TileLayer
        url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
        attribution="&copy; OpenStreetMap contributors"
      />
      {points.map((p, i) => (
        <CircleMarker
          key={i}
          center={[p.lat, p.lon]}
          radius={18}
          pathOptions={{ color: p.dominance === "client" ? "#39FF14" : "#FF3B3B", fillColor: p.dominance === "client" ? "#39FF14" : "#FF3B3B", fillOpacity: 0.7 }}
        >
          <Tooltip direction="top" offset={[0, -10]} opacity={1} permanent>
            {p.dominance === "client" ? "Dominio propio" : "Competencia"}
          </Tooltip>
        </CircleMarker>
      ))}
    </MapContainer>
  );
}
