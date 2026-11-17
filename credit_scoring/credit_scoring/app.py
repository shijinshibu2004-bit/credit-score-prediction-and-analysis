import streamlit as st
from src.prediction import predict
import google.generativeai as genai
import os
# from dotenv import load_dotenv
import pdfkit  
import markdown, re
from fpdf import FPDF

# Load environment variables from .env file
# load_dotenv()

# Set up Gemini API
GENAI_API_KEY = "AIzaSyCk3n8O3Hy3UWqA7n8Sa4TSjCJTGqA5MC4" # Ensure you set this in your .env file

# Configure Gemini AI
genai.configure(api_key=GENAI_API_KEY)

class PDF(FPDF):
    def header(self):
        self.set_font("Arial", "B", 16)
        self.cell(0, 10, "Credit Score Report", ln=True, align="C")
        self.ln(10)

    def chapter_title(self, title):
        self.set_font("Arial", "B", 12)
        self.cell(0, 10, title, ln=True, align="L")
        self.ln(5)

    def add_bullet_point(self, text):
        self.set_x(15)  
        self.set_font("Arial", "", 11)
        self.cell(5, 5, "-")  
        self.multi_cell(0, 5, text)

    def add_table(self, table_data):
        self.set_font("Arial", "B", 10)
        col_widths = [60, 60, 60]  # Adjust column widths

        # Draw table header
        for header in table_data[0]:
            self.cell(col_widths[table_data[0].index(header)], 8, header, border=1, align="C")
        self.ln()

        self.set_font("Arial", "", 10)
        for row in table_data[1:]:
            for i in range(len(row)):
                self.cell(col_widths[i], 8, row[i], border=1, align="L")
            self.ln()


import mysql.connector
from mysql.connector import Error
import os


def get_database_connection():
    try:
        connection = mysql.connector.connect(host='localhost',user='root',password= 'shijin',database='credit_scoring')
        return connection
    except Error as e:
        print(f"Error connecting to MySQL: {e}")
        return None

import hashlib
import re

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def validate_email(email):
    pattern = r'^[\w\.-]+@[\w\.-]+\.\w+$'
    return re.match(pattern, email) is not None

def register_user(username, email, password):
    if not validate_email(email):
        return False, "Invalid email format"
    
    conn = get_database_connection()
    if conn:
        try:
            cursor = conn.cursor()
            password_hash = hash_password(password)
            
            cursor.execute("""
                INSERT INTO users (username, email, password_hash)
                VALUES (%s, %s, %s)
            """, (username, email, password_hash))
            
            conn.commit()
            return True, "Registration successful"
        except Exception as e:
            return False, str(e)
        finally:
            conn.close()
    return False, "Database connection error"

def login_user(username, password):
    conn = get_database_connection()
    if conn:
        try:
            cursor = conn.cursor()
            password_hash = hash_password(password)
            
            cursor.execute("""
                SELECT id, username FROM users 
                WHERE username = %s AND password_hash = %s
            """, (username, password_hash))
            
            user = cursor.fetchone()
            if user:
                return True, "Login successful", user[0]
            return False, "Invalid credentials", None
        finally:
            conn.close()
    return False, "Database connection error", None


# Add this at the beginning of your app
# def init_session_state():
#     if 'logged_in' not in st.session_state:
#         st.session_state.logged_in = False
#     if 'user_id' not in st.session_state:
#         st.session_state.user_id = None
def init_session_state():
    if 'logged_in' not in st.session_state:
        st.session_state.logged_in = False
    if 'user_id' not in st.session_state:
        st.session_state.user_id = None
    if 'show_register' not in st.session_state:
        st.session_state.show_register = False

def login_page():
    st.title("Login")
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")
    
    if st.button("Login"):
        success, message, user_id = login_user(username, password)
        if success:
            st.session_state.logged_in = True
            st.session_state.user_id = user_id
            st.success(message)
            st.rerun()
        else:
            st.error(message)
    
    if st.button("Register Instead"):
        st.session_state.show_register = True
        st.rerun()

def register_page():
    st.title("Register")
    username = st.text_input("Username")
    email = st.text_input("Email")
    password = st.text_input("Password", type="password")
    
    if st.button("Register"):
        success, message = register_user(username, email, password)
        if success:
            st.success(message)
            st.session_state.show_register = False
            st.rerun()
        else:
            st.error(message)
    
    if st.button("Login Instead"):
        st.session_state.show_register = False
        st.rerun()



