import { Pool } from "pg";
import { config } from "./config.js";

export type MonthlyReportRow = {
  id: string;
  user_id: string;
  year: number;
  month: number;
  payload: any;
  generated_at: string;
};

export type ExecutiveSummary = {
  paragraph_1_client_voice: string;
  paragraph_2_key_achievement: string;
  paragraph_3_improvement_opportunity: string;
};

export type TopReviewRow = {
  review_id: string;
  author_display_name: string | null;
  rating: number | null;
  comment: string | null;
  reply_public_text: string | null;
};

export const pool = new Pool({ connectionString: config.databaseUrl });

export async function getMonthlyReportById(reportId: string): Promise<MonthlyReportRow | null> {
  const result = await pool.query<MonthlyReportRow>(
    `select id, user_id, year, month, payload, generated_at
     from monthly_reports
     where id = $1`,
    [reportId],
  );
  return result.rows[0] || null;
}

export async function markPdfProcessing(reportId: string): Promise<void> {
  await pool.query(
    `update monthly_reports
     set pdf_status = 'processing',
         pdf_error = null
     where id = $1`,
    [reportId],
  );
}

export async function markPdfReady(
  reportId: string,
  params: {
    objectKey: string;
    signedUrl: string;
    expiresAtIso: string;
    summary: ExecutiveSummary;
  },
): Promise<void> {
  await pool.query(
    `update monthly_reports
     set pdf_status = 'ready',
         pdf_object_key = $2,
         pdf_signed_url = $3,
         pdf_signed_url_expires_at = $4::timestamptz,
         pdf_generated_at = now(),
         executive_summary = $5::json,
         pdf_error = null
     where id = $1`,
    [
      reportId,
      params.objectKey,
      params.signedUrl,
      params.expiresAtIso,
      JSON.stringify(params.summary),
    ],
  );
}

export async function markPdfFailed(reportId: string, errorMessage: string): Promise<void> {
  await pool.query(
    `update monthly_reports
     set pdf_status = 'failed',
         pdf_error = $2
     where id = $1`,
    [reportId, errorMessage.slice(0, 1000)],
  );
}

export async function getTopMonthlyReviews(
  userId: string,
  year: number,
  month: number,
): Promise<TopReviewRow[]> {
  const result = await pool.query<TopReviewRow>(
    `select
        r.review_id,
        r.author_display_name,
        r.rating,
        r.comment,
        r.reply_public_text
      from reviews r
      join google_connections gc on gc.id = r.connection_id
      where gc.user_id = $1::uuid
        and date_part('year', coalesce(r.create_time, r.created_at)) = $2
        and date_part('month', coalesce(r.create_time, r.created_at)) = $3
        and r.comment is not null
      order by coalesce(r.rating, 0) desc, coalesce(r.create_time, r.created_at) desc
      limit 3`,
    [userId, year, month],
  );
  return result.rows;
}
