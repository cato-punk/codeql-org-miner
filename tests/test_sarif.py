import json
from miner.sarif import parse_sarif

def test_parse_sarif(tmp_path):
    sarif_data = {
        "runs": [{
            "tool": {
                "driver": {
                    "rules": [{"id": "py/unused-import", "defaultConfiguration": {"level": "note"}}]
                }
            },
            "results": [{
                "ruleId": "py/unused-import",
                "message": {"text": "Unused import statement"},
                "locations": [{
                    "physicalLocation": {
                        "artifactLocation": {"uri": "src/main.py"},
                        "region": {"startLine": 10}
                    }
                }]
            }]
        }]
    }

    file_path = tmp_path / "sample.sarif"
    file_path.write_text(json.dumps(sarif_data))

    findings = parse_sarif(str(file_path))
    assert len(findings) == 1
    assert findings[0].rule_id == "py/unused-import"
    assert findings[0].file == "src/main.py"
    assert findings[0].start_line == 10