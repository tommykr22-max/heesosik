// 희소식 구독 메일 공용 도구
import { getStore } from "@netlify/blobs";
import crypto from "node:crypto";

export const SITE = (process.env.SITE_URL || "https://heesosik.news").replace(/\/$/, "");
export const FROM = process.env.MAIL_FROM || "희소식 <news@heesosik.news>";

// 테스트 때는 globalThis.__heesosikStores 로 가짜 저장소를 끼워 넣을 수 있다
export const subs = () => globalThis.__heesosikStores?.subscribers || getStore({ name: "subscribers", consistency: "strong" });
export const state = () => globalThis.__heesosikStores?.state || getStore({ name: "newsletter-state", consistency: "strong" });

export const normEmail = (s) => String(s || "").trim().toLowerCase();
export const validEmail = (s) => s.length <= 254 && /^[^\s@<>()",;:]+@[^\s@<>()",;:]+\.[a-z]{2,}$/i.test(s);
export const hashEmail = (email) => crypto.createHash("sha256").update(email).digest("hex").slice(0, 40);
export const newToken = () => crypto.randomBytes(24).toString("hex");
export const safeEq = (a, b) => {
  const x = Buffer.from(String(a || "")), y = Buffer.from(String(b || ""));
  return x.length === y.length && crypto.timingSafeEqual(x, y);
};

export const unsubUrl = (h, t) => `${SITE}/api/unsubscribe?e=${h}&t=${t}`;
export const confirmUrl = (h, t) => `${SITE}/api/confirm?e=${h}&t=${t}`;

export const json = (status, body) =>
  new Response(JSON.stringify(body), { status, headers: { "content-type": "application/json; charset=utf-8" } });

export const page = (title, msg, status = 200) =>
  new Response(`<!DOCTYPE html><html lang="ko"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>${title} — 희소식</title><link rel="stylesheet" href="/assets/style.css"></head><body><header class="sub-hero"><div class="topbar"><a class="logo" href="/" style="text-decoration:none"><i></i>희소식</a></div><h1>${title}</h1><p>${msg}</p></header><main class="wrap" style="text-align:center;padding:40px 0"><a class="cta" href="/" style="position:static">오늘의 희소식 보기</a></main></body></html>`,
    { status, headers: { "content-type": "text/html; charset=utf-8" } });

// Resend로 메일 보내기. list가 2개 이상이면 batch API(한 번에 최대 100통)를 쓴다.
export async function sendMail(list) {
  const key = process.env.RESEND_API_KEY;
  if (!key) throw new Error("RESEND_API_KEY is not set");
  const batch = list.length > 1;
  const res = await fetch(batch ? "https://api.resend.com/emails/batch" : "https://api.resend.com/emails", {
    method: "POST",
    headers: { authorization: `Bearer ${key}`, "content-type": "application/json" },
    body: JSON.stringify(batch ? list : list[0]),
  });
  if (!res.ok) throw new Error(`Resend ${res.status}: ${(await res.text()).slice(0, 300)}`);
  return res.json();
}
