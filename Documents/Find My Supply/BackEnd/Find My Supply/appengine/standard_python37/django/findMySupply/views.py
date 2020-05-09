from .models import *
from django.http import HttpResponse
from django.db.models import F
from push_notifications.models import APNSDevice
from math import cos, asin, sqrt, pi
from geopy import distance
from rest_framework.decorators import api_view
from rest_framework.authtoken.models import Token
import os
from datetime import datetime, timezone, timedelta
from django.db.models import Sum
from findMySupply.Emails.emails import sendVerificationEmail, sendResetPasswordEmail
from django.views.decorators.csrf import csrf_exempt
import random
import json
import urllib.request
import requests


def findLatitudeBound(radius, isMiles):
    if isMiles:
        return 1/(68.92/radius)
    else:
        return 1/(110.91599/radius)

def findLongitudeBound(latitude, radius, isMiles):
    if isMiles:
        return 1/((cos(latitude*(pi/180)) * 69.172)/radius)
    else:
        return 1/((cos(latitude * (pi / 180)) * 111.321543)/radius)

def findDistanceBewteen(lat1, lon1, lat2, lon2, isMiles):
    p = pi/180
    a = 0.5 - cos((lat2-lat1)*p)/2 + cos(lat1*p) * cos(lat2*p) * (1-cos((lon2-lon1)*p))/2
    return (7917.5226 if isMiles else 12742.0176) * asin(sqrt(a))


def find_lat_lon_Bound(latitude, radius, isMiles):
    return findLatitudeBound(radius, isMiles), findLongitudeBound(latitude, radius, isMiles)



#-----------------------------------------
# FEATURE: onload supply menu options
# Selects all supplies currently supported
#-----------------------------------------
def getSupplyOptions(request, token):
    if not Account.objects.filter(salt=token):
        return HttpResponse("Invalid Token!")
    supplies = []
    for supply in Products.objects.order_by('supplyName').values('supplyName').distinct():
        supplies.append(supply)

    return HttpResponse(json.dumps(supplies))

#--------------------------------------------------------------
# FEATURE: onclick find (supply=toilet paper) in X mile radius
# Selects all stores that carry (supply) in bewteen lat and lon
#--------------------------------------------------------------
def getStoresWithSupply(request, supply, radius, metric, latitude, longitude, token):
    if not Account.objects.filter(salt=token):
        return HttpResponse("Invalid Token!")
    #list of dictionaries being rows
    supply, latitude, longitude, stores = supply.replace("_", " "), float(latitude), float(longitude), []


    latBound, lonBound = find_lat_lon_Bound(latitude, radius, metric == "mi")



    print(f"+++LATITUDE BEWTEEN: {latitude-latBound}-{latitude+latBound}     LONGITUDE BEWTEEN: {longitude-lonBound}- {longitude+lonBound}")
    for store in Products.objects.filter( store__latitude__range=(latitude-latBound,latitude+latBound), store__longitude__range=(longitude-lonBound, longitude+lonBound), supplyName=supply, inStock=True).order_by("store__id").values("store__id").distinct().values("store__id", "store__address",  "store__chainName", "store__latitude", "store__longitude", "store__rating", "store__storeImage", "store__weekdayText", "store__openingHours", "store__googlePlaceID"):
        if distance.distance((store["store__latitude"], store["store__longitude"]), (latitude, longitude)).miles > radius:
            continue

        store["store__openingHours"] = list(store["store__openingHours"].split("/"))
        store["store__weekdayText"] = list(store["store__weekdayText"].split("/"))
        for i in range(0,7):
            store["store__weekdayText"][i] = store["store__weekdayText"][i][store["store__weekdayText"][i].find(":") + 2:]

        stores.append(store)


    return HttpResponse(json.dumps(stores))









#------------------------------------------------------------------------------------
# FEATURE: onclick (storeID=7) location with (supply=toilet paper) in stock, displays items
# Selects all (supply) items info in (storeID) ordered by quantity
#------------------------------------------------------------------------------------
def getProductsInStore(request, supply, storeID, token):
    if not Account.objects.filter(salt=token):
        return HttpResponse("Invalid Token!")
    supply = supply.replace("_", " ")
    products = []

    for product in Products.objects.filter(supplyName=supply, store__id=storeID).values("SKU", "name", "quantity", "minQuantity", "price", 'clearance', 'inStock', 'imageLink', 'affiliates__affiliateStore', 'affiliates__affiliatePrice', 'affiliates__affiliateLink'):
        products.append(product)

    return HttpResponse(json.dumps(products))



#--------------------------------------------------------------------------------------------
# FEATURE: nearby stores feature, displays stores at X radius that have (SKU=555555) in stock
# Selects all stores except (storeID=3) in X radius that have item (SKU) in stock
#--------------------------------------------------------------------------------------------
def getNearbyStores(request, sku, radius, metric, latitude, longitude, storeID, token):
    if not Account.objects.filter(salt=token):
        return HttpResponse("Invalid Token!")
    latitude, longitude = float(latitude), float(longitude)
    stores = []

    isMiles = metric == "mi"
    latBound, lonBound = find_lat_lon_Bound(latitude, radius, isMiles)

    for store in sorted(Products.objects.filter( store__latitude__range=(latitude-latBound,latitude+latBound), store__longitude__range=(longitude-lonBound, longitude+lonBound), SKU=sku, inStock=True).exclude(store__id=storeID).values("store__id", 'store__chainName', 'store__address', "store__latitude", "store__longitude", "store__city", "price", "quantity", 'minQuantity', 'clearance', "store__rating", "store__storeImage", "store__weekdayText", "store__openingHours", "store__googlePlaceID"), key=lambda x: distance.distance((x['store__latitude'],x['store__longitude']) , (latitude, longitude) ).miles if isMiles else distance.distance((x['store__latitude'],x['store__longitude']) , (latitude, longitude) ).kilometers):
        store["store__openingHours"] = list(store["store__openingHours"].split("/"))
        store["store__weekdayText"] = list(store["store__weekdayText"].split("/"))
        for i in range(0,7):
            store["store__weekdayText"][i] = store["store__weekdayText"][i][store["store__weekdayText"][i].find(":") + 2:]
        stores.append(store)

    return HttpResponse(json.dumps(stores))



