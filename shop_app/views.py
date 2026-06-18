from django.shortcuts import render
from rest_framework.decorators import api_view, permission_classes
from .models import Product, Cart, CartItem, Transaction
from .serializers import DetailProductSerializer, UserSerializer, ProductSerializer, CartItemSerializer, SimpleCartSerializer, CartSerializer
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from requests.exceptions import RequestException
from decimal import Decimal
import uuid
from django.conf import settings
import requests
import paypalrestsdk
from django.conf import settings
#import paypalrestsdk now

BASE_URL = settings.REACT_BASE_URL

paypalrestsdk.configure({ 
    "mode": settings.PAYPAL_MODE,
    "client_id": settings.PAYPAL_CLIENT_ID,
    "client_secret": settings.PAYPAL_CLIENT_SECRET
})


@api_view(["GET"])
def products(request):
    products = Product.objects.all()
    serializer = ProductSerializer(products, many=True)
    return Response(serializer.data)

@api_view(["GET"])
def product_detail(request, slug):
    try:
        product = Product.objects.get(slug=slug)
        serializer = DetailProductSerializer(product)
        return Response(serializer.data)
    except Product.DoesNotExist:
        return Response({"error": "Product not found"}, status=status.HTTP_404_NOT_FOUND)

@api_view(["POST"])
def add_item(request):
    try:
        cart_code = request.data.get("cart_code")
        product_id = request.data.get("product_id")

        cart, created = Cart.objects.get_or_create(cart_code=cart_code)
        product = Product.objects.get(id=product_id)

        cartitem, created = CartItem.objects.get_or_create(cart=cart, product=product)
        cartitem.quantity = 1 # FIX: Fixed typo 'quntity' -> 'quantity'
        cartitem.save()

        serializer = CartItemSerializer(cartitem)
        return Response({"data": serializer.data, "message": "Cartitem created successfully"}, status=201)
    except Exception as e:
        return Response({"error": str(e)}, status=400)

@api_view(['GET'])
def product_in_cart(request):
    try:
        cart_code = request.query_params.get("cart_code")
        product_id = request.query_params.get("product_id")

        cart = Cart.objects.get(cart_code=cart_code)
        product = Product.objects.get(id=product_id)

        product_exists_in_cart = CartItem.objects.filter(cart=cart, product=product).exists()
        return Response({'product_in_cart': product_exists_in_cart})
    except Exception:
        return Response({'product_in_cart': False})

@api_view(['GET'])
def get_cart_stat(request):
    try:
        cart_code = request.query_params.get("cart_code")
        cart = Cart.objects.get(cart_code=cart_code, paid=False)
        serializer = SimpleCartSerializer(cart)
        return Response(serializer.data)
    except Cart.DoesNotExist:
        return Response({"num_of_items": 0}, status=status.HTTP_200_OK)

@api_view(['GET'])
def get_cart(request):
    try:
        cart_code = request.query_params.get("cart_code")
        cart = Cart.objects.get(cart_code=cart_code, paid=False)
        serializer = CartSerializer(cart)
        return Response(serializer.data)
    except Cart.DoesNotExist:
        return Response({"error": "Cart not found"}, status=status.HTTP_404_NOT_FOUND)

@api_view(['PATCH'])
def update_quantity(request):
    try: 
        cartitem_id = request.data.get("item_id")
        quantity = request.data.get("quantity")
        quantity = int(quantity)
        cartitem = CartItem.objects.get(id=cartitem_id)
        cartitem.quantity = quantity
        cartitem.save()
        serializer = CartItemSerializer(cartitem)
        return Response({ "data": serializer.data, "message": "Cartitem updated successfully"})
    except Exception as e:
        return Response({'error': str(e)}, status=400)

@api_view(['POST'])
def delete_cartitem(request):
    try:
        cartitem_id = request.data.get("item_id")
        cartitem = CartItem.objects.get(id=cartitem_id)
        cartitem.delete()
        return Response({"message": "item deleted successfully"}, status=status.HTTP_204_NO_CONTENT)
    except CartItem.DoesNotExist:
        return Response({"error": "Item not found"}, status=status.HTTP_404_NOT_FOUND)

@api_view(["GET"])
@permission_classes([IsAuthenticated])
def get_username(request):
    user = request.user
    return Response({"username": user.username})

@api_view(["GET"])
@permission_classes([IsAuthenticated])
def user_info(request): 
    user = request.user
    serializer = UserSerializer(user)
    return Response(serializer.data)

# @api_view(["POST"])
# @permission_classes([IsAuthenticated])
# def initiate_payment(request):
#     try:
#         tx_ref = str(uuid.uuid4())
#         cart_code = request.data.get("cart_code")
#         cart = Cart.objects.get(cart_code=cart_code)
#         user = request.user

#         # FIX: Fixed spelling typo 'quantitiy' -> 'quantity'
#         amount = sum([item.quantity * item.product.price for item in cart.items.all()])
#         tax = Decimal("4.00")
#         total_amount = amount + tax
#         currency = "NGN"
#         redirect_url = f"{BASE_URL}/payment-status/"

