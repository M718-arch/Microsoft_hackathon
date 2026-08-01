import torch
import torch.nn as nn
from transformers import AutoTokenizer, AutoModel
import numpy as np
from typing import Dict, List, Optional, Tuple
import os
import re
import warnings
warnings.filterwarnings("ignore")

# Constants (must match training)
ASPECTS = ["food", "service", "price", "cleanliness", 
           "delivery", "ambiance", "app_experience", "general", "none"]
SENTIMENTS = ["positive", "negative", "neutral"]
A2I = {a: i for i, a in enumerate(ASPECTS)}
I2A = {i: a for a, i in A2I.items()}
I2S = {i: s for s, i in enumerate(SENTIMENTS)}
NUM_ASPECTS = len(ASPECTS)
NUM_SENTIMENTS = len(SENTIMENTS)

class ABSAModel(nn.Module):
    """XLM-RoBERTa with dual heads for aspect and sentiment prediction"""
    
    def __init__(self, model_name="xlm-roberta-base", dropout=0.1):
        super().__init__()
        self.encoder = AutoModel.from_pretrained(model_name)
        hidden_size = self.encoder.config.hidden_size
        
        self.dropout = nn.Dropout(dropout)
        # +1 input dim for normalized star_rating
        self.aspect_head = nn.Linear(hidden_size + 1, NUM_ASPECTS)
        self.sentiment_head = nn.Linear(hidden_size + 1, NUM_ASPECTS * NUM_SENTIMENTS)
        
    def forward(self, input_ids, attention_mask, star_rating=None):
        outputs = self.encoder(input_ids=input_ids, attention_mask=attention_mask)
        pooled = outputs.last_hidden_state[:, 0, :]  # [CLS] token
        pooled = self.dropout(pooled)
        
        if star_rating is None:
            star_rating = torch.zeros(pooled.size(0), device=pooled.device)
        pooled = torch.cat([pooled, star_rating.unsqueeze(-1)], dim=-1)
        
        aspect_logits = self.aspect_head(pooled)
        sentiment_logits = self.sentiment_head(pooled).view(-1, NUM_ASPECTS, NUM_SENTIMENTS)
        
        return aspect_logits, sentiment_logits

class FrancoTranslator:
    """Franco-Arabic to Arabic transliterator"""
    
    def __init__(self):
        self.number_map = {
            '2': 'ا', '3': 'ع', '7': 'ح', '8': 'غ',
            '5': 'خ', '4': 'ش', '6': 'ط', '9': 'ص', "'": 'ء'
        }
        
        self.combinations = {
            'sh': 'ش', 'ch': 'تش', 'th': 'ث', 'kh': 'خ',
            'gh': 'غ', 'dh': 'ذ', 'zh': 'ظ', 'aa': 'ا',
            'ee': 'ي', 'oo': 'و', 'uu': 'و', 'ii': 'ي'
        }
        
        self.dictionary = {
            'ana': 'انا', 'enta': 'انت', 'enti': 'انتي', 'ento': 'انتو',
            'ehna': 'احنا', 'homma': 'هما', 'hoa': 'هو', 'heya': 'هي',
            '5idma': 'خدمة', 'service': 'خدمة', '5edma': 'خدمة',
            '7elwa': 'حلوة', '7elw': 'حلو', 'helwa': 'حلوة', 'helw': 'حلو',
            'gedan': 'جداً', 'gdn': 'جداً', 'ktir': 'كتير',
            'awi': 'اوي', 'awy': 'اوي', 'wallahi': 'والله',
            'kwayes': 'كويس', 'kwyes': 'كويس', 'mish': 'مش', 'mesh': 'مش',
            '3ayez': 'عايز', '3ayza': 'عايزة', '7abibi': 'حبيبي',
            'shukran': 'شكرا', 'khalas': 'خلاص', 'tamam': 'تمام',
            'mumtaz': 'ممتاز', 'ghaly': 'غالي', 'fi': 'في', '3ala': 'على',
            'w': 'و', 'bas': 'بس', 'eeh': 'ايه', 'taman': 'تمن',
            'sa3r': 'سعر', 'akl': 'اكل', 'food': 'اكل', 'el': 'ال', 'al': 'ال',
            'gamed': 'جامد', 'gamda': 'جامدة', 'nadeef': 'نظيف', 'nadeefa': 'نظيفة',
            'wesekh': 'وسخ', 'wesekha': 'وسخة', 'sa5t': 'سخت', 'zabat': 'ظبط'
        }
    
    def transliterate(self, text: str) -> str:
        """Transliterate Franco-Arabic text to Arabic script"""
        if not isinstance(text, str):
            return str(text)
        
        text = text.lower()
        
        # Word replacements
        for k, v in self.dictionary.items():
            text = re.sub(r'\b' + re.escape(k) + r'\b', v, text)
        
        # Number mappings
        for k, v in self.number_map.items():
            text = text.replace(k, v)
        
        # Combination mappings
        for k, v in self.combinations.items():
            text = text.replace(k, v)
        
        # Clean up
        text = re.sub(r'\s+', ' ', text).strip()
        return text