#-----------------------------------------------------------------------------------
# FEATURE: (SKU=555555) in X radius finally in stock notification if query not null
# Selects all stores in X radius that have item (SKU) in stock
#-----------------------------------------------------------------------------------
def getStoresWithSKU(request, sku, radius, metric, latitude, longitude, token):
    if not Account.objects.filter(salt=token):
        return HttpResponse("Invalid Token!")
    latitude, longitude = float(latitude), float(longitude)
    stores = []
    isMiles = metric == "mi"
    latBound, lonBound = find_lat_lon_Bound(latitude, radius, isMiles)

    for store in sorted(Products.objects.filter(store__latitude__range=(latitude-latBound,latitude+latBound), store__longitude__range=(longitude-lonBound, longitude+lonBound), SKU=sku, inStock=True).values("store__id",'store__chain__chainName','store__address',"store__latitude","store__longitude","store__chain__chainImgLink",'name', 'price', "quantity",'minQuantity','clearance', 'imageLink', 'affiliates__affiliateStore', 'affiliates__affiliatePrice', 'affiliates__affiliateLink'),key=lambda x: distance.distance((x['store__latitude'],x['store__longitude']) , (latitude, longitude) ).miles if isMiles else distance.distance((x['store__latitude'],x['store__longitude']) , (latitude, longitude) ).miles):
        stores.append(store)

    return HttpResponse(json.dumps(stores))




#-------------------------------------------------------------------------------------------
# FEATURE: item (SKU=5555555) in (storeID=5) finally in stock notification if query not null
# Selects (storeID) that has (SKU) in stock
#-------------------------------------------------------------------------------------------
def getStoreWithSKU(request, sku, storeID, token):
    if not Account.objects.filter(salt=token):
        return HttpResponse("Invalid Token!")

    store = Products.objects.filter(SKU=sku, store__id=storeID, inStock=True).values("store__id",'store__chain__chainName','store__address',"store__latitude","store__longitude","store__chain__chainImgLink",'name', 'price', "quantity",'minQuantity','clearance', 'imageLink', 'affiliates__affiliateStore', 'affiliates__affiliatePrice', 'affiliates__affiliateLink')
    return HttpResponse( json.dumps(store[0] if store.count() else []))


#----------------------------------------------------------------------------------------------
# FEATURE: (supply=toilet paper) in X radius finally in stock notification if query not null
# Selects all stores that carry (supply) in X radius
#----------------------------------------------------------------------------------------------
def getStoresWithSupply_Notif(request, supply, radius, metric, latitude, longitude, token):
    if not Account.objects.filter(salt=token):
        return HttpResponse("Invalid Token!")
    supply, latitude, longitude, stores = supply.replace("_", " "), float(latitude), float(longitude), []

    latBound, lonBound = find_lat_lon_Bound(latitude, radius, metric == "mi")
    for store in sorted(Products.objects.filter(store__latitude__range=(latitude-latBound,latitude+latBound), store__longitude__range=(longitude-lonBound, longitude+lonBound), supplyName=supply, inStock=True).values("store__id",'store__chain__chainName','store__address',"store__latitude","store__longitude","store__chain__chainImgLink",'name', 'price', "quantity",'minQuantity','clearance', 'imageLink', 'affiliates__affiliateStore', 'affiliates__affiliatePrice', 'affiliates__affiliateLink'), key=lambda x: distance.distance((x['store__latitude'],x['store__longitude']) , (latitude, longitude) ).miles if metric=="mi" else distance.distance((x['store__latitude'],x['store__longitude']) , (latitude, longitude) ).miles):
        stores.append(store)

    return HttpResponse(json.dumps(stores))



#----------------------------------------------------------------------------------------------
# FEATURE: (supply=toilet paper) in (storeID = 6) finally in stock notification
# Selects (storeID) that carries (supply)
#----------------------------------------------------------------------------------------------
def getStoreWithSupply(request, supply, storeID, token):
    if not Account.objects.filter(salt=token):
        return HttpResponse("Invalid Token!")
    store = Products.objects.filter(supplyName=supply.replace("_", " "), store__id=storeID, inStock=True).values("store__id",'store__chain__chainName','store__address',"store__latitude","store__longitude","store__chain__chainImgLink",'name', 'price', "quantity",'minQuantity','clearance', 'imageLink', 'affiliates__affiliateStore', 'affiliates__affiliatePrice', 'affiliates__affiliateLink')
    return HttpResponse( json.dumps(store[0] if store.count() else []))


#-------------------------------------------------------------------------------
# FEATURE: Register new user given (first name), (email), (username), (password)
# Pushes new user
#-------------------------------------------------------------------------------
@api_view(['POST',])
def registerUser(request, fname, email,  username, salt, psw, zip):

    user1 = Account.objects.filter(email=email)
    if user1:
        if user1[0].isVerified:
            return HttpResponse(json.dumps({"message": "#User with email: %s, already exists." % email}))
        return HttpResponse(json.dumps({"message": "#Verify your email to login."}))
    if Account.objects.filter(username=username):
        return HttpResponse(json.dumps({"message": "#User with username: %s, already exists." % username}))


    zipcode = Zipcodes.objects.filter(zip=zip)

    if not zipcode:
        return HttpResponse(json.dumps({"message": "#ZIP code is invalid."}))

    user = Account(firstName=fname, email=email, username=username, password=psw, salt=salt, zip=zip, zipcode=zipcode[0], dateJoined = datetime.now(timezone.utc), lastLogin=datetime.now(timezone.utc))
    user.save()

    isNew = False

    searchableZip = zipcode[0].mappedZipcode
    searchableZip.userCount = F('userCount') + 1

    if searchableZip.rank == 4 or searchableZip.rank == 0:
        isNew = True
        if searchableZip.rank == 4:
            searchableZip.isNew = True
            searchableZip.rank = 0

    searchableZip.save(update_fields=['rank', 'userCount', 'isNew'])


    try:
        sendVerificationEmail(user, salt)
    except:
        user.delete()
        return HttpResponse(json.dumps({"message": "#Email address is invalid."}))



    prefix = 'T' if isNew else 'F'

    return HttpResponse(json.dumps({"message": str(prefix)+str(user.id)}))


#------------------------------------------------
# FEATURE: Delete user given (userID) and (token)
# Deletes user
#------------------------------------------------
@api_view(['POST',])
def deleteUser(request, username, token):
    if not Account.objects.filter(salt=token, username=username):
        return HttpResponse("Invalid Token!")
    u = Account.objects.filter(username=username)
    u.delete()

    return HttpResponse(json.dumps({"message": "User %s deleted." % username}))

