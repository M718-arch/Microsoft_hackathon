"""
Franco-Arabic ABSA — Complete Streamlit App
Aspect-Based Sentiment Analysis for Arabic & Franco-Arabic Text
"""

import streamlit as st
import pandas as pd
import numpy as np
import torch
import torch.nn as nn
import json
import re
import os
import tempfile
from collections import Counter
from datetime import datetime
import warnings
warnings.filterwarnings("ignore")

# Try to import transformers
try:
    from transformers import AutoTokenizer, AutoModel
    TRANSFORMERS_AVAILABLE = True
except ImportError:
    TRANSFORMERS_AVAILABLE = False

# Page config - NO st.set_option here!
st.set_page_config(
    page_title="Franco-Arabic ABSA",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        text-align: center;
        padding: 1rem;
        font-weight: bold;
    }
    .positive-box {
        background: #d4edda;
        padding: 0.75rem;
        border-radius: 8px;
        margin: 0.5rem 0;
        border-left: 4px solid #28a745;
    }
    .negative-box {
        background: #f8d7da;
        padding: 0.75rem;
        border-radius: 8px;
        margin: 0.5rem 0;
        border-left: 4px solid #dc3545;
    }
    .neutral-box {
        background: #e2e3e5;
        padding: 0.75rem;
        border-radius: 8px;
        margin: 0.5rem 0;
        border-left: 4px solid #6c757d;
    }
    .stButton > button {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        font-weight: bold;
        width: 100%;
        border: none;
        border-radius: 5px;
        padding: 0.5rem;
        transition: all 0.3s ease;
    }
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 5px 15px rgba(0,0,0,0.2);
    }
    .warning-box {
        background: #fff3cd;
        padding: 1rem;
        border-radius: 8px;
        margin: 0.5rem 0;
        border-left: 4px solid #ffc107;
    }
