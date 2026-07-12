"""
# ================================
# USER PROFILE
# ================================

USER_PROFILE = {

    "target_titles": [
        "Instrumentation Engineer",
        "Senior Instrumentation Engineer",
        "Lead Instrumentation Engineer",
        "I&C Engineer",
        "Control Engineer",
        "Automation Engineer",
        "Process Control Engineer",
        "PLC Engineer",
        "DCS Engineer",
        "SCADA Engineer",
    ],

    "industries": [
        "Oil & Gas",
        "Petrochemical",
        "Refinery",
        "Gas Compressor Station",
        "Power Plant",
        "Energy",
    ],

    "systems": [
        "PCS7",
        "TIA Portal",
        "STEP7",
        "WinCC",
        "Honeywell",
        "Experion",
        "Emerson",
        "DeltaV",
        "ABB",
        "800xA",
        "Yokogawa",
        "CENTUM",
        "Foxboro",
        "Schneider",
        "Rockwell",
    ],

    "keywords": [
        "Instrumentation",
        "Control",
        "PLC",
        "SCADA",
        "DCS",
        "SIS",
        "ESD",
        "Commissioning",
        "Loop Check",
        "FAT",
        "SAT",
        "FEED",
        "Detailed Engineering",
    ]
}

INDEED_QUERIES = [
    "Instrumentation Engineer",
    "Instrument Engineer",
    "I&C Engineer",
    "Automation Engineer",
    "Control Systems Engineer",
    "PLC Engineer",
    "DCS Engineer",
    "SCADA Engineer",
    "Commissioning Engineer",
    "Electrical Instrumentation Engineer",
]

MATCH_WEIGHTS = {
    "title": 35,
    "industry": 20,
    "systems": 15,
    "skills": 15,
    "company": 10,
    "location": 5,
}
#شرکت های هدف
PREFERRED_COMPANIES = [
    "Siemens",
    "ABB",
    "Emerson",
    "Honeywell",
    "Yokogawa",
    "Schneider",
    "Wood",
    "Technip",
    "SLB",
    "Baker Hughes",
    "Fluor",
    "Bechtel",
    "Saipem",
    "Petrofac",
    "Shell",
    "BP",
    "TotalEnergies",
    "Equinor",
]
#کشورهای هدف
TARGET_COUNTRIES = {
    "Netherlands",
    "Germany",
    "Denmark",
    "Norway",
    "Sweden",
    "Belgium",
    "Finland",
    "Turkey",
    "Poland",
}

GREENHOUSE_TITLE_KEYWORDS = [
    "instrument",
    "automation",
    "controls",
    "control",
    "plc",
    "scada",
    "dcs",
    "electrical",
    "commissioning",
    "process",
]

I&C Job Scraper Bot v5.0
========================
منابع رایگان:
  • Remotive.com
  • Jobicy.com
  • Arbeitnow
  • Adzuna (با API key)
  • FindWork.dev
  • Cloudflare Worker
  • Linkedin

  https://remotive.com/
  https://www.arbeitnow.com/
  https://jobicy.com/
  https://developer.adzuna.com/
  https://remotejobs.org/
  https://findwork.dev

منابع پولی (اختیاری):
  • JSearch via RapidAPI  — پلن رایگان 200 req/ماه

Cover Letter:
  • هر آگهی یک دکمه "ChatGPT Cover Letter" داره
  • کلیک → باز شدن ChatGPT با پرامپت آماده

ذخیره‌سازی اختیاری:
  • Google Sheets (Batch append)

متغیرهای محیطی (GitHub Secrets):
  TELEGRAM_BOT_TOKEN   — اجباری
  TELEGRAM_CHAT_ID     — اجباری
  RAPIDAPI_KEY         — اختیاری
  GSHEET_CREDENTIALS   — اختیاری (JSON)
  GSHEET_ID            — اختیاری
  CF_WORKER_URL        — اختیاری
  ADZUNA_APP_ID        — اختیاری
  ADZUNA_API_KEY       — اختیاری
"""
import hashlib
import html
import feedparser    #new
import urllib.parse    #new
import json
import logging
import os
import re
import time
import traceback
import urllib.parse
#import pprint  #جدید
from collections import OrderedDict
from datetime import datetime, timezone
from pathlib import Path

import requests
from dotenv import load_dotenv

try:
    import gspread
    from google.oauth2.service_account import Credentials
    SHEETS_AVAILABLE = True
except ImportError:
    SHEETS_AVAILABLE = False

SCRIPT_DIR = Path(__file__).parent

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    handlers=[logging.StreamHandler()],
)
log = logging.getLogger(__name__)

def safe_fetch(source_name: str, fetch_function):
    """
    Execute a job source safely without stopping the whole bot.
    """
    try:
        log.info("Fetching jobs from %s ...", source_name)

        jobs = fetch_function()

        log.info(
            "%s completed successfully (%d jobs found).",
            source_name,
            len(jobs),
        )

        return jobs

    except Exception:
        log.exception("%s failed.", source_name)
        return []




load_dotenv()

TELEGRAM_TOKEN   = os.environ.get("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID", "")

if not TELEGRAM_TOKEN:
    raise ValueError("TELEGRAM_BOT_TOKEN not set")
if not TELEGRAM_CHAT_ID:
    raise ValueError("TELEGRAM_CHAT_ID not set")

RAPIDAPI_KEY       = os.environ.get("RAPIDAPI_KEY", "")
GSHEET_CREDENTIALS = os.environ.get("GSHEET_CREDENTIALS", "")
GSHEET_ID          = os.environ.get("GSHEET_ID", "")
GSHEET_SHEET_NAME  = "Jobs"

CF_WORKER_URL    = os.environ.get("CF_WORKER_URL", "")
ADZUNA_APP_ID    = os.environ.get("ADZUNA_APP_ID", "")
ADZUNA_API_KEY   = os.environ.get("ADZUNA_API_KEY", "")

ADZUNA_APP_ID = os.getenv("ADZUNA_APP_ID", "")
ADZUNA_API_KEY = os.getenv("ADZUNA_API_KEY", "")

SEEN_JOBS_FILE   = SCRIPT_DIR / "seen_jobs.txt"
MAX_SEEN_JOBS    = 3000
MAX_JOBS_PER_RUN = 20
MIN_FIT_SCORE    = 35
MAX_JOB_AGE_DAYS = 7

JSEARCH_QUERIES = {
    1: ["I&C junior engineer", "I&C senior engineer", "Instrument engineer", "control system engineer"],
    2: ["PLC engineer", "SCADA engineer"],
    3: ["Control engineer", "PLC programmer remote"],
}

