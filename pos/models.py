# -*- coding: utf-8 -*-
from datetime import datetime, timedelta
from django.utils.timezone import utc
import pytz

from django.conf import settings
from django.db import models
from django.contrib.auth.models import User

try:
    from printer import printOrder
except:
    pass

class Employee(models.Model):
    user = models.OneToOneField(User)
    pin = models.CharField(max_length=10, unique=True)
    #role = models.

    def _userId(self):
        return self.user.id
    userId = property(_userId)

    def _username(self):
        return self.user.username
    username = property(_username)

    def _name(self):
        return self.user.first_name
    name = property(_name)

class Table(models.Model):
    number = models.IntegerField()
    nickname = models.CharField(max_length=100, blank=True, null=True)
    taken = models.BooleanField(default=False)
    parent = models.ForeignKey("Table", blank=True, null=True)
    booked = models.DateField(blank=True, null=True)

    def _parentId(self):
        if self.parent is None: return None
        return self.parent.id
    parentId = property(_parentId)

    def __unicode__(self):
        return Table._meta.verbose_name + " " + self.nickname

    class Meta:
        verbose_name = u'Маса'
        verbose_name_plural = u'Маси'

class CategoryType(models.Model):
    name = models.CharField(max_length=100)

    def __unicode__(self):
        return self.name

    class Meta:
        verbose_name = u'Тип Категория'
        verbose_name_plural = u'Тип Категории'


class Category(models.Model):
    name = models.CharField(max_length=500)
    neatName = models.CharField(max_length=100)
    order = models.IntegerField()
    categoryType = models.ForeignKey(CategoryType);

    def __unicode__(self):
        return self.name

    class Meta:
        verbose_name = u'Категория'
        verbose_name_plural = u'Категории'

class Product(models.Model):
    name = models.CharField(max_length=200)
    description = models.CharField(max_length=500, blank=True, null=True)
    category = models.ForeignKey(Category)
    price = models.DecimalField(decimal_places=2, max_digits=10)
    availability = models.IntegerField(default=0)
    availabilityUpdated = models.DateField(blank=True, null=True)
    order = models.IntegerField()
    available = models.BooleanField(blank=True, default=True)

    def _categoryNeatName(self):
        return self.category.neatName
    categoryNeatName = property(_categoryNeatName)

    def _categoryId(self):
        return self.category.id
    categoryId = property(_categoryId)

    def __unicode__(self):
        return self.name

    class Meta:
        verbose_name = u'Ястие'
        verbose_name_plural = u'Ястия'

class Order(models.Model):
    table = models.ForeignKey(Table)
    total = models.DecimalField(decimal_places=2, max_digits=10, default=0)
    discount = models.DecimalField(decimal_places=2, max_digits=10, default=0)
    discountReason = models.CharField(max_length=500, blank=True, null=True)
    notes = models.CharField(max_length=500, blank=True, null=True)

    started = models.DateTimeField(auto_now=True)
    closed = models.DateTimeField(blank=True, null=True)
    status = models.BooleanField()
    fis = models.BooleanField(default=False)
    reported = models.BooleanField(default=False)
    reportedDate = models.DateTimeField(blank=True, null=True)

    openedBy = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='openedBy')
    closedBy = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='closedBy', blank=True, null=True)
    operatedBy = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='operatedBy')

    def _tableId(self):
        return self.table.id
    tableId = property(_tableId)

    def _operatedBy(self):
        return self.operatedBy.id
    operatedById = property(_operatedBy)

    def _orderItems(self):
        return set(orderItem.id for orderItem in OrderItem.objects.filter(order__id=self.id))
    items = property(_orderItems)

    def save(self, *args, **kwargs):
        self.operatedBy = self.openedBy

        if self.id:
            orderItems = OrderItem.objects.filter(order__id=self.id)
            if self.reported == True:
                pass
            else:
                self.total = 0
                for oi in orderItems:
                    self.total += oi.quantity*oi.product.price

                if self.discount > 0:
                    self.total -= self.total*(self.discount/100)

                if self.status:
                    self.table.taken = False
                    self.table.save()

                    self.closed = datetime.now()

                    try:
                        printOrder(self, orderItems)
                    except:
                        pass


        super(Order, self).save(*args, **kwargs)

    def __unicode__(self):
        return self.table.nickname + " / " + datetime.strftime(self.started, "%Y-%m-%d %H:%M")

    class Meta:
        verbose_name = u'Поръчка'
        verbose_name_plural = u'Поръчки'

class OrderItem(models.Model):
    order = models.ForeignKey(Order)
    product = models.ForeignKey(Product)
    quantity = models.PositiveIntegerField(default=1)
    entered = models.DateTimeField(blank=True, null=True)
    changed = models.DateTimeField(blank=True, null=True)
    wasted = models.BooleanField(default=False)
    wastedReason = models.CharField(max_length=500, blank=True, null=True)
    addedBy = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='addedBy', blank=True, null=True)
    wastedBy = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='wastedBy', blank=True, null=True)
    sent = models.BooleanField(default=False)
    comment = models.CharField(max_length=500, blank=True, null=True)
    cooked = models.BooleanField(default=False)
    reduced = models.PositiveIntegerField(default=0)
    price = models.DecimalField(decimal_places=2, max_digits=10)

    def save(self, *args, **kwargs):
        if not self.id:
            self.entered = datetime.utcnow().replace(tzinfo=utc)
            pass

        if self.sent and not self.changed:
            self.changed = datetime.utcnow().replace(tzinfo=utc)
        else:
            self.sent = True

        #self.operatedBy = self.openedBy
        super(OrderItem, self).save(*args, **kwargs)

    def _orderId(self):
        return self.order.id
    orderId = property(_orderId)

    def _productId(self):
        return self.product.id
    productId = property(_productId)

    def _productName(self):
        return self.product.name
    productName = property(_productName)

    def _productDesc(self):
        return self.product.description
    productDesc = property(_productDesc)

    def _productPrice(self):
        return self.product.price
    productPrice = property(_productPrice)

    def _tableName(self):
        return self.order.table.nickname
    tableName = property(_tableName)

    def _categoryType(self):
        return self.product.category.categoryType.name
    categoryType = property(_categoryType)

    def _categoryNeatName(self):
        return self.product.category.neatName
    categoryNeatName = property(_categoryNeatName)

    def _waiter(self):
        return self.addedBy.first_name
    waiter = property(_waiter)

    def __unicode__(self):
        retVal = self.order.table.nickname + " / " + self.product.name
        if(self.changed):
            retVal += " / " + datetime.strftime(self.changed, "%Y-%m-%d %H:%M")
            return retVal

        return retVal + u" / не е обработена"

    class Meta:
        verbose_name = u'Продажба'
        verbose_name_plural = u'Продажби'