from flask import render_template, request, redirect, url_for
from app.main.forms import SubscriptionForm
from app.main import main
from app import api_client


@main.route('/subscription', methods=['GET', 'POST'])
def subscription():
    subscription_form = SubscriptionForm()

    if subscription_form.validate_on_submit():
        try:
            api_client.add_subscription_email(subscription_form.email.data)
            return redirect(url_for('.index'))
        except Exception as e:
            return render_template(
                'views/subscription.html',
                subscription_form=subscription_form,
                email=subscription_form.email.data,
                error=e
            )

    return render_template(
        'views/subscription.html',
        subscription_form=subscription_form,
        email=request.args['email'],
    )
