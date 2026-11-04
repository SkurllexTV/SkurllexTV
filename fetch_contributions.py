import json
import os
import sys
import urllib.request
from pathlib import Path

QUERY = """query($login:String!){user(login:$login){contributionsCollection{contributionCalendar{
totalContributions weeks{contributionDays{date contributionCount}}}}}}"""


def main() -> None:
    token = os.environ.get("GH_TOKEN")
    login = os.environ.get("GH_USER")
    if not token or not login:
        sys.exit("GH_TOKEN and GH_USER must be set")
    req = urllib.request.Request(
        "https://api.github.com/graphql",
        data=json.dumps({"query": QUERY, "variables": {"login": login}}).encode(),
        headers={"Authorization": f"bearer {token}", "Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=30) as res:
        payload = json.load(res)
    if "errors" in payload:
        sys.exit(f"GraphQL error: {payload['errors']}")
    cal = payload["data"]["user"]["contributionsCollection"]["contributionCalendar"]
    weeks = [[{"date": d["date"], "count": d["contributionCount"]} for d in w["contributionDays"]] for w in cal["weeks"]]
    out = Path(__file__).resolve().parent / "data" / "contributions.json"
    out.parent.mkdir(exist_ok=True)
    out.write_text(json.dumps({"total": cal["totalContributions"], "weeks": weeks}), encoding="utf-8")


if __name__ == "__main__":
    main()
