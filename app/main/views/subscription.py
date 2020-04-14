from flask import current_app, request, session
from app.main.forms import SubscriptionForm
from app.main import main
from app.main.views import render_page
from app import api_client


@main.route('/subscription', methods=['GET', 'POST'])
def subscription():
    marketings = api_client.get_marketings()
    subscription_form = SubscriptionForm()
    subscription_form.setup(marketings)

    if subscription_form.validate_on_submit():
        try:
            api_client.add_subscription_email(
                subscription_form.subscription_name.data,
                subscription_form.subscription_email.data,
                subscription_form.subscription_marketings.data
            )
            return render_page(
                'views/subscription.html',
                subscription_form=subscription_form,
                done=True if 'error' not in session else False,
            )
        except Exception as e:
            current_app.logger.error('Problem subscribing email: %r', e)
            return render_page(
                'views/subscription.html',
                subscription_form=subscription_form,
                email=subscription_form.subscription_email.data,
                error=e.message
            )
    elif subscription_form.errors:
        return render_page(
            'views/subscription.html',
            subscription_form=subscription_form,
            email=subscription_form.subscription_email.data
        )

    return render_page(
        'views/subscription.html',
        subscription_form=subscription_form,
        email=request.args.get('email'),
    )