_DEFAULT_SKILLS = [
    "siemens", "eplan", "basic", "instrument",
    "autocad", "aveva", "aveva instrumentation", "aveva e3d",
    "HMI", "basic design", "FEED",
    "EPC", "detail design", "electrcial", "DCS", "PLC", "siemens", "eplan", "basic design", "instrument", "autocad", "aveva", "aveva instrumentation", "aveva e3d", "HMI", "detail design", "FEED", "EPC", "electrcial", "DCS", "PLC", "RTU", "SCADA", "ESD", "FGS", "sensor", "control valve", "MOV", "conceptual design", "FAT", "SAT",
]
_user_skills_env = os.environ.get("USER_SKILLS", "")
MY_SKILLS = [s.strip().lower() for s in _user_skills_env.split(",") if s.strip()] if _user_skills_env else _DEFAULT_SKILLS

BLACKLIST_KEYWORDS = [
    "us residents only", "must reside in us", "must be located in us",
    "must be based in the us", "must be based in us",
    "must be authorized to work in the us",
    "agency", "full stack", "fullstack",
    "native english speaker only",
    "director", "head of", "vp of",
]

BOOST_KEYWORDS = {
    # Core I&C Titles
    "Instrumentation": 30,
    "Instrument": 28,
    "Instrumentation Engineer": 30,
    "Instrument Engineer": 28,
    "Instrumentation & Control": 30,
    "I&C": 30,
    "I&C Engineer": 30,
    "Control Engineer": 28,
    "Control Systems Engineer": 28,
    "Automation Engineer": 26,
    "Process Control Engineer": 26,
    "Electrical & Instrumentation": 24,
    "E&I": 24,

    # Control Systems
    "SCADA": 26,
    "PLC": 26,
    "DCS": 26,
    "RTU": 22,
    "SIS": 22,
    "ESD": 22,
    "F&G": 18,
    "HMI": 18,
    "Telemetry": 18,

    # Engineering Activities
    "FEED": 24,
    "Basic Engineering": 22,
    "Detailed Engineering": 22,
    "Engineering Design": 22,
    "Commissioning": 24,
    "Pre-commissioning": 22,
    "Start-up": 20,
    "FAT": 20,
    "SAT": 20,
    "Loop Check": 18,
    "Troubleshooting": 18,
    "Vendor": 16,
    "Procurement": 14,

    # Documentation
    "Control Philosophy": 18,
    "Cause & Effect": 18,
    "Instrument Datasheet": 18,
    "Instrument Index": 16,
    "I/O List": 16,
    "Loop Diagram": 16,
    "Hook-up": 14,
    "Cable Schedule": 14,

    # Industries
    "Oil & Gas": 24,
    "Offshore": 22,
    "Onshore": 18,
    "Petrochemical": 20,
    "Refinery": 20,
    "Pipeline": 20,
    "Gas Transmission": 18,
    "Power Plant": 18,
    "Combined Cycle": 16,
    "Mining": 16,
    "Mineral Processing": 16,
    "Copper": 14,
    "Iron Ore": 14,

    # Standards
    "ISA": 14,
    "IEC": 14,
    "HAZOP": 14,
    "SIL": 12,

    # Work Type
    "Remote": 10,
    "Hybrid": 10,
    "WFH": 8,
    "Flexible": 6,
    "Contract": 6,
    "Permanent": 6,

    # Experience Levels
    "Junior": 8,
    "Mid-Level": 12,
    "Senior": 18,
    "Lead": 16,
    "Principal": 14,
}

_SKILL_PATTERNS   = {s: re.compile(r"\b" + re.escape(s) + r"\b", re.I) for s in MY_SKILLS}
_BOOST_PATTERNS   = {kw: re.compile(r"\b" + re.escape(kw) + r"\b", re.I) for kw in BOOST_KEYWORDS}
_BLACKLIST_PATTERNS = {kw: re.compile(r"\b" + re.escape(kw.lower()) + r"\b", re.I) for kw in BLACKLIST_KEYWORDS}

# ── Prompt Template ─────────────────────────────────────────────────────────

CL_PROMPT_TEMPLATE = os.environ.get("CL_PROMPT", "")

def load_prompt_template() -> str:
    # اول از متغیر محیطی CL_PROMPT بخون
    if CL_PROMPT_TEMPLATE:
        return CL_PROMPT_TEMPLATE.strip()
    # اگه نیست، از فایل prompt.txt بخون
    try:
        prompt_file = SCRIPT_DIR / "prompt.txt"
        if prompt_file.exists():
            with open(prompt_file, "r", encoding="utf-8") as f:
                content = f.read().strip()
                if content:
                    return content
    except Exception as e:
        log.warning(f"Could not load prompt.txt: {e}")
    return "Write a short, professional cover letter for the '{title}' position at '{company}'. Focus on my technical I&C skills. Job link: {url}"


from urllib.parse import urlsplit, urlunsplit
import hashlib


def build_job_id(job: dict) -> str:
    """
    Build a stable unique identifier for a job.
    """

    if job.get("id"):
        return str(job["id"]).strip()

    url = (job.get("url") or "").strip().lower()

    if url:

        parts = urlsplit(url)

        normalized = urlunsplit((
            parts.scheme,
            parts.netloc,
            parts.path.rstrip("/"),
            "",     # remove query
            "",     # remove fragment
        ))

        return hashlib.sha256(
            normalized.encode("utf-8")
        ).hexdigest()

    fingerprint = "|".join([
        (job.get("title") or "").strip().lower(),
        (job.get("company") or "").strip().lower(),
        (job.get("location") or "").strip().lower(),
    ])

    return hashlib.sha256(
        fingerprint.encode("utf-8")
    ).hexdigest()


# ── ژalculate resume match ─────────────────────────────────────────────────────────
def calculate_resume_match(job: dict):

    score = 0

    text = (
        (job.get("title") or "") + " " +
        (job.get("description") or "")
    ).lower()

    matched = []

    for title in USER_PROFILE["target_titles"]:
        if title.lower() in text:
            score += 20
            matched.append(title)

    for industry in USER_PROFILE["industries"]:
        if industry.lower() in text:
            score += 15
            matched.append(industry)

    for system in USER_PROFILE["systems"]:
        if system.lower() in text:
            score += 8
            matched.append(system)

    for keyword in USER_PROFILE["keywords"]:
        if keyword.lower() in text:
            score += 4
            matched.append(keyword)

    return min(score,100), matched


