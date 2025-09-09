import streamlit as st
import pandas as pd
import pandas as pd
import re
from collections import Counter

hyperlinkString = "https://store.steampowered.com/app/"

css = """
.st-key-my_custom_container {
    background-color: #008871ff; /* Light blue */
    padding: 20px;
    border-radius: 10px;
}
.st-key-my_custom_container2 {
    background-color: #008871ff; /* Light blue */
    padding: 20px;
    border-radius: 10px;
}
"""

# Inject the CSS into the Streamlit app
st.html(f"<style>{css}</style>")

st.set_page_config(layout="wide")
st.write ("# 🦥 SlothHat's Indie Game Toolbox")

with st.container(width=1200, height="content",key="my_custom_container"): # Fixed width, height based on content
    
    st.write("&nbsp;&nbsp;&nbsp;&nbsp; Indie games are a unique and vibrant part of the gaming ecosystem, often developed by small teams or individual creators." \
" These games can bring fresh ideas, innovative gameplay mechanics, and unique artistic styles that may not be found in mainstream titles." \
    " However, many indie games struggle to gain visibility and reach their target audience due to limited marketing resources and lack of publisher support. " \
        "This toolbox aims to bridge that gap by providing a platform for publishers to discover indie games that have potential but may not yet have the necessary backing to succeed in the market.")

st.write("---")

with st.container(width=1000   , height="content"): # Fixed width, height based on content
    st.write ("##  🔍 Explore Indie Games with ease!")
    with st.expander("See How To & Tips"):
        st.write(" &nbsp;&nbsp;&nbsp;&nbsp; To use the tool, simply apply the filters on the left-hand side to narrow down the list of indie games based on your specific criteria. ")
        st.write(" &nbsp;&nbsp;&nbsp;&nbsp; Pro Tip: Use Publisher Tags 'Unlikely', or 'Uncertain' combined with >= 100 reviews and <1000 reviews to find games that may be overlooked by other publishers but have 🗲 'Spark'.")
    with st.expander("Caveats & Limitations"):
        st.write(" &nbsp;&nbsp;&nbsp;&nbsp; The data used in this tool is sourced from various platforms and may not be comprehensive or up-to-date. Last update May 2025.")

st.write("")
col1, col2, col3 = st.columns([2, 3, 1], gap="large")

@st.cache_data
def clean_publishers(publisher_str):
    if pd.isna(publisher_str) or publisher_str.strip() == "":
        return [""]
    
    # Split on common delimiters
    raw_parts = re.split(r'[;,/&|]', publisher_str)
    
    cleaned_parts = []
    for part in raw_parts:
        part = part.strip().lower()
        # Remove corporate suffixes
        part = re.sub(r'\b(inc|llc|ltd|co|corp|corporation|gmbh)\b\.?', '', part)
        # Keep alphanumeric + spaces only
        part = re.sub(r'[^a-z0-9\s]', '', part)
        part = re.sub(r'\s+', ' ', part).strip()
        if part:
            cleaned_parts.append(part)
        else:
            cleaned_parts.append("")
    
    return list(set(cleaned_parts))

@st.cache_data
def load_data():
    df = pd.read_csv(
        "games.csv",
        index_col=False)
    #Chunk of code for cleaning the messy data set 

    truColNames = df.columns.tolist()

    truColNames = list(filter(lambda item: item != 'DiscountDLC count', truColNames))
    truColNames = list(filter(lambda item: item != 'Movies', truColNames))
    ### Drop 'DiscountDLC count' and reoranize headers
    df= df.drop(['DiscountDLC count', 'About the game'],axis=1)
    df.columns = truColNames

    ### Drop all Genre-less Games
    df = df.dropna(subset=['Genres'])



    ###Date Related Variables
    df['Release date'] = pd.to_datetime(df['Release date'], errors='coerce')
    df['age_days'] = (pd.Timestamp.today() - df['Release date']).dt.days
    df['age_weeks'] = df['age_days'] / 7

    ### Review Related Variables
    df['total_reviews'] = df['Positive'] + df['Negative']
    df['review_ratio'] = df['Positive'] / (df['total_reviews'] + 1e-6)
    df['reviews_per_day'] = df['total_reviews'] / (df['age_days'] + 1e-6)
    # -------------------------------
    # Step 2: Apply cleaning
    # -------------------------------
    df["publisher_canonical"] = df["Publishers"].apply(clean_publishers)

    # -------------------------------
    # Step 3: Count publishers across dataset
    # -------------------------------
    publisher_counts = Counter([pub for pubs in df["publisher_canonical"] for pub in pubs])

    # -------------------------------
    # Step 4: Define whitelist
    # -------------------------------
    whitelist = {"tbd", "none", "self published", "independent", "indie", ""}

    # -------------------------------
    # Step 5: Tagging logic
    # -------------------------------
    X, Y = 3, 7   # thresholds
    def classify_publishers(pubs):
        has_likely = False
        has_uncertain = False
        
        for pub in pubs:
            if pub in whitelist:
                continue
            count = publisher_counts[pub]
            if count > Y:
                has_likely = True
            elif X < count <= Y:
                has_uncertain = True
        
        if has_likely:
            return "likely"
        elif has_uncertain:
            return "uncertain"
        else:
            return "unlikely"   
        


    df["HasPublisher"] = df["publisher_canonical"].apply(classify_publishers)


    return df

