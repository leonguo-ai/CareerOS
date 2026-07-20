import csv
from pathlib import Path

VERIFIED_JOBS_PATH = "data/bytedance_verified_jobs.csv"
MASTER_RESUME_PATH = "resumes/master_resume.txt"
DETAIL_DIRECTORY = Path("data/bytedance_job_details")
OUTPUT_PATH = "data/bytedance_resume_shortlist.csv"


KEYWORD_LIBRARY = [
    "Python",
    "SQL",
    "Power BI",
    "Excel",
    "数据分析",
    "商业分析",
    "经营分析",
    "财务分析",
    "财务建模",
    "年度预算",
    "滚动预测",
    "成本分析",
    "供应链",
    "产品运营",
    "策略",
    "战略分析",
    "行业研究",
    "国际支付",
    "英语",
    "沟通能力",
    "项目管理"
]


JD_ALIASES = {
    "英语": ["英语", "英文", "English"],
    "数据分析": ["数据分析", "数据处理", "数据清洗", "数据洞察"],
    "商业分析": ["商业分析", "业务分析", "商业洞察"],
    "经营分析": ["经营分析", "经营数据", "经营指标"],
    "财务分析": ["财务分析", "财务测算", "财务模型"],
    "财务建模": ["财务建模", "财务模型", "估值模型"],
    "成本分析": ["成本分析", "成本控制", "成本优化", "成本差异"],
    "供应链": ["供应链", "供给策略", "采购", "物流"],
    "产品运营": ["产品运营", "运营策略", "策略运营"],
    "策略": ["策略", "策略分析", "策略制定"],
    "沟通能力": ["沟通能力", "沟通协调", "跨部门沟通"],
    "项目管理": ["项目管理", "项目推进", "项目协调"]
}


RESUME_ALIASES = {
    "英语": ["英语", "英文", "CET-6", "中英文"],
    "数据分析": [
        "数据分析",
        "数据处理",
        "数据清洗",
        "数据可视化",
        "商业分析",
        "经营分析"
    ],
    "商业分析": [
        "商业分析",
        "战略咨询",
        "决策分析",
        "经营分析"
    ],
    "经营分析": [
        "经营分析",
        "年度预算",
        "滚动预测",
        "盈利分析"
    ],
    "财务分析": [
        "财务分析",
        "财务测算",
        "DCF",
        "盈利预测"
    ],
    "财务建模": [
        "财务建模",
        "DCF",
        "估值模型",
        "TCO",
        "现金流折现"
    ],
    "成本分析": [
        "成本分析",
        "成本控制",
        "成本差异分析",
        "BOM成本分析"
    ],
    "供应链": [
        "供应链",
        "采购价格差异",
        "物料成本",
        "物流"
    ],
    "产品运营": [
        "产品运营",
        "业务流程",
        "工作流",
        "管理汇报"
    ],
    "策略": [
        "策略",
        "战略咨询",
        "情景分析",
        "决策分析"
    ],
    "战略分析": [
        "战略分析",
        "战略咨询",
        "情景分析",
        "敏感性分析"
    ],
    "沟通能力": [
        "跨部门协作",
        "管理层汇报",
        "研究例会",
        "投委会材料"
    ],
    "项目管理": [
        "项目负责人",
        "项目经历",
        "工作流",
        "跨部门协作"
    ]
}


# 读取完整主简历
with open(
    MASTER_RESUME_PATH,
    "r",
    encoding="utf-8"
) as f:
    resume = f.read()

resume_lower = resume.lower()


# 读取已验证岗位
with open(
    VERIFIED_JOBS_PATH,
    "r",
    encoding="utf-8-sig"
) as f:
    reader = csv.DictReader(f)
    verified_jobs = list(reader)


results = []

