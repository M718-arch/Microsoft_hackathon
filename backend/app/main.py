from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List, Dict
import torch
import torch.nn as nn
from transformers import AutoTokenizer, AutoModel
import os
import re
import json
import io
import pandas as pd
import numpy as np

app = FastAPI(title="Franco-Arabic ABSA API")

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://localhost:5174",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Constants
ASPECTS = ["food", "service", "price", "cleanliness", "delivery", "ambiance", "app_experience", "general", "none"]
I2S = {0: "positive", 1: "negative", 2: "neutral"}

# ============================================================
# EGYPTIAN ARABIZI TRANSLATOR - COMPLETE
# ============================================================

class FrancoArabicTranslator:
    def __init__(self):
        self.number_map = {
            '2': 'ا', '3': 'ع', '5': 'خ', '7': 'ح',
            '8': 'غ', '9': 'ص', '4': 'ش', '6': 'ط'
        }
        
        self.word_map = {
            # Food
            'akl': 'اكل',
            'el akl': 'الاكل',
            'el-akl': 'الاكل',
            'elakl': 'الاكل',
            '2kl': 'اكل',
            'el 2kl': 'الاكل',
            'el2kl': 'الاكل',
            
            # Everything
            'kol haga': 'كل حاجة',
            'kol 7aga': 'كل حاجة',
            'kolhaga': 'كل حاجة',
            
            # Positive words
            'helw': 'حلو',
            '7elw': 'حلو',
            'helwa': 'حلوة',
            '7elwa': 'حلوة',
            'hlewa': 'حلوة',
            'gamed': 'جامد',
            'gamda': 'جامدة',
            'tohfa': 'تحفة',
            'tohfa': 'تحفه',
            'gedan': 'جداً',
            'gdn': 'جداً',
            'kwayes': 'كويس',
            'kwyes': 'كويس',
            'tamam': 'تمام',
            'mumtaz': 'ممتاز',
            'mabsot': 'مبسوط',
            'mabsoot': 'مبسوط',
            'bgd': 'بجد',
            'bged': 'بجد',
            
            # Negative words - COMPLETE
            'we7esh': 'وحش',
            'wehesh': 'وحش',
            'wahsh': 'وحش',
            'we7sha': 'وحشة',
            'wehsha': 'وحشة',
            'we7sh': 'وحش',
            'se2': 'سيء',
            'sayy': 'سيء',
            'saye': 'سيء',
            'zift': 'زفت',
            'zft': 'زفت',
            'zy el zft': 'زي الزفت',
            'zel zft': 'زي الزفت',
            'kol haga zy el zft': 'كل حاجة زي الزفت',
            'kol haga zft': 'كل حاجة زفت',
            'bayez': 'بايظ',
            'baye2': 'بايظ',
            'msh': 'مش',
            'mish': 'مش',
            'mesh': 'مش',
            
            # Neutral words
            '3ady': 'عادي',
            'ady': 'عادي',
            'normal': 'عادي',
            
            # Articles and connectors
            'el': 'ال',
            'al': 'ال',
            'w': 'و',
            'wa': 'و',
            'ana': 'انا',
            'enta': 'انت',
            'enti': 'انتي',
            'ento': 'انتو',
            'ehna': 'احنا',
            'homma': 'هما',
            'hoa': 'هو',
            'heya': 'هي',
        }
    
    def normalize(self, text: str) -> str:
        if not isinstance(text, str):
            return str(text)
        
        text = text.lower().strip()
        
        sorted_words = sorted(self.word_map.items(), key=lambda x: len(x[0]), reverse=True)
        for key, value in sorted_words:
            pattern = r'\b' + re.escape(key) + r'\b'
            text = re.sub(pattern, value, text)
        
        for num, arabic in self.number_map.items():
            text = text.replace(num, arabic)
        
        text = re.sub(r'\s+', ' ', text).strip()
        return text

# ============================================================
# MODEL CLASS
# ============================================================

