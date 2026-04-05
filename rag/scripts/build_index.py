"""One-time script to build the FAISS index from resources_seed.json.

Usage:
    python rag/scripts/build_index.py

Run this once after cloning the repo or when resources_seed.json is updated.
"""
import json
import sys
import asyncio
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import numpy as np
from rag.embedder import ResourceEmbedder
from rag.resource_db import init_db, insert_resources

SEED_PATH = Path(__file__).parent.parent / "data" / "resources_seed.json"
INDEX_DIR = Path(__file__).parent.parent / "data" / "faiss_index"
INDEX_PATH = INDEX_DIR / "nexus.index"
MAP_PATH = INDEX_DIR / "nexus.index.map"

BATCH_SIZE = 256


async def build():
    import faiss

    INDEX_DIR.mkdir(parents=True, exist_ok=True)

    if not SEED_PATH.exists():
        print(f"Seed file not found: {SEED_PATH}")
        print("Generating minimal demo seed...")
        _generate_demo_seed()

    with open(SEED_PATH) as f:
        records = json.load(f)

    print(f"Loaded {len(records)} resources. Initialising DB...")
    await init_db()
    await insert_resources(records)

    print("Embedding resources (this may take a few minutes)...")
    embedder = ResourceEmbedder()

    texts = [f"{r['title']} {r.get('description', '')} {' '.join(r.get('tags', []))}" for r in records]
    dim = 384  # all-MiniLM-L6-v2 output dim
    index = faiss.IndexFlatIP(dim)
    id_map: dict[int, int] = {}  # faiss_pos → resource_id

    for start in range(0, len(texts), BATCH_SIZE):
        batch_texts = texts[start : start + BATCH_SIZE]
        batch_records = records[start : start + BATCH_SIZE]
        embeddings = await embedder.embed(batch_texts)
        for i, (vec, rec) in enumerate(zip(embeddings, batch_records)):
            faiss_pos = start + i
            id_map[faiss_pos] = rec["id"]
        index.add(embeddings)
        print(f"  Indexed {min(start + BATCH_SIZE, len(texts))}/{len(texts)}")

    faiss.write_index(index, str(INDEX_PATH))
    with open(MAP_PATH, "w") as f:
        json.dump({str(k): v for k, v in id_map.items()}, f)

    print(f"Done. Index saved to {INDEX_PATH}")
    print(f"ID map saved to {MAP_PATH}")