#------------------------------------------------------------
# FEATURE: Logs in given (email) or (username) and (password)
# Logs existing user in
#------------------------------------------------------------
@api_view(['POST', ])
def loginUser(request, login, psw, lat, lon, token):
    if not Account.objects.filter(salt=token):
        return HttpResponse("Invalid Token!")

    user1 = Account.objects.filter(email=login)
    user2 =  Account.objects.filter(username=login)
    if not(user1 or user2):
        return HttpResponse(json.dumps({"message": "#Username or email not found."}))


    if user1:
        user1 = user1[0]
        if user1.password == psw:
            user1.lastLogin = datetime.now(timezone.utc)
            if not lat == '0.0':
                user1.latitude = float(lat)
                user1.longitude = float(lon)
                user1.save(update_fields=['lastLogin', 'latitude', 'longitude'])

            user1.badges = 0
            isGold = updateUserGoldStatus(user1) if user1.isGold else False
            user1.save(update_fields=['lastLogin', 'badges'])

            return HttpResponse(json.dumps({"message": "T" if isGold else "F"}))
    else:
        user2 = user2[0]
        if user2.password == psw:
            user2.lastLogin = datetime.now(timezone.utc)
            if not lat == '0.0':
                user2.latitude = float(lat)
                user2.longitude = float(lon)
                user2.save(update_fields=['lastLogin', 'latitude', 'longitude'])

            user2.badges = 0
            isGold = updateUserGoldStatus(user2) if user2.isGold else False
            user2.save(update_fields=['lastLogin', 'badges'])

            return HttpResponse(json.dumps({"message": "T" if isGold else "F"}))

    return HttpResponse(json.dumps({"message": "#Incorrect password."}))



def updateUserGoldStatus(user):
    #Case subscription is expired
    #CHANGE SECONDS TO DAYS
    if (user.expirationDate - datetime.now(timezone.utc)).days < 0:
        payload = {
            'receipt-data': user.receiptData,
            'exclude-old-transactions': True,
            'password': SHAREDSECRET
        }

        # Production
        # https://buy.itunes.apple.com/verifyReceipt
        response = requests.post('https://sandbox.itunes.apple.com/verifyReceipt', json=payload)

        if response.status_code != 200:
            #Benefit of the doubt
            return True

        responseObj = response.json()
        print(json.dumps(responseObj, indent=4, sort_keys=True))


        try:
            print(f"status: {responseObj['status']}")
            print(f"bundle: {responseObj['receipt']['bundle_id']}")
            print(f"productID: {responseObj['latest_receipt_info'][0]['product_id']}")

            if (responseObj["status"] != 0) or (responseObj["receipt"]["bundle_id"] != "cpp.Find-My-Supply") or (responseObj["latest_receipt_info"][0]["product_id"] not in SUBSCRIPTIONS):
                print("INVALID receipt")
                return False

            expirationDate = datetime.strptime(responseObj['latest_receipt_info'][0]['expires_date'][:-8], '%Y-%m-%d %H:%M:%S').replace(tzinfo=timezone.utc)
            print(f"Latest Expiration Date:  {expirationDate}")

            print(f"Time delta: {(expirationDate - datetime.now(timezone.utc)).days}")

            #Check if most-recent expiration date is valid
            #Case that it is still expired
            if (expirationDate - datetime.now(timezone.utc)).days < 0:
                print("Expired")
                user.isGold = False
                user.save(update_fields=['isGold'])

                if user.registration_id:
                    device = APNSDevice.objects.filter(user_id=user.id)
                    if device.exists():
                        device[0].active = False
                        device[0].save(update_fields=['active'])
                return False
            else:
                print("Renewed!")
                user.expirationDate = expirationDate + timedelta(days=GRACE)
                user.isGold = True
                user.receiptData = responseObj['latest_receipt']
                user.save(update_fields=['isGold', 'expirationDate', 'receiptData'])

                device = APNSDevice.objects.filter(user_id=user.id)
                if device.exists():
                    device[0].active = True
                    device[0].save(update_fields=['active'])
                return True
        except:
            print("EXCEPTION THROWN")
            return False
    else:
        return True

#----------------------------------
# FEATURE: When registering account
# Returns random salt
#---------------------------------
def getSalt(response):
    return HttpResponse(json.dumps({"salt": os.urandom(32).hex()}))

#------------------------------------------
# FEATURE: When logging a user in
# Returns users info to update UserDefualts
#------------------------------------------
def getUserInfo(response, login):
    user1 = Account.objects.filter(email=login)
    user2 =  Account.objects.filter(username=login)
    if not(user1 or user2):
        return HttpResponse(json.dumps({
            "message": "#Username or email not found.",
            "ID": 0,
            "fName": '',
            "email": '',
            "username": '',
            "salt": '',
            "password": '',
            "identifiedByEmail": False,
            "zip": 0,
            "isGold": False


        }))

    if user1:
        user1 = user1[0]
        return HttpResponse(json.dumps({
            "message": "T" if user1.isVerified else "F",
            "ID": user1.id,
            "fName": user1.firstName,
            "email": user1.email,
            "username": user1.username,
            "salt": user1.salt,
            "password": user1.password,
            "identifiedByEmail": True,
            "zip": user1.zip,
            "isGold": updateUserGoldStatus(user1) if user1.isGold else False


        }))
    else:
        user2 = user2[0]
        return HttpResponse(json.dumps({
            "message": "T" if user2.isVerified else "F",
            "ID": user2.id,
            "fName": user2.firstName,
            "email": user2.email,
            "username": user2.username,
            "salt": user2.salt,
            "password": user2.password,
            "identifiedByEmail": False,
            "zip": user2.zip,
            "isGold": updateUserGoldStatus(user2) if user2.isGold else False


        }))




#-------------------------------------------------------
# FEATURE: Displays total quantity of product at a store
# Returns int
#-------------------------------------------------------
def getTotalQuantity(response, supply, storeID, token):
    if not Account.objects.filter(salt=token):
        return HttpResponse("Invalid Token!")

    sum = Products.objects.filter(store_id=storeID, minQuantity__gte=0, supplyName=supply.replace("_", " ")).aggregate(Sum('minQuantity'))
    return HttpResponse(json.dumps({"totalQuantity": sum["minQuantity__sum"]}))




#----------------------------------------------------------
# FEATURE: Updates Account table
# isActive = False if user has not logged in within 7 days
#----------------------------------------------------------
def setActiveUsers():
    now = datetime.now(timezone.utc)
    for user in Account.objects.all():
        if (now- user.lastLogin).days > 7:
            user.isActive = False
        else:
            user.isActive = True
        user.save()

#----------------------------
# FEATURE: Adds notification
# Creates new db row for user
#----------------------------
@api_view(['POST', ])
def addSKUStoreNotification(request, usernm, sku, storeID, date, token):
    if not Account.objects.filter(salt=token):
        return HttpResponse("Invalid Token!")

    user = Account.objects.filter(username=usernm)[0]
    store = Stores.objects.filter(id=storeID)[0]

    product = Products.objects.filter(SKU=sku, store_id=store.id)[0]

    if Notifications.objects.filter(user=user, store=store, product__SKU=sku).count() == 0:
        newNotif = Notifications(user=user, store=store, type=3, product=product, date=date, dateTime=datetime.now(timezone.utc))
        newNotif.save()
        return HttpResponse(json.dumps({"message": "Successfully added notification"}))

    return HttpResponse(json.dumps({"message": "#Notification already exists."}))


