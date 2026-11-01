#!/usr/bin/env python3
"""희소식 사이트 빌드: issues/N.json → index.html, issues/N.html, archive.html, sitemap.xml

사용법: python3 build.py
새 호를 내려면 issues/ 에 다음 번호의 JSON 파일을 추가하고 다시 실행하면 된다.
"""
import json, glob, os, html, datetime, sys

SITE = "https://heesosik.news"
ROOT = os.path.dirname(os.path.abspath(__file__))
DAYS = ["월", "화", "수", "목", "금", "토", "일"]
CATS = {
    "people": ("사람", "var(--c-people)", "linear-gradient(135deg,#FFE0BC,#FFF6EA)"),
    "animal": ("동물", "var(--c-animal)", "linear-gradient(135deg,#F2DCC2,#FBF3EA)"),
    "health": ("건강", "var(--c-health)", "linear-gradient(135deg,#FFD0DA,#FFF0F3)"),
    "sci":    ("과학", "var(--c-sci)",    "linear-gradient(135deg,#BFE3F2,#E8F6FB)"),
    "earth":  ("지구", "var(--c-earth)",  "linear-gradient(135deg,#C7EBCF,#EFFAEF)"),
    "space":  ("우주", "var(--c-space)",  "linear-gradient(135deg,#D9CCF5,#F3EEFD)"),
}
STORY_KEYS = ["id", "cat", "emoji", "where", "title", "body", "why", "quote", "who", "src", "url"]
e = lambda s: html.escape(str(s), quote=True)


def kdate(d):
    dt = datetime.date.fromisoformat(d)
    return f"{dt.year}년 {dt.month}월 {dt.day}일 {DAYS[dt.weekday()]}요일"


def validate(iss, path):
    errs = []
    for k in ["no", "date", "daily_quote", "numbers", "feature", "stories"]:
        if k not in iss:
            errs.append(f"missing {k}")
    for s in [iss.get("feature", {})] + iss.get("stories", []):
        for k in STORY_KEYS:
            if not s.get(k):
                errs.append(f"story {s.get('id')}: missing {k}")
        if s.get("cat") not in CATS:
            errs.append(f"story {s.get('id')}: bad cat {s.get('cat')}")
        if not str(s.get("url", "")).startswith("http"):
            errs.append(f"story {s.get('id')}: bad url")
    if len(iss.get("numbers", [])) != 3:
        errs.append("numbers must have 3 items")
    if errs:
        sys.exit(f"{path}: " + "; ".join(errs))


def head(title, desc, canonical):
    return f"""<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{e(title)}</title>
<meta name="description" content="{e(desc)}">
<link rel="canonical" href="{canonical}">
<meta name="naver-site-verification" content="e266edb50e648d63de5fa33eac142656ee8fe846">
<meta property="og:type" content="website">
<meta property="og:site_name" content="희소식">
<meta property="og:title" content="{e(title)}">
<meta property="og:description" content="{e(desc)}">
<meta property="og:url" content="{canonical}">
<meta property="og:image" content="https://heesosik.news/assets/og.png">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="630">
<meta name="twitter:card" content="summary_large_image">
<link rel="icon" href="data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100'><circle cx='50' cy='50' r='40' fill='%23F7B32B'/></svg>">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Noto+Serif+KR:wght@500;700;900&family=Noto+Sans+KR:wght@400;500;700&display=swap" rel="stylesheet">
<link rel="stylesheet" href="/assets/style.css">
</head>
<body>
"""


