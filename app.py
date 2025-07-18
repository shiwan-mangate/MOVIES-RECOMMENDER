import streamlit as st
import pickle
import pandas as pd
import requests
import time
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry

# Configure retry strategy for requests
retry_strategy = Retry(
    total=5,  # Increased retry count
    backoff_factor=2,  # Exponential backoff
    status_forcelist=[429, 500, 502, 503, 504]
)
adapter = HTTPAdapter(max_retries=retry_strategy)
http = requests.Session()
http.mount("https://", adapter)
http.mount("http://", adapter)

# Silently fetch poster with fallback
@st.cache_data(show_spinner=False)
def fetch_poster(movie_id):
    try:
        response = http.get(
            f"https://api.themoviedb.org/3/movie/{movie_id}?api_key=78312778659915a84078ab9741247d5b",
            timeout=10
        )
        response.raise_for_status()
        data = response.json()
        return "https://image.tmdb.org/t/p/w500/" + data['poster_path']
    except Exception as e:
        # Log error to console for debugging (not on the site)
        print(f"[Poster Error] Movie ID {movie_id}: {e}")
        return "https://via.placeholder.com/300x450?text=No+Image"

# Recommend function
def recommend(movie):
    try:
        movie_index = movies[movies['title'] == movie].index[0]
        distance = similarity[movie_index]
        movies_list = sorted(list(enumerate(distance)), reverse=True, key=lambda x: x[1])[1:6]

        recommended_movies = []
        recommended_posters = []

        for i in movies_list:
            movie_id = movies.iloc[i[0]].movie_id
            recommended_movies.append(movies.iloc[i[0]].title)

            poster = fetch_poster(movie_id)
            recommended_posters.append(poster)

            time.sleep(0.25)  # To avoid hitting API rate limits

        return recommended_movies, recommended_posters
    except Exception as e:
        st.warning(f"Error generating recommendations: {str(e)}")
        return [], []

# Load data
movies_dict = pickle.load(open("movie_dict.pkl", 'rb'))
movies = pd.DataFrame(movies_dict)
similarity = pickle.load(open("similarity.pkl", "rb"))

# Streamlit UI
st.title("🎬 Movie Recommender System")

selected_movie_name = st.selectbox(
    "Select a movie to get recommendations:",
    movies['title'].values
)

if st.button("Recommend"):
    with st.spinner('🔍 Finding recommendations...'):
        names, posters = recommend(selected_movie_name)

    if names:
        cols = st.columns(5)
        for i, (col, name, poster) in enumerate(zip(cols, names, posters)):
            with col:
                st.subheader(name)
                st.image(poster, use_container_width=True)
    else:
        st.warning("⚠️ Couldn't fetch recommendations. Please try again.")