# ── Calculate Overall Match ─────────────────────────────────────────────────────────
def calculate_overall_match(job):

    score = 0

    matched = []

    text = (
        (job.get("title") or "") +
        " " +
        (job.get("description") or "")
    ).lower()

    # ------------------------
    # Title
    # ------------------------

    for t in USER_PROFILE["target_titles"]:

        if t.lower() in text:

            score += MATCH_WEIGHTS["title"]

            matched.append(t)

            break

    # ------------------------
    # Industry
    # ------------------------

    for ind in USER_PROFILE["industries"]:

        if ind.lower() in text:

            score += MATCH_WEIGHTS["industry"]

            matched.append(ind)

            break

    # ------------------------
    # Systems
    # ------------------------

    for sys in USER_PROFILE["systems"]:

        if sys.lower() in text:

            score += MATCH_WEIGHTS["systems"]

            matched.append(sys)

            break

    # ------------------------
    # Company
    # ------------------------

    company = (job.get("company") or "").lower()

    for c in PREFERRED_COMPANIES:

        if c.lower() in company:

            score += MATCH_WEIGHTS["company"]

            matched.append(c)

            break

    # ------------------------
    # Country
    # ------------------------

    location = (job.get("location") or "").lower()

    for country in TARGET_COUNTRIES:

        if country.lower() in location:

            score += MATCH_WEIGHTS["location"]

            matched.append(country)

            break

    return min(score,100), matched



# ── Seen Jobs Cache ─────────────────────────────────────────────────────────

def load_seen_jobs() -> OrderedDict:
    seen = OrderedDict()
    if SEEN_JOBS_FILE.exists():
        for line in SEEN_JOBS_FILE.read_text(encoding="utf-8").splitlines():
            if line.strip():
                seen[line.strip()] = True
        log.info(f"Loaded {len(seen)} seen IDs")
    else:
        log.info("No cache — starting fresh")
    return seen

def save_seen_jobs(seen: OrderedDict) -> None:
    ids = list(seen.keys())
    if len(ids) > MAX_SEEN_JOBS:
        ids = ids[-MAX_SEEN_JOBS:]
    SEEN_JOBS_FILE.write_text("\n".join(ids), encoding="utf-8")
    log.info(f"Saved {len(ids)} IDs to cache")

# ── is_relevant_ic_job(job) ───────────────────────────────────────────────────────────────

IC_KEYWORDS = [
    "instrumentation",
    "instrument engineer",
    "control engineer",
    "control systems",
    "process control",
    "scada",
    "dcs",
    "plc",
    "automation",
    "field engineer",
    "commissioning",
    "control system",
    "I&C engineer",
    "automation enginner",
    "siemens pcs7",
    "honeywell",
    "yokogawa",
    "emerson",
    "abb",
    "foxboro",
    "field instrumentation",
    "E&I engineer",
    "RTU",
    "instrument",
    "control system",
    "automation engineer",
    "industrial automation",
    "electrical and instrumentation",
    "i&c",
    "plc",
    "scada",
    "dcs",
    "pcs7",
    "tia portal",
    "wincc",
    "step7",
    "siemens",
    "abb",
    "emerson",
    "yokogawa",
    "honeywell",
    "foxboro",
    "schneider",
    "rockwell",
    "allen bradley",
    "commissioning",
    "field instrumentation",
    "loop check",
    "functional safety",
    "esd",
    "sis",
]

NON_IC_KEYWORDS = [
    "software",
    "backend",
    "frontend",
    "full stack",
    "machine learning",
    "artificial intelligence",
    "ai engineer",
    "ios",
    "android",
    "react",
    "python developer",
    "java developer",
    "software engineer",
    "software developer",
    "mobile developer",
    "node.js",
    "javascript",
    "typescript",
    "golang",
    "machine learning",
    "artificial intelligence",
    "ai engineer",
    "data scientist",
    "data engineer",
    "cyber security",
    "product manager",
    "sales",
    "marketing",
    "recruiter",
    "hr",
]

# ── Relevant I&C job ───────────────────────────────────────────────────────────────
def is_relevant_ic_job(job: dict) -> bool:
    """
    Returns True if the job is related to Instrumentation & Control.
    """

    text = " ".join([
        (job.get("title") or "").lower(),
        (job.get("description") or "").lower(),
        (job.get("company") or "").lower(),
        (job.get("location") or "").lower(),
    ])

    # Normalize separators
    text = (
        text.replace("-", " ")
            .replace("/", " ")
            .replace("&", " ")
    )

    # Reject unrelated jobs
    if any(word.lower() in text for word in NON_IC_KEYWORDS):
        return False

    # Accept if any I&C keyword exists
    if any(word.lower() in text for word in IC_KEYWORDS):
        return True

    return False

# ── Fit Score ───────────────────────────────────────────────────────────────
def calculate_fit_score(job: dict) -> tuple:
    score = 0

    TITLE_SCORES = {
        "lead instrumentation engineer": 35,
        "senior instrumentation engineer": 32,
        "instrumentation engineer": 30,
        "lead control engineer": 30,
        "control engineer": 28,
        "i&c engineer": 30,
        "instrument engineer": 28,
        "automation engineer": 25,
        "process control engineer": 25,
        "dcs engineer": 24,
        "plc engineer": 22,
        "scada engineer": 22,
        "electrical & instrumentation engineer": 28,
        "commissioning engineer": 18,
    }

    INDUSTRY_SCORES = {
        "oil & gas": 18,
        "oil and gas": 18,
        "lng": 16,
        "refinery": 16,
        "petrochemical": 15,
        "power plant": 14,
        "energy": 12,
        "chemical plant": 12,
        "offshore": 14,
        "pipeline": 12,
    }

    SYSTEM_SCORES = {
        "siemens": 8,
        "pcs7": 10,
        "tia portal": 8,
        "step7": 8,
        "wincc": 8,
        "honeywell": 8,
        "experion": 10,
        "emerson": 8,
        "deltav": 10,
        "abb": 8,
        "800xa": 10,
        "yokogawa": 8,
        "centum": 10,
        "foxboro": 8,
        "schneider": 8,
        "rockwell": 8,
    }
  
    EXPERT_KEYWORDS = {
        "feed": 10,
        "detail engineering": 8,
        "oil & gas": 12,
        "gas compressor": 15,
        "commissioning": 10,
        "dcs": 8,
        "plc": 6,
        "scada": 6,
        "instrumentation": 8,
        "control system": 8,
        "functional safety": 8,
        "sis": 8,
    }
    #Blacklist برای شرکت‌هایی که علاقه‌ای به آن‌ها ندارید
    BLACKLIST_COMPANIES = [
        "tiktok",
        "bytedance",
    ]
  
    matched_skills = []
    title    = (job.get("title") or "").lower()
    desc     = (job.get("description") or "").lower()
    combined = f"{title} {desc}"

    for title_keyword, pts in TITLE_SCORES.items():
        if title_keyword in title:
            score += pts
  
    company = (job.get("company") or "").lower()
    if any(c in company for c in BLACKLIST_COMPANIES):
        return (0, [])  # ✅ Return early instead of continue
  
    for keyword, pts in EXPERT_KEYWORDS.items():
        if keyword in combined:
            score += pts

    for keyword, pts in INDUSTRY_SCORES.items():
        if keyword in combined:
            score += pts
          
    for keyword, pts in SYSTEM_SCORES.items():
        if keyword in combined:
            score += pts
  
  
    for skill in MY_SKILLS:
        if _SKILL_PATTERNS[skill].search(combined):
            matched_skills.append(skill)
            score += 7

    if re.search(r"\bI&C\b", title):
        score += 12
    if job.get("salary"):
        score += 10
    if job.get("remote"):
        score += 8
    if any(re.search(r"\b" + w + r"\b", title) for w in ["junior", "associate", "entry", "jr"]):
        score += 10

    return min(score, 100), matched_skills[:4]

