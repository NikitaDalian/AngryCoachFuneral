"""Собирает реестр воспитанников Тренера по пяти курсам из опубликованных лендингов.

Источники локальные (в репозиторий не кладутся): лендинги прошлых курсов и экспорт чата.
Выход: src/people.json — только агрегаты (итоги, награды, счётчики), без переписки.
    python src/extract.py
"""
import collections
import json
import pathlib
import re
import sys

sys.stdout.reconfigure(encoding="utf-8")
ROOT = pathlib.Path(r"C:\AIAgent\PlankCoach")
PREV = pathlib.Path(r"C:\Users\NikitaEN\AppData\Local\Temp\claude\C--AIAgent-PlankCoach\48c7c910-93ea-4f80-a63e-d235409a0405\scratchpad\prev")
OUT = pathlib.Path(__file__).parent / "people.json"
BOT = "8652442090"

# ---------- канон: Telegram ID -> имя на некрологе ----------
NAMES = {
    "23942556": "Никита Федоров", "58811221": "Лев Грин", "24905927": "Сергей Медведев",
    "2897263": "Александр (mrb8r)", "156212094": "Саня Лихачёв", "487463175": "Вадим Влахко",
    "405742979": "Семён Неверов", "377672278": "Серёга Пономарёв", "1021394934": "Юлия",
    "1167325690": "Макс Родионов", "154123037": "Владимир Шабалкин", "201499258": "Марсель",
    "438807980": "Макс Богородский", "577313928": "Артём", "588145813": "Ярослав Федоров",
    "110502345": "Вера Р.", "712563629": "Александр Сторублевый", "116674374": "Владимир",
    "253086756": "Женя Бурова", "148648420": "Павел Орлов", "335500807": "Андрей",
    "5023466261": "Никита Гаранов", "349055373": "А", "516053955": "Екатерина",
    "1371701991": "Саня Быков", "977313866": "Гриша Гедз", "77251189": "Влад Львов",
    "5046656995": "Сергей Синькович", "389132599": "Максим Логвинов", "233655445": "Даня Попов",
    "400042922": "Зворыгин", "212742635": "Ольга", "329732306": "Александр Дмитриев",
    "56401752": "Алёна Федорова", "471200964": "Алла", "5123958539": "Саня Пономарёв",
    "517526569": "Женя Квант", "282585544": "Антон Ромашов", "GUEST:Yifei": "Yifei",
}
# имена в источниках -> ID
PLANK_KEYS = {"yuliya": "1021394934", "seryoga": "377672278", "vadim": "487463175", "yaroslav": "588145813",
              "sanya": "156212094", "nikita_f": "23942556", "lev": "58811221", "ekaterina": "516053955",
              "storublevy": "712563629", "zvorygin": "400042922", "marsel": "201499258", "danya": "233655445",
              "artem": "577313928", "vlad": "77251189", "maksim": "389132599", "yifei": "GUEST:Yifei",
              "sergey_m": "24905927", "ponomarev_a": "5123958539", "vladimir": "116674374",
              "nikita_g": "5023466261", "olga": "212742635", "bykov": "1371701991", "johnny": "517526569"}
CHAIR_NAMES = {"Ярослав": "588145813", "Vadim Vlakhko": "487463175", "Юлия": "1021394934",
               "Серега Пономарев": "377672278", "Marsel": "201499258", "Лев Грин": "58811221",
               "Maxim Bogorodskiy": "438807980", "Nikita Fedorov": "23942556", "Саня Лихачев": "156212094",
               "Max Rodionov": "1167325690", "Andrei": "335500807", "Александр Сторублевый": "712563629",
               "Zvorygin": "400042922", "Сергей Медведев": "24905927", "Alexandr": "1371701991",
               "Ekaterina": "516053955", "Artem": "577313928", "Алёна": "56401752",
               "Evgeniya Burova": "253086756", "Александр": "329732306", "Никита Гаранов": "5023466261",
               "Olga": "212742635"}
PUSH_NAMES = {"Vadim Vlakhko": "487463175", "Nikita Fedorov": "23942556", "Саня Лихачев": "156212094",
              "Серега Пономарев": "377672278", "А": "349055373", "Max Rodionov": "1167325690",
              "Marsel": "201499258", "Лев Грин": "58811221", "Artem Артем": "577313928",
              "Макс Богородский": "438807980", "Юлия ...": "1021394934", "Александр Сторублевый": "712563629",
              "Никита Гаранов": "5023466261", "Semen Neverov": "405742979", "Vladimir Shabalkin": "154123037",
              "Ярослав Федоров": "588145813", "Сергей Медведев": "24905927", "Alexander": "2897263",
              "Владимир": "116674374", "Alla": "471200964", "Александр": "329732306", "Саня Быков": "1371701991"}
