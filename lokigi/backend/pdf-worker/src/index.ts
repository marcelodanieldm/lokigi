import { startHttpServer } from "./server.js";
import { pdfWorker } from "./worker.js";

startHttpServer();

console.log("[pdf-worker] worker online", {
  concurrency: 2,
  queue: pdfWorker.name,
});
