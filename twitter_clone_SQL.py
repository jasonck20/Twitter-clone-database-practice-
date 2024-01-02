import sqlite3
from re import findall
import getpass
import random
import os
import time
from datetime import datetime
connection = None
cursor = None

# Main page where user selects from their options
def main_page():
    main_choice = input("1. Search for tweets\n2. Search for users\n3. Compose a tweet\n4. List followers\n5. Logout\n\nSelect an option: ").lower().strip()

    while main_choice.isdigit() != True or not 1 <= int(main_choice) <= 5:
        main_choice = input("Error. Invalid entry. Please try again.\n1. Search for tweets\n2. Search for users\n3. Compose a tweet\n4. List followers\n5. Logout\n\nSelect an option: ").lower().strip()
    
    if main_choice == '1':
        find_tweet()

    elif main_choice == '2':
        search_for_users(input("Please enter a keyword to retrieve all users or cities that contain that keyword: \n"))

    elif main_choice == '3':
        compose_tweet()

    elif main_choice == '4':
        list_followers()

    elif main_choice == '5':
        logged_in_id = None
        print("Thanks for visiting!\nLogging out...")
        time.sleep(2)
        welcome_screen()

# Allows user to retweet or reply to tweet id specified in parameter
def rt_or_rp(t_id):

    while True:
        rt_rp_choice = input("Would you like to retweet or reply to this tweet?\nEnter 'rt' if you'd like to retweet,\nenter 'rp' if you'd like to reply,\nor enter 'n' to do neither: ").lower().strip()

        if rt_rp_choice == 'rt':
            cursor.execute('INSERT INTO retweets (usr, tid, rdate) VALUES (?, ?, ?);', (logged_in_id, t_id, datetime.today().strftime('%Y-%m-%d')))
            connection.commit()
            return

        elif rt_rp_choice == 'rp':
            compose_tweet(t_id)
            return
        
        elif rt_rp_choice == 'n':
            return
        
        print("Invalid entry. Please try again.")
 


# Prints details of a tweet
def tweet_deets(t_id):
    # Query for # of retweets
    cursor.execute('''SELECT COUNT(*)
                      FROM retweets
                      WHERE retweets.tid = :tweetID''',
                      {'tweetID': t_id})
    
    print("# of retweets:", cursor.fetchone()[0])

    # Query for # of replies
    cursor.execute('''SELECT COUNT(*)
                      FROM tweets
                      WHERE replyto = :tweetID''',
                      {'tweetID': t_id})
    
    print("# of replies:", cursor.fetchone()[0])


    
# Shows 5 most recent tweets on timeline
def show_timeline():

    # Query most recent tweets/retweets from followers and sort by descending order
    cursor.execute('''SELECT tweets.tid, writer, tdate as date, text, replyto
                      FROM tweets, follows
                      WHERE follows.flwer = :uid
                      AND follows.flwee = tweets.writer
                   
                      UNION
                   
                      SELECT tweets.tid, retweets.usr, rdate as date, text, replyto
                      FROM tweets, follows, retweets
                      WHERE follows.flwer = :uid
                      AND follows.flwee = retweets.usr
                      AND tweets.tid = retweets.tid
                      ORDER BY date DESC;''',
                      {'uid': logged_in_id})
    
    return cursor.fetchall()

# Splash page where timeline is displayed
def splash_page(limit):
    os.system('cls' if os.name == 'nt' else 'clear')
    print('\nHello', logged_in_name + "\nWelcome to Twitter!")
    print("----------------------------------")
    print("Your recent timeline:\n")

    request_more = 'y'

    # Total number of tweets possible on timeline
    num_tweets = len(show_timeline())

    # Show timeline to appropriate limit
    curr_timeline = show_timeline()[0:limit]

    # Prints tweets
    print("Tweet no  | Tid | Tweet writer | Tweet date | Tweet text | Reply to\n")
    i = 0
    for tweet_retweet in curr_timeline:
        i += 1
        print("Tweet", i, "| " + ' | '.join(map(str, tweet_retweet)))
        

    request_more = valid_request_more(input("Show more? (Y/N): "))

    # If user wishes to see more tweets
    while request_more == 'y':
        # If all tweets shown
        if limit == num_tweets:
            print("\nNo more tweets to show.")
        # If there's less than 5 tweets left to show, adjust limit appropriately
        elif limit + 5 > num_tweets:
            splash_page(num_tweets)
        # Else increase limit by 5
        else:
            splash_page(limit+5)

    # Allow user to check tweet details or goto main page
    while True:
        sp_choice = input("\nEnter a tweet # to see details,\nor type 'main' to proceed to the main page.\n\nChoose option: ").lower().strip()

        if sp_choice.isdigit() and 1 <= int(sp_choice) <= len(curr_timeline):
            selected_tweet = curr_timeline[int(sp_choice)-1][0]
            tweet_deets(selected_tweet)
            rt_or_rp(selected_tweet)

        elif sp_choice == 'main':
            main_page()
        
        print("Error. Invalid selection.")
            
