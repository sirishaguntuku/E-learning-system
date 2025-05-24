import streamlit as st
import requests
import pandas as pd
import random

API_BASE = "http://localhost:5000"
# Path to the CSV file
CSV_FILE_PATH = "C:/cds/courses_v2.csv"
# File paths for CSV files
USERS_CSV_PATH = "C:/cds/users (1).csv"
INTERACTIONS_CSV_PATH = "C:/cds/interactions.csv"
REVIEWS_CSV_PATH = "C:/cds/reviews.csv"

# ----------- Page Configuration -----------
st.set_page_config(page_title="CourseBuddy", layout="wide")
st.title("🎓 Course Buddy : Your Course Recommender")

# ----------- Initialize session state variables -----------
def init_session():
    st.session_state.setdefault("user_logged_in", False)
    st.session_state.setdefault("admin_logged_in", False)
    st.session_state.setdefault("user_id", None)
    st.session_state.setdefault("show_recommendations", False)
    st.session_state.setdefault("enrollment_history", [])
    st.session_state.setdefault("enrolled_courses", set())
    st.session_state.setdefault("recent_enrolled", None)

if 'enrolled_courses' not in st.session_state:
    st.session_state.enrolled_courses = set()
if 'enrollment_history' not in st.session_state:
    st.session_state.enrollment_history = []
if 'recent_enrolled' not in st.session_state:
    st.session_state.recent_enrolled = None

init_session()

# ----------- Function to calculate course price -----------
def calculate_price(rating):
    try:
        return round(random.uniform(10, 50) * (float(rating) / 5), 2)
    except:
        return 20.0

# ----------- Display User Info -----------
def display_user_info():
    with st.sidebar:
        try:
            user_info = requests.get(f"{API_BASE}/user/{st.session_state.user_id}").json()
            st.markdown("#### 👤 User Details")
            st.write(f"**Username:** {user_info.get('username', 'N/A')}")
            st.write(f"**Email:** {user_info.get('email', 'N/A')}")
            st.write(f"**Contact:** {user_info.get('contact', 'N/A')}")
            st.write(f"**User ID:** {user_info.get('user_id', 'N/A')}")
        except Exception as e:
            st.error(f"Error fetching user details: {e}")

# ----------- Display Enrollment History -----------
def display_enrollment_history():
    if st.session_state.enrollment_history:
        st.markdown("### 📚 Your Enrolled Courses")
        for enrollment in st.session_state.enrollment_history:
            st.info(
                f"**Course ID:** {enrollment['course_id']} | "
                f"**Title:** {enrollment['title']} | "
                f"**Rating:** {enrollment['rating']} | "
                f"**Price:** ${enrollment['price']}"
            )
    else:
        st.warning("You have not enrolled in any course yet.")

# ----------- Display Courses -----------
def display_courses(courses):
    for course in courses:
        with st.expander(f"**{course['title']}**"):
            col1, col2 = st.columns([1, 2])
            with col1:
                st.markdown(f"**Category:** {course['category']}")
                st.markdown(f"**Difficulty:** {course['difficulty']}")
                st.markdown(f"**Rating:** {course.get('rating', 'N/A')}")
            with col2:
                st.markdown(f"**Course ID:** {course['course_id']}")
                price = calculate_price(course.get('rating', 3))
                st.markdown(f"**Price:** ${price}")

# ----------- Course Enrollment -----------
def enroll_course(course_id, payment_method):
    if course_id not in st.session_state.enrolled_courses:
        # Enrollment process with payment method
        st.session_state.enrollment_history.append({
            "course_id": course_id,
            "title": f"Course {course_id}",
            "rating": "N/A",
            "price": calculate_price(3),
            "payment_method": payment_method
        })
        st.session_state.enrolled_courses.add(course_id)
        st.session_state.recent_enrolled = {"course_id": course_id, "title": f"Course {course_id}"}
        st.success(f"✅ Course {course_id} enrolled successfully via {payment_method}!")
        st.balloons()
    else:
        st.warning(f"You have already enrolled in Course {course_id}.")

# ----------- Filter and Recommendation Functions -----------
def filter_courses(courses, course_id, title, category, difficulty, min_rating):
    filtered_courses = []
    for course in courses:
        if (course_id and course_id not in course['course_id']) or \
           (title and title.lower() not in course['title'].lower()) or \
           (category and category.lower() not in course['category'].lower()) or \
           (difficulty != "All" and difficulty != course['difficulty']) or \
           (min_rating and float(course['rating']) < min_rating):
            continue
        filtered_courses.append(course)
    return filtered_courses

def get_recommended_courses():
    try:
        rec_res = requests.get(f"{API_BASE}/hybrid_recommend/U{st.session_state.user_id}")
        if rec_res.status_code == 200:
            return rec_res.json().get("recommended_courses", [])
        else:
            st.error("Failed to fetch recommendations.")
            return []
    except Exception as e:
        st.error(f"Error: {e}")
        return []

# ----------- Role Selection -----------
role = st.sidebar.selectbox("Select Role", ["Student", "Admin"])

