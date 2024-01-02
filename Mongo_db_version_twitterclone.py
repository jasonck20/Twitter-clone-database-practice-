
import sys
import re
from pymongo import MongoClient
from datetime import datetime, timezone



################################################  LOG IN Functions ############################################################

db = None
tweets_collection = None


def welcome():
    """Display the welcome screen and provide options for interactions.
    Returns:
        None
    """
    global db, tweets_collection

    while True:
        # Clear the Screen to begin Sign In/ Login
        # print("Profile account ID: " + str(account_user_id))
        print("\n" + "-"*40)
        print("|          Welcome to the App          |")
        print("-"*40)

        tweets_collection = db['tweets']
    
        print("\nMain Menu:")
        print("1. Search for tweets")
        print("2. Search for users")
        print("3. List top tweets")
        print("4. List top users")
        print("5. Compose a tweet")
        print("6. End Program")

        choice = input("Enter your choice (1-6): ")

        if choice == "1":
            search_tweets()

        elif choice == "2":
            keyword = input("Enter a keyword to search for users: ")
            search_users(keyword)

        elif choice == "3":
            while True:
                field = input("Enter the field to list top tweets \n1. retweetCount, \n2. likeCount, \n3. quoteCount: ")
                if field in ["1","2","3"]:
                    break
            while True:
                n = input("Enter the number of top tweets to list: ")
                if n.isnumeric():
                    break
            list_top_tweets(field, int(n))

        elif choice == "4":
            while True:
                n = input("Enter the number of top users to list: ")
                if n.isnumeric():
                    break
            list_top_users(int(n))

        elif choice == "5":
            # prompt for users to enter a valid tweet
            while True:
                content = input("Enter the content for the new tweet: ")
                if content.strip():  # Check if the content is not empty after stripping whitespaces
                    compose_tweet(content)
                    break
                else:
                    print("Tweet content is empty. Please enter some content.")

        elif choice == "6":
            break

        else:
            print("Invalid choice. Please enter a number from 1 to 6.")



def compose_tweet(content):
    """Compose a new tweet and store it in the database.

    Args:
        content (str): The tweet ID to which the new tweet is a reply (None for new tweets).

    Returns:
        None
    """
    global tweets_collection

    # Get the current date and time in UTC
    current_datetime = datetime.now(timezone.utc)

    # Format the datetime in the desired format
    formatted_date = current_datetime.isoformat()
    # Compose a tweet and insert it into the database

    tweet = {
        "url": None,
        "date": formatted_date,
        "content": content,
        "id": None,
        "user": {
            "username":  "291user",
            "displayname": None,
            "id": None,
            "description": None,
            "rawDescription": None,
            "descriptionUrls": [],
            "verified": None,
            "created": None,
            "followersCount": None,
            "friendsCount": None,
            "statusesCount": None,
            "favouritesCount": None,
            "listedCount": None,
            "mediaCount": None,
            "location": None,
            "protected": None,
            "linkUrl": None,
            "linkTcourl": None,
            "profileImageUrl": None,
            "profileBannerUrl": None,
            "url": None,
        },
        "outlinks": [],
        "tcooutlinks": [],
        "replyCount": None,
        "retweetCount": None,
        "likeCount": None,
        "quoteCount": None,
        "conversationId": None,
        "lang": None,
        "source": None,
        "sourceUrl": None,
        "sourceLabel": None,
        "media": None,
        "retweetedTweet": None,
        "quotedTweet": None,
        "mentionedUsers": None,
        }

    # Insert the tweet into the database
    result = tweets_collection.insert_one(tweet)
    # Check if the insertion was successful
    if result.inserted_id:
        # Print the inserted tweet's ID
        print("Tweet inserted with ID:", result.inserted_id)
        print("Tweet composed successfully!")
    else:
        print("Error inserting tweet.")

################################################ End of LOG IN Functions ######################################################





