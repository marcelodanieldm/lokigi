import "dotenv/config";

function required(name: string, fallback?: string): string {
  const value = process.env[name] || fallback;
  if (!value) {
    throw new Error(`Missing required env var: ${name}`);
  }
  return value;
}

function toPgConnectionString(url: string): string {
  if (url.startsWith("postgresql+psycopg://")) {
    return url.replace("postgresql+psycopg://", "postgresql://");
  }
  return url;
}

export const config = {
  nodeEnv: process.env.NODE_ENV || "development",
  port: Number(process.env.PDF_WORKER_PORT || 4310),
  authToken: process.env.PDF_WORKER_ENQUEUE_TOKEN || "",
  redisUrl: required("REDIS_URL", "redis://localhost:6379"),
  queueName: process.env.PDF_QUEUE_NAME || "monthly-report-pdf",
  databaseUrl: toPgConnectionString(required("DATABASE_URL")),
  s3Region: required("AWS_REGION"),
  s3Bucket: required("AWS_S3_BUCKET"),
  s3Prefix: process.env.S3_REPORT_PREFIX || "monthly-reports",
  signedUrlTtlSeconds: Number(process.env.PDF_SIGNED_URL_TTL_SECONDS || 604800),
  appDomain: process.env.APP_DOMAIN || "localhost:8000",
  logoUrl: process.env.LOKIGI_LOGO_URL || "",
  llmEnabled: (process.env.EXEC_SUMMARY_LLM_ENABLED || "false").toLowerCase() === "true",
  llmApiBase: process.env.EXEC_SUMMARY_LLM_API_BASE || "https://api.openai.com/v1",
  llmApiKey: process.env.EXEC_SUMMARY_LLM_API_KEY || "",
  llmModel: process.env.EXEC_SUMMARY_LLM_MODEL || "gpt-4o-mini",
};
