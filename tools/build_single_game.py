#!/usr/bin/env python3
"""Build a static falling-star radical review game from a JSON question file."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


FALLBACK_DISTRACTORS = ["口", "木", "水", "手", "心", "艸", "人", "土", "言", "辵", "肉", "目", "巾", "虫", "宀", "鳥", "足", "金", "糸", "火"]

KANGXI_RADICALS = set(
    "一丨丶丿乙亅二亠人儿入八冂冖冫几凵刀力勹匕匚匸十卜卩厂厶又口囗土士夂夊夕大女子宀寸小尢尸屮山巛工己巾干幺广廴廾弋弓彐彡彳心戈戶手支攴文斗斤方无日曰月木欠止歹殳毋比毛氏气水火爪父爻爿片牙牛犬玄玉瓜瓦甘生用田疋疒癶白皮皿目矛矢石示禸禾穴立竹米糸缶网羊羽老而耒耳聿肉臣自至臼舌舛舟艮色艸虍虫血行衣襾見角言谷豆豕豸貝赤走足身車辛辰辵邑酉釆里金長門阜隶隹雨青非面革韋韭音頁風飛食首香馬骨高髟鬥鬯鬲鬼魚鳥鹵鹿麥麻黃黍黑黹黽鼎鼓鼠鼻齊齒龍龜龠"
)

RADICAL_VARIANTS = {
    "亻": "人",
    "刂": "刀",
    "忄": "心",
    "扌": "手",
    "氵": "水",
    "灬": "火",
    "犭": "犬",
    "礻": "示",
    "衤": "衣",
    "艹": "艸",
    "辶": "辵",
    "钅": "金",
    "纟": "糸",
    "饣": "食",
}


def clean_text(value) -> str:
    return str(value or "").replace("`", "").replace("~", "").strip()


def clean_radical(value) -> str:
    cleaned = clean_text(value)
    return RADICAL_VARIANTS.get(cleaned, cleaned)


def normalize_data(raw: dict) -> dict:
    title = str(raw.get("title") or "星空部首複習")
    source_note = str(raw.get("source_note") or "部首以教育部《重編國語辭典修訂本》/萌典資料整理。")
    levels = raw.get("levels")
    if not isinstance(levels, list) or not levels:
        raise ValueError("data JSON must contain a non-empty levels array")

    normalized_levels = []
    for level_index, level in enumerate(levels, start=1):
        if isinstance(level, list):
            level_title = f"第 {level_index} 關"
            items = level
        else:
            level_title = str(level.get("title") or f"第 {level_index} 關")
            items = level.get("items")
        if not isinstance(items, list) or not items:
            raise ValueError(f"level {level_index} must contain a non-empty items array")

        normalized_items = []
        for item_index, item in enumerate(items, start=1):
            char = clean_text(item.get("char"))
            radical = clean_radical(item.get("radical"))
            if not char or not radical:
                raise ValueError(f"level {level_index} item {item_index} needs char and radical")
            distractors = [clean_radical(x) for x in item.get("distractors", []) if clean_radical(x)]
            if radical not in KANGXI_RADICALS:
                raise ValueError(
                    f"level {level_index} item {item_index}: {radical} is not an official radical"
                )
            invalid = [option for option in distractors if option not in KANGXI_RADICALS]
            if invalid:
                raise ValueError(
                    f"level {level_index} item {item_index}: non-radical options {invalid}"
                )
            seen = {radical}
            clean = []
            for option in distractors + FALLBACK_DISTRACTORS:
                if option not in seen:
                    seen.add(option)
                    clean.append(option)
                if len(clean) == 3:
                    break
            normalized_items.append({"char": char, "radical": radical, "distractors": clean})
        normalized_levels.append({"title": level_title, "questions": normalized_items})

    return {"title": title, "source_note": source_note, "levels": normalized_levels}


def write_game(data: dict, out_dir: Path) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "index.html").write_text(index_html(data["title"]), encoding="utf-8")
    (out_dir / "styles.css").write_text(styles_css(), encoding="utf-8")
    (out_dir / "app.js").write_text(app_js(data), encoding="utf-8")
    (out_dir / "README.md").write_text(readme_md(data), encoding="utf-8")


def index_html(title: str) -> str:
    return f"""<!doctype html>
