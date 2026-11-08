// GET /api/confirm?e=<hash>&t=<token>
import { subs, safeEq, page } from "./lib/common.mjs";

export default async (req) => {
  const u = new URL(req.url);
  const h = (u.searchParams.get("e") || "").replace(/[^a-f0-9]/g, "");
  const t = u.searchParams.get("t") || "";
  const store = subs();
  if (h && (await store.get(`active/${h}`))) return page("이미 구독 중이에요", "매일 아침 희소식을 메일로 보내 드릴게요.");
  const p = h ? await store.get(`pending/${h}`, { type: "json" }) : null;
  if (!p || !safeEq(p.token, t)) return page("링크를 확인해 주세요", "만료되었거나 잘못된 링크예요. 사이트에서 다시 구독해 주세요.", 400);
  await store.setJSON(`active/${h}`, { email: p.email, token: p.token, created: p.created, agreedAt: p.agreedAt, confirmedAt: Date.now() });
  await store.delete(`pending/${h}`);
  return page("구독이 완료되었어요 ☀", "내일 아침부터 매일 희소식을 메일로 보내 드릴게요.");
};

export const config = { path: "/api/confirm" };
