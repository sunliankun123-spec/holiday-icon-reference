from __future__ import annotations

from typing import List


CHRISTMAS_ELEMENTS = [
    "圣诞老人",
    "驯鹿",
    "圣诞树",
    "树顶星",
    "圣诞挂球",
    "拐杖糖",
    "礼物盒",
    "蝴蝶结",
    "圣诞袜",
    "圣诞花环",
    "槲寄生",
    "冬青叶",
    "雪人",
    "雪花",
    "铃铛",
    "雪橇",
    "烟囱",
    "壁炉",
    "姜饼人",
    "姜饼屋",
    "热可可",
    "棉花糖杯",
    "圣诞饼干",
    "圣诞布丁",
    "烤火鸡",
    "树桩蛋糕",
    "松果",
    "冬季手套",
    "针织围巾",
    "毛线帽",
    "冰刀鞋",
    "红丝带",
    "串灯",
    "降临节日历",
    "胡桃夹子",
    "天使挂饰",
    "唱诗班",
    "教堂钟",
    "蜡烛",
    "提灯",
    "给圣诞老人的信",
    "北极路牌",
    "精灵帽",
    "精灵鞋",
    "薄荷糖旋纹",
    "雪花水晶球",
    "北极熊",
    "礼物堆",
    "圣诞袜纹样",
    "节日针织手套",
]


GENERIC_CATEGORIES = [
    "吉祥物",
    "传统服饰",
    "代表性食物",
    "节日甜点",
    "节日饮品",
    "主视觉符号",
    "动物符号",
    "花卉符号",
    "叶片纹样",
    "图案纹样",
    "节日灯光",
    "灯笼",
    "横幅",
    "礼品",
    "挂饰",
    "乐器",
    "舞蹈动作",
    "烟花图案",
    "门票图标",
    "日历图标",
    "贺卡",
    "贴纸图标",
    "表情风图标",
    "毛绒玩具",
    "帽子配饰",
    "包包配饰",
    "鞋子配饰",
    "项链配饰",
    "手链配饰",
    "戒指配饰",
    "甜味小吃",
    "咸味小吃",
    "街头美食",
    "家居装饰",
    "餐桌装饰",
    "窗户装饰",
    "门饰",
    "舞台装饰",
    "旅行符号",
    "城市地标",
    "交通图标",
    "天气图标",
    "太阳元素",
    "月亮元素",
    "星星元素",
    "云朵元素",
    "海浪元素",
    "山脉元素",
    "幸运物",
    "庆祝手势",
]


def _normalize_theme(theme: str) -> str:
    return " ".join(theme.strip().lower().split())


def build_50_elements(theme: str) -> List[str]:
    normalized = _normalize_theme(theme)
    if normalized in {"christmas", "xmas"}:
        return CHRISTMAS_ELEMENTS[:50]

    base = [f"{theme}{item}" for item in GENERIC_CATEGORIES]
    # Ensure exactly 50 items and stable order.
    return base[:50]
