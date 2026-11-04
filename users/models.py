from django.db import models

class UserRegistrationModel(models.Model):
    name = models.CharField(max_length=100)
    loginid = models.CharField(unique=True, max_length=100)
    password = models.CharField(max_length=128) # Increased length
    mobile = models.CharField(unique=True, max_length=15)
    email = models.EmailField(unique=True, max_length=100)
    locality = models.CharField(max_length=100)
    address = models.TextField(max_length=1000)
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=100)
    status = models.CharField(max_length=50, default='waiting')

    def __str__(self):
        return self.loginid

    class Meta:
        db_table = 'UserRegistrations'