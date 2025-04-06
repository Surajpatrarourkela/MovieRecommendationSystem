import streamlit as st
import mysql.connector
import pickle
import pandas as pd
import requests
import hashlib
from streamlit_lottie import st_lottie


# --------------------- #
#     CSS Styling       #
# --------------------- #
def local_css():
    st.markdown(
        """
        <style>
        body {
            font-family: Arial, sans-serif;
            background-color: #f4f4f9;
            padding: 20px;
        }
        h1, h2, h3 {
            color: #333;
        }
        .stButton>button {
            background-color: #4CAF50;
            color: white;
            border: none;
            padding: 10px 24px;
            text-align: center;
            text-decoration: none;
            display: inline-block;
            font-size: 16px;
            margin: 4px 2px;
            cursor: pointer;
            border-radius: 12px;
        }
        .stSelectbox>div>div>div>select {
            padding: 10px;
            border-radius: 12px;
        }
        </style>
        """,
        unsafe_allow_html=True
    )


# Apply the local CSS
local_css()


# --------------------- #
#    Lottie Animation   #
# --------------------- #
def load_lottieurl(url: str):
    try:
        r = requests.get(url)
        if r.status_code != 200:
            return None
        return r.json()
    except:
        return None


# Lottie URLs
lottie_error_url = "https://assets10.lottiefiles.com/packages/lf20_j1adxtyb.json"
lottie_success_url = "https://assets10.lottiefiles.com/packages/lf20_tulwxazd.json"

# Load Lottie animations
lottie_error = load_lottieurl(lottie_error_url)
lottie_success = load_lottieurl(lottie_success_url)

# --------------------- #
#    Database Setup     #
# --------------------- #
DB_HOST = "localhost"
DB_USER = "root"
DB_PASSWORD = "442005"
DB_NAME = "movie_recommender"

# OMDb API Key for fetching movie posters
OMDB_API_KEY = "187596f"  # Replace with your OMDb API key


# Database connection
def create_connection():
    try:
        conn = mysql.connector.connect(
            host=DB_HOST,
            user=DB_USER,
            password=DB_PASSWORD,
            database=DB_NAME
        )
        return conn
    except mysql.connector.Error as err:
        st.error(f"Error connecting to the database: {err}")
        if lottie_error:
            st_lottie(lottie_error, height=200)
        return None


def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()


# --------------------- #
#        Login          #
# --------------------- #
def login_user(email, password):
    conn = create_connection()
    if conn is None:
        return None
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("SELECT * FROM users WHERE email = %s AND password = %s", (email, hash_password(password)))
        user = cursor.fetchone()
    except Exception as e:
        st.error("An error occurred during login.")
        if lottie_error:
            st_lottie(lottie_error, height=200)
        user = None
    conn.close()
    return user


# --------------------- #
#        Signup         #
# --------------------- #
def signup_user(username, email, password):
    conn = create_connection()
    if conn is None:
        return False
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO users (username, email, password) VALUES (%s, %s, %s)",
                       (username, email, hash_password(password)))
        conn.commit()
        success = True
    except mysql.connector.IntegrityError:
        st.error("User already exists.")
        if lottie_error:
            st_lottie(lottie_error, height=200)
        success = False
    except Exception as e:
        st.error("An error occurred during signup.")
        if lottie_error:
            st_lottie(lottie_error, height=200)
        success = False
    conn.close()
    return success


# --------------------- #
#   Logout Function     #
# --------------------- #
def logout():
    st.session_state['logged_in'] = False
    st.session_state['user'] = None


# --------------------- #
#    Fetch Poster from OMDb API  #
# --------------------- #
def get_movie_poster(movie_name):
    try:
        url = f"http://www.omdbapi.com/?t={movie_name}&apikey={OMDB_API_KEY}"
        response = requests.get(url, timeout=10)
        data = response.json()
        if data['Response'] == 'True':
            return data['Poster']
        else:
            return None
    except requests.exceptions.RequestException as e:
        st.error(f"Network error occurred while fetching the poster: {e}")
        return None
    except Exception as e:
        st.error(f"An error occurred: {e}")
        return None


# --------------------- #
#    Recommendation     #
# --------------------- #
def recommend(movie):
    try:
        movie_index = movies[movies['title'] == movie].index[0]
        distances = similarity[movie_index]
        movie_list = sorted(list(enumerate(distances)), reverse=True, key=lambda x: x[1])[1:6]
        recommended_movies = []
        recommended_movie_posters = []
        recommended_movie_ratings = []
        for i in movie_list:
            movie_name = movies.iloc[i[0]].title
            poster = get_movie_poster(movie_name)
            recommended_movies.append(movie_name)
            recommended_movie_posters.append(poster)
            recommended_movie_ratings.append("N/A")  # Placeholder for rating
        return recommended_movies, recommended_movie_posters, recommended_movie_ratings
    except Exception as e:
        st.error(f"An error occurred during recommendation: {e}")
        return [], [], []


# --------------------- #
#   Streamlit App Logic #
# --------------------- #

# Check if user is logged in
if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False
    st.session_state['user'] = None

if st.session_state['logged_in']:
    st.title("Movie Recommender System")

    if st.button("Logout"):
        logout()
        st.success("Successfully logged out.")

    # Load movie data
    @st.cache_data
    def load_movie_data():
        try:
            with st.spinner('Loading movie data...'):
                movies_dict = pickle.load(open('movie_dict.pkl', 'rb'))
                movies_df = pd.DataFrame(movies_dict)
                similarity_matrix = pickle.load(open('similarity.pkl', 'rb'))
                return movies_df, similarity_matrix
        except Exception as e:
            st.error("Failed to load movie data.")
            st.stop()

    movies, similarity = load_movie_data()

    movie_list = movies['title'].values
    selected_movie = st.selectbox("Select a movie you like", movie_list)

    if st.button("Recommend"):
        names, posters, ratings = recommend(selected_movie)

        for i in range(len(names)):
            st.subheader(names[i])  # Movie Name is displayed regardless of errors
            if posters[i]:
                st.image(posters[i])
            st.text(f"Rating: {ratings[i]}")

else:
    st.title("Login / Signup")

    option = st.selectbox("Choose an option", ["Login", "Signup"])

    if option == "Login":
        email = st.text_input("Email")
        password = st.text_input("Password", type="password")

        if st.button("Login"):
            user = login_user(email, password)
            if user:
                st.session_state['logged_in'] = True
                st.session_state['user'] = user
                st.success("Logged in successfully!")
            else:
                st.error("Invalid email or password.")

    if option == "Signup":
        username = st.text_input("Username")
        email = st.text_input("Email")
        password = st.text_input("Password", type="password")

        if st.button("Signup"):
            success = signup_user(username, email, password)
            if success:
                st.success("Signed up successfully! Please log in.")
            else:
                st.error("Signup failed.")

