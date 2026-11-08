// 30분마다 실행: 오늘(서울 기준) 새 호가 배포됐고 아직 안 보냈으면 확인된 구독자 전원에게 보낸다.
// 한 번에 다 못 보내면 어디까지 보냈는지 기록해 두고 다음 실행 때 이어서 보낸다.
import { subs, state, unsubUrl, sendMail, SITE, FROM } from "./lib/common.mjs";

const BATCH = 100;          // Resend batch API 한 번에 최대 100통
const TIME_BUDGET = 20_000; // 예약 함수 제한(30초) 안에서 여유 있게

const seoulToday = () => new Date(Date.now() + 9 * 3600_000).toISOString().slice(0, 10);

async function activeList(store) {
  const keys = [];
  for await (const pageRes of store.list({ prefix: "active/", paginate: true })) {
    for (const b of pageRes.blobs) keys.push(b.key);
  }
  keys.sort();
  return keys;
}

async function getMany(store, keys) {
  const out = [];
  for (let i = 0; i < keys.length; i += 25) {
    const part = await Promise.all(keys.slice(i, i + 25).map((k) => store.get(k, { type: "json" })));
    part.forEach((v, j) => v && out.push({ h: keys[i + j].slice(7), ...v }));
  }
  return out;
}

export async function run({ fetchImpl = fetch, now = Date.now } = {}) {
  const started = now();
  if (process.env.NEWSLETTER_PAUSED === "1") return { skipped: "paused" };
  if (!process.env.RESEND_API_KEY) return { skipped: "no RESEND_API_KEY" };

  const res = await fetchImpl(`${SITE}/newsletter/latest.json?ts=${started}`);
  if (!res.ok) return { skipped: `latest.json ${res.status}` };
  const nl = await res.json();
  if (nl.date !== seoulToday()) return { skipped: `latest is ${nl.date}, not today` };

  const st = state();
  const key = `issue-${nl.no}`;
  const s = (await st.get(key, { type: "json" })) || { offset: 0, sent: 0, startedAt: started };
  if (s.done) return { skipped: `issue ${nl.no} already sent` };

  const store = subs();
  const keys = await activeList(store);
  let offset = s.offset;
  while (offset < keys.length && now() - started < TIME_BUDGET) {
    const people = await getMany(store, keys.slice(offset, offset + BATCH));
    const mails = people.map((p) => {
      const un = unsubUrl(p.h, p.token);
      return {
        from: FROM, to: [p.email], subject: nl.subject,
        html: nl.html.replaceAll("%%UNSUB%%", un),
        text: nl.text.replaceAll("%%UNSUB%%", un),
        headers: { "List-Unsubscribe": `<${un}>`, "List-Unsubscribe-Post": "List-Unsubscribe=One-Click" },
      };
    });
    if (mails.length) await sendMail(mails);
    offset += BATCH;
    s.sent += mails.length;
    await st.setJSON(key, { ...s, offset });
    await new Promise((r) => setTimeout(r, 600)); // Resend 초당 요청 제한
  }
  const done = offset >= keys.length;
  await st.setJSON(key, { ...s, offset, done, finishedAt: done ? now() : undefined });
  console.log(`issue ${nl.no}: sent ${s.sent}/${keys.length}${done ? " (done)" : " (continuing next run)"}`);
  return { no: nl.no, sent: s.sent, total: keys.length, done };
}

export default async () => {
  try { console.log(JSON.stringify(await run())); }
  catch (err) { console.error("newsletter-send failed", err); }
};

export const config = { schedule: "*/30 * * * *" };