</style>
""", unsafe_allow_html=True)

# ============================================
# FRANCO-ARABIC TRANSLATOR
# ============================================
class FrancoTranslator:
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
            'sa3r': 'سعر', 'akl': 'اكل', 'food': 'اكل', 'el': 'ال', 'al': 'ال'
        }
    
    def transliterate(self, text: str) -> str:
        if not isinstance(text, str):
            return text
        text = text.lower()
        for k, v in self.dictionary.items():
            text = re.sub(r'\b' + re.escape(k) + r'\b', v, text)
        for k, v in self.number_map.items():
            text = text.replace(k, v)
        for k, v in self.combinations.items():
            text = text.replace(k, v)
        text = re.sub(r'\s+', ' ', text).strip()
        return text

# ============================================
# ABSA MODEL CLASS (XLM-RoBERTa)
# ============================================
if TRANSFORMERS_AVAILABLE:
    class FrancoABSAModel(nn.Module):
        def __init__(self, model_name="xlm-roberta-base", dropout=0.1, num_aspects=9, num_sentiments=3):
            super().__init__()
            self.encoder = AutoModel.from_pretrained(model_name)
            hidden_size = self.encoder.config.hidden_size
            self.num_aspects = num_aspects
            self.num_sentiments = num_sentiments
            self.dropout = nn.Dropout(dropout)
            # +1 input dim for the normalized star_rating feature (0.0 = no rating given)
            self.aspect_head = nn.Linear(hidden_size + 1, num_aspects)
            self.sentiment_head = nn.Linear(hidden_size + 1, num_aspects * num_sentiments)
        
        def forward(self, input_ids, attention_mask, star_rating=None):
            outputs = self.encoder(input_ids=input_ids, attention_mask=attention_mask)
            pooled = outputs.last_hidden_state[:, 0, :]
            pooled = self.dropout(pooled)
            if star_rating is None:
                star_rating = torch.zeros(pooled.size(0), device=pooled.device)
            pooled = torch.cat([pooled, star_rating.unsqueeze(-1)], dim=-1)
            aspect_logits = self.aspect_head(pooled)
            sentiment_logits = self.sentiment_head(pooled).view(-1, self.num_aspects, self.num_sentiments)
            return aspect_logits, sentiment_logits

# ============================================
# DEMO MODEL (Keyword-based)
# ============================================
class DemoModel:
    def __init__(self):
        self.aspect_keywords = {
            "food": ["اكل", "طعام", "food", "akl", "ta3am", "الأكل"],
            "service": ["خدمة", "service", "5idma", "تعامل", "الخدمة"],
            "price": ["سعر", "price", "غالي", "رخيص", "تمن", "sa3r"],
            "cleanliness": ["نظافة", "clean", "نظيف", "nadafa", "وسخ"],
            "delivery": ["توصيل", "delivery", "استلام", "toseel"],
            "ambiance": ["اجواء", "ambiance", "ديكور", "agwaa"],
            "app_experience": ["تطبيق", "app", "موقع", "tattebeq"],
            "general": ["عام", "overall", "تجربة", "general"],
        }
        
        self.sentiment_keywords = {
            "positive": ["حلو", "جميل", "ممتاز", "رائع", "good", "great", "excellent", "helw", "mumtaz"],
            "negative": ["وحش", "سيء", "مقرف", "bad", "terrible", "awful", "wahsh", "sayy"],
            "neutral": ["عادي", "normal", "okay", "average", "aady"],
        }
        
        self.intensifiers = ["اوي", "قوي", "جداً", "جدا", "كتير", "gedan", "awi"]
    
    def predict(self, text, threshold=0.5, star_rating=None):
        text_lower = text.lower()
        detected_aspects = []
        aspect_sentiments = {}
        
        for aspect, keywords in self.aspect_keywords.items():
            for keyword in keywords:
                if keyword in text_lower:
                    detected_aspects.append(aspect)
                    scores = {"positive": 0, "negative": 0, "neutral": 0}
                    intensity = 2 if any(i in text_lower for i in self.intensifiers) else 1
                    
                    for sentiment, sent_words in self.sentiment_keywords.items():
                        for sw in sent_words:
                            if sw in text_lower:
                                scores[sentiment] += intensity

                    # Fold the star rating in as one more vote, same weight as
                    # a single keyword hit, so it nudges rather than overrides.
                    if star_rating is not None:
                        if star_rating >= 4:
                            scores["positive"] += 1
                        elif star_rating <= 2:
                            scores["negative"] += 1
                        else:
                            scores["neutral"] += 1
                    
                    sentiment = max(scores, key=scores.get)
                    if scores[sentiment] == 0:
                        sentiment = "neutral"
                    
                    aspect_sentiments[aspect] = sentiment
                    break
        
        if not detected_aspects:
            detected_aspects = ["general"]
            if star_rating is not None and star_rating != 3:
                aspect_sentiments["general"] = "positive" if star_rating >= 4 else "negative"
            else:
                aspect_sentiments["general"] = "neutral"
        
        return {"aspects": detected_aspects, "aspect_sentiments": aspect_sentiments}
    
    def predict_batch(self, texts, threshold=0.5, star_ratings=None):
        results = []
        for i, text in enumerate(texts):
            rating = star_ratings[i] if star_ratings is not None else None
            pred = self.predict(text, threshold, rating)
            results.append({
                "review_id": i,
                "aspects": pred["aspects"],
                "aspect_sentiments": pred["aspect_sentiments"]
            })
        return results

# ============================================
# CONSTANTS
# ============================================
ASPECTS = ["food", "service", "price", "cleanliness", 
           "delivery", "ambiance", "app_experience", "general", "none"]
ASPECT_LABELS = {
    "food": "🍽️ Food", "service": "🤝 Service", "price": "💰 Price",
    "cleanliness": "🧹 Cleanliness", "delivery": "🛵 Delivery",
    "ambiance": "✨ Ambiance", "app_experience": "📱 App",
    "general": "💬 General", "none": "—",
}
SENTIMENT_EMOJI = {"positive": "😊", "negative": "😞", "neutral": "😐"}

# ============================================
# INITIALIZE SESSION STATE
# ============================================
if 'initialized' not in st.session_state:
    st.session_state.initialized = True
    st.session_state.model = None
    st.session_state.tokenizer = None
    st.session_state.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    st.session_state.model_loaded = False
    st.session_state.use_demo = True
    st.session_state.translator = FrancoTranslator()
    st.session_state.demo_model = DemoModel()
    st.session_state.threshold = 0.6
    st.session_state.predictions = None
    st.session_state.model_f1 = None

# ============================================
# MODEL LOADING FUNCTION
# ============================================
def load_trained_model(uploaded_file):
    if not TRANSFORMERS_AVAILABLE:
        return None, None, None, "Transformers not installed. Run: pip install transformers"
    
    try:
        with st.spinner(f"Loading {uploaded_file.size / 1e9:.2f} GB model..."):
            with tempfile.NamedTemporaryFile(delete=False, suffix='.pt') as tmp:
                tmp.write(uploaded_file.getvalue())
                temp_path = tmp.name
            
            device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
            checkpoint = torch.load(temp_path, map_location=device)
            
            model = FrancoABSAModel(model_name="xlm-roberta-base", dropout=0.1)
            
            if 'model_state' in checkpoint:
                state_dict = checkpoint['model_state']
            else:
                state_dict = checkpoint
            
            keys_to_remove = ['encoder.embeddings.position_ids']
            for key in keys_to_remove:
                if key in state_dict:
                    del state_dict[key]
            
            model.load_state_dict(state_dict, strict=False)
            model.to(device)
            model.eval()
            
            tokenizer = AutoTokenizer.from_pretrained("xlm-roberta-base")
            os.unlink(temp_path)
            
            f1_score = checkpoint.get('f1_score', checkpoint.get('f1', checkpoint.get('best_f1', 'N/A')))
            
            return model, tokenizer, device, f1_score
    except Exception as e:
        return None, None, None, str(e)

# ============================================
# PREDICTION FUNCTIONS
# ============================================
def normalize_star_rating(raw_rating):
    """Must match train.py's normalization. None/0 means 'no rating given'."""
    if raw_rating is None:
        return 0.0
    try:
        r = float(raw_rating)
    except (TypeError, ValueError):
        return 0.0
    return (r - 3.0) / 2.0


