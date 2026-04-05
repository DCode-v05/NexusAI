import asyncio
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from src.pathway import models, schemas
from src.students.service import get_student_by_user


async def get_or_create_skill_profile(db: AsyncSession, student_id: int) -> models.SkillProfile:
    result = await db.execute(select(models.SkillProfile).where(models.SkillProfile.student_id == student_id))
    profile = result.scalar_one_or_none()
    if not profile:
        profile = models.SkillProfile(student_id=student_id, skills=[])
        db.add(profile)
        await db.commit()
        await db.refresh(profile)
    return profile


async def parse_resume(db: AsyncSession, user_id: int, file_bytes: bytes) -> schemas.SkillProfileResponse:
    """Extract skills from resume PDF using spaCy NER."""
    import spacy
    import io

    student = await get_student_by_user(db, user_id)

    # Extract text from PDF
    try:
        import PyPDF2
        reader = PyPDF2.PdfReader(io.BytesIO(file_bytes))
        text = " ".join(page.extract_text() or "" for page in reader.pages)
    except Exception:
        text = file_bytes.decode("utf-8", errors="ignore")

    # Extract skills via spaCy (run in thread pool — CPU-bound)
    def _extract(text: str) -> list[str]:
        try:
            nlp = spacy.load("en_core_web_sm")
        except OSError:
            # Fallback: simple keyword extraction
            skill_keywords = [
                "Python", "Java", "JavaScript", "TypeScript", "React", "FastAPI",
                "SQL", "PostgreSQL", "Docker", "AWS", "ML", "Machine Learning",
                "Deep Learning", "NLP", "TensorFlow", "PyTorch", "scikit-learn",
                "Git", "Linux", "REST API", "GraphQL", "Redis", "MongoDB",
            ]
            return [kw for kw in skill_keywords if kw.lower() in text.lower()]

        doc = nlp(text[:50000])
        # Skills are typically NOUN phrases or ORG/PRODUCT entities
        skills = set()
        for ent in doc.ents:
            if ent.label_ in ("ORG", "PRODUCT", "GPE"):
                skills.add(ent.text.strip())
        # Also extract noun chunks that look like tech terms
        for chunk in doc.noun_chunks:
            if len(chunk.text.split()) <= 3 and chunk.text[0].isupper():
                skills.add(chunk.text.strip())
        return list(skills)[:50]

    loop = asyncio.get_event_loop()
    skills = await loop.run_in_executor(None, _extract, text)

    profile = await get_or_create_skill_profile(db, student.id)
    profile.skills = skills
    profile.raw_resume_text = text[:5000]
    await db.commit()
    await db.refresh(profile)

    return schemas.SkillProfileResponse.model_validate(profile)


