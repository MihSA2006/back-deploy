from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models

class CustomUserManager(BaseUserManager):
    def create_user(self, email_admin, password=None, **extra_fields):
        if not email_admin:
            raise ValueError("L'email est requis")
        email_admin = self.normalize_email(email_admin)
        user = self.model(email_admin=email_admin, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email_admin, password, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        return self.create_user(email_admin, password, **extra_fields)

class CustomUser(AbstractBaseUser, PermissionsMixin):
    nom_admin = models.CharField(max_length=255)
    prenom_admin = models.CharField(max_length=255)
    pseudo_admin = models.CharField(max_length=150, unique=True)
    email_admin = models.EmailField(unique=True)
    photo_admin = models.ImageField(upload_to='photos/', null=True, blank=True)

    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)

    objects = CustomUserManager()

    USERNAME_FIELD = 'email_admin'
    REQUIRED_FIELDS = ['pseudo_admin', 'nom_admin', 'prenom_admin']

    def __str__(self):
        return self.email_admin
