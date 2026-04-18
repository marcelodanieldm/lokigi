import { Queue, Worker } from "bullmq";
import IORedis from "ioredis";

import { config } from "./config.js";
import {
  getTopMonthlyReviews,
  getMonthlyReportById,
  markPdfFailed,
  markPdfProcessing,
  markPdfReady,
} from "./db.js";
import { generateExecutiveSummary } from "./executive-summary.js";
import { renderHtmlToPdfBuffer } from "./pdf.js";
import { buildReportHtml } from "./report-html.js";
import { uploadPdfAndGetSignedUrl } from "./s3.js";

export const redis = new IORedis(config.redisUrl, { maxRetriesPerRequest: null });

export const pdfQueue = new Queue(config.queueName, {
  connection: redis,
  defaultJobOptions: {
    attempts: 3,
    removeOnComplete: 100,
    removeOnFail: 200,
    backoff: {
      type: "exponential",
      delay: 5000,
    },
  },
});

export const pdfWorker = new Worker(
  config.queueName,
  async (job) => {
    const reportId = String(job.data?.report_id || "");
    if (!reportId) {
      throw new Error("Missing report_id in job payload");
    }

    await markPdfProcessing(reportId);

    try {
      const row = await getMonthlyReportById(reportId);
      if (!row) {
        throw new Error(`Monthly report not found: ${reportId}`);
      }

      const summary = await generateExecutiveSummary({
        business_name: row.payload?.business_name || "Negocio",
        month_label: `${row.month}/${row.year}`,
        metrics: row.payload?.kpis || {},
        sentiment: row.payload?.sentiment || {},
      });

      const topReviews = await getTopMonthlyReviews(row.user_id, row.year, row.month);

      const html = buildReportHtml(row, summary, topReviews);
      const pdfBuffer = await renderHtmlToPdfBuffer(html);

      const objectKey = `${config.s3Prefix}/${row.user_id}/${row.year}-${String(row.month).padStart(2, "0")}-report.pdf`;
      const ttl = Number(job.data?.signed_url_ttl_seconds || config.signedUrlTtlSeconds);
      const { signedUrl, expiresAtIso } = await uploadPdfAndGetSignedUrl(objectKey, pdfBuffer, ttl);

      await markPdfReady(reportId, {
        objectKey,
        signedUrl,
        expiresAtIso,
        summary,
      });
    } catch (error) {
      const message = error instanceof Error ? error.message : "Unknown PDF generation error";
      await markPdfFailed(reportId, message);
      throw error;
    }
  },
  {
    connection: redis,
    concurrency: 2,
  },
);

pdfWorker.on("completed", (job) => {
  console.log(`[pdf-worker] completed job ${job.id}`);
});

pdfWorker.on("failed", (job, err) => {
  console.error(`[pdf-worker] failed job ${job?.id}:`, err.message);
});