# ── Free Sources ────────────────────────────────────────────────────────────

def fetch_remotive() -> list:
    endpoints = [
        "https://remotive.com/api/remote-jobs?category=Instrument+engineer&limit=20",
        "https://remotive.com/api/remote-jobs?search=Control+engineer&limit=10",
        "https://remotive.com/api/remote-jobs?search=I&C+engineer&limit=10",
       
    ]
    results = []
    for url in endpoints:
        try:
            resp = requests.get(url, timeout=15, headers={"User-Agent": "Mozilla/5.0"})
            resp.raise_for_status()
            for j in resp.json().get("jobs", []):
                results.append({
                    "id":           f"remotive_{j.get('id', '')}",
                    "title":        j.get("title", ""),
                    "company":      j.get("company_name", ""),
                    "description":  j.get("description", ""),
                    "salary":       j.get("salary", ""),
                    "remote":       True,
                    "url":          j.get("url", ""),
                    "source":       "Remotive",
                    "source_emoji": "🌐",
                    "posted_at":    (j.get("publication_date") or "")[:10],
                    "location":     "Remote",
                })
        except Exception as e:
            log.error(f"Remotive error: {e}")
        time.sleep(1)
    log.info(f"Remotive -> {len(results)} jobs")
    return results
#--------------------------------------------------
def fetch_indeed() -> list:
    endpoints = [
        "https://indeed.com/api/remote-jobs?category=Instrument+engineer&limit=20",
        "https://indeed.com/api/remote-jobs?search=Control+engineer&limit=10",
        "https://indeed.com/api/remote-jobs?search=I&C+engineer&limit=10",
       
    ]
    results = []
    for url in endpoints:
        try:
            resp = requests.get(url, timeout=15, headers={"User-Agent": "Mozilla/5.0"})
            resp.raise_for_status()
            for j in resp.json().get("jobs", []):
                results.append({
                    "id":           f"indeed{j.get('id', '')}",
                    "title":        j.get("title", ""),
                    "company":      j.get("company_name", ""),
                    "description":  j.get("description", ""),
                    "salary":       j.get("salary", ""),
                    "remote":       True,
                    "url":          j.get("url", ""),
                    "source":       "Indeed",
                    "source_emoji": "🌐",
                    "posted_at":    (j.get("publication_date") or "")[:10],
                    "location":     "Remote",
                })
        except Exception as e:
            log.error(f"Indeed error: {e}")
        time.sleep(1)
    log.info(f"Indeed -> {len(results)} jobs")
    return results

#--------------------------------------------------
def fetch_jobicy() -> list:
    endpoints = [
        "https://jobicy.com/api/v2/remote-jobs?tag=Instrument+engineer&limit=20",
        "https://jobicy.com/api/v2/remote-jobs?tag=Control+engineer&limit=15",
        "https://jobicy.com/api/v2/remote-jobs?tag=I&C+engineer&limit=10",
    ]
    results = []
    for url in endpoints:
        try:
            resp = requests.get(url, timeout=15)
            resp.raise_for_status()
            for j in resp.json().get("jobs", []):
                lo = j.get("annualSalaryMin")
                hi = j.get("annualSalaryMax")
                cur = j.get("annualSalaryCurrency", "USD")
                sal = f"{cur} {int(lo):,}-{int(hi):,}/yr" if lo and hi else (f"{cur} {int(lo):,}+/yr" if lo else "")
                results.append({
                    "id":           f"jobicy_{j.get('id', '')}",
                    "title":        j.get("jobTitle", ""),
                    "company":      j.get("companyName", ""),
                    "description":  j.get("jobDescription", ""),
                    "salary":       sal,
                    "remote":       True,
                    "url":          j.get("url", ""),
                    "source":       "Jobicy",
                    "source_emoji": "🟢",
                    "posted_at":    (j.get("pubDate") or "")[:10],
                    "location":     "Remote",
                })
        except Exception as e:
            log.error(f"Jobicy error: {e}")
        time.sleep(1)
    log.info(f"Jobicy -> {len(results)} jobs")
    return results

def fetch_arbeitnow() -> list:
    IandC_TERMS = [
      "I&C", 
      "instrument", 
      "control", 
      "PLC", 
      "SCADA", 
      "instrumentation", 
      "control valve"
    ]
    try:
        resp = requests.get(
          "https://arbeitnow.com/api/job-board-api", 
          timeout=15,
          headers={"User-Agent": "Mozilla/5.0"},
        )
        resp.raise_for_status()
      
        results = []
        for j in resp.json().get("data", []):
            if not j.get("remote"):
                continue
            title = (j.get("title") or "").lower()
            desc  = (j.get("description") or "").lower()[:300]
            if not any(t in title or t in desc for t in IandC_TERMS):
                continue
            results.append({
                "id":           f"arbeitnow_{j.get('slug', '')}",
                "title":        j.get("title", ""),
                "company":      j.get("company_name", ""),
                "description":  j.get("description", ""),
                "salary":       "",
                "remote":       True,
                "url":          j.get("url", ""),
                "source":       "Arbeitnow",
                "source_emoji": "🔷",
                "posted_at":    datetime.now(timezone.utc).strftime("%Y-%m-%d"),
                "location":     "Remote",
            })
        log.info(f"Arbeitnow -> {len(results)} jobs")
        return results
    except Exception as e:
        log.error(f"Arbeitnow error: {e}")
        return []

def fetch_adzuna() -> list:
    if not ADZUNA_APP_ID or not ADZUNA_API_KEY:
        log.info("Skipping Adzuna (credentials not configured)")
        return []

    results = []
    for q in ["I&C junior engineer", "I&C senior engineer", "Instrument engineer", "control system engineer", "PLC engineer", "SCADA engineer", "Control engineer", "PLC programmer remote"]:
        try:
            resp = requests.get(
                f"https://api.adzuna.com/v1/api/jobs/us/search/1",
                params={"app_id": ADZUNA_APP_ID, "app_key": ADZUNA_API_KEY,
                        "what": q, "what_or": "remote", "max_days_old": 7,
                        "results_per_page": 15, "content-type": "application/json"},
                timeout=15,
            )
            resp.raise_for_status()
            for j in resp.json().get("results", []):
                results.append({
                    "id":           f"adzuna_{j.get('id', '')}",
                    "title":        j.get("title", ""),
                    "company":      (j.get("company") or {}).get("display_name", ""),
                    "description":  j.get("description", ""),
                    "salary":       f"${int(float(j['salary_min'])):,}-${int(float(j.get('salary_max') or j.get('salary_min'))):,}/yr" if j.get("salary_min") else "",
                    "remote":       True,
                    "url":          j.get("redirect_url", ""),
                    "source":       "Adzuna",
                    "source_emoji": "🟡",
                    "posted_at":    (j.get("created") or "")[:10],
                    "location":     j.get("location", {}).get("display_name", "Remote"),
                })
        except Exception as e:
            log.error(f"Adzuna error ({q}): {e}")
        time.sleep(1)
    log.info(f"Adzuna -> {len(results)} jobs")
    return results

