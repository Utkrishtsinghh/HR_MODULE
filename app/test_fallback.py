"""
Run from your project root:
    python test_fallback.py

Tests the full fallback chain: Gemini → OpenAI → Claude → Regex
"""

import sys
import os
sys.path.insert(0, os.path.abspath("."))

SAMPLE_JD = """
We are looking for a Senior Python Developer with experience in FastAPI, 
PostgreSQL, Docker, and REST APIs. The candidate should have strong knowledge 
of machine learning, data pipelines, AWS cloud services, and CI/CD workflows. 
Experience with React, TypeScript, and agile methodologies is a plus.
"""

def test_normal():
    print("\n" + "="*55)
    print("TEST 1: Normal run (real .env keys)")
    print("="*55)
    from app.services.gemini import generate_tags
    tags = generate_tags(SAMPLE_JD)
    print(f"✅ Got {len(tags)} tags")
    for t in tags[:5]:
        print(f"   {t['tag']:<25} weight={t['weight']}")
    print("   ...")

def test_gemini_fails():
    print("\n" + "="*55)
    print("TEST 2: Gemini key blanked → expects OpenAI or Claude")
    print("="*55)
    from app.core import config as cfg
    original = cfg.settings.gemini_api_key
    cfg.settings.gemini_api_key = "INVALID_KEY_FORCED_FAIL"

    from app.services import gemini as svc
    import importlib; importlib.reload(svc)  

    tags = svc.generate_tags(SAMPLE_JD)
    print(f"✅ Got {len(tags)} tags via backup")
    for t in tags[:5]:
        print(f"   {t['tag']:<25} weight={t['weight']}")
    print("   ...")
    cfg.settings.gemini_api_key = original   

def test_all_fail():
    print("\n" + "="*55)
    print("TEST 3: All keys blanked → expects regex fallback")
    print("="*55)
    from app.core import config as cfg
    orig_g = cfg.settings.gemini_api_key
    orig_o = cfg.settings.openai_api_key
    orig_c = cfg.settings.claude_api_key

    cfg.settings.gemini_api_key = ""
    cfg.settings.openai_api_key = ""
    cfg.settings.claude_api_key = ""

    from app.services import gemini as svc
    import importlib; importlib.reload(svc)

    tags = svc.generate_tags(SAMPLE_JD)
    print(f"✅ Got {len(tags)} tags via REGEX fallback")
    for t in tags[:5]:
        print(f"   {t['tag']:<25} weight={t['weight']}")
    print("   ...")

    cfg.settings.gemini_api_key = orig_g
    cfg.settings.openai_api_key = orig_o
    cfg.settings.claude_api_key = orig_c


def test_hallucination_detector():
    print("\n" + "="*55)
    print("TEST 4: Hallucination detector")
    print("="*55)
    from app.services.gemini import _is_hallucinated

    good_tags = [
        {"tag": "python", "weight": 0.9},
        {"tag": "fastapi", "weight": 0.8},
        {"tag": "postgresql", "weight": 0.7},
        {"tag": "docker", "weight": 0.7},
        {"tag": "aws", "weight": 0.6},
    ]
    result = _is_hallucinated(good_tags, SAMPLE_JD)
    status = "❌ FAIL" if result else "✅ PASS"
    print(f"{status}  Good tags correctly {'flagged' if result else 'accepted'}")

    bad_tags = [
        {"tag": "kubernetes", "weight": 0.9},
        {"tag": "blockchain", "weight": 0.8},
        {"tag": "solidity", "weight": 0.7},
        {"tag": "rust", "weight": 0.6},
        {"tag": "golang", "weight": 0.5},
        {"tag": "swift", "weight": 0.4},
    ]
    result = _is_hallucinated(bad_tags, SAMPLE_JD)
    status = "✅ PASS" if result else "❌ FAIL"
    print(f"{status}  Hallucinated tags correctly {'flagged' if result else 'accepted'}")

    # Should BE flagged — too few tags
    tiny_tags = [{"tag": "python", "weight": 0.9}]
    result = _is_hallucinated(tiny_tags, SAMPLE_JD)
    status = "✅ PASS" if result else "❌ FAIL"
    print(f"{status}  Too-few-tags correctly {'flagged' if result else 'accepted'}")


if __name__ == "__main__":
    import logging
    logging.basicConfig(level=logging.WARNING,
                        format="%(levelname)s  %(name)s  %(message)s")

    test_hallucination_detector()   # pure logic — no API calls
    test_all_fail()                 # regex fallback — no API calls
    test_normal()                   # uses your real .env keys
    test_gemini_fails()             # needs at least OpenAI or Claude key