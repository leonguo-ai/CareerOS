"""Compatibility entry point: build the evidence-based shortlist using a local resume."""
from pathlib import Path
from bytedance_workflow import DATA, REVIEW_PATH, build, read_csv, read_reviews, save_csv


def main():
    resume_path = Path('resumes/master_resume.txt')
    if not resume_path.is_file():
        raise SystemExit('Missing private resume: resumes/master_resume.txt')
    rows = build(read_csv(DATA / 'bytedance_filtered_jobs.csv'),
                 read_csv(DATA / 'bytedance_verified_jobs.csv'),
                 DATA / 'bytedance_job_details', read_reviews(REVIEW_PATH),
                 resume_path.read_text(encoding='utf-8'))
    output = DATA / 'bytedance_actionable.csv'
    save_csv(output, rows)
    print(f'{len(rows)} jobs saved to {output}; manual verification is still required')


if __name__ == '__main__':
    main()
