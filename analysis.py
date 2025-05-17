import streamlit as st 
import numpy as np 
import pickle
import pandas as pd
from pandas import plotting
import os
import matplotlib.pyplot as plt
import seaborn as sns
plt.style.use('fivethirtyeight')
import joblib
import gc
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
import warnings                                  
warnings.filterwarnings('ignore')
import seaborn as sns                            # more plots
from dateutil.relativedelta import relativedelta # working with dates with style
from scipy.optimize import minimize              # for function minimization
import scipy.stats as scs
from itertools import product                    # some useful functions
from sklearn.metrics import r2_score, median_absolute_error, mean_absolute_error
from sklearn.metrics import median_absolute_error, mean_squared_log_error
from sklearn.model_selection import TimeSeriesSplit # you have everything done for you
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LinearRegression
from sklearn.ensemble import BaggingRegressor
from sklearn.ensemble import RandomForestRegressor
from xgboost import XGBRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
from scipy import stats
# let look at a final approach to combine three regression we have so far using Voting method
from sklearn.ensemble import VotingRegressor
import psutil
import platform
import requests
import shutil




scaler = StandardScaler()


BASE_DIR = os.getcwd()
MODEL_DIR ='models/'




# Function to check if training is allowed
def can_train():
    # Check if running on Streamlit Cloud
    is_cloud = os.getenv("STREAMLIT_SHARING") is not None or platform.system() == "Linux"
    
    # Check system resources
    try:
        available_ram = psutil.virtual_memory().available / (1024 ** 3)  # RAM in GB
        cpu_count = psutil.cpu_count(logical=True)  # CPU cores
    except Exception:
        return False
    
    # Allow training only if local, with >=2 GB RAM and >=2 CPU cores
    return not is_cloud and available_ram >= 2.0 and cpu_count >= 2




if not os.path.exists(MODEL_DIR):
    os.makedirs(MODEL_DIR)


def get_binary_file_downloader_html(bin_file, file_label='File'):
    with open(bin_file, 'rb') as f:
        data = f.read()
    bin_str = base64.b64encode(data).decode()
    href = f'<a href="data:application/octet-stream;base64,{bin_str}" download="{os.path.basename(bin_file)}">Download {file_label}</a>'
    return href



def download_file_from_google_drive(file_id, destination):
    """Download a file from Google Drive using its file ID."""
    URL = "https://drive.google.com/uc?export=download"
    session = requests.Session()
    response = session.get(URL, params={'id': file_id}, stream=True)
    with open(destination, 'wb') as f:
        for chunk in response.iter_content(32768):
            if chunk:
                f.write(chunk)



@st.cache_data
def convert_df(df):
   return df.to_csv().encode('utf-8')







# Handle datetime conversion with error handling
def parse_datetime(row):
    try:
        return pd.to_datetime(row['date'] + ' ' + row['time'], format="%Y-%m-%d %H:%M:%S", errors='coerce')
    except Exception as e:
        return pd.NaT  # Assign NaT (Not a Time) if parsing fails


def Dataset_upload():
    # Define the required columns
    required_columns = ['date', 'time', 'timestamp', 'pm2.5', 'pm10', 'tsp', 'temp', 'hum', 'press', 'wspd', 'wdir', 'rain']

    # Check if the dataset is already in session state
    if 'uploaded_data' in st.session_state and isinstance(st.session_state['uploaded_data'], pd.DataFrame):
        st.success("Existing dataset loaded from session!")
        st.write("## Data Preview")
        st.dataframe(st.session_state['uploaded_data'])

        # Option to re-upload the dataset
        reupload = st.checkbox("Re-upload dataset")
        if not reupload:
            return st.session_state['uploaded_data']

    # File uploader for new dataset
    data_file = st.file_uploader("**Upload a CSV or Excel file here**", type=["csv", "xlsx"])  

    if data_file is not None:
        # Read the uploaded file
        if data_file.name.endswith('.csv'):
            df = pd.read_csv(data_file)
        elif data_file.name.endswith('.xlsx'):
            df = pd.read_excel(data_file, engine='openpyxl')

        # Check if all required columns are present
        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            st.error(f"The uploaded dataset is missing the following required columns: {missing_columns}")
            return None

        # Check if 'tsp' is present before dropping it
        if 'tsp' in df.columns:
            df = df.drop(['tsp'], axis=1)
        else:
            st.warning("The 'tsp' column is not present in the dataset.")

        # Data preprocessing steps
        df = df.rename(columns={'pm2.5': 'pm25'})
        # df['date'] = df['date'].astype(str)
        # df['time'] = df['time'].astype(str)
        # df['datetime'] = pd.to_datetime(df['date'] + ' ' + df['time'])
        
        df['date'] = df['date'].astype(str)

        # Clean up 'time' column: Keep only the last valid HH:MM:SS part
        df['time'] = df['time'].astype(str).str.extract(r'(\d{2}:\d{2}:\d{2})', expand=False)

        # Handle missing values in 'time' after extraction
        df['time'].fillna('00:00:00', inplace=True)

        try:
            # Combine date and cleaned time column
            df['datetime'] = pd.to_datetime(df['date'] + ' ' + df['time'], errors='coerce')
        except Exception as e:
            st.error(f"Datetime conversion error: {e}")
            return None

        # Drop rows where datetime conversion failed
        df.dropna(subset=['datetime'], inplace=True)
        
            
        df = df.drop(['date', 'time', 'timestamp'], axis=1)
        df.set_index(['datetime'], inplace=True)
        df = df.astype(float)

        # Store the dataset in session state
        st.session_state['uploaded_data'] = df

        # Display the data
        st.write("## Data Preview")
        st.dataframe(df)

        return df

    # If no data is uploaded and nothing is in session state, show a message
    st.info("Please upload a dataset.")
    return None