FOOTER = """<footer>
  <div class="wrap">
    <div>
      <div class="logo"><i></i>희소식</div>
      지칠 때 열어 보는 좋은 소식.<br>
      모든 기사는 원문을 바탕으로 희소식이 직접 요약해 쓴 글이며, 원문 출처를 함께 밝힙니다.<br>
      <a href="/about.html">희소식을 시작하며</a> · <a href="/archive.html">지난 호 모아 보기</a> · <a href="https://pf.kakao.com/_ZXUWX" target="_blank" rel="noopener">카카오톡 채널 「희소식」</a><br>
      <a href="/contact.html">문의</a> · <a href="/privacy.html">개인정보처리방침</a>
    </div>
    <div>
      <h4>편집 원칙</h4>
      검증된 매체의 보도만 다룹니다 · 정치적 편 가르기를 하지 않습니다 · 좋은 소식이라도 과장하지 않습니다
    </div>
  </div>
</footer>
<div class="toast" id="toast"></div>
"""


def story_card(s):
    name, color, bg = CATS[s["cat"]]
    return f"""<article class="card" id="s-{e(s['id'])}" data-cat="{e(s['cat'])}">
  <div class="band" style="background:{bg}"><span class="flag">{e(s['where'])}</span>{e(s['emoji'])}</div>
  <div class="body"><span class="tag" style="background:{color}">{name}</span>
    <h3>{e(s['title'])}</h3><p>{e(s['body'])}</p>
    <div class="why"><b>왜 희소식일까?</b> {e(s['why'])}</div>
    <div class="quote">{e(s['quote'])}<cite>— {e(s['who'])}</cite></div>
    <div class="foot"><a href="{e(s['url'])}" target="_blank" rel="noopener">출처: {e(s['src'])} ↗</a>
      <div class="acts"><button class="btn-ic like" data-id="{e(s['id'])}">♡ <span>0</span></button><button class="btn-ic share" data-t="{e(s['title'])}">공유</button></div></div>
  </div>
</article>"""