# Checks validity of request_more input
def valid_request_more(rm):
    rm = rm.lower().strip()
    while rm != 'n' and rm != 'y':
        rm = input("\nError. Invalid entry.\nShow more? (Y/N): ").lower().strip()
    
    return rm

# Registers user into database
def register_user(data):
    cursor.execute('INSERT INTO users (usr, pwd, name, email, city, timezone) VALUES (?, ?, ?, ?, ?, ?);', data)
    connection.commit()

# Returns true if string contains digit
def contains_digits(s):
    if any(c.isdigit() for c in s):
        return True
    return False

# Login screen where user can log in
def login_screen():
    uid = input("Enter your user ID: ")
    password = getpass.getpass("Enter your password: ")

    cursor.execute('SELECT name FROM users WHERE usr= :uid AND pwd = :pw',
                       {'uid': uid, 'pw': password})
    
    name = cursor.fetchone()

    if name is not None:
        print("Success! Logging in...")
        time.sleep(2)
        global logged_in_id
        global logged_in_name
        logged_in_id = uid
        logged_in_name = name[0]
        splash_page(5)
    
    else:
        print("No user with these credentials exist.")
        login_screen()

# Generates uid and ensures it's not already in database
def generate_unique_id():
    user_id = random.randint(10000000000, 99999999999)
    
    cursor.execute('SELECT * FROM users WHERE usr= :uid',
                       {'uid': user_id},)
    
    is_unique = cursor.fetchone() is None

    # While ID is not unique, regenerate
    while not is_unique:
        user_id = random.randint(1000000000, 9999999999)
        cursor.execute('SELECT * FROM users WHERE usr= :uid',
                       {'uid': user_id},)
        is_unique = cursor.fetchone() is None

    return user_id

# User creates valid password
def password_creation():
    password = getpass.getpass("Enter a password between 10 and 20 characters: ")

    # Ensure password is greater than 10 characters but less than 20
    while not 5 <= len(password) <= 20:
       password = getpass.getpass("Error. Password must be between 5 and 20 characters.\nPlease try again.\nEnter a password between 10 and 20 characters: ") 

    # Hide password while being inputted
    password_conf = getpass.getpass("Re-enter your password: ")

    # If passwords match
    if password == password_conf:
        return password
    
    else:
        os.system('cls' if os.name == 'nt' else 'clear')
        print("Your passwords do not match. Please try again.\n")
        password = password_creation()
        return password

# Screen where user creates account
def create_acc_screen():
    name = input("Enter your name: ")
    
    while contains_digits(name):
        name = input("Error. Name cannot include numbers.\nPlease try again.\nEnter your name: ")

    while not 2 <= len(name) <= 20:
        name = input("Error. Name must be between 2 and 20 characters.\nPlease try again.\nEnter your name: ")

    email = input("Enter your email: ")

    while "@" not in email or email == '@':
        email = input("Error. It appears your email is not valid.\nPlease try again.\nEnter your email: ")

    city = input("Enter your city of residence: ")

    while contains_digits(city):
            city = input("Error. Your city of residence cannot include numbers.\nPlease try again.\nEnter your city: ")

    timezone = input("Enter your timezone by UTC offset (-12 to +14): ")
    timezone_range = [str(i) for i in range(-12, 15)]

    while timezone not in timezone_range:
        timezone = input("Error. Timezone must be between -12 and +14.\nPlease try again.\nEnter your timezone: ")

    user_id = generate_unique_id()

    pwd = str(password_creation())
    print(pwd)

    user_data = (user_id, pwd, name, email, city, timezone)

    register_user(user_data)

    print("Your unique User ID is:", user_id, "\nWrite it down so you can log in.")
    
    print("\nYour account has been successfully created.\nWrite it down so you can log in.\nSending you to login page...\n")

    login_screen()