def plotMovingAverage(series, window, plot_intervals=False, scale=1.96, plot_anomalies=False):
	rolling_mean = series.rolling(window=window).mean()
	fig=plt.figure(figsize=(20,10))
	plt.title("Moving average of pm2.5\n window size = {}".format(window))
	plt.plot(rolling_mean, "g", label="Rolling mean trend")
	if plot_intervals:
		mae = mean_absolute_error(series[window:], rolling_mean[window:])
		deviation = np.std(series[window:] - rolling_mean[window:])
		lower_bond = rolling_mean - (mae + scale * deviation)
		upper_bond = rolling_mean + (mae + scale * deviation)
		plt.plot(upper_bond, "r--", label="Upper Bond / Lower Bond")
		plt.plot(lower_bond, "r--")
		if plot_anomalies:
			anomalies = pd.DataFrame(index=series.index, columns=series.columns)
			anomalies[series<lower_bond] = series[series<lower_bond]
			anomalies[series>upper_bond] = series[series>upper_bond]
			plt.plot(anomalies, "ro", markersize=10)

	plt.plot(series[window:], label="Actual values")
	plt.legend(loc="upper left")
	plt.grid(True)
	st.pyplot(fig)



def mean_absolute_percentage_error(y_true, y_pred, threshold=1e-5):
    y_true, y_pred = np.array(y_true), np.array(y_pred)
    # Replace zero values in y_true with threshold
    y_true[np.abs(y_true) < threshold] = threshold
    return np.mean(np.abs((y_true - y_pred) / y_true)) * 100


def timeseriesCVscore(params, series, loss_function=mean_squared_error, slen=24):
    """
        Returns error on CV

        params - vector of parameters for optimization
        series - dataset with timeseries
        slen - season length for Holt-Winters model
    """
    # errors array
    errors = []

    values = series.values
    alpha, beta, gamma = params

    # set the number of folds for cross-validation
    tscv = TimeSeriesSplit(n_splits=3)

    # iterating over folds, train model on each, forecast and calculate error
    for train, test in tscv.split(values):

        model = HoltWinters(series=values[train], slen=slen,
                            alpha=alpha, beta=beta, gamma=gamma, n_preds=len(test))
        model.triple_exponential_smoothing()

        predictions = model.result[-len(test):]
        actual = values[test]
        error = loss_function(predictions, actual)
        errors.append(error)

    return np.mean(np.array(errors))

def moving_average(series, n):
    """
        Calculate average of last n observations
    """
    return np.average(series[-n:])

def timeseries_train_test_split(X, y, test_size):
    """
        Perform train-test split with respect to time series structure
    """

    # get the index after which test set starts
    test_index = int(len(X)*(1-test_size))

    X_train = X.iloc[:test_index]
    y_train = y.iloc[:test_index]
    X_test = X.iloc[test_index:]
    y_test = y.iloc[test_index:]

    return X_train, X_test, y_train, y_test





def prepareData(series, test_size,lags=None,timeseries='timeseries',target_encoding=False):
    # copy of the initial dataset
    data = pd.DataFrame(series.copy(deep=True))
    # data.columns = ["y"]
    # datetime features
    data.index = pd.to_datetime(data.index)
    data["hour"] = data.index.hour
    data["minutes"]=data.index.minute
    # # Example: Rolling mean for PM2.5
    data['pm25_rolling_mean'] = data['pm25_log'].rolling(window=30).mean()
    if target_encoding:
        # calculate averages on train set only
        test_index = int(len(data.dropna())*(1-test_size))
        # data['weekday_average'] = list(map(code_mean(data[:test_index], 'weekday', "y").get, data.weekday))
        data["hour_average"] = list(map(code_mean(data[:test_index], 'hour', "pm25").get, data.hour))
        data["min_average"] = list(map(code_mean(data[:test_index], 'minutes', "pm25").get, data.hour))

        # frop encoded variables
        data.drop(["hour"], axis=1, inplace=True)
        data.drop(["minutes"], axis=1, inplace=True)


      # train-test split
    y = data.dropna().pm25_log
    X = data.dropna().drop(['pm25','pm25_log'], axis=1)
    if timeseries=='timeseries':
      X_train, X_test, y_train, y_test = timeseries_train_test_split(X, y, test_size=test_size)
    elif timeseries=='ml':
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=test_size,random_state=2020)
    else:
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=test_size, shuffle=False)


    return X_train, X_test, y_train, y_test



