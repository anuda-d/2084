"""Structured worker results and persisted verification contracts."""

from .evidence import validate_reference
import re


WORK_SCHEMA = {
    "type": "object", "additionalProperties": False,
    "properties": {
        "outcome": {"type": "string", "enum": ["change_ready", "goal_complete", "blocked", "checkpoint"]},
        "summary": {"type": "string"}, "evidence": {"type": "string"},
        "remaining": {"type": "string"}, "commit_message": {"type": "string"},
        "review_required": {"type": "boolean"}, "review_reason": {"type": "string"},
        "review_scope": {"type":"string", "enum":["change", "goal"]},
        "artifacts": {"type":"array", "items": {
            "type":"object", "additionalProperties":False,
            "properties":{"id":{"type":"string"}, "path":{"type":"string"},
                          "classification":{"type":"string", "enum":["supporting", "contrary"]}},
            "required":["id", "path", "classification"]}},
    },
    "required": ["outcome", "summary", "evidence", "remaining", "commit_message", "review_required", "review_reason", "review_scope", "artifacts"],
}
REVIEW_SCHEMA = {
    "type": "object", "additionalProperties": False,
    "properties": {"verdict": {"type": "string", "enum": ["pass", "repair"]}, "findings": {"type": "string"},
                   "goal_criteria_verified":{"type":"boolean"}, "completion_only":{"type":"boolean"}},
    "required": ["verdict", "findings", "goal_criteria_verified", "completion_only"],
}


def validate_result(value: object, schema: dict) -> dict:
    if not isinstance(value, dict) or set(value) != set(schema["required"]):
        raise ValueError("Agent result is missing fields or has unexpected fields")
    for name, rule in schema["properties"].items():
        expected = {"boolean":bool, "string":str, "array":list}[rule["type"]]
        if not isinstance(value[name], expected) or ("enum" in rule and value[name] not in rule["enum"]):
            raise ValueError(f"Invalid agent result field: {name}")
        if name == "artifacts":
            for reference in value[name]:
                validate_reference(reference)
    return value


def validate_verification_state(data):
    """Old state has no receipts; malformed new receipts never imply acceptance."""
    def digest(value, size):
        return isinstance(value, str) and re.fullmatch(r"[0-9a-f]{" + str(size) + "}", value)

    def key(value):
        if (not isinstance(value, dict) or set(value) != {"tree", "identity", "evidence"}
                or not digest(value["tree"], 40) or not digest(value["identity"], 64)
                or not isinstance(value["evidence"], dict)):
            raise ValueError("Invalid persisted verification key")

    def review(value):
        if (not isinstance(value, dict) or value.get("scope") not in {"change", "goal"}
                or value.get("requested_scope") not in {"change", "goal", "completion_correction"}):
            raise ValueError("Invalid persisted review scope")
        key(value.get("key"))
        validate_result(value.get("result"), REVIEW_SCHEMA)

    receipt = data.get("verification")
    if receipt is not None:
        if not isinstance(receipt, dict):
            raise ValueError("Invalid persisted verification")
        key(receipt.get("key"))
        if not isinstance(receipt.get("checks"), list):
            raise ValueError("Invalid persisted check results")
        for check in receipt["checks"]:
            if (not isinstance(check, dict) or type(check.get("exit_code")) is not int
                    or check["exit_code"] != 0 or not isinstance(check.get("command"), list)
                    or not check["command"] or not all(isinstance(v, str) for v in check["command"])
                    or not isinstance(check.get("log"), str)):
                raise ValueError("Invalid persisted passed check")
        if receipt.get("review") is not None:
            review(receipt["review"])
            if receipt["review"]["key"] != receipt["key"]:
                raise ValueError("Review does not match verification key")
    coverage = data.get("goal_review")
    if coverage is not None:
        review(coverage)
        decision = coverage["result"]
        if (coverage["scope"] != "goal" or not decision["goal_criteria_verified"]
                or (decision["verdict"] != "pass" and not decision["completion_only"])):
            raise ValueError("Invalid persisted goal coverage")
    if data.get("review_obligation") is not None:
        review(data["review_obligation"])
    artifacts = data.get("artifacts", {})
    if not isinstance(artifacts, dict):
        raise ValueError("Invalid persisted evidence registry")
    for goal, records in artifacts.items():
        if not digest(goal, 64) or not isinstance(records, dict):
            raise ValueError("Invalid persisted evidence goal")
        for identifier, record in records.items():
            if not isinstance(record, dict) or record.get("id") != identifier:
                raise ValueError("Invalid persisted evidence record")
            validate_reference({k:record.get(k) for k in ("id", "path", "classification")})
            if record.get("historical_missing") is True:
                continue
            if (not digest(record.get("manifest_sha256"), 64)
                    or any(type(record.get(k)) is not int for k in ("device", "inode"))
                    or not isinstance(record.get("verification"), dict)
                    or type(record["verification"].get("passed")) is not bool):
                raise ValueError("Invalid persisted evidence measurement")
