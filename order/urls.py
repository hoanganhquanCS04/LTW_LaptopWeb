from django.urls import path, include
from . import views, vnpay_views
urlpatterns = [
    path('', views.index,name='index'),
    path('addtoshopcart/<int:id>', views.addtoshopcart, name='addtoshopcart'),
    path('deletefromcart/<int:id>', views.deletefromcart, name='deletefromcart'),
    path('orderproduct/', views.orderproduct, name='orderproduct'),
    path('payment-vnpay/', vnpay_views.payment_vnpay, name='payment_vnpay'),
    path('payment-return/', vnpay_views.payment_return, name='payment_return'),
]