def generate_gemini_response(credit_score):
    """Generates text using Google's Gemini AI"""
    model = genai.GenerativeModel("gemini-1.5-pro")
    if credit_score < 500:
        prompt = f"""
            You are an expert financial advisor. A user has a credit score of ${credit_score} and needs a detailed markdown report on improving their credit standing. 
            Generate a structured, professional markdown output with the following sections:

            ## 📉 Credit Score Analysis
            - Explain why a credit score below 500 is considered high risk.
            - Mention the impact on loan approvals and interest rates.

            ## 📌 Key Areas to Improve
            - **Credit Utilization:** How to reduce it effectively.
            - **Timely Payments:** Importance of consistent payments.
            - **Debt Reduction Strategies:** Practical steps to lower debt.
            - **Credit Mix & History:** How to diversify and build credit history.

            ## 🎯 Personalized Action Plan
            - Provide a **3-month** step-by-step guide to improve their credit score.
            - Mention tools or resources that can help.

            ## 📊 Financial Insights
            - Display a simple table with recommended financial habits.

            Ensure the output is **well-structured in markdown format** and provides actionable insights.
            """
    elif credit_score < 650:
        prompt = f"""
            You are a financial expert providing insights on credit scores. A user has a credit score of ${credit_score} and seeks advice on improving it. 
            Generate a structured, professional markdown report with the following sections:

            ## 📉 Credit Score Evaluation
            - Explain the importance of a credit score in the 500-650 range.
            - How this score affects loan approvals and credit card offers.

            ## 🚀 Strategies for Improvement
            - **On-time Payments:** How to build consistency.
            - **Credit Utilization:** Recommended usage percentage.
            - **Debt Consolidation:** When to consider it.
            - **New Credit Accounts:** How to open and manage them effectively.

            ## 📌 Next Steps
            - Provide a **6-month plan** to boost credit score with actionable tips.
            - Include financial tools and apps for tracking progress.

            ## 📊 Summary Table
            | Factor | Current Status | Recommended Action |
            |--------|---------------|-------------------|
            | Payment History | Improving | Set auto-payments |
            | Utilization | High | Reduce usage below 30% |
            | Credit Mix | Limited | Diversify credit types |

            Ensure the output is **markdown formatted** and user-friendly.
            """
    else:
        prompt = f"""
            You are a financial expert advising users on maintaining a good credit score. A user has a credit score of ${credit_score} and seeks insights on keeping or increasing it further. 
            Generate a structured, markdown-based financial insights report with the following sections:

            ## 🎉 Credit Score Overview
            - Explain why a score above 650 is favorable.
            - Benefits of having a high credit score (loan approvals, low interest rates).

            ## 🔑 Best Practices for Maintaining a Strong Credit Score
            - **Keep Utilization Low:** Ideal credit usage percentage.
            - **Maintain Old Accounts:** Why account age matters.
            - **Monitor Credit Reports:** How to check for errors and dispute them.
            - **Smart Credit Usage:** When to apply for new credit.

            ## 📈 Advanced Financial Strategies
            - **Investing & Credit Score:** How responsible credit use can help investments.
            - **Business Credit Building:** Steps to establish business credit.
            - **Elite Credit Card Perks:** How to maximize rewards.

            ## 📊 Summary
            | Best Practice | Benefit |
            |--------------|---------|
            | Keep Utilization < 30% | Higher Score |
            | Regular Payments | Build Trust |
            | No Hard Inquiries | Stable Credit |

            Make sure the output is **professionally formatted in markdown** with bullet points, tables, and structured sections.
            """

    response = model.generate_content(prompt)
    return response.text  # Extract the generated text






