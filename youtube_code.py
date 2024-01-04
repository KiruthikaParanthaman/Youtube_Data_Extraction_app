#import necessary libraries
from logging import PlaceHolder
from googleapiclient.discovery import build
import copy
import isodate
from pprint import pprint
from pymongo import MongoClient
import mysql.connector
import streamlit as st
from streamlit_option_menu import option_menu
import pandas as pd
import numpy as np

#Youtube search and Retrieve data:
#youtube API key,version
api_service_name = "youtube"
api_version = "v3"
api_key = "AIzaSyCIw6hk163RqqMD8IY8ceRHA8OnlSDGUD4"

#list of channel names stored in mongodb channel
mongodb_appended_channel_id = []
mongodb_appended_channels_name = []


#youtube channel details
def channel_table(channel_id):
    youtube = build(api_service_name, api_version, developerKey=api_key)
    request = youtube.channels().list(part="snippet,contentDetails,statistics",id = channel_id)
    response = request.execute()
    channel_data = dict(channel_name = response['items'][0]['snippet'].get('title'),
                        channel_id = channel_id,
                        channel_views = response['items'][0]['statistics'].get('viewCount'),
                        channel_description = response['items'][0]['snippet'].get('description'),
                        subscription_count = response['items'][0]['statistics'].get('subscriberCount'),
                        video_count = response['items'][0]['statistics'].get('videoCount'),
                        master_videos_id = response['items'][0]['contentDetails']['relatedPlaylists'].get('uploads'))
    return channel_data

#playlist table details
def playlist_table(channel_id):     
    nextPageToken = None
    while True:
        youtube = build(api_service_name, api_version, developerKey=api_key)
        request = youtube.playlists().list(part="id,snippet",channelId = channel_id,pageToken = nextPageToken,maxResults = 50)
        response = request.execute()
        playlist_id_list = []
        playlist_name_list = []
        for i in range(len(response['items'])):
            playlist_id = response['items'][i]['id']
            playlist_id_list.append(playlist_id)
            playlist_name = response['items'][i]['snippet']['title']
            playlist_name_list.append(playlist_name)
        nextPageToken = response.get('nextPageToken')         
        if nextPageToken is None:
            break
    playlist_data = dict(playlist_id_list = playlist_id_list,playlist_name_list = playlist_name_list)
    return(playlist_data)

#video_id table details:
def video_ids_table(master_videos_id):
    video_id_list = []
    nextPageToken = None
    while True:
        youtube = build(api_service_name, api_version,developerKey=api_key)
        request = youtube.playlistItems().list(part ='id,snippet,contentDetails',playlistId = master_videos_id,pageToken = nextPageToken,maxResults = 50)     
        response = request.execute()
        for i in range(len(response['items'])):
            video_id = response['items'][i]['contentDetails'].get('videoId')
            video_id_list.append(video_id)
        nextPageToken = response.get('nextPageToken')
        if nextPageToken is None:
            break
    return video_id_list

#video table details:
def video_table(video_id):
    youtube = build(api_service_name, api_version, developerKey=api_key)
    request = youtube.videos().list(part="id,snippet,statistics,contentDetails",id = video_id)
    response = request.execute()
    video_data = dict(video_id = response['items'][0].get('id'),
    video_name = response['items'][0]['snippet'].get('title'),
    video_description = response['items'][0]['snippet'].get('description'),
    video_tags = response['items'][0]['snippet'].get('tags'),
    video_published_date = isodate.parse_datetime(response['items'][0]['snippet'].get('publishedAt')).date().isoformat(),
    video_view_count = response['items'][0]['statistics'].get('viewCount'),
    video_like_count = response['items'][0]['statistics'].get('likeCount'),
    video_dislike_count = response['items'][0]['statistics'].get('dislikeCount'),
    video_favourite_count = response['items'][0]['statistics'].get('favoriteCount'),             
    video_comment_count = response['items'][0]['statistics'].get('commentCount'),
    video_duration = int(isodate.parse_duration(response['items'][0]['contentDetails'].get('duration')).total_seconds()),
    video_thumbnail = response['items'][0]['snippet']['thumbnails']['default'].get('url'),
    video_caption_status = response['items'][0]['contentDetails'].get('caption'))
    return video_data

