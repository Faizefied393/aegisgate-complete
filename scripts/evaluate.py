"""Deterministic security regression/evaluation: 25 scenarios, no API calls."""
import json
import os
import tempfile
from app.gateway import execute
from app.security import Principal, Denied

SCENARIOS = []
for user,role in [("bob","employee"),("alice","analyst"),("carol","admin")]:
    for tool,resource in [("search_events","security_events"),("read_document","it_policy"),("read_document","soc_runbook"),("read_document","executive_report"),("read_document","injection_sample"),("create_ticket","incident_tickets"),("run_shell","host"),("read_document","unknown"),("create_ticket","executive_report")]:
        expected = (role in {"analyst","admin"} if tool=="search_events" else role in {"analyst","admin"} if tool=="create_ticket" and resource=="incident_tickets" else role in {"employee","analyst","admin"} if tool=="read_document" and resource=="it_policy" else role in {"analyst","admin"} if tool=="read_document" and resource in {"soc_runbook","injection_sample"} else role=="admin" if tool=="read_document" and resource=="executive_report" else False)
        SCENARIOS.append((Principal(user,role),tool,resource,expected))

def main():
    with tempfile.TemporaryDirectory() as tmp:
        os.environ["AEGIS_DB"] = os.path.join(tmp,"eval.db")
        passed=0
        results=[]
        for principal,tool,resource,expected in SCENARIOS:
            try:
                execute(principal,tool,resource,{"title":"Synthetic test ticket"})
                actual=True
            except Denied:
                actual=False
            ok=expected==actual
            passed += ok
            results.append({"user":principal.user,"tool":tool,"resource":resource,"expected_allow":expected,"actual_allow":actual,"passed":ok})
        report={"total":len(results),"passed":passed,"failed":len(results)-passed,"scope":"Deterministic gateway evaluation only; NOT LLM prompt injection ASR", "results":results}
        print(json.dumps({k:v for k,v in report.items() if k!="results"},indent=2))
        if passed != len(results):
            raise SystemExit(1)
if __name__=="__main__":
    main()
