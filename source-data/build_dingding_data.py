import json
import time
import urllib.parse
import urllib.request
from pathlib import Path

SOURCE = Path("dingding_source_chars.json")
OUT = Path("dingding_radical_game_data.json")

KANGXI_RADICALS = set(
    "一丨丶丿乙亅二亠人儿入八冂冖冫几凵刀力勹匕匚匸十卜卩厂厶又口囗土士夂夊夕大女子宀寸小尢尸屮山巛工己巾干幺广廴廾弋弓彐彡彳心戈戶手支攴文斗斤方无日曰月木欠止歹殳毋比毛氏气水火爪父爻爿片牙牛犬玄玉瓜瓦甘生用田疋疒癶白皮皿目矛矢石示禸禾穴立竹米糸缶网羊羽老而耒耳聿肉臣自至臼舌舛舟艮色艸虍虫血行衣襾見角言谷豆豕豸貝赤走足身車辛辰辵邑酉釆里金長門阜隶隹雨青非面革韋韭音頁風飛食首香馬骨高髟鬥鬯鬲鬼魚鳥鹵鹿麥麻黃黍黑黹黽鼎鼓鼠鼻齊齒龍龜龠"
)

PREFERRED_COMPONENTS = {
    "討": ["寸", "口", "十"], "支": ["十", "又", "手"], "壘": ["田", "土", "厶"], "菠": ["水", "皮", "又"], "勝": ["力", "肉", "刀"],
    "觸": ["角", "虫", "网"], "振": ["辰", "厂", "衣"], "局": ["尸", "口", "勹"], "反": ["又", "厂", "手"], "輸": ["車", "肉", "人"],
    "曉": ["日", "土", "儿"], "賽": ["貝", "宀", "八"], "弱": ["弓", "冫", "羽"], "衰": ["衣", "口", "一"], "准": ["隹", "水", "二"],
    "腰": ["肉", "月", "襾"], "贏": ["貝", "肉", "亡"], "硬": ["石", "日", "一"], "挨": ["手", "矢", "厶"], "罵": ["网", "馬", "口"],
    "衝": ["行", "重", "彳"], "猶": ["犬", "酉", "八"], "豫": ["豕", "矛", "象"], "膳": ["肉", "羊", "口"], "插": ["手", "臼", "千"],
    "領": ["頁", "人", "卩"], "喘": ["口", "山", "而"], "愈": ["心", "肉", "人"], "躁": ["足", "口", "木"], "扮": ["手", "刀", "八"],
    "提": ["手", "日", "疋"], "似": ["人", "匕", "丶"], "眺": ["目", "儿", "冫"], "秀": ["禾", "乃", "丿"], "趨": ["走", "屮", "勹"],
    "舒": ["舌", "予", "人"], "緩": ["糸", "爪", "又"], "巧": ["工", "一", "乙"], "透": ["辵", "禾", "乃"], "棧": ["木", "戈", "一"],
    "盛": ["皿", "戈", "厂"], "劃": ["刀", "田", "聿"], "選": ["辵", "己", "廾"], "途": ["辵", "人", "禾"], "霧": ["雨", "力", "矛"],
    "關": ["門", "幺", "一"], "椅": ["木", "大", "口"], "訣": ["言", "大", "人"], "乃": ["乙", "弓", "丿"], "聖": ["耳", "口", "王"],
    "獨": ["犬", "虫", "网"], "嫂": ["女", "臼", "又"], "菩": ["艸", "口", "立"], "薩": ["艸", "生", "阜"], "丹": ["冂", "一", "丶"],
    "芭": ["艸", "己", "乙"], "焰": ["火", "臼", "勹"], "擔": ["手", "言", "儿"], "摘": ["手", "口", "亠"], "熄": ["火", "心", "自"],
    "磚": ["石", "寸", "田"], "薄": ["艸", "水", "寸"], "賺": ["貝", "八", "女"], "搬": ["手", "舟", "殳"], "梯": ["木", "弓", "丿"],
    "咳": ["口", "人", "亠"], "醫": ["酉", "殳", "匚"], "危": ["卩", "厂", "儿"], "嚴": ["口", "厂", "攴"], "藤": ["艸", "水", "肉"],
    "租": ["禾", "一", "目"], "蒙": ["艸", "冖", "豕"], "瘦": ["疒", "臼", "又"], "肺": ["肉", "巾", "一"], "炎": ["火", "八", "日"],
    "鐘": ["金", "立", "里"], "響": ["音", "邑", "食"], "欄": ["木", "門", "柬"], "牲": ["牛", "生", "一"], "踴": ["足", "力", "用"],
    "穫": ["禾", "隹", "又"], "任": ["人", "土", "士"], "務": ["力", "矛", "夂"], "閱": ["門", "口", "儿"], "扶": ["手", "大", "人"],
    "捐": ["手", "口", "肉"], "烈": ["火", "歹", "刀"], "犧": ["牛", "羊", "戈"],
}

