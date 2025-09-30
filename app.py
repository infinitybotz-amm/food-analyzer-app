# app.py
# Run with: streamlit run app.py

import streamlit as st
from PIL import Image
import google.generativeai as genai
from dotenv import load_dotenv
import os
import re
import logging
import sqlite3

# --- Setup logging ---
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("app.log"),   # Save logs to app.log
        logging.StreamHandler()           # Also print logs to console
    ]
)



# --- Setup SQLite database ---
DB_PATH = "orders.db"
conn = sqlite3.connect(DB_PATH, check_same_thread=False)
cursor = conn.cursor()
cursor.execute('''
    CREATE TABLE IF NOT EXISTS orders (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        email TEXT NOT NULL,
        cc_number TEXT NOT NULL,
        expiry TEXT NOT NULL,
        cvv TEXT NOT NULL,
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
    )
''')
conn.commit()


# --- Set vegetable background using custom CSS ---

st.markdown(
    """
    <style>
    body {
        background-image: url('https://images.unsplash.com/photo-1504674900247-0877df9cc836?auto=format&fit=crop&w=1500&q=80');
        background-size: cover;
        background-repeat: no-repeat;
        background-attachment: fixed;
    }
    </style>
    """,
    unsafe_allow_html=True
)

load_dotenv()
api_key = os.getenv("GOOGLE_API_KEY")
if not api_key:
    st.error("⚠️ GOOGLE_API_KEY not found. Please add it to your .env file.")
    logging.error("GOOGLE_API_KEY missing in environment variables.")
    st.stop()
genai.configure(api_key=api_key)
model = genai.GenerativeModel("gemini-2.5-flash")

tab1, tab2 = st.tabs(["🛒 Order Food", "🔒 Admin Orders"])


with tab1:
    st.header("🛒 Order This Food")

    uploaded_file = st.file_uploader("Upload a food photo", type=["jpg", "jpeg", "png"])
    if uploaded_file:
        image = Image.open(uploaded_file)
        st.image(image, caption="Uploaded Food", use_container_width=True)
        logging.info(f"User uploaded image: {uploaded_file.name}")

        if st.button("Estimate Calories"):
            logging.info("User clicked Estimate Calories button.")
            with st.spinner("Analyzing calories..."):
                response = model.generate_content(
                    [image, "Estimate the total calories in this food. Also list the food items detected."]
                )
            st.subheader("📊 Calorie Analysis")
            st.write(response.text)
            logging.info("Calorie estimation completed successfully.")

        if st.button("Find Cost to Order"):
            logging.info("User clicked Find Cost button.")
            with st.spinner("Estimating cost..."):
                response = model.generate_content(
                    [image, "Estimate how much this food would cost if ordered in a typical restaurant. Give price in USD."]
                )
            st.subheader("💵 Estimated Cost")
            st.success(response.text)
            logging.info("Cost estimation completed successfully.")

    with st.form("order_form"):
        name = st.text_input("Full Name")
        email = st.text_input("Email Address")
        cc_number = st.text_input("Credit Card Number (16 digits)")
        expiry = st.text_input("Expiry Date (MM/YY)")
        cvv = st.text_input("CVV (3 digits)", type="password")

        submitted = st.form_submit_button("Order Now")

        if submitted:
            # --- Validation only after clicking "Order Now" ---
            valid_name = len(name.strip()) > 0
            valid_email = re.match(r"[^@]+@[^@]+\.[^@]+", email)
            valid_cc = re.fullmatch(r"\d{16}", cc_number)
            valid_expiry = re.fullmatch(r"(0[1-9]|1[0-2])\/\d{2}", expiry)
            valid_cvv = re.fullmatch(r"\d{3}", cvv)

            if not valid_name:
                st.error("❌ Please enter your full name.")
            if not valid_email:
                st.error("❌ Invalid email format.")
            if not valid_cc:
                st.error("❌ Credit card number must be 16 digits.")
            if not valid_expiry:
                st.error("❌ Expiry date must be in MM/YY format (e.g., 08/27).")
            if not valid_cvv:
                st.error("❌ CVV must be exactly 3 digits.")

            if all([valid_name, valid_email, valid_cc, valid_expiry, valid_cvv]):
                # Store order in database
                cursor.execute(
                    "INSERT INTO orders (name, email, cc_number, expiry, cvv) VALUES (?, ?, ?, ?, ?)",
                    (name, email, cc_number, expiry, cvv)
                )
                conn.commit()
                st.success(f"✅ Order placed successfully for {name}! Your food will be delivered soon 🍴")
                logging.info(f"Order placed successfully by {name} ({email}). Order saved to database.")
            else:
                logging.warning("User attempted to order with invalid details.")



with tab2:
    st.header("🔒 Admin: View All Orders")
    admin_password = st.text_input("Enter admin password to view orders", type="password")
    if st.button("Show All Orders"):
        if admin_password == "admin123":  # Change this password for security
            cursor.execute("SELECT id, name, email, cc_number, expiry, cvv, timestamp FROM orders")
            rows = cursor.fetchall()
            if rows:
                import pandas as pd
                df = pd.DataFrame(rows, columns=["ID", "Name", "Email", "Credit Card", "Expiry", "CVV", "Timestamp"])
                st.dataframe(df)
            else:
                st.info("No orders found.")
        else:
            st.error("Incorrect admin password.")


