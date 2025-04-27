import os
import pymongo
import time
import sys
from dotenv import load_dotenv

# Load API key securely
load_dotenv()
MONGO_CONNECTION = os.getenv("MONGO_CONNECTION")


directory_path = "."
files = [f for f in os.listdir(directory_path) if f.endswith('txt')]

try:
    client = pymongo.MongoClient(MONGO_CONNECTION)
    db = client["materials"]     # choose your database
    collection = db["transcripts"]  # choose your collection
# return a friendly error if a URI error is thrown 
except Exception as e:
    print(e)
    sys.exit(1)

docs = []
for path in files:
    with open(path, "r") as f:
        print(path)
        text = f.read()
        parts = path.split("_")
        doc = {
            "transcript": text,
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "name": parts[0]
        }
        docs.append(doc)

print(len(docs))
result = collection.insert_many(docs)
print(result.inserted_ids)

print(collection.find().count())



    
