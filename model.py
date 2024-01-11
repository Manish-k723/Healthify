import joblib
# Make a prediction
model = joblib.load("models\student_predictor.joblib")
print(model.predict([[1, -0.05987475, 1, 1, 1, 1, 0, 1, 0, 0, 0, 0, 1, 0, 0 ,0]]))