def issue_page(iss, prev_no, next_no, is_home):
    f = iss["feature"]
    fname, fcolor, fbg = CATS[f["cat"]]
    no, date = iss["no"], iss["date"]
    canonical = SITE + "/" if is_home else f"{SITE}/issues/{no}.html"
    title = f"희소식 제{no}호 — {f['title']}"
    if is_home:
        title = "희소식 — 지칠 때 열어 보는 좋은 소식"
    desc = f"{kdate(date)} 희소식: " + " · ".join([f["title"]] + [s["title"] for s in iss["stories"][:2]])
    q = iss["daily_quote"]
    all_stories = [f] + iss["stories"]
    ids = {x["id"] for x in all_stories}

    def num_target(n):
        if n.get("ref") in ids:
            return "s-" + n["ref"]
        for x in all_stories:  # ref 없으면 숫자가 들어 있는 기사를 찾는다
            if n["big"] in x["title"] or n["big"] in x["body"]:
                return "s-" + x["id"]
        return "today-news"
    nums = "".join(
        f'<a class="num" href="#{num_target(n)}"><b>{e(n["big"])}</b><span>{e(n["label"])}</span><em class="go">기사 보기 →</em></a>'
        for n in iss["numbers"])
    cats_present = []
    for s in iss["stories"]:
        if s["cat"] not in cats_present:
            cats_present.append(s["cat"])
    chips = '<button class="chip on" data-cat="all">전체</button>' + "".join(
        f'<button class="chip" data-cat="{c}">{CATS[c][0]}</button>' for c in cats_present)
    editor = ""
    if iss.get("editor_note"):
        editor = f'<section class="editor"><div class="av">✍️</div><div><b>편집장 한마디</b><p>{e(iss["editor_note"])}</p></div></section>'
    pager = '<nav class="pager">' + (
        f'<a class="prev" href="/issues/{prev_no}.html">← 제{prev_no}호</a>' if prev_no else "<span></span>") + (
        f'<a class="next" href="/issues/{next_no}.html">제{next_no}호 →</a>' if next_no else (
            '<a class="next" href="/archive.html">지난 호 모아 보기 →</a>')) + "</nav>"
    card_data = {"no": no, "date": kdate(date), "title": f["title"], "why": f["why"],
                 "quote": q["text"], "who": q["who"]}
    return head(title, desc, canonical) + f"""
<header class="hero">
  <div class="stars" id="stars"></div>
  <div class="topbar">
    <a class="logo" href="/" style="text-decoration:none"><i></i>희소식</a>
    <div class="tb-r"><a class="tb-link" href="/about.html">편집자의 글</a><div class="issue"><a href="/archive.html">제{no}호</a></div></div>
  </div>
  <div class="hero-inner">
    <div class="kicker">GOOD NEWS · DAILY</div>
    <h1>세상은 생각보다<br><em>괜찮습니다</em></h1>
    <p class="lead">나쁜 뉴스에 지친 당신을 위해, 전 세계의 좋은 소식만 골라 매일 한국어로 전합니다. 지칠 때 언제든 열어 보세요.</p>
    <div class="date">{kdate(date)} · 제{no}호</div>
    <a href="#today-news" class="cta">오늘의 희소식 보기 ↓</a>
  </div>
  <div class="sun"></div>
  <div class="horizon"></div>
</header>

<main class="wrap">
  <section class="numbers" aria-label="숫자로 보는 오늘">{nums}</section>
  {editor}
  <section class="daily">
    <div class="lbl">오늘의 한 줄</div>
    <blockquote>{e(q['text'])}</blockquote>
    <cite>— {e(q['who'])}</cite>
  </section>

  <div class="sec-head" id="today-news">
    <h2>오늘의 머리기사<small>지금 가장 마음을 밝혀 주는 소식</small></h2>
  </div>
  <article class="feature" id="s-{e(f['id'])}">
    <div class="art" style="background:{fbg}" aria-hidden="true"><span class="flag">{e(f['where'])}</span>{e(f['emoji'])}</div>
    <div class="body">
      <span class="tag" style="background:{fcolor}">{fname}</span>
      <h3>{e(f['title'])}</h3>
      <p>{e(f['body'])}</p>
      <div class="why"><b>왜 희소식일까?</b> {e(f['why'])}</div>
      <div class="quote">{e(f['quote'])}<cite>— {e(f['who'])}</cite></div>
      <div class="foot">
        <a href="{e(f['url'])}" target="_blank" rel="noopener">출처: {e(f['src'])} ↗</a>
        <div class="acts"><button class="btn-ic like" data-id="{e(f['id'])}">♡ <span>0</span></button><button class="btn-ic share" data-t="{e(f['title'])}">공유</button></div>
      </div>
    </div>
  </article>

  <div class="sharecard">
    <button id="saveCard">💬 카톡용 이미지 저장</button>
    <button id="saveStory" class="story">📸 인스타 스토리용</button>
    <small>단톡방·스토리에 좋은 소식 한 장 보내 보세요</small>
    <a class="kmini" href="https://pf.kakao.com/_ZXUWX/friend" target="_blank" rel="noopener">💛 카톡 채널로 매일 받기</a>
  </div>

  <div class="ad">광고 영역 · 애드센스 승인 후 노출됩니다</div>

  <div class="sec-head">
    <h2>세계 곳곳의 희소식<small>분야별로 골라 읽으세요</small></h2>
    <div class="chips" id="chips">{chips}</div>
  </div>
  <section class="grid" id="grid">
{chr(10).join(story_card(s) for s in iss['stories'])}
  </section>

  {pager}

  <section class="sponsor">
    <div>
      <h3>오늘의 희소식을<br>함께 전할 파트너를 찾습니다</h3>
      <p>좋은 소식 옆에 좋은 브랜드가 있어야 합니다. 희소식은 세상을 낫게 만드는 기업과 단체의 후원으로 운영됩니다.</p>
    </div>
    <div class="box">
      <ul>
        <li>하루 한 곳, 머리기사 후원 표기</li>
        <li>뉴스레터 상단 ‘오늘의 후원’ 소개</li>
        <li>지난 호 보관함 상단 배너</li>
      </ul>
      <div class="contact">후원·제휴 문의: 준비 중</div>
    </div>
  </section>

  <section class="news kakao">
    <h3>카카오톡으로 매일 받아 보세요</h3>
    <p>채널을 추가하면 새 희소식이 나올 때마다 카톡으로 만나요.</p>
    <a class="kbtn" href="https://pf.kakao.com/_ZXUWX/friend" target="_blank" rel="noopener">💛 카카오톡 채널 추가하기</a>
  </section>
</main>
{FOOTER}
<canvas id="cv" width="1080" height="1350" style="display:none"></canvas>
<script id="card-data" type="application/json">{json.dumps(card_data, ensure_ascii=False).replace('</', '<\\/')}</script>
<script src="/assets/app.js"></script>
</body>
</html>
"""


