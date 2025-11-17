#!/usr/bin/env python3
"""
Validation Summary Generator

GitHub Actions에서 전체 검증 결과를 요약하는 스크립트.
"""

import json
from pathlib import Path
from datetime import datetime


def load_validation_results():
    """모든 검증 결과 파일 로드"""

    validation_dir = Path('.validation')

    if not validation_dir.exists():
        return {}

    results = {}
    weeks = ['1-2', '4', '5', '7-8', '9']

    for week in weeks:
        result_file = validation_dir / f'week-{week}-result.json'

        if result_file.exists():
            with open(result_file, 'r', encoding='utf-8') as f:
                results[week] = json.load(f)

    return results


def generate_markdown_summary(results):
    """Markdown 형식 요약 생성"""

    md = "# POKER-BRAIN Validation Summary\n\n"
    md += f"**Generated**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"

    md += "## Overall Status\n\n"

    total = len(results)
    passed = sum(1 for r in results.values() if r.get('passed'))

    pass_rate = (passed / total * 100) if total > 0 else 0

    md += f"- **Total Weeks**: {total}\n"
    md += f"- **Passed**: {passed}\n"
    md += f"- **Failed**: {total - passed}\n"
    md += f"- **Pass Rate**: {pass_rate:.1f}%\n\n"

    # Overall status emoji
    if pass_rate == 100:
        md += "## ✅ All Validations Passed!\n\n"
    elif pass_rate >= 80:
        md += "## ⚠️ Most Validations Passed\n\n"
    else:
        md += "## ❌ Multiple Validation Failures\n\n"

    # Week-by-week results
    md += "## Week-by-Week Results\n\n"

    week_names = {
        '1-2': 'Week 1-2: API Design + Mock Environment',
        '4': 'Week 4: M1 Data Ingestion Complete',
        '5': 'Week 5: M2 Complete + Mock → Real Transition',
        '7-8': 'Week 7-8: E2E Tests (80% → 100%)',
        '9': 'Week 9: Production Deployment',
    }

    for week, result in sorted(results.items()):
        week_name = week_names.get(week, f'Week {week}')
        status = "✅ Passed" if result.get('passed') else "❌ Failed"

        md += f"### {week_name}\n\n"
        md += f"**Status**: {status}\n"
        md += f"**Timestamp**: {result.get('timestamp', 'N/A')}\n"

        if not result.get('passed') and result.get('error'):
            md += f"\n**Error**:\n```\n{result['error']}\n```\n"

        md += "\n"

    # Failed validations detail
    failed = [week for week, r in results.items() if not r.get('passed')]

    if failed:
        md += "## ⚠️ Failed Validations\n\n"

        for week in failed:
            result = results[week]
            week_name = week_names.get(week, f'Week {week}')

            md += f"### {week_name}\n\n"
            md += f"**Error**: {result.get('error', 'Unknown error')}\n\n"

            # Action items
            if week == '1-2':
                md += "**Action Items**:\n"
                md += "- Check OpenAPI spec files\n"
                md += "- Verify Mock BigQuery tables\n"
                md += "- Ensure Pub/Sub Emulator is running\n"
                md += "- Verify Prism Mock Servers\n\n"

            elif week == '4':
                md += "**Action Items**:\n"
                md += "- Check M1 Dataflow pipeline\n"
                md += "- Verify BigQuery data insertion\n"
                md += "- Test M1 Cloud Run deployment\n"
                md += "- Ensure M3, M4 can read M1 data\n\n"

            elif week == '5':
                md += "**Action Items**:\n"
                md += "- Verify environment variables (POKER_ENV=production)\n"
                md += "- Test Real BigQuery access\n"
                md += "- Check Pub/Sub Topic creation\n"
                md += "- Verify M6 API endpoints\n\n"

            elif week == '7-8':
                md += "**Action Items**:\n"
                md += "- Review E2E test failures\n"
                md += "- Fix bugs from Week 7\n"
                md += "- Re-run Playwright tests\n"
                md += "- Check performance metrics\n\n"

            elif week == '9':
                md += "**Action Items**:\n"
                md += "- Check Production deployment logs\n"
                md += "- Verify SSL certificates\n"
                md += "- Test Production E2E scenarios\n"
                md += "- Review rollback logs (if applicable)\n\n"

    # Next steps
    md += "## Next Steps\n\n"

    if pass_rate == 100:
        md += "🎉 All validations passed! Project is ready for production.\n\n"
        md += "- [ ] Schedule launch party\n"
        md += "- [ ] Prepare user onboarding materials\n"
        md += "- [ ] Monitor production metrics\n"
    else:
        next_week = None

        for week in ['1-2', '4', '5', '7-8', '9']:
            if week not in results or not results[week].get('passed'):
                next_week = week
                break

        if next_week:
            md += f"Focus on fixing **Week {next_week}** validation issues.\n\n"
            md += "- [ ] Review error logs\n"
            md += "- [ ] Apply fixes\n"
            md += "- [ ] Re-run validation\n"

    return md


def main():
    # 검증 결과 로드
    results = load_validation_results()

    if not results:
        print("⚠️ No validation results found.")
        return

    # Markdown 요약 생성
    summary_md = generate_markdown_summary(results)

    # 파일 저장
    summary_file = Path('.validation/summary.md')
    summary_file.parent.mkdir(exist_ok=True)

    with open(summary_file, 'w', encoding='utf-8') as f:
        f.write(summary_md)

    print(f"✅ Validation summary generated: {summary_file}")

    # 콘솔 출력
    print("\n" + summary_md)


if __name__ == '__main__':
    main()