#comments table details:
def comment_thread_table(video_id):
    comments_data = []
    youtube = build(api_service_name, api_version, developerKey=api_key)
    request = youtube.commentThreads().list(part="id,snippet",videoId = video_id)
    try:
        response = request.execute()
        for item in response['items']:
            #fetching data from commentthreads->items->snippet->toplevelcomment. Here toplevel comment is again comment resource(comments.list)     
            comments_details = dict(comment_id = item['snippet']['topLevelComment'].get('id'),
            video_id = video_id,
            comment_text = item['snippet']['topLevelComment']['snippet'].get('textDisplay'),                                
            comment_author = item['snippet']['topLevelComment']['snippet'].get('authorDisplayName'),
            comment_published_date = isodate.parse_datetime(item['snippet']['topLevelComment']['snippet'].get('publishedAt')).date().isoformat())
            comments_data.append(comments_details)  
    except:
         pass                                   
    return comments_data

#Comments channel details:
def complete_channel_data(channel_id):
    c = channel_table(channel_id)
    p = playlist_table(channel_id)
    video_id_list1 = video_ids_table(c['master_videos_id'])
    video_list = []
    comments_list = []
    for i in range(len(video_id_list1)):
        single_video_data = video_table(str(video_id_list1[i]))
        comments = comment_thread_table(str(video_id_list1[i]))
        video_list.append(single_video_data)
        comments_list.append(comments)
    cm_filter = list(filter(None, comments_list))
    cm = [x for item in cm_filter for x in item]
    result = dict(channel_details = c,playlist_details = p,video_details = video_list,comments = cm)
    return result

#Establishes Mongodb connection with youtube_project database:
def mongodb_connection():
    client=MongoClient("mongodb://localhost:27017")
    mydb = client["youtube_project"]
    mycollection = mydb["youtube_data"]
    return mycollection



#function for calling youtube details and storing in mongodb:
def to_mongodb(channel_id):
    c = channel_table(channel_id)    
    channel_name = c['channel_name']
    if channel_id not in st.session_state:
        st.session_state[channel_id] = "channel_name"
        result = complete_channel_data(channel_id)
        client=MongoClient("mongodb://localhost:27017")
        mydb = client["youtube_project"]
        mycollection = mydb["youtube_data"]
        mycollection.insert_one(result)
        flag = 1 #successfully inserted
    else:
        flag = 2 #channel already exists
    return flag

#function to check existence of database in mysql database
def sql_db_check():
    mydb = mysql.connector.connect(host="localhost",user="root",password="*******")
    mycursor = mydb.cursor()
    try:
        mycursor.execute("USE youtube_project")
        flag = 1
    except:
        flag = 0
    return flag

#create youtube_project database and create tables channel,playlist,videos and comments:
def mysql_table_creation():
    mydb = mysql.connector.connect(host="localhost",user="root",password="*******")
    mycursor = mydb.cursor()
    mycursor.execute("CREATE DATABASE youtube_project")
    mydb = mysql_connection()
    mycursor = mydb.cursor()
    mycursor.execute('''CREATE TABLE channel (channel_id VARCHAR(255) PRIMARY KEY NOT NULL, channel_name VARCHAR(255), 
                        channel_views INT DEFAULT 0 ,channel_description TEXT ,video_count INT,
                        subscription_count INT NOT NULL DEFAULT 0,master_videos_id VARCHAR(255))''') 
    mycursor.execute("CREATE TABLE playlist (playlist_id VARCHAR(255) PRIMARY KEY, channel_id VARCHAR(255), playlist_name VARCHAR(255))") 
    mycursor.execute("CREATE TABLE comments (comment_id VARCHAR(255) PRIMARY KEY, video_id VARCHAR(255),comment_text TEXT,\
                     comment_author VARCHAR(255),comment_published_date DATE)")
    mycursor.execute('''CREATE TABLE video (video_id VARCHAR(255) PRIMARY KEY NOT NULL,channel_id VARCHAR(255),
                     video_name VARCHAR(255)  DEFAULT '' ,video_description TEXT,tags TEXT ,
                     published_date DATE,view_count INT DEFAULT 0,like_count INT  DEFAULT 0,
                     dislike_count INT DEFAULT 0,favorite_count INT DEFAULT 0,comment_count INT DEFAULT 0,
                     duration_in_sec INT,thumbnail VARCHAR(255) ,caption_status VARCHAR(255)) ''') 
    return True

#function for establishing connection sql database youtube_project
def mysql_connection():
    mydb = mysql.connector.connect(host="localhost",user="root",password="******",database = "youtube_project")
    return mydb

