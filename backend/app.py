from fastapi import FastAPI, Depends
from sqlalchemy.orm import Session

from database.deps import get_db
from database.models.user import User

app = FastAPI()


@app.get("/")
def root():
    return {"message": "RepRight API is running 🚀"}


@app.post("/create-user")
def create_user(name: str, email: str, db: Session = Depends(get_db)):
    new_user = User(name=name, email=email)

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return {
        "message": "User created",
        "user_id": new_user.user_id
    }