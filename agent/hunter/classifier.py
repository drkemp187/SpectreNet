import logging
import os
import re
from dataclasses import dataclass

log = logging.getLogger("spectre.hunter.classifier")


@dataclass
class Classification:
    intent: str
    confidence: float
    tool: str
    ttp: str
    summary: str


SIGNATURES = {
    "nmap": r"(nmap|Nmap|NMAP|masscan|zmap)",
    "sqlmap": r"(sqlmap|SQLMAP|sql injection|union select|sleep\(|pg_sleep)",
    "burp": r"(burp|BurpSuite|Burp|repeater|intruder)",
    "nessus": r"(nessus|Nessus|openvas|qualys)",
    "metasploit": r"(metasploit|msf|meterpreter|payload|reverse_tcp)",
    "dirbuster": r"(dirbuster|gobuster|ffuf|dirb|wfuzz)",
    "shodan": r"(shodan|Shodan|shodan\.io)",
    "bot": r"(bot|crawler|scrapy|curl|python-requests|go-http-client)",
    "exploitdb": r"(exploit|CVE-\d{4}-\d{4,})",
}


class Classifier:
    def __init__(self):
        self.endpoint = os.getenv("LLM_ENDPOINT")
        self.model = os.getenv("LLM_MODEL", "local-model")

    async def classify(self, event) -> Classification:
        matched_tools = []
        for tool, pattern in SIGNATURES.items():
            text = f"{event.method} {event.path} {str(event.headers)} {event.body or ''}"
            if re.search(pattern, text, re.IGNORECASE):
                matched_tools.append(tool)

        if matched_tools:
            return Classification(
                intent="malicious",
                confidence=0.8,
                tool=matched_tools[0],
                ttp="T1595" if matched_tools[0] in ("nmap", "masscan") else "T1190",
                summary=f"Detected {matched_tools[0]} scanning activity",
            )

        if event.path in ("/admin", "/wp-admin", "/.env", "/config", "/api"):
            return Classification(
                intent="suspicious",
                confidence=0.6,
                tool="manual",
                ttp="T1595",
                summary=f"Probed sensitive path: {event.path}",
            )

        if event.method == "POST" and "/login" in event.path:
            return Classification(
                intent="suspicious",
                confidence=0.5,
                tool="manual",
                ttp="T1110",
                summary="Login brute-force attempt",
            )

        return Classification(
            intent="benign",
            confidence=0.3,
            tool="unknown",
            ttp="N/A",
            summary="Unclassified traffic",
        )