def code_mean(data, cat_feature, real_feature):
    """
    Returns a dictionary where keys are unique categories of the cat_feature,
    and values are means over real_feature
    """
    return dict(data.groupby(cat_feature)[real_feature].mean())


def plotModelResults(model, X_train, X_test, y_train, y_test, plot_intervals=False, plot_anomalies=False):
	prediction = model.predict(X_test)
	print(y_test.shape)
	fig=plt.figure(figsize=(15, 7))
	plt.plot(prediction, "g", label="prediction", linewidth=2.0)
	plt.plot(y_test.values, label="actual", linewidth=2.0)
	if plot_intervals:
		cv = cross_val_score(model, X_train, y_train,
									cv=tscv,
									scoring="neg_mean_absolute_error")
		mae = cv.mean() * (-1)
		deviation = cv.std()

		scale = 1.96
		lower = prediction - (mae + scale * deviation)
		upper = prediction + (mae + scale * deviation)

		plt.plot(lower, "r--", label="upper bond / lower bond", alpha=0.5)
		plt.plot(upper, "r--", alpha=0.5)

		if plot_anomalies:
			anomalies = np.array([np.NaN]*len(y_test))
			anomalies[y_test<lower] = y_test[y_test<lower]
			anomalies[y_test>upper] = y_test[y_test>upper]
			plt.plot(anomalies, "o", markersize=10, label = "Anomalies")

	error = mean_absolute_percentage_error(prediction, y_test)
	if np.isinf(error):  # If error is infinite, switch to mean squared error
		error = mean_squared_error(prediction, y_test)
		plt.title("Mean squared error: {:.2f}".format(error))
	else:
		plt.title("Mean absolute percentage error: {:.2f}%".format(error))

	plt.legend(loc="best")
	plt.tight_layout()
	plt.grid(True)
	st.pyplot(fig)


def plotCoefficients(model):
	coefs = pd.DataFrame(model.coef_, X_train.columns)
	coefs.columns = ["coef"]
	coefs["abs"] = coefs.coef.apply(np.abs)
	coefs = coefs.sort_values(by="abs", ascending=False).drop(["abs"], axis=1)
	fig=plt.figure(figsize=(15, 7))
	coefs.coef.plot(kind='bar')
	plt.grid(True, axis='y')
	plt.hlines(y=0, xmin=0, xmax=len(coefs), linestyles='dashed')
	st.pyplot(fig)


def plotRegression(y_test, y_pred):

    """
    Plots a regression plot of actual vs predicted values with a regression line.
    """

    fig=plt.figure(figsize=(10, 6))
    plt.scatter(y_test, y_pred, color='blue', label='Actual', alpha=0.3)


    # Plot regression line
    regression_line = np.polyfit(y_test, y_pred, 1)
    plt.plot(y_test, np.polyval(regression_line, y_test), color='green', linewidth=2.0, label='Regression Line')

    plt.title('Regression Plot: Actual vs Predicted PM2.5 Concentration')
    plt.xlabel('Actual PM2.5 Concentration')
    plt.ylabel('Predicted PM2.5 Concentration')
    plt.legend()
    plt.grid(True)
    st.pyplot(fig)


def plot_residual(y_test,y_pred):
	residuals = y_test - y_pred
	fig=plt.figure(figsize=(8, 6))
	plt.scatter(y_pred, residuals, color='blue', alpha=0.2)
	plt.axhline(y=0, color='black', linestyle='--')
	plt.title('Residual Plot f')
	plt.xlabel('Predicted Values')
	plt.ylabel('Residuals')
	st.pyplot(fig)

