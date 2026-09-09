import typer
from pathlib import Path
from rich.console import Console
from miner.github import GitHubClient
from miner.codeql import process_repository
from miner.models import OrganizationReport, RepositoryResult, Summary, AnalysisStatus

# Se crea la aplicación principal de Typer
app = typer.Typer(
    help="Minero de seguridad con CodeQL para organizaciones de GitHub.",
    no_args_is_help=True
)

@app.command(name="scan")
def scan(
    organization: str = typer.Option(..., "--organization", "-o", help="Nombre de la organización de GitHub"),
    output: Path = typer.Option(Path("results.json"), "--output", "-out", help="Archivo JSON de salida"),
    max_repos: int = typer.Option(5, "--max-repos", "-m", help="Límite máximo de repositorios a analizar")
):
    """
    Escanea los repositorios de una organización de GitHub usando CodeQL.
    """
    console = Console()
    console.print(f"[bold blue]Iniciando minería para la organización:[/bold blue] {organization}")
    
    try:
        gh_client = GitHubClient()
        repos = gh_client.get_org_repositories(organization, max_repos=max_repos)
    except Exception as e:
        console.print(f"[bold red]Error al conectar con GitHub:[/bold red] {e}")
        raise typer.Exit(code=1)

    console.print(f"Se encontraron [green]{len(repos)}[/green] repositorios (límite máximo: {max_repos}).")

    work_dir = Path("workspace")
    work_dir.mkdir(exist_ok=True)

    repo_results = []
    
    for repo_data in repos:
        name = repo_data["name"]
        clone_url = repo_data["clone_url"]
        html_url = repo_data["html_url"]

        console.print(f"\n[yellow]Procesando repo:[/yellow] {name}...")

        status, langs, findings, error = process_repository(clone_url, name, work_dir)

        if status == AnalysisStatus.ANALYZED:
            console.print(f"  └─ [green]Analizado con éxito.[/green] Hallazgos: {len(findings)}")
        else:
            console.print(f"  └─ [red]Estado: {status.value}.[/red] Razón: {error}")

        repo_results.append(RepositoryResult(
            name=name,
            url=html_url,
            status=status,
            error_reason=error,
            languages=langs,
            findings=findings
        ))

    summary = Summary(
        repositories=len(repo_results),
        analyzed=sum(1 for r in repo_results if r.status == AnalysisStatus.ANALYZED),
        failed=sum(1 for r in repo_results if r.status in [AnalysisStatus.FAILED_CLONE, AnalysisStatus.FAILED_DB_CREATE, AnalysisStatus.FAILED_ANALYSIS]),
        unsupported=sum(1 for r in repo_results if r.status == AnalysisStatus.UNSUPPORTED_LANGUAGE),
        findings=sum(len(r.findings) for r in repo_results)
    )

    report = OrganizationReport(
        organization=organization,
        summary=summary,
        repositories=repo_results
    )

    report.sort_results()

    with open(output, "w", encoding="utf-8") as f:
        f.write(report.model_dump_json(indent=2))

    console.print(f"\n[bold green]Análisis completado.[/bold green] Resultados guardados en: {output}")

if __name__ == "__main__":
    app()