#----------------------------
# FEATURE: Adds notification
# Creates new db row for user
#----------------------------
@api_view(['POST', ])
def addSKURegionNotification(request, usernm, sku, radius, metric, city, latitude, longitude, date, token):
    if not Account.objects.filter(salt=token):
        return HttpResponse("Invalid Token!")

    user = Account.objects.filter(username=usernm)[0]

    latitude, longitude = float(latitude), float(longitude)

    latBound, lonBound = find_lat_lon_Bound(latitude, 1, metric == "mi")

    product = Products.objects.filter(SKU=sku)[0]

    city = city.replace("_", " ")

    if Notifications.objects.filter(user=user, radius=radius, product__SKU=sku, latitude__range=(latitude-latBound, latitude+latBound), longitude__range=(longitude-lonBound, longitude+lonBound)).count() == 0:
        newNotif = Notifications(user=user,  product=product, radius=radius, type=2, latitude=latitude, longitude=longitude, city=city, date=date, dateTime=datetime.now(timezone.utc))
        newNotif.save()
        return HttpResponse(json.dumps({"message": "Successfully added notification"}))

    return HttpResponse(json.dumps({"message": "#Notification already exists."}))

#----------------------------
# FEATURE: Adds notification
# Creates new db row for user
#----------------------------
@api_view(['POST', ])
def addSupplyRegionNotification(request, usernm, supply, radius,  metric, city, latitude, longitude, date, token):
    if not Account.objects.filter(salt=token):
        return HttpResponse("Invalid Token!")

    user = Account.objects.filter(username=usernm)[0]

    latitude, longitude = float(latitude), float(longitude)

    latBound, lonBound = find_lat_lon_Bound(latitude, 1, metric == "mi")

    supply, city = supply.replace("_", " "), city.replace("_", " ")

    if Notifications.objects.filter(user=user, radius=radius, supplyName=supply, latitude__range=(latitude-latBound, latitude+latBound), longitude__range=(longitude-lonBound, longitude+lonBound)).count() == 0:
        newNotif = Notifications(user=user,  supplyName=supply, radius=radius, type=1, latitude=latitude, longitude=longitude, city=city, date=date, dateTime=datetime.now(timezone.utc))
        newNotif.save()
        return HttpResponse(json.dumps({"message": "Successfully added notification"}))

    return HttpResponse(json.dumps({"message": "#Notification already exists."}))


#----------------------------
# FEATURE: Update user info
# Updates user profile
#----------------------------
@api_view(['POST', ])
def updateUserProfile(request, oldUsername, fName, usrname, email, token):
    if not Account.objects.filter(salt=token):
        return HttpResponse("Invalid Token!")

    if not fName == "_":
        user = Account.objects.filter(username=oldUsername)[0]
        user.firstName = fName
        user.save()

    if not usrname == "_":
        if Account.objects.filter(username=usrname):
            return HttpResponse(json.dumps({"message": "#Username already exists."}))
        user = Account.objects.filter(username=oldUsername)[0]
        user.username = usrname
        user.save()

    if not email == "_":
        if Account.objects.filter(email=email):
            return HttpResponse(json.dumps({"message": "#Email already exists."}))
        user = Account.objects.filter(username=oldUsername)[0]
        user.email = email
        user.save()


    return HttpResponse(json.dumps({"message": "Successfully updated user profile."}))

#------------------------------
# FEATURE: Update user password
# Updates user profile
#----------------------------
@api_view(['POST', ])
def changePassword(request, login, salt, newPsw, type):
    user1 = Account.objects.filter(email=login)
    user2 =  Account.objects.filter(username=login)


    if user1:
        user1 = user1[0]
        if type == "forgot":
            user1.salt = salt
        user1.password = newPsw
        user1.forgotPassword = False
        user1.save(update_fields=['salt', 'password', 'forgotPassword'])

    if user2:
        user2 = user2[0]
        if type == "forgot":
            user2.salt = salt
        user2.password = newPsw
        user2.forgotPassword = False
        user2.save(update_fields=['salt', 'password', 'forgotPassword'])

    return HttpResponse(json.dumps({"message": "Successfully changed password."}))


#---------------------------------
# FEATURE: View user notifications
# Returns all user notifications
#---------------------------------
def getAreaNotifications(request, username, token):
    if not Account.objects.filter(salt=token):
        return HttpResponse("Invalid Token!")


    notifs = []

    now = datetime.now(timezone.utc)
    user = Account.objects.filter(username=username)[0]
    for notif in sorted(Notifications.objects.filter(user=user, store=None).values("radius", "city", "store__id", "store__chainName", "store__address", "supplyName", "product__id", "product__name", "product__imageLink", "date", "dateTime"), key=lambda x: now - x["dateTime"]):
        del notif["dateTime"]
        notifs.append(notif)

    return HttpResponse(json.dumps(notifs))

#---------------------------------
# FEATURE: View user notifications
# Returns all user notifications
#---------------------------------
def getStoreNotifications(request, username, token):
    if not Account.objects.filter(salt=token):
        return HttpResponse("Invalid Token!")


    notifs = []

    now = datetime.now(timezone.utc)
    user = Account.objects.filter(username=username)[0]
    for notif in sorted(Notifications.objects.filter(user=user, radius=None).values("radius", "city", "store__id", "store__chainName", "store__address", "supplyName", "product__id", "product__name", "product__imageLink", "date", "dateTime"), key=lambda x: now - x["dateTime"]):
        del notif["dateTime"]
        notifs.append(notif)

    return HttpResponse(json.dumps(notifs))



#------------------------------------------
# FEATURE: Delete SupplyRegion Notification
# Deletes user notification
#-------------------------------------------
@api_view(['POST', ])
def deleteSupplyRegionNotification(request, username, supply, radius, city, date, token):
    if not Account.objects.filter(salt=token):
        return HttpResponse("Invalid Token!")

    supply = supply.replace("_", " ")
    city = city.replace("_", " ")
    notif = Notifications.objects.filter(user__username=username, supplyName=supply, radius=radius, city=city, date=date)[0]
    notif.delete()

    return HttpResponse("Success")

#------------------------------------------
# FEATURE: Delete SKUStore Notification
# Deletes user notification
#-----------------------------------------
@api_view(['POST', ])
def deleteSKUStoreNotification(request, username, productID, storeID, date, token):
    if not Account.objects.filter(salt=token):
        return HttpResponse("Invalid Token!")

    notif = Notifications.objects.filter(user__username=username, product__id=productID, store__id=storeID, date=date)[0]
    notif.delete()

    return HttpResponse("Success")

