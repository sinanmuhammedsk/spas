import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import r2_score, mean_squared_error, mean_absolute_error
import joblib
import os

# Manual Mappings for Ordinal / Categorical fields
GENDER_MAP = {'Male': 0, 'Female': 1, 'Other': 2}
CLASS_MAP = {'Grade 9': 9, 'Grade 10': 10, 'Grade 11': 11, 'Grade 12': 12, 'University Undergrad': 13}
COACHING_MAP = {'No': 0, 'Yes': 1}
PREP_MAP = {'Low': 0, 'Medium': 1, 'High': 2}
INTERNET_MAP = {'No': 0, 'Yes': 1}
EXTRA_MAP = {'No': 0, 'Yes': 1}
PARENT_MAP = {'High School': 0, 'Bachelor': 1, 'Master': 2, 'PhD': 3}
SUPPORT_MAP = {'Low': 0, 'Medium': 1, 'High': 2}

def generate_synthetic_data(n_samples=1500):
    np.random.seed(42)
    
    # 1. Generate core variables
    age = np.random.randint(14, 23, n_samples)
    gender = np.random.choice(['Male', 'Female', 'Other'], n_samples, p=[0.48, 0.48, 0.04])
    class_name = np.random.choice(['Grade 9', 'Grade 10', 'Grade 11', 'Grade 12', 'University Undergrad'], n_samples)
    
    # Attendance - skewed higher
    attendance = np.random.beta(a=5, b=1.5, size=n_samples) * 100
    
    # Previous Score - normal around 70, sd 12
    prev_score = np.random.normal(70, 12, n_samples)
    prev_score = np.clip(prev_score, 30, 100)
    
    # Study Habits
    study_daily = np.random.uniform(0.5, 8, n_samples)
    self_weekly = study_daily * 3 + np.random.normal(5, 3, n_samples)
    self_weekly = np.clip(self_weekly, 1, 60)
    
    coaching = np.random.choice(['Yes', 'No'], n_samples, p=[0.35, 0.65])
    prep = np.random.choice(['Low', 'Medium', 'High'], n_samples, p=[0.25, 0.50, 0.25])
    
    # Coursework
    assignments = np.round(np.clip(
        (attendance / 100) * 12 + (prev_score / 100) * 3 + np.random.normal(0, 1.5, n_samples),
        0, 15
    )).astype(int)
    
    failed_subjects = np.round(np.clip(
        (100 - prev_score) / 15 + (100 - attendance) / 20 - 1.5 + np.random.normal(0, 0.8, n_samples),
        0, 5
    )).astype(int)
    
    internal_score = np.clip(
        (prev_score / 100) * 20 + (assignments / 15) * 10 + np.random.normal(0, 2, n_samples),
        0, 30
    )
    
    # Environmental factors
    internet = np.random.choice(['Yes', 'No'], n_samples, p=[0.85, 0.15])
    extracurriculars = np.random.choice(['Yes', 'No'], n_samples, p=[0.40, 0.60])
    parent_edu = np.random.choice(['High School', 'Bachelor', 'Master', 'PhD'], n_samples, p=[0.30, 0.45, 0.18, 0.07])
    family_support = np.random.choice(['Low', 'Medium', 'High'], n_samples, p=[0.15, 0.50, 0.35])
    
    # 2. Build final score linear equation with weights
    final_score = (
        0.28 * attendance + 
        0.26 * prev_score + 
        0.85 * assignments + 
        0.45 * internal_score + 
        0.55 * study_daily + 
        0.05 * self_weekly
    )
    
    # Categorical additions
    for i in range(n_samples):
        if prep[i] == 'High': final_score[i] += 4
        elif prep[i] == 'Low': final_score[i] -= 5
        
        if failed_subjects[i] > 0:
            final_score[i] -= (failed_subjects[i] * 4.5)
            
        if parent_edu[i] == 'PhD': final_score[i] += 2.5
        elif parent_edu[i] == 'High School': final_score[i] -= 1.5
        
        if family_support[i] == 'High': final_score[i] += 2
        elif family_support[i] == 'Low': final_score[i] -= 3
        
        if coaching[i] == 'Yes': final_score[i] += 1.5
        if internet[i] == 'No': final_score[i] -= 2
        if extracurriculars[i] == 'Yes': final_score[i] += 1
        
    # Add Gaussian Noise
    final_score += np.random.normal(0, 2.5, n_samples)
    final_score = np.clip(np.round(final_score), 15, 99)
    
    df = pd.DataFrame({
        'Age': age,
        'Gender': gender,
        'Class': class_name,
        'PrevScore': prev_score,
        'Attendance': attendance,
        'Assignments': assignments,
        'FailedSubjects': failed_subjects,
        'InternalScore': internal_score,
        'StudyDaily': study_daily,
        'SelfWeekly': self_weekly,
        'Coaching': coaching,
        'PrepLevel': prep,
        'Internet': internet,
        'Extracurriculars': extracurriculars,
        'ParentEdu': parent_edu,
        'FamilySupport': family_support,
        'FinalScore': final_score
    })
    
    return df

