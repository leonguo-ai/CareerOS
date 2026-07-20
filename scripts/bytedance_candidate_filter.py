import csv

INPUT_PATH = "data/bytedance_discovered_jobs.csv"
OUTPUT_PATH = "data/bytedance_filtered_jobs.csv"


TARGET_KEYWORDS = [
    "商业分析",
    "经营分析",
    "财务",
    "财经",
    "战略",
    "策略",
    "产品运营",
    "商业化",
    "行业研究",
    "投资",
    "数据分析",
    "供应链",
    "国际支付",
    "风控",
    "管理培训生",
    "管培生"
]


LOW_RELEVANCE_KEYWORDS = [
    "前端开发",
    "后端开发",
    "算法",
    "机器学习",
    "大模型算法",
    "代码质量",
    "SRE",
    "运维",
    "客户端开发",
    "测试开发",
    "视频算法",
    "推荐算法"
]


GRADUATION_KEYWORDS = [
    "2027届",
    "面向2027届毕业生",
    "2026年9月-2027年8月",
    "ByteIntern"
]


rows = []

with open(INPUT_PATH, "r", encoding="utf-8-sig") as f:
    reader = csv.DictReader(f)

    for row in reader:
        rows.append(row)


filtered_results = []

for row in rows:
    job_text = row["job_title"].strip()
    job_text_lower = job_text.lower()

    score = 0
    reasons = []

    is_2027 = any(
        keyword.lower() in job_text_lower
        for keyword in GRADUATION_KEYWORDS
    )

    if is_2027:
        score += 35
        reasons.append("明确匹配2027届 +35")
    else:
        reasons.append("暂未确认2027届")

    matched_target_keywords = []

    for keyword in TARGET_KEYWORDS:
        if keyword.lower() in job_text_lower:
            matched_target_keywords.append(keyword)
            score += 15

    if matched_target_keywords:
        reasons.append(
            "匹配目标方向："
            + "、".join(matched_target_keywords)
        )

    matched_low_relevance_keywords = []

    for keyword in LOW_RELEVANCE_KEYWORDS:
        if keyword.lower() in job_text_lower:
            matched_low_relevance_keywords.append(keyword)
            score -= 25

    if matched_low_relevance_keywords:
        reasons.append(
            "低相关技术方向："
            + "、".join(matched_low_relevance_keywords)
        )

    if "实习" in job_text:
        score += 5
        reasons.append("实习岗位 +5")

    if score >= 50:
        recommendation = "priority_review"
    elif score >= 20:
        recommendation = "manual_review"
    else:
        recommendation = "low_priority"

    filtered_results.append(
        {
            "company": row["company"],
            "raw_job_title": job_text,
            "source_url": row["source_url"],
            "is_2027": "yes" if is_2027 else "unverified",
            "relevance_score": score,
            "matched_target_keywords": "、".join(
                matched_target_keywords
            ),
            "low_relevance_keywords": "、".join(
                matched_low_relevance_keywords
            ),
            "recommendation": recommendation,
            "reasons": "；".join(reasons),
            "status": row["status"],
            "review_status": "pending"
        }
    )


filtered_results.sort(
    key=lambda item: item["relevance_score"],
    reverse=True
)


print("===== ByteDance Candidate Filter V1 =====")
print(f"原始候选岗位：{len(rows)}")
print()

for rank, result in enumerate(filtered_results, start=1):
    short_title = result["raw_job_title"][:80]

    print(f"{rank}. {short_title}")
    print(f'   2027届：{result["is_2027"]}')
    print(f'   相关性评分：{result["relevance_score"]}')
    print(f'   建议：{result["recommendation"]}')
    print(f'   原因：{result["reasons"]}')
    print()


fieldnames = [
    "company",
    "raw_job_title",
    "source_url",
    "is_2027",
    "relevance_score",
    "matched_target_keywords",
    "low_relevance_keywords",
    "recommendation",
    "reasons",
    "status",
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
    writer.writerows(filtered_results)


priority_count = sum(
    result["recommendation"] == "priority_review"
    for result in filtered_results
)

manual_count = sum(
    result["recommendation"] == "manual_review"
    for result in filtered_results
)

low_priority_count = sum(
    result["recommendation"] == "low_priority"
    for result in filtered_results
)


print("===== 筛选报告 =====")
print(f"优先审核：{priority_count}")
print(f"人工审核：{manual_count}")
print(f"低优先级：{low_priority_count}")
print(f"结果已保存：{OUTPUT_PATH}")