ABS_TICKS = {"SVP": "24905927", "JUL": "1021394934", "ALX": "2897263", "MAX": "1167325690",
             "VDM": "487463175", "VERA": "110502345", "SMN": "405742979", "PVL": "148648420",
             "VLD": "154123037", "NKT": "23942556", "MXB": "438807980", "LEV": "58811221",
             "MRC": "349055373", "SNK": "5046656995"}
BURPEE_KEYS = {"semen": "405742979", "nikita": "23942556", "vadim": "487463175", "sergey": "377672278",
               "yulia": "1021394934", "sasha": "156212094", "lev": "58811221", "vera": "110502345",
               "alexander": "2897263", "marsel": "201499258", "max": "1167325690", "grisha": "977313866",
               "medvedev": "24905927", "storublev": "712563629", "pavel": "148648420"}

people = collections.defaultdict(lambda: {"courses": {}, "awards": [], "epithets": []})


def course(pid, ch, **kw):
    people[pid]["courses"][ch] = kw


def award(pid, ch, title, desc="", kind="award", icon=""):
    title, desc = title.strip(), desc.strip()
    for a in people[pid]["awards"]:
        if a["ch"] == ch and a["t"].lower() == title.lower():  # орден, повторённый в наградном листе
            if len(desc) > len(a["d"]):
                a["d"] = desc
            if kind == "hall":
                a["kind"] = "hall"
            if icon and not a.get("i"):
                a["i"] = icon
            return
    people[pid]["awards"].append({"ch": ch, "t": title, "d": desc, "kind": kind, "i": icon})


def mmss(s):
    p = [int(x) for x in s.split(":")]
    return p[0] * 3600 + p[1] * 60 + p[2] if len(p) == 3 else p[0] * 60 + p[1]


# ---------- ПЛАНКА ----------
app = (PREV / "PlankChallenge" / "app.js").read_text(encoding="utf-8")
for k, tot, days, rec in re.findall(r"k: '(\w+)',.*?total:\s*'([\d:]+)',\s*days:\s*'(\d+)/30',\s*rec:\s*'([\d:]+)'", app):
    course(PLANK_KEYS[k], "plank", total=mmss(tot), days=int(days), max=mmss(rec), unit="sec")
PLANK_EMO = {"Гран-при по сумме": "🏆", "Пацанский рекорд одного дня": "💪", "Чемпион постоянства": "📅",
             "Камбэк сезона": "🔄", "Сэр Шаг-Назад": "🎩", "Падлы в помощь": "🦹"}
for pid, t, d in [
    ("1021394934", "Гран-при по сумме", "Лидер по общему времени: 1:48:40 за 30/30. Финиш — 11:00."),
    ("487463175", "Пацанский рекорд одного дня", "Финальный заход на 8:00."),
    ("377672278", "Чемпион постоянства", "Стрик 30/30, ежедневное видео без пропусков."),
    ("156212094", "Камбэк сезона", "Уехал в Узбекистан, но дотянул 29/30 и закрыл финал на 6:00."),
    ("712563629", "Сэр Шаг-Назад", "За стиль и формулировки."),
    ("588145813", "Падлы в помощь", "27/30, рекорд 6:00 — весь рост благодаря падлам-мошенникам."),
]:
    award(pid, "plank", t, d, "hall", PLANK_EMO[t])

# ---------- СТУЛЬЧИК ----------
line = (PREV / "ChairChallenge" / "index.html").read_text(encoding="utf-8").split("\n")[172]
cs = line.replace('\\"', '"').replace("\\n", "\n")
for name, days, ssum, mx in re.findall(r'\{name:"([^"]+)",days:(\d+),sum:(\d+),max:(\d+)', cs):
    course(CHAIR_NAMES[name], "chair", total=int(ssum), days=int(days), max=int(mx), unit="sec")
noms = dict(re.findall(r'"([^"]+)":"([^"]+)"', cs[cs.index("const noms"):cs.index("};", cs.index("const noms"))]))
dost = re.findall(r'"([^"]+)"', cs[cs.index("dostNames="):cs.index("];", cs.index("dostNames="))])
chair_days = {CHAIR_NAMES[n]: people[CHAIR_NAMES[n]]["courses"]["chair"]["days"] for n in CHAIR_NAMES}
for n, title in noms.items():
    pid = CHAIR_NAMES[n]
    if n in dost:
        tier = "высшей степени" if chair_days[pid] >= 30 else ("I степени" if chair_days[pid] >= 25 else "II степени")
        award(pid, "chair", f"Сертификат «Достоявший», {tier}", f"«{title}»", "cert", "🪑")
    else:
        award(pid, "chair", "Сертификат усидчивости, II степени", f"«{title}»", "cert", "🧱")
