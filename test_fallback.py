import sys, os
sys.path.insert(0, os.path.abspath("."))

SAMPLE_JD = """
We are looking for a Senior Python Developer with experience in FastAPI,
PostgreSQL, Docker, REST APIs, machine learning, AWS, CI/CD, React, TypeScript.
"""

print("\n--- TEST 1: Hallucination detector (no API needed) ---")
from app.services.gemini import _is_hallucinated
good = [{"tag":"python","weight":0.9},{"tag":"fastapi","weight":0.8},{"tag":"docker","weight":0.7},{"tag":"aws","weight":0.6},{"tag":"react","weight":0.5}]
bad  = [{"tag":"blockchain","weight":0.9},{"tag":"solidity","weight":0.8},{"tag":"rust","weight":0.7},{"tag":"golang","weight":0.6},{"tag":"swift","weight":0.5},{"tag":"kotlin","weight":0.4}]
tiny = [{"tag":"python","weight":0.9}]
print("PASS" if not _is_hallucinated(good, SAMPLE_JD) else "FAIL", " good tags accepted")
print("PASS" if     _is_hallucinated(bad,  SAMPLE_JD) else "FAIL", " invented tags flagged")
print("PASS" if     _is_hallucinated(tiny, SAMPLE_JD) else "FAIL", " too-few tags flagged")

print("\n--- TEST 2: Regex fallback (no API needed) ---")
from app.services.gemini import _fallback_tags
tags = _fallback_tags(SAMPLE_JD)
print(f"PASS  Got {len(tags)} tags via regex:", [t["tag"] for t in tags[:5]])

print("\n--- TEST 3: Live Gemini call (uses your .env key) ---")
from app.services.gemini import generate_tags
tags = generate_tags(SAMPLE_JD)
print(f"PASS  Got {len(tags)} tags:", [t["tag"] for t in tags[:5]])