#function to store channel details to mysql databse
def channel_data_to_sql(channel_details):
    df = pd.DataFrame.from_dict([channel_details])
    df1 = df[['channel_id','channel_name','channel_description','channel_views','video_count','subscription_count','master_videos_id']]
    sql = "INSERT INTO channel(channel_id,channel_name,channel_description,channel_views,video_count,subscription_count,master_videos_id) VALUES (%s, %s ,%s ,%s, %s, %s, %s)"
    values = df1.to_numpy().tolist()
    mydb = mysql_connection()
    mycursor = mydb.cursor()
    mycursor.executemany(sql,values)
    mydb.commit()
    return True

#function to store playslist details to mysql databse
def playlist_data_to_sql(playlist_details,channel_id):
    df = pd.DataFrame.from_dict(playlist_details)
    length = df.shape[0]
    channel_id = [channel_id for i in range(length)]
    df['channel_id']= channel_id
    df1 = df[['playlist_id_list','channel_id','playlist_name_list']]
    df2 = df1.fillna("")
    sql = "INSERT INTO playlist(playlist_id,channel_id,playlist_name) VALUES (%s, %s ,%s)"
    values = df2.to_numpy().tolist()
    mydb = mysql_connection()
    mycursor = mydb.cursor()
    mycursor.executemany(sql,values)
    mydb.commit()    
    return values

#function to store video details to mysql database

def video_sql_table(video_details,channel_id):
    for item in video_details:
        video_id = item.get('video_id')        
        channel_id = channel_id
        video_name = item.get('video_name')
        video_description= item.get('video_description')
        published_date= item.get('video_published_date')
        view_count= item.get('video_view_count')
        like_count= item.get('video_like_count')
        dislike_count= item.get('video_dislike_count')
        favorite_count= item.get('video_favourite_count')
        comment_count= item.get('video_comment_count')
        duration_in_sec= item.get('video_duration')
        thumbnail   = item.get('video_thumbnail')
        caption_status = item.get('video_caption_status').replace('false','0').replace('true','1')
        tag = item.get('video_tags')
        if tag is not None:
            tags = ' '.join(map(str, tag))
        else:
            tags = ""
        sql = '''INSERT INTO video(video_id,channel_id,video_name,video_description,published_date,
        view_count,like_count,dislike_count,favorite_count,comment_count,duration_in_sec,
        thumbnail,caption_status,tags) VALUES (%s, %s ,%s, %s, %s ,%s, %s, %s ,%s, %s, %s ,%s ,%s ,%s)'''
        values = video_id,channel_id,video_name,video_description,published_date,\
        view_count,like_count,dislike_count,favorite_count,comment_count,duration_in_sec,\
        thumbnail,caption_status,tags   
        mydb = mysql_connection()
        mycursor = mydb.cursor()
        mycursor.execute(sql,values)
        try:
            mydb.commit()
        except:
            mydb.rollback()
    return True

#function to store comments details to mysql table
def comments_sql_table(comments_details):
    df = pd.DataFrame.from_dict (comments_details) [list (comments_details[0].keys())]
    df1 = df[['comment_id','video_id','comment_text','comment_author','comment_published_date']]
    sql = "INSERT INTO comments(comment_id,video_id,comment_text,comment_author,comment_published_date) VALUES (%s, %s ,%s ,%s, %s)"
    values = df1.to_numpy().tolist()
    mydb = mysql_connection()
    mycursor = mydb.cursor()
    mycursor.executemany(sql,values)
    mydb.commit()
    return True

#get channel_names of inserted channels in mongodb
def channels_from_mongodb():
    client=MongoClient("mongodb://localhost:27017")
    mydb = client["youtube_project"]
    mycollection = mydb["youtube_data"]
    mongo_records = list(mycollection.find({},{'channel_details.channel_name':1,'_id':0}))
    channel_name_list = []
    for i in range(len(mongo_records)):
        channel_name = mongo_records[i]['channel_details']['channel_name']
        channel_name_list.append(channel_name)
    return channel_name_list

