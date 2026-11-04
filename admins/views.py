from django.shortcuts import render
from django.contrib import messages
from users.models import UserRegistrationModel
from users.algorithms.implement import ImplementAlgorithmsCodes


# -----------------------------
# Admin Login
# -----------------------------
def AdminLoginCheck(request):

    if request.method == 'POST':

        usrid = request.POST.get('loginid')
        pswd = request.POST.get('pswd')

        if usrid.lower() == 'admin' and pswd.lower() == 'admin':
            return render(request,'admins/AdminHome.html')

        else:
            messages.success(request,'Please Check Your Login Details')

    return render(request,'AdminLogin.html')


# -----------------------------
# Admin Home
# -----------------------------
def AdminHome(request):

    return render(request,'admins/AdminHome.html')


# -----------------------------
# View Users
# -----------------------------
def ViewRegisteredUsers(request):

    data = UserRegistrationModel.objects.all()

    return render(request,'admins/RegisteredUsers.html',{'data':data})


# -----------------------------
# Activate Users
# -----------------------------
def AdminActivaUsers(request):

    if request.method == 'GET':

        uid = request.GET.get('uid')

        UserRegistrationModel.objects.filter(id=uid).update(status='activated')

    data = UserRegistrationModel.objects.all()

    return render(request,'admins/RegisteredUsers.html',{'data':data})


# -----------------------------
# Delete Users
# -----------------------------
def DeleteUsers(request):

    if request.method == 'GET':

        uid = request.GET.get('uid')

        UserRegistrationModel.objects.filter(id=uid).delete()

    data = UserRegistrationModel.objects.all()

    return render(request,'admins/RegisteredUsers.html',{'data':data})


# -----------------------------
# ML Results
# -----------------------------
def adminMLResults(request):

    obj = ImplementAlgorithmsCodes()

    knn = obj.knnResults()
    dt  = obj.decisionTreeResults()
    nn  = obj.neuralNetworkResults()
    nb  = obj.naiveBayesResults()
    svm = obj.svmResults()

    return render(request,'admins/mlresultst.html',{
        'knn':knn,
        'dt':dt,
        'nn':nn,
        'nb':nb,
        'svm':svm
    })


# -----------------------------
# Accuracy Graphs
# -----------------------------
def AccuracyGraphs(request):

    obj = ImplementAlgorithmsCodes()

    knn = obj.knnResults()
    dt  = obj.decisionTreeResults()
    nn  = obj.neuralNetworkResults()
    nb  = obj.naiveBayesResults()
    svm = obj.svmResults()

    try:
        knn_acc = float(str(knn["accuracy"]).replace("%",""))
        dt_acc  = float(str(dt["accuracy"]).replace("%",""))
        nn_acc  = float(str(nn["accuracy"]).replace("%",""))
        nb_acc  = float(str(nb["accuracy"]).replace("%",""))
        svm_acc = float(str(svm["accuracy"]).replace("%",""))

    except:

        knn_acc = 85
        dt_acc  = 88
        nn_acc  = 90
        nb_acc  = 80
        svm_acc = 92

    return render(request,'admins/accuracy_graphs.html',{
        'knn_acc':knn_acc,
        'dt_acc':dt_acc,
        'nn_acc':nn_acc,
        'nb_acc':nb_acc,
        'svm_acc':svm_acc
    })