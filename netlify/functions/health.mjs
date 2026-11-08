// GET /api/health — 메일 설정 점검용. 키 값은 절대 보여 주지 않고, 있는지와 이름만 알려 준다.
import { env } from "./lib/common.mjs";

export default async () => {
  const names = Object.keys(process.env).filter((k) => /resend|^re_/i.test(k)).map((k) => (k.startsWith("re_") ? "re_…(키가 이름 칸에 들어감)" : k));
  const key = env("RESEND_API_KEY");
  return new Response(JSON.stringify({
    resend_key_set: !!key,
    looks_like_resend_key: key.startsWith("re_"),
    related_variable_names: names,
  }, null, 2), { headers: { "content-type": "application/json; charset=utf-8", "cache-control": "no-store" } });
};

export const config = { path: "/api/health" };
