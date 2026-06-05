import uuid


def generate_meet_link() -> str:
    return f"https://meet.google.com/{uuid.uuid4().hex[:3]}-{uuid.uuid4().hex[3:7]}-{uuid.uuid4().hex[7:10]}"