def _build_template_roadmap(skills: list[str], target_role: str) -> dict:
    """Generate a structured 12-week roadmap without LLM."""
    role_lower = target_role.lower()

    # Determine skill gaps based on role
    role_skill_map = {
        "software engineer": ["DSA", "System Design", "REST APIs", "Git", "SQL", "Testing", "CI/CD", "Docker"],
        "data scientist": ["Python", "Statistics", "Pandas", "SQL", "ML Algorithms", "Scikit-learn", "Deep Learning", "Data Visualization"],
        "frontend developer": ["HTML/CSS", "JavaScript", "React", "TypeScript", "Responsive Design", "Testing", "Performance", "Accessibility"],
        "backend developer": ["Python/Node.js", "REST APIs", "Databases", "Authentication", "Caching", "Message Queues", "Docker", "System Design"],
        "ml engineer": ["Python", "Linear Algebra", "ML Algorithms", "TensorFlow/PyTorch", "MLOps", "Data Pipelines", "Model Deployment", "Monitoring"],
        "devops engineer": ["Linux", "Docker", "Kubernetes", "CI/CD", "Cloud (AWS/GCP)", "Terraform", "Monitoring", "Security"],
        "full stack developer": ["HTML/CSS/JS", "React", "Node.js/Python", "REST APIs", "SQL", "Git", "Docker", "Deployment"],
    }

    # Find best matching role
    required_skills = role_skill_map.get("software engineer", [])
    for key, val in role_skill_map.items():
        if key in role_lower or role_lower in key:
            required_skills = val
            break

    current_set = {s.lower() for s in (skills or [])}
    skill_gaps = [s for s in required_skills if s.lower() not in current_set]

    weeks = [
        {"week": 1, "title": f"Foundation & Goal Setting for {target_role}",
         "tasks": [f"Assess current skill levels in {', '.join(skills[:3]) if skills else 'core areas'}", "Set up development environment and tools", "Create a GitHub portfolio repository", "Research job requirements and industry trends"],
         "resources": [], "milestone": "Development environment ready and learning plan set"},
        {"week": 2, "title": f"Core Fundamentals – {skill_gaps[0] if skill_gaps else 'Programming Basics'}",
         "tasks": [f"Deep dive into {skill_gaps[0] if skill_gaps else 'core programming concepts'}", "Complete 10 practice problems on LeetCode/HackerRank", "Read documentation and best practices", "Build a small practice project"],
         "resources": [], "milestone": f"Solid foundation in {skill_gaps[0] if skill_gaps else 'fundamentals'}"},
        {"week": 3, "title": f"Core Fundamentals – {skill_gaps[1] if len(skill_gaps) > 1 else 'Data Structures'}",
         "tasks": [f"Study {skill_gaps[1] if len(skill_gaps) > 1 else 'data structures and algorithms'}", "Implement common patterns from scratch", "Solve 15 medium-difficulty coding challenges", "Document learnings in a blog post"],
         "resources": [], "milestone": "Comfortable with core data structures"},
        {"week": 4, "title": f"Building Skills – {skill_gaps[2] if len(skill_gaps) > 2 else 'APIs & Integration'}",
         "tasks": [f"Learn {skill_gaps[2] if len(skill_gaps) > 2 else 'API design and integration'}", "Build a CRUD application with authentication", "Practice writing clean, testable code", "Review open-source projects for patterns"],
         "resources": [], "milestone": "Working CRUD application completed"},
        {"week": 5, "title": "Project Phase 1 – Planning & Architecture",
         "tasks": [f"Design architecture for a {target_role}-focused portfolio project", "Create wireframes and system design diagrams", "Set up project structure with best practices", "Implement core data models and database schema"],
         "resources": [], "milestone": "Project architecture finalized and scaffolded"},
        {"week": 6, "title": "Project Phase 2 – Core Implementation",
         "tasks": ["Implement main features of portfolio project", "Write unit tests for critical paths", "Set up CI/CD pipeline with GitHub Actions", "Practice code review with peers"],
         "resources": [], "milestone": "Core features implemented with tests"},
        {"week": 7, "title": f"Advanced Topic – {skill_gaps[3] if len(skill_gaps) > 3 else 'System Design'}",
         "tasks": [f"Study {skill_gaps[3] if len(skill_gaps) > 3 else 'system design fundamentals'}", "Design solutions for common architecture problems", "Add advanced features to portfolio project", "Practice whiteboard/system design interviews"],
         "resources": [], "milestone": "Can discuss system design trade-offs confidently"},
        {"week": 8, "title": "Project Phase 3 – Polish & Deploy",
         "tasks": ["Complete all features and fix bugs", "Deploy project to cloud (Vercel/Railway/AWS)", "Write comprehensive README with screenshots", "Add project to portfolio website"],
         "resources": [], "milestone": "Portfolio project live and deployed"},
        {"week": 9, "title": f"Industry Skills – {skill_gaps[4] if len(skill_gaps) > 4 else 'DevOps & Deployment'}",
         "tasks": [f"Learn {skill_gaps[4] if len(skill_gaps) > 4 else 'containerization and deployment'}", "Practice with Docker and cloud services", "Study monitoring and logging best practices", "Contribute to an open-source project"],
         "resources": [], "milestone": "Comfortable with deployment workflows"},
        {"week": 10, "title": "Resume & Profile Optimization",
         "tasks": [f"Tailor resume for {target_role} positions", "Optimize LinkedIn profile with relevant keywords", "Prepare 2-minute project pitch for each portfolio item", "Apply to 10 relevant positions on LinkedIn/Naukri"],
         "resources": [], "milestone": "Resume and profiles optimized, applications started"},
        {"week": 11, "title": "Interview Preparation",
         "tasks": ["Practice 5 coding problems daily on LeetCode", f"Prepare behavioral stories using STAR method for {target_role}", "Do 2 mock interviews with peers or on Pramp", "Research target companies and their tech stacks"],
         "resources": [], "milestone": "Confident in technical and behavioral interviews"},
        {"week": 12, "title": "Final Sprint & Job Applications",
         "tasks": ["Apply to 15+ positions at target companies (TCS, Infosys, startups, MAANG India)", "Follow up on pending applications", "Continue daily coding practice", "Network on LinkedIn – connect with engineers at target companies"],
         "resources": [], "milestone": "Active pipeline of job applications with interview callbacks"},
    ]

    return {"raw": "", "weeks": weeks, "skill_gaps": skill_gaps}


