# backend/app/api/v1/endpoints.py
import os
import json
from openai import OpenAI
from fastapi import APIRouter
from dotenv import load_dotenv
from app.schemas.resume import ResumeCreate, ResumeResponse
import uuid

load_dotenv()
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

client = None
if GROQ_API_KEY:
    try:
        client = OpenAI(
            api_key=GROQ_API_KEY,
            base_url="https://api.groq.com/openai/v1",
        )
    except Exception as e:
        print(f"❌ Client Setup Error: {e}")

router = APIRouter()

@router.post("/create-resume", response_model=ResumeResponse)
def create_resume(data: ResumeCreate):
    
    ai_enhanced_data = data.model_dump()
    
    try:
        if not client:
            raise Exception("API Key Missing")

        # 🔥 FIXED PROMPT: Projects Generate honge agar missing hain
        prompt = f"""
        You are an Expert Resume Writer.
        
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
        - Return ONLY valid JSON matching the input structure.
        """

        chat_completion = client.chat.completions.create(
            messages=[
                {"role": "system", "content": "You are a JSON-only bot. Output strictly valid JSON."},
                {"role": "user", "content": prompt}
            ],
            model="llama-3.3-70b-versatile",
            response_format={"type": "json_object"}
        )
        
        ai_response_text = chat_completion.choices[0].message.content.strip()
        enhanced_json = json.loads(ai_response_text)
        
        # --- MERGING & CLEANING ---
        
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