<html lang="zh-Hant">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>{title}</title>
    <link rel="stylesheet" href="styles.css" />
  </head>
  <body>
    <a class="home-link" href="../../index.html">返回版本選擇</a>
    <div class="game-shell">
      <header class="topbar">
        <div>
          <h1>{title}</h1>
          <p>看玻璃罩裡的生字，在星星落地前選出正確部首。</p>
        </div>
        <div class="status-strip">
          <span>第 <b id="levelNow">1</b> 關</span>
          <span>本關 <b id="levelProgress">0</b> / <b id="levelTotal">0</b></span>
          <span>答錯待複習 <b id="missCount">0</b></span>
        </div>
      </header>
      <main class="sky">
        <div class="star-field" aria-hidden="true"></div>
        <section class="play-area" aria-label="部首選擇遊戲">
          <div class="message hidden" id="message"></div>
          <div class="fall-zone" id="fallZone"></div>
          <div class="ground-line"></div>
          <div class="word-dome">
            <div class="dome-glow"></div>
            <div class="target-label">這個字的部首是？</div>
            <div class="target-word" id="targetWord">？</div>
          </div>
        </section>
      </main>
      <footer class="controlbar">
        <button id="startButton" type="button">開始遊戲</button>
        <button id="pauseButton" type="button">暫停</button>
        <button id="restartButton" type="button">重新開始</button>
        <span id="sourceNote"></span>
      </footer>
    </div>
    <div class="level-overlay hidden" id="levelOverlay"><div class="big-like">讚</div></div>
    <div class="final-overlay hidden" id="finalOverlay">
      <div class="like-ring"><span>讚</span><span>讚</span><span>讚</span><span>讚</span><span>讚</span><span>讚</span></div>
      <div class="gold-star">★</div>
      <h2>全部過關</h2>
    </div>
    <script src="app.js"></script>
  </body>
</html>
"""


def app_js(data: dict) -> str:
    data_json = json.dumps(data, ensure_ascii=False, indent=2)
    return f"""const GAME_DATA = {data_json};
