import streamlit as st

# Set the title of the application
st.title("My First Streamlit App")

# Display a header
st.header("Welcome to Streamlit!")

# Display some text
st.write("This is a simple application to demonstrate Streamlit's basic features.")

# Add a text input widget
user_input = st.text_input("Enter your name:")

# Display the user's input
if user_input:
    st.write(f"Hello, {user_input}!")

# Add a slider widget
age = st.slider("Select your age:", 0, 100, 25)
st.write(f"You are {age} years old.")

# Add a button
if st.button("Click me!"):
    st.write("Button clicked!")