from django.db import models
from django.conf import settings
from django.db.models.signals import post_save
from django.dispatch import receiver

from datetime import datetime, timezone
from datetime import date




class Account(models.Model):
   email = models.EmailField(max_length=100, unique=True)
   username = models.CharField(max_length=150, unique=True)
   firstName = models.CharField(max_length=30)
   #last_name = models.CharField(max_length=30, blank=True)
   dateJoined = models.DateTimeField()
   isActive = models.BooleanField(default=True)
   zip = models.IntegerField(null=True, blank=True, default=None)
   latitude = models.FloatField(blank=True, null=True)
   longitude = models.FloatField(blank=True, null=True)
   #is_admin = models.BooleanField(default=False)
   #is_staff = models.BooleanField(default=False)
   #is_superuser = models.BooleanField(default=False)    s `
   lastLogin = models.DateTimeField(null=True)
   salt = models.CharField(max_length=100)
   password = models.CharField(max_length=300)
   isVerified = models.BooleanField(default=False, blank=True, null=True)
   forgotPassword = models.BooleanField(default=False, blank=True, null=True)
   zipcode = models.ForeignKey('Zipcodes', on_delete=models.SET_NULL, blank=True, null=True)
   isGold = models.BooleanField(default=False, null=True, blank=True)
   expirationDate = models.DateTimeField(default=None, null=True, blank=True)
   receiptData = models.CharField(max_length=20000, default=None, null=True, blank=True)
   badges = models.IntegerField(null=True, blank=True, default=0)
   registration_id = models.CharField(max_length=200, default=None, blank=True, null=True)


   USERNAME_FIELD = 'username'
   REQUIRED_FIELDS = ['first_name', 'email', 'salt', 'password']

  # objects = AccountManager()

   def __str__(self):
      return self.username

   #def has_perm(self, perm, obj=None):
   #   return self.is_admin

  # def has_module_perms(self, app_label):
  #    return True



class Stores(models.Model):
   chainName = models.CharField(db_column='chainName', max_length=50) # Field name made lowercase.
   address = models.CharField(max_length=200)
   latitude = models.FloatField(blank=True, null=True, default=None)
   longitude = models.FloatField(blank=True, null=True, default=None)
   rating = models.FloatField(blank=True, null=True, default=None)
   storeImage = models.URLField(max_length=600, blank=True, null=True, default=None)
   openingHours =  models.CharField(max_length=100, blank=True, null=True, default=None)
   weekdayText = models.CharField(max_length=400, blank=True, null=True, default=None)
   googlePlaceID = models.CharField(max_length=300, blank=True, null=True, default=None)
   scrapeID = models.BigIntegerField   (null=True, blank=True, default=None)
   scrapeName = models.CharField(max_length=100, null=True, blank=True, default=None)
   zip = models.IntegerField(null=True, blank=True, default=None)
   state = models.CharField(default=None, max_length=10, null=True, blank=True)
   city = models.CharField(max_length=100, default=None, null=True, blank=True)

   def __str__(self):
      return "ID: %s Chain: %s Address: %s Latitude: %s Longitude: %s" % (self.id, self.chainName, self.address, self.latitude, self.longitude)


class Products(models.Model):
   SKU = models.BigIntegerField(db_column='SKU')
   supplyName = models.CharField(max_length=100, db_column='supplyName') # Field name made lowercase.
   store = models.ForeignKey(Stores, on_delete=models.CASCADE)  # Field name made lowercase.
   name = models.CharField(max_length=300, db_column='name')
   quantity = models.CharField(max_length=50, db_column='quantity')
   minQuantity = models.BigIntegerField(db_column='minQuantity')  # Field name made lowercase.
   price = models.FloatField()
   clearance = models.IntegerField(blank=True, null=True, default=None)
   inStock = models.BooleanField(db_column='inStock')  # Field name made lowercase.
   imageLink = models.URLField(db_column='imageLink', blank=True, null=True, default=None)  # Field name made lowercase.

   class Meta:
      ordering = ['-minQuantity', 'price']




class Affiliates(models.Model):
   product = models.ForeignKey(Products, on_delete=models.CASCADE) # Field name made lowercase.
   affiliateStore = models.CharField(db_column='affiliateStore', max_length=60)  # Field name made lowercase.
   affiliatePrice = models.FloatField(db_column='affiliatePrice')  # Field name made lowercase.
   affiliateLink = models.URLField(db_column='affiliateLink')  # Field name made lowercase.



class Notifications(models.Model):
   user = models.ForeignKey(Account, on_delete=models.CASCADE)
   latitude = models.FloatField(blank=True, null=True)
   longitude = models.FloatField(blank=True, null=True)
   radius = models.IntegerField(blank=True, null=True)
   city = models.CharField(max_length=100, blank=True, null=True)
   store = models.ForeignKey(Stores, on_delete=models.CASCADE, blank=True, null=True)
   supplyName = models.CharField(max_length=100, blank=True, null=True)
   product = models.ForeignKey(Products, on_delete=models.CASCADE, blank=True, null=True)
   date = models.CharField(max_length=20, blank=True, null=True)
   dateTime = models.DateTimeField()
   type = models.IntegerField(blank=True, null=True, default=None)

class Submissions(models.Model):
   supplyName = models.CharField(max_length=400, blank=True, null=True)



#+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
# S C R A P I N G    O N L Y
#+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

class UserAgents(models.Model):
   agent = models.CharField(max_length=300)
   browser = models.CharField(max_length=50)


class SKUList(models.Model):
   SKU = models.BigIntegerField(db_column='SKU')
   supplyName = models.CharField(max_length=100) # Field name made lowercase.
   chainName = models.CharField( max_length=50) # Field name made lowercase.
   name = models.CharField(max_length=300)

class Zipcodes(models.Model):
   zip = models.IntegerField(null=False)
   state = models.CharField(default=None, max_length=10)
   population = models.IntegerField(default=None, null=True)
   popRank = models.CharField(max_length=10, default=None, null=True)
   userCount = models.IntegerField(default=None, null=True)
   userRank = models.CharField(max_length=10, default=None, null=True)
   rank = models.IntegerField(default=None, null=True)
   mappedTo = models.IntegerField(default=None)
   searchable = models.BooleanField(default=False)
   city = models.CharField(max_length=100, default=None, null=True)
   county = models.CharField(max_length=100, default=None, null=True)
   latitude = models.FloatField(blank=True, null=True, default=None)
   longitude = models.FloatField(blank=True, null=True, default=None)
   lastScraped = models.DateTimeField(null=True, default=None)
   mappedZipcode = models.ForeignKey('self', on_delete=models.CASCADE, blank=True, null=True)
   isNew = models.BooleanField(default=False, null=True, blank=True)




class ClosedStores(models.Model):
   scrapeID = models.BigIntegerField(null=True, blank=True, default=None)


class ScrapeAnalytics(models.Model):
   description = models.CharField(max_length=200, default=None, null=True)
   seconds = models.FloatField(default=None, null=True)



#@receiver(post_save, sender=settings.AUTH_USER_MODEL)
#def create_auth_token(sender, instance=None, created=False, **kwargs):
  #    if created:
 #        Token.objects.create(user=instance)


