# Franco-Arabic Aspect-Based Sentiment Analysis (ABSA)

A deep learning system for Aspect-Based Sentiment Analysis on Arabic and Franco-Arabic restaurant reviews. Uses XLM-RoBERTa for multilingual understanding with **75.6% F1 score**.

---

## Team Information

- **Hackathon**: Franco-Arabic ABSA Challenge
- **Model**: XLM-RoBERTa-base fine-tuned for 9 aspects and 3 sentiments
- **Best F1 Score**: 76%
- **Best Threshold**: 0.6

---

## Project Structure
franco-absa-submission/
├── model_weights.pt 
├── requirements.txt 
├── README.md 
└── submission.json 

---

## Setup Instructions

### 1. Environment Setup

Create a virtual environment (recommended):

**Using Conda:**
```bash
conda create -n franco-absa python=3.10
conda activate franco-absa
```

**Using venv:**
```bash
# Windows
python -m venv franco-absa-env
franco-absa-env\Scripts\activate

# Linux/Mac
python -m venv franco-absa-env
source franco-absa-env/bin/activate
```
**2. Install Dependencies**
```bash
pip install -r requirements.txt
```
**3. Verify Installation**
```bash
python -c "import torch; from transformers import AutoTokenizer; print('✅ All dependencies installed successfully!')"
```
