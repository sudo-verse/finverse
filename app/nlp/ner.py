import spacy

nlp = spacy.load("en_core_web_sm")

def extract_companies(text):
    doc = nlp(text)
    return [ent.text for ent in doc.ents if ent.label_ == "ORG"]