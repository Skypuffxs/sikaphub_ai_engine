import streamlit as st
import pickle
import PyPDF2
import docx
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.naive_bayes import MultinomialNB
from sklearn.metrics import confusion_matrix, accuracy_score
from sklearn.model_selection import train_test_split
import matplotlib.pyplot as plt
import seaborn as sns

# -------------------------
# LOAD MODEL
# -------------------------
try:
    model = pickle.load(open("model.pkl", "rb"))
    vectorizer = pickle.load(open("vectorizer.pkl", "rb"))
except:
    model = None
    vectorizer = None

st.set_page_config(page_title="AI Resume Screening System", layout="wide")

st.title("AI Resume Screening and Applicant Ranking System")

# -------------------------
# TEXT EXTRACTION
# -------------------------
def extract_text(file):
    text = ""
    try:
        if file.type == "application/pdf":
            pdf = PyPDF2.PdfReader(file)
            for page in pdf.pages:
                text += page.extract_text() or ""

        elif file.type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
            doc = docx.Document(file)
            for para in doc.paragraphs:
                text += para.text + " "
    except:
        return ""
    return text.lower()

# -------------------------
# SKILL EXTRACTION
# -------------------------
def extract_skills(text):
    skills_db = [
        "python","java","c++","machine learning","data science",
        "deep learning","sql","excel","communication",
        "leadership","analysis","tensorflow","pandas","numpy"
    ]
    return [skill for skill in skills_db if skill in text]

# -------------------------
# SAFE PREDICTION
# -------------------------
def predict_resume(text):
    vec = vectorizer.transform([text])
    pred = model.predict(vec)[0]
    prob = max(model.predict_proba(vec)[0])
    return pred, prob

# -------------------------
# MENU
# -------------------------
menu = st.sidebar.selectbox(
    "Menu",
    ["Resume Screening", "Train Model (Upload Resumes)"]
)

# =====================================================
# TRAIN MODEL USING RESUMES (HUMAN-IN-THE-LOOP)
# =====================================================
if menu == "Train Model (Upload Resumes)":

    st.header("Train Model Using Uploaded Resumes")

    resume_files = st.file_uploader(
        "Upload Resumes",
        type=["pdf", "docx"],
        accept_multiple_files=True
    )

    training_data = []

    if resume_files:

        st.write("Assign labels:")

        for file in resume_files:
            text = extract_text(file)

            if not text.strip():
                continue

            label = st.selectbox(
                f"{file.name}",
                ["Qualified", "Not Qualified"],
                key=file.name
            )

            training_data.append({
                "resume_text": text,
                "label": 1 if label == "Qualified" else 0
            })

        if st.button("Train Model"):

            if len(training_data) < 5:
                st.warning("Upload at least 5 resumes.")
            else:
                df = pd.DataFrame(training_data)

                X = df["resume_text"]
                y = df["label"]

                vectorizer = TfidfVectorizer(stop_words='english')
                X_vec = vectorizer.fit_transform(X)

                X_train, X_test, y_train, y_test = train_test_split(
                    X_vec, y, test_size=0.2, stratify=y
                )

                model = MultinomialNB()
                model.fit(X_train, y_train)

                y_pred = model.predict(X_test)

                acc = accuracy_score(y_test, y_pred)
                cm = confusion_matrix(y_test, y_pred)

                pickle.dump(model, open("model.pkl", "wb"))
                pickle.dump(vectorizer, open("vectorizer.pkl", "wb"))

                st.success("✅ Model trained successfully!")

                # -------------------------
                # EVALUATION
                # -------------------------
                st.subheader("Model Evaluation")

                st.write(f"Accuracy: {round(acc*100,2)}%")

                fig, ax = plt.subplots()
                sns.heatmap(cm, annot=True, fmt='d', cmap="Blues", ax=ax)
                ax.set_xlabel("Predicted")
                ax.set_ylabel("Actual")
                ax.set_title("Confusion Matrix")

                st.pyplot(fig)

# =====================================================
# RESUME SCREENING
# =====================================================
elif menu == "Resume Screening":

    if model is None or vectorizer is None:
        st.warning("⚠️ Please train a model first.")
        st.stop()

    mode = st.radio("Select Mode", ["Single Resume", "Multiple Resumes"])

    job_description = st.text_area("Job Description (Optional for Ranking)")

    # -------------------------
    # SINGLE
    # -------------------------
    if mode == "Single Resume":

        file = st.file_uploader("Upload Resume", type=["pdf", "docx"])

        if st.button("Evaluate Resume"):

            if file is None:
                st.warning("Please upload a resume.")
            else:
                text = extract_text(file)

                if not text.strip():
                    st.error("Unable to extract text.")
                else:
                    pred, prob = predict_resume(text)

                    st.subheader("Result")

                    if pred == 1:
                        st.success("Classification: Qualified")
                    else:
                        st.error("Classification: Not Qualified")

                    st.write(f"Confidence: {round(prob*100,2)}%")

                    skills = extract_skills(text)
                    st.subheader("Detected Skills")
                    st.write(skills if skills else "No skills detected")

    # -------------------------
    # MULTIPLE
    # -------------------------
    else:

        files = st.file_uploader(
            "Upload Multiple Resumes",
            type=["pdf", "docx"],
            accept_multiple_files=True
        )

        if st.button("Process Resumes"):

            if not files:
                st.warning("Upload resumes.")
            else:

                results = []

                for file in files:

                    text = extract_text(file)

                    if not text.strip():
                        continue

                    pred, prob = predict_resume(text)
                    skills = extract_skills(text)

                    if job_description.strip():
                        job_vec = vectorizer.transform([job_description.lower()])
                        vec = vectorizer.transform([text])
                        similarity = float((vec @ job_vec.T).toarray()[0][0])
                    else:
                        similarity = prob

                    results.append({
                        "Filename": file.name,
                        "Classification": "Qualified" if pred == 1 else "Not Qualified",
                        "Confidence (%)": round(prob*100, 2),
                        "Match Score (%)": round(similarity*100, 2),
                        "Skills": ", ".join(skills)
                    })

                if len(results) == 0:
                    st.error("No valid resumes processed.")
                else:
                    df = pd.DataFrame(results)
                    df = df.sort_values(by="Match Score (%)", ascending=False)

                    st.subheader("Applicant Ranking")
                    st.dataframe(df)

                    top_candidate = df.iloc[0]
                    st.success(f"Top Candidate: {top_candidate['Filename']}")