def archive_page(issues):
    rows = "\n".join(
        f'<li><a href="/issues/{i["no"]}.html"><span class="no">제{i["no"]}호</span>'
        f'<span class="t">{e(i["feature"]["title"])}</span><span class="d">{e(i["date"])}</span></a></li>'
        for i in sorted(issues, key=lambda x: -x["no"]))
    return head("희소식 — 지난 호 모아 보기", "희소식이 지금까지 전한 좋은 소식들", SITE + "/archive.html") + f"""
<header class="sub-hero">
  <div class="topbar"><a class="logo" href="/" style="text-decoration:none"><i></i>희소식</a></div>
  <h1>지난 호 모아 보기</h1>
  <p>지금까지 전한 좋은 소식 {len(issues)}호</p>
</header>
<main class="wrap"><ul class="arch">
{rows}
</ul></main>
{FOOTER}
<script src="/assets/app.js"></script>
</body></html>
"""


ABOUT_PARAS = [
    "아침에 일어나 거울 앞에 서서 웃음을 한 번 짓는 것만으로도 그날이 즐거울 확률이 높아집니다. 수년 전부터 좋은 소식을 전해, 사람들의 마음이 아주 조금이라도 편해지기를 기대해 왔습니다. 자그마한 소식이라도 즐겁게 봐 주시면 감사하겠습니다.",
    "사람들은 모두 지쳐 가고 있습니다. 온갖 미디어는 자극적이고 폭력적인 뉴스를 위주로 다루고, 그런 뉴스가 사람들의 이목을 끕니다. 사실 우리는 스스로 점점 부정적으로 변해 가고 있다는 것도 모른 채, 그저 안 좋은 소식에 노출되고 있습니다. 삶에 지친 분들이 다시 힘을 낼 수 있도록 돕고 싶습니다.",
    "그래서 희소식은 주로 감동적인 이야기를 다루려고 노력합니다. 힘들게 삶을 이어 가는 사람들을 돕는 이야기, 아직은 착하게 사는 것이 삶에 도움이 된다는 소식을 전하고자 합니다.",
    "희소식을 읽으시면서 단 0.1%라도 마음에 작은 변화가 일어나기를 바라 봅니다.",
]


