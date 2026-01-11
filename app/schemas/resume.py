from pydantic import BaseModel, EmailStr
from typing import List, Optional

# 1. Sub-Models
class Experience(BaseModel):
    title: str
    company: str
    start_date: Optional[str] = None
    end_date: Optional[str] = "Present"
    description: Optional[str] = None

class Education(BaseModel):
    degree: str
    school: str
    # ✅ FIX: Flutter ab dates bhej raha hai, 'year' hata kar start/end date lagaya
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    grade: Optional[str] = None

class Project(BaseModel):
    title: str
    description: Optional[str] = None
    link: Optional[str] = None

class Certificate(BaseModel):
    title: str
    issuer: str
    year: str

# 2. Main Resume Model (A to Z Details)
class ResumeCreate(BaseModel):
    # Personal Info
    full_name: str
    email: EmailStr
    mobile: Optional[str] = None
    address: Optional[str] = None
    linkedin_url: Optional[str] = None # ✅ LinkedIn Link Added
    photo_url: Optional[str] = None 
    
    # Sections
    summary: Optional[str] = None
    skills: List[str] = []
    languages: List[str] = []
    
    # Lists
    experience: List[Experience] = []
    education: List[Education] = []
    projects: List[Project] = []
    certificates: List[Certificate] = []
    awards: List[str] = []

class ResumeResponse(ResumeCreate):
    id: str
