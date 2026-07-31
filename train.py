"""
Arabic ABSA — Training Script
Model: XLM-RoBERTa-base (multilingual, handles Arabic + dialects + French/English/Italian in test)
Architecture: Shared encoder → two heads
  Head 1: Multi-label aspect detection      (9 binary classifiers)
  Head 2: Per-aspect sentiment classification (aspect × 3 sentiment scores)
Run:
    python train.py --train_file data/train_fixed.xlsx \
                    --val_file   data/validation_fixed.xlsx \
                    --output_dir models/
"""

import argparse
import json
import os
import random
import numpy as np
import pandas as pd
import torch
import torch.nn as nn
from torch.utils.data import Dataset, DataLoader
from transformers import AutoTokenizer, AutoModel, get_linear_schedule_with_warmup
from torch.optim import AdamW
from sklearn.metrics import f1_score
from tqdm import tqdm

# ── Constants ────────────────────────────────────────────────────────────────

ASPECTS   = ["food", "service", "price", "cleanliness",
             "delivery", "ambiance", "app_experience", "general", "none"]
SENTIMENTS = ["positive", "negative", "neutral"]

A2I = {a: i for i, a in enumerate(ASPECTS)}
S2I = {s: i for i, s in enumerate(SENTIMENTS)}
I2A = {i: a for a, i in A2I.items()}
I2S = {i: s for s, i in S2I.items()}

NUM_ASPECTS    = len(ASPECTS)
NUM_SENTIMENTS = len(SENTIMENTS)

# ── Seed ─────────────────────────────────────────────────────────────────────

def set_seed(seed=42):
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)

# ── Dataset ───────────────────────────────────────────────────────────────────

def normalize_star_rating(raw_rating):
    """
    Map a 1-5 star rating to roughly [-1, 1] so it sits on a similar scale to
    the encoder's hidden activations. Missing/unparseable ratings map to 0.0
    (i.e. "no signal"), not to a fake neutral rating of 3 — that distinction
    matters so the model can learn to rely on it only when it's present.
    """
    if raw_rating is None or (isinstance(raw_rating, float) and np.isnan(raw_rating)):
        return 0.0
    try:
        r = float(raw_rating)
    except (TypeError, ValueError):
        return 0.0
    return (r - 3.0) / 2.0  # 1★→-1.0, 3★→0.0, 5★→1.0


class ABSADataset(Dataset):
    """
    Each item returns:
      input_ids, attention_mask
      aspect_labels:    (NUM_ASPECTS,)         float — 1 if aspect present
      sentiment_labels: (NUM_ASPECTS,)         long  — sentiment index per aspect (-1 = not present)
      star_rating:      scalar float           normalized star rating, 0.0 if unavailable
    """
    def __init__(self, df, tokenizer, max_length=128):
        self.tokenizer  = tokenizer
        self.max_length = max_length
        self.records    = []
        self.has_ratings = "star_rating" in df.columns

        for _, row in df.iterrows():
            text    = str(row["review_text"])
            aspects = json.loads(row["aspects"])
            sents   = json.loads(row["aspect_sentiments"])
            rating  = normalize_star_rating(row.get("star_rating"))

            aspect_labels    = np.zeros(NUM_ASPECTS, dtype=np.float32)
            sentiment_labels = np.full(NUM_ASPECTS, -1, dtype=np.int64)  # -1 = absent

            for asp in aspects:
                if asp in A2I:
                    idx = A2I[asp]
                    aspect_labels[idx] = 1.0
                    sent = sents.get(asp, "neutral")
                    sentiment_labels[idx] = S2I.get(sent, 2)

            self.records.append({
                "text":             text,
                "aspect_labels":    aspect_labels,
                "sentiment_labels": sentiment_labels,
                "star_rating":      rating,
            })

        if not self.has_ratings:
            print("  [ABSADataset] No 'star_rating' column found — model will "
                  "train with the feature fixed at 0.0 (no signal) for this split.")

    def __len__(self):
        return len(self.records)

    def __getitem__(self, idx):
        rec = self.records[idx]
        enc = self.tokenizer(
            rec["text"],
            max_length=self.max_length,
            padding="max_length",
            truncation=True,
            return_tensors="pt",
        )
        return {
            "input_ids":        enc["input_ids"].squeeze(0),
            "attention_mask":   enc["attention_mask"].squeeze(0),
            "aspect_labels":    torch.tensor(rec["aspect_labels"],    dtype=torch.float),
            "sentiment_labels": torch.tensor(rec["sentiment_labels"], dtype=torch.long),
            "star_rating":      torch.tensor(rec["star_rating"],      dtype=torch.float),
        }

# ── Model ─────────────────────────────────────────────────────────────────────

