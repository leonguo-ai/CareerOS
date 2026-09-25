"""Evidence-based, human-reviewed ByteDance shortlist. Standard library only."""
import argparse
import csv
import json
import os
from datetime import datetime, timedelta, timezone
from pathlib import Path

from job_identity import job_id

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / 'data'
REVIEW_PATH = DATA / 'bytedance_reviews.json'
FIELDS = ['job_id', 'company', 'job_title', 'source_url', 'page_status',
          'page_checked_at', 'opening_status', 'opening_evidence',
          'eligibility_2027', 'eligibility_evidence', 'review_status',
          'application_status', 'detail_path', 'requirements_evidence',
          'resume_evidence', 'match_score', 'recommendation']
TERMS = {
    'Python': ['Python'], 'SQL': ['SQL'], 'Excel': ['Excel'],
    '数据分析': ['数据分析', '数据处理'],
    '经营分析': ['经营分析', '经营指标'],
    '财务分析': ['财务分析', '财务测算'],
    '供应链': ['供应链', '采购'],
    '策略分析': ['策略分析', '策略制定'],
    '项目管理': ['项目管理', '项目推进'],
    '英语': ['英语', '英文', 'English'],
}
SOFT_TERMS = {'项目管理', '英语'}


def read_csv(path):
    if not path.exists():
        return []
    with path.open(encoding='utf-8-sig', newline='') as fh:
        return list(csv.DictReader(fh))


def read_reviews(path):
    if not path.exists():
        return {}
    result = json.loads(path.read_text(encoding='utf-8'))
    if not isinstance(result, dict):
        raise ValueError('Review store must be a JSON object keyed by job_id')
    return result


