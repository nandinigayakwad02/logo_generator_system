import os
import json
import uuid
import datetime
from typing import Optional, List
from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

app = FastAPI(title="AI Logo Generator System - OpenAI Edition")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Ensure required directories exist
LOGOS_DIR = os.path.join(os.path.dirname(__file__), "generated_logos")
STATIC_DIR = os.path.join(os.path.dirname(__file__), "static")
os.makedirs(LOGOS_DIR, exist_ok=True)
os.makedirs(STATIC_DIR, exist_ok=True)

# Initialize OpenAI client
api_key = os.getenv("OPENAI_API_KEY")
client = OpenAI(api_key=api_key) if api_key else None

class IdeaRequest(BaseModel):
    brand_name: str
    description: str
    style: Optional[str] = "minimalist"
    colors: Optional[str] = "modern vibrant"

class GenerateLogoRequest(BaseModel):
    brand_name: str
    description: str
    style: Optional[str] = "minimalist vector"
    colors: Optional[str] = "modern vibrant"
    custom_prompt: Optional[str] = None
    quality: Optional[str] = "standard"
    background: Optional[str] = "transparent"

STYLE_PROMPTS = {
    "minimalist": "Minimalist vector logo mark, ultra-clean geometric lines, single iconic symbol, crisp flat design with elegant negative space, Helvetica-level precision, single-color or two-tone palette",
    "monogram": "Sophisticated monogram logo, interlocking custom letterforms, premium typographic craftsmanship, golden ratio proportions, luxury fashion brand aesthetic, geometric precision",
    "cybertech": "Futuristic cyberpunk tech logo, neon-accented vector emblem, circuit-board geometry integrated into letterforms, holographic gradient feel, sharp angular edges, sci-fi digital aesthetic",
    "vintage": "Hand-crafted vintage emblem logo, ornate linework border, retro badge with banner ribbon, detailed engraving style illustration, aged-ink texture feel, classic Americana or European heritage aesthetic",
    "mascot": "Bold stylized mascot character logo, dynamic pose with personality, clean vector illustration with thick outlines, esports/gaming-grade energy, expressive eyes, vibrant saturated color blocks",
    "abstract": "Abstract geometric logo mark, mathematically precise fluid shape, masterful negative-space storytelling, Saul Bass inspired iconic simplicity, single continuous form",
    "luxury": "Ultra-premium luxury brand logo, editorial serif typography, gold foil accent aesthetic, Chanel/Dior level elegance, minimalist icon with maximal sophistication, high-fashion identity",
    "3d_clay": "Soft 3D clay-morphism glossy logo icon, isometric perspective, smooth rounded surfaces with subtle studio lighting, playful yet professional, vibrant candy-colored palette, Pixar-quality rendering"
}

@app.get("/")
def read_root():
    index_file = os.path.join(STATIC_DIR, "index.html")
    if os.path.exists(index_file):
        return FileResponse(index_file)
    return {"message": "Logo Generator API (OpenAI) is running. Access front-end at static/index.html"}

@app.post("/api/generate-ideas")
def generate_ideas(req: IdeaRequest):
    if not client:
        raise HTTPException(status_code=500, detail="OpenAI API key not configured.")
    
    system_prompt = (
        "You are an elite Brand Identity Director & Creative Lead. "
        "Your goal is to propose 3 distinct, exceptionally creative logo concept ideas for a brand."
    )
    user_prompt = (
        f"Brand Name: '{req.brand_name}'\n"
        f"Business/Description: '{req.description}'\n"
        f"Preferred Style Vibe: '{req.style}'\n"
        f"Preferred Colors: '{req.colors}'\n\n"
        "Provide 3 distinct design concept proposals in JSON format with key 'concepts'. "
        "Each concept object should have:\n"
        "- 'title': Creative name of the concept\n"
        "- 'icon_idea': Description of the visual symbol/iconography\n"
        "- 'color_palette': Color suggestions\n"
        "- 'concept_explanation': Why this fits the brand\n"
        "- 'dalle_prompt': A complete, hyper-detailed prompt for DALL-E 3 image generation.\n"
    )

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.7
        )
        return json.loads(response.choices[0].message.content)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate ideas: {str(e)}")

@app.post("/api/generate-logo")
def generate_logo(req: GenerateLogoRequest):
    if not client:
        raise HTTPException(status_code=500, detail="OpenAI API key not configured.")
    
    style_spec = STYLE_PROMPTS.get(req.style, req.style or "Minimalist vector logo")
    
    if req.custom_prompt and req.custom_prompt.strip():
        final_prompt = req.custom_prompt.strip()
    else:
        final_prompt = (
            f"Design a world-class professional vector logo for the brand '{req.brand_name}'. "
            f"Brand context: {req.description}. "
            f"Design direction: {style_spec}. "
            f"Color palette: {req.colors}. "
            f"The logo must feature a distinctive icon paired with custom typography spelling '{req.brand_name}'. "
            f"Clean white background, no photorealism, single centered logo mark."
        )

    try:
        image_resp = client.images.generate(
            model="dall-e-3",
            prompt=final_prompt,
            n=1,
            size="1024x1024",
            quality="standard",
            response_format="b64_json"
        )
        
        b64_data = image_resp.data[0].b64_json

        import base64
        logo_id = str(uuid.uuid4())
        image_filename = f"{logo_id}.png"
        image_path = os.path.join(LOGOS_DIR, image_filename)
        
        with open(image_path, "wb") as f:
            f.write(base64.b64decode(b64_data))
        
        metadata = {
            "id": logo_id,
            "brand_name": req.brand_name,
            "description": req.description,
            "style": req.style,
            "colors": req.colors,
            "prompt": final_prompt,
            "model": "dall-e-3",
            "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
            "image_filename": image_filename,
            "image_url": f"/generated_logos/{image_filename}"
        }
        
        meta_path = os.path.join(LOGOS_DIR, f"{logo_id}.json")
        with open(meta_path, "w") as f:
            json.dump(metadata, f, indent=2)

        return metadata

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Logo generation error: {str(e)}")

@app.get("/api/history")
def get_history():
    history = []
    for fname in os.listdir(LOGOS_DIR):
        if fname.endswith(".json"):
            filepath = os.path.join(LOGOS_DIR, fname)
            try:
                with open(filepath, "r") as f:
                    data = json.load(f)
                    history.append(data)
            except Exception:
                continue
    history.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
    return history

app.mount("/generated_logos", StaticFiles(directory=LOGOS_DIR), name="generated_logos")
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)

