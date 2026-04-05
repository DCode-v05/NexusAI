"""Seed student and counselor accounts with behavior + survey data.

Run: cd backend && uv run python scripts/seed_demo.py

Survey questions:
  q1: "I've been feeling anxious or worried"   -> high = HIGH distress
  q2: "I've been feeling low or sad"            -> high = HIGH distress
  q3: "I've been able to concentrate on tasks"  -> high = LOW distress (inverted)
"""
import asyncio
import httpx

BASE = "http://localhost:8000"

PERSONAS = [
    {
        "email": "abinesh@gmail.com",
        "password": "Abinesh@123",
        "role": "student",
        "behavior": {
            "session_gap_days": 1.0,
            "survey_skip_streak": 0,
            "avg_session_length": 42.0,
            "assignment_delay_hrs": 3.0,
            "chat_initiation_freq": 3.5,
            "mood_score_trend": 0.2,
            "login_hour_variance": 1.5,
        },
        "survey": {"q1_score": 3, "q2_score": 2, "q3_score": 8, "free_text": "Feeling good, focused on project work."},
        "desc": "Abinesh — low risk",
    },
    {
        "email": "denistan@gmail.com",
        "password": "Denistan@123",
        "role": "student",
        "behavior": {
            "session_gap_days": 3.0,
            "survey_skip_streak": 2,
            "avg_session_length": 22.0,
            "assignment_delay_hrs": 16.0,
            "chat_initiation_freq": 1.0,
            "mood_score_trend": -0.4,
            "login_hour_variance": 4.5,
        },
        "survey": {"q1_score": 6, "q2_score": 5, "q3_score": 4, "free_text": "Struggling with deadlines, feeling stressed."},
        "desc": "Denistan — moderate risk",
    },
    {
        "email": "danushika@gmail.com",
        "password": "Danushika@123",
        "role": "student",
        "behavior": {
            "session_gap_days": 6.0,
            "survey_skip_streak": 5,
            "avg_session_length": 8.0,
            "assignment_delay_hrs": 38.0,
            "chat_initiation_freq": 0.3,
            "mood_score_trend": -0.7,
            "login_hour_variance": 9.0,
        },
        "survey": {"q1_score": 8, "q2_score": 9, "q3_score": 2, "free_text": "Can't sleep, very overwhelmed with everything."},
        "desc": "Danushika — high risk",
    },
    {
        "email": "yazhini@gmail.com",
        "password": "Yazhini@123",
        "role": "student",
        "behavior": {
            "session_gap_days": 9.0,
            "survey_skip_streak": 7,
            "avg_session_length": 4.0,
            "assignment_delay_hrs": 48.0,
            "chat_initiation_freq": 0.0,
            "mood_score_trend": -1.0,
            "login_hour_variance": 11.0,
        },
        "survey": {"q1_score": 10, "q2_score": 10, "q3_score": 1, "free_text": "I feel hopeless. Nothing matters anymore."},
        "desc": "Yazhini — crisis risk",
    },
    {
        "email": "qernels@gmail.com",
        "password": "Qernels@123",
        "role": "counselor",
        "behavior": None,
        "survey": None,
        "desc": "Qernels — counselor account",
    },
]


async def seed():
    async with httpx.AsyncClient(base_url=BASE, timeout=30.0) as client:
        for p in PERSONAS:
            print(f"\n-> {p['desc']}: {p['email']}")

            # Register
            try:
                r = await client.post("/auth/register", json={
                    "email": p["email"],
                    "password": p["password"],
                    "role": p["role"],
                })
                if r.status_code in (200, 201):
                    print(f"  OK Registered")
                else:
                    print(f"  Already exists ({r.status_code})")
            except Exception as e:
                print(f"  Register error: {e}")
                continue

            if p["role"] == "counselor":
                print(f"  OK Counselor account ready")
                continue

            # Login
            try:
                form = f"username={p['email']}&password={p['password']}"
                r = await client.post("/auth/login", content=form,
                    headers={"Content-Type": "application/x-www-form-urlencoded"})
                token = r.json()["access_token"]
                headers = {"Authorization": f"Bearer {token}"}
            except Exception as e:
                print(f"  Login error: {e}")
                continue

            # Log behavior
            if p["behavior"]:
                try:
                    r = await client.post("/students/behavior-log", json=p["behavior"], headers=headers)
                    print(f"  OK Behavior logged")
                except Exception as e:
                    print(f"  Behavior error: {e}")

            # Submit survey (triggers risk scoring + counselor alert for high/crisis)
            if p["survey"]:
                try:
                    r = await client.post("/wellbeing/survey", json=p["survey"], headers=headers)
                    data = r.json()
                    tier = data.get('tier', '?')
                    score = data.get('score', 0)
                    print(f"  OK Survey -- risk: {tier} ({score:.2f})")
                    if tier in ('high', 'crisis'):
                        print(f"  !! Counselor alert created!")
                except Exception as e:
                    print(f"  Survey error: {e}")

    print("\n" + "=" * 50)
    print("Seed complete!")
    print("=" * 50)
    print("\nAccounts:")
    print("  Students:")
    print("    abinesh@gmail.com / Abinesh@123")
    print("    denistan@gmail.com / Denistan@123")
    print("    danushika@gmail.com / Danushika@123")
    print("    yazhini@gmail.com / Yazhini@123")
    print("  Counselor:")
    print("    qernels@gmail.com / Qernels@123")


if __name__ == "__main__":
    asyncio.run(seed())