def plotRegression_result(y_test, y_pred):

    """
    Plots a regression plot of actual vs predicted values with additional visualizations.
    """

    plt.figure(figsize=(18, 10))

    # Scatter Plot
    plt.subplot(2, 3, 1)
    plt.scatter(y_test, y_pred, color='blue', label='Actual', alpha=0.5)
    plt.title('Actual vs Predicted')
    plt.xlabel('Actual PM2.5 Concentration')
    plt.ylabel('Predicted PM2.5 Concentration')
    plt.legend()

    # Plot regression line
    regression_line = np.polyfit(y_test, y_pred, 1)
    plt.plot(y_test, np.polyval(regression_line, y_test), color='green', linewidth=2.0, label='Regression Line')
    plt.legend()

    # Residual Plot
    plt.subplot(2, 3, 2)
    residuals = y_test - y_pred
    plt.scatter(y_pred, residuals, color='red', alpha=0.5)
    plt.axhline(y=0, color='black', linestyle='--')
    plt.title('Residual Plot')
    plt.xlabel('Predicted PM2.5 Concentration')
    plt.ylabel('Residuals')

    # Distribution Plot of Residuals
    plt.subplot(2, 3, 3)
    sns.histplot(residuals, kde=True, color='orange')
    plt.title('Distribution of Residuals')
    plt.xlabel('Residuals')
    plt.ylabel('Frequency')

    # Coefficient of Determination (R^2)
    r_squared = np.corrcoef(y_test, y_pred)[0, 1] ** 2
    plt.text(0.05, 0.95, f'$R^2$ = {r_squared:.3f}', transform=plt.gca().transAxes, fontsize=12, verticalalignment='top')

    # Mean Absolute Error (MAE), Mean Squared Error (MSE), Root Mean Squared Error (RMSE)
    mae = np.mean(np.abs(residuals))
    mse = np.mean(residuals ** 2)
    rmse = np.sqrt(mse)
    plt.text(0.05, 0.85, f'MAE = {mae:.3f}', transform=plt.gca().transAxes, fontsize=12, verticalalignment='top')
    plt.text(0.05, 0.75, f'MSE = {mse:.3f}', transform=plt.gca().transAxes, fontsize=12, verticalalignment='top')
    plt.text(0.05, 0.65, f'RMSE = {rmse:.3f}', transform=plt.gca().transAxes, fontsize=12, verticalalignment='top')

    # Line of Perfect Prediction
    plt.plot(y_test, y_test, color='gray', linestyle='--', label='Perfect Prediction')
    plt.legend()

    # Confidence Intervals for the Regression Line
    plt.subplot(2, 3, 4)
    sns.regplot(x=y_test, y=y_pred, ci=95, scatter_kws={'color': 'blue', 'alpha': 0.5}, line_kws={'color': 'green', 'linewidth': 2})
    plt.title('Regression Plot with Confidence Intervals')
    plt.xlabel('Actual PM2.5 Concentration')
    plt.ylabel('Predicted PM2.5 Concentration')

    # Scatter Density Plot
    plt.subplot(2, 3, 5)
    sns.kdeplot(x=y_test, y=y_pred, cmap='Blues', shade=True, shade_lowest=False)
    plt.title('Scatter Density Plot')
    plt.xlabel('Actual PM2.5 Concentration')
    plt.ylabel('Predicted PM2.5 Concentration')

    plt.tight_layout()
    plt.show()

def plotLSTMResults(model, X_test, y_test, plot_intervals=False, plot_anomalies=False):
	prediction = model.predict(X_test)
	fig=plt.figure(figsize=(15, 7))
	plt.plot(prediction, "g", label="prediction", linewidth=2.0)
	plt.plot(y_test.values, label="actual", linewidth=2.0)
	error = mean_absolute_percentage_error(prediction, y_test)
	plt.title("Mean absolute percentage error {0:.2f}%".format(error))
	plt.legend(loc="best")
	plt.tight_layout()
	plt.grid(True)
	plt.show()
	st.pyplot(fig)




def predict_pm25(model, input_features):
    try:
        prediction = model.predict(input_features)
        prediction_pm25 = np.expm1(prediction)
        return prediction_pm25[0]
    except Exception as e:
        st.error(f"Prediction failed: {str(e)}")
        return None

def predict_single_data_point(model, data_point,X_train, scaler):
    """
    Predict PM2.5 for a single data point, handling missing pm25_rolling_mean.

    Parameters:
    - model: trained model
    - data_point: new data point for prediction (dictionary or pandas series)
    - recent_data: optional, recent data points to calculate rolling mean (DataFrame)
    """
    if isinstance(data_point, dict):
        data_point = pd.Series(data_point)

    pm25_rolling_mean=X_train['pm25_rolling_mean'].mean()
    dp=data_point
    data_point_with_rolling_mean = np.append(dp, pm25_rolling_mean)
    newdp=np.array([data_point_with_rolling_mean])
    newdp_scaled=scaler.transform(newdp)
    test_pred =predict_pm25(model, newdp_scaled)
    return test_pred

# the results by train set and test set are rather different, to see it
def plot_prediction(label=None, prediction=None,title=None, limit=200):
    fig=plt.figure(figsize=(14,6))
    plt.plot(label.to_list(),label='Actual')
    plt.plot(prediction, 'ro',label='Predicted')
    plt.xlim(0, limit)
    plt.title(f'{title} Actual vs Predicted')
    plt.legend()
    st.pyplot(fig)
    return None




# Evaluation function
def evaluate_model(y_true, y_pred):
    mae = mean_absolute_error(y_true, y_pred)
    mse = mean_squared_error(y_true, y_pred)
    r2 = r2_score(y_true, y_pred)
    rmse=np.sqrt(mse)
    return mae, mse, r2,rmse






@st.cache_data
def explore_data(dataset):
	df = pd.read_csv(os.path.join(dataset))
	return df 

def callback():
	st.session_state.button_clicked = True
	st.session_state.checked_box = True



# Function to plot feature importance or coefficients
def plot_feature_importance(model, model_name, feature_names):
    if hasattr(model, 'feature_importances_'):
        # For models that have feature_importances_
        importances = model.feature_importances_
    elif hasattr(model, 'coef_'):
        # For linear models that use coefficients
        importances = np.abs(model.coef_)
    else:
        print(f"{model_name} does not support feature importances or coefficients.")
        return
    
    # Plot the feature importances or coefficients
    fig=plt.figure(figsize=(8, 6))
    sns.barplot(x=importances, y=feature_names)
    plt.title(f'Feature Importance for {model_name}')
    plt.xlabel('Importance')
    plt.ylabel('Features')
    plt.show()
    st.pyplot(fig)


