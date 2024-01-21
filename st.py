
import streamlit as st
from PIL import Image
import pymongo
from io import BytesIO
import base64
import hashlib

# MongoDB setup
def get_mongo_client(uri):
    return pymongo.MongoClient(uri)

def save_image_to_mongo(client, db_name, collection_name, image, image_name, user_id):
    db = client[db_name]
    collection = db[collection_name]
    image_bytes = image.getvalue()
    encoded_image = base64.b64encode(image_bytes).decode('utf-8')
    collection.insert_one({"user_id": user_id, "name": image_name, "image": encoded_image})

def get_images_from_mongo(client, db_name, collection_name, user_id):
    db = client[db_name]
    collection = db[collection_name]
    images = []
    for record in collection.find({"user_id": user_id}):
        image_data = base64.b64decode(record["image"])
        images.append(Image.open(BytesIO(image_data)))
    return images

def get_recommended_items(client, db_name, collection_name, category_id):
    db = client[db_name]
    collection = db[collection_name]
    recommended_items = []
    for record in collection.find({"category_id": category_id}):
        image_data = base64.b64decode(record["image"])
        recommended_items.append(Image.open(BytesIO(image_data)))
    return recommended_items

# User Authentication Functions
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def register_user(client, db_name, user_data):
    db = client[db_name]
    users_collection = db["users"]
    user_data["password"] = hash_password(user_data["password"])
    users_collection.insert_one(user_data)

def check_user_login(client, db_name, mobile_number, password):
    db = client[db_name]
    users_collection = db["users"]
    user = users_collection.find_one({"mobile_number": mobile_number})
    if user and user["password"] == hash_password(password):
        return user
    return None

# Local CSS function
def local_css(file_name):
    with open(file_name, "r") as f:
        st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)

# Function to process uploaded files
def process_uploaded_files(uploaded_files, client, user_id):
    for uploaded_file in uploaded_files:
        if uploaded_file is not None:
            image = Image.open(uploaded_file)
            img_byte_arr = BytesIO()
            image.save(img_byte_arr, format='PNG')
            save_image_to_mongo(client, "fashion", "fashion_", img_byte_arr, uploaded_file.name, user_id)

