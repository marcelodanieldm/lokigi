import React from "react";
import { Bar } from "react-chartjs-2";
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  BarElement,
  Title,
  Tooltip,
  Legend,
} from "chart.js";

ChartJS.register(CategoryScale, LinearScale, BarElement, Title, Tooltip, Legend);

const data = {
  labels: ["Lun", "Mar", "Mié", "Jue", "Vie", "Sáb", "Dom"],
  datasets: [
    {
      label: "Consumo de créditos",
      data: [12, 19, 3, 5, 2, 3, 7],
      backgroundColor: "#2563eb",
      borderRadius: 6,
    },
  ],
};

const options = {
  responsive: true,
  plugins: {
    legend: {
      labels: { color: "#2563eb" },
    },
    title: {
      display: true,
      text: "Consumo Diario",
      color: "#2563eb",
      font: { size: 18 },
    },
  },
  scales: {
    x: { ticks: { color: "#2563eb" }, grid: { color: "#e5e7eb" } },
    y: { ticks: { color: "#2563eb" }, grid: { color: "#e5e7eb" } },
  },
};

export default function UsageCharts() {
  return (
    <div id="usage">
      <h2 className="text-xl font-semibold mb-4">Visualización de Consumo</h2>
      <Bar data={data} options={options} />
    </div>
  );
}