def save_model(model, model_name):
    # Create the models directory if it doesn't exist
    model_dir = os.path.join(os.getcwd(), 'models')
    os.makedirs(model_dir, exist_ok=True)  # Ensure the directory exists

    # Define the full path for the model file
    model_filename = os.path.join(model_dir, f'{model_name}_model.pkl')

    # Save the model using joblib
    joblib.dump(model, model_filename, compress=3)
    print(f"Model saved to: {model_filename}")

@st.cache_resource
def load_app_model(model_path):
    """Loads the model from the specified path with error handling."""
    try:
        return joblib.load(model_path)
    except Exception as e:
        raise RuntimeError(f"Failed to load model: {e}")

# Function to calculate the rolling mean for the prediction
def calculate_rolling_mean(df, window=30):
    df['pm25_rolling_mean'] = df['pm25_log'].rolling(window=window).mean().iloc[-1]
        # # Example: Rolling mean for PM2.5
    df['pm25_rolling_mean'] = df['pm25_log'].rolling(window=30).mean()
    return df['pm25_rolling_mean']










# def show_Analysis():
#     # st.title("CUSTOMER SEGMENTATION SYSTEM")
#     # st.set_option('deprecation.showPyplotGlobalUse', False)
#     # st.title("CUSTOMER SEGMENTATION APP")
    
#     df = Dataset_upload()


#     if df is not None:
#         if "button_clicked" not in st.session_state:
#             st.session_state.button_clicked = False
#         if "checked_box" not in st.session_state:
#             st.session_state.checked_box = False
        
#         st.session_state['page'] = 'train'

#         if st.session_state['page'] == 'train':
#              # EDA
#             st.subheader('Exploratory Data Analysis')
#             st.write("### Data Summary")
#             st.write(df.describe())

#             st.write("### Data Visualisation")
#             data = df.copy(deep=True)

#             # Distribution of dust particle concentrations (PM2.5)
#             fig=plt.figure(figsize=(12, 6))
#             sns.histplot(data=data[['pm25']], bins=20, kde=True)
#             plt.title('Distribution of Dust Particle Concentrations (PM2.5)')
#             plt.xlabel('Concentration (ug/m3)')
#             plt.ylabel('Frequency')
#             plt.legend(['PM25'])
#             plt.show()
#             st.pyplot(fig)

#             # Distribution of dust particle concentrations (PM10)
#             fig=plt.figure(figsize=(12, 6))
#             sns.histplot(data=data[['pm10']], bins=20, kde=True)
#             plt.title('Distribution of Dust Particle Concentrations (PM10)')
#             plt.xlabel('Concentration (ug/m3)')
#             plt.ylabel('Frequency')
#             plt.legend(['PM10'])
#             plt.show()
#             st.pyplot(fig)

#             # Distribution of meteorological variables
#             meteorological_vars = ['temp', 'hum', 'press', 'wspd', 'wdir', 'rain']
#             fig=plt.figure(figsize=(12, 6))
#             for var in meteorological_vars:
#                 sns.histplot(data[var], bins=20, kde=True, alpha=0.5)
#             plt.title('Distribution of Meteorological Variables')
#             plt.xlabel('Value')
#             plt.ylabel('Frequency')
#             plt.legend(meteorological_vars)
#             plt.show()
#             st.pyplot(fig)

#             # Correlation matrix
#             correlation_matrix = data.corr()
#             fig=plt.figure(figsize=(12, 8))
#             sns.heatmap(correlation_matrix, annot=True, cmap='coolwarm', fmt=".2f")
#             plt.title('Correlation Matrix')
#             plt.show()
#             st.pyplot(fig)

#             # # Pairplot for selected variables
#             # figs = plt.figure(figsize=(20, 15))
#             # selected_variables = ['pm25', 'pm10', 'temp', 'press', 'hum', 'wspd', 'rain']
            
#             # sns.pairplot(data[selected_variables], diag_kind='kde',)
#             # plt.suptitle('Pairplot of Selected Variables')
#             # # plt.show()
#             # st.pyplot(figs)

#             # Histograms
#             fig=plt.figure(figsize=(12, 8))
#             plt.subplot(2, 3, 1)
#             sns.histplot(df['pm25'], kde=True, bins=20, color='skyblue')
#             plt.title('PM25 Distribution')

#             plt.subplot(2, 3, 2)
#             sns.histplot(df['pm10'], kde=True, bins=20, color='salmon')
#             plt.title('PM10 Distribution')

#             # KDE plots
#             plt.subplot(2, 3, 3)
#             sns.kdeplot(df['temp'], shade=True, color='orange')
#             plt.title('Temperature Distribution')
            
#             plt.tight_layout()
#             plt.show()
#             st.pyplot(fig)

#             # Box plots
#             fig = plt.figure(figsize=(12, 8))
#             plt.subplot(2, 3, 1)
#             sns.boxplot(y=df['pm25'], color='skyblue')
#             plt.title('PM2.5 Box Plot')

#             plt.subplot(2, 3, 2)
#             sns.boxplot(y=df['pm10'], color='salmon')
#             plt.title('PM10 Box Plot')

