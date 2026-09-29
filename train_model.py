import pandas as pd
import pickle
import re

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.model_selection import train_test_split, GridSearchCV, cross_val_score
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, confusion_matrix, classification_report

import matplotlib.pyplot as plt
import seaborn as sns

# -------------------------
# LOAD DATASET
# -------------------------
data = pd.read_csv("dataset.csv")

print("Dataset size:", data.shape)
print(data['label'].value_counts())

# -------------------------
# CLEAN TEXT
# -------------------------
def clean_text(text):
    text = str(text).lower()
    text = re.sub(r'[^a-z\s]', ' ', text)
    return text

data["resume_text"] = data["resume_text"].apply(clean_text)

# Remove empty/short resumes
data = data[data["resume_text"].str.len() > 100]

# -------------------------
# FEATURES
# -------------------------
X = data["resume_text"]
y = data["label"]

vectorizer = TfidfVectorizer(
    stop_words='english',
    ngram_range=(1,2),   # unigram + bigram
    max_df=0.85,
    min_df=2,
    sublinear_tf=True
)

X_vec = vectorizer.fit_transform(X)

# -------------------------
# SPLIT DATA
# -------------------------
X_train, X_test, y_train, y_test = train_test_split(
    X_vec, y, test_size=0.2, stratify=y, random_state=42
)

# -------------------------
# MODEL + GRID SEARCH
# -------------------------
param_grid = {
    "C": [0.5, 1, 1.5, 2]
}

grid = GridSearchCV(
    LogisticRegression(max_iter=2000, class_weight='balanced'),
    param_grid,
    cv=5,
    scoring='accuracy'
)

grid.fit(X_train, y_train)

model = grid.best_estimator_

print("\nBest Parameters:", grid.best_params_)

# -------------------------
# CROSS VALIDATION (REAL ACCURACY)
# -------------------------
cv_scores = cross_val_score(model, X_vec, y, cv=5)

print("\nCross Validation Accuracy:", cv_scores.mean())

# -------------------------
# TEST EVALUATION
# -------------------------
y_pred = model.predict(X_test)

acc = accuracy_score(y_test, y_pred)
print("\nTest Accuracy:", acc)

print("\nClassification Report:\n")
print(classification_report(y_test, y_pred))

# -------------------------
# CONFUSION MATRIX
# -------------------------
cm = confusion_matrix(y_test, y_pred)

plt.figure(figsize=(5,4))
sns.heatmap(cm, annot=True, fmt='d', cmap='Blues',
            xticklabels=["Not Qualified","Qualified"],
            yticklabels=["Not Qualified","Qualified"])

plt.xlabel("Predicted")
plt.ylabel("Actual")
plt.title("Confusion Matrix")
plt.show()

# -------------------------
# SAVE MODEL
# -------------------------
pickle.dump(model, open("model.pkl","wb"))
pickle.dump(vectorizer, open("vectorizer.pkl","wb"))

print("\n✅ Model trained successfully!")