async def _enrich_weeks_with_rag(weeks: list[dict], skills: list[str], target_role: str) -> None:
    """Fetch relevant resources from RAG and populate the `resources` list in each week.

    Retrieves two batches:
    - Courses/learning resources for skill-building weeks (1–9)
    - Career resources for job-search weeks (10–12)
    Silently skips if the RAG system is unavailable.
    """
    try:
        import sys
        from pathlib import Path
        project_root = Path(__file__).parent.parent.parent.parent
        if str(project_root) not in sys.path:
            sys.path.insert(0, str(project_root))

        from rag.retriever import ResourceRetriever
        retriever = ResourceRetriever()

        skill_query = f"{target_role} {' '.join(skills[:3])} online course certification"
        career_query = f"{target_role} career resume interview job India"

        course_resources, career_resources = await asyncio.gather(
            retriever.retrieve(skill_query, top_k=6, domain_filter="course"),
            retriever.retrieve(career_query, top_k=3, domain_filter="career"),
            return_exceptions=True,
        )

        def _to_dict(r) -> dict:
            return {"title": r.title, "url": r.url, "description": r.description}

        if isinstance(course_resources, list) and course_resources:
            # Spread course resources across skill-building weeks (2–9)
            skill_weeks = [w for w in weeks if w["week"] in range(2, 10)]
            for i, week in enumerate(skill_weeks):
                res = course_resources[i % len(course_resources)]
                week["resources"] = [_to_dict(res)]

        if isinstance(career_resources, list) and career_resources:
            # Attach career resources to weeks 10, 11, 12
            for i, week in enumerate(w for w in weeks if w["week"] >= 10):
                if i < len(career_resources):
                    week["resources"] = [_to_dict(career_resources[i])]
    except Exception:
        pass  # RAG unavailable — weeks keep their empty resources list


async def generate_roadmap(
    db: AsyncSession, user_id: int, data: schemas.GenerateRoadmapRequest
) -> schemas.RoadmapResponse:
    from agents.pathway.agent import get_pathway_agent

    student = await get_student_by_user(db, user_id)
    profile = await get_or_create_skill_profile(db, student.id)
    profile.target_role = data.target_role
    profile.target_location = data.target_location
    await db.commit()

    # Try LLM-based generation, fall back to template
    try:
        agent = get_pathway_agent()
        raw = await agent.generate_roadmap(
            current_skills=profile.skills or [],
            target_role=data.target_role,
        )
        # Detect fallback message from LLM router
        if "connectivity issues" in raw or "temporarily" in raw:
            roadmap_data = _build_template_roadmap(profile.skills or [], data.target_role)
        else:
            roadmap_data = {"raw": raw, "weeks": [], "skill_gaps": []}
    except Exception:
        roadmap_data = _build_template_roadmap(profile.skills or [], data.target_role)

    # Enrich week resources from RAG (silently skips if unavailable)
    await _enrich_weeks_with_rag(
        roadmap_data.get("weeks", []),
        profile.skills or [],
        data.target_role,
    )

    # Persist roadmap
    roadmap = models.CareerRoadmap(
        skill_profile_id=profile.id,
        target_role=data.target_role,
        roadmap_json=roadmap_data,
    )
    db.add(roadmap)
    await db.commit()
    await db.refresh(roadmap)

    return schemas.RoadmapResponse(
        id=roadmap.id,
        target_role=roadmap.target_role,
        roadmap=roadmap_data.get("raw", ""),
        weeks=roadmap_data.get("weeks", []),
        skill_gaps=roadmap_data.get("skill_gaps", []),
        generated_at=roadmap.generated_at,
    )