def fetch_findwork() -> list:
    IandC_TERMS =  ["I&C junior engineer", "I&C senior engineer", "Instrument engineer", "control system engineer", "PLC engineer", "SCADA engineer", "Control engineer", "PLC programmer remote"]
    try:
        resp = requests.get(
            "https://findwork.dev/api/jobs/",
            params={"search": "I&C", "remote": "true", "order_by": "-date_posted"},
            headers={"User-Agent": "Mozilla/5.0 (compatible; I&CJobBot/5.0)"},
            timeout=15,
        )
        if resp.status_code == 403:
            log.warning("FindWork.dev: access denied")
            return []
        resp.raise_for_status()
        results = []
        for j in resp.json().get("results", []):
            title = (j.get("role") or "").lower()
            desc  = (j.get("text") or "").lower()[:500]
            if not any(t in title or t in desc for t in IandC_TERMS):
                continue
            results.append({
                "id":           f"findwork_{j.get('id', '')}",
                "title":        j.get("role", ""),
                "company":      j.get("company_name", ""),
                "description":  j.get("text", ""),
                "salary":       "",
                "remote":       j.get("remote", True),
                "url":          j.get("url", ""),
                "source":       "FindWork",
                "source_emoji": "🟣",
                "posted_at":    (j.get("date_posted") or "")[:10],
                "location":     j.get("location") or "Remote",
            })
        log.info(f"FindWork -> {len(results)} jobs")
        return results
    except Exception as e:
        log.error(f"FindWork error: {e}")
        return []

def fetch_cloudflare_worker() -> list:
    if not CF_WORKER_URL:
        return []
    worker_url = CF_WORKER_URL.rstrip("/")
    if not worker_url.endswith("/jobs"):
        worker_url += "/jobs"
    try:
        resp = requests.get(worker_url, headers={"User-Agent": "I&CJobBot/5.0"}, timeout=20)
        if resp.status_code in (401, 404):
            log.error(f"CF Worker: {resp.status_code}")
            return []
        resp.raise_for_status()
        data = resp.json()
        if data.get("status") != "ok":
            return []
        jobs = []
        for j in data.get("jobs", []):
            if not j.get("id") or not j.get("title"):
                continue
            jobs.append({
                "id":           str(j.get("id", "")),
                "title":        j.get("title", ""),
                "company":      j.get("company", ""),
                "description":  j.get("description", ""),
                "salary":       j.get("salary", ""),
                "remote":       j.get("remote", True),
                "url":          j.get("url", ""),
                "source":       j.get("source", "CF Worker"),
                "source_emoji": j.get("source_emoji", "☁️"),
                "posted_at":    (j.get("posted_at") or "")[:10],
                "location":     j.get("location", "Remote"),
            })
        log.info(f"CF Worker -> {len(jobs)} jobs")
        return jobs
    except Exception as e:
        log.error(f"CF Worker error: {e}")
        return []


def fetch_linkedin() -> list:
    endpoints = [
        "https://www.linkedin.com/jobs/remote-jobs/"

       
    ]
    results = []
    for url in endpoints:
        try:
            resp = requests.get(url, timeout=15, headers={"User-Agent": "Mozilla/5.0"})
            resp.raise_for_status()
            for j in resp.json().get("jobs", []):
                results.append({
                    "id":           f"linkedin_{j.get('id', '')}",
                    "title":        j.get("title", ""),
                    "company":      j.get("company_name", ""),
                    "description":  j.get("description", ""),
                    "salary":       j.get("salary", ""),
                    "remote":       True,
                    "url":          j.get("url", ""),
                    "source":       "Linkedin",
                    "source_emoji": "🌐",
                    "posted_at":    (j.get("publication_date") or "")[:10],
                    "location":     "Remote",
                })
        except Exception as e:
            log.error(f"Linkedin error: {e}")
        time.sleep(1)
    log.info(f"Linkedin -> {len(results)} jobs")
    return results


def fetch_linkedin1() -> list:
    IandC_TERMS =  ["I&C junior engineer", "I&C senior engineer", "Instrument engineer", "control system engineer", "PLC engineer", "SCADA engineer", "Control engineer", "PLC programmer remote"]
    try:
        resp = requests.get("https://www.linkedin.com/jobs/remote-jobs/", timeout=15, headers={"User-Agent": "Mozilla/5.0"})
        resp.raise_for_status()
        results = []
        for j in resp.json().get("data", []):
            if not j.get("remote"):
                continue
            title = (j.get("title") or "").lower()
            desc  = (j.get("description") or "").lower()[:300]
            if not any(t in title or t in desc for t in IandC_TERMS):
                continue
            results.append({
                "id":           f"linkedin1_{j.get('slug', '')}",
                "title":        j.get("title", ""),
                "company":      j.get("company_name", ""),
                "description":  j.get("description", ""),
                "salary":       "",
                "remote":       True,
                "url":          j.get("url", ""),
                "source":       "Linkedin1",
                "source_emoji": "🔷",
                "posted_at":    datetime.now(timezone.utc).strftime("%Y-%m-%d"),
                "location":     "Remote",
            })
        log.info(f"Linkedin1 -> {len(results)} jobs")
        return results
    except Exception as e:
        log.error(f"Linkedin1 error: {e}")
        return []

# ── Remove duplicate jobs ────────────────────────────────────────────────


# ── JSearch API (اختیاری) ───────────────────────────────────────────────────

def _should_run_p3() -> bool:
    return datetime.now(timezone.utc).day % 2 == 0

