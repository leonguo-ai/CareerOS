import csv

INPUT_PATH = "data/discovered_entry_links.csv"
OUTPUT_PATH = "data/reviewed_entry_links.csv"

POSITIVE_TEXT_KEYWORDS = {
    "职位": 30,
    "岗位": 25,
    "职位搜索": 35,
    "岗位投递": 25,
    "查看职位": 30,
    "校园招聘": 15,
    "校招": 15,
    "应届生": 15,
    "实习生": 12,
    "提前批": 15
}

POSITIVE_URL_KEYWORDS = {
    "position": 35,
    "job": 30,
    "jobs": 30,
    "career": 20,
    "campus": 15,
    "recruit": 20
}

NEGATIVE_TEXT_KEYWORDS = {
    "隐私": -40,
    "协议": -35,
    "公告": -15,
    "攻略": -15,
    "了解我们": -20,
    "关于我们": -20
}

INVALID_URL_PREFIXES = [
    "javascript:",
    "mailto:",
    "tel:",
    "#"
]

links = []

with open(INPUT_PATH, "r", encoding="utf-8-sig") as f:
    reader = csv.DictReader(f)

    for row in reader:
        links.append(row)

reviewed_links = []

for link in links:
    score = 0
    reasons = []

    link_text = link["link_text"].strip()
    entry_url = link["entry_url"].strip()

    text_lower = link_text.lower()
    url_lower = entry_url.lower()

    is_invalid_url = any(
        url_lower.startswith(prefix)
        for prefix in INVALID_URL_PREFIXES
    )

    if is_invalid_url:
        score -= 100
        reasons.append("不可直接访问的链接 -100")

    for keyword, points in POSITIVE_TEXT_KEYWORDS.items():
        if keyword.lower() in text_lower:
            score += points
            reasons.append(
                f"入口文字包含“{keyword}” +{points}"
            )

    for keyword, points in POSITIVE_URL_KEYWORDS.items():
        if keyword.lower() in url_lower:
            score += points
            reasons.append(
                f"网址包含“{keyword}” +{points}"
            )

    for keyword, points in NEGATIVE_TEXT_KEYWORDS.items():
        if keyword.lower() in text_lower:
            score += points
            reasons.append(
                f"入口文字包含“{keyword}” {points}"
            )

    if is_invalid_url:
        classification = "requires_click_adapter"
        review_status = "manual_review"
    elif score >= 50:
        classification = "likely_job_list"
        review_status = "approved"
    elif score >= 20:
        classification = "possible_recruitment_entry"
        review_status = "manual_review"
    else:
        classification = "low_confidence"
        review_status = "rejected"

    reviewed_links.append(
        {
            "source_id": link["source_id"],
            "company": link["company"],
            "link_text": link_text,
            "entry_url": entry_url,
            "score": score,
            "classification": classification,
            "reasons": "；".join(reasons),
            "review_status": review_status
        }
    )

reviewed_links.sort(
    key=lambda item: item["score"],
    reverse=True
)

print("===== CareerOS Entry Link Reviewer V1 =====")
print(f"候选入口数量：{len(reviewed_links)}")
print()

for rank, link in enumerate(reviewed_links, start=1):
    print(
        f'{rank}. {link["company"]} | '
        f'{link["link_text"]}'
    )
    print(f'   评分：{link["score"]}')
    print(f'   分类：{link["classification"]}')
    print(f'   审核状态：{link["review_status"]}')
    print(f'   网址：{link["entry_url"]}')
    print(f'   原因：{link["reasons"]}')
    print()

fieldnames = [
    "source_id",
    "company",
    "link_text",
    "entry_url",
    "score",
    "classification",
    "reasons",
    "review_status"
]

with open(
    OUTPUT_PATH,
    "w",
    newline="",
    encoding="utf-8-sig"
) as f:
    writer = csv.DictWriter(
        f,
        fieldnames=fieldnames
    )
    writer.writeheader()
    writer.writerows(reviewed_links)

approved_count = sum(
    link["review_status"] == "approved"
    for link in reviewed_links
)

manual_review_count = sum(
    link["review_status"] == "manual_review"
    for link in reviewed_links
)

rejected_count = sum(
    link["review_status"] == "rejected"
    for link in reviewed_links
)

print("===== 入口审核报告 =====")
print(f"自动批准：{approved_count}")
print(f"需要人工检查：{manual_review_count}")
print(f"自动排除：{rejected_count}")
print(f"审核结果已保存：{OUTPUT_PATH}")
