"""Сборка index.html: people.json + tickers.json + botlines.json -> template.html.
    python src/build.py              # собрать
    python src/build.py --import DIR # сначала забрать отобранные реплики из DIR (curated_*.json)
"""
import json
import pathlib
import sys

here = pathlib.Path(__file__).parent
DROP = ["Пиздеть"]  # слишком грубо для мемориала

if len(sys.argv) > 2 and sys.argv[1] == "--import":
    src = pathlib.Path(sys.argv[2])
    tick = {}
    for f in ("curated_A.json", "curated_B.json", "curated_C.json"):
        for k, v in json.loads((src / f).read_text(encoding="utf-8")).items():
            tick[k] = [x for x in v if not any(d in x for d in DROP)]
    (here / "tickers.json").write_text(json.dumps(tick, ensure_ascii=False, indent=1), encoding="utf-8")
    bot = json.loads((src / "curated_BOT.json").read_text(encoding="utf-8"))
    (here / "botlines.json").write_text(json.dumps(bot, ensure_ascii=False, indent=1), encoding="utf-8")
    print("imported", sum(len(v) for v in tick.values()), "person lines,", len(bot), "bot lines")


def compact(name):
    return json.dumps(json.loads((here / name).read_text(encoding="utf-8")), ensure_ascii=False, separators=(",", ":"))


tpl = (here / "template.html").read_text(encoding="utf-8")
out = (tpl.replace("/*__PEOPLE__*/[]", compact("people.json"))
          .replace("/*__TICK__*/{}", compact("tickers.json"))
          .replace("/*__BOT__*/[]", compact("botlines.json")))
(here.parent / "index.html").write_text(out, encoding="utf-8")
print("index.html", len(out.encode("utf-8")), "bytes")