SEED_RESOURCES: list[dict] = [
    # ── Government Schemes (domain: "govt-scheme") ───────────────────────
    {
        "id": 1,
        "title": "PMKVY 4.0 — Pradhan Mantri Kaushal Vikas Yojana",
        "url": "https://pmkvyofficial.org",
        "description": "India's flagship skill development scheme offering free short-term training, certification, and placement support for youth across 40+ sectors.",
        "tags": ["pmkvy", "govt", "free", "certification", "skill-development"],
        "domain": "govt-scheme",
        "type": "govt-scheme",
    },
    {
        "id": 2,
        "title": "Digital India Programme",
        "url": "https://digitalindia.gov.in",
        "description": "Government initiative to transform India into a digitally empowered society with digital infrastructure, governance, and digital literacy programmes including FutureSkills PRIME for IT professionals.",
        "tags": ["digital-india", "govt", "digital-literacy", "futureskills"],
        "domain": "govt-scheme",
        "type": "govt-scheme",
    },
    {
        "id": 3,
        "title": "Startup India — DPIIT Registration & Benefits",
        "url": "https://www.startupindia.gov.in",
        "description": "Government programme offering tax exemptions, seed funding, mentorship, and simplified compliance for recognised startups. Includes the Startup India Seed Fund Scheme and incubator support.",
        "tags": ["startup-india", "govt", "entrepreneurship", "funding", "tax-exemption"],
        "domain": "govt-scheme",
        "type": "govt-scheme",
    },
    {
        "id": 4,
        "title": "AICTE Internship Portal — Engineering Student Internships",
        "url": "https://internship.aicte-india.org",
        "description": "AICTE's dedicated internship portal connecting engineering and polytechnic students with industry internships across India, with stipend and credit support.",
        "tags": ["aicte", "internship", "engineering", "govt", "industry"],
        "domain": "govt-scheme",
        "type": "govt-scheme",
    },
    {
        "id": 5,
        "title": "National Apprenticeship Training Scheme (NATS)",
        "url": "https://portal.mhrdnats.gov.in",
        "description": "One-year apprenticeship programme for graduates and diploma holders in engineering, providing on-the-job training with a monthly stipend from the Government of India.",
        "tags": ["nats", "apprenticeship", "govt", "stipend", "engineering"],
        "domain": "govt-scheme",
        "type": "govt-scheme",
    },
    {
        "id": 6,
        "title": "National Apprenticeship Promotion Scheme (NAPS)",
        "url": "https://www.apprenticeshipindia.gov.in",
        "description": "Government scheme promoting apprenticeship training by sharing 25% of prescribed stipend (up to Rs 1500/month) with employers to encourage hiring apprentices.",
        "tags": ["naps", "apprenticeship", "govt", "stipend", "industry"],
        "domain": "govt-scheme",
        "type": "govt-scheme",
    },
    {
        "id": 7,
        "title": "PM Vidyalaxmi — Education Loan & Financial Support",
        "url": "https://www.vidyalakshmi.co.in",
        "description": "Central government portal for students to apply for education loans from multiple banks and access government scholarships in one place.",
        "tags": ["education-loan", "govt", "scholarship", "financial-aid"],
        "domain": "govt-scheme",
        "type": "govt-scheme",
    },

    # ── Free Course Platforms (domain: "course") ─────────────────────────
    {
        "id": 8,
        "title": "SWAYAM — Free Online Courses from IITs & IIMs",
        "url": "https://swayam.gov.in",
        "description": "India's national MOOC platform with thousands of free courses from IITs, IIMs, and central universities. Covers engineering, humanities, sciences, and management with optional paid certificates.",
        "tags": ["swayam", "mooc", "free", "iit", "iim", "certification"],
        "domain": "course",
        "type": "course",
    },
    {
        "id": 9,
        "title": "NPTEL — Computer Science Courses",
        "url": "https://nptel.ac.in/courses/106",
        "description": "Free IIT-taught Computer Science courses covering Data Structures, Algorithms, Operating Systems, DBMS, Computer Networks, and more with certification exams.",
        "tags": ["nptel", "cs", "iit", "free", "engineering", "certification"],
        "domain": "course",
        "type": "course",
    },
    {
        "id": 10,
        "title": "NPTEL — Data Science & Machine Learning Courses",
        "url": "https://nptel.ac.in/courses/108",
        "description": "Free IIT-taught courses on Data Science, Machine Learning, Deep Learning, NLP, and AI with industry-recognised NPTEL certification.",
        "tags": ["nptel", "data-science", "ml", "ai", "iit", "free"],
        "domain": "course",
        "type": "course",
    },
    {
        "id": 11,
        "title": "NPTEL — Artificial Intelligence Courses",
        "url": "https://nptel.ac.in/courses/106106224",
        "description": "Introduction to AI covering search algorithms, knowledge representation, planning, and machine learning fundamentals taught by IIT Madras professors.",
        "tags": ["nptel", "ai", "iit-madras", "free", "certification"],
        "domain": "course",
        "type": "course",
    },
    {
        "id": 12,
        "title": "Coursera — Google Career Certificates (Financial Aid Available)",
        "url": "https://www.coursera.org/google-career-certificates",
        "description": "Google's professional certificates in Data Analytics, IT Support, UX Design, Project Management, Cybersecurity, and Digital Marketing. Financial aid available for free access.",
        "tags": ["coursera", "google", "certificate", "financial-aid", "career"],
        "domain": "course",
        "type": "course",
    },
    {
        "id": 13,
        "title": "Coursera — IBM Data Science Professional Certificate",
        "url": "https://www.coursera.org/professional-certificates/ibm-data-science",
        "description": "Nine-course IBM specialization covering Python, SQL, data visualization, machine learning, and capstone project. Financial aid available for free access.",
        "tags": ["coursera", "ibm", "data-science", "python", "financial-aid"],
        "domain": "course",
        "type": "course",
    },
    {
        "id": 14,
        "title": "Coursera — Meta Front-End Developer Certificate",
        "url": "https://www.coursera.org/professional-certificates/meta-front-end-developer",
        "description": "Meta's professional certificate covering HTML, CSS, JavaScript, React, and UX/UI design. Prepares for entry-level front-end developer roles. Financial aid available.",
        "tags": ["coursera", "meta", "frontend", "react", "javascript", "financial-aid"],
        "domain": "course",
        "type": "course",
    },
    {
        "id": 15,
        "title": "edX — Harvard CS50: Introduction to Computer Science",
        "url": "https://www.edx.org/learn/computer-science/harvard-university-cs50-s-introduction-to-computer-science",
        "description": "Harvard's legendary intro CS course covering C, Python, SQL, web development, and computer science fundamentals. Completely free to audit with optional paid certificate.",
        "tags": ["edx", "harvard", "cs50", "free", "beginner", "programming"],
        "domain": "course",
        "type": "course",
    },
    {
        "id": 16,
        "title": "edX — MIT Introduction to Computer Science and Programming Using Python",
        "url": "https://www.edx.org/learn/computer-science/massachusetts-institute-of-technology-introduction-to-computer-science-and-programming-using-python",
        "description": "MIT's flagship Python programming course (6.00.1x) covering computational thinking, data structures, algorithms, and testing. Free to audit.",
        "tags": ["edx", "mit", "python", "free", "beginner", "algorithms"],
        "domain": "course",
        "type": "course",
    },
    {
        "id": 17,
        "title": "freeCodeCamp — Full Stack Web Development Curriculum",
        "url": "https://www.freecodecamp.org",
        "description": "Completely free, self-paced coding curriculum with 3,000+ hours covering HTML/CSS, JavaScript, React, Node.js, Python, data science, and machine learning with project-based certification.",
        "tags": ["freecodecamp", "free", "web-dev", "javascript", "python", "certification"],
        "domain": "course",
        "type": "course",
    },
    {
        "id": 18,
        "title": "Khan Academy — Computing & Math Courses",
        "url": "https://www.khanacademy.org/computing",
        "description": "Free courses in computer programming, computer science theory, algorithms, and mathematics. Includes interactive coding challenges and progress tracking.",
        "tags": ["khan-academy", "free", "programming", "math", "beginner"],
        "domain": "course",
        "type": "course",
    },
    {
        "id": 19,
        "title": "MIT OpenCourseWare — Free University-Level Courses",
        "url": "https://ocw.mit.edu",
        "description": "Free lecture notes, exams, and videos from 2,500+ MIT courses across engineering, computer science, mathematics, and sciences.",
        "tags": ["mit", "ocw", "free", "engineering", "cs", "lecture-notes"],
        "domain": "course",
        "type": "course",
    },
    {
        "id": 20,
        "title": "The Odin Project — Full Stack Web Development",
        "url": "https://www.theodinproject.com",
        "description": "Free, open-source full-stack curriculum covering HTML, CSS, JavaScript, React, Node.js, Ruby on Rails, and Git with real-world projects.",
        "tags": ["odin-project", "free", "web-dev", "fullstack", "javascript", "ruby"],
        "domain": "course",
        "type": "course",
    },

    # ── Career Resources (domain: "career") ──────────────────────────────
    {
        "id": 21,
        "title": "Harvard Resume & Cover Letter Guide",
        "url": "https://hwpi.harvard.edu/files/ocs/files/hes-resume-cover-letter-guide.pdf",
        "description": "Harvard Extension School's comprehensive guide to building effective resumes and cover letters, with templates, action verbs, and formatting best practices.",
        "tags": ["resume", "cover-letter", "harvard", "templates", "job-search"],
        "domain": "career",
        "type": "guide",
    },
    {
        "id": 22,
        "title": "Tech Interview Handbook — Coding Interview Preparation",
        "url": "https://www.techinterviewhandbook.org",
        "description": "Free, curated guide for software engineering interviews covering algorithms, system design, behavioral questions, resume tips, and negotiation strategies.",
        "tags": ["interview", "coding", "algorithms", "system-design", "tech"],
        "domain": "career",
        "type": "guide",
    },
    {
        "id": 23,
        "title": "LeetCode — Coding Practice & Interview Prep",
        "url": "https://leetcode.com",
        "description": "Platform with 2,500+ coding problems organized by topic and difficulty. Includes company-tagged questions, contests, and discussion forums for placement preparation.",
        "tags": ["leetcode", "coding", "interview", "dsa", "practice", "placement"],
        "domain": "career",
        "type": "tool",
    },
    {
        "id": 24,
        "title": "LinkedIn Profile Optimization Guide",
        "url": "https://university.linkedin.com/content/dam/university/global/en_US/site/pdf/TipsforBuildingaGreatLinkedInProfile.pdf",
        "description": "Official LinkedIn guide for students to optimize their profiles, including headline writing, summary crafting, skill endorsements, and networking strategies.",
        "tags": ["linkedin", "profile", "networking", "professional-branding"],
        "domain": "career",
        "type": "guide",
    },
    {
        "id": 25,
        "title": "GitHub Student Developer Pack",
        "url": "https://education.github.com/pack",
        "description": "Free developer tools and credits for verified students including GitHub Pro, cloud credits, domain names, CI/CD tools, and IDE licenses to build a strong portfolio.",
        "tags": ["github", "student", "free-tools", "portfolio", "developer"],
        "domain": "career",
        "type": "tool",
    },
    {
        "id": 26,
        "title": "How to Build a GitHub Portfolio That Gets You Hired",
        "url": "https://docs.github.com/en/account-and-profile/setting-up-and-managing-your-github-profile/customizing-your-profile/managing-your-profile-readme",
        "description": "Guide to creating an impressive GitHub profile README, pinning best repositories, writing good documentation, and showcasing projects to recruiters.",
        "tags": ["github", "portfolio", "readme", "projects", "recruiter"],
        "domain": "career",
        "type": "guide",
    },
    {
        "id": 27,
        "title": "Naukri Campus — Fresher Jobs & Placement Resources",
        "url": "https://www.naukri.com/campus",
        "description": "India-focused job portal for freshers and campus placements with resume builder, skill assessments, and company-wise interview experiences.",
        "tags": ["naukri", "jobs", "freshers", "placement", "india", "resume"],
        "domain": "career",
        "type": "tool",
    },
    {
        "id": 28,
        "title": "InterviewBit — Interview Preparation & Practice",
        "url": "https://www.interviewbit.com",
        "description": "Structured interview preparation platform with curated coding problems, system design modules, MCQ practice, and company-wise preparation tracks.",
        "tags": ["interview", "coding", "system-design", "placement", "practice"],
        "domain": "career",
        "type": "tool",
    },

    # ── Mental Health / Wellbeing Resources (domain: "wellbeing") ─────────
    {
        "id": 29,
        "title": "iCall — Psychosocial Helpline by TISS",
        "url": "https://icallhelpline.org",
        "description": "Free telephone and email-based counselling service by TISS (Tata Institute of Social Sciences) for individuals in emotional and psychological distress. Call 9152987821, Mon-Sat 8am-10pm.",
        "tags": ["icall", "helpline", "counselling", "free", "tiss", "crisis"],
        "domain": "wellbeing",
        "type": "helpline",
    },
    {
        "id": 30,
        "title": "Vandrevala Foundation Helpline — 24/7 Mental Health Support",
        "url": "https://www.vandrevalafoundation.com",
        "description": "India's 24/7 free mental health helpline offering support in multiple languages. Call 1860-2662-345 for immediate emotional support and crisis intervention.",
        "tags": ["vandrevala", "helpline", "24x7", "free", "crisis", "multilingual"],
        "domain": "wellbeing",
        "type": "helpline",
    },
    {
        "id": 31,
        "title": "NIMHANS — Student Mental Health Resources",
        "url": "https://nimhans.ac.in",
        "description": "National Institute of Mental Health and Neuro-Sciences resources including self-help guides, psychoeducation materials, and referral pathways for student mental health concerns.",
        "tags": ["nimhans", "mental-health", "self-help", "psychoeducation", "india"],
        "domain": "wellbeing",
        "type": "guide",
    },
    {
        "id": 32,
        "title": "Headspace — Meditation & Mindfulness for Students",
        "url": "https://www.headspace.com/studentplan",
        "description": "Guided meditation and mindfulness app with a discounted student plan. Includes sleep meditations, focus sessions, stress-relief exercises, and SOS sessions for acute anxiety.",
        "tags": ["headspace", "meditation", "mindfulness", "student-discount", "sleep", "anxiety"],
        "domain": "wellbeing",
        "type": "tool",
    },
    {
        "id": 33,
        "title": "UGC Guidelines — Mental Health & Well-being in Higher Education",
        "url": "https://www.ugc.gov.in/pdfnews/0444483_Manodarpan-Guidelines.pdf",
        "description": "UGC's Manodarpan guidelines for establishing campus counselling centres, peer support programmes, and mental health policies in Indian universities and colleges.",
        "tags": ["ugc", "campus-counselling", "guidelines", "policy", "india"],
        "domain": "wellbeing",
        "type": "guide",
    },
    {
        "id": 34,
        "title": "Breathe2Relax — Stress Management Breathing Exercises",
        "url": "https://apps.apple.com/us/app/breathe2relax/id425720246",
        "description": "Evidence-based diaphragmatic breathing exercises for stress management. Developed by the National Center for Telehealth & Technology with guided practice sessions.",
        "tags": ["breathing", "stress-management", "relaxation", "evidence-based"],
        "domain": "wellbeing",
        "type": "tool",
    },
    {
        "id": 35,
        "title": "Student Stress & Time Management Toolkit — Mind (UK)",
        "url": "https://www.mind.org.uk/information-support/tips-for-everyday-living/student-life",
        "description": "Practical strategies for managing academic stress, exam anxiety, time management, and maintaining work-life balance during university life.",
        "tags": ["stress", "time-management", "exam-anxiety", "work-life-balance", "student"],
        "domain": "wellbeing",
        "type": "guide",
    },
    {
        "id": 36,
        "title": "YourDOST — Online Emotional Wellness Platform for Students",
        "url": "https://yourdost.com",
        "description": "India-based emotional wellness platform partnered with 100+ universities offering anonymous chat-based counselling, self-help resources, and expert sessions for students.",
        "tags": ["yourdost", "counselling", "chat", "anonymous", "student", "india"],
        "domain": "wellbeing",
        "type": "tool",
    },
    {
        "id": 37,
        "title": "WHO Self-Help Intervention Guide — Doing What Matters in Times of Stress",
        "url": "https://www.who.int/publications/i/item/9789240003927",
        "description": "World Health Organization's illustrated self-help guide teaching grounding, unhooking from difficult thoughts, acting on values, and building resilience during stressful periods.",
        "tags": ["who", "self-help", "stress", "resilience", "grounding", "free"],
        "domain": "wellbeing",
        "type": "guide",
    },
    {
        "id": 38,
        "title": "Insight Timer — Free Meditation & Sleep App",
        "url": "https://insighttimer.com",
        "description": "World's largest free meditation library with 130,000+ guided meditations, sleep music, yoga nidra, and courses on anxiety management, focus, and self-compassion.",
        "tags": ["meditation", "sleep", "free", "mindfulness", "yoga-nidra", "anxiety"],
        "domain": "wellbeing",
        "type": "tool",
    },
]


def _generate_demo_seed():
    """Create resources_seed.json from the curated SEED_RESOURCES list."""
    SEED_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(SEED_PATH, "w") as f:
        json.dump(SEED_RESOURCES, f, indent=2)
    print(f"Generated {len(SEED_RESOURCES)} curated resources at {SEED_PATH}")


if __name__ == "__main__":
    asyncio.run(build())
