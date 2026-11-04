from django.shortcuts import render, redirect
from django.contrib import messages
from .forms import UserRegistrationForm
from .models import UserRegistrationModel
from django.conf import settings
import os   
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, classification_report
import requests

# Gemini REST endpoint (uses requests directly, no google-generativeai package needed)
GEMINI_URL = (
    "https://generativelanguage.googleapis.com/v1beta/models/"
    "gemini-2.0-flash:generateContent"
)


# ---------------- User Registration ----------------
def UserRegisterActions(request):
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            user_obj = form.save(commit=False)
            user_obj.status = "waiting"
            user_obj.save()

            messages.success(request, 'Registration Successful!')
            return redirect('UserRegisterActions')
        else:
            print("Form Errors:", form.errors)
            messages.error(request, 'Registration failed. Please correct the errors.')
    else:
        form = UserRegistrationForm()

    return render(request, 'UserRegistrations.html', {'form': form})


# ---------------- User Login ----------------
def UserLoginCheck(request):
    if request.method == "POST":
        loginid = request.POST.get('loginname')
        pswd = request.POST.get('pswd')
        print("Login ID = ", loginid, ' Password = ', pswd)
        try:
            check = UserRegistrationModel.objects.get(loginid=loginid, password=pswd)
            status = check.status
            print('Status is = ', status)
            if status == "activated":
                request.session['id'] = check.id
                request.session['loggeduser'] = check.name
                request.session['loginid'] = loginid
                request.session['email'] = check.email
                print("User id At", check.id, status)
                return render(request, 'users/UserHome.html', {})
            else:
                messages.success(request, 'Your Account Not activated')
                return render(request, 'UserLogin.html')
        except Exception as e:
            print('Exception is ', str(e))
            pass
        messages.success(request, 'Invalid Login id and password')
    return render(request, 'UserLogin.html', {})


# ---------------- User Home ----------------
def UserHome(request):
    return render(request, 'users/UserHome.html', {})


# ---------------- View Dataset ----------------
def UserViewData(request):
    path = settings.MEDIA_ROOT + "\\" + "dataset.csv"
    df = pd.read_csv(path, nrows=100)
    df = df.to_html(index=False)
    return render(request, 'users/UserViewDataset.html', {'data': df})


# ---------------- Train Model ----------------
def training(request):
    try:
        path = os.path.join(settings.MEDIA_ROOT, 'dataset.csv')
        df = pd.read_csv(path)

        df['RetardSco'] = df['RetardSco'].fillna('0 year')

        X = df.drop('Result', axis=1)
        y = df['Result'].map({'Fail': 0, 'Pass': 1})

        categorical_cols = ['TypeEtab', 'Genre', 'Niveau', 'RetardSco',
                             'Provenance', 'Handicap', 'SocialAid']

        for col in categorical_cols:
            le = LabelEncoder()
            X[col] = le.fit_transform(X[col].astype(str))

        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42
        )

        model = RandomForestClassifier(n_estimators=100, random_state=42)
        model.fit(X_train, y_train)

        y_pred = model.predict(X_test)

        accuracy = round(accuracy_score(y_test, y_pred) * 100, 2)

        report = classification_report(y_test, y_pred, output_dict=True)
        report_df = pd.DataFrame(report).transpose()
        report_html = report_df.to_html(classes='table table-bordered', index=True)

        context = {
            'accuracy': str(accuracy) + " %",
            'report': report_html
        }

        return render(request, "users/training.html", context)

    except Exception as e:
        return render(request, "users/training.html", {'error': str(e)})


# ---------------- Helper: detect weak areas for a student ----------------
def analyze_weak_areas(input_data, df):
    """Compare a student's values against dataset averages to flag weak areas."""
    weak_points = []

    avg_grade = df['Moy'].mean()
    avg_discipline = df['CD_MIL'].mean()

    if input_data['Moy'] < avg_grade:
        gap = round(avg_grade - input_data['Moy'], 1)
        weak_points.append(f"Grade average is {gap} points below the class average ({avg_grade:.1f}).")

    if input_data['CD_MIL'] < avg_discipline:
        weak_points.append("Attendance/discipline score is below average — may indicate irregular attendance.")

    if input_data['RetardSco'] not in ['0 year', None, '']:
        weak_points.append(f"Student is {input_data['RetardSco']} behind the expected school schedule.")

    if input_data['Handicap'] == 'Yes':
        weak_points.append("Student has a disability — may need additional learning accommodations.")

    if input_data['SocialAid'] == 'Yes':
        weak_points.append("Student receives social aid — possible socio-economic stress factors at home.")

    if not weak_points:
        weak_points.append("No major weak areas detected — student profile is close to or above class averages.")

    return weak_points