#################################################### SEARCH tweets #####################################################
def search_tweets():
    """Search for users based on a keyword and display the results.
    
    Returns:
        None
    """
    
    """Implementation is incomplete and needs modification to account for AND semantic in keyword search."""

    global tweets_collection
    
    keywords=input("Enter space seperated keywords for search: ")
    if not keywords:
        print("No keyword searched")
        print("No search results shown")
        return
    
    # tweets_collection.create_index([("content","text")])
    query = {"$text": {"$search": keywords}}

    document = tweets_collection.find(query)
    keyword_list = keywords.split()

    matching_tweets = []
    seen_url=[]
    cnt=1
    
    for tweet in document:
        content_lower = tweet["content"].lower()
        if all(re.search(rf'\b{re.escape(keyword.lower())}\b', content_lower) for keyword in keyword_list) and tweet["url"] not in seen_url:
            seen_url.append(tweet["url"])
            matching_tweets.append(tweet)
            print("Serial Number:", cnt)
            print("ID:", tweet["id"])
            print("Date:", tweet["date"])
            print("Content:", tweet["content"])
            print("Username:", tweet["user"]["username"])
            print("-"*30)
            cnt+=1

    if len(matching_tweets)==0:
        print("No matching tweets found")
        return
        
    prompt = "yes"
    while prompt == "yes":
        try:
            selected_id = int(input("Enter the serial number of the tweet you want to view: "))
            if 1 <= selected_id <= len(matching_tweets):
                prompt = "no"
            else:
                print("Invalid serial number. Please enter a number within the valid range.")
        except ValueError:
            print("Serial number should be an integer")

    print("All fields related to the tweet with serial number", selected_id, "are listed below: ")
    print("-"*90)
    for item in matching_tweets[selected_id-1]:
        print(item,":", matching_tweets[selected_id-1][item])
    return

########################################################################################################################





#################################################### SEARCH users ######################################################
def search_users(keyword):
    """
    Searches for users in the database whose displayname or location contains the given keyword.
    Allows the user to select a specific user to view all their details.
    For users with multiple records, displays the maximum followersCount among those records.

    Args:
        keyword (str): The keyword to search for in users' displayname or location.

    Returns:
        None
    """
    global tweets_collection

    # Regular expression for case-insensitive search and to match keyword as a separate word
    regular_exp = f'\\b{keyword}\\b'
    query = {'$or': [{'user.displayname': {'$regex': regular_exp, '$options': 'i'}},
                     {'user.location': {'$regex': regular_exp, '$options': 'i'}}]}
    projection = {'user': 1, '_id': 0}

    # Fetching results
    results = tweets_collection.find(query, projection)

    # Processing results to handle duplicates based on composite key
    unique_users = {}
    for result in results:
        user = result['user']
        composite_key = (user['username'], user['displayname'], user['location'])
        if composite_key not in unique_users or user['followersCount'] > unique_users[composite_key]['followersCount']:
            unique_users[composite_key] = user

    # Displaying search results
    cnt=1
    matching_users=[]
    print("\nSearch Results:")
    for _, user_info in unique_users.items():
        matching_users.append(user_info)
        print()
        print(f'Serial Number: {cnt}\nUsername: {user_info["username"]}\nDisplay Name: {user_info["displayname"]}\nLocation: {user_info["location"]}')
        print()
        print("-" * 30)
        cnt+=1
    if not unique_users:
        print("No users found with the given keyword.")
        return
        
    prompt = "yes"
    while prompt == "yes":
        try:
            selected_serial_num = int(input("Enter the serial number of the users you want to view: "))
            if 1 <= selected_serial_num <= len(matching_users):
                prompt = "no"
            else:
                print("Invalid serial number. Please enter a number within the valid range.")
        except ValueError:
            print("Serial number should be an integer")
            
    print("\nAll fields related to the users with serial number", selected_serial_num, "are listed below: ")
    
    for item in matching_users[selected_serial_num-1]:
        print()
        print(item,":", matching_users[selected_serial_num-1][item])
    
    print("-"*90)
    return

########################################################################################################################





