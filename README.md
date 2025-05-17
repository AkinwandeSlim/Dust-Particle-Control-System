
# Dust Particle Control System

The **Dust Particle Control System** is a Streamlit-based web application designed to monitor and predict dust particle concentrations (PM2.5 and PM10) using advanced machine learning techniques. This tool enables environmental agencies, industries, and researchers to analyze air quality data, visualize trends, and forecast PM2.5 levels for proactive dust control.

**🔗 Live Demo:** [Dust Particle Control App](https://dust-particle-control.streamlit.app/)

---

## 📌 Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Technologies](#technologies)
- [Installation](#installation)
- [Usage](#usage)
- [Data Requirements](#data-requirements)
- [Model Training and Predictions](#model-training-and-predictions)
- [Contributing](#contributing)
- [License](#license)
- [Contact](#contact)

---

## 🌍 Overview

The Dust Particle Control System provides a user-friendly platform for air quality analysis and prediction. Key capabilities include:

- **Exploratory Data Analysis (EDA):** Visualize distributions, correlations, and trends in air quality data.
- **Machine Learning Predictions:** Forecast PM2.5 levels using pre-trained models like XGBoost, Random Forest, and Voting Regressor.
- **Real-Time Insights:** Upload datasets for immediate visualizations and predictions.

**Note:** Deployed on **Streamlit Community Cloud** (1 GB RAM), the app disables training to optimize performance. Pre-trained models are stored on Google Drive and downloaded at runtime.

### Ideal For:

- **Clients:** Environmental agencies or industries monitoring air quality.
- **Collaborators:** Data scientists or developers exploring ML for environmental data.
- **Employees:** Team members maintaining or enhancing the system.

---

## ✨ Features

- **Data Upload:** Supports CSV or Excel files with fields such as PM2.5, PM10, temperature, humidity, etc.
- **Exploratory Data Analysis:**
  - Summary statistics (mean, median, etc.)
  - Visualizations: Histograms, box plots, KDE plots
  - Correlation matrix
  - Log transformation for PM2.5 outlier handling
- **Prediction:**
  - Models: Linear Regression, XGBoost, Random Forest, Bagging, Voting Regressor
  - Inputs: PM10, temperature, humidity, pressure, wind speed/direction, rainfall, hour, minutes
- **User Authentication:** Secure SQLite login system
- **Responsive UI:** Streamlit interface with real-time visualizations
- **Cloud Optimization:** Models fetched from Google Drive; training disabled on Streamlit Cloud

---

## ⚙️ Technologies

- **Frontend & App:** Streamlit
- **Language:** Python
- **Data Analysis:** Pandas, NumPy
- **Visualization:** Matplotlib, Seaborn
- **Machine Learning:** Scikit-learn, XGBoost
- **Storage:** Joblib (models), SQLite (authentication), Google Drive (models)
- **Hosting:** Streamlit Community Cloud

---

## 🛠 Installation

### ✅ Prerequisites

- Python 3.8+
- Git
- Virtual environment (recommended)

### 📦 Steps

1. **Clone the Repository:**
   ```bash
   git clone https://github.com/AkinwandeSlim/Dust-Particle-Control-System.git
   cd Dust-Particle-Control-System
   ```

2. **Create a Virtual Environment:**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scriptsctivate
   ```

3. **Install Dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

   **Dependencies include:**

   ```
   streamlit==1.38.0
   pandas==2.2.3
   numpy==1.26.4
   matplotlib==3.9.2
   seaborn==0.13.2
   scikit-learn==1.5.2
   xgboost==2.1.1
   joblib==1.4.2
   openpyxl==3.1.5
   scipy==1.14.1
   pillow==10.4.0
   psutil==6.0.0
   requests==2.32.3
   ```

4. **Set Up SQLite Database:**

   Create a test user:
   ```python
   import sqlite3
   conn = sqlite3.connect("data.db")
   c = conn.cursor()
   c.execute("CREATE TABLE IF NOT EXISTS usertable(username TEXT, password TEXT)")
   c.execute("INSERT INTO usertable(username, password) VALUES (?, ?)", ("testuser", "testpass"))
   conn.commit()
   conn.close()
   ```

5. **Run the App:**
   ```bash
   streamlit run dustapp.py
   ```

   Access at: `http://localhost:8501`

---

## 🚀 Usage

### 🔐 Login
Use test credentials (e.g., `testuser` / `testpass`).

### 📊 Data Modeling
1. Select **“Data Modeling”** from sidebar.
2. Upload CSV/Excel.
3. Explore EDA: stats, visualizations, correlations.

> ⚠️ Local training enabled for machines with ≥ 2 GB RAM and ≥ 2 CPUs. Training is disabled on Streamlit Cloud.

### 🔮 Predict PM2.5
1. Select **“Predict PM2.5”**.
2. Choose a model (e.g., Voting Regressor).
3. Enter required features.
4. Click **“Predict”**.

**Note:** Pre-trained models are automatically downloaded from Google Drive.

### 📄 Sample CSV
```csv
date,time,pm2.5,pm10,tsp,temp,hum,press,wspd,wdir,rain,timestamp
2023-01-01,00:00:00,10.5,20.3,30.0,25.0,60.0,1013.0,2.5,180.0,0.0,1672531200
```

---

## 📁 Data Requirements

The dataset should contain:

| Column     | Description                       |
|------------|-----------------------------------|
| `date`     | e.g., `2023-01-01`                |
| `time`     | e.g., `00:00:00`                  |
| `pm2.5`    | PM2.5 concentration (µg/m³)       |
| `pm10`     | PM10 concentration (µg/m³)        |
| `tsp`      | Total suspended particles (optional) |
| `temp`     | Temperature (°C)                  |
| `hum`      | Humidity (%)                      |
| `press`    | Pressure (hPa)                    |
| `wspd`     | Wind speed (m/s)                  |
| `wdir`     | Wind direction (°)                |
| `rain`     | Rainfall (mm)                     |
| `timestamp`| Unix timestamp                    |

---

## 🧠 Model Training and Predictions

### 🏋️‍♂️ Training
- **Local:** Enabled for systems with ≥2 GB RAM and ≥2 CPUs.
- **Cloud:** Disabled to improve performance.

Models are saved in the `models/` directory as `.pkl`.

### 🔮 Predictions
Pre-trained models and `scaler.pkl` are downloaded automatically from Google Drive.

Available Models:
- Linear Regression
- XGBoost
- Random Forest
- Bagging Regressor
- Voting Regressor (ensemble)

---

## 🤝 Contributing

Contributions are welcome!

1. Fork the repository.
2. Create a feature branch:
   ```bash
   git checkout -b feature/your-feature
   ```
3. Commit changes:
   ```bash
   git commit -m "Add your feature"
   ```
4. Push to GitHub:
   ```bash
   git push origin feature/your-feature
   ```
5. Open a **Pull Request**.

Please follow the [Contributor Covenant Code of Conduct](https://www.contributor-covenant.org/).

---

## 📝 License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for more details.

---

## 📬 Contact

- **Email:** [alexdata2022@gmail.com](mailto:alexdata2022@gmail.com)
- **GitHub:** [AkinwandeSlim](https://github.com/AkinwandeSlim/Dust-Particle-Control-System)
- **Issues:** [Open an Issue](https://github.com/AkinwandeSlim/Dust-Particle-Control-System/issues)
- **Live Demo:** [Streamlit App](https://dust-particle-control.streamlit.app/)

---

Thank you for exploring the **Dust Particle Control System**! We’re excited to support your air quality management needs.