#         transaction = Transaction.objects.create(
#             ref=tx_ref,
#             cart=cart,
#             amount=total_amount,
#             currency=currency,
#             user=user,
#             status='pending'
#         )

#         # Ensure safe access to fallback user profile values if standard model properties are missing
#         phone_number = getattr(user, 'phone', '') or getattr(user, 'phone_number', '')

#         flutterwave_payload = {
#             "tx_ref": tx_ref,
#             "amount": str(total_amount),
#             "currency": currency,
#             "redirect_url": redirect_url,
#             "customer": {
#                 "email": user.email,
#                 "name": user.username,
#                 "phonenumber": str(phone_number)
#             },
#             "customizations": {
#                 "title": "Shoppit Payment"
#             }
#         }

#         headers = {
#             "Authorization": f"Bearer {settings.FLUTTERWAVE_SECRET_KEY}",
#             "Content-Type": "application/json"
#         }

#         response = requests.post(
#             "https://api.flutterwave.com/v3/payments",
#             json=flutterwave_payload,
#             headers=headers
#         )

#         if response.status_code == 200:
#             return Response(response.json(), status=status.HTTP_200_OK)
#         else:
#             return Response(response.json(), status=response.status_code)

#     # FIX: Corrected Exception instance naming structure matches top import references
#     except RequestException as e:
#         return Response({"error": f"Flutterwave connection error: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
#     except Cart.DoesNotExist:
#         return Response({"error": "Active cart record could not be found"}, status=status.HTTP_404_NOT_FOUND)
#     except Exception as e:
#         return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)