# Welcome screen where user can register, login, or exit the program.
def welcome_screen():
    with open('login_page.txt', 'r') as file:
        data = file.read()

    os.system('cls' if os.name == 'nt' else 'clear')

    login_choice = input(data).strip().lower()

    while True:
        
        if login_choice == '1':
            os.system('cls' if os.name == 'nt' else 'clear')
            login_screen()

        elif login_choice == '2':
            os.system('cls' if os.name == 'nt' else 'clear')
            create_acc_screen()

        elif login_choice == 'q':
            os.system('cls' if os.name == 'nt' else 'clear')
            print("You are now leaving twitter.\nPlease visit again soon!")
            time.sleep(2)
            exit()

        login_choice = input("\nIncorrect option.\nPlease type '1' (Login), '2' (Create account) or 'q' to quit: ")


def connect(path):
    global connection, cursor

    connection = sqlite3.connect(path)
    cursor = connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON;")
    connection.commit()
    return


def create_tables():
    global connection, cursor

    cursor.execute('''CREATE TABLE IF NOT EXISTS users ( 
                   usr INT UNIQUE, 
                   pwd TEXT, 
                   name TEXT,
                   email TEXT, 
                   city TEXT, 
                   timezone FLOAT,
                   PRIMARY KEY (usr))''')

    cursor.execute('''CREATE TABLE IF NOT EXISTS follows (
                   flwer TEXT, 
                   flwee TEXT, 
                   start_date DATE, 
                   PRIMARY KEY (flwer, flwee), 
                   FOREIGN KEY(flwer) REFERENCES users(usr), 
                   FOREIGN KEY(flwee) REFERENCES users(usr))''')

    cursor.execute('''CREATE TABLE IF NOT EXISTS tweets ( 
                   tid INTEGER , 
                   writer INTEGER, 
                   tdate DATE, 
                   text TEXT, 
                   replyto INTEGER, 
                   PRIMARY KEY (tid),
                   FOREIGN KEY(writer) REFERENCES users(usr)
                   FOREIGN KEY(replyto) REFERENCES users(usr))''')

    cursor.execute('''CREATE TABLE IF NOT EXISTS hashtags ( 
                   term TEXT, 
                   PRIMARY KEY (term))''')

    cursor.execute('''CREATE TABLE IF NOT EXISTS mentions ( 
                   tid INTEGER, 
                   term TEXT, 
                   PRIMARY KEY (tid, term), 
                   FOREIGN KEY(tid) REFERENCES tweets(tid), 
                   FOREIGN KEY(term) REFERENCES hashtags(term))''')

    cursor.execute('''CREATE TABLE IF NOT EXISTS retweets (
                   usr TEXT, 
                   tid INTEGER, 
                   rdate DATETIME, 
                   PRIMARY KEY (usr, tid), 
                   FOREIGN KEY(usr) REFERENCES users(usr), 
                   FOREIGN KEY(tid) REFERENCES tweets(tid))''')

    cursor.execute('''CREATE TABLE IF NOT EXISTS lists (
                   lname TEXT UNIQUE,
                   owner TEXT,
                   PRIMARY KEY(lname)
                   FOREIGN KEY(owner) REFERENCES users(usr))''')

    cursor.execute('''CREATE TABLE IF NOT EXISTS includes (
                   lname TEXT,
                   member TEXT,
                   PRIMARY KEY (lname, member),
                   FOREIGN KEY (lname) REFERENCES lists(lname),
                   FOREIGN KEY (member) REFERENCES users(usr))''')
    
    connection.commit()

def set_up(keyword):
    # This function will add '%' character to the front and back of each separated keyword
    # This is necessary to prepare the string for use in SQL query later
    # Returns a list containing all the modified keywords

    add_string = '%'
    list_of_keywords=[]
    for i in range(len(keyword)):
        result=keyword[i][:0] + add_string + keyword[i][0:]
        result=result+add_string
        list_of_keywords.append(result)

    return list_of_keywords