# ----------- Student Workflow -----------
if role == "Student":
    student_choice = st.sidebar.radio("Select Option", ["Login", "Register"])

    if student_choice == "Register":
        st.subheader("New User Registration")
        user_id = st.text_input("Enter your existing User ID (from system)")
        username = st.text_input("Choose a Username")
        password = st.text_input("Create Password", type="password")
        email = st.text_input("Email")
        contact = st.text_input("Contact")

        if st.button("Register"):
            try:
                res = requests.post(f"{API_BASE}/user/register", json={
                    "user_id": int(user_id),
                    "username": username,
                    "password": password,
                    "email": email,
                    "contact": contact
                })
                if res.status_code == 201:
                    st.success(res.text)
                else:
                    st.error(res.json().get("error", "Registration failed."))
            except Exception as e:
                st.error(f"Error: {e}")

    elif student_choice == "Login" and not st.session_state.user_logged_in:
        st.subheader("Student Login")
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")

        if st.button("Login"):
            try:
                res = requests.post(f"{API_BASE}/user/login", json={"username": username, "password": password})
                if res.status_code == 200:
                    user_data = res.json()
                    st.session_state.user_logged_in = True
                    st.session_state.user_id = user_data["user_id"]
                    st.session_state.show_recommendations = True
                    st.success(f"Login successful! Welcome, {user_data['name']}")
                    st.experimental_rerun()
                else:
                    st.error(res.json().get("error"))
            except Exception as e:
                st.error(f"Error: {e}")

    if st.session_state.user_logged_in and st.session_state.show_recommendations:
        st.subheader("🎓 User Dashboard")
        display_user_info()

        st.markdown("#### 📚 Filter Courses")
        course_id = st.text_input("Filter by Course ID")
        title = st.text_input("Filter by Title")
        category = st.text_input("Filter by Category")
        difficulty = st.selectbox("Filter by Difficulty", ["All", "Easy", "Medium", "Hard"])
        min_rating = st.slider("Filter by Minimum Rating", 1, 5, 1)

        if st.button("Apply Filters"):
            try:
                # Build query parameters
                params = {
                    "course_id": course_id,
                    "title": title,
                    "category": category,
                    "difficulty": None if difficulty == "All" else difficulty,
                    "min_rating": min_rating
                }

                # Send GET request to /filter_courses
                res = requests.get(f"{API_BASE}/filter_courses", params=params)
                if res.status_code == 200:
                    courses = res.json().get("courses", [])
                    if courses:
                        st.markdown("#### 📚 Filtered Courses")
                        display_courses(courses)
                    else:
                        st.info("No courses match the filter criteria.")
                else:
                    st.error(f"Failed to fetch courses: {res.text}")

            except Exception as e:
                st.error(f"Error: {e}")

        if st.button("Show Recommended Courses"):
            recommended_courses = get_recommended_courses()
            if recommended_courses:
                st.markdown("#### 📚 Recommended Courses")
                display_courses(recommended_courses)
            else:
                st.info("No recommendations available.")

        # Enrollment Section
        course_to_enroll = st.text_input("Enter the Course ID you wish to enroll in:")
        if course_to_enroll:
            payment_method = st.selectbox("Select Payment Method", ["Card", "Net Banking", "PayPal"])
            enroll_button = st.button(f"Enroll in Course {course_to_enroll}")
            if enroll_button:
                enroll_course(course_to_enroll, payment_method)

        # After Enrolling, Show Latest Enrolled Course Once
        if st.session_state.recent_enrolled:
            st.markdown("---")
            st.success("✅ Recently Enrolled Course:")
            recent = st.session_state.recent_enrolled
            st.info(
                f"**Course ID:** {recent['course_id']} | "
                f"**Title:** {recent['title']}"
            )

        display_enrollment_history()

# ----------- Admin Panel -----------

# ----------- Admin Login via API -----------
def admin_login(username, password):
    """Authenticate the admin using the API."""
    try:
        res = requests.post(f"{API_BASE}/admin/login", json={"username": username, "password": password})
        if res.status_code == 200:
            return res.json().get("admin", {})
        else:
            st.error(res.json().get("error", "Login failed"))
            return None
    except Exception as e:
        st.error(f"Error during login: {e}")
        return None

# ----------- Load Courses from CSV -----------
def load_courses():
    """Load courses from CSV using pandas."""
    try:
        courses_df = pd.read_csv(CSV_FILE_PATH)
        return courses_df
    except Exception as e:
        st.error(f"Error loading courses from CSV: {e}")
        return pd.DataFrame()

# ----------- Admin Panel after Login -----------
if 'admin_logged_in' not in st.session_state:
    st.session_state.admin_logged_in = False