### Get all the genres posibilities
df = load_data()
genres_series = df['Genres'].str.split(',').explode()
# 2. Strip any whitespace from the resulting strings
cleaned_genres = genres_series.str.strip()
# 3. Get the unique values
unique_genres = cleaned_genres.unique()

### Get Publihsher Tag Options
publisher_tag_options = df['HasPublisher'].unique()


col1.write("### Filtering Criteria")

selected_publisher_tags = col1.multiselect('Has Publisher Tag:', publisher_tag_options, default=['unlikely'])
pattern2 = '|'.join(selected_publisher_tags)

# Example: Filter by date range using st.date_input
start_date, end_date = col1.date_input('Select Release Date Range:',
    min_value=pd.to_datetime('2000-01-01'),
    max_value=pd.to_datetime('2030-12-31'), 
    value=(pd.to_datetime('2000-01-01'), pd.to_datetime('2030-12-31')))

genre_options= unique_genres
selected_genres = col1.multiselect('Genre:', genre_options)
pattern = '|'.join(selected_genres)


# Example: Filter by a numerical range using st.slider
min_value, max_value = col1.slider('Price Range $USD:', 
    min_value=0.00, 
    max_value=100.00, 
    value=(0.00, 100.00))


# Example: Filter by a numerical range using st.slider
min_valueRevs, max_valueRevs = col1.slider('Number of Reviews:', 
    min_value=10, 
    max_value=10000, 
    value=(10, 10000))




filtered_df = df[(df['Price'] >= min_value) & (df['Price']  <= max_value)]
filtered_df = filtered_df[filtered_df['Genres'].str.contains(pattern, na=False)]
filtered_df = filtered_df[(filtered_df['total_reviews'] >= min_valueRevs) & (filtered_df['total_reviews'] <= max_valueRevs)]
filtered_df = filtered_df[(filtered_df['Release date'].dt.date >= start_date) & (filtered_df['Release date'].dt.date <= end_date)]
filtered_df = filtered_df[filtered_df['HasPublisher'].str.contains(pattern2, na=False)]

col2.write("### Filtered Games Table")
col2.dataframe(filtered_df)
col3.write(f" ### Total games found: {len(filtered_df)}")


st.write("---")

st.write("## Queried Games Insights: Brightest Star & Underdog")


with st.expander("See Methodology & Explanation"):
    st.write(" &nbsp;&nbsp;&nbsp;&nbsp; The 'Brightest Star' is defined as the game with the highest review ratio (positive reviews to total reviews) among those that have a review ratio of at least 0.9. This indicates a strong positive reception from players. ")
    st.write(" &nbsp;&nbsp;&nbsp;&nbsp; The 'Underdog' is defined as the game that has a review ratio of at least 0.8, but has fewer total reviews than the average number of reviews in the filtered dataset, and has a higher reviews per day rate than the average age of games in days. This indicates a game that may be overlooked but is gaining traction quickly.")


game1 = filtered_df[filtered_df['review_ratio'] >= 0.9].sort_values(
    'total_reviews', ascending=False
).head(1)

# Second game: review_ratio >= 0.8, total_reviews < average, highest reviews_per_day, younger than average
avg_reviews = filtered_df['total_reviews'].mean()
avg_days = filtered_df['age_days'].mean()

game2 = filtered_df[
    (filtered_df['review_ratio'] >= 0.8) &
    (filtered_df['total_reviews'] < avg_reviews) &
    (filtered_df['age_days'] < avg_days)
].sort_values('reviews_per_day', ascending=False).head(1)

# Combine the two games into one DataFrame (optional)
selected_games = pd.concat([game1, game2])

# Build hyperlinks
# Assuming Steam URL pattern: https://store.steampowered.com/app/<app_id>
selected_games['link'] = selected_games['AppID'].apply(lambda x: f"https://store.steampowered.com/app/{x}")
selected_games['Insight'] = ['Brightest Star', 'Underdog']


# Display
st.write(selected_games[['Insight', 'Name','review_ratio', 'total_reviews', 'reviews_per_day', 'Release date', 'HasPublisher']])
st.link_button("Go to Brightest Star Game Page", selected_games.iloc[0]['link'])
st.link_button("Go to Underdog Game Page", selected_games.iloc[1]['link'])