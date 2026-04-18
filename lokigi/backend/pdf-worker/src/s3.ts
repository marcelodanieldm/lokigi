import { GetObjectCommand, PutObjectCommand, S3Client } from "@aws-sdk/client-s3";
import { getSignedUrl } from "@aws-sdk/s3-request-presigner";
import { config } from "./config.js";

const s3 = new S3Client({ region: config.s3Region });

export async function uploadPdfAndGetSignedUrl(
  objectKey: string,
  body: Buffer,
  ttlSeconds: number,
): Promise<{ signedUrl: string; expiresAtIso: string }> {
  await s3.send(
    new PutObjectCommand({
      Bucket: config.s3Bucket,
      Key: objectKey,
      Body: body,
      ContentType: "application/pdf",
      CacheControl: "private,max-age=0,no-cache",
    }),
  );

  const command = new GetObjectCommand({
    Bucket: config.s3Bucket,
    Key: objectKey,
  });

  const signedUrl = await getSignedUrl(s3, command, { expiresIn: ttlSeconds });
  const expiresAt = new Date(Date.now() + ttlSeconds * 1000);

  return {
    signedUrl,
    expiresAtIso: expiresAt.toISOString(),
  };
}
