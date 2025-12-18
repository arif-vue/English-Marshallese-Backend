import stripe
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
from .models import UserSubscription, Invoice

stripe.api_key = settings.STRIPE_SECRET_KEY


@csrf_exempt
def stripe_webhook(request):
    """Handle Stripe webhook events for subscription payments"""
    if request.method != "POST":
        return JsonResponse({'error': 'Method not allowed'}, status=405)
    
    payload = request.body
    sig_header = request.META.get('HTTP_STRIPE_SIGNATURE')
    
    if not sig_header:
        return JsonResponse({'error': 'Missing signature'}, status=400)
    
    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, settings.STRIPE_WEBHOOK_SECRET
        )
    except ValueError:
        return JsonResponse({'error': 'Invalid payload'}, status=400)
    except stripe.error.SignatureVerificationError:
        return JsonResponse({'error': 'Invalid signature'}, status=400)
    
    # Handle different event types
    event_type = event['type']
    
    if event_type == 'checkout.session.completed':
        session = event['data']['object']
        handle_checkout_completed(session)
    
    elif event_type == 'invoice.payment_succeeded':
        invoice = event['data']['object']
        handle_payment_succeeded(invoice)
    
    elif event_type == 'invoice.payment_failed':
        invoice = event['data']['object']
        handle_payment_failed(invoice)
    
    elif event_type == 'customer.subscription.deleted':
        subscription = event['data']['object']
        handle_subscription_deleted(subscription)
    
    return JsonResponse({'status': 'success'}, status=200)


def handle_checkout_completed(session):
    """Handle successful checkout session"""
    subscription_id = session.get('client_reference_id')
    
    if subscription_id:
        try:
            from django.utils import timezone
            from dateutil.relativedelta import relativedelta
            
            user_subscription = UserSubscription.objects.get(id=subscription_id)
            
            # Calculate subscription dates
            start_date = timezone.now()
            if user_subscription.plan.billing_cycle == 'monthly':
                end_date = start_date + relativedelta(months=1)
            else:  # yearly
                end_date = start_date + relativedelta(years=1)
            
            # Activate subscription with proper dates
            user_subscription.status = 'active'
            user_subscription.start_date = start_date
            user_subscription.end_date = end_date
            user_subscription.auto_renew = True
            user_subscription.save()
            
            # Create invoice
            Invoice.objects.create(
                user=user_subscription.user,
                subscription=user_subscription,
                amount=user_subscription.plan.price if user_subscription.plan else 0,
                currency='USD',
                payment_status='paid',
                stripe_session_id=session.get('id'),
                stripe_payment_intent=session.get('payment_intent'),
                paid_at=timezone.now()
            )
            
            print(f"Subscription {subscription_id} activated and invoice created")
        except UserSubscription.DoesNotExist:
            print(f"Subscription {subscription_id} not found")


def handle_payment_succeeded(invoice):
    """Handle successful payment"""
    customer_id = invoice.get('customer')
    if customer_id:
        try:
            user_subscription = UserSubscription.objects.filter(
                user__email=invoice.get('customer_email')
            ).first()
            if user_subscription:
                user_subscription.status = 'active'
                user_subscription.save()
                print(f"Payment succeeded for {invoice.get('customer_email')}")
        except Exception as e:
            print(f"Error handling payment: {e}")


def handle_payment_failed(invoice):
    """Handle failed payment"""
    customer_email = invoice.get('customer_email')
    if customer_email:
        try:
            user_subscription = UserSubscription.objects.filter(
                user__email=customer_email
            ).first()
            if user_subscription:
                user_subscription.status = 'expired'
                user_subscription.save()
                print(f"Payment failed for {customer_email}")
        except Exception as e:
            print(f"Error handling payment failure: {e}")


def handle_subscription_deleted(subscription):
    """Handle subscription cancellation"""
    customer_id = subscription.get('customer')
    if customer_id:
        try:
            # Find subscription by customer
            user_subscription = UserSubscription.objects.filter(
                status='active'
            ).first()
            if user_subscription:
                user_subscription.status = 'cancelled'
                user_subscription.save()
                print(f"Subscription cancelled")
        except Exception as e:
            print(f"Error handling cancellation: {e}")