# Main function
def main():
    local_css("style.css")
    logo_filenames = ["logo.jpg", "logo1.jpeg", "logo2.jpg", "logo3.jpg", "logo4.jpg", "logo5.jpg"]
    st.markdown(
    """
    <style>
    .content {
        background-color: #add8e6;
        padding: 10px;
        border-radius: 5px;
    }
    </style>
    """,
    unsafe_allow_html=True
)
    st.markdown(
    '''
    <div class="content">
        <h2>TECH STACK</h2>
        <ul>
            <li>StreamLit</li>
            <li>Python ML Frameworks</li>
            <li>MongoDB Atlas</li>
        </ul>
        <h2>Hosting Service</h2>
        <p>streamlit sharing + GitHub</p>
        <h2>Security</h2>
        <p>Cloud Fare</p>
        <h2>DNS</h2>
        <p>Porkbun Through Godaddy</p>
        <h2>Testing Purpose Credentials</h2>
        <p><b>User1:</b></p>
        <p>Username: 9182442102</p>
        <p>Password: 1234</p>
        <p><b>User2:</b></p>
        <p>Username: 987654321</p>
        <p>Password: 4321</p>
        <p>Login, choose your apparel from wardrobe and grab your matchings.</p>
        <p><i>Note: Don't concentrate on frontend, this project mainly concentrates on the algorithm to find matchings for their wardrobe.</i></p>
    </div>
    ''',
    unsafe_allow_html=True
)
    # Create a row of columns
    cols = st.columns(len(logo_filenames))

    # Iterate over each column and corresponding logo filename
    for col, logo_filename in zip(cols, logo_filenames):
        with col:  # Use the column as the context
            logo = Image.open(logo_filename)
            st.image(logo, width=100)

    # MongoDB client
    uri = "mongodb+srv://pavan_tech:SjsGBgoWBLyDHaWX@cluster0.3zqhlo9.mongodb.net/?retryWrites=true&w=majority"  # Replace with your MongoDB URI
    client = get_mongo_client(uri)

    # Session state initialization
    if 'current_user' not in st.session_state:
        st.session_state.current_user = None
    if 'show_sidebar' not in st.session_state:
        st.session_state.show_sidebar = False
    if 'images' not in st.session_state:
        st.session_state.images = None

    # User not logged in
    if st.session_state.current_user is None:
        with st.form("user_form"):
            st.write("Register or Login")
            name = st.text_input("Name (for registration)")
            mobile_number = st.text_input("Mobile Number")
            password = st.text_input("Password", type="password")
            submitted = st.form_submit_button("Login")
            if submitted:
                user = check_user_login(client, "fashion", mobile_number, password)
                if user:
                    st.session_state.current_user = user
                    st.success("Logged in successfully!")
                else:
                    st.error("Invalid login details.")
            registered = st.form_submit_button("Register")
            if registered:
                register_user(client, "fashion", {"name": name, "mobile_number": mobile_number, "password": password})
                st.success("Registered successfully! Please login.")

    # User is logged in
    if st.session_state.current_user is not None:
        user_id = st.session_state.current_user["_id"]
        user_name = st.session_state.current_user["name"]
        st.title(f"Hey {user_name}")

        if st.button("☰"):
            st.session_state.show_sidebar = not st.session_state.show_sidebar

        if st.session_state.show_sidebar:
            st.sidebar.title("Wardrobe")
            if st.sidebar.button("Show Wardrobe"):
                st.session_state.images = get_images_from_mongo(client, "fashion", "fashion_", user_id)
            if st.sidebar.button("Logout"):
                st.session_state.current_user = None
                st.session_state.show_sidebar = False
                st.session_state.images = None
                st.experimental_rerun()

        uploaded_files = st.file_uploader("Upload Images", type=['jpg', 'jpeg', 'png'], accept_multiple_files=True)
        if uploaded_files:
            submit_button = st.button("Submit")
            if submit_button:
                process_uploaded_files(uploaded_files, client, user_id)
                st.success("Images uploaded successfully!")
                st.session_state.images = get_images_from_mongo(client, "fashion", "fashion_", user_id)

        if st.button("Wardrobe"):
            st.session_state.images = get_images_from_mongo(client, "fashion", "fashion_", user_id)

        selected_images = []
        if st.session_state.images:
            cols_per_row = 3
            for i in range(0, len(st.session_state.images), cols_per_row):
                cols = st.columns(cols_per_row)
                for j in range(cols_per_row):
                    index = i + j
                    if index < len(st.session_state.images):
                        with cols[j]:
                            if st.checkbox(f"Select Image {index}", key=f"select_{index}"):
                                selected_images.append(st.session_state.images[index])
                            st.image(st.session_state.images[index], use_column_width=True)

        if selected_images:
            gender = st.selectbox("Gender", ["Male", "Female"], key="gender_select")
            category = st.selectbox("Category", ["Top Wear", "Bottom Wear", "Foot Wear", "Accessories"], key="category_select")
            category_id_mapping = {
                ("Male", "Top Wear"): 1,
                ("Male", "Bottom Wear"): 2,
                ("Male", "Foot Wear"): 3,
                ("Male", "Accessories"): 4,
                ("Female", "Top Wear"): 5,
                ("Female", "Bottom Wear"): 6,
                ("Female", "Foot Wear"): 7,
                ("Female", "Accessories"): 8
            }
            selected_category_id = category_id_mapping[(gender, category)]
            if st.button("Recommend", key="recommend_button"):
                recommended_items = get_recommended_items(client, "fashion", "fashion_", selected_category_id)
                cols_per_row = 3
                for i in range(0, len(recommended_items), cols_per_row):
                    cols = st.columns(cols_per_row)
                    for j in range(cols_per_row):
                        index = i + j
                        if index < len(recommended_items):
                            with cols[j]:
                                st.image(recommended_items[index], use_column_width=True, output_format="JPEG")

if __name__ == "__main__":
    main()

