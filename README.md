# Youtube_Data_Extraction_app
Youtube Data Harvesting and Warehousing extracts data about channels in youtube, stores data in Mongodb, Mysql.

**Problem Statement:**
`The problem statement is to create a Streamlit application that allows users to access
and analyze data from multiple YouTube channels. The application should have the
following features:
1. Ability to **input a YouTube channel ID** and **retrieve** all the **relevant data**
(Channel name, subscribers, total video count, playlist ID, video ID, likes,
dislikes, comments of each video) using Google API.
2. Option to **store the data in a MongoDB** database as a data lake.
3. Ability to collect data for up to 10 different YouTube channels and store them in
the data lake by clicking a button.
4. Option to select a channel name and** migrate its data** from the data lake **to a**
**SQL database** as tables.
5. Ability to **search and retrieve data from the SQL database** using different
search options, including joining tables to get channel details.

**Languages and Tools Used:** Python,MongodbCompass,Mysql Workbench,Jupyter Notebook,Streamlit Application

**End Product:**
![project screenshot](https://github.com/KiruthikaParanthaman/Youtube_Data_Extraction_app/assets/141828622/e271a975-d217-41fb-ba4f-5d0a11a49f79)

**Take a Tour of options:**

**Home :** Home option gives overview of the features of the youtube Data Extraction application

**Search and store in Mongodb :** Search and store in Mongodb enables user to enter channel_id or choose from the list of sample channel list. When channel is chosen, Store in Mongodb button is enabled
which enables user to store data in Mongodb

**Migrate Data to Sql :** Migrate data to sql option provides list of channel names already stored in Mongodb and user can select channels to migrate to Mysql. Sample preview of datas stored in Mysql
is available through channel,video,playlist and comment radiobutton

**Data Analysis:** Users can find answers to their general queries like which is the most liked video,most commented video,most viewed videos and so on through selecting the appropriate question from the
list of 10 predefined questions
`
**Challenges and Learning:**
1. Challenge: Google API key restricts data retrieval to 10000 requests per day
   Approach : In regards to the constraint, all channels were chosen with maximum of 500 videos so as not to exceed the quota limit for the day
2. Challenge : Data Integrity and Data Duplication to be maintained while storing data in Mongodb and Mysql
   Approach  : St.session state of Mongodb was used to prevent users from storing same channels twice in Mongodb. A pre-check with list of stored channel names was made before storing data in Mysql.
   Users were cautioned and prevented from storing same data twice.Data Integration was enabled by specifying Primary keys in both databases
3. Challenge : 
