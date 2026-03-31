from transformers import pipeline

model = pipeline("sentiment-analysis",model="ProsusAI/finbert")

def get_sentiment(text):
    result = model(text)[0]
    return result["label"], result["score"]