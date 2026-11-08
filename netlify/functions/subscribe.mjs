// POST /api/subscribe  {email, agree(동의 체크), website(봇 걸러내기용 빈 칸)}
import { subs, normEmail, validEmail, hashEmail, newToken, confirmUrl, sendMail, json, FROM, SITE } from "./lib/common.mjs";

export default async (req) => {
  if (req.method !== "POST") return json(405, { ok: false, msg: "잘못된 요청이에요." });
  let body = {};
  try {
    const ct = req.headers.get("content-type") || "";
    body = ct.includes("json") ? await req.json() : Object.fromEntries(await req.formData());
  } catch { return json(400, { ok: false, msg: "잘못된 요청이에요." }); }

  if (body.website) return json(200, { ok: true, msg: "확인 메일을 보냈어요." }); // 봇
  const email = normEmail(body.email);
  if (!validEmail(email)) return json(400, { ok: false, msg: "이메일 주소를 다시 확인해 주세요." });
  if (body.agree !== true && body.agree !== "1" && body.agree !== "on") return json(400, { ok: false, msg: "개인정보 수집·이용에 동의해 주세요." });
  if (!process.env.RESEND_API_KEY) return json(503, { ok: false, msg: "메일 구독은 곧 열립니다. 조금만 기다려 주세요 ☀" });

  const store = subs();
  const h = hashEmail(email);
  if (await store.get(`active/${h}`)) return json(200, { ok: true, msg: "이미 구독 중이에요. 고마워요 ☀" });

  const prev = await store.get(`pending/${h}`, { type: "json" });
  if (prev && Date.now() - prev.sentAt < 60_000) return json(429, { ok: false, msg: "확인 메일을 방금 보냈어요. 메일함(스팸함 포함)을 확인해 주세요." });
  const token = prev?.token || newToken();
  await store.setJSON(`pending/${h}`, { email, token, created: prev?.created || Date.now(), sentAt: Date.now(), agreedAt: Date.now() });

  const link = confirmUrl(h, token);
  try {
    await sendMail([{
      from: FROM, to: [email], subject: "[희소식] 구독을 확인해 주세요",
      text: `희소식 구독 신청을 받았어요.\n아래 링크를 누르면 구독이 완료됩니다.\n\n${link}\n\n직접 신청하지 않으셨다면 이 메일은 무시하셔도 됩니다.\n${SITE}`,
      html: `<div style="font-family:sans-serif;max-width:520px;margin:auto;padding:24px;color:#2b2118"><h2 style="margin:0 0 12px">☀️ 희소식 구독 확인</h2><p>희소식 구독 신청을 받았어요. 아래 버튼을 누르면 구독이 완료되고, 매일 아침 희소식을 메일로 보내 드려요.</p><p style="margin:28px 0"><a href="${link}" style="background:#F08A24;color:#fff;padding:14px 26px;border-radius:99px;text-decoration:none;font-weight:700">구독 확인하기</a></p><p style="color:#8a7a6a;font-size:13px">직접 신청하지 않으셨다면 이 메일은 무시하셔도 됩니다.</p></div>`,
    }]);
  } catch (err) {
    console.error("confirm mail failed", err);
    return json(502, { ok: false, msg: "메일을 보내지 못했어요. 잠시 뒤 다시 시도해 주세요." });
  }
  return json(200, { ok: true, msg: "확인 메일을 보냈어요. 메일 속 버튼을 누르면 구독이 완료돼요 ☀" });
};

export const config = { path: "/api/subscribe" };