FORCED_RADICALS = {
    "准": "冫",
    "醫": "酉",
    "危": "卩",
    "乃": "丿",
    "丹": "丶",
    "務": "力",
    "響": "音",
}

SIMILAR_RADICALS = {
    "肉": ["骨", "舟", "頁", "目", "心", "自"],
    "犬": ["豸", "馬", "牛", "鹿", "鼠", "鳥"],
    "手": ["寸", "支", "攴", "爪", "又", "廾"],
    "水": ["冫", "雨", "川", "巛", "火", "气"],
    "艸": ["竹", "禾", "木", "米", "生", "屮"],
    "辵": ["走", "行", "彳", "足", "止", "廴"],
    "口": ["囗", "曰", "日", "舌", "言", "音"],
    "木": ["禾", "竹", "米", "艸", "支", "爿"],
    "火": ["水", "日", "黑", "心", "赤", "光"],
    "言": ["口", "舌", "音", "文", "曰", "心"],
    "貝": ["頁", "見", "目", "谷", "金", "鼎"],
    "酉": ["里", "曰", "襾", "皿", "食", "豆"],
    "金": ["玉", "石", "貝", "長", "里", "缶"],
    "門": ["鬥", "囗", "冂", "戶", "广", "宀"],
    "疒": ["广", "宀", "尸", "厂", "肉", "心"],
    "目": ["日", "曰", "自", "見", "貝", "皿"],
    "足": ["走", "辵", "止", "行", "彳", "身"],
}

FALLBACK_RADICALS = ["口", "木", "水", "手", "心", "艸", "人", "土", "言", "辵", "肉", "目", "巾", "虫", "宀", "鳥", "足", "金", "糸", "火"]


def clean_option(text):
    return str(text or "").replace("`", "").replace("~", "").strip()


def radical_from_moedict(ch):
    url = "https://www.moedict.tw/a/" + urllib.parse.quote(ch) + ".json"
    with urllib.request.urlopen(url, timeout=12) as response:
        data = json.loads(response.read().decode("utf-8"))
    return clean_option(data.get("r"))


def fill_radical_distractors(radical, preferred):
    options = []
    candidates = preferred + SIMILAR_RADICALS.get(radical, []) + FALLBACK_RADICALS
    for option in candidates:
        option = clean_option(option)
        if option == "灬":
            option = "火"
        if option and option in KANGXI_RADICALS and option != radical and option not in options:
            if radical == "肉" and option == "月":
                continue
            options.append(option)
        if len(options) == 3:
            return options
    raise ValueError(f"not enough distractors for radical {radical}")


def main():
    source = json.loads(SOURCE.read_text(encoding="utf-8"))
    cache_path = Path("dingding_radical_cache.json")
    cache = json.loads(cache_path.read_text(encoding="utf-8")) if cache_path.exists() else {}
    output = {"title": source["title"], "source_note": source["source_note"], "levels": []}
    missing = []
    for level in source["levels"]:
        items = []
        for ch in level["chars"]:
            radical = clean_option(FORCED_RADICALS.get(ch) or cache.get(ch))
            if not radical:
                try:
                    radical = radical_from_moedict(ch)
                    if radical:
                        cache[ch] = radical
                        time.sleep(0.08)
                except Exception as exc:
                    missing.append((ch, str(exc)))
            if not radical:
                missing.append((ch, "no radical"))
                radical = clean_option(PREFERRED_COMPONENTS[ch][0])
            if radical not in KANGXI_RADICALS:
                missing.append((ch, f"non-radical answer: {radical}"))
            options = fill_radical_distractors(radical, PREFERRED_COMPONENTS.get(ch, []))
            items.append({"char": ch, "radical": radical, "distractors": options})
        output["levels"].append({"title": level["title"], "items": items})
    cache_path.write_text(json.dumps(cache, ensure_ascii=False, indent=2), encoding="utf-8")
    OUT.write_text(json.dumps(output, ensure_ascii=False, indent=2), encoding="utf-8")
    print("wrote", OUT)
    print("missing", missing)


if __name__ == "__main__":
    main()