#             plt.subplot(2, 3, 3)
#             sns.boxplot(y=df['temp'], color='orange')
#             plt.title('Temperature Box Plot')
            
#             plt.tight_layout()
#             plt.show()
#             st.pyplot(fig)

#             # Handling outliers
#             st.write("***Normalise PM25 into a normal distribution by taking its log function***")
#             sns.histplot(data['pm25'], kde=True, bins=20)

#             # Applying log transformation
#             data['pm25_log'] = np.log1p(data['pm25'])  # log1p is log(1 + x), avoids issues with zero

#             # Transformed histogram and normal probability plot
#             sns.distplot(data['pm25_log'])
#             fig = plt.figure()
#             res = stats.probplot(data['pm25_log'], plot=plt)
#             st.pyplot(fig)
#             st.subheader('Modeling')
#             models = ['Linear Regression', 'XGBoost', 'Random Forest', 'Bagging Regressor', 'Voting']
#             model_choice = st.selectbox("Choose a model", models)
#             data = data.select_dtypes(['int', 'float'])
#             X_train, X_test, y_train, y_test = prepareData(data, test_size=0.2, target_encoding=False, timeseries='ml')
#             X_train_scaled = scaler.fit_transform(X_train)
#             X_test_scaled = scaler.transform(X_test)
#             # # Save the scaler to sessions
#             st.session_state['scaler']=scaler
#             model = None
#             if model_choice == 'Linear Regression':
#                 model = LinearRegression()
#             elif model_choice == 'XGBoost':
#                 model = XGBRegressor()
#             elif model_choice == 'Bagging Regressor':
#                 model = BaggingRegressor(n_estimators=100, random_state=42)
#             elif model_choice == 'Random Forest':
#                 model = RandomForestRegressor()
#             elif model_choice == 'Voting':
#                 rnd_reg = RandomForestRegressor(n_estimators=200, max_depth=10, random_state=42)
#                 bag_reg = BaggingRegressor(n_estimators=200, random_state=42)
#                 xgb_reg = XGBRegressor(n_estimators=200, max_depth=10, learning_rate=0.1, random_state=42)
#                 model = VotingRegressor(
#                     estimators=[('rnd', rnd_reg), ('bag', bag_reg), ('xgb', xgb_reg)],
#                 )

#             trains = st.checkbox('Train model')
#             if trains and model is not None:
#                 model.fit(X_train_scaled, y_train)
#                 train_predictions = model.predict(X_train_scaled)
#                 test_predictions = model.predict(X_test_scaled)

#                 plot_prediction(y_train, train_predictions,title='Training Data:')
#                 test_predictions = model.predict(X_test_scaled)
#                 plot_prediction(y_test, test_predictions,title='Testing Data:')
#                 plotModelResults(model, X_train=X_train_scaled, X_test=X_test_scaled,y_train=y_train,y_test=y_test, plot_intervals=False)
#                 plotRegression(y_test, test_predictions)


#                 mae, mse, r2, rmse = evaluate_model(y_test, test_predictions)
#                 result = {
#                     "mean_absolute_error": f"{mae}",
#                     "mean_squared_error": f"{mse}",
#                     "Root_mean_squared_error": f"{rmse}",
#                     "R2_score": f"{r2}",
#                 }

#                 st.write(result)

#                 # Save the trained model
#                 # model_filename =os.path.join(os.getcwd(),'models',f'{model_choice}_model.pkl')
#                 save_model(model, model_choice)
#                 # Feature importance visualization
#                 feature_names = X_train.columns
#                 if model_choice != 'Voting':
#                     plot_feature_importance(model, model_choice, feature_names=feature_names)
#                 else:
#                     importances = []
#                     for name, est in model.named_estimators_.items():
#                         if hasattr(est, 'feature_importances_'):
#                             importances.append(est.feature_importances_)
#                     average_importance = np.mean(importances, axis=0)

#                     fig = plt.figure(figsize=(8, 6))
#                     sns.barplot(x=average_importance, y=feature_names)
#                     plt.title('Averaged Feature Importance from Voting Regressor')
#                     plt.xlabel('Average Importance')
#                     plt.ylabel('Features')
#                     plt.show()
#                     st.pyplot(fig)



#                 st.success("Model trained successfully and saved.")

#                 st.write("Now you can proceed to the prediction page.")



#                 # Clear model and variables to free up memory
#                 del model, X_train_scaled, X_test_scaled, y_train, y_test, train_predictions, test_predictions
#                 gc.collect()  # Manually trigger garbage collection to free up memory

#                 # # When the user wants to navigate to the prediction page
#                 # if st.button("Go to Prediction Page"):
#                 #     st.session_state['page'] = 'predict'
#                 #     st.rerun()

#                 # # When the user wants to navigate to the prediction page
#                 # if st.button("Go to Prediction Page"):
#                 #     st.session_state['page'] = 'predict'
#                 #     st.experimental_set_query_params(page='predict')  # Set query params to trigger the rerun




#         # else:
#         st.markdown("""
#         <br>
#         <br>
#         <br>
#         <br>
#         <br>
#         <br>
#         <h1 style="color:rgb(8 221 231);"></h1>
#         <p style="color:#f68b28;">Using Machine learning Techniques  for Dust particle control<p>

