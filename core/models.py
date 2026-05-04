from django.db import models
from django.contrib.auth.models import AbstractUser

# Create your models here.
class CustomUser(AbstractUser):
    city  = models.CharField(max_length=100, blank=True, null=True)
    state  = models.CharField(max_length=100, blank=True, null=True)
    address  = models.TextField(blank=True, null=True)
    phone  = models.CharField(max_length=15, blank=True, null=True)
  
    def __str__(self):
      return self.username
  
  
  # def save(self, *args, **kwargs):
    
  #   if not self.slug:
  #     self.slug = slugify(self.name)
  #     unique_slug = self.slug
  #     counter = 1
  #     if product.objects.filter(slug=unique_slug).exists():
  #       unique_slug = f'{self.slug}-{counter}'
  #       counter += 1
  #     self.slug = unique_slug
  #   super().save(*args, **kwargs)