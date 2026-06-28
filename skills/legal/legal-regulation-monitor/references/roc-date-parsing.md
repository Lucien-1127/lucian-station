# 中華民國曆 → 西元日期轉換

## 國字數字對照

| 國字 | 數值 |
|------|:----:|
| 〇 / 零 | 0 |
| 一 | 1 |
| 二 / 兩 | 2 |
| 三 | 3 |
| 四 | 4 |
| 五 | 5 |
| 六 | 6 |
| 七 | 7 |
| 八 | 8 |
| 九 | 9 |

## 位數處理

```
十 → 乘以 10 並累加
百 → 乘以 100 並累加
千 → 乘以 1000 並累加
```

範例：
- 「一百零六」→ 0 + 0 + (1*100) + 0 + 6 = 106
- 「十三」→ (1*10) + 3 = 13
- 「二十」→ (2*10) + 0 = 20
- 「一百一十二」→ (1*100) + 0 + (1*10) + 2 = 112

### 邊界情況

| 輸入 | 正確 | 注意 |
|------|:----:|------|
| 十 | 10 | 十前面無數字時 = 1×10 |
| 二十 | 20 | |
| 一百 | 100 | 百後面無數字時不加 |
| 兩百 | 200 | 「兩」= 2 |

## 民國 → 西元

```
西元年 = 民國年 + 1911
```

範例：
- 民國 106 年 6 月 14 日 → 2017-06-14
- 民國 113 年 12 月 31 日 → 2024-12-31

## 實作模板

```python
def parse_roc_date(s: str) -> str:
    """中華民國一百零六年六月十四日 → '20170614'"""
    m = re.search(
        r"([〇零一二三四五六七八九十百千兩]+)\s*年\s*"
        r"([〇零一二三四五六七八九十百千兩]+)\s*月\s*"
        r"([〇零一二三四五六七八九十百千兩]+)\s*日",
        s or "",
    )
    if not m:
        return ""
    y = cn_to_num(m.group(1)) + 1911
    mo = cn_to_num(m.group(2))
    da = cn_to_num(m.group(3))
    if not y or not mo or not da:
        return ""
    return f"{y}{mo:02d}{da:02d}"


def cn_to_num(s: str) -> int:
    cn_digits = {
        "〇": 0, "零": 0, "一": 1, "二": 2, "三": 3, "四": 4,
        "五": 5, "六": 6, "七": 7, "八": 8, "九": 9, "兩": 2,
    }
    section = 0
    num = 0
    for ch in s:
        if ch in cn_digits:
            num = cn_digits[ch]
        elif ch == "十":
            section += (num or 1) * 10
            num = 0
        elif ch == "百":
            section += (num or 1) * 100
            num = 0
        elif ch == "千":
            section += (num or 1) * 1000
            num = 0
    return section + num
```

## 從沿革提取所有版本日期

```python
def parse_amendment_dates(text: str) -> list[str]:
    """從沿革文字擷取所有修正日期（升冪排序）"""
    dates = set()
    for m in re.finditer(
        r"中華民國\s*"
        r"([〇零一二三四五六七八九十百千兩]+\s*年"
        r"[〇零一二三四五六七八九十百千兩]+\s*月"
        r"[〇零一二三四五六七八九十百千兩]+\s*日)",
        text,
    ):
        d = parse_roc_date(m.group(1))
        if d:
            dates.add(d)
    return sorted(dates)
```

## 測試案例

```python
assert parse_roc_date("中華民國一百零六年六月十四日") == "20170614"
assert parse_roc_date("中華民國一百一十三年十二月三十一日") == "20241231"
assert parse_roc_date("中華民國九十九年一月一日") == "20100101"
assert parse_roc_date("") == ""
assert parse_roc_date("一些不包含日期的文字") == ""

# 沿革解析
text = """1. 中華民國一百零六年六月十四日總統令修正公布...
2. 中華民國一百一十三年十二月三十一日總統令修正公布..."""
assert parse_amendment_dates(text) == ["20170614", "20241231"]
```
