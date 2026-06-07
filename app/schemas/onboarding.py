from pydantic import BaseModel
from typing import Optional


class OnboardingDocumentsRequest(BaseModel):
    aadhar_number: str
    pan_number: str

    aadhar_file: Optional[str] = ""
    pan_file: Optional[str] = ""

    marksheet_10_file: Optional[str] = ""
    marksheet_12_file: Optional[str] = ""