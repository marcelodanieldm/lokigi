import express from "express";
import { config } from "./config.js";
import { pdfQueue } from "./worker.js";

export function startHttpServer(): void {
  const app = express();
  app.use(express.json({ limit: "256kb" }));

  app.get("/health", (_req, res) => {
    res.json({ ok: true, queue: config.queueName });
  });

  app.post("/enqueue", async (req, res) => {
    const token = req.header("X-Worker-Token") || "";
    if (config.authToken && token !== config.authToken) {
      return res.status(401).json({ error: "unauthorized" });
    }

    const reportId = String(req.body?.report_id || "").trim();
    const ttlSeconds = Number(req.body?.signed_url_ttl_seconds || config.signedUrlTtlSeconds);
    if (!reportId) {
      return res.status(400).json({ error: "report_id is required" });
    }

    const job = await pdfQueue.add("generate-monthly-report-pdf", {
      report_id: reportId,
      signed_url_ttl_seconds: ttlSeconds,
      requested_at: req.body?.requested_at,
    });

    return res.status(202).json({
      status: "queued",
      queue: config.queueName,
      job_id: job.id,
      report_id: reportId,
    });
  });

  app.listen(config.port, () => {
    console.log(`[pdf-worker] HTTP server listening on :${config.port}`);
  });
}