def about_page():
    paras = "\n".join(f"<p>{e(x)}</p>" for x in ABOUT_PARAS)
    return head("희소식을 시작하며 — 편집자의 글", "희소식은 왜 좋은 소식만 전할까요. 편집자가 직접 쓴 창간의 글.", SITE + "/about.html") + f"""
<header class="sub-hero">
  <div class="topbar"><a class="logo" href="/" style="text-decoration:none"><i></i>희소식</a></div>
  <h1>희소식을 시작하며</h1>
  <p>편집자의 글</p>
</header>
<main class="wrap"><article class="letter">
{paras}
<p class="sign">— 희소식 편집자</p>
</article>
<section class="principles">
  <h2>희소식이 소식을 고르는 방법</h2>
  <ul>
    <li><b>사람 냄새 나는 이야기</b>를 먼저 고릅니다. 이웃을 돕는 사람, 묵묵히 제 몫을 다하는 사람, 사람과 동물의 우정.</li>
    <li><b>검증된 매체의 보도</b>만 다루고, 모든 소식에 원문 출처를 밝힙니다.</li>
    <li>원문을 옮기지 않고 <b>직접 요약</b>합니다. 좋은 소식이라도 과장하지 않습니다.</li>
    <li><b>편을 가르는 소식</b>은 다루지 않습니다.</li>
    <li>소식을 찾고 요약하는 일에는 AI의 도움을 받고, 무엇을 실을지와 방향은 편집자가 정합니다.</li>
  </ul>
  <p class="links"><a href="/">오늘의 희소식 보기</a> · <a href="/archive.html">지난 호 모아 보기</a> · <a href="https://pf.kakao.com/_ZXUWX" target="_blank" rel="noopener">카카오톡 채널 추가</a></p>
</section></main>
{FOOTER}
<script src="/assets/app.js"></script>
</body></html>
"""


def simple_page(slug, title, desc, h1, sub, body_html):
    return head(title, desc, f"{SITE}/{slug}.html") + f"""
<header class="sub-hero">
  <div class="topbar"><a class="logo" href="/" style="text-decoration:none"><i></i>희소식</a></div>
  <h1>{h1}</h1>
  <p>{sub}</p>
</header>
<main class="wrap"><article class="letter doc">
{body_html}
</article></main>
{FOOTER}
<script src="/assets/app.js"></script>
</body></html>
"""


CONTACT_HTML = """
<p>희소식에 전하고 싶은 좋은 소식, 기사 내용의 오류 제보, 후원·제휴 문의는 아래로 보내 주세요.</p>
<h2>카카오톡 채널</h2>
<p><a href="https://pf.kakao.com/_ZXUWX" target="_blank" rel="noopener">카카오톡 채널 「희소식」</a>을 추가하시면 소식을 받아 보실 수 있고, 채널을 통해 의견을 남기실 수 있습니다.</p>
<h2>오류 정정 원칙</h2>
<p>희소식의 모든 기사는 원문 출처를 함께 밝힙니다. 사실과 다른 내용이 확인되면 해당 호의 기사를 바로 고치고, 고친 사실을 숨기지 않습니다.</p>
<h2>저작권</h2>
<p>희소식은 원문 기사를 옮기지 않고 직접 요약해 쓰며, 원문 링크를 함께 제공합니다. 원문 기사의 저작권은 각 언론사에 있습니다. 저작권과 관련한 요청은 위 채널로 알려 주시면 신속히 확인하겠습니다.</p>
"""

PRIVACY_HTML = """
<p>희소식(heesosik.news, 이하 ‘사이트’)은 이용자의 개인정보를 소중히 여기며, 「개인정보 보호법」 등 관련 법령을 지킵니다.</p>
<h2>1. 수집하는 개인정보</h2>
<p>사이트는 회원 가입이나 별도의 개인정보 입력 없이 이용할 수 있으며, 이름·연락처 등 이용자를 식별할 수 있는 정보를 직접 수집하지 않습니다.</p>
<h2>2. 자동으로 생성되는 정보</h2>
<p>사이트 운영과 보안을 위해 호스팅 서비스(Netlify)가 접속 기록(IP 주소, 브라우저 종류, 방문 일시 등)을 자동으로 남길 수 있습니다. ‘좋아요’ 표시는 이용자의 브라우저(로컬 저장소)에만 저장되며 사이트 운영자에게 전송되지 않습니다.</p>
<h2>3. 쿠키와 광고</h2>
<p>사이트는 Google 애드센스 등 제3자 광고 서비스를 사용할 수 있습니다. Google을 비롯한 제3자 공급업체는 쿠키를 사용해 이용자의 이 사이트 및 다른 사이트 방문 기록을 바탕으로 광고를 게재할 수 있습니다. 이용자는 <a href="https://adssettings.google.com" target="_blank" rel="noopener">Google 광고 설정</a>에서 맞춤 광고를 끌 수 있고, 브라우저 설정에서 쿠키 저장을 거부할 수 있습니다. 자세한 내용은 <a href="https://policies.google.com/technologies/ads?hl=ko" target="_blank" rel="noopener">Google 광고 정책</a>을 참고해 주세요.</p>
<h2>4. 외부 링크</h2>
<p>사이트의 기사에는 원문 언론사 등 외부 사이트 링크가 포함됩니다. 외부 사이트의 개인정보 처리는 해당 사이트의 방침을 따릅니다.</p>
<h2>5. 문의</h2>
<p>개인정보와 관련한 문의는 <a href="/contact.html">문의 페이지</a>의 안내에 따라 보내 주세요.</p>
<p class="sign">시행일: 2026년 11월 1일</p>
"""


