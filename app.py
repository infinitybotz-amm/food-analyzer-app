# app.py
# Run with: streamlit run app.py

import streamlit as st
from PIL import Image
from google import genai
from dotenv import load_dotenv
import os
import re
import logging

# --- Setup logging ---
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("app.log"),   # Save logs to app.log
        logging.StreamHandler()           # Also print logs to console
    ]
)

# --- Load environment variables ---
load_dotenv()
api_key = os.getenv("GOOGLE_API_KEY")

if not api_key:
    st.error("⚠️ GOOGLE_API_KEY not found. Please add it to your .env file.")
    logging.error("GOOGLE_API_KEY missing in environment variables.")
    st.stop()

# Initialize Google GenAI client
client = genai.Client(api_key=api_key)

# --- Streamlit UI ---
st.set_page_config(page_title="🍽️ Food Analyzer", page_icon="🍎", layout="centered")
st.title("🍽️ Food Calorie, Cost & Order App")

uploaded_file = st.file_uploader("Upload a food photo", type=["jpg", "jpeg", "png"])

if uploaded_file:
    image = Image.open(uploaded_file)
    st.image(image, caption="Uploaded Food", use_container_width=True)
    logging.info(f"User uploaded image: {uploaded_file.name}")

    # --- Calorie Estimation ---
    if st.button("Estimate Calories"):
        logging.info("User clicked Estimate Calories button.")
        with st.spinner("Analyzing calories..."):
            response = client.models.generate_content(
                model="gemini-2.5-flash",
                contents=[image, "Estimate the total calories in this food. Also list the food items detected."]
            )
        st.subheader("📊 Calorie Analysis")
        st.write(response.text)
        logging.info("Calorie estimation completed successfully.")

    # --- Cost Estimation ---
    if st.button("Find Cost to Order"):
        logging.info("User clicked Find Cost button.")
        with st.spinner("Estimating cost..."):
            response = client.models.generate_content(
                model="gemini-2.5-flash",
                contents=[image, "Estimate how much this food would cost if ordered in a typical restaurant. Give price in USD."]
            )
        st.subheader("💵 Estimated Cost")
        st.success(response.text)
        logging.info("Cost estimation completed successfully.")

    # --- Order Food Section ---
# --- Order Food Section ---
st.header("🛒 Order This Food")

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
            st.success(f"✅ Order placed successfully for {name}! Your food will be delivered soon 🍴")
            logging.info(f"Order placed successfully by {name} ({email}).")
        else:
            logging.warning("User attempted to order with invalid details.")