class ABSAModel(nn.Module):
    """
    XLM-RoBERTa encoder with two classification heads:
      - aspect_head:    Linear(hidden+1, NUM_ASPECTS)       → binary sigmoid per aspect
      - sentiment_head: Linear(hidden+1, NUM_ASPECTS * 3)   → softmax per aspect
    The "+1" is a normalized star_rating scalar concatenated onto the pooled
    [CLS] embedding — 0.0 when no rating is available for a given example.
    """
    def __init__(self, model_name="xlm-roberta-base", dropout=0.1):
        super().__init__()
        self.encoder = AutoModel.from_pretrained(model_name)
        hidden = self.encoder.config.hidden_size

        self.dropout = nn.Dropout(dropout)

        # Aspect detection head
        self.aspect_head = nn.Linear(hidden + 1, NUM_ASPECTS)

        # Sentiment head — outputs NUM_ASPECTS × NUM_SENTIMENTS logits
        self.sentiment_head = nn.Linear(hidden + 1, NUM_ASPECTS * NUM_SENTIMENTS)

    def forward(self, input_ids, attention_mask, star_rating=None):
        outputs = self.encoder(input_ids=input_ids, attention_mask=attention_mask)
        pooled  = outputs.last_hidden_state[:, 0, :]   # [CLS] token
        pooled  = self.dropout(pooled)

        if star_rating is None:
            star_rating = torch.zeros(pooled.size(0), device=pooled.device)
        pooled = torch.cat([pooled, star_rating.unsqueeze(-1)], dim=-1)  # (B, hidden+1)

        aspect_logits    = self.aspect_head(pooled)                              # (B, A)
        sentiment_logits = self.sentiment_head(pooled).view(-1, NUM_ASPECTS, NUM_SENTIMENTS)  # (B, A, 3)

        return aspect_logits, sentiment_logits

# ── Loss ──────────────────────────────────────────────────────────────────────

def compute_loss(aspect_logits, sentiment_logits, aspect_labels, sentiment_labels):
    """
    aspect_loss:    BCE on all 9 aspect slots
    sentiment_loss: CrossEntropy only on present aspects (where sentiment_labels >= 0)
    """
    # Aspect detection loss — BCE with pos_weight to upweight rare aspects
    pos_weight = torch.tensor([3.0, 1.0, 2.0, 4.0, 4.0, 2.5, 2.0, 3.0, 8.0],
                               device=aspect_logits.device)
    aspect_loss = nn.BCEWithLogitsLoss(pos_weight=pos_weight)(aspect_logits, aspect_labels)

    # Sentiment loss — only where aspect is present
    mask = sentiment_labels >= 0                      # (B, A) bool
    if mask.sum() == 0:
        return aspect_loss

    # Flatten and filter
    sentiment_logits_flat = sentiment_logits.view(-1, NUM_SENTIMENTS)   # (B*A, 3)
    sentiment_labels_flat = sentiment_labels.view(-1)                    # (B*A,)
    mask_flat             = mask.view(-1)                                # (B*A,)

    # Class weights: upweight neutral (very rare)
    class_weights   = torch.tensor([1.0, 1.0, 4.0], device=sentiment_logits.device)
    sentiment_loss  = nn.CrossEntropyLoss(weight=class_weights)(
        sentiment_logits_flat[mask_flat],
        sentiment_labels_flat[mask_flat]
    )

    return aspect_loss + sentiment_loss

# ── Evaluation ────────────────────────────────────────────────────────────────

def evaluate(model, loader, device, threshold=0.5):
    """
    Returns micro-F1 on (aspect, sentiment) pairs — same metric as the competition.
    A prediction is correct only if BOTH the aspect AND its sentiment are right.
    """
    model.eval()
    all_true_pairs, all_pred_pairs = [], []

    with torch.no_grad():
        for batch in loader:
            input_ids      = batch["input_ids"].to(device)
            attention_mask = batch["attention_mask"].to(device)
            star_rating    = batch["star_rating"].to(device)
            aspect_labels  = batch["aspect_labels"].numpy()
            sent_labels    = batch["sentiment_labels"].numpy()

            asp_logits, sent_logits = model(input_ids, attention_mask, star_rating)
            asp_probs  = torch.sigmoid(asp_logits).cpu().numpy()      # (B, A)
            sent_preds = sent_logits.argmax(-1).cpu().numpy()          # (B, A)

            B = asp_probs.shape[0]
            for b in range(B):
                true_pairs, pred_pairs = [], []
                for a in range(NUM_ASPECTS):
                    # True
                    if aspect_labels[b, a] == 1:
                        true_pairs.append((a, sent_labels[b, a]))
                    # Predicted
                    if asp_probs[b, a] >= threshold:
                        pred_pairs.append((a, sent_preds[b, a]))

                all_true_pairs.append(set(true_pairs))
                all_pred_pairs.append(set(pred_pairs))

    # Micro F1 on (aspect_idx, sentiment_idx) pairs
    tp = fp = fn = 0
    for true, pred in zip(all_true_pairs, all_pred_pairs):
        tp += len(true & pred)
        fp += len(pred - true)
        fn += len(true - pred)

    precision = tp / (tp + fp + 1e-9)
    recall    = tp / (tp + fn + 1e-9)
    f1        = 2 * precision * recall / (precision + recall + 1e-9)
    return f1, precision, recall