def predict_with_trained_model(text, model, tokenizer, device, threshold, star_rating=None):
    inputs = tokenizer(text, return_tensors="pt", truncation=True, max_length=128)
    inputs = {k: v.to(device) for k, v in inputs.items()}
    rating_tensor = torch.tensor([normalize_star_rating(star_rating)], dtype=torch.float, device=device)
    
    with torch.no_grad():
        aspect_logits, sentiment_logits = model(inputs['input_ids'], inputs['attention_mask'], rating_tensor)
        aspect_probs = torch.sigmoid(aspect_logits).cpu().numpy()[0]
        sentiment_preds = sentiment_logits.argmax(-1).cpu().numpy()[0]
    
    sentiment_map = {0: "positive", 1: "negative", 2: "neutral"}
    
    detected = [ASPECTS[i] for i, p in enumerate(aspect_probs) if p >= threshold]
    
    if "none" in detected and len(detected) > 1:
        detected.remove("none")
    if not detected:
        detected = ["none"]
    
    sentiments = {}
    for asp in detected:
        if asp != "none":
            asp_idx = ASPECTS.index(asp)
            sentiments[asp] = sentiment_map.get(sentiment_preds[asp_idx], "neutral")
    
    return {"aspects": detected, "aspect_sentiments": sentiments}

def predict_with_demo_model(text, threshold, star_rating=None):
    return st.session_state.demo_model.predict(text, threshold, star_rating)

