"use client";
import dynamic from "next/dynamic";
import { useRef } from "react";
import ImpactReport from "../components/ImpactReport";
import { useSearchParams } from "next/navigation";

// next-pdf: npm install @react-pdf/renderer
import { PDFDownloadLink, Page, Text, View, Document, StyleSheet, Image } from "@react-pdf/renderer";
import { useState, RefObject } from "react";
import { Radar } from "react-chartjs-2";

// Helper para renderizar el ImpactReport en PDF (simplificado)
const styles = StyleSheet.create({
  page: { backgroundColor: "#18181b", color: "#fff", fontFamily: "monospace", padding: 32 },
  section: { marginBottom: 24 },
  h1: { fontSize: 32, color: "#39FF14", marginBottom: 16 },
  h2: { fontSize: 20, color: "#39FF14", marginBottom: 8 },
  text: { fontSize: 14, marginBottom: 8 },
  table: { flexDirection: "column", width: "auto", marginBottom: 16 },
  row: { flexDirection: "row" },
  cell: { padding: 4, fontSize: 12, border: "1px solid #333" }
});

// Tipos explícitos para las props
type Photo = { url: string; lat: number; lon: number };
type Ranking = { name: string; score: number };
type ImpactReportPDFProps = {
  score: number;
  improvements: string[];
  photos: Photo[];
  ranking: Ranking[];
  radarImg?: string | null;
};

function ImpactReportPDF({ score, improvements, photos, ranking, radarImg }: ImpactReportPDFProps) {
  return (
    <Document>
      <Page size="A4" style={styles.page}>
        <View style={styles.section}>
          <Text style={styles.h1}>Lokigi Impact Report</Text>
          <Text style={styles.text}>Score Actual: {score}</Text>
        </View>
        <View style={styles.section}>
          <Text style={styles.h2}>Mejoras Realizadas</Text>
          {improvements.map((item, i) => <Text key={i} style={styles.text}>• {item}</Text>)}
        </View>
        <View style={styles.section}>
          <Text style={styles.h2}>Fotos Optimizadas con Geo-tag</Text>
          {photos.map((p, i) => <Text key={i} style={styles.text}>Lat: {p.lat}, Lon: {p.lon}</Text>)}
        </View>
        <View style={styles.section}>
          <Text style={styles.h2}>Ranking de Competencia</Text>
          <View style={styles.table}>
            {ranking.map((comp, i) => (
              <View key={i} style={styles.row}>
                <Text style={styles.cell}>{i + 1}</Text>
                <Text style={styles.cell}>{comp.name}</Text>
                <Text style={styles.cell}>{comp.score}</Text>
              </View>
            ))}
          </View>
        </View>
        <View style={styles.section}>
          <Text style={styles.h2}>Tu Radar de Protección</Text>
          <Text style={styles.text}>¿Qué pasaría si la competencia reacciona y tú no tienes monitoreo activo?</Text>
          {radarImg && (
            <Image src={radarImg} style={{ width: 320, height: 320, marginTop: 12, borderRadius: 12 }} />
          )}
        </View>
      </Page>
    </Document>
  );
// ...existing code...

  // Recibe datos desde query params
  const params = useSearchParams();
  const [radarImgState, setRadarImgState] = useState<string | null>(null);
  const scoreVal = Number(params.get("score")) || 85;
  const improvementsVal = params.getAll("improvements")?.length
    ? params.getAll("improvements")
    : ["Optimización de perfil Google My Business", "Actualización de NAP y fotos geolocalizadas", "Mejora de reputación y respuesta a reseñas"];
  const photosVal = params.getAll("photos")?.length
    ? JSON.parse(params.get("photos"))
    : [ { url: "/demo/photo1.jpg", lat: -34.6, lon: -58.4 }, { url: "/demo/photo2.jpg", lat: -34.61, lon: -58.41 } ];
  const rankingVal = params.getAll("ranking")?.length
    ? JSON.parse(params.get("ranking"))
    : [ { name: "Tu Negocio", score: 85 }, { name: "Competidor A", score: 78 }, { name: "Competidor B", score: 72 } ];
  const radarData = params.get("radarData")
    ? JSON.parse(params.get("radarData"))
    : {
        labels: ["Reputación", "SEO Local", "Visual", "NAP"],
        datasets: [
          { label: "Antes", data: [60, 55, 50, 70] },
          { label: "Después", data: [85, 80, 90, 95] }
        ]
      };

  // Captura el canvas del radar como imagen base64
  function handleRadarRef(node: any) {
    if (node && !radarImgState) {
      const canvas = node?.canvas as HTMLCanvasElement | undefined;
      if (canvas) setRadarImgState(canvas.toDataURL("image/png"));
    }
  }

  return (
    <div className="min-h-screen bg-gray-950 text-white p-8">
      <h1 className="text-3xl font-bold mb-6 text-[#39FF14]">Reporte de Impacto</h1>
      <ImpactReport
        score={scoreVal}
        improvements={improvementsVal}
        photos={photosVal}
        ranking={rankingVal}
        radarData={radarData}
      />
      {/* Renderizar el radar oculto para exportar imagen */}
      <div style={{ position: "absolute", left: -9999, top: -9999 }}>
        <Radar
          data={radarData}
          options={{
            scales: {
              r: {
                angleLines: { display: false },
                suggestedMin: 0,
                suggestedMax: 100,
                pointLabels: { color: "#39FF14", font: { size: 14 } },
                grid: { color: "#333" },
                ticks: { color: "#39FF14" }
              }
            },
            plugins: {
              legend: { labels: { color: "#39FF14" } }
            }
          }}
          ref={handleRadarRef}
        />
      </div>
      <div className="mt-8">
        <PDFDownloadLink
          document={<ImpactReportPDF score={scoreVal} improvements={improvementsVal} photos={photosVal} ranking={rankingVal} radarImg={radarImgState} />}
          fileName="lokigi-impact-report.pdf"
        >
          {({ loading }) => (
            <button className="bg-[#39FF14] text-black font-bold px-6 py-2 rounded-lg hover:scale-105 transition">
              {loading ? "Generando PDF..." : "Descargar PDF"}
            </button>
          )}
        </PDFDownloadLink>
      </div>
    </div>
  );
}