#------------------------------------------
# FEATURE: Delete SKURegion Notification
# Deletes user notification
#-----------------------------------------
@api_view(['POST', ])
def deleteSKURegionNotification(request, username, productID, radius, city, date, token):
    if not Account.objects.filter(salt=token):
        return HttpResponse("Invalid Token!")

    city = city.replace("_", " ")
    notif = Notifications.objects.filter(user__username=username, product__id=productID, radius=radius, city=city, date=date)[0]
    notif.delete()

    return HttpResponse("Success")

#------------------------------------------
# FEATURE: Users can add supply suggestions
# adds suggestion to DB
#-----------------------------------------
@api_view(['POST', ])
def addSubmission(request, supply, token):
    if not Account.objects.filter(salt=token):
        return HttpResponse("Invalid Token!")

    submission = Submissions(supplyName=supply)
    submission.save()

    return HttpResponse("Success")



#--------------------------
# FEATURE: Updates user zip
# Adds new zip to user row
#--------------------------
@api_view(['POST', ])
def updateUserZip(request, username, zip, token):
    if not Account.objects.filter(salt=token):
        return HttpResponse("Invalid Token!")


    #Might fail because zipcode may not exist in the DB
    try:
        user = Account.objects.filter(username=username)[0]

        oldZip = Zipcodes.objects.filter(zip=user.zip)[0].mappedZipcode
        oldZip.userCount = F('userCount') - 1


        newZip = Zipcodes.objects.filter(zip=zip)[0].mappedZipcode
        newZip.userCount = F('userCount') + 1

        isNew = False
        if newZip.rank == 4 or newZip.rank == 0:
            isNew = True


        oldZip.save(update_fields=['userCount'])
        newZip.save(update_fields=['userCount'])

        user.zip = zip
        user.zipcode = newZip
        user.save(update_fields=['zip', 'zipcode'])
    except:
        return HttpResponse(json.dumps({"message": "#"}))




    return HttpResponse(json.dumps({"message": "T" if isNew else "F"}))


def sendVerifEmail(request, userID, token):
    user = Account.objects.filter(id=userID)[0]
    sendVerificationEmail(user, token)

    return HttpResponse("Success")



def verifyUser(request, userID, token):
    if not Account.objects.filter(salt=token, id=userID):
        return HttpResponse("Invalid Token!")

    user = Account.objects.filter(id=userID)

    if user.count() == 0:
        return HttpResponse("Oops, an error has occurred.")

    user = user[0]
    user.isVerified = True
    user.save(update_fields=['isVerified'])

    url = "findmysupply://"
    redirect = HttpResponse(url, status=302)
    redirect['Location'] = url
    return redirect


def isUserVerified(request, userID, token):
    if not Account.objects.filter(salt=token, id=userID):
        return HttpResponse("Invalid Token!")

    user = Account.objects.filter(id=userID)[0]

    return HttpResponse(json.dumps({"isVerified": user.isVerified}))


def privatizeEmail(email):
    emailPrefix = email[:email.find('@')]
    emailSuffix = email[email.find('@'):]
    length = len(emailPrefix)

    if length == 1:
        return email
    if length == 2:
        return f"{emailPrefix[:1]}*{emailSuffix}"
    if length == 3:
        return f"{emailPrefix[:1]}*{emailPrefix[-1:]}{emailSuffix}"
    if length == 4:
        return f"{emailPrefix[:1]}**{emailPrefix[-1:]}{emailSuffix}"
    if length == 5:
        return f"{emailPrefix[:2]}**{emailPrefix[-1:]}{emailSuffix}"
    stars = '*' * (length - 4)
    return f"{emailPrefix[:2]}{stars}{emailPrefix[-2:]}{emailSuffix}"




def sendResetPswEmail(request, login):
    user1 = Account.objects.filter(email=login)
    user2 =  Account.objects.filter(username=login)
    if not(user1 or user2):
        return HttpResponse(json.dumps({"message": "#Username or email not found."}))

    if user1:
        if not user1[0].isVerified:
            return HttpResponse(json.dumps({"message": "VVerification email sent. Tap to resend."}))
    if user2:
        if not user2[0].isVerified:
            return HttpResponse(json.dumps({"message": "VVerification email sent. Tap to resend."}))

    sendResetPasswordEmail(user1[0]) if user1 else sendResetPasswordEmail(user2[0])

    return HttpResponse(json.dumps({"message": f"TEmail sent to {privatizeEmail(user1[0].email if user1 else user2[0].email)}. Tap to resend."}))


def resetPsw(request, userID):
    user = Account.objects.filter(id=userID)
    if user.count() == 0:
        return HttpResponse("Oops, an error has occurred.")

    user = user[0]
    user.forgotPassword = True
    user.save(update_fields=['forgotPassword'])

    url = "findmysupply://"
    redirect = HttpResponse(url, status=302)
    redirect['Location'] = url
    return redirect

def canUserChangePsw(request, login):
    user1 = Account.objects.filter(email=login)
    user2 =  Account.objects.filter(username=login)

    canChangePsw = None

    if user1:
        canChangePsw = user1[0].forgotPassword
    if user2:
        canChangePsw = user2[0].forgotPassword

    if canChangePsw == None:
        return HttpResponse("Oops, an error has occurred.")


    return HttpResponse(json.dumps({"isVerified": canChangePsw}))

def openApp(request):
    url = "findmysupply://"
    redirect = HttpResponse(url, status=302)
    redirect['Location'] = url
    return redirect

@api_view(['POST', ])
def addNewZipcode(request, zip, token):
    if not Account.objects.filter(salt=token):
        return HttpResponse("Invalid Token!")

    zipcode = Zipcodes.objects.filter(zip=zip)[0].mappedZipcode

    if zipcode.rank == 4:
        zipcode.rank = 0
        zipcode.isNew = True

        zipcode.save(update_fields=['rank', 'isNew'])

    return HttpResponse("Success")

