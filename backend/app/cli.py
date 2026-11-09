import sys

from dotenv import load_dotenv

load_dotenv()
sys.stdout.reconfigure(encoding="utf-8")
sys.stderr.reconfigure(encoding="utf-8")

from app.crew import EngineeringTeam  # noqa: E402

REQUIREMENTS = (
    "A simple habit tracker. Users create habits, check them off each day, "
    "and see current streaks. Prevent duplicate check-ins on the same day."
)

if __name__ == "__main__":
    result = EngineeringTeam().crew().kickoff(inputs={"requirements": REQUIREMENTS})
    print(result.raw)