award("24905927", "chair", "Особое отличие", "За героическое удержание стены между кормлениями.", "hall", "🍼")
CHAIR_ICON = {"crown": "👑", "stopwatch": "⏱️", "phoenix": "🔥"}
for ic, t, n, d in re.findall(r'icon:"(\w+)",title:"([^"]+)",name:"([^"]+)",val:"[^"]*",desc:"([^"]+)"', cs):
    award(CHAIR_NAMES[n], "chair", t, d, "hall", CHAIR_ICON.get(ic, "🏅"))
dipl = re.findall(r'"([^"]+)"', cs[cs.index("diplomaNames="):cs.index("];", cs.index("diplomaNames="))])
for n in dipl:
    award(CHAIR_NAMES[n], "chair", "Диплом участника", "Сел к стене. Это уже немало.", "cert", "📜")

# ---------- ОТЖИМАНИЯ ----------
mx = json.loads((PREV / "PushUpsResults" / "src" / "matrix.json").read_text(encoding="utf-8"))
for n, v in mx["m"].items():
    course(PUSH_NAMES[n], "pushups", total=v["total"], days=v["days"], max=max(x or 0 for x in v["vals"]), unit="reps",
           test=v.get("test"), final=v["vals"][-1])  # день 30 = один подход до отказа
PUSH_EMO = {"zol": "🥇", "plat": "💿", "stal": "🔩", "zhel": "⚙️", "bron": "🥉", "perv": "🎖️", "krov": "🩸", "d30": "📅",
            "x2": "⏫", "gerakl": "🦁", "sotnya": "💯", "ruki": "🫨", "ogon": "🔥", "lenty": "🎞️", "arifm": "🧮",
            "trev": "🚨", "molch": "🤐", "luna": "🌙", "liniya": "📏", "hrono": "⏱️", "otec": "👶", "zub": "🦷",
            "kot": "🐈", "yavka": "🚪", "kpd": "⚡", "lampa": "🪔", "edin": "👑", "luchn": "🏹", "almaz": "💎",
            "voda": "🏄", "prich": "🌱", "yazyk": "👅", "gum": "📜", "triyav": "🔁", "neprov": "❓", "orakul": "🔮",
            "klesh": "🕷️", "inzh": "🛠️", "reliz": "🚀", "neuro": "🤖", "sluch": "🎲", "narez": "🔪", "otstup": "🏳️"}
ns = {}
exec((PREV / "PushUpsResults" / "src" / "content3.py").read_text(encoding="utf-8"), ns)
for p in ns["PEOPLE"]:
    pid = PUSH_NAMES[p["key"]]
    people[pid]["epithets"].append({"ch": "pushups", "t": p["epithet"].capitalize()})
    for code in p["ord"]:
        t, d = ns["ORDERS"][code]
        award(pid, "pushups", t, d, "order", PUSH_EMO.get(code, "🎖️"))
by_name = {p["name"]: PUSH_NAMES[p["key"]] for p in ns["PEOPLE"]}
TITLE_EMO = {ns["ORDERS"][c][0].lower(): e for c, e in PUSH_EMO.items()}
for pr in ns["PRIZES"]:
    award(by_name[pr["w"]], "pushups", pr["t"].capitalize(), pr["d"], "hall", TITLE_EMO.get(pr["t"].lower(), "🏅"))
nick = collections.defaultdict(list)
for t, w in ns["NICKNAMES"]:
    nick[by_name[w]].append(t)

# ---------- ПРЕСС ----------
abs_lines = (ROOT / "ABSChallengeResults" / "index.html").read_text(encoding="utf-8").split("\n")
d = abs_lines[354]
dj = json.loads(d[d.index("{"):d.rindex("}") + 1])
for p in dj["participants"]:
    vals = [x for x in p["series"] if x]
    course(ABS_TICKS[p["tick"]], "abs", total=p["total"], days=p["days"], max=max(vals) if vals else 0, unit="reps")
