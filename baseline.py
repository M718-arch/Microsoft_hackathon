"""
Arabic ABSA — Rule-Based Baseline
Generates a valid submission.json using keyword matching.

Use this to:
  1. Get a valid submission on day 1 while the model trains
  2. As a sanity-check / lower bound
  3. As an ensemble component

Run:
    python baseline.py --test_file data/unlabeled_fixed.xlsx \
                       --output    predictions/baseline_submission.json
"""

import json
import re
import argparse
import pandas as pd
from tqdm import tqdm

# ── Keyword Lexicons ──────────────────────────────────────────────────────────
# Arabic + transliterated + common dialect forms

ASPECT_KEYWORDS = {
    "food": [
        "اكل", "أكل", "طعام", "وجبة", "وجبات", "منيو", "قائمة", "مطبخ",
        "طبخ", "مذاق", "طازج", "حار", "بارد", "لذيذ", "مش لذيذ", "تحفة",
        "رائع", "بيتزا", "برجر", "شاورما", "كشري", "فول", "فطار", "غداء",
        "عشاء", "سلطة", "حلويات", "ديسرت", "كيك", "مشروبات", "عصير",
        "قهوة", "شاي", "سندوتش", "وجبه", "food", "meal", "menu",
    ],
    "service": [
        "خدمة", "خدمه", "موظف", "موظفين", "ستاف", "staff", "نادل",
        "نادلين", "كاشير", "مدير", "تعامل", "استقبال", "وقت الانتظار",
        "انتظرت", "بطيء", "سريع", "محترم", "مؤدب", "وقح", "بيساعد",
        "service", "staff", "waiter", "employee",
    ],
    "price": [
        "سعر", "أسعار", "اسعار", "غالي", "رخيص", "مناسب", "تمن",
        "حساب", "فاتورة", "كلف", "قيمة", "مبلغ", "مصاري", "فلوس",
        "price", "expensive", "cheap", "cost", "value",
    ],
    "cleanliness": [
        "نظافة", "نظيف", "نظيفة", "وسخ", "وسخة", "قذر", "قذرة",
        "حمام", "دورة مياه", "نظاف", "نضيف", "نضافة", "hygiene", "clean", "dirty",
    ],
    "delivery": [
        "توصيل", "توصيله", "دليفري", "delivery", "شحن", "وصل",
        "وصول", "متأخر", "متاخر", "سريع", "استلمت", "استلام",
        "السائق", "المندوب", "طلب", "order",
    ],
    "ambiance": [
        "مكان", "جو", "ديكور", "تصميم", "جلسة", "جلسات", "هادئ",
        "هادئة", "صاخب", "ضوضاء", "موسيقى", "موسيقا", "اضاءة",
        "إضاءة", "ترتيب", "ambiance", "atmosphere", "decor", "seating",
    ],
    "app_experience": [
        "تطبيق", "تطبيق الموبايل", "app", "تطبيق محمول", "موقع", "website",
        "سايت", "برنامج", "واجهة", "تصميم التطبيق", "بطيء التطبيق",
        "توقف", "crash", "update", "تحديث", "نوتيفكيشن", "حساب",
        "اشتراك", "دفع", "بطاقة",
    ],
    "general": [
        "عموما", "بشكل عام", "في المجمل", "overall", "generally",
        "مجمل", "كله", "كلها", "جميع", "تجربة كاملة",
    ],
}

POSITIVE_WORDS = {
    "ar": [
        "ممتاز", "رائع", "تحفة", "جيد", "جيد جدا", "جميل", "حلو", "كويس",
        "احسن", "أحسن", "عالي", "فخم", "مميز", "مدهش", "بحبه", "بحبها",
        "نظيف", "نضيف", "سريع", "محترم", "تمام", "عظيم", "بديع", "خرافي",
        "خروفي", "اوييي", "تحفه", "واو", "wow", "5 نجوم", "10/10",
        "ينصح", "أوصي", "مذهل", "أجمل", "الأفضل", "افضل", "يستاهل",
        "اتمنى ارجع", "هرجع", "معجب", "متميز", "ناجح",
    ],
    "en": ["excellent", "great", "amazing", "good", "best", "love", "perfect",
           "wonderful", "fantastic", "awesome", "nice", "clean", "fast"],
    "fr": ["excellent", "super", "magnifique", "bien", "parfait", "beau", "propre"],
}

NEGATIVE_WORDS = {
    "ar": [
        "سيء", "سيئة", "وحش", "وحشة", "زفت", "بايظ", "غلط", "مش كويس",
        "بطيء", "بطيئة", "وسخ", "وسخة", "غالي", "مزعج", "محبط", "كارثي",
        "فضيحة", "مش تمام", "مش ممتاز", "مش راضي", "زعلت", "خيبت",
        "ما عجبني", "معجبنيش", "مخيب", "مخيبة", "ما استاهل", "بلاش",
        "مش هرجع", "مش راجع", "مرة وحدة", "للمرة الأخيرة", "حسبي الله",
        "غلبت", "تعبت", "انزعجت", "رديء", "ردئ",
    ],
    "en": ["bad", "terrible", "awful", "poor", "worst", "horrible", "slow",
           "dirty", "expensive", "rude", "disappointing", "mediocre"],
    "fr": ["mauvais", "terrible", "horrible", "cher", "sale", "lent", "déçu"],
}

