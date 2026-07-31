"""
Arabic ABSA — Inference Script
Generates predictions/submission.json for the hidden test set.

Run:
    python predict.py --test_file  data/unlabeled_fixed.xlsx \
                      --model_dir  models/ \
                      --output     predictions/submission.json
"""

import argparse
import json
import os
import pandas as pd
import torch
import torch.nn as nn
from torch.utils.data import Dataset, DataLoader
from transformers import AutoTokenizer, AutoModel
from tqdm import tqdm

# ── Constants (must match train.py) ──────────────────────────────────────────

ASPECTS    = ["food", "service", "price", "cleanliness",
              "delivery", "ambiance", "app_experience", "general", "none"]
SENTIMENTS = ["positive", "negative", "neutral"]
A2I = {a: i for i, a in enumerate(ASPECTS)}
S2I = {s: i for i, s in enumerate(SENTIMENTS)}
I2A = {i: a for a, i in A2I.items()}
I2S = {i: s for s, i in S2I.items()}
NUM_ASPECTS    = len(ASPECTS)
NUM_SENTIMENTS = len(SENTIMENTS)

# ── Model (copy of train.py) ──────────────────────────────────────────────────

def normalize_star_rating(raw_rating):
    """Must match train.py exactly — same normalization used at training time."""
    if raw_rating is None or (isinstance(raw_rating, float) and pd.isna(raw_rating)):
        return 0.0
    try:
        r = float(raw_rating)
    except (TypeError, ValueError):
        return 0.0
    return (r - 3.0) / 2.0


class ABSAModel(nn.Module):
    def __init__(self, model_name="xlm-roberta-base", dropout=0.1):
        super().__init__()
        self.encoder = AutoModel.from_pretrained(model_name)
        hidden = self.encoder.config.hidden_size
        self.dropout       = nn.Dropout(dropout)
        self.aspect_head   = nn.Linear(hidden + 1, NUM_ASPECTS)
        self.sentiment_head = nn.Linear(hidden + 1, NUM_ASPECTS * NUM_SENTIMENTS)

    def forward(self, input_ids, attention_mask, star_rating=None):
        outputs = self.encoder(input_ids=input_ids, attention_mask=attention_mask)
        pooled  = outputs.last_hidden_state[:, 0, :]
        pooled  = self.dropout(pooled)
        if star_rating is None:
            star_rating = torch.zeros(pooled.size(0), device=pooled.device)
        pooled = torch.cat([pooled, star_rating.unsqueeze(-1)], dim=-1)
        asp_logits  = self.aspect_head(pooled)
        sent_logits = self.sentiment_head(pooled).view(-1, NUM_ASPECTS, NUM_SENTIMENTS)
        return asp_logits, sent_logits

# ── Dataset ───────────────────────────────────────────────────────────────────

class TestDataset(Dataset):
    def __init__(self, df, tokenizer, max_length=128):
        self.tokenizer  = tokenizer
        self.max_length = max_length
        self.texts      = df["review_text"].astype(str).tolist()
        self.ids        = df["review_id"].tolist()
        if "star_rating" in df.columns:
            self.ratings = [normalize_star_rating(r) for r in df["star_rating"].tolist()]
        else:
            print("[TestDataset] No 'star_rating' column found — running with "
                  "the feature fixed at 0.0 (no signal) for all rows.")
            self.ratings = [0.0] * len(self.texts)

    def __len__(self):
        return len(self.texts)

    def __getitem__(self, idx):
        enc = self.tokenizer(
            self.texts[idx],
            max_length=self.max_length,
            padding="max_length",
            truncation=True,
            return_tensors="pt",
        )
        return {
            "review_id":      self.ids[idx],
            "input_ids":      enc["input_ids"].squeeze(0),
            "attention_mask": enc["attention_mask"].squeeze(0),
            "star_rating":    torch.tensor(self.ratings[idx], dtype=torch.float),
        }

# ── Prediction ────────────────────────────────────────────────────────────────