def search_tweets(keyword): 
    # This function takes in a keyword(subtext)
    # Uses SQL query to access database
    # Grabs text, date, and tweet id from tweets which have subtext matching the provided keyword
    # Returns all of the text, date, tweet id obtained

    cursor.execute("select text, tdate, tid, writer from tweets where text like ?", (keyword, ))
    rows=cursor.fetchall()
    return rows

def search_mentions(keyword):
    # This function takes in a keyword(hashtag)
    # Uses SQL query to access database
    # Grabs text, date, and tweet id from tweets which have tweet id in mentions table and mentions term matches keyword
    # Returns all of the text, date, tweet id obtained

    keyword=keyword.replace("#","")
    cursor.execute("select text, tdate, t1.tid, t1.writer from tweets t1, mentions m1 where m1.term like ? and m1.tid = t1.tid", (keyword,))
    rows=cursor.fetchall()
    return rows

def select_tweet(tweet_num, offset):
    # Checks if there even exists a tweet in the list
    if len(tweet_num) == 0:
       return
    
    # If there is, then we can ask which tweet they want to see stats for
    select = int(input("Select tweet number!(must be valid integer): "))
    select -= 1

    # Make sure user inputs number within the range
    if select >= len(tweet_num) or select < 0:
        select_tweet(tweet_num, offset)
    else:
        # Display the chosen tweet
        # Grab the statistics of that tweet
        print("Tweet :", tweet_num[select][0])
        get_stat(tweet_num, select)

def get_stat(tweet_num, select):
    # This function will return the number of retweets and replies of a given tweet
    # Then prompt what user wants to do with the tweet

    # SQL queries to grab number of retweets and replies
    tid = tweet_num[select][2]
    cursor.execute("select * from tweets where replyto = ?", (tid, ))
    rows=cursor.fetchall()
    no_of_replies = len(rows)
    cursor.execute("select * from retweets where tid = ?", (tid, ))
    rows=cursor.fetchall()
    no_of_retweets = len(rows)

    # Printing our values
    print("Number of Retweets: ", no_of_retweets)
    print("Number of Replies: ", no_of_replies)

    rep_or_ret(tweet_num, select)

def retweet(tweets, select):
    cursor.execute("select * from retweets where ? = usr and ? = tid", (logged_in_id, tweets[select][2], ))
    rows=cursor.fetchall()
    if len(rows)!=0:
        print("Already retweeted!")
    else:
        rdate = datetime.now().strftime('%Y-%m-%d')
        cursor.execute("insert into retweets values (?, ?, ?);", (logged_in_id, tweets[select][2], rdate, ))
        connection.commit()
        print("Succesfully retweeted!! \n")
    rep_or_ret(tweets, select)


def reply(tweets, select):
    compose_tweet(tweets[select][2])

def rep_or_ret(tweets, select):
    # This function allows user to retweet, reply or go back to search for a tweet using keyword
    usr_input = input("Type 1 to reply or 2 to retweet or Q to go back to search : ")
    if usr_input == '1':
      #jump to compose a tweet function 
        reply(tweets, select)
    elif usr_input == '2':
        # retweet
        # Need to check who is logged in for usr value, can grab tid from tweets[select], and rdate from date function
        retweet(tweets, select)
    elif usr_input == 'Q' or usr_input == 'q':
        print('\n')
        main_page()

def display_more(checked_tweets, offset):
    # Function allows user to see next top 5 tweets from the list
    request_more = input("Show more? (Y/N): ")
    if request_more == 'Y' or request_more == 'y':
        if offset+5 < len(checked_tweets):
            for i in range(offset, offset+5):
                print('Tweet  ', i+1, '|', checked_tweets[i][2], ' |', checked_tweets[i][1], '| ', checked_tweets[i][3], ' |', checked_tweets[i][0])
        else:
            for i in range(offset, len(checked_tweets)):
                print('Tweet  ', i+1, '|', checked_tweets[i][2], ' |', checked_tweets[i][1], '| ', checked_tweets[i][3], ' |', checked_tweets[i][0])

      # If there is no more tweets to show after 
      # Let user know and return offset
        if len(checked_tweets) < offset + 5:
            print("No more tweets with matching keyword!!")
            return offset
      # Otherwise ask again if user wants to see more
        else:
            display_more(checked_tweets, offset + 5)

    # If user decide to stop, he can choose to select a tweet
    elif request_more == 'N' or request_more == 'n':
      select_tweet(checked_tweets, offset)
    # In case user inputs invalid choice, ask again
    else: 
      display_more(checked_tweets, offset)
      
