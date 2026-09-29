import pandas as pd
import random

skills = [
    "python", "java", "c++", "machine learning",
    "data science", "deep learning", "sql",
    "excel", "communication", "leadership"
]

data = []

for i in range(1000):

    skill_sample = " ".join(random.sample(skills, random.randint(3,6)))

    experience = random.randint(0,5)
    internships = random.randint(0,3)
    cgpa = round(random.uniform(2.0,4.0),2)

    text = f"""
    Candidate with {skill_sample}, 
    {experience} years experience, 
    {internships} internships, 
    CGPA {cgpa}
    """

    # Better labeling logic
    score = experience + internships + (cgpa * 2)

    label = 1 if score > 6 else 0

    data.append([text.strip(), label])

df = pd.DataFrame(data, columns=["resume_text","label"])

# Balance dataset
df_1 = df[df.label == 1]
df_0 = df[df.label == 0]

min_size = min(len(df_1), len(df_0))

df_balanced = pd.concat([
    df_1.sample(min_size),
    df_0.sample(min_size)
])

df_balanced.to_csv("dataset.csv", index=False)

print("✅ Dataset generated:", df_balanced.shape)
