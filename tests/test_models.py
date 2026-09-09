from miner.models import OrganizationReport, RepositoryResult, Finding, Summary, AnalysisStatus

def test_reproducible_sorting():
    repo = RepositoryResult(
        name="b-repo",
        url="http://example.com",
        status=AnalysisStatus.ANALYZED,
        findings=[
            Finding(rule_id="r2", severity="high", message="m2", file="b.py", start_line=10),
            Finding(rule_id="r1", severity="low", message="m1", file="a.py", start_line=5)
        ]
    )

    report = OrganizationReport(
        organization="test-org",
        summary=Summary(repositories=1, analyzed=1, failed=0, unsupported=0, findings=2),
        repositories=[repo]
    )

    report.sort_results()
    assert repo.findings[0].file == "a.py"