#main function call to store all datas in Mysql
#receives user input and uses channel primary parameter error to check whether channel has already been stored in mongodb database
def to_sql(user_inputs):
    check = sql_db_check()
    if check == 1:
        mydb = mysql_connection()
    else:
        mydb = mysql_table_creation()
        if mydb == True:
            print("Mysql database and tables successfully created")
        else:
            print("Error creating database")
    for i in range(len(user_inputs)):
        try:            
            mycollection = mongodb_connection()
            data_from_mongodb = list(mycollection.find({'channel_details.channel_name':user_inputs[i]},{'_id':0}))
            channel_details = data_from_mongodb[0]['channel_details']
            channel_table = channel_data_to_sql(channel_details)
            channel_id = channel_details.get('channel_id')
            playlist_details = data_from_mongodb[0]['playlist_details']
            playlist_table = playlist_data_to_sql(playlist_details,channel_id)
            video_details = data_from_mongodb[0]['video_details']
            video_table = video_sql_table(video_details,channel_id)
            comments_details = data_from_mongodb[0]['comments']
            comments_table = comments_sql_table(comments_details)
            st.session_state[user_inputs[i]]=i
            flag = 1 #successfully stored
        except:
            flag = 0
    return flag

# Displays sample inserted channel tables in sql database 
def show_channel_tables():
    mydb = mysql_connection()
    mycursor = mydb.cursor()
    query = '''SELECT channel_id,channel_name,channel_description,channel_views,video_count,
                subscription_count,master_videos_id FROM youtube_project.channel LIMIT 5'''
    mycursor.execute(query)
    result = mycursor.fetchall()
    df = pd.DataFrame(result, columns = ['channel_id','channel_name','channel_description','channel_views','video_count','subscription_count','master_videos_id']) 
    st.dataframe(df)

# Displays sample inserted playlist tables in sql database 
def show_playlist_tables():
    mydb = mysql_connection()
    mycursor = mydb.cursor()
    query = "SELECT playlist_id,channel_id,playlist_name FROM youtube_project.playlist LIMIT 5"
    mycursor.execute(query)
    result = mycursor.fetchall()
    df = pd.DataFrame(result, columns = ['playlist_id','channel_id','playlist_name']) 
    st.dataframe(df)

# Displays sample inserted video tables in sql database 
def show_video_tables():
    mydb = mysql_connection()
    mycursor = mydb.cursor()
    query = '''SELECT * FROM youtube_project.video LIMIT 5'''
    mycursor.execute(query)
    result = mycursor.fetchall()
    df = pd.DataFrame(result, columns = ['video_id','channel_id','video_name','video_description','tags','published_date',
        'view_count','like_count','dislike_count','favorite_count','comment_count','duration_in_sec',
        'thumbnail','caption_status']) 
    st.dataframe(df)

# Displays sample inserted comment tables in sql database    
def show_comments_tables():
    mydb = mysql_connection()
    mycursor = mydb.cursor()
    query = "SELECT comment_id,video_id,comment_text,comment_author,comment_published_date FROM youtube_project.comments LIMIT 5"
    mycursor.execute(query)
    result = mycursor.fetchall()
    df = pd.DataFrame(result, columns = ['comment_id','video_id','comment_text','comment_author','comment_published_date']) 
    st.dataframe(df)