@api_view(['POST', ])
def verifyReceipt(request, userID, token):
    user = Account.objects.filter(id=userID)[0]
    if user.salt != token:
        return HttpResponse("Invalid Token!")

    #Verify receipt

    receipt = json.loads(request.body.decode("utf-8"))
    print(f"receipt: \n{receipt['receipt'][:10]}\n")



    payload = {
        'receipt-data': receipt['receipt'],
        'exclude-old-transactions': True,
        'password': 'f222795534cc4c09a58392a56f1f5cfa'
    }

    #Production
    #https://buy.itunes.apple.com/verifyReceipt
    response = requests.post('https://sandbox.itunes.apple.com/verifyReceipt', json=payload)

    if response.status_code != 200:
        return HttpResponse(json.dumps({"isVerified": False}))

    responseObj = response.json()
    print(json.dumps(responseObj, indent=4, sort_keys=True))



    try:
        print(f"status: {responseObj['status']}")
        print(f"bundle: {responseObj['receipt']['bundle_id']}")
        print(f"productID: {responseObj['latest_receipt_info'][0]['product_id']}")

        if (responseObj["status"] != 0) or (responseObj["receipt"]["bundle_id"] != "cpp.Find-My-Supply") or (responseObj["latest_receipt_info"][0]["product_id"] not in SUBSCRIPTIONS):
            print("INVALID receipt")
            return HttpResponse(json.dumps({"isVerified": False}))

        print(f"Expiration Date:  {responseObj['latest_receipt_info'][0]['expires_date'][:-8]}" )

        #TURN SECONDS TO DAYS
        expirationDate = datetime.strptime(responseObj['latest_receipt_info'][0]['expires_date'][:-8], '%Y-%m-%d %H:%M:%S').replace(tzinfo=timezone.utc)

        print(f"Time delta: {(expirationDate - datetime.now(timezone.utc)).days}")

        if (expirationDate - datetime.now(timezone.utc)).days < 0:
            print("INVALID receipt")
            return HttpResponse(json.dumps({"isVerified": False}))


        print("right before reg id")
        if user.registration_id:
            print("got here 1")
            device = APNSDevice.objects.filter(user_id=user.id)
            print("got here 2")
            if device.exists():
                print("got here 3")
                device[0].active = True
                device[0].save(update_fields=['active'])
                print("got here 4")


        user.expirationDate = expirationDate + timedelta(days=GRACE)
        user.isGold = True
        user.receiptData = responseObj['latest_receipt']
        user.save(update_fields=['isGold', 'expirationDate', 'receiptData'])
    except:
        print("EXCEPTION THROWN")
        return HttpResponse(json.dumps({"isVerified": False}))


    return HttpResponse(json.dumps({"isVerified": True }))

@csrf_exempt
@api_view(['POST', ])
def addRegistrationID(request, userID, token, ID):
    if not Account.objects.filter(salt=token, id=userID):
        return HttpResponse("Invalid Token!")

    user = Account.objects.filter(id=userID)[0]

    user.registration_id = ID
    user.save(update_fields=['registration_id'])

    if not APNSDevice.objects.filter(user_id=userID).exists():
        APNSDevice(user_id=userID, registration_id=ID, active=True).save()


    return HttpResponse("Success")


def test(request):
    payload = {
        'receipt-data': RECEIPT,
        'exclude-old-transactions': True,
        'password': SHAREDSECRET
    }

    #Production
    #https://buy.itunes.apple.com/verifyReceipt
    url = 'https://sandbox.itunes.apple.com/verifyReceipt'
    response = requests.post(url, json=payload)

    if response.status_code != 200:
        return HttpResponse(json.dumps({"isVerified": False}))

    responseObj = response.json()
    print(json.dumps(responseObj, indent=4, sort_keys=True))

    expirationDate = datetime.strptime(responseObj['latest_receipt_info'][0]['expires_date'][:-8], '%Y-%m-%d %H:%M:%S').replace(tzinfo=timezone.utc)
    print(expirationDate)
    print(datetime.now(timezone.utc))
    print((expirationDate - datetime.now(timezone.utc)).days)
    if (expirationDate - datetime.now(timezone.utc)).days < 0:
        print("EXPIRED!")
    else:
        print("renewed")

    return HttpResponse("SUCCESS")







