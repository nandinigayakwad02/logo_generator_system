import os
import json
import uuid
import base64
import datetime
from typing import Optional, List
from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import httpx
from dotenv import load_dotenv

load_dotenv()

app = FastAPI(
    title="AI Logo Generator System - Google Imagen 3 Edition",
    description="Python microservice powered by Google's latest Imagen 3 engine (gemini-3-pro-image).",
    version="3.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

LOGOS_DIR = os.path.join(os.path.dirname(__file__), "generated_logos")
STATIC_DIR = os.path.join(os.path.dirname(__file__), "static")
os.makedirs(LOGOS_DIR, exist_ok=True)
os.makedirs(STATIC_DIR, exist_ok=True)

raw_key = os.getenv("GEMINI_API_KEY", "").strip()
gemini_api_key = raw_key.strip('"').strip("'")

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

class LogoRequest(BaseModel):
    entity_name: str
    business_description: Optional[str] = ""
    style: Optional[str] = "Wordmark — the name as type"
    primary_color: Optional[str] = "#0B74D9"
    secondary_color: Optional[str] = "#ffffff"

class LogoVariation(BaseModel):
    variant_name: str
    concept_title: str
    concept_description: str
    image_url: str

class LogoResponse(BaseModel):
    entity_name: str
    provider_used: str
    logos: list[LogoVariation]

STYLE_PROMPTS = {
    "minimalist": "Minimalist vector logo mark, ultra-clean geometric lines, single iconic symbol, crisp flat design with elegant negative space, Helvetica-level precision",
    "monogram": "Sophisticated monogram logo, interlocking custom letterforms, premium typographic craftsmanship, golden ratio proportions, luxury fashion brand aesthetic",
    "cybertech": "Futuristic cyberpunk tech logo, neon-accented emblem, circuit-board geometry integrated into letterforms, holographic gradient feel, sharp angular edges",
    "vintage": "Hand-crafted vintage emblem logo, ornate linework border, retro badge with banner ribbon, detailed engraving style illustration",
    "mascot": "Bold stylized mascot character logo, dynamic pose with personality, clean vector illustration with thick outlines, esports/gaming-grade energy",
    "abstract": "Abstract geometric logo mark, mathematically precise fluid shape, masterful negative-space storytelling, Saul Bass inspired iconic simplicity",
    "luxury": "Ultra-premium luxury brand logo, editorial serif typography, gold foil accent aesthetic, Chanel/Dior level elegance, minimalist icon with maximal sophistication",
    "3d_clay": "Soft 3D clay-morphism glossy logo icon, isometric perspective, smooth rounded surfaces with subtle studio lighting, playful yet professional"
}

@app.get("/")
def read_root():
    index_file = os.path.join(STATIC_DIR, "index.html")
    if os.path.exists(index_file):
        return FileResponse(index_file)
    return {
        "status": "online",
        "service": "Trinity AI Logo Generator (Google Imagen 3)",
        "gemini_active": bool(gemini_api_key),
        "docs": "/docs"
    }

# ----------------- GEMINI / IMAGEN 3 IDEAS GENERATION -----------------
@app.post("/api/generate-ideas")
async def generate_ideas(req: IdeaRequest):
    if not gemini_api_key:
        raise HTTPException(status_code=500, detail="Gemini API key not configured.")
    
    system_prompt = (
        "You are an elite Brand Identity Director & Creative Lead. "
        "Your goal is to propose 3 distinct, exceptionally creative logo concept ideas for a brand."
    )
    user_prompt = (
        f"{system_prompt}\n"
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
        "- 'dalle_prompt': A hyper-detailed prompt for Google Imagen 3 image generation. "
        "The prompt MUST specify: 'Professional award-winning logo design', describe the exact icon in detail, "
        "specify exact color palette, request 'clean white background', mention 'crisp custom typography', "
        "and end with 'high resolution, commercial brand logo identity mark'.\n"
        "Return ONLY raw valid JSON."
    )

    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={gemini_api_key}"
    payload = {
        "contents": [{"parts": [{"text": user_prompt}]}],
        "generationConfig": {"responseMimeType": "application/json"}
    }

    try:
        async with httpx.AsyncClient(timeout=30.0) as client_http:
            resp = await client_http.post(url, json=payload)
            if resp.status_code == 200:
                data = resp.json()
                text = data["candidates"][0]["content"]["parts"][0]["text"]
                return json.loads(text)
            else:
                raise Exception(f"Gemini API status {resp.status_code}: {resp.text}")
    except Exception:
        return {
            "concepts": [
                {
                    "title": f"Option 1: {req.brand_name} Dynamic Innovation",
                    "icon_idea": f"A sleek geometric emblem for {req.brand_name}",
                    "color_palette": req.colors or "#0B74D9",
                    "concept_explanation": "Modern high-tech brand identity",
                    "dalle_prompt": f"Award winning modern vector logo design for {req.brand_name}, crisp geometry, studio lighting, clean background"
                },
                {
                    "title": f"Option 2: {req.brand_name} Tech Fusion",
                    "icon_idea": f"Interlocking monogram logo for {req.brand_name}",
                    "color_palette": req.colors or "#0B74D9",
                    "concept_explanation": "Clean luxury typography identity",
                    "dalle_prompt": f"Luxury gold and metallic logo design for {req.brand_name}, 8k resolution, elegant emblem"
                },
                {
                    "title": f"Option 3: {req.brand_name} Elevated Vision",
                    "icon_idea": "3D glossy crest emblem",
                    "color_palette": req.colors or "#0B74D9",
                    "concept_explanation": "Sleek premium brand identity",
                    "dalle_prompt": f"Premium modern crest logo for {req.brand_name}, studio background"
                }
            ]
        }


# ----------------- GOOGLE IMAGEN 3 HIGH RESOLUTION ENGINE -----------------
async def generate_imagen3_image(prompt: str, filename: str) -> str:
    if not gemini_api_key:
        raise Exception("GEMINI_API_KEY is not set.")

    # High quality Google Imagen 3 models in order of visual quality
    imagen_models = [
        "gemini-3-pro-image",
        "gemini-3.1-flash-image",
        "gemini-2.5-flash-image"
    ]

    for model_name in imagen_models:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={gemini_api_key}"
        payload = {
            "contents": [{"parts": [{"text": prompt}]}]
        }

        try:
            async with httpx.AsyncClient(timeout=60.0) as client_http:
                resp = await client_http.post(url, json=payload)
                if resp.status_code == 200:
                    data = resp.json()
                    candidates = data.get("candidates", [])
                    if candidates:
                        parts = candidates[0].get("content", {}).get("parts", [])
                        for part in parts:
                            if "inlineData" in part:
                                b64_data = part["inlineData"]["data"]
                                mime_type = part["inlineData"].get("mimeType", "image/png")
                                ext = ".jpg" if "jpeg" in mime_type else ".png"
                                
                                final_filename = filename.replace(".png", ext).replace(".jpg", ext)
                                file_path = os.path.join(LOGOS_DIR, final_filename)
                                
                                with open(file_path, "wb") as f:
                                    f.write(base64.b64decode(b64_data))
                                
                                return f"/generated_logos/{final_filename}"
                else:
                    continue
        except Exception:
            continue

    raise Exception("Failed to generate image with Imagen 3 models.")


@app.post("/api/generate-logo")
async def generate_logo(req: GenerateLogoRequest):
    logo_id = str(uuid.uuid4())
    filename = f"{logo_id}.png"
    
    style_spec = STYLE_PROMPTS.get(req.style, req.style or "Minimalist vector logo")
    
    if req.custom_prompt and req.custom_prompt.strip():
        final_prompt = req.custom_prompt.strip()
    else:
        final_prompt = (
            f"Design a world-class, award-winning, high-resolution logo for '{req.brand_name}'. "
            f"Brand context: {req.description}. "
            f"Design direction: {style_spec}. "
            f"Color palette: {req.colors}. "
            f"The logo must feature an ultra-crisp, memorable iconic emblem paired with typography spelling '{req.brand_name}'. "
            f"Rendered in 8K resolution, clean white background, professional studio lighting, commercial quality identity mark."
        )

    try:
        url = await generate_imagen3_image(final_prompt, filename)
        
        metadata = {
            "id": logo_id,
            "brand_name": req.brand_name,
            "description": req.description,
            "style": req.style,
            "colors": req.colors,
            "prompt": final_prompt,
            "model": "Google Imagen 3 (gemini-3-pro-image)",
            "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
            "image_filename": filename,
            "image_url": url
        }
        
        meta_path = os.path.join(LOGOS_DIR, f"{logo_id}.json")
        with open(meta_path, "w") as f:
            json.dump(metadata, f, indent=2)

        return metadata
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Imagen 3 generation error: {str(e)}")


@app.post("/api/v1/generate-logos", response_model=LogoResponse)
@app.post("/api/v1/generate-logos/gemini", response_model=LogoResponse)
async def generate_logos_gemini(req: LogoRequest):
    if not req.entity_name:
        raise HTTPException(status_code=400, detail="Entity name is required.")
    
    import asyncio
    variants = [
        ("Colour", "Play Ring", f"Modern vibrant brand logo for {req.entity_name}, primary color {req.primary_color}, clean background"),
        ("White", "Play Ring (Inverted)", f"White inverted logo emblem for {req.entity_name} on dark slate background"),
        ("Black", "Play Ring (Monochrome)", f"Black monochromatic logo emblem for {req.entity_name} on clean white background")
    ]

    async def process_variant(variant_name: str, concept_title: str, concept_desc: str):
        filename = f"{uuid.uuid4().hex}_{variant_name.lower()}.png"
        prompt = (
            f"Design an award-winning high-resolution vector logo mark for '{req.entity_name}'. "
            f"Business description: {req.business_description or 'Modern business'}. "
            f"Style: {req.style or 'Wordmark'}. Variant: {variant_name}. "
            f"{concept_desc}. Ultra-crisp geometry, professional studio presentation."
        )
        url = await generate_imagen3_image(prompt, filename)
        return LogoVariation(
            variant_name=variant_name,
            concept_title=concept_title,
            concept_description=concept_desc,
            image_url=url
        )

    tasks = [process_variant(v[0], v[1], v[2]) for v in variants]
    results = await asyncio.gather(*tasks)

    return LogoResponse(
        entity_name=req.entity_name,
        provider_used="Google Imagen 3 (gemini-3-pro-image)",
        logos=list(results)
    )


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
    uvicorn.run(app, host="127.0.0.1", port=8001)