#################################################### LIST top tweets ####################################################
def list_top_tweets(field, n):
    """List the followers of the current user and display information about them.
    
    This function retrieves the list of users who follow the current user and provides options to
    select and view details about each follower. It also allows the user to follow a selected follower.

    Returns:
        None
    """
    global tweets_collection

    if field == '1':
        counter = 0
        list_1 = []
        mydoc=tweets_collection.find().sort("retweetCount", -1).limit(n)
        for x in mydoc:
            counter += 1
            print('\n', counter,"-"*40,'\n',"Tweet ID: ", x['id'], '\n', "Tweet date: ", x['date'],'\n', "Content: ", x['content'], '\n', "Username: ", x['user']['username'],'\n')
            list_1.append(x)
        while True:
            select = int(input("Select a tweet number to see more information or zero to exit: "))
            if 1 <= select <= n: 
                print(list_1[select - 1])
                break
            elif select == 0:
                break
        
            
    elif field == '2':
        counter = 0
        list_1 =[]
        mydoc=tweets_collection.find().sort("likeCount", -1).limit(n)
        for x in mydoc:
            counter += 1
            print('\n', counter,"-"*40,'\n',"Tweet ID: ", x['id'], '\n', "Tweet date: ", x['date'],'\n', "Content: ", x['content'], '\n', "Username: ", x['user']['username'],'\n')
            list_1.append(x)
        while True:
            select = int(input("Select a tweet number to see more information or zero to exit: "))
            if 1 <= select <= n: 
                print(list_1[select - 1])
                break
            elif select == 0:
                break
    elif field == '3':
        counter = 0
        list_1 = []
        mydoc=tweets_collection.find().sort("quoteCount", -1).limit(n)
        for x in mydoc:
            counter += 1
            print('\n', counter,"-"*40,'\n',"Tweet ID: ", x['id'], '\n', "Tweet date: ", x['date'],'\n', "Content: ", x['content'], '\n', "Username: ", x['user']['username'],'\n')
            list_1.append(x)
        while True:
            select = int(input("Select a tweet number to see more information or zero to exit: "))
            if 1 <= select <= n: 
                print(list_1[select - 1])
                break
            elif select == 0:
                break

########################################################################################################################



#################################################### LIST top users ####################################################
def list_top_users(n):
    """List the followers of the current user and display information about them.
    
    This function retrieves the list of users who follow the current user and provides options to
    select and view details about each follower. It also allows the user to follow a selected follower.

    Returns:
        None
    """
    global tweets_collection


    name_list = []
    counter = 0
    results = tweets_collection.find().sort('user.followersCount', -1)
    for x in results:
        if len(name_list) == n:
            break
        name_list.append(x['user']['username'])
        name_list = list(dict.fromkeys(name_list))

    for i in range(len(name_list)):
        results = tweets_collection.find({'user.username':name_list[i]}).sort('user.followersCount',-1).limit(1)
        for x in results:
            counter += 1
            print('User number ', counter ,'-'*40, '\n', 'Username: ', x['user']['username'], '\n', 'Display name: ', x['user']['displayname'], '\n', 'Followers count: ', x['user']['followersCount'], '\n')

    while True:
        select = int(input("Select a user number to see more information or zero to exit: "))
        if 1 <= select <= n: 
            results = tweets_collection.find({'user.username':name_list[select - 1]}).sort('user.followersCount', -1).limit(1)
            for x in results:
                print(x)
                break
        elif select == 0:
            break
    


########################################################################################################################




def main():
    global db

    if len(sys.argv) != 2:
        print("Please provide the database port number")
        print("Usage: python main.py <mongodb_port>")
        sys.exit(1)
    mongodb_port = sys.argv[1]
    # python3 main.py 65000
    # Connect to MongoDB
    client = MongoClient(f"mongodb://localhost:{mongodb_port}/")
    db = client['291db']

    # displays the options for user
    welcome()   
    # Else we exit the application
    print("Exiting the application...")
    # Close the MongoDB connection
    client.close()
    return

if __name__ == "__main__":
    main()
