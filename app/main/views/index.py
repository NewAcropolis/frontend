from flask import current_app, render_template, redirect, url_for
from random import randint
from app.main.forms import SubscriptionForm
from app.main import main
from app import api_client


@main.route('/', methods=['GET', 'POST'])
def index():
    events = api_client.get_events_in_future(approved_only=True)
    for event in events:
        if event['event_type'] == 'Introductory Course':
            event['carousel_text'] = 'Courses starting {}'.format(event['event_monthyear'])
    past_events = api_client.get_events_past_year()
    articles = api_client.get_articles_summary()
    index = randint(0, len(articles) - 1)
    subscription_form = SubscriptionForm()

    if subscription_form.validate_on_submit():
        return redirect(url_for('main.subscription', email=subscription_form.email.data))

    return render_template(
        'views/home.html',
        images_url=current_app.config['IMAGES_URL'],
        main_article=articles[index],
        articles=articles,
        events=events,
        current_page='',
        subscription_form=subscription_form,
        email=subscription_form.email.data,
        past_events=past_events
    )

@main.route('/about')
def about():
    events = api_client.get_events_in_future(approved_only=True)
    for event in events:
        if event['event_type'] == 'Introductory Course':
            event['carousel_text'] = 'Courses starting {}'.format(event['event_monthyear'])

    articles = api_client.get_articles_summary()
    index = randint(0, len(articles) - 1)
    return render_template(
        'views/about.html',
        images_url=current_app.config['IMAGES_URL'],
        main_article=articles[index],
        articles=articles,
        events=events,
        current_page='about'
    )

@main.route('/resources')
def resources():
    subscription_form = SubscriptionForm()
    return render_template(
        'views/resources.html',
        current_page='resources',
        subscription_form=subscription_form
    )


@main.route('/whats-on')
def whats_on():
    subscription_form = SubscriptionForm()
    return render_template(
        'views/whats_on.html',
        current_page='whats-on',
        subscription_form=subscription_form
    )


@main.route('/what-we-offer')
def what_we_offer():
    subscription_form = SubscriptionForm()
    return render_template(
        'views/what_we_offer.html',
        current_page='what-we-offer',
        subscription_form=subscription_form
    )


@main.route('/e-shop')
def e_shop():
    subscription_form = SubscriptionForm()
    return render_template(
        'views/e-shop.html',
        current_page='e-shop',
        subscription_form=subscription_form
    )