for index, job in enumerate(verified_jobs, start=1):
    detail_files = list(
        DETAIL_DIRECTORY.glob(f"{index:02d}_*.txt")
    )

    if not detail_files:
        print(f'跳过：{job["job_title"]} 缺少详情文本')
        continue

    jd_text = detail_files[0].read_text(
        encoding="utf-8"
    )

    jd_lower = jd_text.lower()

    required_keywords = []

    for keyword in KEYWORD_LIBRARY:
        aliases = JD_ALIASES.get(
            keyword,
            [keyword]
        )

        if any(
            alias.lower() in jd_lower
            for alias in aliases
        ):
            required_keywords.append(keyword)

    matched_keywords = []
    missing_keywords = []

    for keyword in required_keywords:
        aliases = RESUME_ALIASES.get(
            keyword,
            [keyword]
        )

        if any(
            alias.lower() in resume_lower
            for alias in aliases
        ):
            matched_keywords.append(keyword)
        else:
            missing_keywords.append(keyword)

    if required_keywords:
        resume_match_score = (
            len(matched_keywords)
            / len(required_keywords)
            * 100
        )
    else:
        resume_match_score = 0

    relevance_score = int(
        job["relevance_score"]
    )

    normalized_relevance = max(
        0,
        min(100, relevance_score + 50)
    )

    final_score = (
        resume_match_score * 0.70
        + normalized_relevance * 0.30
    )

    if job["page_status"] != "reachable":
        recommendation = "hold"
    elif final_score >= 75:
        recommendation = "priority_review"
    elif final_score >= 55:
        recommendation = "manual_review"
    else:
        recommendation = "low_priority"

    results.append(
        {
            "company": job["company"],
            "job_title": job["job_title"],
            "source_url": job["source_url"],
            "page_status": job["page_status"],
            "is_2027": job["is_2027"],
            "required_keywords": "、".join(
                required_keywords
            ),
            "matched_keywords": "、".join(
                matched_keywords
            ),
            "missing_keywords": "、".join(
                missing_keywords
            ),
            "resume_match_score": (
                f"{resume_match_score:.1f}"
            ),
            "relevance_score": relevance_score,
            "final_score": f"{final_score:.1f}",
            "recommendation": recommendation,
            "review_status": "pending",
            "application_status": "not_applied"
        }
    )


results.sort(
    key=lambda row: float(row["final_score"]),
    reverse=True
)


print("===== ByteDance Resume Matcher V1 =====")
print(f"成功匹配岗位：{len(results)}")
print()

for rank, result in enumerate(results, start=1):
    print(f'{rank}. {result["job_title"]}')
    print(
        f'   简历匹配率：'
        f'{result["resume_match_score"]}%'
    )
    print(
        f'   综合评分：'
        f'{result["final_score"]}'
    )
    print(
        f'   缺失关键词：'
        f'{result["missing_keywords"] or "无"}'
    )
    print(
        f'   建议：'
        f'{result["recommendation"]}'
    )
    print()


fieldnames = [
    "rank",
    "company",
    "job_title",
    "source_url",
    "page_status",
    "is_2027",
    "required_keywords",
    "matched_keywords",
    "missing_keywords",
    "resume_match_score",
    "relevance_score",
    "final_score",
    "recommendation",
    "review_status",
    "application_status"
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

    for rank, result in enumerate(
        results,
        start=1
    ):
        writer.writerow(
            {
                "rank": rank,
                **result
            }
        )


priority_count = sum(
    result["recommendation"] == "priority_review"
    for result in results
)

manual_count = sum(
    result["recommendation"] == "manual_review"
    for result in results
)

low_count = sum(
    result["recommendation"] == "low_priority"
    for result in results
)

hold_count = sum(
    result["recommendation"] == "hold"
    for result in results
)


print("===== 字节岗位匹配报告 =====")
print(f"优先审核：{priority_count}")
print(f"人工审核：{manual_count}")
print(f"低优先级：{low_count}")
print(f"暂缓处理：{hold_count}")
print(f"结果已保存：{OUTPUT_PATH}")