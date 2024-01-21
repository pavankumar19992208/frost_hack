
import streamlit as st
from PIL import Image
import pymongo
from io import BytesIO
import base64
import hashlib

# MongoDB setup
def process_uploaded_files(uploaded_files, client, user_id):
    for uploaded_file in uploaded_files:
        if uploaded_file is not None:
            save_image_to_mongo(client, "fashion", "fashion_", uploaded_file, uploaded_file.name, user_id)
    st.session_state.images = None
    st.experimental_rerun()

def process_captured_image(captured_image, client, user_id):
    # Assuming captured_image is a bytes-like object
    save_image_to_mongo(client, "fashion", "fashion_", BytesIO(captured_image), "captured_image.jpg", user_id)
    st.session_state.images = None
    st.experimental_rerun()

def get_mongo_client(uri):
    return pymongo.MongoClient(uri)

# MongoDB Image Functions
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

def local_css(file_name):
    with open(file_name, "r") as f:
        st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)

def main():
    local_css("style.css")

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
                for uploaded_file in uploaded_files:
                    if uploaded_file is not None:
                        save_image_to_mongo(client, "fashion", "fashion_", uploaded_file, uploaded_file.name, user_id)
                st.success("Wardrobe Updated")#1
                st.session_state.images = None
                st.experimental_rerun()
        selected_images = []
        if st.button("Wardrobe", key="wardrobe_button"):
            st.session_state.images = get_images_from_mongo(client, "fashion", "fashion_", st.session_state.current_user["_id"])
        
        if st.session_state.images:
            cols_per_row = 3
            for i in range(0, len(st.session_state.images), cols_per_row):
                cols = st.columns(cols_per_row)
                for j in range(cols_per_row):
                    index = i + j
                    if index < len(st.session_state.images):
                        with cols[j]:
                            # Display checkbox with each image
                            if st.checkbox(f"Select Image {index}", key=f"select_{index}"):
                                selected_images.append(st.session_state.images[index])
                            st.image(st.session_state.images[index], use_column_width=True)
        
        if selected_images:
            if st.button("Recommend", key="recommend_button"):
                recommended_items = send_images_to_backend(selected_images)  # Implement this function as required
                st.write("Recommended Items")
                for item in recommended_items:
                    st.image(item, use_column_width=True)


def send_images_to_backend(selected_images):
    # Placeholder function for sending images to backend and getting recommendations
    # You'll need to define how to send these images and process the response
    # This is a dummy function and should be replaced with actual implementation
    recommended_items = []  # Replace with actual response from backend
    return recommended_items


if __name__ == "__main__":
    main()





