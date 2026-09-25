import sys
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from bytedance_workflow import build, read_reviews, set_review, write_reviews
from job_identity import job_id

URL = 'https://jobs.bytedance.com/campus/position/12345/detail'
NOW = datetime(2026, 9, 25, tzinfo=timezone.utc)


class ByteDanceWorkflowTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.detail_dir = Path(self.temp.name)
        (self.detail_dir / 'BD-12345.txt').write_text(
            '岗位要求：使用 Python 和 SQL 进行数据分析。\n2027届毕业生。', encoding='utf-8')
        self.filtered = [{'source_url': URL, 'company': '字节跳动',
                          'raw_job_title': '数据分析实习生', 'relevance_score': '80'}]
        self.verified = [{'source_url': URL, 'job_title': '数据分析实习生',
                          'page_status': 'reachable', 'verified_at': NOW.isoformat()}]

    def run_build(self, reviews, resume='使用 Python 和 SQL 做数据分析。', now=NOW):
        return build(self.filtered, self.verified, self.detail_dir, reviews,
                     resume, now=now)[0]

    def test_identity_survives_title_and_order_and_ignores_tracking(self):
        other = URL.replace('12345', '99999')
        self.assertEqual(job_id(URL), job_id(URL + '?utm_source=email#top'))
        rows = build(self.filtered + [{'source_url': other, 'raw_job_title': '其他'}],
                     self.verified, self.detail_dir, {}, now=NOW)
        self.assertEqual({r['job_id'] for r in rows}, {'BD-12345', 'BD-99999'})
        self.assertEqual(self.run_build({})['detail_path'], str(self.detail_dir / 'BD-12345.txt'))

    def test_high_match_without_manual_checks_cannot_advance(self):
        row = self.run_build({})
        self.assertEqual(row['recommendation'], 'verify_first')
        self.assertEqual(row['opening_status'], 'unverified')
        self.assertEqual(row['eligibility_2027'], 'unverified')
        self.assertIn('岗位要求：', row['requirements_evidence'])
        self.assertIn('evidence_found', row['resume_evidence'])
        self.assertEqual(row['match_score'], '100.0')

    def test_independent_evidence_review_persists_and_expires(self):
        reviews = {}
        with self.assertRaises(ValueError):
            set_review(reviews, 'BD-12345', opening='open', now=NOW)
        set_review(reviews, 'BD-12345', opening='open', eligibility='yes',
                   opening_evidence='仍在招聘', eligibility_evidence='2027届', now=NOW)
        set_review(reviews, 'BD-12345', review='approved', application='applied', now=NOW)
        path = self.detail_dir / 'reviews.json'
        write_reviews(path, reviews)
        reloaded = read_reviews(path)
        row = self.run_build(reloaded)
        self.assertEqual(row['recommendation'], 'manually_approved')
        self.assertEqual(row['application_status'], 'applied')
        self.assertEqual(self.run_build(reloaded, now=NOW + timedelta(days=8))['recommendation'],
                         'verify_first')
        self.assertEqual(self.run_build(reloaded, now=NOW + timedelta(days=8))['opening_status'],
                         'unverified')

    def test_missing_details_or_failed_page_holds_even_when_approved(self):
        reviews = {}
        set_review(reviews, 'BD-12345', opening='open', eligibility='yes',
                   opening_evidence='仍在招聘', eligibility_evidence='2027届',
                   review='approved', now=NOW)
        self.verified[0]['page_status'] = 'http_error'
        self.assertEqual(self.run_build(reviews)['recommendation'], 'verify_first')
        self.verified[0]['page_status'] = 'reachable'
        (self.detail_dir / 'BD-12345.txt').unlink()
        row = self.run_build(reviews)
        self.assertEqual(row['recommendation'], 'verify_first')
        self.assertEqual(row['match_score'], '')

    def test_missing_resume_evidence_is_explicit(self):
        row = self.run_build({}, resume='无关联技能。')
        self.assertIn('not_found', row['resume_evidence'])
        self.assertEqual(row['match_score'], '0.0')

    def test_no_resume_does_not_claim_evidence_is_missing(self):
        row = self.run_build({}, resume='')
        self.assertIn('not_checked', row['resume_evidence'])
        self.assertEqual(row['match_score'], '')

    def test_stale_historical_page_cannot_be_promoted(self):
        reviews = {}
        set_review(reviews, 'BD-12345', opening='open', eligibility='yes',
                   opening_evidence='仍在招聘', eligibility_evidence='2027届', now=NOW)
        self.verified[0]['verified_at'] = '2026-07-20T22:50:56'
        row = self.run_build(reviews)
        self.assertEqual(row['page_status'], 'unverified')
        self.assertEqual(row['recommendation'], 'verify_first')


if __name__ == '__main__':
    unittest.main()
