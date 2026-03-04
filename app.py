
from enum import Enum
from fastapi import FastAPI,Depends
from pydantic import BaseModel ,Field
from sqlalchemy.orm import Session
from db import get_db
from models import UserMedinfo



app=FastAPI()
     
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

@app.post("/username")
def get_username(User:username):
    return f"Hello, {User.name} I would need to collect some information about you to give you the best advice on how to take care of your health. Please provide me with the following information"

@app.post("/medicinfoept")
def get_medicinfo(medicinfoAdd:medicinfo, db: Session =Depends(get_db)) ->dict:
    score =0
    bmi=calculate_BMI(medicinfoAdd.weight, medicinfoAdd.height)
    if bmi < 18.5:
         score +=1
    elif 18.5 <= bmi < 24.9:
            score +=0
    elif 25 <= bmi < 29.9:
            score +=2
    else:        
          score +=4 

    if medicinfoAdd.smokeRate == SmokeRate.Frequently:
        score +=3
    elif medicinfoAdd.smokeRate == SmokeRate.Moderate:
            score +=1
    elif medicinfoAdd.smokeRate == SmokeRate.Never:
          score +=0

    if medicinfoAdd.bloodPressure < 120:
          score +=0
    elif 120 <= medicinfoAdd.bloodPressure < 130:
            score +=1
    elif 130 <= medicinfoAdd.bloodPressure < 139:
            score +=2      
    else:
          score +=4

    if 60 <= medicinfoAdd.heartRate <= 100:
            score +=0    
    elif medicinfoAdd.heartRate> 100:
            score +=2
    else:
          score +=1

    if medicinfoAdd.age < 30:
            score +=0
    elif 30 <= medicinfoAdd.age < 44:
          score +=1
    elif 45<= medicinfoAdd.age < 59:
          score +=2
    else:
          score +=3

    if medicinfoAdd.existingConditions:
        score += len(medicinfoAdd.existingConditions) * 2
    if medicinfoAdd.bodyTemperature > 37.5:
        score +=1   
    
    if score >=10:
            risk_level = "High Risk"
    elif score >=5:
            risk_level = "Moderate Risk"
    else:
              risk_level = "Low Risk"


    record = UserMedinfo(
        age=medicinfoAdd.age,
        sex=medicinfoAdd.sex,
        weight=medicinfoAdd.weight,
        height=medicinfoAdd.height,
        smoke_rate=medicinfoAdd.smokeRate,
        blood_pressure=medicinfoAdd.bloodPressure,
        heart_rate=medicinfoAdd.heartRate,
        body_temperature=medicinfoAdd.bodyTemperature,
        existing_conditions=", ".join(medicinfoAdd.existingConditions),
        bmi=round(bmi, 1),
        risk_score=score,
        risk_level=risk_level
    )
    db.add(record)
    db.commit()
    db.refresh(record)


    return {
                "score": score,
                "risk_level": risk_level,
                "disclaimer": "This is a general health risk indicator based on WHO primary care screening guidelines, not a medical diagnosis. Please consult a healthcare professional"

              }
        

        





   

    

  