#         """, unsafe_allow_html=True)




def show_Analysis():
    df = Dataset_upload()
    if df is not None:
        if "button_clicked" not in st.session_state:
            st.session_state.button_clicked = False
        if "checked_box" not in st.session_state:
            st.session_state.checked_box = False
        st.session_state['page'] = 'train'

        if st.session_state['page'] == 'train':
            # EDA
            st.subheader('Exploratory Data Analysis')
            st.write("### Data Summary")
            st.write(df.describe())
            st.write("### Data Visualisation")
            data = df.copy(deep=True)

            # Distribution of dust particle concentrations (PM2.5)
            fig = plt.figure(figsize=(12, 6))
            sns.histplot(data=data[['pm25']], bins=20, kde=True)
            plt.title('Distribution of Dust Particle Concentrations (PM2.5)')
            plt.xlabel('Concentration (ug/m3)')
            plt.ylabel('Frequency')
            plt.legend(['PM25'])
            plt.show()
            st.pyplot(fig)

            # Distribution of dust particle concentrations (PM10)
            fig = plt.figure(figsize=(12, 6))
            sns.histplot(data=data[['pm10']], bins=20, kde=True)
            plt.title('Distribution of Dust Particle Concentrations (PM10)')
            plt.xlabel('Concentration (ug/m3)')
            plt.ylabel('Frequency')
            plt.legend(['PM10'])
            plt.show()
            st.pyplot(fig)

            # Distribution of meteorological variables
            meteorological_vars = ['temp', 'hum', 'press', 'wspd', 'wdir', 'rain']
            fig = plt.figure(figsize=(12, 6))
            for var in meteorological_vars:
                sns.histplot(data[var], bins=20, kde=True, alpha=0.5)
            plt.title('Distribution of Meteorological Variables')
            plt.xlabel('Value')
            plt.ylabel('Frequency')
            plt.legend(meteorological_vars)
            plt.show()
            st.pyplot(fig)

            # Correlation matrix
            correlation_matrix = data.corr()
            fig = plt.figure(figsize=(12, 8))
            sns.heatmap(correlation_matrix, annot=True, cmap='coolwarm', fmt=".2f")
            plt.title('Correlation Matrix')
            plt.show()
            st.pyplot(fig)

            # Histograms
            fig = plt.figure(figsize=(12, 8))
            plt.subplot(2, 3, 1)
            sns.histplot(df['pm25'], kde=True, bins=20, color='skyblue')
            plt.title('PM25 Distribution')
            plt.subplot(2, 3, 2)
            sns.histplot(df['pm10'], kde=True, bins=20, color='salmon')
            plt.title('PM10 Distribution')
            plt.subplot(2, 3, 3)
            sns.kdeplot(df['temp'], shade=True, color='orange')
            plt.title('Temperature Distribution')
            plt.tight_layout()
            plt.show()
            st.pyplot(fig)

            # Box plots
            fig = plt.figure(figsize=(12, 8))
            plt.subplot(2, 3, 1)
            sns.boxplot(y=df['pm25'], color='skyblue')
            plt.title('PM2.5 Box Plot')
            plt.subplot(2, 3, 2)
            sns.boxplot(y=df['pm10'], color='salmon')
            plt.title('PM10 Box Plot')
            plt.subplot(2, 3, 3)
            sns.boxplot(y=df['temp'], color='orange')
            plt.title('Temperature Box Plot')
            plt.tight_layout()
            plt.show()
            st.pyplot(fig)

            # Handling outliers
            st.write("***Normalise PM25 into a normal distribution by taking its log function***")
            sns.histplot(data['pm25'], kde=True, bins=20)
            data['pm25_log'] = np.log1p(data['pm25'])
            sns.distplot(data['pm25_log'])
            fig = plt.figure()
            res = stats.probplot(data['pm25_log'], plot=plt)
            st.pyplot(fig)

            # Modeling section
            st.subheader('Modeling')
            if can_train():
                models = ['Linear Regression', 'XGBoost', 'Random Forest', 'Bagging Regressor', 'Voting']
                model_choice = st.selectbox("Choose a model", models)
                data = data.select_dtypes(['int', 'float'])
                X_train, X_test, y_train, y_test = prepareData(data, test_size=0.2, target_encoding=False, timeseries='ml')
                X_train_scaled = scaler.fit_transform(X_train)
                X_test_scaled = scaler.transform(X_test)
                st.session_state['scaler'] = scaler
                model = None
                if model_choice == 'Linear Regression':
                    model = LinearRegression()
                elif model_choice == 'XGBoost':
                    model = XGBRegressor()
                elif model_choice == 'Bagging Regressor':
                    model = BaggingRegressor(n_estimators=100, random_state=42)
                elif model_choice == 'Random Forest':
                    model = RandomForestRegressor()
                elif model_choice == 'Voting':
                    rnd_reg = RandomForestRegressor(n_estimators=200, max_depth=10, random_state=42)
                    bag_reg = BaggingRegressor(n_estimators=200, random_state=42)
                    xgb_reg = XGBRegressor(n_estimators=200, max_depth=10, learning_rate=0.1, random_state=42)
                    model = VotingRegressor(estimators=[('rnd', rnd_reg), ('bag', bag_reg), ('xgb', xgb_reg)])
                
                trains = st.checkbox('Train model')
                if trains and model is not None:
                    model.fit(X_train_scaled, y_train)
                    train_predictions = model.predict(X_train_scaled)
                    test_predictions = model.predict(X_test_scaled)
                    plot_prediction(y_train, train_predictions, title='Training Data:')
                    test_predictions = model.predict(X_test_scaled)
                    plot_prediction(y_test, test_predictions, title='Testing Data:')
                    plotModelResults(model, X_train=X_train_scaled, X_test=X_test_scaled, y_train=y_train, y_test=y_test, plot_intervals=False)
                    plotRegression(y_test, test_predictions)
                    mae, mse, r2, rmse = evaluate_model(y_test, test_predictions)
                    result = {
                        "mean_absolute_error": f"{mae}",
                        "mean_squared_error": f"{mse}",
                        "Root_mean_squared_error": f"{rmse}",
                        "R2_score": f"{r2}",
                    }
                    st.write(result)
                    save_model(model, model_choice)
                    feature_names = X_train.columns
                    if model_choice != 'Voting':
                        plot_feature_importance(model, model_choice, feature_names=feature_names)
                    else:
                        importances = []
                        for name, est in model.named_estimators_.items():
                            if hasattr(est, 'feature_importances_'):
                                importances.append(est.feature_importances_)
                        average_importance = np.mean(importances, axis=0)
                        fig = plt.figure(figsize=(8, 6))
                        sns.barplot(x=average_importance, y=feature_names)
                        plt.title('Averaged Feature Importance from Voting Regressor')
                        plt.xlabel('Average Importance')
                        plt.ylabel('Features')
                        plt.show()
                        st.pyplot(fig)
                    st.success("Model trained successfully and saved.")
                    st.write("Now you can proceed to the prediction page.")
                    del model, X_train_scaled, X_test_scaled, y_train, y_test, train_predictions, test_predictions
                    gc.collect()
            else:
                st.warning("Model training is disabled on this platform due to limited resources. Please use pre-trained models in the Predict PM2.5 section.")

        st.markdown("""
        <br>
        <br>
        <br>
        <br>
        <br>
        <br>
        <h1 style="color:rgb(8 221 231);"></h1>
        <p style="color:#f68b28;">Using Machine learning Techniques for Dust particle control</p>
        """, unsafe_allow_html=True)











