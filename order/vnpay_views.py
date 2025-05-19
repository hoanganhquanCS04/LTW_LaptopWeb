from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseRedirect
from django.shortcuts import render, redirect
from django.utils import timezone

from order.models import ShopCart, Order
from vnpay.models import Billing


@login_required(login_url='/login')
def payment_vnpay(request):
    current_user = request.user
    shopcart = ShopCart.objects.filter(user_id=current_user.id)
    total = 0
    for rs in shopcart:
        total += rs.product.price * rs.quantity

    # Tạo billing cho VNPay
    billing = Billing.objects.create(
        status='NEW',
        currency='VND',
        pay_by=current_user,
        amount=total,
        reference_number=timezone.now().strftime('%Y%m%d%H%M%S'),
    )

    # Lấy URL thanh toán từ VNPay
    payment_url = billing.get_payment_url(request)
    
    # Lưu billing_id vào session để sử dụng khi thanh toán hoàn tất
    request.session['billing_id'] = billing.id
    
    # Chuyển hướng đến trang thanh toán VNPay
    return HttpResponseRedirect(payment_url)


@login_required(login_url='/login')
def payment_return(request):
    # Get the VNPAY parameters directly from request.GET
    order_id = request.GET.get('vnp_TxnRef')
    payment_status = request.GET.get('vnp_ResponseCode') == '00'
    
    # Find the order
    try:
        order = Order.objects.get(code=order_id)
    except Order.DoesNotExist:
        order = None
    
    # Find billing to update if payment is successful
    try:
        billing = Billing.objects.filter(reference_number=order_id).first()
        if payment_status and billing and billing.status != 'CONFIRMED':
            billing.status = 'CONFIRMED'
            billing.is_paid = True
            billing.save()
            
            # Update order if found
            if order:
                order.status = 'Chấp nhận'
                order.save()
                
                # Clear shopping cart
                ShopCart.objects.filter(user_id=request.user.id).delete()
                request.session['cart_items'] = 0
    except:
        pass
    
    if payment_status:
        messages.success(request, "Thanh toán thành công! Đơn hàng của bạn đã được xác nhận.")
    else:
        messages.warning(request, "Thanh toán không thành công!")
    
    # Add required context variables that might be missing
    from product.models import Category
    categories = Category.objects.all()
    
    # Render with complete context including category
    return render(request, 'Order_Completed.html', {
        'ordercode': order_id,
        'payment_method': 'vnpay',
        'payment_status': payment_status,
        'user': request.user,
        'category': categories,  # Add this to fix the error
        'categories': categories  # Add this as well in case it's needed
    })