# Modify your main app code
def main():
    init_session_state()
    
    if not st.session_state.logged_in:
        if 'show_register' not in st.session_state:
            st.session_state.show_register = False
        
        if st.session_state.show_register:
            register_page()
        else:
            login_page()
        return

    # Add logout button in sidebar
    if st.sidebar.button("Logout"):
        st.session_state.logged_in = False
        st.session_state.user_id = None
        st.rerun()

    # Your existing credit scoring code goes here
    markdown_output=''
    st.title("🏦 Credit Scoring Prediction System")

    income = st.number_input("💰 Annual Income ($)", min_value=1000, max_value=5000000, step=500)
    credit_history = st.number_input("📜 Credit History (years)", min_value=0, max_value=50)
    loan_amount = st.number_input("💳 Loan Amount ($)", min_value=500, max_value=500000)
    existing_accounts = st.number_input("🏦 Existing Bank Accounts", min_value=0, max_value=10)
    credit_utilization = st.slider("📈 Credit Utilization Ratio", 0.0, 1.0, step=0.01)

    if st.button("🔮 Predict Credit Score"):
        user_data = {
            "income": income,
            "credit_history": credit_history,
            "loan_amount": loan_amount,
            "existing_accounts": existing_accounts,
            "credit_utilization": credit_utilization
        }
        
        # Get prediction results
        result, credit_score, confidence = predict(user_data)
        pred_result = '✅ Approved' if result == 1 else '❌ Rejected'

        st.success(f"🎯 **Credit Prediction:** {pred_result}")
        st.info(f"📊 **Predicted Credit Score:** {credit_score}")
        st.progress(int(confidence * 100))  # Show confidence level

        # Generate insights and store in session state
        if credit_score < 500:
            st.warning("⚠️ Low credit score! Consider reducing credit utilization.")
        elif credit_score < 650:
            st.warning("💳 Moderate risk. Improve payment history for better offers.")
        else:
            st.success("🎉 Good credit score! Eligible for most loans.")
        
        insights = generate_gemini_response(credit_score)
        st.session_state["markdown_output"] = insights  # Store in session state

        st.write(insights)  # Display insights


    st.write(markdown_output)



    # PDF Download
    # def save_as_pdf(md_text, pdf_path="credit_report.pdf"):
    #     try:
    #         if not md_text.strip():
    #             st.error("⚠️ No content available for PDF.")
    #             return None

    #         # Convert Markdown to HTML
    #         html_content = markdown.markdown(md_text)

    #         # Ensure wkhtmltopdf is installed
    #         config = pdfkit.configuration(wkhtmltopdf=r"C:\Program Files\wkhtmltopdf\bin\wkhtmltopdf.exe")

    #         # Generate PDF from HTML
    #         pdfkit.from_string(html_content, pdf_path, configuration=config)

    #         # Debugging: Check if file was created
    #         if os.path.exists(pdf_path):
    #             print(f"✅ PDF successfully created at {pdf_path}")
    #             return pdf_path
    #         else:
    #             st.error("⚠️ PDF generation failed.")
    #             return None
    #     except Exception as e:
    #         st.error(f"❌ Error generating PDF: {e}")
    #         return None

    def save_as_pdf(markdown_output):
        pdf = PDF()
        pdf.set_auto_page_break(auto=True, margin=15)
        pdf.add_page()
        pdf.set_font("Arial", "", 12)

        # Ensure encoding is correct
        markdown_output = markdown_output.encode("latin1", "ignore").decode("utf-8")

        # Parse Markdown and add elements to PDF
        lines = markdown_output.split("\n")
        table_data = []
        is_table = False

        for line in lines:
            line = line.strip()

            if not line:
                continue

            # Headers
            if line.startswith("# "):
                pdf.chapter_title(line.replace("# ", "").strip())
            elif line.startswith("## "):
                pdf.chapter_title(line.replace("## ", "").strip())

            # Bullet points
            elif line.startswith("- ") or line.startswith("* "):
                pdf.add_bullet_point(line[2:].strip())

            # Tables (Markdown format)
            elif "|" in line:
                if "---" in line:
                    continue  # Skip table formatting row
                is_table = True
                table_data.append([col.strip() for col in line.split("|") if col])

            # Regular text
            else:
                if is_table:
                    pdf.add_table(table_data)
                    table_data = []
                    is_table = False
                pdf.multi_cell(0, 7, line)

        # Handle any remaining table
        if table_data:
            pdf.add_table(table_data)

        pdf_file = "credit_report.pdf"
        pdf.output(pdf_file, "F")

        return pdf_file



    if st.button("📥 Download Insights as PDF"):
        markdown_output = st.session_state.get("markdown_output", "")

        if not markdown_output.strip():
            st.error("⚠️ No insights available. Predict your credit score first!")
        else:
            pdf_file = save_as_pdf(markdown_output)

            if pdf_file:
                with open(pdf_file, "rb") as f:
                    st.download_button(label="📥 Download PDF", data=f, file_name="credit_report.pdf", mime="application/pdf")
                print("✅ PDF download button displayed.")
            else:
                st.error("⚠️ Failed to generate PDF.")


if __name__ == "__main__":
    main()




