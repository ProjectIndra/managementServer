from pymongo import MongoClient
import os
import dotenv

dotenv.load_dotenv()

MONGO_URI = os.environ.get("MONGO_URI")
client = MongoClient(MONGO_URI)
db = client["project-badal-db"]

def setupConnection():
    try:
        client.admin.command('ping')
        print("Pinged your deployment. Successfully connected to MongoDB!")
    except Exception as e:
        print(f"MongoDB Connection Error: {e}")
