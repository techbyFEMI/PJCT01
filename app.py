
from enum import Enum
from fastapi import FastAPI,Depends
from pydantic import BaseModel ,Field
from sqlalchemy.orm import Session
from db import get_db
from dotenv import load_dotenv
from models import UserMedinfo
from  openai import OpenAI
import os
from fastapi.middleware.cors import CORSMiddleware


load_dotenv()

client =OpenAI(
      base_url="https://openrouter.ai/api/v1",
      api_key=os.getenv("OPENROUTER_API_KEY")
)


app=FastAPI()
     
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)
class sexenum(str, Enum):
    Male="male"
    Female="female"

class SmokeRate(str, Enum):
        Frequently="frequently"
        Moderate="moderate"
        Never="never"

class username(BaseModel):
     name:str

class medicinfo(BaseModel):
    age:int=Field(..., le=120)
    sex:sexenum
    weight:float
    height:float
    smokeRate:SmokeRate
    bloodPressure:float
    heartRate:float
    bodyTemperature:float
    existingConditions:list[str]

def calculate_BMI(weight_kg:float,Heiht_m:float)->float:
    weight_kg=float(weight_kg)
    height_m=float(Heiht_m)
    return weight_kg/(height_m**2)

@app.post("/medicinfoept")
def get_medicinfo(medicinfoAdd: medicinfo, db: Session = Depends(get_db)) -> dict:
    score = 0
    bmi = calculate_BMI(medicinfoAdd.weight, medicinfoAdd.height)

    if bmi < 18.5:
        score += 1
    elif 18.5 <= bmi < 24.9:
        score += 0
    elif 25 <= bmi < 29.9:
        score += 2
    else:
        score += 4

    if medicinfoAdd.smokeRate == SmokeRate.Frequently:
        score += 3
    elif medicinfoAdd.smokeRate == SmokeRate.Moderate:
        score += 1
    elif medicinfoAdd.smokeRate == SmokeRate.Never:
        score += 0

    if medicinfoAdd.bloodPressure < 120:
        score += 0
    elif 120 <= medicinfoAdd.bloodPressure < 130:
        score += 1
    elif 130 <= medicinfoAdd.bloodPressure < 139:
        score += 2
    else:
        score += 4

    if 60 <= medicinfoAdd.heartRate <= 100:
        score += 0
    elif medicinfoAdd.heartRate > 100:
        score += 2
    else:
        score += 1

    if medicinfoAdd.age < 30:
        score += 0
    elif 30 <= medicinfoAdd.age < 44:
        score += 1
    elif 45 <= medicinfoAdd.age < 59:
        score += 2
    else:
        score += 3

    if medicinfoAdd.existingConditions:
        score += len(medicinfoAdd.existingConditions) * 2

    if medicinfoAdd.bodyTemperature > 37.5:
        score += 1

    if score >= 10:
        risk_level = "High Risk"
    elif score >= 5:
        risk_level = "Moderate Risk"
    else:
        risk_level = "Low Risk"

    prompt = f"""
    You are a professional health advisor. Based on the following patient health profile,
    generate a personalized 7-day health plan with daily diet and exercise recommendations.

    Patient Profile:
    - Age: {medicinfoAdd.age}
    - Sex: {medicinfoAdd.sex.value}
    - BMI: {round(bmi, 1)}
    - Blood Pressure: {medicinfoAdd.bloodPressure} mmHg
    - Heart Rate: {medicinfoAdd.heartRate} bpm
    - Body Temperature: {medicinfoAdd.bodyTemperature}C
    - Smoking Status: {medicinfoAdd.smokeRate.value}
    - Existing Conditions: {", ".join(medicinfoAdd.existingConditions) if medicinfoAdd.existingConditions else "None"}
    - Risk Score: {score}
    - Risk Level: {risk_level}

    Instructions:
    - Structure the plan as Day 1 through Day 7
    - Each day should include a morning routine, diet recommendations and exercise
    - Tailor the intensity based on the risk level
    - If risk level is High Risk, include a strong recommendation to see a doctor
    - Keep advice practical and achievable
    - Do not diagnose any condition
    - End with a general wellness tip

    Respond in a clear, friendly and encouraging tone.
    """

    response = client.chat.completions.create(
        model="nvidia/nemotron-3-nano-30b-a3b:free",
        messages=[{"role": "user", "content": prompt}]
    )

    health_plan = response.choices[0].message.content

    record = UserMedinfo(
        age=medicinfoAdd.age,
        sex=medicinfoAdd.sex.value,
        weight=medicinfoAdd.weight,
        height=medicinfoAdd.height,
        smokeRate=medicinfoAdd.smokeRate.value,
        bloodPressure=medicinfoAdd.bloodPressure,
        heartRate=medicinfoAdd.heartRate,
        bodyTemperature=medicinfoAdd.bodyTemperature,
        existingConditions=", ".join(medicinfoAdd.existingConditions),
        bmi=round(bmi, 1),
        risk_score=score,
        risk_level=risk_level
    )
    db.add(record)
    db.commit()
    db.refresh(record)

    return {
        "id": record.id,
        "bmi": round(bmi, 1),
        "risk_score": score,
        "risk_level": risk_level,
        "health_plan": health_plan,
        "disclaimer": "This is a general health risk indicator based on WHO primary care screening guidelines, not a medical diagnosis. Please consult a healthcare professional."
    }