def search_jsearch(query: str) -> list:
    if not RAPIDAPI_KEY:
        return []
    url = "https://jsearch.p.rapidapi.com/search"
    headers = {"x-rapidapi-key": RAPIDAPI_KEY, "x-rapidapi-host": "jsearch.p.rapidapi.com"}
    params = {"query": query, "num_pages": "1", "date_posted": "week", "work_from_home": "true"}

    for attempt in range(1, 4):
        try:
            resp = requests.get(url, headers=headers, params=params, timeout=20)
            if resp.status_code == 429:
                log.warning("JSearch rate limit — waiting 60s")
                time.sleep(60)
                continue
            if resp.status_code == 403:
                log.error("JSearch 403")
                return []
            resp.raise_for_status()
            data = resp.json()
            if data.get("status") != "OK":
                return []
            return [_normalize_jsearch(j) for j in data.get("data", [])]
        except requests.exceptions.Timeout:
            log.warning(f"JSearch timeout {attempt}/3")
        except Exception as e:
            log.error(f"JSearch error: {e}")
            return []
        if attempt < 3:
            time.sleep(5 * attempt)
    return []

def _normalize_jsearch(j: dict) -> dict:
    salary = j.get("job_salary_string", "")
    if not salary and j.get("job_min_salary"):
        lo = int(j["job_min_salary"])
        hi = int(j.get("job_max_salary") or lo)
        per = {"year": "/yr", "month": "/mo", "hour": "/hr"}.get((j.get("job_salary_period") or "").lower(), "")
        salary = f"${lo:,}-${hi:,}{per}" if lo != hi else f"${lo:,}+{per}"

    city, country = j.get("job_city") or "", j.get("job_country") or ""
    loc_parts = [p for p in (city, country) if p]
    loc = ", ".join(loc_parts) or "Remote"

    return {
        "id":           j.get("job_id", ""),
        "title":        j.get("job_title", ""),
        "company":      j.get("employer_name", ""),
        "description":  j.get("job_description", ""),
        "salary":       salary,
        "remote":       True,
        "url":          j.get("job_apply_link") or j.get("job_google_link") or "",
        "source":       j.get("job_publisher", "JSearch"),
        "source_emoji": "🔍",
        "posted_at":    (j.get("job_posted_at_datetime_utc") or "")[:10],
        "location":     loc,
    }

# ── Filters ─────────────────────────────────────────────────────────────────

def is_blacklisted(job: dict) -> tuple:
    text = f"{(job.get('title') or '').lower()} {(job.get('description') or '')[:2000].lower()}"
    for kw, pattern in _BLACKLIST_PATTERNS.items():
        if pattern.search(text):
            return True, kw
    return False, ""

def is_too_old(job: dict) -> bool:
    posted = (job.get("posted_at") or "")[:10]
    if not posted:
        return False
    try:
        dt = datetime.strptime(posted, "%Y-%m-%d").replace(tzinfo=timezone.utc)
        return (datetime.now(timezone.utc) - dt).days > MAX_JOB_AGE_DAYS
    except Exception:
        return False

# ── Telegram ────────────────────────────────────────────────────────────────

def _score_bar(score: int) -> str:
    filled = round(score / 10)
    return "█" * filled + "░" * (10 - filled)

def format_job(
    job: dict,
    score: int,
    skills: list,
    resume_score: int = None,
    resume_matches: list = None,
) -> str:
    title   = html.escape(job.get("title") or "No Title")
    company = html.escape(job.get("company") or "Unknown")
    salary  = job.get("salary") or ""
    source  = html.escape(job.get("source") or "")
    semoji  = job.get("source_emoji", "🌐")
    posted  = job.get("posted_at") or ""
    loc     = html.escape(job.get("location") or "Remote")
    
    lines = [
        f"💼 <b>{title}</b>",
        f"🏢 {company}",
        f"📍 {loc}",
    ]
    if salary:
        lines.append(f"💰 <b>{html.escape(str(salary))}</b>")
    lines.append(f"📊 {_score_bar(score)} {score}/100")

    # ---------- NEW ----------
    if resume_score is not None:
        #lines.append(f"🎯 Resume Match: <b>{resume_score}%</b>")
        lines.append(f"🏆 Overall Match: <b>{resume_score}%</b>")
        
    if resume_matches:
        lines.append(
            "🧠 " + ", ".join(
                html.escape(x) for x in resume_matches[:5]
            )
        )
    # -------------------------

  
    if skills:
        lines.append(
          f"✅ {', '.join(html.escape(s) for s in skills)}"
        )
    lines.append(f"{semoji} {source}")
  
    if posted:
        lines.append(f"📅 {posted}")

    return "\n".join(lines)

def build_job_buttons(job: dict) -> dict:
    """ساخت دکمه‌ها: Apply + ChatGPT Cover Letter"""
    url = job.get("url", "")
    if not url:
        return {}

    title   = job.get("title", "")
    company = job.get("company", "")

    template = load_prompt_template()
    prompt   = template.format(title=title, company=company, url=url)
    safe_prompt = urllib.parse.quote(prompt)
    chatgpt_url = f"https://chatgpt.com/?q={safe_prompt}"

    return {"inline_keyboard": [
        [{"text": "📝 Apply Now", "url": url}],
        [{"text": "🤖 ChatGPT Cover Letter", "url": chatgpt_url}]
    ]}

def send_telegram(text: str, reply_markup: dict = None, _retries: int = 3) -> bool:
    api_url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": text,
        "parse_mode": "HTML",
        "link_preview_options": {"is_disabled": True},
    }
    if reply_markup:
        payload["reply_markup"] = reply_markup

    for attempt in range(1, _retries + 1):
        try:
            resp = requests.post(api_url, json=payload, timeout=15)
            if resp.ok:
                return True

            if resp.status_code == 429:
                retry_after = resp.json().get("parameters", {}).get("retry_after", 30)
                log.warning(f"Telegram Flood Wait — sleeping {retry_after}s (attempt {attempt}/{_retries})")
                time.sleep(retry_after + 1)
                continue

            log.error(f"Telegram {resp.status_code}: {resp.text[:200]}")
            return False
        except requests.exceptions.Timeout:
            log.warning(f"Telegram timeout (attempt {attempt}/{_retries})")
            if attempt < _retries:
                time.sleep(3)
        except Exception as e:
            log.error(f"Telegram error: {e}")
            return False
    return False

# ── Google Sheets ────────────────────────────────────────────────────────────

def get_sheets_client():
    if not SHEETS_AVAILABLE or not GSHEET_CREDENTIALS or not GSHEET_ID:
        return None
    try:
        creds = Credentials.from_service_account_info(
            json.loads(GSHEET_CREDENTIALS),
            scopes=["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"],
        )
        log.info("Google Sheets connected")
        return gspread.authorize(creds)
    except Exception as e:
        log.error(f"Sheets auth error: {e}")
        return None

