#!/usr/bin/env python3
"""Generate competitor diff for Step 7 Part 3 and update validation-report.json."""
import json

BASE = "/home/dv/myskills/.allforai/product-map"

# Load existing validation report
with open(f"{BASE}/validation-report.json") as f:
    validation = json.load(f)

# Competitor diff based on web search
competitor_diff = {
    "comparison_scope": "comprehensive",
    "competitors_analyzed": ["Speak", "ELSA Speak", "Duolingo Max", "Praktika AI"],
    "data_sources": [
        "https://www.speak.com/",
        "https://elsaspeak.com/en/",
        "https://blog.duolingo.com/duolingo-max/",
        "https://praktika.ai/"
    ],
    "we_have_they_dont": [
        {
            "feature": "记忆曲线语境嵌入复习（对话中学的词在新场景中用出来）",
            "our_task": "T007",
            "note": "核心差异化：竞品用孤立卡片复习，我们将词汇嵌入新场景语境",
            "confirmed": False,
            "decision": None
        },
        {
            "feature": "紧急场景速学（出发前10分钟预演）",
            "our_task": "T021",
            "note": "针对新移民的独特场景，竞品均无此功能",
            "confirmed": False,
            "decision": None
        },
        {
            "feature": "三大角色专属场景路径（职场/旅行/移民）",
            "our_task": "T019",
            "note": "竞品有场景分类但无角色专属推荐路径",
            "confirmed": False,
            "decision": None
        },
        {
            "feature": "自由对话中自然引导复习记忆曲线词汇",
            "our_task": "T004",
            "note": "Speak有Free Talk但不与复习系统联动",
            "confirmed": False,
            "decision": None
        }
    ],
    "they_have_we_dont": [
        {
            "feature": "AI视频通话（视频头像对话）",
            "competitor": "Duolingo Max (Video Call with Lily), Praktika AI (AI avatars)",
            "note": "沉浸感更强，但技术成本高。建议评估是否作为V2功能",
            "confirmed": False,
            "decision": None
        },
        {
            "feature": "标准化考试备考（IELTS/TOEFL模块）",
            "competitor": "ELSA Speak, Praktika AI",
            "note": "高价值变现场景，但偏离我们的场景化口语定位",
            "confirmed": False,
            "decision": None
        },
        {
            "feature": "多语言支持",
            "competitor": "Speak (6语言), Duolingo (40+语言), Praktika (9语言)",
            "note": "我们聚焦英语口语，多语言非当前优先级",
            "confirmed": False,
            "decision": None
        },
        {
            "feature": "口音选择（美式/英式/澳式）",
            "competitor": "ELSA Speak",
            "note": "对新移民角色有价值（目标国口音），建议评估",
            "confirmed": False,
            "decision": None
        },
        {
            "feature": "语法解释模块",
            "competitor": "Duolingo Max (Explain My Answer)",
            "note": "我们以口语为核心，语法可融入对话报告中而非独立模块",
            "confirmed": False,
            "decision": None
        },
        {
            "feature": "多模态输入（上传照片/PDF发起对话）",
            "competitor": "Praktika AI",
            "note": "创新但使用频率低，非优先级",
            "confirmed": False,
            "decision": None
        }
    ],
    "both_have_different_approach": [
        {
            "feature": "发音纠正方式",
            "our_approach": "融入对话流程的轻提示，不打断交流（MEC2）",
            "their_approach": "ELSA: 独立评估模块+音素级详细报告",
            "note": "我们降低技术恐惧感，ELSA更专业但更有压迫感",
            "confirmed": False,
            "decision": None
        },
        {
            "feature": "游戏化体系",
            "our_approach": "连胜+排行榜+积分（轻社交，无好友系统）",
            "their_approach": "Duolingo: XP+联赛+成就+好友+Heart系统（重游戏化）",
            "note": "我们偏轻量，Duolingo偏重但粘性更强",
            "confirmed": False,
            "decision": None
        },
        {
            "feature": "场景对话模式",
            "our_approach": "角色专属场景+AI脚本+人工审核的混合内容",
            "their_approach": "Speak: 任务导向场景（完成3个任务自动结束）",
            "note": "我们更开放灵活，Speak更结构化",
            "confirmed": False,
            "decision": None
        }
    ]
}

# Update validation report
validation["competitor_diff"] = competitor_diff
validation["summary"]["competitor_gaps"] = (
    len(competitor_diff["they_have_we_dont"])
)

with open(f"{BASE}/validation-report.json", "w", encoding="utf-8") as f:
    json.dump(validation, f, ensure_ascii=False, indent=2)

# Update competitor-profile.json
competitor_profile = {
    "competitors": ["Speak", "ELSA Speak", "Duolingo Max", "Anki", "可栗口语", "Langua", "Praktika AI"],
    "comparison_scope": "comprehensive",
    "analysis_status": "completed",
    "analyzed_at": "2026-02-25T15:20:00Z",
    "analyzed_competitors": ["Speak", "ELSA Speak", "Duolingo Max", "Praktika AI"],
    "unavailable_competitors": ["Anki", "可栗口语", "Langua"],
    "unavailable_reason": "Anki为开源卡片工具非直接竞品；可栗口语和Langua信息有限"
}

with open(f"{BASE}/competitor-profile.json", "w", encoding="utf-8") as f:
    json.dump(competitor_profile, f, ensure_ascii=False, indent=2)

print("Competitor diff complete:")
print(f"  我有竞品没有: {len(competitor_diff['we_have_they_dont'])}")
print(f"  竞品有我没有: {len(competitor_diff['they_have_we_dont'])}")
print(f"  都有但做法不同: {len(competitor_diff['both_have_different_approach'])}")
