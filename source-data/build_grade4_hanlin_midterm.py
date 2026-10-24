import json
import time
import urllib.parse
import urllib.request
from pathlib import Path


HERE = Path(__file__).resolve().parent
SOURCE = HERE / "grade4-hanlin-midterm-source.json"
CACHE = HERE / "grade4-hanlin-midterm-radicals.json"
OUTPUT = HERE / "grade4-hanlin-midterm.json"

KANGXI_RADICALS = set(
    "一丨丶丿乙亅二亠人儿入八冂冖冫几凵刀力勹匕匚匸十卜卩厂厶又口囗土士夂夊夕大女子宀寸小尢尸屮山巛工己巾干幺广廴廾弋弓彐彡彳心戈戶手支攴文斗斤方无日曰月木欠止歹殳毋比毛氏气水火爪父爻爿片牙牛犬玄玉瓜瓦甘生用田疋疒癶白皮皿目矛矢石示禸禾穴立竹米糸缶网羊羽老而耒耳聿肉臣自至臼舌舛舟艮色艸虍虫血行衣襾見角言谷豆豕豸貝赤走足身車辛辰辵邑酉釆里金長門阜隶隹雨青非面革韋韭音頁風飛食首香馬骨高髟鬥鬯鬲鬼魚鳥鹵鹿麥麻黃黍黑黹黽鼎鼓鼠鼻齊齒龍龜龠"
)

SIMILAR_GROUPS = [
    ["口", "囗", "曰", "日", "目"],
    ["水", "冫", "雨", "巛", "气"],
    ["手", "寸", "支", "攴", "爪", "廾"],
    ["心", "肉", "月", "自", "骨"],
    ["木", "禾", "竹", "米", "艸"],
    ["言", "舌", "音", "文", "口"],
    ["走", "足", "辵", "行", "彳", "止"],
    ["人", "儿", "入", "八", "大"],
    ["金", "玉", "石", "貝", "缶"],
    ["阜", "邑", "山", "厂", "广", "宀"],
    ["糸", "幺", "巾", "衣", "网"],
    ["犬", "豸", "牛", "馬", "鹿"],
    ["鳥", "羽", "隹", "飛"],
    ["食", "米", "禾", "豆", "皿"],
    ["車", "舟", "行", "辵", "門"],
    ["火", "日", "赤", "黑", "光"],
    ["立", "辛", "亠", "文", "生"],
    ["土", "士", "山", "里", "田"],
    ["女", "子", "毋", "幺", "大"],
    ["刀", "力", "弓", "戈", "矛"],
    ["牙", "齒", "角", "見", "頁"],
    ["耳", "聿", "臣", "自", "臼"],
    ["耒", "禾", "木", "竹", "米"],
    ["鼓", "鬥", "鼎", "高", "鬲"],
    ["一", "丨", "丶", "丿", "亅"],
    ["白", "自", "日", "曰", "目"],
    ["癶", "夂", "夊", "廴", "辵"],
    ["老", "士", "土", "耒", "耳"],
    ["艮", "良", "見", "頁", "首"],
    ["甘", "曰", "口", "舌", "皿"],
    ["匚", "匸", "凵", "冂", "囗"],
    ["虫", "魚", "鳥", "鼠", "黽"],
]

FALLBACKS = ["口", "木", "水", "手", "心", "艸", "人", "土", "言", "辵", "目", "巾", "虫", "宀", "鳥", "足", "金", "糸", "火"]


def clean_radical(value):
    return str(value or "").replace("`", "").replace("~", "").strip()


def lookup_radical(char):
    url = "https://www.moedict.tw/a/" + urllib.parse.quote(char) + ".json"
    request = urllib.request.Request(url, headers={"User-Agent": "radical-practice/1.0"})
    with urllib.request.urlopen(request, timeout=15) as response:
        data = json.loads(response.read().decode("utf-8"))
    return clean_radical(data.get("r"))


def distractors_for(radical):
    candidates = []
    for group in SIMILAR_GROUPS:
        if radical in group:
            candidates.extend(group)
    candidates.extend(FALLBACKS)
    result = []
    for option in candidates:
        if option == radical or option in result or option not in KANGXI_RADICALS:
            continue
        result.append(option)
        if len(result) == 3:
            return result
    raise ValueError(f"Cannot find three distractors for {radical}")


def main():
    source = json.loads(SOURCE.read_text(encoding="utf-8"))
    cache = json.loads(CACHE.read_text(encoding="utf-8")) if CACHE.exists() else {}
    output = {
        "title": source["title"],
        "source_note": "部首以教育部《重編國語辭典修訂本》／萌典資料整理。",
        "levels": [],
    }

    for level in source["levels"]:
        items = []
        for char in level["chars"]:
            radical = clean_radical(cache.get(char))
            if not radical:
                radical = lookup_radical(char)
                cache[char] = radical
                time.sleep(0.08)
            if radical not in KANGXI_RADICALS:
                raise ValueError(f"{char}: invalid radical {radical!r}")
            items.append(
                {
                    "char": char,
                    "radical": radical,
                    "distractors": distractors_for(radical),
                }
            )
        output["levels"].append({"title": level["title"], "items": items})

    CACHE.write_text(json.dumps(cache, ensure_ascii=False, indent=2), encoding="utf-8")
    OUTPUT.write_text(json.dumps(output, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Wrote {OUTPUT}")
    print("Levels:", [len(level["items"]) for level in output["levels"]])


if __name__ == "__main__":
    main()