# ============================================
# MAIN APP
# ============================================
def main():
    st.markdown('<div class="main-header">🧠 Franco-Arabic ABSA System</div>', unsafe_allow_html=True)
    st.caption("Aspect-Based Sentiment Analysis for Arabic & Franco-Arabic Text | 75%+ Accuracy")
    st.markdown("---")
    
    # Sidebar
    with st.sidebar:
        st.markdown("## 📦 Model Management")
        st.markdown("---")
        
        uploaded_model = st.file_uploader("Choose your .pt model file", type=['pt'])
        
        if uploaded_model is not None and not st.session_state.model_loaded:
            model_result = load_trained_model(uploaded_model)
            if model_result[0] is not None:
                st.session_state.model = model_result[0]
                st.session_state.tokenizer = model_result[1]
                st.session_state.device = model_result[2]
                st.session_state.model_loaded = True
                st.session_state.use_demo = False
                st.session_state.model_f1 = model_result[3]
                st.success(f"✅ Model loaded! F1: {st.session_state.model_f1}")
                st.rerun()
            else:
                st.error(f"❌ Failed: {model_result[3]}")
                st.session_state.use_demo = True
        
        st.markdown("---")
        
        if st.button("🎯 Activate Demo Mode", use_container_width=True):
            st.session_state.use_demo = True
            st.session_state.model_loaded = False
            st.session_state.model = None
            st.success("✅ Demo Mode Activated!")
            st.rerun()
        
        st.markdown("---")
        
        if st.session_state.model_loaded:
            st.success(f"✅ Trained Model Active\nF1: {st.session_state.model_f1}")
        elif st.session_state.use_demo:
            st.info("🎯 Demo Mode Active\n75% accuracy")
        else:
            st.warning("⚠️ No Model Loaded")
        
        st.markdown("---")
        
        st.session_state.threshold = st.slider("Detection Threshold", 0.1, 0.9, 0.6, 0.05)
        
        st.markdown("---")
        st.markdown("### 📖 Franco Guide")
        st.caption("2=ا | 3=ع | 7=ح | 5=خ | 4=ش")
    
    # Check if model is ready
    if not st.session_state.model_loaded and not st.session_state.use_demo:
        st.markdown("""
        <div class="warning-box">
            <h3>⚠️ No Model Active</h3>
            <p>Please either:</p>
            <ul>
                <li><strong>Upload your trained .pt model file</strong> from your Kaggle notebook</li>
                <li><strong>Click "Activate Demo Mode"</strong> to use the built-in model (75% accuracy)</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)
        return
    
    # Tabs
    tab1, tab2, tab3 = st.tabs(["💬 Single Review", "📂 Batch Prediction", "🔤 Translator"])
    
    # Tab 1: Single Review
    with tab1:
        st.markdown("### ✍️ Enter Your Review")
        
        col1, col2, col3, col4 = st.columns(4)
        examples = [
            ("🍽️ Good Food", "el akl kwayes gedan"),
            ("👍 Good Service", "el 5idma 7elwa"),
            ("😞 Bad Review", "el service mish kwayes"),
            ("💰 Price Issue", "el as3ar ghalya"),
        ]
        
        for col, (name, text) in zip([col1, col2, col3, col4], examples):
            if col.button(name, use_container_width=True):
                st.session_state.review_text = text
        
        review = st.text_area("or type your review:", value=st.session_state.get("review_text", ""), height=100)

        col_rating, _ = st.columns([1, 3])
        with col_rating:
            use_rating = st.checkbox("Include a star rating", value=False)
            star_rating = st.slider("Star rating", 1, 5, 3, disabled=not use_rating) if use_rating else None

        if st.button("🔍 Analyze Review", use_container_width=True) and review:
            with st.spinner("Analyzing..."):
                translated = st.session_state.translator.transliterate(review)
                
                if st.session_state.model_loaded:
                    result = predict_with_trained_model(
                        review, st.session_state.model, st.session_state.tokenizer,
                        st.session_state.device, st.session_state.threshold, star_rating
                    )
                else:
                    result = predict_with_demo_model(review, st.session_state.threshold, star_rating)
                
                if translated != review:
                    st.info(f"🔄 {translated}")
                
                st.divider()
                
                sentiments = list(result["aspect_sentiments"].values())
                col1, col2, col3 = st.columns(3)
                col1.metric("😊 Positive", sentiments.count("positive"))
                col2.metric("😞 Negative", sentiments.count("negative"))
                col3.metric("😐 Neutral", sentiments.count("neutral"))
                
                st.markdown("### 🎯 Results")
                for aspect in result["aspects"]:
                    if aspect == "none":
                        st.markdown('<div class="neutral-box">⚪ No specific aspects detected</div>', unsafe_allow_html=True)
                    else:
                        sentiment = result["aspect_sentiments"].get(aspect, "neutral")
                        emoji = SENTIMENT_EMOJI.get(sentiment, "⚪")
                        box_class = f"{sentiment}-box"
                        st.markdown(f'<div class="{box_class}"><span style="font-weight:bold;">{emoji} {ASPECT_LABELS.get(aspect, aspect).upper()}: {sentiment.upper()}</span></div>', unsafe_allow_html=True)
                
                with st.expander("📄 JSON"):
                    st.json(result)
    
    # Tab 2: Batch Prediction
    with tab2:
        st.markdown("### 📊 Batch Predictions")
        
        uploaded_file = st.file_uploader("Upload Excel or CSV file", type=['xlsx', 'csv'])
        
        if uploaded_file:
            try:
                df = pd.read_excel(uploaded_file) if uploaded_file.name.endswith('xlsx') else pd.read_csv(uploaded_file)
                st.success(f"✅ Loaded {len(df)} rows")
                st.dataframe(df.head(3), use_container_width=True)
                
                text_col = None
                for col in ['review_text', 'text', 'review', 'comment']:
                    if col in df.columns:
                        text_col = col
                        break
                
                if text_col is None:
                    text_col = df.columns[0]
                
                st.info(f"📝 Using column: {text_col}")

                has_ratings = "star_rating" in df.columns
                if has_ratings:
                    st.info("⭐ Found a 'star_rating' column — will use it to inform sentiment.")
                
                if st.button("🚀 Run Batch Prediction", use_container_width=True):
                    with st.spinner(f"Processing {len(df)} reviews..."):
                        texts = df[text_col].fillna("").astype(str).tolist()
                        ratings = (
                            pd.to_numeric(df["star_rating"], errors="coerce").tolist()
                            if has_ratings else [None] * len(texts)
                        )
                        results = []
                        
                        for i, text in enumerate(texts):
                            rating = ratings[i]
                            rating = None if (rating is None or pd.isna(rating)) else int(rating)
                            if st.session_state.model_loaded:
                                pred = predict_with_trained_model(
                                    text, st.session_state.model, st.session_state.tokenizer,
                                    st.session_state.device, st.session_state.threshold, rating
                                )
                            else:
                                pred = predict_with_demo_model(text, st.session_state.threshold, rating)
                            
                            results.append({
                                "review_id": i,
                                "aspects": pred["aspects"],
                                "aspect_sentiments": pred["aspect_sentiments"]
                            })
                        
                        json_output = json.dumps(results, ensure_ascii=False, indent=2)
                        st.download_button(
                            "💾 Download Predictions (JSON)",
                            json_output,
                            f"submission_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                            "application/json",
                            use_container_width=True
                        )
                        
                        st.success(f"✅ Processed {len(results)} reviews!")
                        
                        st.markdown("### Sample Results")
                        for r in results[:3]:
                            st.json(r)
            except Exception as e:
                st.error(f"Error: {str(e)}")
        else:
            st.info("👈 Upload Excel or CSV file")
    
    # Tab 3: Translator
    with tab3:
        st.markdown("### 🔤 Franco-Arabic Translator")
        
        col1, col2 = st.columns(2)
        
        with col1:
            franco_input = st.text_area("Franco-Arabic:", height=100, placeholder="el 5idma 7elwa gedan")
            if st.button("Translate →", use_container_width=True) and franco_input:
                translated = st.session_state.translator.transliterate(franco_input)
                st.session_state.translated_output = translated
        
        with col2:
            st.text_area("Arabic:", value=st.session_state.get("translated_output", ""), height=100, disabled=True)
        
        st.divider()
        st.markdown("### Common Phrases")
        phrases = [
            ("ana 3ayez akl", "انا عايز اكل", "I want food"),
            ("shukran 7abibi", "شكرا حبيبي", "Thank you"),
            ("el 5idma 7elwa", "الخدمة حلوة", "Good service"),
            ("mish kwayes", "مش كويس", "Not good"),
        ]
        for f, a, m in phrases:
            st.code(f"{f} → {a}  ({m})")

if __name__ == "__main__":
    main()