@api_view(["POST"])
@permission_classes([IsAuthenticated])
def initiate_payment(request):
    try:
        tx_ref = str(uuid.uuid4())
        cart_code = request.data.get("cart_code")
        cart = Cart.objects.get(cart_code=cart_code)
        user = request.user

        # FIX 1: Provide Decimal("0.00") as the second argument to sum() so types align cleanly
        amount = sum([item.quantity * item.product.price for item in cart.items.all()], Decimal("0.00"))
        tax = Decimal("4.00")
        total_amount = amount + tax
        currency = "NGN"
        redirect_url = f"{BASE_URL}/payment-status/"

        transaction = Transaction.objects.create(
            ref=tx_ref,
            cart=cart,
            amount=total_amount,
            currency=currency,
            user=user,
            status='pending'
        )

        # FIX 2: Check both 'phone' and 'phone_number' fields to prevent attribute errors
        phone_number = getattr(user, 'phone', '') or getattr(user, 'phone_number', '') or "0000000000"

        flutterwave_payload = {
            "tx_ref": tx_ref,
            "amount": str(total_amount),
            "currency": currency,
            "redirect_url": redirect_url,
            "customer": {
                "email": user.email,
                "name": user.username,
                "phonenumber": str(phone_number)
            },
            "customizations": {
                "title": "Shoppit Payment"
            }
        }

        headers = {
            "Authorization": f"Bearer {settings.FLUTTERWAVE_SECRET_KEY}",
            "Content-Type": "application/json"
        }

        response = requests.post(
            "https://api.flutterwave.com/v3/payments",
            json=flutterwave_payload,
            headers=headers
        )

        if response.status_code == 200:
            return Response(response.json(), status=status.HTTP_200_OK)
        else:
            return Response(response.json(), status=response.status_code)

    except RequestException as e:
        return Response({"error": f"Flutterwave connection error: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    except Cart.DoesNotExist:
        return Response({"error": "Active cart record could not be found"}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)




@api_view(["GET", "POST"])
@permission_classes([IsAuthenticated])
def payment_callback(request):
    """
    Handles the payment redirect / webhook callback from Flutterwave.
    Verifies transaction validity and marks the associated cart as paid.
    """
    # 1. Extract transaction parameters from query string or request body
    status_param = request.query_params.get("status") or request.data.get("status")
    tx_ref = request.query_params.get("tx_ref") or request.data.get("tx_ref")
    transaction_id = request.query_params.get("transaction_id") or request.data.get("id")

    # 2. Early exit if the initial parameter indicates anything other than success
    if status_param not in ["successful", "completed"]:
        return Response(
            {"message": "Payment execution was cancelled or failed.", "status": "failed"},
            status=status.HTTP_400_BAD_REQUEST
        )

    # 3. Fetch matching Transaction and Cart from local database records
    try:
        transaction = Transaction.objects.get(ref=tx_ref)
        cart = transaction.cart
    except Transaction.DoesNotExist:
        return Response(
            {"error": "The specified transaction reference record could not be found."},
            status=status.HTTP_404_NOT_FOUND
        )

    # 4. Perform live server-to-server transaction verification with Flutterwave API
    try:
        url = f"https://api.flutterwave.com/v3/transactions/{transaction_id}/verify"
        headers = {
            "Authorization": f"Bearer {settings.FLUTTERWAVE_SECRET_KEY}",
            "Content-Type": "application/json"
        }

        response = requests.get(url, headers=headers)

        if response.status_code != 200:
            transaction.status = "failed"
            transaction.save()
            return Response(
                {"error": "Could not successfully contact Flutterwave transaction verification gateway."},
                status=response.status_code
            )

        response_data = response.json()

        # 5. Extract verification values returned securely from the gateway API response dict
        flw_status = response_data.get("data", {}).get("status")
        flw_amount = response_data.get("data", {}).get("amount")
        flw_currency = response_data.get("data", {}).get("currency")

        # 6. Critical business validation checks (Verifying status, amount, and currency integrity)
        if flw_status == "successful":
            # Cast response string values to ensure valid numeric comparison against Decimal models
            if Decimal(str(flw_amount)) >= transaction.amount and flw_currency == transaction.currency:
                
                # Update Transaction status in the database
                transaction.status = "completed"
                transaction.save()

                # Mark the shopping cart pool instance record as paid
                cart.paid = True
                cart.save()

                return Response(
                    {
                        "message": "Payment verified and completed successfully.",
                        "status": "completed",
                        "cart_code": cart.cart_code
                    },
                    status=status.HTTP_200_OK
                )
            else:
                # Security Hazard: Integrity checks failed (Paid total or currency altered mid-flight)
                transaction.status = "failed"
                transaction.save()
                return Response(
                    {"error": "Security check mismatch. Paid values do not match transaction history initialization data."},
                    status=status.HTTP_400_BAD_REQUEST
                )
        else:
            transaction.status = "failed"
            transaction.save()
            return Response(
                {"error": "Transaction verification was officially rejected by Flutterwave platform."},
                status=status.HTTP_400_BAD_REQUEST
            )

    except RequestException as e:
        return Response(
            {"error": f"Flutterwave link connection error: {str(e)}"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
    except Exception as e:
        return Response(
            {"error": f"Internal payment engine system processing failure: {str(e)}"},
            status=status.HTTP_400_BAD_REQUEST
        )







# @api_view(['POST'])
# def initiate_paypal_payment(request):
#     if request.method == 'POST' and request.user.is_authenticated
#         try: 
#             tx_ref = str(uuid.uuid4())
#             user = request.user
#             cart_code = request.data.get('cart_code')
#             cart = Cart.objects.get(cart_code=cart_code)
#             total_amount = sum(item.product.price * ite.quantity for item in cart.items.all())

#             payment = paypalresultrestsdk.Payment({})
#             tax = Decimal('4.00')
#             # total_amount = amount + rax
#             currency = 'USD'
#             redirect_url = f"{BASE_URL}/payment-status/"


#             transaction = Transaction.objects.create(
#                 ref=tx_ref,
#                 cart=cart,
#                 amount=total_amount,
#                 currency=currency,
#                 user=user,
#                 status="pending"
#             )

#             flutterwave



@api_view(['POST'])
def initiate_paypal_payment(request):
    if request.method == 'POST' and request.user.is_authenticated:
        # Fetch the cart and calculate total amount
        tx_ref = str(uuid.uuid4())
        user = request.user
        cart_code = request.data.get("cart_code")
        cart = Cart.objects.get(cart_code=cart_code)
        total_amount = sum(item.product.price * item.quantity for item in cart.items.all())
        tax = Decimal("4.00")
        total_amount = amount + tax

        # Create a PayPal payment object
        payment = paypalrestsdk.Payment({
            "intent": "sale",
            "payer": {
                "payment_method": "paypal"
            },
            "redirect_urls": {
                # Use a single redirect URL for both success and cancel
                "return_url": f"{BASE_URL}/payment-status?paymentStatus=success&ref={tx_ref}",
                "cancel_url": f"{BASE_URL}/payment-status?paymentStatus=cancel"
            },
            "transactions": [{
                "item_list": {
                    "items": [{
                        "name": "Cart Items",
                        "sku": "cart",
                        "price": str(total_amount),
                        "currency": "USD",
                        "quantity": 1
                    }]
                },
                "amount": {
                    "total": str(total_amount),
                    "currency": "USD"
                },
                "description": "Payment for cart items."
            }]
        })

        print("pay_id", payment)

        transaction, created = Transaction.objects.get_or_create(
            ref=tx_ref,
            cart=cart,
            amount=total_amount,
            user=user,
            status='pending'
        )

        if payment.create():
            # print(payment.links)
            # Extract PayPal approval URL to redirect the user
            for link in payment.links:
                if link.rel == "approval_url":
                    approval_url = str(link.href)
                    return Response({"approval_url": approval_url})
        else:
            return Response({"error": payment.error}, status=400)

    return Response({"error": "Invalid request"}, status=400)   





@api_view(['POST'])
def paypal_payment_callback(request):
    payment_id = request.query_params.get("paymentId")
    payer_id = request.query_params.get("payerID")
    ref = request.query_params.get("ref")

    user = request.user

    print("refff", ref)

    transaction = Transaction.objects.get(ref=ref)

    if payment_id and payer_id:
        payment = paypalrestdk.Payment.find(payment_id)

        transaction.status = "completed"
        transaction.save()
        cart = transcation.cart
        cart.paid = True
        cart.user = user
        cart.save()

        return Response({"message": 'Payment Successful', 'subMessage': 'You have successfully made payment for the items you purchased'})

    else: 
        return Response({"error": "Invalid payment details"}, status=400)