NEUTRAL_WORDS = [
    "عادي", "مقبول", "وسط", "معقول", "يمشي", "تمام تمام", "okay", "ok",
    "مناسب", "لا بأس", "مش كتير", "يصلح",
]


def detect_sentiment(text: str, star_rating: int = None) -> str:
    text_l = text.lower()
    pos = sum(1 for w in POSITIVE_WORDS["ar"] + POSITIVE_WORDS["en"] + POSITIVE_WORDS["fr"]
              if w in text_l)
    neg = sum(1 for w in NEGATIVE_WORDS["ar"] + NEGATIVE_WORDS["en"] + NEGATIVE_WORDS["fr"]
              if w in text_l)
    neu = sum(1 for w in NEUTRAL_WORDS if w in text_l)

    # Star rating mentioned inline in the text (e.g. "5 نجوم", "5 star") — treat
    # it like an extra keyword vote so it actually influences the count.
    rating_match = re.search(r"(\d)\s*نجم|(\d)\s*star", text_l)
    inline_rating = None
    if rating_match:
        inline_rating = int(rating_match.group(1) or rating_match.group(2))

    # Structured star_rating column (if provided) — weighted vote, not a hard
    # override, so strong keyword signal in the text can still win out.
    for rating in (star_rating, inline_rating):
        if rating is None:
            continue
        if rating >= 4:
            pos += 1
        elif rating <= 2:
            neg += 1
        else:
            neu += 1

    if pos > neg + neu:
        return "positive"
    elif neg > pos + neu:
        return "negative"
    elif neu > 0:
        return "neutral"

    # No keyword or rating signal at all — fall back to rating if we have one,
    # else default to positive (matches the skew typically seen in these reviews).
    if star_rating is not None:
        if star_rating >= 4:
            return "positive"
        elif star_rating <= 2:
            return "negative"
        return "neutral"
    return "positive"   # default for Arabic reviews with emoji / no keywords


def detect_aspects(text: str, star_rating: int = None) -> list[str]:
    text_l = text.lower()
    found  = []
    for asp, keywords in ASPECT_KEYWORDS.items():
        if any(kw in text_l for kw in keywords):
            found.append(asp)

    if not found:
        # Very short or no keywords — a rating on its own doesn't tell us
        # *which* aspect the review is about, so we still fall back to
        # "general". The rating is used downstream to set its sentiment.
        return ["general"]
    return found


def per_aspect_sentiment(text: str, aspects: list[str], overall_sent: str,
                          star_rating: int = None) -> dict:
    """
    Try to assign sentiments per aspect using local context windows.
    Falls back to the overall sentiment (which already factors in star_rating
    via detect_sentiment). At the clause level, star_rating only breaks ties
    that the local keyword count can't resolve.
    """
    text_l = text.lower()
    result = {}

    # Split on common conjunctions to get local clauses
    clauses = re.split(r'\b(بس|لكن|ولكن|إلا|غير|ماعدا|but|however|though|مع ذلك)\b',
                       text_l)

    for asp in aspects:
        keywords = ASPECT_KEYWORDS.get(asp, [])
        asp_sent = overall_sent   # default

        # Find clause containing this aspect's keyword
        for clause in clauses:
            if any(kw in clause for kw in keywords):
                pos = sum(1 for w in POSITIVE_WORDS["ar"] + POSITIVE_WORDS["en"] if w in clause)
                neg = sum(1 for w in NEGATIVE_WORDS["ar"] + NEGATIVE_WORDS["en"] if w in clause)
                neu = sum(1 for w in NEUTRAL_WORDS if w in clause)
                if pos > neg:
                    asp_sent = "positive"
                elif neg > pos:
                    asp_sent = "negative"
                elif neu > 0:
                    asp_sent = "neutral"
                elif star_rating is not None:
                    # True tie at the clause level — let the rating decide
                    # instead of silently keeping the overall default.
                    if star_rating >= 4:
                        asp_sent = "positive"
                    elif star_rating <= 2:
                        asp_sent = "negative"
                    else:
                        asp_sent = "neutral"
                break

        result[asp] = asp_sent

    return result


def predict_row(row) -> dict:
    text        = str(row["review_text"])
    # star_rating is optional — None (not 3/"neutral") when the column is
    # missing, so we don't silently inject a fake neutral vote for every row.
    raw_rating  = row.get("star_rating", None)
    star_rating = int(raw_rating) if pd.notna(raw_rating) else None
    review_id   = int(row["review_id"])

    aspects = detect_aspects(text, star_rating)
    overall = detect_sentiment(text, star_rating)
    sents   = per_aspect_sentiment(text, aspects, overall, star_rating)

    return {
        "review_id":         review_id,
        "aspects":           aspects,
        "aspect_sentiments": sents,
    }


def main(args):
    df      = pd.read_excel(args.test_file)
    results = []

    for _, row in tqdm(df.iterrows(), total=len(df), desc="Predicting (baseline)"):
        results.append(predict_row(row))

    results.sort(key=lambda x: x["review_id"])

    import os
    os.makedirs(os.path.dirname(args.output) if os.path.dirname(args.output) else ".", exist_ok=True)
    with open(args.output, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    print(f"Saved {len(results)} predictions → {args.output}")
    print("Sample:")
    for r in results[:3]:
        print(f"  {json.dumps(r, ensure_ascii=False)}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--test_file", default="data/unlabeled_fixed.xlsx")
    parser.add_argument("--output",    default="predictions/baseline_submission.json")
    args = parser.parse_args()
    main(args)