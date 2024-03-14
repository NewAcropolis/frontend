from flask import render_template

from app.clients import BaseAPIClient


class PaypalClient(BaseAPIClient):
    def init_app(self, app, paypal_url):
        super(PaypalClient, self).init_app(app, base_url=paypal_url, client_id=None)

    def checkout(self, delivery_form, cart):
        data = {
            "first_name": delivery_form.first_name.data,
            "last_name": delivery_form.last_name.data,
            "address1": delivery_form.address1.data,
            "address2": delivery_form.address2.data,
            "city": delivery_form.city.data,
            "zip": delivery_form.zip.data,
        }

        return render_template(
            'views/checkout.html',
            data=data,
            cart=cart
        )