def write_reviews(path, reviews):
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + '.tmp')
    try:
        tmp.write_text(json.dumps(reviews, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
        os.replace(tmp, path)
    finally:
        tmp.unlink(missing_ok=True)


def evidence_lines(text, aliases):
    return [line.strip()[:240] for line in text.splitlines()
            if line.strip() and any(a.casefold() in line.casefold() for a in aliases)][:3]


def match_requirements(jd, resume):
    requirements, resume_evidence = {}, {}
    for term, aliases in TERMS.items():
        jd_lines = evidence_lines(jd, aliases)
        if not jd_lines:
            continue
        requirements[term] = jd_lines
        hits = evidence_lines(resume, aliases) if resume else []
        resume_evidence[term] = {
            'status': ('not_checked' if not resume else
                       'human_review' if term in SOFT_TERMS and hits else
                       'evidence_found' if hits else
                       'human_review' if term in SOFT_TERMS else 'not_found'),
            'excerpt': hits,
        }
    return requirements, resume_evidence


def current_opening(review, now, max_age_days):
    if review.get('opening_status') != 'open':
        return review.get('opening_status', 'unverified')
    try:
        checked = datetime.fromisoformat(review['opening_checked_at'].replace('Z', '+00:00'))
        if checked.tzinfo is None:
            return 'unverified'
        return 'open' if now - checked <= timedelta(days=max_age_days) and checked <= now else 'unverified'
    except (KeyError, ValueError, TypeError):
        return 'unverified'


def current_page(detail, now, max_age_days):
    if detail.get('page_status') != 'reachable':
        return detail.get('page_status', 'unverified')
    try:
        checked = datetime.fromisoformat(detail['verified_at'].replace('Z', '+00:00'))
        if checked.tzinfo is None:
            return 'unverified'
        return 'reachable' if checked <= now and now - checked <= timedelta(days=max_age_days) else 'unverified'
    except (KeyError, ValueError, TypeError):
        return 'unverified'


def build(filtered, verified, detail_dir, reviews, resume='', now=None, max_age_days=7):
    now = now or datetime.now(timezone.utc)
    indexed = {job_id(r['source_url']): r for r in verified if r.get('source_url')}
    output = []
    seen = set()
    for candidate in filtered:
        if not candidate.get('source_url'):
            continue
        ident = job_id(candidate['source_url'])
        if ident in seen:
            continue
        seen.add(ident)
        detail = indexed.get(ident, {})
        review = reviews.get(ident, {})
        path = detail_dir / f'{ident}.txt'
        jd = path.read_text(encoding='utf-8') if path.is_file() else ''
        requirements, evidence = match_requirements(jd, resume)
        matched = sum(v['status'] == 'evidence_found' for v in evidence.values())
        score = f'{matched / len(requirements) * 100:.1f}' if requirements and resume else ''
        opening = current_opening(review, now, max_age_days)
        page = current_page(detail, now, max_age_days)
        eligibility = review.get('eligibility_2027', 'unverified')
        review_status = review.get('review_status', 'pending')
        # No priority or application-ready label until independent checks agree.
        if review_status == 'rejected':
            recommendation = 'rejected'
        elif page != 'reachable' or not jd or opening != 'open' or eligibility != 'yes':
            recommendation = 'verify_first'
        elif review_status == 'approved':
            recommendation = 'manually_approved'
        elif review_status == 'rejected':
            recommendation = 'rejected'
        else:
            recommendation = 'manual_review'
        output.append({
            'job_id': ident, 'company': candidate.get('company', '字节跳动'),
            'job_title': detail.get('job_title') or candidate.get('raw_job_title', '')[:80],
            'source_url': candidate['source_url'],
            'page_status': page,
            'page_checked_at': detail.get('verified_at', ''),
            'opening_status': opening,
            'opening_evidence': review.get('opening_evidence', ''),
            'eligibility_2027': eligibility,
            'eligibility_evidence': review.get('eligibility_evidence', ''),
            'review_status': review_status,
            'application_status': review.get('application_status', 'not_applied'),
            'detail_path': str(path) if jd else '',
            'requirements_evidence': json.dumps(requirements, ensure_ascii=False),
            'resume_evidence': json.dumps(evidence, ensure_ascii=False),
            'match_score': score, 'recommendation': recommendation,
        })
    return sorted(output, key=lambda r: (r['recommendation'] != 'manually_approved',
                                          r['recommendation'] != 'manual_review',
                                          -float(r['match_score'] or 0)))


def save_csv(path, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('w', encoding='utf-8-sig', newline='') as fh:
        writer = csv.DictWriter(fh, FIELDS)
        writer.writeheader()
        writer.writerows(rows)


def set_review(reviews, ident, opening=None, eligibility=None, review=None,
               application=None, opening_evidence='', eligibility_evidence='', now=None):
    now = now or datetime.now(timezone.utc)
    if opening in ('open', 'closed') and not opening_evidence.strip():
        raise ValueError('Opening status requires --opening-evidence')
    if eligibility in ('yes', 'no') and not eligibility_evidence.strip():
        raise ValueError('Eligibility status requires --eligibility-evidence')
    item = dict(reviews.get(ident, {}))
    if opening is not None:
        item['opening_status'] = opening
        item['opening_evidence'] = opening_evidence if opening != 'unverified' else ''
        item['opening_checked_at'] = now.isoformat()
    if eligibility is not None:
        item['eligibility_2027'] = eligibility
        item['eligibility_evidence'] = eligibility_evidence if eligibility != 'unverified' else ''
    if review is not None:
        item['review_status'] = review
    if application is not None:
        item['application_status'] = application
    item['updated_at'] = now.isoformat()
    reviews[ident] = item


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='command', required=True)
    generate = sub.add_parser('build', help='Merge job evidence and private review state')
    generate.add_argument('--filtered', type=Path, default=DATA / 'bytedance_filtered_jobs.csv')
    generate.add_argument('--verified', type=Path, default=DATA / 'bytedance_verified_jobs.csv')
    generate.add_argument('--details', type=Path, default=DATA / 'bytedance_job_details')
    generate.add_argument('--reviews', type=Path, default=REVIEW_PATH)
    generate.add_argument('--resume', type=Path, help='Optional private plain-text resume')
    generate.add_argument('--output', type=Path, default=DATA / 'bytedance_actionable.csv')
    update = sub.add_parser('review', help='Record human checks; does not apply for a job')
    update.add_argument('job_id', help='BD-<numeric position ID>')
    update.add_argument('--reviews', type=Path, default=REVIEW_PATH)
    update.add_argument('--opening', choices=['open', 'closed', 'unverified'])
    update.add_argument('--eligibility', choices=['yes', 'no', 'unverified'])
    update.add_argument('--review', choices=['pending', 'approved', 'rejected'])
    update.add_argument('--application', choices=['not_applied', 'applied', 'assessment', 'interview', 'offer', 'rejected'])
    update.add_argument('--opening-evidence', default='', help='Verbatim quote showing job is open or closed')
    update.add_argument('--eligibility-evidence', default='', help='Verbatim quote showing 2027 eligibility')
    args = parser.parse_args()
    if args.command == 'build':
        resume = args.resume.read_text(encoding='utf-8') if args.resume else ''
        rows = build(read_csv(args.filtered), read_csv(args.verified), args.details,
                     read_reviews(args.reviews), resume)
        save_csv(args.output, rows)
        print(f'{len(rows)} jobs saved to {args.output}; {sum(r["recommendation"] == "verify_first" for r in rows)} require verification')
    else:
        if not any((args.opening, args.eligibility, args.review, args.application)):
            parser.error('Specify at least one status field')
        known_ids = {job_id(r['source_url']) for r in read_csv(DATA / 'bytedance_filtered_jobs.csv')
                     if r.get('source_url')}
        if args.job_id not in known_ids:
            parser.error('job_id is absent from the filtered ByteDance jobs CSV')
        reviews = read_reviews(args.reviews)
        set_review(reviews, args.job_id, args.opening, args.eligibility,
                   args.review, args.application, args.opening_evidence,
                   args.eligibility_evidence)
        write_reviews(args.reviews, reviews)
        print(f'Review saved for {args.job_id}')


if __name__ == '__main__':
    main()
