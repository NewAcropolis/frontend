from flask import current_app, jsonify, session
from app import api_client
from app.main import main
from app.main.views import render_page


@main.route('/e-shop')
def e_shop():
    return render_page('views/e-shop.html')


@main.route('/e-shop-static')
def e_shop_static():
    return render_page('views/e-shop-static.html')
