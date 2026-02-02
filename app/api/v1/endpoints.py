# backend/app/api/v1/endpoints.py
import os
import json
from openai import OpenAI
from fastapi import APIRouter
from dotenv import load_dotenv
from app.schemas.resume import ResumeCreate, ResumeResponse
import uuid

load_dotenv()
# ⚠️ Make sure to add OPENAI_API_KEY in Render Dashboard
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

router = APIRouter()


@router.post("/create-resume", response_model=ResumeResponse)
def create_resume(data: ResumeCreate):
    
    ai_enhanced_data = data.model_dump()
    
    try:
        if not OPENAI_API_KEY:
            print("⚠️ OpenAI Key Missing - Skipping AI")
            return {"id": str(uuid.uuid4()), **ai_enhanced_data}

        client = OpenAI(api_key=OPENAI_API_KEY)

        # 🔥 PROMPT
        prompt = f"""
        You are an Expert Resume Writer. Output strictly valid JSON.
        
        USER INPUT DATA:
        {json.dumps(data.model_dump(), default=str)}

        YOUR TASKS:
        1. **SUMMARY:** Write a professional summary.
        2. **EXPERIENCE:** - Use key "title" for Job Title.
           - If NO experience provided, GENERATE 1 generic entry relevant to the job.
           - Keep dates empty string "" if not provided.
        3. **PROJECTS:** - Use key "title" for Project Name.
           - If EMPTY, GENERATE 2 impressive projects.
        4. **SKILLS:** Generate 6-8 relevant skills if missing.

        OUTPUT FORMAT:
        - Return ONLY valid JSON matching the input structure. 
        """

        # 🔥 Using gpt-4o-mini (Best 'Nano' equivalent currently available)
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a helpful assistant designed to output JSON."},
                {"role": "user", "content": prompt}
            ],
            response_format={"type": "json_object"}
        )
        
        ai_response_text = response.choices[0].message.content.strip()
        enhanced_json = json.loads(ai_response_text)
        
        # --- SMART MERGING & FIXING (Preserved to prevent 500 Error) ---
        
        # 1. Summary
        if "summary" in enhanced_json: 
            ai_enhanced_data["summary"] = enhanced_json["summary"]

        # 2. Skills
        if "skills" in enhanced_json:
            user_skills = set(data.skills)
            ai_skills = set(enhanced_json["skills"])
            ai_enhanced_data["skills"] = list(user_skills.union(ai_skills))

        # 3. Experience
        if "experience" in enhanced_json:
            clean_exp = []
            for exp in enhanced_json["experience"]:
                # 🔥 FIX: AI sometimes calls it 'role' or 'job_title'
                if "title" not in exp:
                    if "role" in exp: exp["title"] = exp.pop("role")
                    elif "job_title" in exp: exp["title"] = exp.pop("job_title")
                    elif "position" in exp: exp["title"] = exp.pop("position")
                    else: exp["title"] = "Professional Role"

                # Company Fix
                if "company" not in exp or not exp["company"]: 
                    exp["company"] = "Freelance / Independent Project"
                
                # Date Fix
                if "start_date" not in exp: exp["start_date"] = ""
                if "end_date" not in exp: exp["end_date"] = ""
                
                # Description Fix
                if "description" in exp and isinstance(exp["description"], list):
                     exp["description"] = "\n• ".join(exp["description"])
                
                if "description" not in exp: exp["description"] = ""

                clean_exp.append(exp)
            
            if not data.experience or (data.experience and clean_exp):
                 ai_enhanced_data["experience"] = clean_exp

        # 4. Projects
        if "projects" in enhanced_json:
            clean_proj = []
            for proj in enhanced_json["projects"]:
                # 🔥 FIX: AI sometimes calls it 'name' or 'project_name'
                if "title" not in proj:
                    if "name" in proj: proj["title"] = proj.pop("name")
                    elif "project_name" in proj: proj["title"] = proj.pop("project_name")
                    else: proj["title"] = "Project"

                if "description" in proj and isinstance(proj["description"], list):
                     proj["description"] = "\n• ".join(proj["description"])
                
                if "description" not in proj: proj["description"] = ""
                
                clean_proj.append(proj)
            
            if not data.projects or (data.projects and clean_proj):
                ai_enhanced_data["projects"] = clean_proj
            
        if "languages" in enhanced_json and not data.languages:
             ai_enhanced_data["languages"] = ["English", "Hindi"]

    except Exception as e:
        print(f"❌ AI Error: {e}")
        return {"id": str(uuid.uuid4()), **ai_enhanced_data}
    
    return {
        "id": str(uuid.uuid4()),
        **ai_enhanced_data
    }

