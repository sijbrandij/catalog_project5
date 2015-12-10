from flask import Flask, render_template, url_for, request, redirect, flash, jsonify

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database_setup import Base, Category, Item, User

from flask import session as login_session
from flask.ext.seasurf import SeaSurf
import random, string

from oauth2client.client import flow_from_clientsecrets
from oauth2client.client import FlowExchangeError
import httplib2, json, requests, dicttoxml
from flask import make_response
from functools import wraps

app = Flask(__name__)
csrf = SeaSurf(app)

CLIENT_ID = json.loads(open('google_client_secrets.json', 'r').read())['web']['client_id']

engine = create_engine('sqlite:///catalogwithusers.db')
Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)
session = DBSession()

# Authentication

@app.route('/login')
def showLogin():
    state = ''.join(random.choice(string.ascii_uppercase + string.digits)
                    for x in xrange(32))
    login_session['state'] = state
    return render_template('login.html', STATE=state)

# Google authentication
@csrf.exempt
@app.route('/gconnect', methods=['POST'])
# This view is exempted from CSRF validation
def gconnect():
    # Validate state token
    if request.args.get('state') != login_session['state']:
        response = make_response(json.dumps('Invalid state parameter.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    # Obtain authorization code
    code = request.data

    try:
        # Upgrade the authorization code into a credentials object
        oauth_flow = flow_from_clientsecrets('google_client_secrets.json', scope='')
        oauth_flow.redirect_uri = 'postmessage'
        credentials = oauth_flow.step2_exchange(code)
    except FlowExchangeError:
        response = make_response(
            json.dumps('Failed to upgrade the authorization code.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Check that the access token is valid.
    access_token = credentials.access_token
    url = ('https://www.googleapis.com/oauth2/v1/tokeninfo?access_token=%s'
           % access_token)
    h = httplib2.Http()
    result = json.loads(h.request(url, 'GET')[1])
    # If there was an error in the access token info, abort.
    if result.get('error') is not None:
        response = make_response(json.dumps(result.get('error')), 500)
        response.headers['Content-Type'] = 'application/json'

    # Verify that the access token is used for the intended user.
    gplus_id = credentials.id_token['sub']
    if result['user_id'] != gplus_id:
        response = make_response(
            json.dumps("Token's user ID doesn't match given user ID."), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Verify that the access token is valid for this app.
    if result['issued_to'] != CLIENT_ID:
        response = make_response(
            json.dumps("Token's client ID does not match app's."), 401)
        print "Token's client ID does not match app's."
        response.headers['Content-Type'] = 'application/json'
        return response

    stored_credentials = login_session.get('access_token')
    stored_gplus_id = login_session.get('gplus_id')
    if stored_credentials is not None and gplus_id == stored_gplus_id:
        response = make_response(json.dumps('Current user is already connected.'),
                                 200)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Store the access token in the session for later use.
    login_session['access_token'] = credentials.access_token
    login_session['gplus_id'] = gplus_id

    # Get user info
    userinfo_url = "https://www.googleapis.com/oauth2/v1/userinfo"
    params = {'access_token': credentials.access_token, 'alt': 'json'}
    answer = requests.get(userinfo_url, params=params)

    data = answer.json()

    login_session['username'] = data['name']
    login_session['picture'] = data['picture']
    login_session['email'] = data['email']

    # Check if a user exists, otherwise make one.
    user_id = getUserID(login_session['email'])
    if not user_id:
        user_id = createUser(login_session)
    login_session['user_id'] = user_id

    output = ''
    output += '<h1>Welcome, '
    output += login_session['username']
    output += '!</h1>'
    output += '<img src="'
    output += login_session['picture']
    output += ' " style = "width: 300px; height: 300px;border-radius: 150px;-webkit-border-radius: 150px;-moz-border-radius: 150px;"> '
    flash("you are now logged in as %s" % login_session['username'])
    print "done!"
    return output

# Google disconnect
@app.route('/gdisconnect')
def gdisconnect():
    # Only disconnect a connected user.
    access_token = login_session.get('access_token')
    if access_token is None:
        response = make_response(
            json.dumps('Current user not connected.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    url = 'https://accounts.google.com/o/oauth2/revoke?token=%s' % access_token
    h = httplib2.Http()
    result = h.request(url, 'GET')[0]

    if result['status'] == '200':
        # Reset the user's session.
        del login_session['access_token']
        del login_session['gplus_id']
        del login_session['username']
        del login_session['email']
        del login_session['picture']

        response = make_response(json.dumps('Successfully disconnected.'), 200)
        response.headers['Content-Type'] = 'application/json'
        return response
    else:
        # For whatever reason, the given token was invalid.
        response = make_response(
            json.dumps('Failed to revoke token for given user.', 400))
        response.headers['Content-Type'] = 'application/json'
        return response



# API endpoints
@app.route('/categories/JSON')
def categoriesJSON():
    categories = session.query(Category).all()
    return jsonify(Categories=[category.serialize for category in categories])

@app.route('/categories/XML')
def categoriesXML():
    categories = session.query(Category).all()
    response = make_response(dicttoxml.dicttoxml([category.serialize for category in categories]))
    response.headers['Content-Type'] = 'text/xml'
    return response

@app.route('/categories/<int:category_id>/items/JSON')
def categoryItemsJSON(category_id):
    items = session.query(Item).filter_by(category_id = category_id).all()
    return jsonify(Items=[i.serialize for i in items])

@app.route('/categories/<int:category_id>/items/XML')
def categoryItemsXML(category_id):
    items = session.query(Item).filter_by(category_id = category_id).all()
    response = make_response(dicttoxml.dicttoxml([item.serialize for item in items]))
    response.headers['Content-Type'] = 'text/xml'
    return response

@app.route('/categories/<int:category_id>/items/<int:item_id>/JSON')
def itemJSON(category_id, item_id):
    item = session.query(Item).filter_by(id = item_id, category_id = category_id).one()
    return jsonify(Item=item.serialize)

@app.route('/categories/<int:category_id>/items/<int:item_id>/XML')
def itemXML(category_id, item_id):
    item = session.query(Item).filter_by(id = item_id, category_id = category_id).one()
    response = make_response(dicttoxml.dicttoxml([item.serialize]))
    response.headers['Content-Type'] = 'text/xml'
    return response

# Decorator
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # redirect to login screen when user is not logged in
        if 'username' not in login_session:
            return redirect(url_for('showLogin'))
        return f(*args, **kwargs)
    return decorated_function

# Routes
@app.route('/')
@app.route('/categories/')
def categories():
    categories = session.query(Category).all()
    # render the public template (without links to create/edit/delete) if there is no logged in user
    if 'username' not in login_session:
        return render_template('public_categories.html', categories = categories)
    else:
        return render_template('categories.html', categories = categories)

@app.route('/categories/new/', methods=['GET', 'POST'])
@login_required
def newCategory():
    # Create category if a post request is received, otherwise show form for new category
    if request.method == 'POST':
        newCategory = Category(name = request.form['name'], user_id = login_session['user_id'])
        session.add(newCategory)
        session.commit()
        flash("New category created")
        return redirect(url_for('categories'))
    else:
        return render_template('new_category.html')

@app.route('/categories/<int:category_id>/edit/', methods=['GET', 'POST'])
@login_required
def editCategory(category_id):
    category = session.query(Category).filter_by(id = category_id).one()
    if category.user_id != login_session['user_id']:
        # Show alert that user is not authorized to perform action if current user and category user don't match
        return "<script>function myFunction() { alert('You are not authorized to edit this category. Please create your own category in order to edit.');}</script><body onload='myFunction()''>"
    # update category if post request is received, otherwise show form to edit category
    if request.method == 'POST':
        if request.form['name'] != '':
          category.name = request.form['name']
          session.add(category)
          session.commit()
          flash("Category updated")
          return redirect(url_for('categories'))
    else:
        return render_template('edit_category.html', category = category)

@app.route('/categories/<int:category_id>/delete/', methods=['GET', 'POST'])
@login_required
def deleteCategory(category_id):
    category = session.query(Category).filter_by(id = category_id).one()
    # Show alert that user is not authorized to perform action if current user and category user don't match
    if category.user_id != login_session['user_id']:
        return "<script>function myFunction() { alert('You are not authorized to delete this category. Please create your own category in order to delete.');}</script><body onload='myFunction()''>"
    # delete category if post request is received, otherwise show form to delete category
    if request.method == 'POST':
      session.delete(category)
      session.commit()
      flash("Category deleted")
      return redirect(url_for('categories'))
    else:
        return render_template('delete_category.html', category = category)

@app.route('/categories/<int:category_id>/items/')
def items(category_id):
    category = session.query(Category).filter_by(id = category_id).first()
    items = session.query(Item).filter_by(category_id = category_id)
    # if there is no logged in user, show the public template, without links to create/edit/delete items
    if 'username' not in login_session or login_session['user_id'] != category.user_id:
        return render_template('public_items.html', category = category, items = items)
    else:
        return render_template('items.html', category = category, items = items)

@app.route('/categories/<int:category_id>/items/new/', methods=['GET', 'POST'])
@login_required
def newItem(category_id):
    category = session.query(Category).filter_by(id = category_id).one()
    # if the logged in user and the category's creator don't match, show alert and don't render the form
    if category.user_id != login_session['user_id']:
        return "<script>function myFunction() { alert('You are not authorized to create an item in this category. Please create your own category in order to create items.');}</script><body onload='myFunction()''>"
    # create the item if a post request is received, otherwise render the form.
    if request.method == 'POST':
        newItem = Item(name = request.form['name'], category_id = category_id, user_id = login_session['user_id'], description = request.form['description'], picture = request.form['picture'])
        session.add(newItem)
        session.commit()
        flash("Item created")
        return redirect(url_for('items', category_id = category_id))
    else:
        return render_template('new_item.html', category_id = category_id)

@app.route('/categories/<int:category_id>/items/<int:item_id>/edit/', methods=['GET', 'POST'])
@login_required
def editItem(category_id, item_id):
    item = session.query(Item).filter_by(id = item_id, category_id = category_id).one()
    # show alert if logged in user's id and item's user id don't match
    if item.user_id != login_session['user_id']:
        return "<script>function myFunction() { alert('You are not authorized to edit this item. Please create your own category and items in order to edit.');}</script><body onload='myFunction()''>"
    # update the item if a post request is received, otherwise render the edit form.
    if request.method == 'POST':
        item.name = request.form['name']
        item.description = request.form['description']
        item.picture = request.form['picture']
        session.add(item)
        session.commit()
        flash("Item updated")
        return redirect(url_for('items', category_id = category_id))
    else:
        return render_template('edit_item.html', category_id = category_id, item = item)

@app.route('/categories/<int:category_id>/items/<int:item_id>/delete/', methods=['GET', 'POST'])
@login_required
def deleteItem(category_id, item_id):
    item = session.query(Item).filter_by(id = item_id, category_id = category_id).one()
    # if the logged in user's id and the item's user id don't match, show an alert
    if item.user_id != login_session['user_id']:
        return "<script>function myFunction() { alert('You are not authorized to delete this item. Please create your own category and items in order to delete.');}</script><body onload='myFunction()''>"
    # delete the item if a post request is received, otherwise render the form to delete the item.
    if request.method == 'POST':
      session.delete(item)
      session.commit()
      flash("Item deleted")
      return redirect(url_for('items', category_id = category_id))
    else:
        return render_template('delete_item.html', category_id = category_id, item = item)

def getUserID(email):
    try:
        user = session.query(User).filter_by(email = email).one()
        return user.id
    except:
        return None

def getUserInfo(user_id):
    user = session.query(User).filter_by(id = user_id).one()
    return user

def createUser(login_session):
    newUser = User(name = login_session['username'], email = login_session['email'], picture = login_session['picture'])
    session.add(newUser)
    session.commit()
    user = session.query(User).filter_by(email = login_session['email']).one()
    return user.id

if __name__ == '__main__':
    app.secret_key = 'super_secret_key'
    app.debug = True
    app.run(host = '0.0.0.0', port = 5000)