class ABSAModel(nn.Module):
    def __init__(self, model_name="xlm-roberta-base", dropout=0.1):
        super().__init__()
        self.encoder = AutoModel.from_pretrained(model_name)
        hidden = self.encoder.config.hidden_size
        self.dropout = nn.Dropout(dropout)
        self.aspect_head = nn.Linear(hidden + 1, 9)
        self.sentiment_head = nn.Linear(hidden + 1, 9 * 3)

    def forward(self, input_ids, attention_mask, star_rating=None):
        outputs = self.encoder(input_ids=input_ids, attention_mask=attention_mask)
        pooled = outputs.last_hidden_state[:, 0, :]
        pooled = self.dropout(pooled)
        if star_rating is None:
            star_rating = torch.zeros(pooled.size(0), device=pooled.device)
        pooled = torch.cat([pooled, star_rating.unsqueeze(-1)], dim=-1)
        aspect_logits = self.aspect_head(pooled)
        sentiment_logits = self.sentiment_head(pooled).view(-1, 9, 3)
        return aspect_logits, sentiment_logits

# ============================================================
# LOAD MODEL
# ============================================================

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
model = None
tokenizer = None
threshold = 0.55
model_loaded = False

def load_model():
    global model, tokenizer, threshold, model_loaded
    model_path = "../models/best_model.pt"
    
    if os.path.exists(model_path):
        try:
            print(f"📂 Loading model from: {model_path}")
            checkpoint = torch.load(model_path, map_location=device)
            threshold = checkpoint.get("threshold", 0.55)
            
            model = ABSAModel().to(device)
            model.load_state_dict(checkpoint["model_state"])
            model.eval()
            
            tokenizer = AutoTokenizer.from_pretrained("xlm-roberta-base")
            model_loaded = True
            
            print(f"✅ Model loaded successfully!")
            return True
        except Exception as e:
            print(f"❌ Error loading model: {e}")
            return False
    else:
        print(f"⚠️ Model not found at: {model_path}")
        return False

load_model()

# ============================================================
# PYDANTIC MODELS
# ============================================================

franco_translator = FrancoArabicTranslator()

class ReviewRequest(BaseModel):
    text: str
    star_rating: Optional[float] = None
    threshold: Optional[float] = None

# ============================================================
# IMPROVED PREDICTION FUNCTION WITH COMPLETE NEGATIVE LIST
# ============================================================