class ABSAPredictor:
    """Main prediction class for ABSA"""
    
    def __init__(self):
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.model = None
        self.tokenizer = None
        self.model_path = None
        self.threshold = 0.6
        self.is_loaded = False
        self.f1_score = None
        
        # For demo/fallback mode
        self.demo_mode = True
        
        # Keyword-based fallback
        self.aspect_keywords = {
            "food": ["اكل", "طعام", "food", "akl", "ta3am", "الأكل", "مأكولات"],
            "service": ["خدمة", "service", "5idma", "تعامل", "الخدمة", "ستاف"],
            "price": ["سعر", "price", "غالي", "رخيص", "تمن", "sa3r", "اسعار"],
            "cleanliness": ["نظافة", "clean", "نظيف", "nadafa", "وسخ", "نضيف"],
            "delivery": ["توصيل", "delivery", "استلام", "toseel", "وصل"],
            "ambiance": ["اجواء", "ambiance", "ديكور", "agwaa", "جو"],
            "app_experience": ["تطبيق", "app", "موقع", "tattebeq", "برنامج"],
            "general": ["عام", "overall", "تجربة", "general", "كله"],
        }
        
        self.sentiment_keywords = {
            "positive": ["حلو", "جميل", "ممتاز", "رائع", "good", "great", 
                        "excellent", "helw", "mumtaz", "تحفة", "كويس", "تمام"],
            "negative": ["وحش", "سيء", "مقرف", "bad", "terrible", "awful", 
                        "wahsh", "sayy", "زفت", "بايظ", "غلط"],
            "neutral": ["عادي", "normal", "okay", "average", "aady", "مقبول"],
        }
    
    def load_model(self, model_path: str) -> bool:
        """Load trained model from checkpoint"""
        try:
            if not os.path.exists(model_path):
                print(f"Model file not found: {model_path}")
                return False
            
            checkpoint = torch.load(model_path, map_location=self.device)
            model_name = checkpoint.get("model_name", "xlm-roberta-base")
            self.threshold = checkpoint.get("threshold", 0.6)
            self.f1_score = checkpoint.get("f1", None)
            
            # Initialize model
            self.model = ABSAModel(model_name).to(self.device)
            
            # Load state dict (handle possible mismatches)
            state_dict = checkpoint["model_state"]
            
            # Remove problematic keys if present
            keys_to_remove = ['encoder.embeddings.position_ids']
            for key in keys_to_remove:
                if key in state_dict:
                    del state_dict[key]
            
            self.model.load_state_dict(state_dict, strict=False)
            self.model.eval()
            
            # Load tokenizer
            self.tokenizer = AutoTokenizer.from_pretrained(model_name)
            
            self.model_path = model_path
            self.is_loaded = True
            self.demo_mode = False
            
            print(f"✅ Model loaded successfully!")
            print(f"   📍 Threshold: {self.threshold}")
            print(f"   📊 F1 Score: {self.f1_score}")
            print(f"   ⚡ Device: {self.device}")
            
            return True
            
        except Exception as e:
            print(f"❌ Error loading model: {e}")
            self.is_loaded = False
            self.demo_mode = True
            return False
    
    def normalize_star_rating(self, rating: Optional[float]) -> float:
        """Normalize star rating to [-1, 1] range"""
        if rating is None:
            return 0.0
        try:
            r = float(rating)
        except (TypeError, ValueError):
            return 0.0
        return (r - 3.0) / 2.0
    
    def predict(self, text: str, threshold: Optional[float] = None, 
                star_rating: Optional[float] = None) -> Dict:
        """Predict aspects and sentiments for a single review"""
        
        # Use demo mode if model not loaded
        if not self.is_loaded or self.demo_mode:
            return self._predict_demo(text, threshold or 0.6, star_rating)
        
        # Use trained model
        try:
            threshold = threshold or self.threshold
            
            # Tokenize
            inputs = self.tokenizer(
                text,
                return_tensors="pt",
                truncation=True,
                max_length=128,
                padding="max_length"
            )
            inputs = {k: v.to(self.device) for k, v in inputs.items()}
            
            # Prepare star rating
            rating_tensor = torch.tensor(
                [self.normalize_star_rating(star_rating)],
                dtype=torch.float,
                device=self.device
            )
            
            # Predict
            with torch.no_grad():
                aspect_logits, sentiment_logits = self.model(
                    inputs['input_ids'],
                    inputs['attention_mask'],
                    rating_tensor
                )
                
                aspect_probs = torch.sigmoid(aspect_logits).cpu().numpy()[0]
                sentiment_preds = sentiment_logits.argmax(-1).cpu().numpy()[0]
            
            # Extract predictions
            detected = []
            confidence = {}
            
            for i, prob in enumerate(aspect_probs):
                if prob >= threshold and ASPECTS[i] != "none":
                    detected.append(ASPECTS[i])
                    confidence[ASPECTS[i]] = float(prob)
            
            # Handle no aspects detected
            if not detected:
                detected = ["general"]
                # Use star rating for sentiment if available
                if star_rating is not None:
                    if star_rating >= 4:
                        sentiments = {"general": "positive"}
                    elif star_rating <= 2:
                        sentiments = {"general": "negative"}
                    else:
                        sentiments = {"general": "neutral"}
                else:
                    sentiments = {"general": "neutral"}
            else:
                # Get sentiments for detected aspects
                sentiments = {}
                for asp in detected:
                    if asp != "none":
                        asp_idx = ASPECTS.index(asp)
                        sentiment_idx = sentiment_preds[asp_idx]
                        sentiments[asp] = I2S.get(sentiment_idx, "neutral")
            
            return {
                "aspects": detected,
                "aspect_sentiments": sentiments,
                "confidence": confidence
            }
            
        except Exception as e:
            print(f"Prediction error: {e}")
            return self._predict_demo(text, threshold or 0.6, star_rating)
    
    def _predict_demo(self, text: str, threshold: float, 
                      star_rating: Optional[float]) -> Dict:
        """Fallback keyword-based prediction"""
        text_lower = text.lower()
        
        # Detect aspects
        detected = []
        for aspect, keywords in self.aspect_keywords.items():
            if any(kw in text_lower for kw in keywords):
                detected.append(aspect)
        
        if not detected:
            detected = ["general"]
        
        # Determine sentiments
        sentiments = {}
        for aspect in detected:
            # Count sentiment keywords
            scores = {"positive": 0, "negative": 0, "neutral": 0}
            
            for sentiment, keywords in self.sentiment_keywords.items():
                for kw in keywords:
                    if kw in text_lower:
                        scores[sentiment] += 1
            
            # If star rating provided, use it
            if star_rating is not None:
                if star_rating >= 4:
                    scores["positive"] += 2
                elif star_rating <= 2:
                    scores["negative"] += 2
                else:
                    scores["neutral"] += 1
            
            # Get max sentiment
            sentiment = max(scores, key=scores.get) if any(scores.values()) else "neutral"
            sentiments[aspect] = sentiment
        
        return {
            "aspects": detected,
            "aspect_sentiments": sentiments,
            "confidence": {}
        }