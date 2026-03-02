
from enum import Enum
from os import name
from fastapi import FastAPI
from pydantic import BaseModel ,Field



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
def username(User:username):
    return f"Hello, {User.name} I would need to collect some information about you to give you the best advice on how to take care of your health. Please provide me with the following information"

@app.post("/medicinfoept")
def medicinfo(medicinfoAdd:medicinfo):
    bmi=calculate_BMI(medicinfoAdd.weight, medicinfoAdd.height)
    return{
     "bmi": bmi,
     
}





   

    

  

