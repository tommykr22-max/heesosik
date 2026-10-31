(function () {
  // 별 반짝임
  var st = document.getElementById('stars');
  if (st) for (var i = 0; i < 60; i++) {
    var s = document.createElement('div'); s.className = 'star';
    s.style.left = Math.random() * 100 + '%'; s.style.top = Math.random() * 55 + '%';
    s.style.animationDelay = (Math.random() * 3) + 's';
    s.style.transform = 'scale(' + (0.5 + Math.random()) + ')';
    st.appendChild(s);
  }

  function toast(m) {
    var t = document.getElementById('toast'); if (!t) return;
    t.textContent = m; t.classList.add('on'); clearTimeout(t._h);
    t._h = setTimeout(function () { t.classList.remove('on'); }, 2200);
  }

  // 분야 필터
  var chips = document.getElementById('chips');
  if (chips) chips.addEventListener('click', function (ev) {
    var b = ev.target.closest('.chip'); if (!b) return;
    chips.querySelectorAll('.chip').forEach(function (x) { x.classList.remove('on'); });
    b.classList.add('on');
    var c = b.dataset.cat;
    document.querySelectorAll('#grid .card').forEach(function (card) {
      card.classList.toggle('hide', c !== 'all' && card.dataset.cat !== c);
    });
  });

  // 좋아요 (이 브라우저에만 기억)
  var likes = {};
  try { likes = JSON.parse(localStorage.getItem('hs_likes')) || {}; } catch (e) {}
  function paintLikes() {
    document.querySelectorAll('.like').forEach(function (b) {
      var on = !!likes[b.dataset.id];
      b.classList.toggle('liked', on);
      b.firstChild.textContent = on ? '♥ ' : '♡ ';
      b.querySelector('span').textContent = on ? 1 : 0;
    });
  }
  document.addEventListener('click', function (ev) {
    var b = ev.target.closest('.like'); if (!b) return;
    likes[b.dataset.id] = !likes[b.dataset.id];
    try { localStorage.setItem('hs_likes', JSON.stringify(likes)); } catch (e) {}
    paintLikes();
  });
  paintLikes();

  // 공유
  document.addEventListener('click', function (ev) {
    var b = ev.target.closest('.share'); if (!b) return;
    var text = '[희소식] ' + b.dataset.t, url = location.href.split('#')[0];
    if (navigator.share) {
      navigator.share({ title: '희소식', text: text, url: url }).catch(function () {});
      return;
    }
    if (navigator.clipboard) {
      navigator.clipboard.writeText(text + '\n' + url).then(function () {
        toast('링크를 복사했어요. 단톡방에 붙여 넣어 보세요');
      }, function () { toast('복사가 지원되지 않는 환경이에요'); });
    }
  });

  // 뉴스레터 (준비 중)
  var nl = document.getElementById('nl');
  if (nl) nl.addEventListener('submit', function (ev) {
    ev.preventDefault();
    document.getElementById('nlmsg').textContent = '뉴스레터는 곧 열립니다. 정식 오픈 때 다시 찾아 주세요 ☀';
  });

  // 카톡 공유용 이미지 카드
  var btn = document.getElementById('saveCard');
  var dataEl = document.getElementById('card-data');
  if (!btn || !dataEl) return;
  var D = JSON.parse(dataEl.textContent);

  function wrap(ctx, text, maxW) {
    var words = text.split(' '), lines = [], line = '';
    words.forEach(function (w) {
      var test = line ? line + ' ' + w : w;
      if (ctx.measureText(test).width <= maxW) { line = test; return; }
      if (line) lines.push(line);
      if (ctx.measureText(w).width <= maxW) { line = w; return; }
      var part = '';
      for (var k = 0; k < w.length; k++) {
        if (ctx.measureText(part + w[k]).width > maxW) { lines.push(part); part = ''; }
        part += w[k];
      }
      line = part;
    });
    if (line) lines.push(line);
    return lines;
  }

  function draw() {
    var cv = document.getElementById('cv'), ctx = cv.getContext('2d'), W = 1080, H = 1350, P = 90;
    var g = ctx.createLinearGradient(0, 0, 0, H);
    g.addColorStop(0, '#0E1330'); g.addColorStop(0.45, '#1B1F4B'); g.addColorStop(0.72, '#5B2A5E');
    g.addColorStop(0.9, '#C2464A'); g.addColorStop(1, '#FF6B35');
    ctx.fillStyle = g; ctx.fillRect(0, 0, W, H);
    for (var i = 0; i < 70; i++) {
      ctx.fillStyle = 'rgba(255,255,255,' + (0.2 + Math.random() * 0.6) + ')';
      ctx.beginPath(); ctx.arc(Math.random() * W, Math.random() * H * 0.55, Math.random() * 2 + 0.6, 0, 7); ctx.fill();
    }
    var sg = ctx.createRadialGradient(W / 2, H + 60, 10, W / 2, H + 60, 420);
    sg.addColorStop(0, '#FFF4D6'); sg.addColorStop(0.35, '#FFD36B'); sg.addColorStop(0.6, 'rgba(247,179,43,.9)'); sg.addColorStop(1, 'rgba(255,107,53,0)');
    ctx.fillStyle = sg; ctx.fillRect(0, H - 420, W, 420);

    // 상단 로고
    ctx.fillStyle = '#F7B32B'; ctx.beginPath(); ctx.arc(P + 14, P + 4, 14, 0, 7); ctx.fill();
    ctx.fillStyle = '#fff'; ctx.font = '900 46px "Noto Serif KR", serif'; ctx.textBaseline = 'middle';
    ctx.fillText('희소식', P + 42, P + 6);
    ctx.font = '500 28px "Noto Sans KR", sans-serif'; ctx.textAlign = 'right'; ctx.globalAlpha = .8;
    ctx.fillText('제' + D.no + '호 · ' + D.date, W - P, P + 6); ctx.globalAlpha = 1; ctx.textAlign = 'left';

    var y = 250;
    ctx.fillStyle = '#F7B32B'; ctx.font = '700 30px "Noto Sans KR", sans-serif'; ctx.fillText('오늘의 희소식', P, y);
    y += 70;
    ctx.fillStyle = '#fff'; ctx.font = '900 64px "Noto Serif KR", serif'; ctx.textBaseline = 'top';
    wrap(ctx, D.title, W - P * 2).slice(0, 4).forEach(function (l) { ctx.fillText(l, P, y); y += 88; });
    y += 20;
    ctx.font = '400 34px "Noto Sans KR", sans-serif'; ctx.globalAlpha = .88;
    wrap(ctx, D.why, W - P * 2).slice(0, 3).forEach(function (l) { ctx.fillText(l, P, y); y += 52; });
    ctx.globalAlpha = 1;
    y += 36;
    ctx.fillStyle = 'rgba(255,255,255,.35)'; ctx.fillRect(P, y, 120, 3); y += 40;
    ctx.fillStyle = '#FFE29A'; ctx.font = '700 40px "Noto Serif KR", serif';
    wrap(ctx, '“' + D.quote + '”', W - P * 2).slice(0, 4).forEach(function (l) { ctx.fillText(l, P, y); y += 60; });
    ctx.fillStyle = 'rgba(255,255,255,.75)'; ctx.font = '400 28px "Noto Sans KR", sans-serif';
    ctx.fillText('— ' + D.who, P, y + 8);

    ctx.textAlign = 'center'; ctx.fillStyle = '#1C1A17'; ctx.font = '700 34px "Noto Sans KR", sans-serif';
    ctx.textBaseline = 'alphabetic';
    ctx.fillText('heesosik.news', W / 2, H - 70);
    ctx.font = '500 24px "Noto Sans KR", sans-serif'; ctx.fillText('지칠 때 열어 보는 좋은 소식', W / 2, H - 34);
    ctx.textAlign = 'left';
    return cv;
  }

  btn.addEventListener('click', function () {
    var fonts = document.fonts ? Promise.all([
      document.fonts.load('900 64px "Noto Serif KR"'), document.fonts.load('700 40px "Noto Serif KR"'),
      document.fonts.load('400 34px "Noto Sans KR"'), document.fonts.load('700 34px "Noto Sans KR"')
    ]) : Promise.resolve();
    fonts.catch(function () {}).then(function () {
      var cv = draw();
      cv.toBlob(function (blob) {
        var file = new File([blob], 'heesosik-' + D.no + '.png', { type: 'image/png' });
        if (navigator.canShare && navigator.canShare({ files: [file] })) {
          navigator.share({ files: [file], title: '희소식 제' + D.no + '호' }).catch(function () {});
          return;
        }
        var a = document.createElement('a');
        a.href = URL.createObjectURL(blob); a.download = file.name;
        document.body.appendChild(a); a.click(); a.remove();
        toast('이미지를 저장했어요');
      }, 'image/png');
    });
  });
  window.__drawCard = draw;
})();
