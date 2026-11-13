"""Convert a small sample of a public resume dataset into real_profiles.json.
Uses ONLY each resume's job category and a few skill keywords, never names or
contact details, pseudonymized P1..Pn. No scraping: the CSV is downloaded by hand.
    python build_real_profiles.py Resume.csv 5"""
import json, sys
import pandas as pd
CSV = sys.argv[1] if len(sys.argv) > 1 else "Resume.csv"
N = int(sys.argv[2]) if len(sys.argv) > 2 else 5
CAT_TO_ROLE = {
    "INFORMATION-TECHNOLOGY":"Software Engineer","ENGINEERING":"Software Engineer",
    "HR":"HR Coordinator","FINANCE":"Finance Director","BANKING":"Finance Director",
    "ACCOUNTANT":"Accounts Payable Specialist","BUSINESS-DEVELOPMENT":"Marketing Manager",
    "SALES":"Marketing Manager","DIGITAL-MEDIA":"Marketing Manager",
    "CONSULTANT":"Procurement Analyst","DESIGNER":"Marketing Manager"}
DEFAULT_ROLE = "Research Assistant"
CAT_TO_INDUSTRY = {
    "INFORMATION-TECHNOLOGY":"SaaS","ENGINEERING":"Manufacturing","HR":"Higher Education",
    "FINANCE":"Fintech","BANKING":"Fintech","ACCOUNTANT":"Fintech",
    "BUSINESS-DEVELOPMENT":"Retail","SALES":"Retail","DIGITAL-MEDIA":"Retail","HEALTHCARE":"Healthcare"}
SKILLS = ["python","sql","excel","machine learning","java","marketing","accounting",
          "leadership","project management","data analysis","cloud","communication",
          "design","sales","finance","recruiting"]
def interests_from(text):
    t = str(text).lower()
    return [s for s in SKILLS if s in t][:3] or ["professional development"]
df = pd.read_csv(CSV)
seen_roles, rows = set(), []
for _, r in df.iterrows():
    cat = str(r.get("Category","")).strip().upper()
    role = CAT_TO_ROLE.get(cat, DEFAULT_ROLE)
    if role not in seen_roles:
        seen_roles.add(role); rows.append(r)
    if len(rows) >= N: break
out = []
for i, r in enumerate(rows, 1):
    cat = str(r.get("Category","")).strip().upper()
    out.append({"code":f"P{i}","role":CAT_TO_ROLE.get(cat,DEFAULT_ROLE),
        "organization":"a company (from public resume dataset)",
        "industry":CAT_TO_INDUSTRY.get(cat,"Higher Education"),
        "interests":interests_from(r.get("Resume_str","")),
        "recent_activity":[f"public resume in the {cat.title()} field"],
        "relationships":["professional contacts in the same field"],
        "present_on":["email","linkedin"]})
json.dump(out, open("real_profiles.json","w"), indent=2)
print(f"wrote {len(out)} profiles to real_profiles.json from {CSV}")