def main():
    paths = sorted(glob.glob(os.path.join(ROOT, "issues", "*.json")), key=lambda p: int(os.path.basename(p)[:-5]))
    issues = []
    for p in paths:
        iss = json.load(open(p, encoding="utf-8"))
        validate(iss, p)
        if iss["no"] != int(os.path.basename(p)[:-5]):
            sys.exit(f"{p}: no field does not match filename")
        issues.append(iss)
    if not issues:
        sys.exit("no issues")
    nos = [i["no"] for i in issues]
    if nos != list(range(1, len(nos) + 1)):
        sys.exit(f"issue numbers must be 1..N without gaps: {nos}")
    for idx, iss in enumerate(issues):
        prev_no = issues[idx - 1]["no"] if idx > 0 else None
        next_no = issues[idx + 1]["no"] if idx + 1 < len(issues) else None
        open(os.path.join(ROOT, "issues", f"{iss['no']}.html"), "w", encoding="utf-8").write(
            issue_page(iss, prev_no, next_no, False))
    latest = issues[-1]
    open(os.path.join(ROOT, "index.html"), "w", encoding="utf-8").write(
        issue_page(latest, issues[-2]["no"] if len(issues) > 1 else None, None, True))
    open(os.path.join(ROOT, "archive.html"), "w", encoding="utf-8").write(archive_page(issues))
    open(os.path.join(ROOT, "about.html"), "w", encoding="utf-8").write(about_page())
    open(os.path.join(ROOT, "contact.html"), "w", encoding="utf-8").write(simple_page(
        "contact", "희소식 — 문의", "희소식 제보·정정·제휴 문의 안내", "문의", "좋은 소식 제보와 정정 요청을 기다립니다", CONTACT_HTML))
    open(os.path.join(ROOT, "privacy.html"), "w", encoding="utf-8").write(simple_page(
        "privacy", "희소식 — 개인정보처리방침", "희소식 개인정보처리방침", "개인정보처리방침", "희소식은 이용자의 개인정보를 소중히 여깁니다", PRIVACY_HTML))
    urls = [(SITE + "/", latest["date"]), (SITE + "/archive.html", latest["date"]), (SITE + "/about.html", latest["date"]), (SITE + "/contact.html", latest["date"]), (SITE + "/privacy.html", latest["date"])] + [
        (f"{SITE}/issues/{i['no']}.html", i["date"]) for i in issues]
    sm = '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n' + "".join(
        f"  <url><loc>{u}</loc><lastmod>{d}</lastmod></url>\n" for u, d in urls) + "</urlset>\n"
    open(os.path.join(ROOT, "sitemap.xml"), "w").write(sm)
    open(os.path.join(ROOT, "robots.txt"), "w").write(f"User-agent: *\nAllow: /\nSitemap: {SITE}/sitemap.xml\n")
    print(f"built {len(issues)} issue(s); latest = 제{latest['no']}호 ({latest['date']})")


if __name__ == "__main__":
    main()