# ---------------- Helper: call Gemini for improvement suggestions ----------------
def get_improvement_suggestions(weak_points, result, prob):
    try:
        weak_points_text = "\n".join(f"- {point}" for point in weak_points)

        prompt = f"""
        A student was predicted to: {result} (confidence: {prob}%)

        Detected weak areas:
        {weak_points_text}

        Based ONLY on these weak areas, give 3 short, practical, encouraging
        improvement suggestions a teacher could act on this week. Format as a
        numbered list. Keep each suggestion under 20 words. Avoid generic advice
        like "study harder" — be specific to the weak area mentioned.
        """

        payload = {
            "contents": [
                {"parts": [{"text": prompt}]}
            ]
        }

        response = requests.post(
            GEMINI_URL,
            params={"key": settings.GEMINI_API_KEY},
            json=payload,
            timeout=15
        )

        if response.status_code != 200:
            print("Gemini HTTP error:", response.status_code, response.text)
            return "AI suggestions are temporarily unavailable."

        data = response.json()
        text = data["candidates"][0]["content"]["parts"][0]["text"]
        return text

    except Exception as e:
        print("Gemini error:", e)
        return "AI suggestions are temporarily unavailable."


# ---------------- Prediction ----------------
def prediction(request):
    res = None
    prob = 0
    weak_areas = []
    suggestions = ""

    # 1. Load Dataset
    path = os.path.join(settings.MEDIA_ROOT, 'dataset.csv')
    if not os.path.exists(path):
        return render(request, 'users/prediction.html', {'error': 'Dataset not found'})

    df = pd.read_csv(path)
    df['RetardSco'] = df['RetardSco'].fillna('0 year')

    # 2. Setup Encoding
    categorical_cols = ['TypeEtab', 'Genre', 'Niveau', 'RetardSco', 'Provenance', 'Handicap', 'SocialAid']
    X_raw = df.drop('Result', axis=1)
    y_raw = df['Result'].map({'Fail': 0, 'Pass': 1})

    encoders = {}
    X_encoded = X_raw.copy()
    for col in categorical_cols:
        le = LabelEncoder()
        X_encoded[col] = le.fit_transform(X_raw[col].astype(str))
        encoders[col] = le

    # 3. Train Model
    model = RandomForestClassifier(n_estimators=100, random_state=42)
    model.fit(X_encoded, y_raw)

    if request.method == 'POST':
        try:
            # 4. Capture Form Data
            u_input = {
                'TypeEtab': request.POST.get('TypeEtab'),
                'Genre': request.POST.get('Genre'),
                'Niveau': request.POST.get('Niveau'),
                'RetardSco': request.POST.get('RetardSco'),
                'Provenance': request.POST.get('Provenance'),
                'Handicap': request.POST.get('Handicap'),
                'SocialAid': request.POST.get('SocialAid'),
                'CD_MIL': float(request.POST.get('CD_MIL', 0)),
                'Moy': float(request.POST.get('Moy', 0))
            }

            input_df = pd.DataFrame([u_input])[X_raw.columns]

            for col in categorical_cols:
                try:
                    input_df[col] = encoders[col].transform(input_df[col].astype(str))
                except Exception:
                    input_df[col] = 0

            # 5. Predict
            pred_value = model.predict(input_df)[0]
            prob = round(model.predict_proba(input_df)[0][pred_value] * 100, 1)
            res = "PASS" if pred_value == 1 else "FAIL"

            # 6. NEW: weak-area detection + AI-generated suggestions
            weak_areas = analyze_weak_areas(u_input, df)
            suggestions = get_improvement_suggestions(weak_areas, res, prob)

        except Exception as e:
            print(f"Error: {e}")
            res = "ERROR"

    return render(request, 'users/prediction.html', {
        'res': res,
        'prob': prob,
        'weak_areas': weak_areas,
        'suggestions': suggestions
    })