def encode_dataset(df):
    df_encoded = df.copy()
    df_encoded['Gender'] = df_encoded['Gender'].map(GENDER_MAP)
    df_encoded['Class'] = df_encoded['Class'].map(CLASS_MAP)
    df_encoded['Coaching'] = df_encoded['Coaching'].map(COACHING_MAP)
    df_encoded['PrepLevel'] = df_encoded['PrepLevel'].map(PREP_MAP)
    df_encoded['Internet'] = df_encoded['Internet'].map(INTERNET_MAP)
    df_encoded['Extracurriculars'] = df_encoded['Extracurriculars'].map(EXTRA_MAP)
    df_encoded['ParentEdu'] = df_encoded['ParentEdu'].map(PARENT_MAP)
    df_encoded['FamilySupport'] = df_encoded['FamilySupport'].map(SUPPORT_MAP)
    return df_encoded

def main():
    print("Generating synthetic student training dataset...")
    df = generate_synthetic_data(1500)
    df.to_csv('student_dataset.csv', index=False)
    print("Dataset generated and saved to 'student_dataset.csv'")
    
    print("\nEncoding categorical columns...")
    df_encoded = encode_dataset(df)
    
    X = df_encoded.drop(columns=['FinalScore'])
    y = df_encoded['FinalScore']
    
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    
    print(f"Training shapes - Train: {X_train.shape}, Test: {X_test.shape}")
    print("\nTraining RandomForestRegressor...")
    model = RandomForestRegressor(n_estimators=100, max_depth=12, random_state=42)
    model.fit(X_train, y_train)
    
    # Evaluate
    preds = model.predict(X_test)
    r2 = r2_score(y_test, preds)
    mse = mean_squared_error(y_test, preds)
    mae = mean_absolute_error(y_test, preds)
    
    print("\n=== RandomForest Model Evaluation ===")
    print(f"R-squared (R2) score : {r2:.4f}")
    print(f"Mean Squared Error (MSE): {mse:.4f}")
    print(f"Mean Absolute Error (MAE): {mae:.4f}")
    
    # Feature Importances
    importances = model.feature_importances_
    features = X.columns
    importance_df = pd.DataFrame({'Feature': features, 'Importance': importances}).sort_values('Importance', ascending=False)
    print("\n--- Feature Importance Table ---")
    print(importance_df.to_string(index=False))
    
    # Save the model
    print("\nSerializing and saving model estimator...")
    model_data = {
        'model': model,
        'feature_names': list(features),
        'mappings': {
            'Gender': GENDER_MAP,
            'Class': CLASS_MAP,
            'Coaching': COACHING_MAP,
            'PrepLevel': PREP_MAP,
            'Internet': INTERNET_MAP,
            'Extracurriculars': EXTRA_MAP,
            'ParentEdu': PARENT_MAP,
            'FamilySupport': SUPPORT_MAP
        },
        'metrics': {
            'r2': float(r2),
            'mse': float(mse),
            'mae': float(mae)
        },
        'importances': importance_df.to_dict(orient='records')
    }
    
    joblib.dump(model_data, 'model.pkl')
    print("Model packaged and saved as 'model.pkl'. Done.")

if __name__ == '__main__':
    main()