const LEVELS = GAME_DATA.levels;
const els = {{
  levelNow: document.querySelector("#levelNow"),
  levelProgress: document.querySelector("#levelProgress"),
  levelTotal: document.querySelector("#levelTotal"),
  missCount: document.querySelector("#missCount"),
  fallZone: document.querySelector("#fallZone"),
  targetWord: document.querySelector("#targetWord"),
  message: document.querySelector("#message"),
  startButton: document.querySelector("#startButton"),
  pauseButton: document.querySelector("#pauseButton"),
  restartButton: document.querySelector("#restartButton"),
  levelOverlay: document.querySelector("#levelOverlay"),
  finalOverlay: document.querySelector("#finalOverlay"),
  sourceNote: document.querySelector("#sourceNote")
}};
const state = {{ levelIndex: 0, pending: [], missed: [], current: null, running: false, paused: false, lock: false, timer: null, questionNumber: 0, nextOnResume: false }};
const sizes = ["small", "medium", "large", "wide"];
function shuffle(items) {{ return [...items].sort(() => Math.random() - 0.5); }}
function resetGame() {{
  clearTimeout(state.timer); state.levelIndex = 0; state.running = false; state.paused = false; state.lock = false; state.nextOnResume = false;
  els.finalOverlay.classList.add("hidden"); els.levelOverlay.classList.add("hidden"); loadLevel(0);
  setMessage("按「開始遊戲」後，星星會從上方墜落。", false);
}}
function loadLevel(index) {{
  const level = LEVELS[index]; state.pending = shuffle(level.questions); state.missed = []; state.current = null; state.questionNumber = 0;
  els.levelNow.textContent = `${{index + 1}} / ${{LEVELS.length}}`; els.levelTotal.textContent = level.questions.length; updateStats(); clearStars(); els.targetWord.textContent = "？";
}}
function startGame() {{
  if (state.running && state.paused) {{ pauseGame(); return; }}
  if (!state.running) {{ state.running = true; state.paused = false; els.pauseButton.textContent = "暫停"; clearMessage(); nextQuestion(); }}
}}
function pauseGame() {{
  if (!state.running) return; state.paused = !state.paused; els.pauseButton.textContent = state.paused ? "繼續" : "暫停";
  document.querySelectorAll(".falling-star").forEach(star => star.style.animationPlayState = state.paused ? "paused" : "running");
  if (state.paused) setMessage("已暫停", false);
  else {{ clearMessage(); if (state.nextOnResume) {{ state.nextOnResume = false; nextQuestion(); }} }}
}}
function nextQuestion() {{
  if (!state.running || state.lock) return;
  if (state.paused) {{ state.nextOnResume = true; setMessage("已暫停", false); return; }}
  clearTimeout(state.timer); clearStars();
  if (state.pending.length === 0) {{
    if (state.missed.length) {{ state.pending = shuffle(state.missed); state.missed = []; setMessage("錯題再挑戰", false); updateStats(); state.timer = setTimeout(nextQuestion, 900); return; }}
    finishLevel(); return;
  }}
  state.current = state.pending.shift(); state.questionNumber += 1; els.targetWord.textContent = state.current.char; updateStats(); spawnOptions(state.current);
}}
function spawnOptions(question) {{
  const answers = shuffle([{{ text: question.radical, correct: true }}, ...question.distractors.slice(0, 3).map(text => ({{ text, correct: false }}))]);
  const duration = Math.max(3.8, 9.2 - state.levelIndex * 0.65 - state.questionNumber * 0.08);
  answers.forEach((answer, index) => {{
    const star = document.createElement("button"); star.type = "button"; star.className = `falling-star ${{sizes[index]}}`; star.textContent = answer.text;
    star.style.left = `clamp(calc(var(--w) / 2), ${{12.5 + index * 25 + Math.random() * 4 - 2}}%, calc(100% - var(--w) / 2))`; star.style.animationDuration = `${{duration + Math.random() * 0.8}}s`; star.style.animationDelay = `${{Math.random() * 0.35}}s`;
    star.addEventListener("click", () => chooseAnswer(answer, star));
    star.addEventListener("animationend", () => {{ if (!state.lock && state.current === question) {{ explode(star); showWrong(null, true); }} }});
    els.fallZone.appendChild(star);
  }});
}}
function chooseAnswer(answer, star) {{
  if (state.lock || state.paused) return;
  if (answer.correct) {{ star.classList.add("correct"); state.lock = true; setMessage("答對了", false); state.timer = setTimeout(() => {{ state.lock = false; clearMessage(); nextQuestion(); }}, 600); }}
  else showWrong(star, false);
}}
function showWrong(selectedStar, timedOut) {{
  if (state.lock) return; state.lock = true; if (state.current) state.missed.push(state.current);
  document.querySelectorAll(".falling-star").forEach(star => {{
    star.style.animationPlayState = "paused";
    if (star.textContent === state.current.radical) {{ star.classList.add("answer-reveal"); star.style.left = "50%"; star.style.top = "40%"; }}
    else star.classList.add("fade-away");
  }});
  if (selectedStar) selectedStar.classList.add("wrong");
  setMessage(timedOut ? `時間到，正確部首是「${{state.current.radical}}」` : `正確部首是「${{state.current.radical}}」`, true);
  updateStats(); state.timer = setTimeout(() => {{ state.lock = false; clearMessage(); nextQuestion(); }}, 3000);
}}
function explode(star) {{
  const zone = els.fallZone.getBoundingClientRect(); const box = star.getBoundingClientRect();
  const blast = document.createElement("div"); blast.className = "explosion";
  blast.style.left = `${{box.left + box.width / 2 - zone.left}}px`; blast.style.top = `${{zone.height}}px`;
  blast.innerHTML = `<span class="blast"></span><span class="shockwave"></span>` + Array.from({{ length: 12 }}, (_, i) => `<span class="spark" style="--angle:${{i * 30}}deg"></span>`).join("");
  if (star.textContent !== state.current.radical) star.classList.add("exploded");
  els.fallZone.appendChild(blast);
  const area = els.fallZone.parentElement; area.classList.remove("shake"); void area.offsetWidth; area.classList.add("shake");
}}
function finishLevel() {{
  state.running = false; state.lock = true; clearStars(); els.levelOverlay.classList.remove("hidden");
  setTimeout(() => {{
    els.levelOverlay.classList.add("hidden"); state.lock = false;
    if (state.levelIndex === LEVELS.length - 1) finishGame();
    else {{ state.levelIndex += 1; loadLevel(state.levelIndex); state.running = true; setMessage("下一關開始", false); state.timer = setTimeout(() => {{ clearMessage(); nextQuestion(); }}, 900); }}
  }}, 1700);
}}
function finishGame() {{ clearStars(); els.finalOverlay.classList.remove("hidden"); setMessage("全部完成", false); }}
function updateStats() {{
  const level = LEVELS[state.levelIndex]; const solved = level.questions.length - state.pending.length - (state.current ? 1 : 0);
  els.levelProgress.textContent = Math.max(0, solved); els.missCount.textContent = state.missed.length;
}}
function clearStars() {{ els.fallZone.replaceChildren(); }}
function setMessage(text, danger) {{ els.message.textContent = text; els.message.classList.toggle("danger", danger); els.message.classList.remove("hidden"); }}
function clearMessage() {{ els.message.classList.add("hidden"); }}
els.sourceNote.textContent = GAME_DATA.source_note;
els.startButton.addEventListener("click", startGame); els.pauseButton.addEventListener("click", pauseGame); els.restartButton.addEventListener("click", resetGame);
resetGame();
"""


def styles_css() -> str:
    return """:root { color-scheme: dark; --ink:#f8fbff; --muted:#b7c4df; --cyan:#8ee8ff; --gold:#ffd85a; --danger:#ff6270; }
* { box-sizing: border-box; } body { margin:0; min-height:100vh; color:var(--ink); font-family:"Microsoft JhengHei","Noto Sans TC",system-ui,sans-serif; background:radial-gradient(circle at 20% 15%,rgba(118,82,255,.28),transparent 28rem),radial-gradient(circle at 80% 10%,rgba(0,209,255,.22),transparent 24rem),linear-gradient(180deg,#061029 0%,#0b1236 55%,#14123a 100%); overflow:hidden; } button { border:0; color:inherit; font:inherit; cursor:pointer; } h1,h2,p { margin:0; }
.game-shell { display:grid; grid-template-rows:auto 1fr auto; min-height:100vh; }
.topbar,.controlbar { position:relative; z-index:5; display:flex; align-items:center; justify-content:space-between; gap:1rem; padding:1rem 1.25rem; background:rgba(5,11,31,.72); border-bottom:1px solid rgba(142,232,255,.22); backdrop-filter:blur(16px); }
.home-link { position:fixed; top:.8rem; left:.8rem; z-index:12; padding:.55rem .75rem; border:1px solid rgba(255,255,255,.22); border-radius:8px; background:rgba(5,11,31,.82); color:var(--ink); font-size:.9rem; font-weight:700; text-decoration:none; backdrop-filter:blur(12px); }
.home-link:hover,.home-link:focus-visible { border-color:var(--cyan); outline:none; box-shadow:0 0 18px rgba(142,232,255,.34); } .topbar { padding-left:10rem; }
.topbar h1 { font-size:clamp(1.35rem,3vw,2rem); } .topbar p,#sourceNote { color:var(--muted); font-size:.95rem; }
.status-strip { display:flex; flex-wrap:wrap; justify-content:flex-end; gap:.55rem; } .status-strip span { min-width:7.25rem; padding:.55rem .7rem; border:1px solid rgba(255,255,255,.16); border-radius:8px; background:rgba(255,255,255,.08); text-align:center; }
.sky { position:relative; overflow:hidden; } .star-field,.star-field:before,.star-field:after { position:absolute; inset:0; content:""; background-image:radial-gradient(circle,rgba(255,255,255,.9) 0 1px,transparent 1.5px),radial-gradient(circle,rgba(142,232,255,.65) 0 1px,transparent 1.5px); background-position:0 0,35px 65px; background-size:110px 110px,170px 170px; animation:twinkle 4s ease-in-out infinite alternate; }
.star-field:before { opacity:.45; transform:rotate(9deg) scale(1.1); } .star-field:after { opacity:.3; transform:rotate(-6deg) scale(1.2); }
.play-area { position:relative; height:calc(100vh - 9.5rem); min-height:34rem; overflow:hidden; } .fall-zone { position:absolute; inset:0 0 8.5rem; z-index:2; }
.ground-line { position:absolute; right:0; bottom:8.2rem; left:0; z-index:3; height:.35rem; background:linear-gradient(90deg,transparent,rgba(142,232,255,.75),transparent); box-shadow:0 0 26px rgba(142,232,255,.8); }
.word-dome { position:absolute; bottom:1rem; left:50%; z-index:4; display:grid; width:min(24rem,calc(100vw - 2rem)); height:8.6rem; place-items:center; transform:translateX(-50%); border:1px solid rgba(255,255,255,.36); border-radius:8rem 8rem 1.4rem 1.4rem; background:linear-gradient(135deg,rgba(255,255,255,.28),rgba(255,255,255,.05)),rgba(32,55,90,.55); box-shadow:inset 0 0 38px rgba(255,255,255,.16),0 18px 55px rgba(0,0,0,.36); backdrop-filter:blur(10px); }
.dome-glow { position:absolute; inset:.6rem 1.2rem auto; height:1.5rem; border-radius:50%; background:rgba(255,255,255,.35); filter:blur(10px); } .target-label { align-self:end; color:var(--muted); font-size:.95rem; } .target-word { align-self:start; font-size:clamp(3.5rem,11vw,6rem); font-weight:900; line-height:1; text-shadow:0 0 24px rgba(142,232,255,.95); }
.falling-star { position:absolute; top:-6rem; z-index:4; display:grid; place-items:center; aspect-ratio:1; clip-path:polygon(50% 0%,61% 33%,96% 34%,68% 55%,79% 90%,50% 69%,21% 90%,32% 55%,4% 34%,39% 33%); background:radial-gradient(circle at 35% 28%,#fff8bd 0 14%,var(--gold) 15% 48%,#f5a623 72%,#be6d00 100%); width:var(--w); margin-left:calc(var(--w) / -2); color:#271700; font-size:2.45rem; font-weight:900; filter:drop-shadow(0 0 24px rgba(255,216,90,.75)); animation-name:fall; animation-timing-function:linear; animation-fill-mode:forwards; }
.falling-star.small{--w:6.36rem}.falling-star.medium{--w:7.44rem}.falling-star.large{--w:8.64rem}.falling-star.wide{--w:8.16rem}.falling-star:hover,.falling-star:focus-visible{outline:3px solid #fff; transform:scale(1.08)} .falling-star.correct{background:radial-gradient(circle at 35% 28%,#fff 0 14%,#80ffb8 15% 52%,#18b875 76%)} .falling-star.wrong{background:radial-gradient(circle at 35% 28%,#fff 0 14%,#ff91a4 15% 52%,#e33b50 76%)}
.answer-reveal { width:13rem!important; margin-left:0; animation:none!important; transform:translate(-50%,-50%); transition:all .35s ease; } .fade-away { opacity:0; pointer-events:none; transition:opacity .28s ease; }
.falling-star.exploded { opacity:0; transition:none; } .explosion { position:absolute; z-index:6; width:0; height:0; pointer-events:none; } .explosion span { position:absolute; top:0; left:0; border-radius:50%; }
.explosion .blast { width:9rem; height:9rem; margin:-4.5rem 0 0 -4.5rem; background:radial-gradient(circle,#fff 0 12%,#fff3a0 22%,#ffb02e 45%,rgba(255,80,40,.75) 62%,transparent 72%); animation:blast .75s ease-out forwards; } .explosion .shockwave { width:3rem; height:3rem; margin:-1.5rem 0 0 -1.5rem; border:.3rem solid rgba(255,230,140,.9); animation:shockwave .7s ease-out forwards; }
.explosion .spark { width:.7rem; height:.7rem; margin:-.35rem 0 0 -.35rem; background:#fff2a6; box-shadow:0 0 12px #ffb02e; animation:spark .8s ease-out forwards; } .play-area.shake { animation:shake .45s ease-in-out; }
.message { position:absolute; top:1rem; left:50%; z-index:7; min-width:min(30rem,calc(100vw - 2rem)); padding:.8rem 1rem; transform:translateX(-50%); border:1px solid rgba(255,255,255,.18); border-radius:8px; background:rgba(8,18,48,.88); text-align:center; box-shadow:0 16px 40px rgba(0,0,0,.28); backdrop-filter:blur(12px); } .message.danger { border-color:rgba(255,98,112,.45); background:rgba(75,12,24,.92); } .hidden { display:none!important; }
.controlbar { border-top:1px solid rgba(142,232,255,.22); border-bottom:0; } .controlbar button { min-width:6.5rem; padding:.7rem .9rem; border-radius:8px; background:linear-gradient(135deg,#47d5ff,#8b7cff); color:#061029; font-weight:800; } .controlbar button:nth-child(2),.controlbar button:nth-child(3){background:rgba(255,255,255,.12);color:var(--ink)} #sourceNote { margin-left:auto; text-align:right; }
.level-overlay,.final-overlay { position:fixed; inset:0; z-index:20; display:grid; place-items:center; background:rgba(3,7,22,.54); backdrop-filter:blur(8px); } .big-like { color:#fff2a6; font-size:clamp(7rem,22vw,18rem); font-weight:1000; text-shadow:0 0 20px rgba(255,216,90,1),0 0 70px rgba(255,125,194,.75); animation:likePop 1.45s ease forwards; }
.like-ring { position:relative; width:min(28rem,78vw); aspect-ratio:1; animation:spinRing 3.8s ease-in-out forwards; } .like-ring span { position:absolute; top:50%; left:50%; display:grid; width:5rem; height:5rem; place-items:center; border-radius:50%; background:rgba(255,255,255,.12); color:#fff2a6; font-size:2.2rem; font-weight:950; box-shadow:0 0 24px rgba(255,216,90,.7); }
.like-ring span:nth-child(1){transform:translate(-50%,-50%) rotate(0deg) translateY(-12rem) rotate(0deg)}.like-ring span:nth-child(2){transform:translate(-50%,-50%) rotate(60deg) translateY(-12rem) rotate(-60deg)}.like-ring span:nth-child(3){transform:translate(-50%,-50%) rotate(120deg) translateY(-12rem) rotate(-120deg)}.like-ring span:nth-child(4){transform:translate(-50%,-50%) rotate(180deg) translateY(-12rem) rotate(-180deg)}.like-ring span:nth-child(5){transform:translate(-50%,-50%) rotate(240deg) translateY(-12rem) rotate(-240deg)}.like-ring span:nth-child(6){transform:translate(-50%,-50%) rotate(300deg) translateY(-12rem) rotate(-300deg)}
.gold-star { position:absolute; z-index:2; color:var(--gold); font-size:clamp(8rem,26vw,20rem); text-shadow:0 0 20px #fff,0 0 50px rgba(255,216,90,1),0 0 100px rgba(255,133,194,.8); animation:starShine 1.15s ease-in-out infinite alternate; } .final-overlay h2 { position:absolute; bottom:12vh; z-index:3; font-size:clamp(2.5rem,7vw,5rem); text-shadow:0 0 28px rgba(142,232,255,.95); }
@keyframes fall{0%{top:calc(var(--w) * -1);transform:rotate(-8deg)}100%{top:calc(100% - var(--w));transform:rotate(24deg)}} @keyframes blast{0%{transform:scale(.15);opacity:1}60%{opacity:.95}100%{transform:scale(1.5);opacity:0}} @keyframes shockwave{0%{transform:scale(.3);opacity:1}100%{transform:scale(5);opacity:0}} @keyframes spark{0%{transform:rotate(var(--angle)) translateY(0) scale(1);opacity:1}100%{transform:rotate(var(--angle)) translateY(-7rem) scale(.3);opacity:0}} @keyframes shake{0%,100%{transform:translate(0,0)}20%{transform:translate(-8px,4px)}40%{transform:translate(7px,-5px)}60%{transform:translate(-5px,3px)}80%{transform:translate(4px,-2px)}} @keyframes twinkle{from{opacity:.7}to{opacity:1}} @keyframes likePop{0%{opacity:0;transform:scale(.2) rotate(-14deg)}55%{opacity:1;transform:scale(1.14) rotate(4deg)}100%{opacity:0;transform:scale(.88)}} @keyframes spinRing{0%{transform:rotate(0deg) scale(.65);opacity:0}15%{opacity:1}82%{transform:rotate(720deg) scale(1);opacity:1}100%{transform:rotate(720deg) scale(1.06);opacity:.25}} @keyframes starShine{from{transform:scale(.92) rotate(-3deg);filter:brightness(1)}to{transform:scale(1.04) rotate(3deg);filter:brightness(1.35)}}
@media (max-width:760px){body{overflow:auto}.home-link{position:relative;top:auto;left:auto;display:inline-block;margin:.65rem .65rem 0;width:max-content}.topbar{padding-left:1.25rem}.topbar,.controlbar{align-items:stretch;flex-direction:column}.status-strip{justify-content:stretch}.status-strip span{flex:1 1 8rem}.play-area{height:calc(100vh - 15rem);min-height:32rem}.falling-star.small,.falling-star.medium,.falling-star.large,.falling-star.wide{--w:min(5.76rem,24vw);font-size:2.1rem}#sourceNote{margin-left:0;text-align:left}}
@media (prefers-reduced-motion:reduce){.play-area.shake{animation:none}}
"""


def readme_md(data: dict) -> str:
    counts = ", ".join(str(len(level["questions"])) for level in data["levels"])
    return f"""# {data["title"]}

這是由 `radical-star-game` skill 產生的靜態部首複習遊戲。

## 開啟方式

直接開啟 `index.html`，或用任一靜態檔案伺服器開啟此資料夾。

## 題數

共 {len(data["levels"])} 關；各關題數：{counts}。
"""


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("data_json", type=Path)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    raw = json.loads(args.data_json.read_text(encoding="utf-8"))
    data = normalize_data(raw)
    write_game(data, args.out)
    print(f"Wrote radical star game to {args.out}")


if __name__ == "__main__":
    main()
