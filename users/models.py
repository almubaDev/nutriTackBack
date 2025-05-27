from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.contrib.auth.base_user import BaseUserManager
from django.db import models
from django.utils import timezone


class UserManager(BaseUserManager):
    """Manager personalizado para el modelo User"""
    
    def create_user(self, email, password=None, **extra_fields):
        """Crear y guardar un usuario regular"""
        if not email:
            raise ValueError('El email es obligatorio')
        
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user
    
    def create_superuser(self, email, password=None, **extra_fields):
        """Crear y guardar un superusuario"""
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)
        
        if extra_fields.get('is_staff') is not True:
            raise ValueError('El superusuario debe tener is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('El superusuario debe tener is_superuser=True.')
        
        return self.create_user(email, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):
    """Usuario personalizado que usa email como identificador único"""
    
    email = models.EmailField(
        'Email',
        unique=True,
        error_messages={
            'unique': "Ya existe un usuario con este email.",
        }
    )
    first_name = models.CharField('Nombre', max_length=150, blank=True)
    last_name = models.CharField('Apellido', max_length=150, blank=True)
    
    is_staff = models.BooleanField(
        'Staff',
        default=False,
        help_text='Designa si el usuario puede acceder al admin.'
    )
    is_active = models.BooleanField(
        'Activo',
        default=True,
        help_text='Designa si el usuario debe ser tratado como activo.'
    )
    is_email_verified = models.BooleanField(
        'Email verificado',
        default=False,
        help_text='Designa si el email del usuario ha sido verificado.'
    )
    
    date_joined = models.DateTimeField('Fecha de registro', default=timezone.now)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    objects = UserManager()
    
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []  # Email ya es requerido por USERNAME_FIELD
    
    def __str__(self):
        return self.email
    
    def get_full_name(self):
        """Retorna el nombre completo del usuario"""
        full_name = f'{self.first_name} {self.last_name}'
        return full_name.strip()
    
    def get_short_name(self):
        """Retorna el nombre corto del usuario"""
        return self.first_name
    
    class Meta:
        db_table = 'users_user'
        verbose_name = 'Usuario'
        verbose_name_plural = 'Usuarios'
        indexes = [
            models.Index(fields=['email']),
            models.Index(fields=['created_at']),
        ]