#function to return required dataframe for the question selected from the list of 10 question for data analysis
def ques_answer(data_questions):
    mydb = mysql_connection()
    mycursor = mydb.cursor()
    if data_questions == ques1:
        query = '''SELECT video.channel_id,channel.channel_name,video.video_name FROM youtube_project.video as video
                INNER JOIN youtube_project.channel as channel ON channel.channel_id = video.channel_id ORDER BY channel_name'''
        column = ['channel_id','channel_name','video_name']
    elif data_questions == ques2:
        query = '''SELECT channel_id,channel_name,video_count  FROM youtube_project.channel  ORDER BY video_count DESC;
                    mycursor.execute(query) result = mycursor.fetchall()'''
        column = ['channel_id','channel_name','video_count']
    elif data_questions == ques3:
        query = '''SELECT video.channel_id, channel.channel_name,video.video_name, video.view_count FROM youtube_project.video AS video
                   INNER JOIN youtube_project.channel AS channel ON video.channel_id = channel.channel_id ORDER BY video.view_count DESC LIMIT 10;'''
        column = ['channel_id','channel_name','video_name','view_count']
    elif data_questions == ques4:
        query = '''SELECT video_name,comment_count FROM youtube_project.video ORDER BY comment_count DESC;'''
        column = ['video_name','comment_count']
    elif data_questions == ques5:
        query = '''SELECT channel.channel_name, video.video_name,video.like_count FROM youtube_project.video AS video INNER JOIN youtube_project.channel as channel
                   ON  channel.channel_id = video.channel_id ORDER BY like_count DESC;'''
        column = ['channel_name','video_name','like_count']
    elif data_questions == ques6:
        query = '''SELECT video_name,like_count,dislike_count FROM youtube_project.video ORDER BY like_count DESC'''
        column = ['video_name','like_count','dislike_count']
    elif data_questions == ques7:
        query = '''SELECT channel_name,channel_views  FROM youtube_project.channel  ORDER BY channel_views DESC;'''
        column = ['channel_name','channel_views']
    elif data_questions == ques8:
        query = '''SELECT channel.channel_name,COUNT(video.video_id) AS No_of_videos_in_2022  FROM youtube_project.video AS video  INNER JOIN youtube_project.channel AS channel ON channel.channel_id = video.channel_id
                    WHERE YEAR(video.published_date) IN (2022)  GROUP BY channel.channel_name  ORDER BY No_of_videos_in_2022 DESC;'''
        column = ['channel_name', 'No_of_videos_in_2022']
    elif data_questions == ques9:
        query = '''SELECT channel.channel_name AS channel_name, substring(sec_to_time(AVG(duration_in_sec)),1,8) AS Average_duration_hms
                    FROM youtube_project.video as video INNER JOIN youtube_project.channel as channel ON channel.channel_id = video.channel_id
                    GROUP BY channel.channel_name ORDER BY Average_duration_hms DESC;'''
        column = ['channel_name','Average_duration_hms']
    else:
        query = '''SELECT channel.channel_name,video.video_name,video.comment_count FROM youtube_project.video as video INNER JOIN youtube_project.channel as channel
                ON channel.channel_id = video.channel_id ORDER BY comment_count DESC;'''
        column = ['channel_name','video_name','comment_count'] 
    mycursor.execute(query)
    result = mycursor.fetchall()
    df = pd.DataFrame(result, columns = column) 
    return df
  
#Streamlit codes
#page configuration
st.set_page_config(page_title="Youtube Data Harvesting and Warehousing",page_icon="▶️",layout="wide",initial_sidebar_state="expanded")
st.title("▶️ :red[Youtube] Data Harvesting and Warehousing")

#Sidebar configuration with seelctbox to let user copy channel_id and channel_name from sample list
with st.sidebar:
    option = st.selectbox ('May I help you?',
    ("MATH THE IMMORTAL - என்றும் அழியா கணிதம் : UCl5LlCSvu5896s7n1tUYarA",
    "Deep Breath - Relaxing Music : UCCaLwBoi-veAmQQFDuYhs4A",
    "Stock Data Analysis : UCzp6RKEj8OzB8er0_o1weoQ","Cut N Color : UCsmiF9Q74t5OPxezlh0-X2A" ,
    "Physics Gene : UCiITynNRu0md5KiV1diaVjg" ,"Direct English : UClLLonVHsdlz-VRAedNJVKA",
    "My visa and travel Vlogs : UC34p2yLG8TkQd5wrBA-ulWw",
    "meditation music : UCPolpRGk23Ls9AkpL5HvTTA","English Motivational Videos : UCRkiQ__KZModKaMFUJ5nXAg",
    "Analytics Training Hub : UCT0uGNH5koT5UpjZAgsjouA"),
    help="sample channel_names and channel_ids",
    placeholder="sample channel_names with channel_ids with ease",)
    st.write("You Selected :" ,option)

#Main Layout with horizontal option bar with 4 options
menu_bar = option_menu(None, ["Home","Search and Store in Mongodb", "Migrate data to SQL", ' Data Analysis'], 
    icons=['house','box', "cloud", 'play'], 
    menu_icon="cast", default_index=0, orientation="horizontal")   

#Home bar with brief explanation about the project
if menu_bar == "Home":
    st.markdown("**About us** :" )
    st.markdown(                     ''' "Youtube Data Harvesting and Warehousing" application enables users to search any youtube channel data through channel id.The data retrieved
                from youtube API will be stored in Mongodb and further can be migrated to Mysql database.Users can also analyse data by selecting a option 
                from pre-defined set of 10 common queries for the youtube channel_datas stored in Mysql database.Happy analysing:chart_with_upwards_trend:!!!''')

