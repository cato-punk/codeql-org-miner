import subprocess
import shutil
from pathlib import Path
from typing import Tuple, Optional, List
from miner.models import AnalysisStatus, Finding
from miner.sarif import parse_sarif

CODEQL_LANG_MAP = {
    ".py": "python",
    ".js": "javascript",
    ".ts": "javascript",
    ".java": "java",
    ".go": "go",
    ".cpp": "cpp",
    ".c": "cpp",
    ".cs": "csharp"
}

def detect_languages(repo_dir: Path) -> List[str]:
    detected = set()
    for file in repo_dir.rglob("*"):
        if file.is_file() and file.suffix in CODEQL_LANG_MAP:
            detected.add(CODEQL_LANG_MAP[file.suffix])
    return list(detected)

def process_repository(clone_url: str, repo_name: str, work_dir: Path) -> Tuple[AnalysisStatus, List[str], List[Finding], Optional[str]]:
    repo_dir = work_dir / repo_name
    db_dir = work_dir / f"{repo_name}-db"
    sarif_file = work_dir / f"{repo_name}-results.sarif"

    # 1. Clonar
    try:
        subprocess.run(["git", "clone", "--depth", "1", clone_url, str(repo_dir)], check=True, capture_output=True)
    except subprocess.CalledProcessError as e:
        return AnalysisStatus.FAILED_CLONE, [], [], f"Error al clonar: {e.stderr.decode()}"

    # 2. detectar lenguaje
    languages = detect_languages(repo_dir)
    if not languages:
        shutil.rmtree(repo_dir, ignore_errors=True)
        return AnalysisStatus.UNSUPPORTED_LANGUAGE, [], [], "Sin lenguajes soportados por CodeQL"

    target_lang = languages[0]

    # 3. crear la bd con CodeQL
    try:
        cmd_db = ["codeql", "database", "create", str(db_dir), f"--language={target_lang}", f"--source-root={repo_dir}"]
        subprocess.run(cmd_db, check=True, capture_output=True)
    except subprocess.CalledProcessError as e:
        shutil.rmtree(repo_dir, ignore_errors=True)
        return AnalysisStatus.FAILED_DB_CREATE, languages, [], f"Falló db create: {e.stderr.decode()}"

    # 4. analisis con CodeQL
    try:
        cmd_analyze = ["codeql", "database", "analyze", str(db_dir), "--format=sarif-latest", f"--output={sarif_file}"]
        subprocess.run(cmd_analyze, check=True, capture_output=True)
    except subprocess.CalledProcessError as e:
        shutil.rmtree(repo_dir, ignore_errors=True)
        shutil.rmtree(db_dir, ignore_errors=True)
        return AnalysisStatus.FAILED_ANALYSIS, languages, [], f"Falló db analyze: {e.stderr.decode()}"

    # 5. Parseo de SARIF
    findings = parse_sarif(str(sarif_file))

    # Limpieza temporal del repositorio y la BD
    shutil.rmtree(repo_dir, ignore_errors=True)
    shutil.rmtree(db_dir, ignore_errors=True)

    return AnalysisStatus.ANALYZED, languages, findings, None