def take_second(elem):
    return elem[1]

def find_tweet():
    # First we need to use split() so that we separate keywords if there are more than one
    # We also need to use our set_up function to prepare the keywords for use in SQL queries
    keywords = input("Search tweet: ")
    print("Tweet no  | Tid | Tweet date | Tweet writer | Tweet text ")
    keywords = keywords.split()
    keywords = set_up(keywords)

    # Remove duplicate keywords
    keyword_no_dup = list(dict.fromkeys(keywords))

    # Set variables for use 
    checked_tweets = []
    display_num = 5
    offset = 0

    # Now we need to decide if keyword is a hashtag or just a subtext of a tweet
    for i in range(len(keyword_no_dup)):
        # Checks if there is '#' character, which indicates a term is a hashtag
        # Else, we can be sure the keyword is a subtext
        if keyword_no_dup[i][1] == '#':
            tweets_containing = search_mentions(keyword_no_dup[i])
            for i in range(len(tweets_containing)):
                checked_tweets.append(tweets_containing[i])
        else:
            tweets_containing=search_tweets(keyword_no_dup[i])
            for i in range(len(tweets_containing)):
                checked_tweets.append(tweets_containing[i])
    
    # Next step is to remove duplicate tweets from the list containing all matching tweets
    checked_tweets = list(dict.fromkeys(checked_tweets))
    # We also need to sort the list by the date from latest to oldest
    checked_tweets.sort(key=take_second, reverse=True)

    # Now we need to display the top 5 tweets from the list
    if len(checked_tweets) > 5:
        # Here we check if there are more than 5 tweets in the list
        # If that is the case, we will only display 5 tweets from the top of the list
        for i in range(5):
            print('Tweet  ', i+1, '|', checked_tweets[i][2], ' |', checked_tweets[i][1], '| ', checked_tweets[i][3], ' |', checked_tweets[i][0])
        # After displaying top 5 tweets, we need to ask if user wants to see more
        offset = display_more(checked_tweets, display_num)
    elif len(checked_tweets) >= 1:
        # If there is less than 5 tweets present in the list
        # We show all tweets and let the user know there no more tweets to display
        # We also skip asking user if they want to see more
        
        for i in range(len(checked_tweets)):
            print('Tweet  ', i+1, '|', checked_tweets[i][2], ' |', checked_tweets[i][1], '| ', checked_tweets[i][3], ' |', checked_tweets[i][0])
        print("No more tweets with matching keyword!!")

    else:
        print("No more tweets with matching keyword!!")
        find_tweet()

        
    
    # Lastly we ask user to choose a tweet so we can show stats for that specific tweet

    select_tweet(checked_tweets, offset)

# 2. search for users
def search_for_users(keyword):  
    page = 0
    page_size = 5

    while True:
        offset = page * page_size

        search_query = '''
        SELECT usr, name, city
        FROM users
        WHERE name LIKE ?
        OR (city LIKE ? AND name NOT LIKE ?)
        ORDER BY CASE WHEN name LIKE ? THEN 1 ELSE 2 END,
                 CASE WHEN name LIKE ? THEN LENGTH(name) ELSE LENGTH(city) END
        LIMIT 5 OFFSET ?
        '''
        search_keyword = f"%{keyword}%"
        cursor.execute(search_query, (search_keyword, search_keyword, search_keyword, search_keyword, search_keyword, offset))
        results = cursor.fetchall()
        
        # No users found of that keyword
        if not results:
            if page > 0:
                print("No more users found.")
            else:
                print("No user found.")
            return
        
        # print out user and city
        for index, (usr, name, city) in enumerate(results, start = 1):
            print(f"{index}. {name} from {city} city.")

        user_input = input("\nEnter a number to see more about that user, 'm' to see more users or 'q' to quit: ").lower()
        if user_input == 'm':
            page += 1
            continue
        elif user_input == 'q':
            main_page()

        # if user choice is a number
        else:
            try:
                user_choice = int(user_input)
                
                # Choice have to be greater than 1 and not greater than the result
                if 1 <= user_choice <= len(results):
                    selected_user_id = results[user_choice - 1][0]
                    user_information(selected_user_id)
                    more_option(selected_user_id)
                else:
                    print("Invalid selection. Please choose a valid number.\n")
                    

            except ValueError:
                print("Invalid input")