#Search and Store Menubar option with option to enter channel_id(col1) or select from list of channels(col2)   
elif menu_bar == "Search and Store in Mongodb":
    st.markdown("<h4 style='text-align: center; color: grey;'>Enter channel_id or Select from list of channels</h4>", unsafe_allow_html=True)
    col1, col2 = st.columns(2)
    with col1:
        search_bar = st.text_input('Enter youtube channel id',placeholder="Enter channel id and click Enter",label_visibility="hidden")
        chan_id = ','.join(search_bar.split())
        if search_bar:
            st.write("you selected :",chan_id)
            store_search = st.button("Store in mongodb",help="Retrieves youtube data and stores in Mongodb",type="primary",key='1')
            if store_search:
                channel_data = to_mongodb(chan_id)
                if channel_data == 1:
                    st.write("Successfully inserted",chan_id)
                else:
                    st.write(chan_id,"Channel already exists") 
             

    with col2:
        user_input = st.selectbox("Select channel_id from the list",['UCl5LlCSvu5896s7n1tUYarA','UCCaLwBoi-veAmQQFDuYhs4A',
        'UCzp6RKEj8OzB8er0_o1weoQ','UCsmiF9Q74t5OPxezlh0-X2A','UCiITynNRu0md5KiV1diaVjg','UClLLonVHsdlz-VRAedNJVKA',
        'UC34p2yLG8TkQd5wrBA-ulWw','UCPolpRGk23Ls9AkpL5HvTTA','UCRkiQ__KZModKaMFUJ5nXAg','UCT0uGNH5koT5UpjZAgsjouA'],index=None,placeholder="Select channel_id to store in Mongodb",label_visibility="hidden")
        if user_input:
            st.write("you selected :",user_input)
            retrieve_list = st.button("Store in mongodb",help="Retrieves youtube data and stores in Mongodb",type="primary",key='2')
            if retrieve_list:
                channel_data = to_mongodb(user_input)
                if channel_data == 1:
                    st.write("Successfully inserted",user_input)
                else:
                    st.write(user_input,"Channel already exists")  

#Migrate data to SQL option with option to select multiple channles.List of channels stored in Mongodb stored here
#Integrity check to prevent data duplication and migration of data to mysql done through to_sql function   
#displays 4 radio buttons to let user select channel,playlist,video or comments to display sample datas inserted in mysql                 
elif menu_bar == "Migrate data to SQL":
    channel_names = channels_from_mongodb()
    channel_dropdown = st.multiselect("select channel name to store in Mysql",channel_names)
    if channel_dropdown:
        st.write("you selected  :", *tuple(channel_dropdown))
        store_sql = st.button("store in sql",help = "Fetches data from mongodb and stores in Mysql",type="primary" )
        if store_sql:
            channel_datas = to_sql(channel_dropdown)
            if channel_datas == 1:
                st.write("Selected channels",tuple(channel_dropdown), "succcessfully stored in Mysql databse")
            else:
                st.write("Channel Already exists in Mysql database")
        if channel_dropdown and (sql_db_check() == 1):
            sample_data = st.radio("Select an option to view sample of inserted channel data",["channel","Playlist","Video","Comments"])
            if sample_data == 'channel':
                show_channel_tables()
            if sample_data == 'Playlist':
                show_playlist_tables()
            if sample_data == 'Video':
                show_video_tables()
            if sample_data == "Comments":
                show_comments_tables()

#Data Analysis option to let user choose a question.Answers will be in the form of dataframe
else :
    ques1 = "1.What are the names of all the videos and their corresponding channels?"
    ques2 = "2.Which channels have the most number of videos, and how many videos do they have?"
    ques3 = "3.What are the top 10 most viewed videos and their respective channels?"
    ques4 = "4.How many comments were made on each video, and what are their corresponding video names?"
    ques5 = "5.Which videos have the highest number of likes, and what are their corresponding channel names?"
    ques6 = "6.What is the total number of likes and dislikes for each video, and what are their corresponding video names?"
    ques7 = "7.What is the total number of views for each channel, and what are their corresponding channel names?"
    ques8 = "8.What are the names of all the channels that have published videos in the year 2022?"
    ques9 = "9.What is the average duration of all videos in each channel, and what are their corresponding channel names?"
    ques10 = "10.Which videos have the highest number of comments, and what are their corresponding channel names?"
    data_questions = st.selectbox("select a question to view the data analysis",[ques1,ques2,ques3,ques4,ques5,ques6,ques7,ques8,ques9,ques10],index=None,
                                               placeholder   = "Selecct an option to analyse data")
    if data_questions:
        df = ques_answer(data_questions)
        st.dataframe(df)
    

    
    





        






            






    