if role == "Admin":
    admin_choice = st.sidebar.radio("Select Option", ["Login"])

    if admin_choice == "Login" and not st.session_state.admin_logged_in:
        st.subheader("Admin Login")
        username = st.text_input("Admin Username")
        password = st.text_input("Password", type="password")

        if st.button("Login as Admin"):
            admin_data = admin_login(username, password)
            if admin_data:
                # If login is successful, set session states for admin info
                st.session_state.admin_logged_in = True
                st.session_state.admin_name = admin_data.get("name", "Admin Name")
                st.session_state.admin_email = admin_data.get("email", "admin@example.com")
                st.session_state.admin_contact = admin_data.get("contact", "123-456-7890")
                st.success(f"Admin Login successful! Welcome, {st.session_state.admin_name}")
                st.experimental_rerun()  # Re-run to display admin details on the new page

    if st.session_state.admin_logged_in:
        st.markdown("### 🔒 Admin Panel")

        # Display Admin Details in Sidebar (excluding password)
        with st.sidebar:
            st.markdown("#### 👤 Admin Details")
            st.write(f"**Admin Name:** {st.session_state.admin_name}")
            st.write(f"**Email:** {st.session_state.admin_email}")
            st.write(f"**Contact:** {st.session_state.admin_contact}")

        st.markdown(f"### Welcome {st.session_state.admin_name}!")

        # Function to load and display the first 10 rows of a CSV
        def load_csv_data(file_path):
            try:
                data = pd.read_csv(file_path)
                return data.head(10)  # Return the first 10 rows
            except Exception as e:
                st.error(f"Error loading CSV file {file_path}: {e}")
                return pd.DataFrame()

        # Load and display data from each CSV file
        users_data = load_csv_data(USERS_CSV_PATH)
        interactions_data = load_csv_data(INTERACTIONS_CSV_PATH)
        reviews_data = load_csv_data(REVIEWS_CSV_PATH)
        courses_data = load_csv_data(CSV_FILE_PATH)

        if not users_data.empty:
            st.markdown("### Users Data (First 10 Rows)")
            st.dataframe(users_data)
        else:
            st.info("No data available in users CSV.")

        if not interactions_data.empty:
            st.markdown("### Interactions Data (First 10 Rows)")
            st.dataframe(interactions_data)
        else:
            st.info("No data available in interactions CSV.")

        if not reviews_data.empty:
            st.markdown("### Reviews Data (First 10 Rows)")
            st.dataframe(reviews_data)
        else:
            st.info("No data available in reviews CSV.")

        if not courses_data.empty:
            st.markdown("### Courses Data (First 10 Rows)")
            st.dataframe(courses_data)
        else:
            st.info("No data available in courses CSV.")

        # ----------- Sidebar Buttons to Download CSVs -----------
        st.sidebar.markdown("#### 📂 Download CSVs")


        # Create download buttons for each CSV file
        def create_download_button(file_path, label):
            try:
                with open(file_path, "rb") as file:
                    st.sidebar.download_button(label, file, file_name=file_path.split("/")[-1], mime="text/csv")
            except Exception as e:
                st.sidebar.error(f"Error generating download button for {label}: {e}")

        create_download_button(USERS_CSV_PATH, "Download Users CSV")
        create_download_button(INTERACTIONS_CSV_PATH, "Download Interactions CSV")
        create_download_button(REVIEWS_CSV_PATH, "Download Reviews CSV")
        create_download_button(CSV_FILE_PATH, "Download Courses CSV")

        # ----------- Admin Filter and Manage Courses -----------
        st.markdown("#### 📚 Filter and Manage Courses")

        # Load courses from CSV
        courses_df = load_courses()

        if not courses_df.empty:
            # Get filter criteria from admin input
            course_id = st.text_input("Enter Course ID to delete:")
            title = st.text_input("Filter by Title:")
            category = st.selectbox("Filter by Category:", ["All", "Math", "Science", "History", "Programming", "Art"])
            difficulty = st.selectbox("Filter by Difficulty:", ["All", "Easy", "Medium", "Hard"])
            min_rating = st.slider("Minimum Rating", 0, 5, 0)

            # Apply filtering on the DataFrame
            filtered_courses = courses_df

            if course_id:
                filtered_courses = filtered_courses[filtered_courses['course_id'] == course_id]
            if title:
                filtered_courses = filtered_courses[filtered_courses['title'].str.contains(title, case=False, na=False)]
            if category != "All":
                filtered_courses = filtered_courses[filtered_courses['category'] == category]
            if difficulty != "All":
                filtered_courses = filtered_courses[filtered_courses['difficulty'] == difficulty]
            if min_rating:
                filtered_courses = filtered_courses[filtered_courses['rating'] >= min_rating]

            # Show filtered courses
            if not filtered_courses.empty:
                st.markdown("### Filtered Courses")
                st.dataframe(filtered_courses)  # Display filtered courses
            else:
                st.info("No courses found matching the filter criteria.")

            # Button to delete course
            if course_id and st.button("Delete Course"):
                # Delete the course from the DataFrame
                courses_df = courses_df[courses_df['course_id'] != course_id]

                # Save the updated DataFrame back to CSV (replace the original file)
                try:
                    courses_df.to_csv(CSV_FILE_PATH, index=False)
                    st.success(f"✅ Course {course_id} deleted successfully!")
                except Exception as e:
                    st.error(f"Error saving updated courses: {e}")
        else:
            st.error("No courses found.")