def user_information(user_id):
    global connection, cursor

    # Get the user information
    user_query = '''
    SELECT *
    FROM users
    WHERE usr = ?;'''
    cursor.execute(user_query, (user_id,))
    user_info = cursor.fetchone()

    print(f"User Details: \n Name: {user_info[2]} \n Email: {user_info[3]} \n City: {user_info[4]} \n Timezone: {user_info[5]}")
    print("\n Stat of user: ")

    # Get number of tweets
    nTweets_query = '''
    SELECT COUNT (*)
    FROM tweets
    WHERE writer = ?;'''
    cursor.execute(nTweets_query, (user_id,))
    tweets_count = cursor.fetchone()[0]
    print(f"Number of tweets: {tweets_count}")  

    # Get number of followers
    nFollowers_query = '''
    SELECT COUNT (*)
    FROM follows
    WHERE flwee = ?;'''
    cursor.execute(nFollowers_query, (user_id,))
    followers_count = cursor.fetchone()[0]
    print(f"Number of followers: {followers_count}")

    # Get number of users being followed
    nFollowing_query = '''
    SELECT COUNT (*)
    FROM follows 
    WHERE flwer = ?;'''
    cursor.execute(nFollowing_query, (user_id,))
    following_count = cursor.fetchone()[0]
    print(f"Number of users being followed: {following_count}")

    # Get 3 most recent tweets
    recent_tweets_query = '''
    SELECT text, tdate
    FROM tweets
    WHERE writer = ?
    ORDER BY tdate
    DESC LIMIT 3;'''
    cursor.execute(recent_tweets_query, (user_id,))
    recent_tweets = cursor.fetchall()
    print("Recent Tweets (up to 3 tweets):")
    for tweet in recent_tweets:
        text, tdate = tweet
        print(f" - {tdate}: {text}")

def more_option(user_id):
    while True:
        user_input = input("\nEnter 'f' to follow this user, 't' to see more tweets, or 'b' to go back: ").lower()
        print('-'*20)
    
        if user_input == 'f':
            follow(user_id)
                        
        elif user_input == 't':
            see_more_tweets(user_id)
        elif user_input == 'b':
            break
        else:
            print("Invalid option. Please try again.")

def follow(fid):
    '''
    Step 1. Check if the user has already followed the selected person
    Step 2. If Yes: Back to the follower list
            If No: follow the selected person (insert this into follows)

    Params:
        fid (int) : the id of the selected person
    '''
    global connection, cursor, logged_in_id

    # Find all followees of the current user
    follower = (logged_in_id,)
    cursor.execute("SELECT f.flwee FROM follows f WHERE f.flwer = ?;", follower)
    followee_set = cursor.fetchall()
    
    # Check if the user has already followed the selected person; if yes return -1
    for followee in followee_set:
        if followee[0] == int(fid):
            print("You have already followed this user. Please select another user.")
            return -1
    
    # If no, record this action in the table (follows)
    start_date = datetime.now().strftime('%Y-%m-%d')
    insertions = (logged_in_id, fid, start_date)
    cursor.execute("INSERT INTO follows VALUES (?, ?, ?);",insertions)
    connection.commit()

    # Display
    print('-'*20)
    print("You have succeessfully followed the user!")
    print('-'*20)
    return



def see_more_tweets(user_id):
    more_tweets_query = '''
    SELECT text, tdate
    FROM tweets
    WHERE writer = ?
    ORDER BY tdate DESC;
    '''
    cursor.execute(more_tweets_query, (user_id,))
    tweets = cursor.fetchall()
    for tweet in tweets:
        text, tdate = tweet
        print(f"{tdate}: {text}")   