def ensure_sheet_headers(client) -> None:
    if not client:
        return

    try:
        workbook = client.open_by_key(GSHEET_ID)

        try:
            sheet = workbook.worksheet(GSHEET_SHEET_NAME)
        except Exception:
            log.warning(
                "Worksheet '%s' not found. Creating it...",
                GSHEET_SHEET_NAME,
            )

            sheet = workbook.add_worksheet(
                title=GSHEET_SHEET_NAME,
                rows=1000,
                cols=20,
            )

        if not sheet.row_values(1):
            sheet.insert_row(
                [
                    "Job Title",
                    "Company",
                    "Source",
                    "Apply Link",
                    "Posted",
                    "Salary",
                    "Fit Score",
                    "Location",
                    "Saved At (UTC)",
                    "Status",
                    "Cover Letter Link",
                ],
                1,
            )

    except Exception:
        log.exception("Sheet header error")


def batch_append_to_sheet(client, rows: list) -> None:
    if not client or not rows:
        return
    try:
        sheet = client.open_by_key(GSHEET_ID).worksheet(GSHEET_SHEET_NAME)
        sheet.append_rows(rows, value_input_option="USER_ENTERED")
        log.info(f"Batch appended {len(rows)} rows to Google Sheets")
    except Exception as e:
        log.error(f"Sheet batch append error: {e}")

#------خواندن همه URLهای ارسال شده
#def load_sent_jobs(sheet):
 #   urls = set()

  #  records = sheet.get_all_records()

  #  for row in records:
   #     url = row.get("URL")

    #    if url:
     #       urls.add(url.strip())

    #log.info("Loaded %d sent jobs", len(urls))

   # return urls

#----ذخیره Job جدید
#from datetime import datetime

#def save_sent_job(sheet, job):

 #   sheet.append_row(
   #     [
  #          job.get("url", ""),
    #        datetime.now().strftime("%Y-%m-%d %H:%M"),
     #       job.get("company", ""),
      #      job.get("title", "")
       # ]
    #)




# ── Remove duplicate jobs ────────────────────────────────────────────────
def deduplicate_jobs(jobs: list) -> list:
    """
    Remove duplicate jobs collected from different sources.
    """

    seen = set()
    unique = []

    for job in jobs:
        jid = build_job_id(job)

        if jid in seen:
            continue

        seen.add(jid)
        unique.append(job)

    log.info(
        "Duplicate removal: %d -> %d jobs",
        len(jobs),
        len(unique),
    )

    return unique


#GREENHOUSE_COMPANIES = [
   # "openai",
    #"canonical",
   # "shopify",
   # "reddit",
   # "cloudflare",
#]

GREENHOUSE_COMPANIES = [
    "anduril",
    "astranis",
    "crusoe",
]

LEVER_COMPANIES = [
    "anduril",
    "zipline",
    "crusoe",
    "astranis",
    "saronic",
    "skydio",
    "shield-ai",
]
# ── Greenhouse Companies ─────────────────────────────────────
def fetch_greenhouse() -> list:
    """
    Fetch jobs from Greenhouse job boards.
    """
    jobs = []
    #if len(jobs) < 3:
        #pprint.pprint(job)
        
    for company in GREENHOUSE_COMPANIES:

        url = f"https://boards-api.greenhouse.io/v1/boards/{company}/jobs"

        try:
            resp = requests.get(
                url,
                timeout=20,
                headers={"User-Agent": "Mozilla/5.0"}
            )

            if resp.status_code != 200:
                continue

            data = resp.json()

            for item in data.get("jobs", []):

                jobs.append({
                    "id": f"greenhouse-{item.get('id')}",
                    "title": item.get("title", ""),
                    "company": company.title(),
                    "location": (
                        item.get("location", {}) or {}
                    ).get("name", ""),
                    "url": item.get("absolute_url", ""),
                    "description": "",
                    "salary": "",
                    "remote": False,
                    "source": "Greenhouse",
                    "posted_at": ""
                })

        except Exception as e:
            log.error(f"Greenhouse ({company}) error: {e}")

    log.info(f"Greenhouse: {len(jobs)} jobs")

    return jobs



# ── Fetch lever ─────────────────────────────────────────────────────────────────────

def fetch_lever() -> list:
    """
    Fetch jobs from Lever job boards.
    """
    jobs = []

    for company in LEVER_COMPANIES:

        url = f"https://api.lever.co/v0/postings/{company}?mode=json"

        try:
            r = requests.get(
                url,
                timeout=20,
                headers={"User-Agent": "Mozilla/5.0"}
            )
            log.info(f"Lever URL: {url}")
            log.info(f"Lever Status: {r.status_code}")

            if r.status_code != 200:
                log.info(f"Lever Response: {r.text[:300]}")
                continue
          
            data = r.json()

            for item in data:

                title = item.get("text", "")

                jobs.append({
                    "id": f"lever-{item.get('id')}",
                    "title": title,
                    "company": company.title(),
                    "location": (
                        item.get("categories", {})
                        .get("location", "")
                    ),
                    "url": item.get("hostedUrl", ""),
                    "description": "",
                    "salary": "",
                    "remote": False,
                    "source": "Lever",
                    "posted_at": "",
                })

        except Exception as e:
            log.error(f"Lever ({company}) error: {e}")

    log.info(f"Lever: {len(jobs)} jobs")

    return jobs

# ── Main ─────────────────────────────────────────────────────────────────────

def main() -> None:
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    log.info(f"=== I&C Job Scraper v5.0 started at {now} ===")

    seen_jobs = load_seen_jobs()
    sheets = get_sheets_client()
    ensure_sheet_headers(sheets)