# ── Threshold Search ──────────────────────────────────────────────────────────

def find_best_threshold(model, loader, device):
    """Search for the best aspect-detection threshold on the validation set."""
    best_t, best_f1 = 0.5, 0.0
    for t in [0.3, 0.35, 0.4, 0.45, 0.5, 0.55, 0.6]:
        f1, _, _ = evaluate(model, loader, device, threshold=t)
        if f1 > best_f1:
            best_f1, best_t = f1, t
    return best_t, best_f1

# ── Training Loop ─────────────────────────────────────────────────────────────

def train(args):
    set_seed(args.seed)
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"Device: {device}")

    # Data
    train_df = pd.read_excel(args.train_file)
    val_df   = pd.read_excel(args.val_file)
    print(f"Train: {len(train_df)} | Val: {len(val_df)}")

    tokenizer = AutoTokenizer.from_pretrained(args.model_name)

    train_ds = ABSADataset(train_df, tokenizer, args.max_length)
    val_ds   = ABSADataset(val_df,   tokenizer, args.max_length)

    train_loader = DataLoader(train_ds, batch_size=args.batch_size, shuffle=True,  num_workers=2)
    val_loader   = DataLoader(val_ds,   batch_size=args.batch_size, shuffle=False, num_workers=2)

    # Model
    model = ABSAModel(args.model_name, dropout=args.dropout).to(device)

    # Optimizer — lower LR for encoder, higher for heads
    encoder_params = list(model.encoder.parameters())
    head_params    = list(model.aspect_head.parameters()) + list(model.sentiment_head.parameters())
    optimizer = AdamW([
        {"params": encoder_params, "lr": args.encoder_lr},
        {"params": head_params,    "lr": args.head_lr},
    ], weight_decay=0.01)

    total_steps   = len(train_loader) * args.epochs
    warmup_steps  = total_steps // 10
    scheduler     = get_linear_schedule_with_warmup(optimizer, warmup_steps, total_steps)

    best_f1 = 0.0
    os.makedirs(args.output_dir, exist_ok=True)

    for epoch in range(1, args.epochs + 1):
        model.train()
        total_loss = 0.0

        for batch in tqdm(train_loader, desc=f"Epoch {epoch}/{args.epochs}"):
            input_ids      = batch["input_ids"].to(device)
            attention_mask = batch["attention_mask"].to(device)
            star_rating    = batch["star_rating"].to(device)
            aspect_labels  = batch["aspect_labels"].to(device)
            sent_labels    = batch["sentiment_labels"].to(device)

            optimizer.zero_grad()
            asp_logits, sent_logits = model(input_ids, attention_mask, star_rating)
            loss = compute_loss(asp_logits, sent_logits, aspect_labels, sent_labels)
            loss.backward()

            nn.utils.clip_grad_norm_(model.parameters(), 1.0)
            optimizer.step()
            scheduler.step()

            total_loss += loss.item()

        avg_loss = total_loss / len(train_loader)
        f1, prec, rec = evaluate(model, val_loader, device)
        print(f"Epoch {epoch} | Loss: {avg_loss:.4f} | Val F1: {f1:.4f} | P: {prec:.4f} | R: {rec:.4f}")

        if f1 > best_f1:
            best_f1 = f1
            torch.save({
                "epoch":       epoch,
                "model_state": model.state_dict(),
                "f1":          best_f1,
                "model_name":  args.model_name,
            }, os.path.join(args.output_dir, "best_model.pt"))
            print(f"  -> Saved best model (F1={best_f1:.4f})")

    # Find best threshold on validation
    print("\nSearching for best threshold...")
    ckpt = torch.load(os.path.join(args.output_dir, "best_model.pt"), map_location=device)
    model.load_state_dict(ckpt["model_state"])
    best_t, best_f1 = find_best_threshold(model, val_loader, device)
    print(f"Best threshold: {best_t:.2f} | F1: {best_f1:.4f}")

    # Save threshold with checkpoint
    ckpt["threshold"] = best_t
    torch.save(ckpt, os.path.join(args.output_dir, "best_model.pt"))
    print(f"\nDone. Best Val F1: {best_f1:.4f}")

# ── CLI ───────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--train_file",  default="data/train_fixed.xlsx")
    parser.add_argument("--val_file",    default="data/validation_fixed.xlsx")
    parser.add_argument("--output_dir",  default="models/")
    parser.add_argument("--model_name",  default="xlm-roberta-base")
    parser.add_argument("--max_length",  type=int,   default=128)
    parser.add_argument("--batch_size",  type=int,   default=16)
    parser.add_argument("--epochs",      type=int,   default=8)
    parser.add_argument("--encoder_lr",  type=float, default=2e-5)
    parser.add_argument("--head_lr",     type=float, default=1e-4)
    parser.add_argument("--dropout",     type=float, default=0.1)
    parser.add_argument("--seed",        type=int,   default=42)
    args = parser.parse_args()
    train(args)