def show_predict():
    st.subheader('Prediction')

    try:
        model_files = [f for f in os.listdir(MODEL_DIR) if f.endswith('.pkl')]
    except FileNotFoundError:
        st.error("Model directory not found.")
        return

    if not model_files:
        st.write("No models available. Please train a model first.")
        return

    selected_model = st.selectbox("Select a saved model", model_files)

    pm10 = st.number_input("PM10")
    temp = st.number_input("Temperature (°C)")
    hum = st.number_input("Humidity (%)")
    press = st.number_input("Pressure (hPa)")
    wspd = st.number_input("Wind Speed (m/s)")
    wdir = st.number_input("Wind Direction (°)")
    rain = st.number_input("Rainfall (mm)")
    hour = st.number_input("Hour", min_value=0, max_value=23, value=12)
    minutes = st.number_input("Minutes", min_value=0, max_value=59, value=30)

    input_data = np.array([pm10, temp, hum, press, wspd, wdir, rain, hour, minutes]).reshape(1, -1)

    if 'uploaded_data' in st.session_state and isinstance(st.session_state['uploaded_data'], pd.DataFrame):
        historical_data = st.session_state['uploaded_data']

        if 'pm25' not in historical_data.columns:
            st.error("'pm25' column missing.")
            return

        historical_data['pm25_log'] = np.log1p(historical_data['pm25'])

        try:
            X_train, _, _, _ = prepareData(historical_data, test_size=0.2, target_encoding=False, timeseries='ml')
        except Exception as e:
            st.error(f"Error in preparing data: {e}")
            return

        model_path = os.path.join(os.getcwd(),'models', selected_model)

        if st.button("Predict"):
            try:
                if not os.path.exists(model_path):
                    st.error(f"Model '{selected_model}' not found.")
                    return

                model = load_app_model(model_path)
                scaler = st.session_state.get('scaler')
                if scaler is None:
                    st.error("Scaler not found. Please upload or re-train.")
                    return

                result = predict_single_data_point(model, input_data, X_train, scaler)
                if result is not None:
                    st.success(f"Predicted PM2.5 level: {result:.2f}")



                # Clear memory after prediction
                del model  # Explicitly delete the model object
                del input_data  # Delete input data if no longer needed
                gc.collect()  # Trigger garbage collection






                if st.button("Go back to Training"):
                    st.session_state['page'] = 'train'
                    st.experimental_rerun()

            except Exception as e:
                st.error(f"Error during prediction: {e}")

    else:
        st.error("No valid DataFrame found. Please upload the data.")