#---added abbas
    #history_sheet = gc.open_by_key(GSHEET_ID).worksheet("SentJobs")
    GSHEET_SHEET_NAME = "Jobs"

    #sent_urls = load_sent_jobs(history_sheet)
  
    raw_jobs = []
    source_counts = {}

    sources = [
    ("Indeed", fetch_indeed),
    #("Adzuna", fetch_adzuna),
    ("Remotive", fetch_remotive),
    #("Jobicy", fetch_jobicy),
    ("ArbeitNow", fetch_arbeitnow),
    #("Greenhouse", fetch_greenhouse),
    #("Lever", fetch_lever),
    ("Indeed", fetch_indeed),
    ]

    relevant_jobs = 0

    for source_name, fetch_function in sources:

        source_jobs = safe_fetch(
            source_name,
            fetch_function,
        )

        source_counts[source_name] = len(source_jobs)
        raw_jobs.extend(source_jobs)

    # Count relevant jobs from this source (avoid referencing `job` before it's defined)
    for _job in source_jobs:
        try:
            if is_relevant_ic_job(_job):
                relevant_jobs += 1
        except Exception:
            # defensive: don't let one malformed job stop counting
            log.exception("Error while checking relevance for job from %s", source_name) 
  ###  
    log.info("=" * 60)
    log.info("SOURCE SUMMARY")

    for name, count in source_counts.items():
        log.info("%-20s : %4d jobs", name, count)

    log.info("=" * 60)
    raw_jobs = deduplicate_jobs(raw_jobs)
   # log.info("Greenhouse included in total jobs.")
    log.info("Collected %d jobs", len(raw_jobs))
    log.info("Relevant I&C jobs: %d", relevant_jobs)

    #  raw_jobs = []
     #   source_counts = {}

    # ── منابع رایگان ─────────────────────────────────────────────────────────
     #   for fn, name in [
    #      (fetch_remotive, "Remotive"),
     #     (fetch_jobicy, "Jobicy"),
      #    (fetch_arbeitnow, "Arbeitnow"),
     #   (fetch_adzuna, "Adzuna"),
      #  (fetch_findwork, "FindWork"),
      #      (fetch_cloudflare_worker, "CF Worker"),
       #     (fetch_linkedin, "Linkedin"),
        #    (fetch_linkedin1, "Linkedin1"),
      #  ]:
      #      try:
        #          jobs = fn()
      #          source_counts[name] = len(jobs)
      #          raw_jobs.extend(jobs)
      #      except Exception as e:
        #          log.error(f"{name} failed: {e}\n{traceback.format_exc()}")
        #          source_counts[name] = 0

  
    # ── JSearch (اختیاری) ────────────────────────────────────────────────────

  
    # ── فیلتر + امتیازدهی ────────────────────────────────────────────────────
    seen_ids = set()
    stats = {
        "blacklisted": 0,
        "seen": 0,
        "old": 0,
        "low_score": 0,
    }
    qualified = []

    debug = {
        "total": len(raw_jobs),
        "relevant": 0,
        "seen": 0,
        "blacklisted": 0,
        "old": 0,
        "low_score": 0,
        "qualified": 0,
    }

    log.info("Processing %d jobs...", len(raw_jobs))
    for job in raw_jobs:

        debug = {
            "total": len(raw_jobs),
            "relevant": 0,
            "seen": 0,
            "blacklisted": 0,
            "old": 0,
            "low_score": 0,
            "qualified": 0,
        }
        try:
            log.info(
                "JOB: %s | COMPANY: %s | SOURCE: %s",
                job.get("title"),
                job.get("company"),
                job.get("source"),
            )
            jid = build_job_id(job)
            if not is_relevant_ic_job(job):
                log.info("Rejected: %s", job.get("title"))
                continue

            if len(raw_jobs) > 0:
                log.info(
                    "DEBUG JOB -> %s | %s",
                    job.get("title"),
                    job.get("description", "")[:120]
            )

            
                debug["relevant"] += 1
                
            log.info("Accepted: %s", job.get("title"))
          

            if jid in seen_jobs or jid in seen_ids:
                debug["seen"] += 1
                stats["seen"] += 1
                continue

            seen_ids.add(jid)
            seen_jobs[jid] = True

            blacklisted, _ = is_blacklisted(job)
            if blacklisted:
                debug["blacklisted"] += 1
                stats["blacklisted"] += 1
                continue

            if is_too_old(job):
                debug["old"] += 1
                stats["old"] += 1
                continue

            score, skills = calculate_fit_score(job)
            #resume_score, resume_matches = calculate_resume_match(job)
            overall_score, overall_matches = calculate_overall_match(job)
            log.info(
                "Qualified Candidate -> %s | Score=%d",
                job.get("title"),
                score,
            )

            if score < MIN_FIT_SCORE:
                debug["low_score"] += 1
                stats["low_score"] += 1
                continue

            #qualified.append((job, score, skills))
            qualified.append((job, overall_score, overall_matches))
            debug["qualified"] += 1
            log.info("Added to qualified: %s", job.get("title"))

        except Exception:
            log.exception("Processing error")
  
        # Sort after collecting all qualified jobs
    qualified.sort(key=lambda x: x[1], reverse=True)

    log.info(
        f"Qualified: {len(qualified)} | BL: {stats['blacklisted']} | "
        f"Seen: {stats['seen']} | Old: {stats['old']} | Low: {stats['low_score']}"
     )
    #جدید
    log.info("=" * 60)
    log.info("DEBUG SUMMARY")
    log.info("Total jobs      : %d", debug["total"])
    log.info("Relevant I&C    : %d", debug["relevant"])
    log.info("Seen            : %d", debug["seen"])
    log.info("Blacklisted     : %d", debug["blacklisted"])
    log.info("Too old         : %d", debug["old"])
    log.info("Low score       : %d", debug["low_score"])
    log.info("Qualified       : %d", debug["qualified"])
    log.info("=" * 60)
    
    # ── ارسال به تلگرام ──────────────────────────────────────────────────
    # Prepare and send report
    active_sources = {k: v for k, v in source_counts.items() if v > 0}
    sources_line = " | ".join(f"{k}: {v}" for k, v in active_sources.items())

    if not qualified:
        send_telegram(
            f"🔍 <b>Daily Report</b>\n📅 {now}\n\n"
            f"No qualified jobs found.\n\n"
            f"📌 {sources_line or 'No sources'}\n"
            f"⛔ {stats['blacklisted']} filtered | "
            f"📉 {stats['low_score']} low score | "
            f"🔁 {stats['seen']} duplicates | "
            f"🕐 {stats['old']} old"
        )
        save_seen_jobs(seen_jobs)
        return

    send_telegram(
        f"🤖 <b>New I&C Jobs</b>\n"
        f"📅 {now}\n\n"
        f"✅ <b>{len(qualified)}</b> jobs (sorted by fit)\n"
        f"⛔ {stats['blacklisted']} filtered | "
        f"📉 {stats['low_score']} low | "
        f"🔁 {stats['seen']} dupes\n\n"
        f"📌 {sources_line}\n"
        f"🤖 ChatGPT Cover Letter: ON\n"
        f"➖➖➖➖➖➖➖➖"
    )
    time.sleep(1.5)

    sent = 0
    sheet_rows = []

    for job, score, skills in qualified[:MAX_JOBS_PER_RUN]:
        try:
            buttons = build_job_buttons(job)

            # get overall match details (use as resume match)
            overall_score, overall_matches = calculate_overall_match(job)
            resume_score, resume_matches = overall_score, overall_matches

            msg = format_job(
                job,
                score,
                skills,
                resume_score,
                resume_matches,
            )

            if send_telegram(msg, reply_markup=buttons if buttons else None):
                sent += 1
                sheet_rows.append([
                    job.get("title", ""), job.get("company", ""),
                    job.get("source", ""), job.get("url", ""),
                    job.get("posted_at", ""), job.get("salary", ""),
                    score, job.get("location", ""),
                    datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M"),
                    "New", "ChatGPT URL"
                ])

            time.sleep(1.5)
        except Exception as e:
            log.error(f"Send error: {e}")

    batch_append_to_sheet(sheets, sheet_rows)
    save_seen_jobs(seen_jobs)
    log.info(f"=== Done. Sent {sent}/{len(qualified)} ===")

if __name__ == "__main__":
    main()
