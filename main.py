from fastapi import FastAPI

app=FastAPI(title="AssignmentTrackerAPI")

@app.get("/")
def home():
    return{"message":"Hello from docker!"}
    