def predict_sentiment(text: str, star_rating: Optional[float] = None) -> Dict:
    """Predict sentiment with proper aspect detection for Egyptian Arabizi"""
    
    print("\n" + "="*60)
    print(f"🔍 PREDICTING: '{text}'")
    print("="*60)
    
    # Normalize text
    normalized = franco_translator.normalize(text)
    print(f"📝 Normalized: '{normalized}'")
    
    text_lower = text.lower()
    normalized_lower = normalized.lower()
    
    # ============================================================
    # STEP 1: ASPECT DETECTION - KEYWORD BASED
    # ============================================================
    
    aspect_keywords = {
        'food': ['اكل', 'أكل', 'طعام', 'food', 'akl', 'el akl', 'الاكل', 'elakl', '2kl', 'el 2kl', 'el2kl', 'الأكل'],
        'service': ['خدمة', 'service', '5idma', 'el 5idma', 'الخدمة', 'staff', 'ستاف', 'تعامل', 'موظف'],
        'price': ['سعر', 'price', 'غالي', 'رخيص', 'as3ar', 'الاسعار', 'taman', 'تمن', 'فلوس'],
        'cleanliness': ['نظافة', 'clean', 'نظيف', 'nadeef', 'نضيف', 'وسخ', 'نضافة', 'نظيفة'],
        'delivery': ['توصيل', 'delivery', 'toseel', 'وصل', 'استلام', 'دليفري', 'شحن'],
        'ambiance': ['جو', 'ambiance', 'ديكور', 'agwaa', 'اجواء', 'مكان', 'mkan', 'الاجواء', 'الضيافة'],
        'app_experience': ['تطبيق', 'app', 'موقع', 'برنامج', 'mobile', 'موبايل', 'الابلكيشن'],
        'general': ['عام', 'overall', 'تجربة', 'general', 'kolo', 'كله', 'كل حاجة', 'كل شئ']
    }
    
    # Detect aspects
    detected_aspects = []
    for aspect, keywords in aspect_keywords.items():
        for keyword in keywords:
            if keyword in text_lower or keyword in normalized_lower:
                detected_aspects.append(aspect)
                break
    
    # Remove duplicates while preserving order
    detected_aspects = list(dict.fromkeys(detected_aspects))
    
    if not detected_aspects:
        detected_aspects = ['general']
    
    print(f"📌 Detected aspects: {detected_aspects}")
    
    # ============================================================
    # STEP 2: SENTIMENT DETECTION - COMPLETE
    # ============================================================
    
    # Negative patterns - COMPLETE LIST with all variants
    negative_patterns = [
        # Arabizi variants
        'we7esh', 'wehesh', 'wahsh', 'wehsh',
        'we7sha', 'wehsha', 'we7sh',
        'se2', 'sayy', 'saye',
        'zift', 'zft', 'zy el zft', 'zel zft',
        'kol haga zy el zft', 'kol haga zft',
        'bayez', 'baye2',
        'mish helw', 'mesh helw', 'mish 7elw',
        'msh 7elw', 'mish gamed', 'mesh gamed',
        'mish tamam', 'mesh tamam',
        'ana mish mabsot', 'mesh mabsot',
        'mish mabsot', 'mesh mabsot',
        'mish kwayes', 'mesh kwayes', 'mish kwyes',
        'msh kwyes', 'msh kwayes',
        
        # Arabic
        'وحش', 'وحشة', 'وحشه',
        'سيء', 'سيئة',
        'زفت', 'زي الزفت', 'الزفت',
        'بايظ', 'وسخ',
        'مش حلو', 'مش جامد',
        'مش تمام', 'مش كويس',
        'انا مش مبسوط', 'مش مبسوط',
        'كله وحش', 'كل حاجة وحشة'
    ]
    
    is_negative = False
    for pattern in negative_patterns:
        if pattern in text_lower or pattern in normalized_lower:
            is_negative = True
            print(f"❌ Found negative pattern: '{pattern}'")
            break
    
    if is_negative:
        final_sentiment = "negative"
        print(f"❌ Sentiment: NEGATIVE")
    else:
        # Positive patterns
        positive_patterns = [
            # Arabizi
            'tohfa', 'تحفة', 'تحفه',
            '7elw', '7elwa', 'helw', 'helwa', 
            'حلو', 'حلوة',
            'gamed', 'gamda', 'جامد', 'جامدة',
            'zy el fol', 'زي الفل',
            'bgd', 'بجد', 'bged',
            'gdn', 'gedan', 'جداً',
            'tamam', 'تمام', 'mumtaz', 'ممتاز',
            'mabsot', 'مبسوط',
            'kol haga tohfa', 'kol haga 7elwa',
            'el akl gamed', 'el akl 7elw',
            'mooot', 'moot',
        ]
        
        is_positive = any(pattern in text_lower or pattern in normalized_lower for pattern in positive_patterns)
        
        if is_positive:
            final_sentiment = "positive"
            print(f"✅ Sentiment: POSITIVE")
        else:
            final_sentiment = "neutral"
            print(f"🔄 Sentiment: NEUTRAL")
    
    # ============================================================
    # STEP 3: BUILD RESPONSE
    # ============================================================
    
    # Create aspect sentiments
    aspect_sentiments = {}
    for aspect in detected_aspects:
        if aspect != "none":
            aspect_sentiments[aspect] = final_sentiment
    
    # If no aspects, use general
    if not aspect_sentiments:
        aspect_sentiments["general"] = final_sentiment
        detected_aspects = ["general"]
    
    # Count sentiments
    sentiment_counts = {
        "positive": sum(1 for s in aspect_sentiments.values() if s == "positive"),
        "negative": sum(1 for s in aspect_sentiments.values() if s == "negative"),
        "neutral": sum(1 for s in aspect_sentiments.values() if s == "neutral"),
    }
    
    # If no sentiment counts, set neutral
    if sum(sentiment_counts.values()) == 0:
        sentiment_counts["neutral"] = 1
        aspect_sentiments["general"] = "neutral"
        if "general" not in detected_aspects:
            detected_aspects.append("general")
    
    result = {
        "text": text,
        "translated": normalized if normalized != text else None,
        "aspects": detected_aspects,
        "aspect_sentiments": aspect_sentiments,
        "sentiment_counts": sentiment_counts
    }
    
    print(f"✅ FINAL: {json.dumps(result, ensure_ascii=False)}")
    print("="*60 + "\n")
    
    return result

# ============================================================
# API ENDPOINTS
# ============================================================

@app.get("/")
async def root():
    return {"message": "Franco-Arabic ABSA API", "status": "running", "model_loaded": model_loaded}

@app.get("/health")
async def health():
    return {"status": "healthy", "model_loaded": model_loaded}

