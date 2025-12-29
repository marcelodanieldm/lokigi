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
      backgroundColor: "#39FF14BB",
      borderRadius: 6,
    },
  ],
};

const options = {
  responsive: true,
  plugins: {
    legend: {
      labels: { color: "#39FF14" },
    },
    title: {
      display: true,
      text: "Consumo Diario",
      color: "#39FF14",
      font: { size: 18 },
    },
  },
  scales: {
    x: { ticks: { color: "#39FF14" }, grid: { color: "#222" } },
    y: { ticks: { color: "#39FF14" }, grid: { color: "#222" } },
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