def predict(args):
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"Device: {device}")

    # Load checkpoint
    ckpt_path = os.path.join(args.model_dir, "best_model.pt")
    ckpt      = torch.load(ckpt_path, map_location=device)
    model_name = ckpt.get("model_name", "xlm-roberta-base")
    threshold  = ckpt.get("threshold", 0.5)
    print(f"Model: {model_name} | Threshold: {threshold:.2f} | Best Val F1: {ckpt.get('f1', '?'):.4f}")

    tokenizer = AutoTokenizer.from_pretrained(model_name)
    model     = ABSAModel(model_name).to(device)
    model.load_state_dict(ckpt["model_state"])
    model.eval()

    # Data
    test_df = pd.read_excel(args.test_file)
    print(f"Test reviews: {len(test_df)}")

    dataset = TestDataset(test_df, tokenizer, args.max_length)
    loader  = DataLoader(dataset, batch_size=args.batch_size, shuffle=False, num_workers=2)

    results = []

    with torch.no_grad():
        for batch in tqdm(loader, desc="Predicting"):
            review_ids     = batch["review_id"]
            input_ids      = batch["input_ids"].to(device)
            attention_mask = batch["attention_mask"].to(device)
            star_rating    = batch["star_rating"].to(device)

            asp_logits, sent_logits = model(input_ids, attention_mask, star_rating)
            asp_probs  = torch.sigmoid(asp_logits).cpu().numpy()   # (B, A)
            sent_preds = sent_logits.argmax(-1).cpu().numpy()       # (B, A)

            B = asp_probs.shape[0]
            for b in range(B):
                rid      = int(review_ids[b])
                aspects  = []
                asp_sent = {}

                for a in range(NUM_ASPECTS):
                    if asp_probs[b, a] >= threshold:
                        asp_name  = I2A[a]
                        sent_name = I2S[sent_preds[b, a]]
                        aspects.append(asp_name)
                        asp_sent[asp_name] = sent_name

                # Fallback: if nothing detected, use "none" / neutral
                if not aspects:
                    aspects  = ["none"]
                    asp_sent = {"none": "neutral"}

                # Validate: aspect_sentiments keys must exactly match aspects
                assert set(aspects) == set(asp_sent.keys()), \
                    f"Mismatch for review_id {rid}"

                results.append({
                    "review_id":         rid,
                    "aspects":           aspects,
                    "aspect_sentiments": asp_sent,
                })

    # Sort by review_id for cleanliness
    results.sort(key=lambda x: x["review_id"])

    # Validate no missing review_ids
    predicted_ids = {r["review_id"] for r in results}
    all_ids       = set(test_df["review_id"].tolist())
    missing       = all_ids - predicted_ids
    if missing:
        print(f"WARNING: Missing {len(missing)} review_ids: {list(missing)[:10]}")

    os.makedirs(os.path.dirname(args.output) if os.path.dirname(args.output) else ".", exist_ok=True)
    with open(args.output, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    print(f"\nSubmission saved: {args.output}")
    print(f"Total predictions: {len(results)}")
    print(f"Sample:")
    for r in results[:2]:
        print(f"  {json.dumps(r, ensure_ascii=False)}")

# ── Validation Helper ─────────────────────────────────────────────────────────

def validate_submission(path, test_df):
    """Run this before uploading to catch schema errors."""
    ALLOWED_ASPECTS    = set(ASPECTS)
    ALLOWED_SENTIMENTS = set(SENTIMENTS)

    with open(path, encoding="utf-8") as f:
        preds = json.load(f)

    expected_ids = set(test_df["review_id"].tolist())
    pred_ids     = {p["review_id"] for p in preds}
    errors       = []

    if pred_ids != expected_ids:
        missing = expected_ids - pred_ids
        extra   = pred_ids - expected_ids
        if missing: errors.append(f"Missing review_ids: {list(missing)[:5]}")
        if extra:   errors.append(f"Extra review_ids:   {list(extra)[:5]}")

    for p in preds:
        rid   = p["review_id"]
        asps  = p.get("aspects", [])
        sents = p.get("aspect_sentiments", {})

        # Unknown aspects
        bad_asp = [a for a in asps if a not in ALLOWED_ASPECTS]
        if bad_asp:
            errors.append(f"review_id {rid}: unknown aspects {bad_asp}")

        # Unknown sentiments
        bad_sent = [v for v in sents.values() if v not in ALLOWED_SENTIMENTS]
        if bad_sent:
            errors.append(f"review_id {rid}: unknown sentiments {bad_sent}")

        # aspects / aspect_sentiments key mismatch
        if set(asps) != set(sents.keys()):
            errors.append(f"review_id {rid}: aspects/sentiments mismatch "
                          f"{set(asps)} vs {set(sents.keys())}")

    if errors:
        print(f"VALIDATION FAILED — {len(errors)} errors:")
        for e in errors[:20]:
            print(f"  - {e}")
    else:
        print(f"Submission valid. {len(preds)} predictions, no errors.")

    return len(errors) == 0

# ── CLI ───────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--test_file",  default="data/unlabeled_fixed.xlsx")
    parser.add_argument("--model_dir",  default="models/")
    parser.add_argument("--output",     default="predictions/submission.json")
    parser.add_argument("--max_length", type=int, default=128)
    parser.add_argument("--batch_size", type=int, default=32)
    args = parser.parse_args()

    predict(args)

    # Auto-validate after generating
    test_df = pd.read_excel(args.test_file)
    print("\nValidating submission schema...")
    validate_submission(args.output, test_df)