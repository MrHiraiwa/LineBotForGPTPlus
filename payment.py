import os
import stripe

STRIPE_SECRET_KEY = os.getenv('STRIPE_SECRET_KEY')

def create_checkout_session(line_user_id, price_id, success_url, cancel_url):
    stripe.api_key = STRIPE_SECRET_KEY

    try:
        session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            line_items=[{
                'price': price_id,
                'quantity': 1,
            }],
            mode='subscription',
            success_url=success_url,
            cancel_url=cancel_url,
            metadata={
                'line_user_id': line_user_id,
            },
        )
        return session.url

    except Exception as e:
        # エラーを標準出力に記録
        print(f"Error creating checkout session for user {line_user_id}: {e}")

        # Stripe固有のエラー情報があればそれも記録
        if hasattr(e, 'code'):
            print(f"Stripe error code: {e.code}")

        # エラーが発生した場合には None を返す
        return None
