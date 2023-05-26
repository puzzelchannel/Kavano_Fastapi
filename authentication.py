from datetime import datetime, timedelta

import jwt
from fastapi import FastAPI, HTTPException, Depends, UploadFile, File
from fastapi import Header
from pydantic import BaseModel
from sqlalchemy import create_engine, Column, Integer, String, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session, relationship

app = FastAPI()

DATABASE_URL = "postgresql://postgres:2703@localhost:5432/task"

SECRET_KEY = "never-give-up"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    password = Column(String)
    records = relationship("Record", back_populates="user")


class Record(Base):
    __tablename__ = "records"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String)
    content = Column(String)
    user_id = Column(Integer, ForeignKey("users.id"))
    user = relationship("User", back_populates="records")


class UserCreate(BaseModel):
    username: str
    password: str


class RegisterResponse(BaseModel):
    message: str


class LoginResponse(BaseModel):
    access_token: str
    token_type: str


class RecordCreate(BaseModel):
    title: str
    content: str


class RecordResponse(BaseModel):
    id: int
    title: str
    content: str
    user_id: int


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def create_tables():
    Base.metadata.create_all(bind=engine)


def create_access_token(data: dict, expires_delta: timedelta):
    to_encode = data.copy()
    expire = datetime.today() + expires_delta
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


@app.post("/register", response_model=RegisterResponse)
def register_user(user: UserCreate, db: Session = Depends(get_db)):
    if db.query(User).filter(User.username == user.username).first():
        raise HTTPException(status_code=400, detail="Username already taken")

    new_user = User(username=user.username, password=user.password)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return {"message": "User registered successfully"}


@app.post("/login", response_model=LoginResponse)
def login_user(user: UserCreate, db: Session = Depends(get_db)):
    stored_user = db.query(User).filter(User.username == user.username).first()

    if not stored_user or stored_user.password != user.password:
        raise HTTPException(status_code=401, detail="Invalid username or password")

    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": stored_user.username}, expires_delta=access_token_expires
    )

    return {"access_token": access_token, "token_type": "bearer"}


# @app.post("/record")
# def upload_record(file: UploadFile = File(...), authorization: str = Header(None)):
#     # Check if the access token is present
#     if not authorization:
#         raise HTTPException(status_code=401, detail="Access token missing")
#
#     # Verify the access token
#     try:
#         payload = jwt.decode(authorization, SECRET_KEY, algorithms=[ALGORITHM])
#         username = payload.get("sub")
#         # You can use the username or perform any additional checks/validation here
#     except jwt.DecodeError:
#         raise HTTPException(status_code=401, detail="Invalid access token")
#
#     # Process the uploaded file
#     # You can access the file using the `file` parameter, e.g., file.filename, file.content_type, etc.
#
#     return {"message": "File uploaded successfully"}


create_tables()

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)