# 3. Compose a tweet
def update_tweets(tid, tdate, text, replyto):
    '''
    Updates the new tweet in the table (tweets)

    Params:
        tid (int): the tid of the new tweet
        tdate (str): the time that is being catched
        text (str): the content of the tweet
        replyto (int): the tid of the tweet that is being replied
    '''
    global connection, cursor, logged_in_id
    insertions = (tid, logged_in_id, tdate, text, replyto)
    cursor.execute("INSERT INTO tweets VALUES (?, ?, ?, ?, ?);",insertions)
    connection.commit()
    return


def update_mentions(tid, tags):
    '''
    Record the tags of the new tweet in mentions table

    Params:
        tid (int): the tid of the new tweet
        text (str): the content of the new tweet

    Return:
        tags (list): all tags that are being mentioned
    '''
    global connection, cursor

    # Record each term into table
    for term in tags:
        insertions = (tid, term)
        cursor.execute("INSERT INTO mentions VALUES (?, ?);", insertions)
        
    connection.commit()
     
    return

def update_hashtags(text):
    '''
    Update the tags if this is the first time they are being mentioned

    Params:
        tags (list): all tags that are being mentioned
    '''
    global connection, cursor

    # Use regular expression to find the tags
    regex = '#\s*(\w+)'
    tags = findall(regex, text)

    # For each term, if it does not exist in the table, insert it
    for term in tags:
        insertions = (term, term)
        cursor.execute("INSERT INTO hashtags SELECT ? WHERE NOT EXISTS (SELECT * FROM hashtags WHERE lower(term) = lower(?));",insertions)
    connection.commit()

    return tags

def compose_tweet(replyto = None):
    '''
    Workflow

    Params:
        replyto (int): optional. the tid of the tweet that is being replied
    '''
    global connection, cursor, logged_in_id

    # 1. Recieve a text
    print('-'*10)
    print("Please write down your text here:")
    text = input()
    tdate = datetime.now().strftime('%Y-%m-%d')

    # 2. Generate a tid
    cursor.execute("SELECT MAX(t.tid) FROM tweets t")
    tid = cursor.fetchone()
    tid = tid[0]
    tid += 1
    
    # 3. Update tables
    update_tweets(tid, tdate, text, replyto)
    tags = update_hashtags(text)
    update_mentions(tid, tags)
    print("-"*20)
    print("You have sccessfully post a tweet!")
    print("-"*20)
    #return
    main_page()

# 4. List followers
def more_tweet(fid):
    '''
    Step 1. Display all the tweets of the selected person
    Step 2. Ask the next action

    Params:
        fid (int) : the id of the selected person    
    '''
    global connection, cursor, logged_in_id

    # Find all the tweets of the selected person
    follower = (fid,)
    cursor.execute("SELECT t.tid, t.tdate , t.'text', t.replyto FROM tweets t  WHERE t.writer = ? ORDER BY t.tdate DESC ", follower)
    all_tweets = cursor.fetchall()
    connection.commit()

    # Display
    print('-'*20)
    print("Here are all the tweets..")
    for tweet in all_tweets:
        if tweet[3] == None:
            print("(tid " + str(tweet[0]) + ')' + tweet[1] + ': ' + tweet[2])
        else:
            print("(tid " + str(tweet[0]) + ')' + tweet[1] + ': ' + tweet[2] + "    (reply to user id " + str(tweet[3]) + "'s tweet)")

    # Ask the next action, continue to ask until a valid answer is recieved
    valid = False
    while not valid:
        print('-'*20)
        print("Select the next action:\na. follow this user\nb. back to the follower list\nc. back to the main menu \nPlease enter the letter.")
        selection = input()

        # if the user chooses A or a, then follows this selected person
        if selection.lower() == 'a':
            error = follow(fid)

            # if the user has already followed this person, redisplay the follower list
            if error == -1:
                list_followers()
            valid = True

        # if the user chooses b or B, then back to the main menu
        elif selection.lower() == 'b':
            list_followers()
            valid = True

        # if the user chooses C or c, then back to the main menu
        elif selection.lower() == 'c':
            valid = True

        # Others are invalid answers
        else:
            print(selection, "is not a valid option. Please try again.")


    return

