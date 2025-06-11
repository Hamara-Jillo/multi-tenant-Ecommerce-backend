from django.db import models
from django.contrib.auth.models import AbstractUser, Group, Permission, BaseUserManager

class CustomUserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError('The Email field must be set')
        email = self.normalize_email(email)
        
        # Generate unique username from email
        base_username = email.split('@')[0]
        username = base_username
        counter = 1
        while self.model.objects.filter(username=username).exists():
            username = f"{base_username}{counter}"
            counter += 1
            
        user = self.model(email=email, username=username, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_platform_admin', True)
        
        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')
            
        return self.create_user(email, password, **extra_fields)

class User(AbstractUser):
    username = models.CharField(max_length=150, unique=True, null=True)  # Make username nullable
    is_platform_admin = models.BooleanField(default=False)
    email = models.EmailField(unique=True)
    
    objects = CustomUserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []
    ROLES = (
        ('public_admin', 'Public Admin'),
        ('merchant_admin', 'Merchant Admin'),
        ('store_manager', 'Store Manager'),
        ('store_customer', 'Store Customer'),
    )
    role = models.CharField(max_length=20, choices=ROLES, default='store_customer')

    schema_name = models.CharField(
        max_length=63,
        blank=True,
        null=True,
        help_text="Tenant schema this user belongs to"
    )

    store = models.ForeignKey(
        'store_meta.Store',
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )

    groups = models.ManyToManyField(
        Group,
        related_name='multistore_users',  # Unique name
        blank=True,
        help_text='The groups this user belongs to...',
        verbose_name='groups'
    )
    user_permissions = models.ManyToManyField(
        Permission,
        related_name='multistore_users_permissions',  # Unique name
        blank=True,
        help_text='Specific permissions for this user...',
        verbose_name='user permissions'
    )
    def __str__(self):
        return self.email
    
    # class Meta:
    #     proxy = True