start = next(i for i, l in enumerate(abs_lines) if l.startswith("const NOMS"))
for l in abs_lines[start + 1:]:
    if l.startswith("];"):
        break
    m = re.search(r'i:"([^"]+)",t:"([^"]+)",tick:"(\w+)",sub:"([^"]+)"', l)
    if m:
        award(ABS_TICKS[m.group(3)], "abs", m.group(2), m.group(4), "hall", m.group(1))

# ---------- БЁРПИ ----------
bd = json.loads((ROOT / "BurpeeChallengeResults" / "src" / "data.json").read_text(encoding="utf-8"))
for k, v in bd["p"].items():
    vals = [x[0] for x in v["s"] if x]
    course(BURPEE_KEYS[k], "burpee", total=sum(vals), days=len(vals), max=max(vals), unit="reps")
tpl = (ROOT / "BurpeeChallengeResults" / "src" / "template.html").read_text(encoding="utf-8")
for k in ["semen", "nikita", "vadim", "sasha", "lev", "vera", "alexander", "marsel", "max", "sergey", "yulia"]:
    i = tpl.index(f"\n{k}:{{")
    j = tpl.index("]]}", i)
    blk = tpl[i:j + 3]
    dx = re.search(r'dx:"([^"]+)"', blk).group(1)
    people[BURPEE_KEYS[k]]["epithets"].append({"ch": "burpee", "t": dx})
    for ic, t, desc in re.findall(r'\["([^"]*)","([^"]+)","([^"]+)"\]', blk[blk.index("ach:"):]):
        award(BURPEE_KEYS[k], "burpee", t, desc, "ach", ic)
for pid in ("377672278", "1021394934"):
    award(pid, "burpee", "Folie à deux", "Палата № 2: 30 из 30 совместных дней — одно и то же число.", "ach", "👫")
    award(pid, "burpee", "Один секундомер на двоих", "11 дней — совпадение до секунды.", "ach", "⏱️")
AMB = {"977313866": [("🕰️", "Пациент из будущего", "В первые сутки подписал отчёт «День 31»."), ("🪳", "Нутрициолог", "Тараканье молоко — белковая бомба."), ("🎭", "Драма в трёх /skip", "«Болит спина» → «всё ещё болеюшкин» → «плохо мне, плохо».")],
       "24905927": [("🎲", "Случайно", "«9 за 35 — случайно»."), ("🌬️", "Слишком много кислорода", "Подышал на приседе, не понравилось."), ("🏖️", "Отпуск", "«Работаю 15 часов в неделю вместо 50»."), ("🦴", "Ортопед", "Предупредил коллег о судьбе их поясниц.")],
       "712563629": [("👋", "Так, всем привет!", "Четыре визита."), ("⚡", "3,1 сек на бёрпи", "Лучший средний темп отделения.")],
       "148648420": [("🔙", "Я вернулся", "Однажды, на 12-е сутки.")],
       "282585544": [("🩺", "Самодиагностика", "«Сделал 7, понял, что капец не создан для спорта».")]}
for pid, ts in AMB.items():
    for ic, t, d in ts:
        award(pid, "burpee", t, d, "ach", ic)

# ---------- чат: сколько писал, сколько ему отвечал бот ----------
ex = json.loads((ROOT / "ChatHistory_till_16_10_2026" / "result.json").read_text(encoding="utf-8"))
msgs = [m for m in ex["messages"] if m.get("type") == "message"]
byid = {m["id"]: m for m in msgs}
sent = collections.Counter(str(m.get("from_id", "")).replace("user", "") for m in msgs)
replied = collections.Counter()
for m in msgs:
    if str(m.get("from_id")) == "user" + BOT:
        r = byid.get(m.get("reply_to_message_id"))
        if r:
            replied[str(r.get("from_id", "")).replace("user", "")] += 1

ORDER = ["plank", "chair", "pushups", "abs", "burpee"]
out = []
for pid, p in people.items():
    p["id"] = pid
    p["name"] = NAMES[pid]
    p["n"] = len(p["courses"])
    p["msgs"] = sent.get(pid, 0)
    p["bot_replies"] = replied.get(pid, 0)
    p["nicknames"] = nick.get(pid, [])
    p["courses"] = {c: p["courses"][c] for c in ORDER if c in p["courses"]}
    out.append(p)
out.sort(key=lambda p: (-p["n"], -len(p["awards"])))
OUT.write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
print(len(out), "people,", sum(len(p["awards"]) for p in out), "awards")
for p in out:
    print(f'{p["name"]:24} курсов {p["n"]}  наград {len(p["awards"]):2}  сообщ {p["msgs"]:4}  ответов бота {p["bot_replies"]:3}  {"/".join(p["courses"])}')