def more_information(fid):
    '''
    Display the account information of the selected user

    Params:
        fid (int): the id of the selected person
    '''
    global connection, cursor

    follower = (fid,)

    # the number of tweets
    cursor.execute("SELECT COUNT(*) FROM tweets t WHERE t.writer = ?;", follower)
    num_tweet = cursor.fetchone()

    # the number of retweets
    cursor.execute("SELECT COUNT(*) FROM retweets r WHERE r.usr = ?;", follower)
    num_retweet = cursor.fetchone()    

    # the number of followings
    cursor.execute("SELECT COUNT(*) FROM follows f WHERE f.flwer = ?;", follower)
    following = cursor.fetchone()

    # the number of followers
    cursor.execute("SELECT COUNT(*) FROM follows f WHERE f.flwee = ?;", follower)
    followers_of_follower = cursor.fetchone()

    # 3 recent tweets (ignore ties)
    cursor.execute("SELECT t.tid, t.tdate , t.'text', t.replyto FROM tweets t WHERE t.writer = ? ORDER BY t.tdate DESC  LIMIT 3", follower)
    recent_tweets = cursor.fetchall()

    connection.commit()


    # Display
    print('-'*20)
    print("Here are the statstics:")
    print("User ID:", str(fid))
    print("Total Post: " + str(num_tweet[0] + num_retweet[0]) + " (" + str(num_retweet[0]) + " for retweet(s))")
    print("Following:", str(following[0]))
    print("Followers:", str(followers_of_follower[0]))
    print("3 Recent Post:")

    for tweet in recent_tweets:
        if tweet[3] == None:
            print("(tid " + str(tweet[0]) + ')' + tweet[1] + ': ' + tweet[2])
        else:
            print("(tid " + str(tweet[0]) + ')' + tweet[1] + ': ' + tweet[2] + "    (reply to user id " + str(tweet[3]) + "'s tweet)")
    
    print('-'*20)
    
    return


def show_followers():
    '''
    Display a list with all followers the user has

    Return:
        id_set (list): the id (str) of all followers 
    '''
    global connection, cursor, logged_in_id

    # Find all the followers and their names
    followee = (logged_in_id,)
    cursor.execute("SELECT f.flwer, u.name FROM follows f, users u WHERE f.flwee = ? AND f.flwer = u.usr;", followee)
    followers = cursor.fetchall()

    connection.commit()

    # Display

    if len(followers) == 0:
        print('-'*20)
        print("You currently have no followers. Sent you to the main menu...")
        time.sleep(2)
        print('-'*20)
        return
    
    idx = 1
    id_set = list()
    print('-'*20)
    print("Here are your followers:")
    print("     id      user name")
    for follower in followers:
        id_set.append(str(follower[0]))
        print(str(idx) + '.   ' + str(follower[0]) + '      ' + follower[1])
        idx+=1
    
    return id_set


def list_followers():
    '''
    Workflow
    '''

    # 1. show followers
    fid_set = show_followers()
    if fid_set == None:
        main_page()


    # 2. select follower (expect to get a valid input)
    valid = False
    while not valid:
        print('-'*20)
        print("Please select the id of the user you are interested in, or type B back to the main menu:")
        fid = input()

        # If input is B or b, then back to the main menu
        if fid == 'B' or fid == 'b':
            #return
            main_page()
        
        # If the input is valid, display more information about the selected person
        elif fid in fid_set:
            more_information(int(fid))
            valid = True

        # The input is not valid
        else:
            print(fid, "is not a valid option. Please try again.")

    # 3. next action (expect to get a valid input, same as above)
    valid = False
    while not valid:
        print("Select the next action:\na. follow this user\nb. see more tweets\nc. back to the main menu\nPlease enter the letter.") #不支持换一个用户
        selection = input()

        # action: follow
        if selection.lower() == 'a':
            error = follow(fid)
            if error == -1:
                list_followers()
            valid = True

        # action: see more information
        elif selection.lower() == 'b':
            more_tweet(fid)
            valid = True

        # action：back
        elif selection.lower() == 'c':
            valid = True

        # not valid
        else:
            print(selection, "is not an valid option. Please try again.")
    main_page()


def main():
    path = input("Enter the name of the database you'd like to use: ")
    try:
        connect(path)
        print("Successfully connected to database!\nContinuing to twitter...")
        time.sleep(2)
    except:
        print("Unable to connect to database.\nExiting program...")
        time.sleep(2)
        exit()        
    create_tables()
    welcome_screen()

    return


if __name__ == "__main__":
    main()
