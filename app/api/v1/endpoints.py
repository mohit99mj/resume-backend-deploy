# backend/app/api/v1/endpoints.py
import os
import json
import google.generativeai as genai
from fastapi import APIRouter
from dotenv import load_dotenv
from app.schemas.resume import ResumeCreate, ResumeResponse
import uuid

load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# 🔥 Configure Gemini
if GEMINI_API_KEY:
    try:
        genai.configure(api_key=GEMINI_API_KEY)
    except Exception as e:
        print(f"❌ Gemini Setup Error: {e}")

router = APIRouter()

@router.post("/create-resume", response_model=ResumeResponse)
def create_resume(data: ResumeCreate):
    
    ai_enhanced_data = data.model_dump()
    
    try:
        if not GEMINI_API_KEY:
            raise Exception("Gemini API Key Missing")

        # 🔥 Gemini Model Init (Flash model is fast & cheap)
        model = genai.GenerativeModel('gemini-1.5-flash')

        # 🔥 FIXED PROMPT: Same logic as before
        prompt = f"""
        You are an Expert Resume Writer. Output strictly valid JSON.
        
        USER INPUT DATA:
        {json.dumps(data.model_dump(), default=str)}

        YOUR TASKS:
        1. **SUMMARY:** Write a professional summary based on the Job Role.
        
        2. **EXPERIENCE:** - If user provided details, POLISH them.
           - If user provided NO experience, GENERATE generic entries (e.g., "Freelance Project").
           - **DATE RULE:** DO NOT invent dates. If user input dates are empty, keep them EMPTY string ("").
           - **COMPANY RULE:** If company missing, use "Independent Project" or "Freelance".
        
        3. **PROJECTS (IMPORTANT):** - **If the user's project list is EMPTY, GENERATE 2 impressive projects relevant to the job role.**
           - If provided, POLISH descriptions.
           - Use 'title' for Project Name.
        
        4. **SKILLS:** If skills are missing, generate 6-8 relevant skills.

        OUTPUT FORMAT:
        - Return ONLY valid JSON matching the input structure. Do not include markdown code blocks (```json ... ```).
        """

        # 🔥 Gemini Generation Call (Force JSON Mode)
        response = model.generate_content(
            prompt,
            generation_config={"response_mime_type": "application/json"}
        )
        
        ai_response_text = response.text.strip()
        enhanced_json = json.loads(ai_response_text)
        
        # --- MERGING & CLEANING (Same Logic Preserved) ---
        
        if "summary" in enhanced_json: 
            ai_enhanced_data["summary"] = enhanced_json["summary"]

        if "skills" in enhanced_json:
            user_skills = set(data.skills)
            ai_skills = set(enhanced_json["skills"])
            ai_enhanced_data["skills"] = list(user_skills.union(ai_skills))

        if "experience" in enhanced_json:
            clean_exp = []
            for exp in enhanced_json["experience"]:
                if "position" in exp and "title" not in exp: exp["title"] = exp.pop("position")
                
                # Company Fix
                if "company" not in exp or not exp["company"]: 
                    exp["company"] = "Freelance / Independent Project"
                
                # Date Fix (Strict: No Auto-Fill)
                if "start_date" not in exp: exp["start_date"] = ""
                if "end_date" not in exp: exp["end_date"] = ""
                
                # Bullet Points Fix
                if "description" in exp and isinstance(exp["description"], list):
                     exp["description"] = "\n• ".join(exp["description"])
                     if not exp["description"].startswith("•"): exp["description"] = "• " + exp["description"]

                clean_exp.append(exp)
            
            # Agar user ne experience diya tha to update karo, nahi diya tha to AI ka generated lo
            if not data.experience or (data.experience and clean_exp):
                 ai_enhanced_data["experience"] = clean_exp

        # 🔥 PROJECTS LOGIC FIX
        if "projects" in enhanced_json:
            clean_proj = []
            for proj in enhanced_json["projects"]:
                if "name" in proj and "title" not in proj: proj["title"] = proj.pop("name")
                
                if "description" in proj and isinstance(proj["description"], list):
                     proj["description"] = "\n• ".join(proj["description"])
                     if not proj["description"].startswith("•"): proj["description"] = "• " + proj["description"]
                
                clean_proj.append(proj)
            
            # Agar user ne projects nahi diye the, to AI ke generated projects use karo
            if not data.projects or (data.projects and clean_proj):
                ai_enhanced_data["projects"] = clean_proj
            
        if "languages" in enhanced_json and not data.languages:
             ai_enhanced_data["languages"] = ["English", "Hindi"]

    except Exception as e:
        print(f"❌ AI Error: {e}")
    
    return {
        "id": str(uuid.uuid4()),
        **ai_enhanced_data
    }
