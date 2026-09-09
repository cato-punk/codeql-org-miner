import json
from typing import List
from miner.models import Finding

def parse_sarif(sarif_path: str) -> List[Finding]:
    findings = []
    
    try:
        with open(sarif_path, "r", encoding="utf-8") as f:
            sarif_data = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return []

    for run in sarif_data.get("runs", []):
        rules = {}
        #severidades + adelante
        driver = run.get("tool", {}).get("driver", {})
        for rule in driver.get("rules", []):
            rules[rule["id"]] = rule.get("defaultConfiguration", {}).get("level", "warning")

        for result in run.get("results", []):
            rule_id = result.get("ruleId", "unknown")
            message = result.get("message", {}).get("text", "Sin descripción")
            severity = rules.get(rule_id, "warning")

            for location in result.get("locations", []):
                phys_loc = location.get("physicalLocation", {})
                file_path = phys_loc.get("artifactLocation", {}).get("uri", "unknown")
                start_line = phys_loc.get("region", {}).get("startLine", 1)

                findings.append(Finding(
                    rule_id=rule_id,
                    severity=severity,
                    message=message,
                    file=file_path,
                    start_line=start_line
                ))

    return findings