import sqlite3
import streamlit as st
import pandas as pd

# Connect to the SQLite database
def get_connection():
    conn = sqlite3.connect('food_tracker.db')
    return conn

# Create user in the database
def create_user(username, password):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, password))
    conn.commit()
    conn.close()

# Check user credentials for login
def authenticate_user(username, password):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM users WHERE username = ? AND password = ?", (username, password))
    user = cursor.fetchone()
    conn.close()
    if user:
        return user[0]  # Return user ID
    return None

# Store food log in the database
def add_food_log(user_id, food_name, weight, fats, carbs, proteins, calories):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''INSERT INTO food_logs (user_id, food_name, weight, fats, carbs, proteins, calories)
                      VALUES (?, ?, ?, ?, ?, ?, ?)''', 
                   (user_id, food_name, weight, fats, carbs, proteins, calories))
    conn.commit()
    conn.close()

# Retrieve food logs for a user
def get_user_food_logs(user_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT food_name, weight, fats, carbs, proteins, calories FROM food_logs WHERE user_id = ?", (user_id,))
    logs = cursor.fetchall()
    conn.close()
    return logs

# Main App
if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False

# Show login/signup forms
if not st.session_state['logged_in']:
    st.title("Welcome to the Food Tracker App")
    
    # Login or Sign-up selection
    option = st.radio("Login or Sign Up", ("Login", "Sign Up"))

    if option == "Sign Up":
        st.subheader("Create a new account")
        new_username = st.text_input("New Username")
        new_password = st.text_input("New Password", type="password")
        if st.button("Sign Up"):
            try:
                create_user(new_username, new_password)
                st.success("Account created successfully! You can now log in.")
            except sqlite3.IntegrityError:
                st.error("Username already exists. Try a different one.")
    else:
        st.subheader("Log In to your account")
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        if st.button("Login"):
            user_id = authenticate_user(username, password)
            if user_id:
                st.session_state['logged_in'] = True
                st.session_state['user_id'] = user_id
                st.success(f"Welcome, {username}!")
            else:
                st.error("Invalid username or password.")

# If logged in, show food tracker
if st.session_state['logged_in']:
    st.title("Food Tracker")
    
    # Load food data from a CSV (you can add more food items)
    food_data = pd.read_csv('food_data.csv')
    
    # Input: Food name and weight
    food_name = st.selectbox('Select a food', food_data['food_name'].unique())
    weight = st.number_input('Enter the weight (in grams)', min_value=0, step=10)

    # Calculate nutritional values based on weight
    def calculate_nutrition(food_name, weight):
        food = food_data[food_data['food_name'] == food_name].iloc[0]
        fats = food['fats'] * weight / 100
        carbs = food['carbs'] * weight / 100
        proteins = food['proteins'] * weight / 100
        calories = food['calories'] * weight / 100
        return fats, carbs, proteins, calories

    if st.button("Add food"):
        fats, carbs, proteins, calories = calculate_nutrition(food_name, weight)
        add_food_log(st.session_state['user_id'], food_name, weight, fats, carbs, proteins, calories)
        st.success(f"{food_name} ({weight}g) added to your log.")

    # Show user's food logs
    st.subheader("Your Food Log")
    food_logs = get_user_food_logs(st.session_state['user_id'])
    
    if food_logs:
        log_df = pd.DataFrame(food_logs, columns=['Food', 'Weight', 'Fats', 'Carbs', 'Proteins', 'Calories'])
        st.write(log_df)

        # Show totals as a bar chart
        totals = log_df[['Fats', 'Carbs', 'Proteins', 'Calories']].sum()
        chart_data = pd.DataFrame({
            'Nutrient': ['Fats', 'Carbs', 'Proteins', 'Calories'],
            'Amount': [totals['Fats'], totals['Carbs'], totals['Proteins'], totals['Calories']]
        })
        st.bar_chart(chart_data.set_index('Nutrient'))

    # Logout button
    if st.button("Logout"):
    # Clear session state on logout
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.rerun()
