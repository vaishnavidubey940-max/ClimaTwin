# ClimateTwin-IN 
PROJECT TILTLE- ClimateTwin-IN - AI Powered Digital Twin of India's Climate

Team Name- CLIMATE CORE          	

Problem Statement-

India is facing increasingly frequent floods, droughts, heatwaves, and unpredictable rainfall due to climate change.

Existing weather systems may not provide highly accurate local predictions or clearly show how climate changes could affect different regions. This creates challenges for farmers, government agencies, disaster management teams, researchers, and planners when preparing for future conditions.

ClimaTwin-IN addresses this problem by creating an AI-powered Digital Twin of India's Climate using data from ISRO satellites, IMD weather stations, and historical climate records.

The system monitors climate conditions, predicts rainfall and temperature, and allows users to test "What-If" scenarios to support better decision-making and climate preparedness.

Solution Overview

ClimaTwin-IN combines climate data, AI-based prediction, interactive visualization, and scenario simulation into a single web platform.

Key Features
 Combines ISRO satellite images and IMD rainfall/weather data. <br>
 Automatically collects and updates climate data. <br>
 Uses AI (Random Forest) for short-term rainfall and temperature predictions.<br>
 Displays climate information through easy-to-understand maps and charts.<br>
 Provides a "What-If" simulator to test different climate scenarios.<br>
 Converts complex climate data into clear visual insights.<br>
 Supports farmers, disaster management teams, students, researchers, and planners.<br>
 Provides a simple web interface accessible through a normal laptop and web browser.<br>

Live Demonstration Link: Coming Soon

Technology Stack
Based on the project architecture and features:
Python| Flask| FastAPI| Uvicorn| Pandas| Random Forest| Scikit-learn| SQLite| HTML5| CSS3| Vite| JavaScript| Leaflet| Chart.js

Team Members Name-           	
Vaishnavi Dubey (Team leader)-Frontend <br>
Mritunjai Jha (Team member)-UI/UX <br>
Bhumika Gupta (Team member-Backend <br>
Apeksha Gupta	(Team member)-Database <br>

Setup instruction

1. Clone the Repository
git clone <your-repository-link>
cd dharatwin-ai-2

2. Backend Setup
   
Create a Python virtual environment:
python -m venv .venv

Install the required Python dependencies:
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install -r requirements.txt

Start the FastAPI backend server:
.\.venv\Scripts\python.exe -m uvicorn backend.fastapi_app:app --port 5000 --reload

The backend will run at:
http://127.0.0.1:5000

3. Frontend Setup
   
Open a new terminal in VS Code.
Start the frontend server:

cd "C:\Users\apeks\Documents\New folder\dharatwin-ai-2--main"
.\.venv\Scripts\python.exe -m http.server 3000 --directory frontend

The frontend will be available at:
http://localhost:3000

Open this URL in your browser.

