from pymongo import MongoClient

client = MongoClient("mongodb://localhost:27017")
db = client["orientation_db"]

# 查看集合列表
print(db.list_collection_names()) 
