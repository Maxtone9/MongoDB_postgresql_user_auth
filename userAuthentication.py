import uvicorn
from fastapi import FastAPI, Form, UploadFile, File, HTTPException
from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
import pymongo

app = FastAPI()

# PostgreSQL Configuration
DATABASE_URL = "postgresql://admin:asdfgh@127.0.0:5432/db_user_auth"
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class User(Base):
    __tablename__ = "tbl_users"
    id = Column(Integer, primary_key=True, index=True)
    full_name = Column(String, index=True)
    email = Column(String, unique=True, index=True)
    password = Column(String)
    phone = Column(String, unique=True, index=True)

# MongoDB Configuration
mongo_client = pymongo.MongoClient("mongodb://127.0.0:27017/")
mongo_db = mongo_client["user_profiles"]
mongo_collection = mongo_db["profiles"]

# FastAPI Models
class UserCreate(BaseModel):
    full_name: str
    email: str
    password: str
    phone: str

# FastAPI Endpoints

@app.post("/register/")
async def register_user(
    full_name: str = Form(...),
    email: str = Form(...),
    password: str = Form(...),
    phone: str = Form(...),
    profile_picture: UploadFile = File(...),
):
    db = SessionLocal()

    # Check if email already exists in PostgreSQL
    user_exists = db.query(User).filter(User.email == email).first()
    if user_exists:
        db.close()
        raise HTTPException(status_code=400, detail="Email already registered")
    new_user = User(full_name=full_name, email=email, password=password, phone=phone)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    db.close()

    # Store profile picture in MongoDB
    profile_data = {
        "user_id": new_user.id,
        "profile_picture": profile_picture.filename,
    }
    mongo_collection.insert_one(profile_data)

    return {"message": "User registered successfully"}

@app.get("/user/{user_id}/")
async def get_user(user_id: int):
    db = SessionLocal()
    user = db.query(User).filter(User.id == user_id).first()
    db.close()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Fetch profile picture from MongoDB
    profile_data = mongo_collection.find_one({"user_id": user.id})
    user_data = {
        "id": user.id,
        "full_name": user.full_name,
        "email": user.email,
        "phone": user.phone,
        "profile_picture": profile_data.get("profile_picture") if profile_data else None,
    }

    return user_data

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