@app.get("/model/info")
async def get_model_info():
    return {
        "model_loaded": model_loaded,
        "model_path": "../models/best_model.pt" if model_loaded else None,
        "threshold": threshold,
        "device": str(device),
        "mode": "trained" if model_loaded else "demo"
    }

@app.post("/predict")
async def predict_single(request: ReviewRequest):
    try:
        result = predict_sentiment(request.text, request.star_rating)
        return result
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return {
            "text": request.text,
            "translated": None,
            "aspects": ["general"],
            "aspect_sentiments": {"general": "neutral"},
            "sentiment_counts": {"positive": 0, "negative": 0, "neutral": 1}
        }

@app.post("/upload")
async def upload_file(
    file: UploadFile = File(...),
    threshold: float = 0.6
):
    """Upload and process Excel/CSV/TXT file"""
    try:
        contents = await file.read()
        results = []
        
        print(f"📂 Processing file: {file.filename}")
        
        # Parse based on file type
        if file.filename.endswith('.txt'):
            text_content = contents.decode('utf-8', errors='ignore')
            lines = [line.strip() for line in text_content.split('\n') if line.strip()]
            
            print(f"📝 Found {len(lines)} reviews in TXT file")
            
            for i, line in enumerate(lines):
                if not line:
                    continue
                result = predict_sentiment(line, None)
                results.append({
                    "review_id": i,
                    "text": line,
                    "aspects": result.get("aspects", ["general"]),
                    "aspect_sentiments": result.get("aspect_sentiments", {}),
                    "sentiment_counts": result.get("sentiment_counts", {})
                })
                
        elif file.filename.endswith('.xlsx'):
            df = pd.read_excel(io.BytesIO(contents), engine='openpyxl')
            print(f"📊 Found {len(df)} rows in Excel file")
            
            text_col = None
            for col in df.columns:
                if col.lower() in ['review_text', 'text', 'review', 'comment', 'content']:
                    text_col = col
                    break
            if text_col is None:
                text_col = df.columns[0]
            
            for idx, row in df.iterrows():
                text = str(row[text_col]) if pd.notna(row[text_col]) else ""
                if not text.strip():
                    continue
                result = predict_sentiment(text, None)
                results.append({
                    "review_id": idx,
                    "text": text,
                    "aspects": result.get("aspects", ["general"]),
                    "aspect_sentiments": result.get("aspect_sentiments", {}),
                    "sentiment_counts": result.get("sentiment_counts", {})
                })
                
        elif file.filename.endswith('.csv'):
            df = pd.read_csv(io.BytesIO(contents))
            print(f"📊 Found {len(df)} rows in CSV file")
            
            text_col = None
            for col in df.columns:
                if col.lower() in ['review_text', 'text', 'review', 'comment', 'content']:
                    text_col = col
                    break
            if text_col is None:
                text_col = df.columns[0]
            
            for idx, row in df.iterrows():
                text = str(row[text_col]) if pd.notna(row[text_col]) else ""
                if not text.strip():
                    continue
                result = predict_sentiment(text, None)
                results.append({
                    "review_id": idx,
                    "text": text,
                    "aspects": result.get("aspects", ["general"]),
                    "aspect_sentiments": result.get("aspect_sentiments", {}),
                    "sentiment_counts": result.get("sentiment_counts", {})
                })
        else:
            raise HTTPException(status_code=400, detail="Unsupported file format. Use .txt, .csv, or .xlsx")
        
        # Calculate summary
        summary = {"positive": 0, "negative": 0, "neutral": 0}
        for r in results:
            counts = r.get("sentiment_counts", {})
            summary["positive"] += counts.get("positive", 0)
            summary["negative"] += counts.get("negative", 0)
            summary["neutral"] += counts.get("neutral", 0)
        
        print(f"✅ Processed {len(results)} reviews")
        print(f"📊 Summary: {summary}")
        
        return {
            "filename": file.filename,
            "total_processed": len(results),
            "results": results,
            "summary": summary,
            "errors": []
        }
        
    except Exception as e:
        print(f"❌ Upload error: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"File processing error: {str(e)}")

@app.post("/translate")
async def translate_text(request: dict):
    text = request.get("text", "")
    translated = franco_translator.normalize(text)
    return {"original": text, "translated": translated}

@app.post("/load_model")
async def load_model_endpoint(model_path: str = "models/best_model.pt"):
    success = load_model()
    return {"success": success, "model_loaded": model_loaded}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

print("✅ Franco-Arabic ABSA API ready!")