GRACE = 0
SHAREDSECRET = 'f222795534cc4c09a58392a56f1f5cfa'
SUBSCRIPTIONS = {"TwelveMonths_auto", 'OneMonth_auto', 'SixMonths_auto'}
RECEIPT = "MIIT1AYJKoZIhvcNAQcCoIITxTCCE8ECAQExCzAJBgUrDgMCGgUAMIIDdQYJKoZIhvcNAQcBoIIDZgSCA2IxggNeMAoCAQgCAQEEAhYAMAoCARQCAQEEAgwAMAsCAQECAQEEAwIBADALAgEDAgEBBAMMATEwCwIBCwIBAQQDAgEAMAsCAQ8CAQEEAwIBADALAgEQAgEBBAMCAQAwCwIBGQIBAQQDAgEDMAwCAQoCAQEEBBYCNCswDAIBDgIBAQQEAgIApDANAgENAgEBBAUCAwH9YDANAgETAgEBBAUMAzEuMDAOAgEJAgEBBAYCBFAyNTMwGAIBBAIBAgQQobWaCr6Klm9n1Lw0aRTgazAbAgEAAgEBBBMMEVByb2R1Y3Rpb25TYW5kYm94MBwCAQICAQEEFAwSY3BwLkZpbmQtTXktU3VwcGx5MBwCAQUCAQEEFA1v020khz8VOswf2gqdl+VH3KhDMB4CAQwCAQEEFhYUMjAyMC0wNS0wNlQyMTo1NDo1MVowHgIBEgIBAQQWFhQyMDEzLTA4LTAxVDA3OjAwOjAwWjA2AgEHAgEBBC4rVpwy29R3ZnsinWhMpnJ+ubhTXeNp4gB5JeZ+TeUGofikRUdj6sIXlIo9Qp8mMEICAQYCAQEEOo3k+oLmucZa9jbRnyPZ7qRodvvVrbXxMmVeBI/91sKar3CP96QmiSgCF5ndN2ghyqV+XwsrAEDgITowggF7AgERAgEBBIIBcTGCAW0wCwICBq0CAQEEAgwAMAsCAgawAgEBBAIWADALAgIGsgIBAQQCDAAwCwICBrMCAQEEAgwAMAsCAga0AgEBBAIMADALAgIGtQIBAQQCDAAwCwICBrYCAQEEAgwAMAwCAgalAgEBBAMCAQEwDAICBqsCAQEEAwIBAzAMAgIGrgIBAQQDAgEAMAwCAgaxAgEBBAMCAQAwDAICBrcCAQEEAwIBADASAgIGrwIBAQQJAgcDjX6n5FKoMBkCAgamAgEBBBAMDlNpeE1vbnRoc19hdXRvMBsCAganAgEBBBIMEDEwMDAwMDA2NjEwNjYxOTMwGwICBqkCAQEEEgwQMTAwMDAwMDY2MDE4MTQ5NjAfAgIGqAIBAQQWFhQyMDIwLTA1LTA2VDIxOjU0OjQ5WjAfAgIGqgIBAQQWFhQyMDIwLTA1LTA1VDA0OjAxOjQxWjAfAgIGrAIBAQQWFhQyMDIwLTA1LTA2VDIyOjI0OjQ5WqCCDmUwggV8MIIEZKADAgECAggO61eH554JjTANBgkqhkiG9w0BAQUFADCBljELMAkGA1UEBhMCVVMxEzARBgNVBAoMCkFwcGxlIEluYy4xLDAqBgNVBAsMI0FwcGxlIFdvcmxkd2lkZSBEZXZlbG9wZXIgUmVsYXRpb25zMUQwQgYDVQQDDDtBcHBsZSBXb3JsZHdpZGUgRGV2ZWxvcGVyIFJlbGF0aW9ucyBDZXJ0aWZpY2F0aW9uIEF1dGhvcml0eTAeFw0xNTExMTMwMjE1MDlaFw0yMzAyMDcyMTQ4NDdaMIGJMTcwNQYDVQQDDC5NYWMgQXBwIFN0b3JlIGFuZCBpVHVuZXMgU3RvcmUgUmVjZWlwdCBTaWduaW5nMSwwKgYDVQQLDCNBcHBsZSBXb3JsZHdpZGUgRGV2ZWxvcGVyIFJlbGF0aW9uczETMBEGA1UECgwKQXBwbGUgSW5jLjELMAkGA1UEBhMCVVMwggEiMA0GCSqGSIb3DQEBAQUAA4IBDwAwggEKAoIBAQClz4H9JaKBW9aH7SPaMxyO4iPApcQmyz3Gn+xKDVWG/6QC15fKOVRtfX+yVBidxCxScY5ke4LOibpJ1gjltIhxzz9bRi7GxB24A6lYogQ+IXjV27fQjhKNg0xbKmg3k8LyvR7E0qEMSlhSqxLj7d0fmBWQNS3CzBLKjUiB91h4VGvojDE2H0oGDEdU8zeQuLKSiX1fpIVK4cCc4Lqku4KXY/Qrk8H9Pm/KwfU8qY9SGsAlCnYO3v6Z/v/Ca/VbXqxzUUkIVonMQ5DMjoEC0KCXtlyxoWlph5AQaCYmObgdEHOwCl3Fc9DfdjvYLdmIHuPsB8/ijtDT+iZVge/iA0kjAgMBAAGjggHXMIIB0zA/BggrBgEFBQcBAQQzMDEwLwYIKwYBBQUHMAGGI2h0dHA6Ly9vY3NwLmFwcGxlLmNvbS9vY3NwMDMtd3dkcjA0MB0GA1UdDgQWBBSRpJz8xHa3n6CK9E31jzZd7SsEhTAMBgNVHRMBAf8EAjAAMB8GA1UdIwQYMBaAFIgnFwmpthhgi+zruvZHWcVSVKO3MIIBHgYDVR0gBIIBFTCCAREwggENBgoqhkiG92NkBQYBMIH+MIHDBggrBgEFBQcCAjCBtgyBs1JlbGlhbmNlIG9uIHRoaXMgY2VydGlmaWNhdGUgYnkgYW55IHBhcnR5IGFzc3VtZXMgYWNjZXB0YW5jZSBvZiB0aGUgdGhlbiBhcHBsaWNhYmxlIHN0YW5kYXJkIHRlcm1zIGFuZCBjb25kaXRpb25zIG9mIHVzZSwgY2VydGlmaWNhdGUgcG9saWN5IGFuZCBjZXJ0aWZpY2F0aW9uIHByYWN0aWNlIHN0YXRlbWVudHMuMDYGCCsGAQUFBwIBFipodHRwOi8vd3d3LmFwcGxlLmNvbS9jZXJ0aWZpY2F0ZWF1dGhvcml0eS8wDgYDVR0PAQH/BAQDAgeAMBAGCiqGSIb3Y2QGCwEEAgUAMA0GCSqGSIb3DQEBBQUAA4IBAQANphvTLj3jWysHbkKWbNPojEMwgl/gXNGNvr0PvRr8JZLbjIXDgFnf4+LXLgUUrA3btrj+/DUufMutF2uOfx/kd7mxZ5W0E16mGYZ2+FogledjjA9z/Ojtxh+umfhlSFyg4Cg6wBA3LbmgBDkfc7nIBf3y3n8aKipuKwH8oCBc2et9J6Yz+PWY4L5E27FMZ/xuCk/J4gao0pfzp45rUaJahHVl0RYEYuPBX/UIqc9o2ZIAycGMs/iNAGS6WGDAfK+PdcppuVsq1h1obphC9UynNxmbzDscehlD86Ntv0hgBgw2kivs3hi1EdotI9CO/KBpnBcbnoB7OUdFMGEvxxOoMIIEIjCCAwqgAwIBAgIIAd68xDltoBAwDQYJKoZIhvcNAQEFBQAwYjELMAkGA1UEBhMCVVMxEzARBgNVBAoTCkFwcGxlIEluYy4xJjAkBgNVBAsTHUFwcGxlIENlcnRpZmljYXRpb24gQXV0aG9yaXR5MRYwFAYDVQQDEw1BcHBsZSBSb290IENBMB4XDTEzMDIwNzIxNDg0N1oXDTIzMDIwNzIxNDg0N1owgZYxCzAJBgNVBAYTAlVTMRMwEQYDVQQKDApBcHBsZSBJbmMuMSwwKgYDVQQLDCNBcHBsZSBXb3JsZHdpZGUgRGV2ZWxvcGVyIFJlbGF0aW9uczFEMEIGA1UEAww7QXBwbGUgV29ybGR3aWRlIERldmVsb3BlciBSZWxhdGlvbnMgQ2VydGlmaWNhdGlvbiBBdXRob3JpdHkwggEiMA0GCSqGSIb3DQEBAQUAA4IBDwAwggEKAoIBAQDKOFSmy1aqyCQ5SOmM7uxfuH8mkbw0U3rOfGOAYXdkXqUHI7Y5/lAtFVZYcC1+xG7BSoU+L/DehBqhV8mvexj/avoVEkkVCBmsqtsqMu2WY2hSFT2Miuy/axiV4AOsAX2XBWfODoWVN2rtCbauZ81RZJ/GXNG8V25nNYB2NqSHgW44j9grFU57Jdhav06DwY3Sk9UacbVgnJ0zTlX5ElgMhrgWDcHld0WNUEi6Ky3klIXh6MSdxmilsKP8Z35wugJZS3dCkTm59c3hTO/AO0iMpuUhXf1qarunFjVg0uat80YpyejDi+l5wGphZxWy8P3laLxiX27Pmd3vG2P+kmWrAgMBAAGjgaYwgaMwHQYDVR0OBBYEFIgnFwmpthhgi+zruvZHWcVSVKO3MA8GA1UdEwEB/wQFMAMBAf8wHwYDVR0jBBgwFoAUK9BpR5R2Cf70a40uQKb3R01/CF4wLgYDVR0fBCcwJTAjoCGgH4YdaHR0cDovL2NybC5hcHBsZS5jb20vcm9vdC5jcmwwDgYDVR0PAQH/BAQDAgGGMBAGCiqGSIb3Y2QGAgEEAgUAMA0GCSqGSIb3DQEBBQUAA4IBAQBPz+9Zviz1smwvj+4ThzLoBTWobot9yWkMudkXvHcs1Gfi/ZptOllc34MBvbKuKmFysa/Nw0Uwj6ODDc4dR7Txk4qjdJukw5hyhzs+r0ULklS5MruQGFNrCk4QttkdUGwhgAqJTleMa1s8Pab93vcNIx0LSiaHP7qRkkykGRIZbVf1eliHe2iK5IaMSuviSRSqpd1VAKmuu0swruGgsbwpgOYJd+W+NKIByn/c4grmO7i77LpilfMFY0GCzQ87HUyVpNur+cmV6U/kTecmmYHpvPm0KdIBembhLoz2IYrF+Hjhga6/05Cdqa3zr/04GpZnMBxRpVzscYqCtGwPDBUfMIIEuzCCA6OgAwIBAgIBAjANBgkqhkiG9w0BAQUFADBiMQswCQYDVQQGEwJVUzETMBEGA1UEChMKQXBwbGUgSW5jLjEmMCQGA1UECxMdQXBwbGUgQ2VydGlmaWNhdGlvbiBBdXRob3JpdHkxFjAUBgNVBAMTDUFwcGxlIFJvb3QgQ0EwHhcNMDYwNDI1MjE0MDM2WhcNMzUwMjA5MjE0MDM2WjBiMQswCQYDVQQGEwJVUzETMBEGA1UEChMKQXBwbGUgSW5jLjEmMCQGA1UECxMdQXBwbGUgQ2VydGlmaWNhdGlvbiBBdXRob3JpdHkxFjAUBgNVBAMTDUFwcGxlIFJvb3QgQ0EwggEiMA0GCSqGSIb3DQEBAQUAA4IBDwAwggEKAoIBAQDkkakJH5HbHkdQ6wXtXnmELes2oldMVeyLGYne+Uts9QerIjAC6Bg++FAJ039BqJj50cpmnCRrEdCju+QbKsMflZ56DKRHi1vUFjczy8QPTc4UadHJGXL1XQ7Vf1+b8iUDulWPTV0N8WQ1IxVLFVkds5T39pyez1C6wVhQZ48ItCD3y6wsIG9wtj8BMIy3Q88PnT3zK0koGsj+zrW5DtleHNbLPbU6rfQPDgCSC7EhFi501TwN22IWq6NxkkdTVcGvL0Gz+PvjcM3mo0xFfh9Ma1CWQYnEdGILEINBhzOKgbEwWOxaBDKMaLOPHd5lc/9nXmW8Sdh2nzMUZaF3lMktAgMBAAGjggF6MIIBdjAOBgNVHQ8BAf8EBAMCAQYwDwYDVR0TAQH/BAUwAwEB/zAdBgNVHQ4EFgQUK9BpR5R2Cf70a40uQKb3R01/CF4wHwYDVR0jBBgwFoAUK9BpR5R2Cf70a40uQKb3R01/CF4wggERBgNVHSAEggEIMIIBBDCCAQAGCSqGSIb3Y2QFATCB8jAqBggrBgEFBQcCARYeaHR0cHM6Ly93d3cuYXBwbGUuY29tL2FwcGxlY2EvMIHDBggrBgEFBQcCAjCBthqBs1JlbGlhbmNlIG9uIHRoaXMgY2VydGlmaWNhdGUgYnkgYW55IHBhcnR5IGFzc3VtZXMgYWNjZXB0YW5jZSBvZiB0aGUgdGhlbiBhcHBsaWNhYmxlIHN0YW5kYXJkIHRlcm1zIGFuZCBjb25kaXRpb25zIG9mIHVzZSwgY2VydGlmaWNhdGUgcG9saWN5IGFuZCBjZXJ0aWZpY2F0aW9uIHByYWN0aWNlIHN0YXRlbWVudHMuMA0GCSqGSIb3DQEBBQUAA4IBAQBcNplMLXi37Yyb3PN3m/J20ncwT8EfhYOFG5k9RzfyqZtAjizUsZAS2L70c5vu0mQPy3lPNNiiPvl4/2vIB+x9OYOLUyDTOMSxv5pPCmv/K/xZpwUJfBdAVhEedNO3iyM7R6PVbyTi69G3cN8PReEnyvFteO3ntRcXqNx+IjXKJdXZD9Zr1KIkIxH3oayPc4FgxhtbCS+SsvhESPBgOJ4V9T0mZyCKM2r3DYLP3uujL/lTaltkwGMzd/c6ByxW69oPIQ7aunMZT7XZNn/Bh1XZp5m5MkL72NVxnn6hUrcbvZNCJBIqxw8dtk2cXmPIS4AXUKqK1drk/NAJBzewdXUhMYIByzCCAccCAQEwgaMwgZYxCzAJBgNVBAYTAlVTMRMwEQYDVQQKDApBcHBsZSBJbmMuMSwwKgYDVQQLDCNBcHBsZSBXb3JsZHdpZGUgRGV2ZWxvcGVyIFJlbGF0aW9uczFEMEIGA1UEAww7QXBwbGUgV29ybGR3aWRlIERldmVsb3BlciBSZWxhdGlvbnMgQ2VydGlmaWNhdGlvbiBBdXRob3JpdHkCCA7rV4fnngmNMAkGBSsOAwIaBQAwDQYJKoZIhvcNAQEBBQAEggEAUQBW4ktBwgpd6LpOWBPW9rvDtPhJtEZ7xQAR9/RGQ6m7urItxBej8modWmJYMF9JOGSTwIz166OEeuk6/gEU83rBCQzTx0lvjGwV9X3qT/ND14wuNGn2CZCfefdhyU3w2L3Xzly8xjTCAZPI2Iy7bOk/xSMn/inXajDTGURJVx74DsPVjiphPq81fVe76hDNyEQxiMY3UHK15H9LMoF206ns6Uns2ljzI/J7CU/yy6cuFfav7GGjXO/s26FHZI5WFxutcZGnV2FlEz8HvbqWLq8tzMcINt/CgotxuoQPTgCvizczEloxtHHcTUmxF8A+/8G2G3Atajv84NTt0vsRrg=="



def main(request):
    return HttpResponse("Welcome to Find My Supply's Backend!")