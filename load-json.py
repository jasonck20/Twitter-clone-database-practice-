import sys
from pymongo import MongoClient
import subprocess

def load_json(json_file, port_number):
    # Connect to MongoDB
    client = MongoClient("localhost", int(port_number))
    # Create or get the database
    db = client["291db"]
    # Drop existing tweets collection and create a new one
    db['tweets'].drop()


    try:
        subprocess.run(["mongoimport", "--port", str(port_number), "--db", "291db", "--collection", "tweets", "--file", str(json_file)])
        print("Successfully Imported JSON file using mongoimport")
    except subprocess.CalledProcessError as e:
        print(f"Error running mongoimport: {e}")
    tweets_collection = db['tweets']

    # Drop all indexes for the collection
    tweets_collection.drop_indexes()
    tweets_collection.create_index([("content","text")])
    # Create an index on user.username
    tweets_collection.create_index([("user.username")])
    # Recreate the index
    tweets_collection.create_index([("user.followersCount")])
    # Specify the indexes you want to create
    indexes_to_create = [
        [("content", "text")],
        [("user.username")],
        [("likeCount")],
        [("quoteCount")],
        [("retweetCount")]
    ]

    # Create the indexes
    for index_spec in indexes_to_create:
        tweets_collection.create_index(index_spec)


 

def main():
    if len(sys.argv) != 3:
        print("Use the following format for providing command line input: python load_json.py <json_file> <port_number>")
        sys.exit(1)

    json_file = sys.argv[1]
    port_number = sys.argv[2]
    # rm -rf db_folder && mkdir db_folder && mongod --port 65000 --dbpath db_folder &
    # python3 load-json.py farmers-protest-tweets-2021-03-5.json 65000

    load_json(json_file, port_number)

if __name__ == "__main__":
    main()
