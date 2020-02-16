import shutil
import pymongo

if __name__ == "__main__":
	client = pymongo.MongoClient()
	db = client['latex']
	expressions = db["expressions"]
	expressions.delete_many({})