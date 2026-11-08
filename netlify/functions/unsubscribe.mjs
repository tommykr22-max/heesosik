// GET  /api/unsubscribe?e=<hash>&t=<token>  → 확인 버튼이 있는 페이지 (메일 보안 검사기가 링크만 열어도 해지되지 않게)
// POST 같은 주소                             → 실제 해지 (페이지의 버튼, 또는 메일 앱의 원클릭 수신 거부)
import { subs, safeEq, page } from "./lib/common.mjs";

// 전달받은 사람이 눌렀을 때 남의 구독임을 알아볼 수 있게 주소 일부만 보여 준다
const mask = (email) => {
  const [id, dom] = String(email).split("@");
  return `${id.slice(0, 2)}${"*".repeat(Math.max(3, id.length - 2))}@${dom}`;
};

export default async (req) => {
  const u = new URL(req.url);
  const h = (u.searchParams.get("e") || "").replace(/[^a-f0-9]/g, "");
  const t = u.searchParams.get("t") || "";
  const store = subs();
  const a = h ? await store.get(`active/${h}`, { type: "json" }) : null;
  const valid = a && safeEq(a.token, t);

  if (req.method === "POST") {
    let fromPage = false;
    try { fromPage = (await req.formData()).get("via") === "page"; } catch {}
    if (valid) await store.delete(`active/${h}`);
    if (!fromPage) return new Response(valid || !a ? "ok" : "bad token", { status: valid || !a ? 200 : 400 });
    if (!valid && a) return page("링크를 확인해 주세요", "잘못된 링크예요. 받은 메일 속 링크를 다시 눌러 주세요.", 400);
    return page("수신 거부되었어요", "더 이상 희소식 메일을 보내지 않아요. 그동안 고마웠어요. 언제든 다시 찾아 주세요.");
  }

  if (!a) return page("이미 수신 거부되었어요", "희소식 메일을 더 보내지 않아요.");
  if (!valid) return page("링크를 확인해 주세요", "잘못된 링크예요. 받은 메일 속 링크를 다시 눌러 주세요.", 400);
  const action = `/api/unsubscribe?e=${h}&t=${encodeURIComponent(t)}`;
  return page("메일 수신을 그만두시겠어요?",
    `<b>${mask(a.email)}</b> 님의 구독이 해지돼요.<br>다른 분께 전달받은 메일이라면 누르지 마시고, <a href="/#subscribe">여기서 직접 구독</a>해 주세요.</p><p>`+
    `아래 버튼을 누르면 이 주소로 희소식 메일을 더 보내지 않아요.</p><form method="POST" action="${action}" style="margin-top:20px"><input type="hidden" name="via" value="page"><button class="cta" style="position:static;border:0;cursor:pointer;font:inherit">수신 거부하기</button></form><p>`);
};

export const config = { path: "/api/unsubscribe" };
