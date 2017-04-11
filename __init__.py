from flask import Flask, render_template, request
from flask import redirect, url_for, flash, jsonify, make_response
from flask import session as login_session
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database_setup import Base, Category, Item, User
import random
import string
import httplib2 
import json
import requests
from oauth2client.client import flow_from_clientsecrets
from oauth2client.client import FlowExchangeError
from functools import wraps
import os
APP_ROOT = os.path.dirname(os.path.abspath(__file__))
def getClientSecrets():
	return os.path.join(APP_ROOT, 'client_secrets.json')
def getFacebookSecrets():
	return os.path.join(APP_ROOT, 'fb_client_secrets.json')

app = Flask(__name__)

engine = create_engine('postgresql://catalog:catalog@localhost/catalog')
Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)
session = DBSession()

CLIENT_ID = json.loads(
	open(getClientSecrets(), 'r').read())['web']['client_id']

active = 'active'


def login_required(f):
	@wraps(f)
	def decorated_function(*args, **kwargs):
		if 'username' in login_session:
			return f(*args, **kwargs)
		else:
			flash("You must be logged in to access that page.")
			return redirect(url_for('login'))
	return decorated_function


# Make an API endpoint for individual items
@app.route('/catalog/<int:item_id>/item/JSON')
def itemJSON(item_id):
	item = session.query(Item).filter_by(id=item_id).one()
	return jsonify(Item=item.serialize)


# Make an API endpoint for all items in a category
@app.route('/catalog/<int:category_id>/category/JSON')
def categoryJSON(category_id):
	category = session.query(Category).filter_by(id=category_id).one()
	items = session.query(Item).filter_by(category_id=category_id).all()
	return jsonify(Item=[i.serialize for i in items])


@app.route('/')
@app.route('/catalog/')
def catalog():
	categories = session.query(Category).all()
	recent_items = session.query(Item).\
		order_by(Item.last_updated.desc()).limit(11).all()
	home_status = 'class=active'
	return render_template('catalog.html', 
							categories=categories, 
							recent_items=recent_items, 
							login_session=login_session, 
							home_status=active)


@app.route('/catalog/<int:category_id>/')
def catalogCategory(category_id):
	category = session.query(Category).filter_by(id=category_id).one()
	items = session.query(Item).filter_by(category_id=category_id).all()
	return render_template('category.html', 
							category=category, 
							items=items, 
							login_session=login_session)


@app.route('/catalog/<int:category_id>/<int:item_id>/')
def catalogItem(category_id, item_id):
	item = session.query(Item).filter_by(id=item_id).one()
	if 'user_id' in login_session:
		user_id = login_session['user_id']
		if user_id != item.user_id:
			return render_template('itemPublic.html', 
									item=item, 
									login_session=login_session)
		else: 
			return render_template('item.html', 
									item=item, 
									category_id=category_id, 
									login_session=login_session)
	else:
		return render_template('itemPublic.html', 
								item=item, 
								login_session=login_session)


@app.route('/catalog/login/')
def login():
	state = ''.join(random.choice(string.ascii_uppercase + string.digits) 
		for x in xrange(32))
	login_session['state'] = state
	return render_template('login.html', 
							STATE=state, 
							login_session=login_session, 
							login_status=active)


@app.route('/catalog/new/', methods=['GET', 'POST'])
@login_required
def newItem():
	if request.method == 'POST':
		if request.form['submit'] == 'Cancel':
			return redirect(url_for('catalog'))
		category = request.form['category']
		category_id = session.query(Category).filter_by(name=category).one().id
		newItem = Item(name=request.form['name'], 
						description=request.form['description'], 
						category_id=category_id,
						user_id=login_session['user_id'])
		session.add(newItem)
		session.commit()
		flash("new item added")
		return redirect(url_for('catalog'))
	else:
		return render_template('newItem.html', 
								login_session=login_session, 
								new_status=active)


@app.route('/catalog/<int:category_id>/<int:item_id>/edit/', methods=['GET', 'POST'])
@login_required
def editItem(item_id, category_id):
	if request.method == 'POST':
		update = session.query(Item).filter_by(id=item_id).one()
		if login_session['user_id'] != update.user_id:
			flash("You must be the owner of this item to edit it.")
			return redirect(url_for('catalogItem', 
									item_id=item_id, 
									category_id=update.category_id))
		else:
			if update.user_id == login_session['user_id']:
				if request.form['submit'] == 'Cancel':
					return redirect(url_for('catalogItem', 
											category_id=category_id, 
											item_id=item_id))
				elif update != []:
					category = request.form['category']
					category_id = session.query(Category).filter_by(name=category).one().id
					update.name = request.form['name']
					update.category_id = category_id
					update.description = request.form['description']
					session.add(update)
					session.commit()
					flash("Your changes were saved")
				return redirect(url_for('catalogItem', 
										category_id=category_id, 
										item_id=item_id))
			else:
				flash("You must be the creator to edit this item.")
				return redirect(url_for('login'))
	else:
		user_id = login_session['user_id']
		item = session.query(Item).filter_by(id=item_id).one()
		
		category = session.query(Category).filter_by(id=item.category_id).one()
		return render_template('editItem.html', 
								item=item, 
								category=category, 
								login_session=login_session)


@app.route('/catalog/<int:category_id>/<int:item_id>/delete/', methods=['GET', 'POST'])
@login_required
def deleteItem(category_id, item_id):
	if request.method == 'POST':
		delete = session.query(Item).filter_by(id=item_id).one()
		if login_session['user_id'] != delete.user_id:
			flash("You must be the owner of this item to delete it.")
			return redirect(url_for('catalogItem', 
									item_id=item_id, 
									category_id=delete.category_id))
		else:											
			if request.form['submit'] == 'Cancel':
				return redirect(url_for('catalogItem', 
										category_id=category_id, 
										item_id=item_id))
			elif delete != []:
				session.delete(delete)
				session.commit()
				flash("Your Item Has Been Deleted")
			return redirect(url_for('catalog'))
	else:
		item = session.query(Item).filter_by(id=item_id).one()
		category = session.query(Category).filter_by(id=item.category_id).one()
		return render_template('confirmDelete.html', 
								item=item, 
								category=category, 
								login_session=login_session)


@app.route('/disconnect')
def disconnect():
	if 'provider' in login_session:
		if login_session['provider'] == 'google':
			gdisconnect()
		elif login_session['provider'] == 'facebook':
			fbdisconnect()

		flash("You have successfully been logged out.")
		return redirect(url_for('catalog'))
	else:
		flash("You were not logged in to begin with!")
		return redirect(url_for('catalog'))


@app.route('/gconnect', methods=['POST'])
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
		oauth_flow = flow_from_clientsecrets(getClientSecrets(), scope='')
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
	result = json.loads(h.request(url, 'GET')[1].decode('utf8'))
	# If there was an error in the access token info, abort.
	if result.get('error') is not None:
		response = make_response(json.dumps(result.get('error')), 500)
		response.headers['Content-Type'] = 'application/json'
		return response

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

	stored_credentials = login_session.get('credentials')
	stored_gplus_id = login_session.get('gplus_id')
	if stored_credentials is not None and gplus_id == stored_gplus_id:
		response = make_response(json.dumps('Current user is already connected.'),
								200)
		response.headers['Content-Type'] = 'application/json'
		return response

	# Store the access token in the session for later use.
	login_session['credentials'] = credentials.access_token
	login_session['gplus_id'] = gplus_id
	login_session['provider'] = 'google'

	# Get user info
	userinfo_url = "https://www.googleapis.com/oauth2/v1/userinfo"
	params = {'access_token': credentials.access_token, 'alt': 'json'}
	answer = requests.get(userinfo_url, params=params)
	data = answer.json()

	login_session['username'] = data['name']
	login_session['picture'] = data['picture']
	login_session['email'] = data['email']

	user_id = getUserId(login_session['email'])
	if not user_id:
		user_id = createUser(login_session)
	login_session['user_id'] = user_id

	output = ''
	output += '<h1>Welcome, '
	output += login_session['username']
	output += '!</h1>'
	output += '<img src="'
	output += login_session['picture']
	output += ' " style = "width: 300px; height: 300px;'
	output += 'border-radius: 150px;-webkit-border-radius: 150px;'
	output += '-moz-border-radius: 150px;"> '
	flash("You are now logged in as %s" % login_session['username'])
	print "done!"
	return output


# DISCONNECT - Revoke a current user's token and reset their login_session.
@app.route('/gdisconnect')
def gdisconnect():
	# Only disconnect a connected user.
	credentials = login_session.get('credentials')
	if credentials is None:
		response = make_response(json.dumps('Current user not connected.'), 401)
		response.headers['Content-Type'] = 'application/json'
		return response
	# Execute HTTP GET request to revoke current token.
	access_token = credentials
	url = 'https://accounts.google.com/o/oauth2/revoke?token=%s' % access_token
	h = httplib2.Http()
	result = h.request(url, 'GET')[0]
	if result['status'] != '200':
		# For whatever reason, the given token was invalid.
		del login_session['provider']
		del login_session['user_id']
		del login_session['credentials']       
		del login_session['gplus_id']     
		del login_session['username']
		del login_session['email']
		response = make_response(
				json.dumps('Failed to revoke token for given user.'), 400)
		response.headers['Content-Type'] = 'application/json'
		return response


@app.route('/fbconnect', methods=['POST'])
def fbconnect():
	if request.args.get('state') != login_session['state']:
		response = make_response(json.dumps('Invalid state parameter.'), 401)
		response.headers['Content-Type'] = 'application/json'
		return response
	access_token = request.data

	# Exchange client token for long-lived server-side token with GET 
	# /oauth/access_token?grant_type=fb_exchange_token&client_id={app-id}
	# &client_secret={app.-secret}&fb_exchange_token={short-lived-token}
	app_id = json.loads(
		open(getFacebookSecrets(), 'r').read())['web']['app_id']
	app_secret = json.loads(
		open(getFacebookSecrets(), 'r').read())['web']['app_secret']

	url = 'https://graph.facebook.com/v2.8/oauth/access_token?grant_type=fb_'
	url += 'exchange_token&client_id='
	url += '%s&client_secret=%s&fb_exchange_token=%s' % (app_id, app_secret, access_token)
	h = httplib2.Http()
	result = h.request(url, 'GET')[1]

	# Strip expire tag from access token
	data = json.loads(result)
	token = 'access_token=' + data['access_token']

	url = "https://graph.facebook.com/v2.8/me?%s&fields=name,id,email" % token
	h = httplib2.Http()
	result = h.request(url, 'GET')[1]
	data = json.loads(result)
	login_session['provider'] = 'facebook'
	login_session['username'] = data['name']
	login_session['facebook_id'] = data['id']
	if data['email']:
		login_session['email'] = data['email']
	else:
		login_session['email'] = data['']

	# The token must be stored in the login_session 
	# in order to properly logout, let's strip out the 
	# information before the equals sign in our token
	stored_token = token.split('=')[1]
	login_session['access_token'] = stored_token

	# Get user picture
	url = 'https://graph.facebook.com/v2.8/me/'
	url += 'picture?%s&redirect=0&height=200&width=200' % token
	h = httplib2.Http()
	result = h.request(url, 'GET')[1]
	data = json.loads(result)

	login_session['picture'] = data["data"]['url']

	# see if user exists
	print(login_session['email'])
	user_id = getUserId(login_session['email'])
	if not user_id:
		user_id = createUser(login_session)
	login_session['user_id'] = user_id

	output = ''
	output += '<h1>Welcome, '
	output += login_session['username']
	output += '!</h1>'
	output += '<img src="'
	output += login_session['picture']
	output += ' " style = "width: 300px; height: 300px;border-radius: 150px;'
	output += '-webkit-border-radius: 150px;-moz-border-radius: 150px;"> '
	flash("You are now logged in as %s" % login_session['username'])
	print "done!"
	return output


@app.route('/fbdisconnect')	
def fbdisconnect():
	del login_session['username']   
	del login_session['email'] 
	del login_session['picture']
	del login_session['user_id']
	del login_session['provider']
	facebook_id = login_session['facebook_id']
	access_token = login_session['access_token']
	url = 'https://graph.facebook.com/'
	url += '%s/permissions?access_token=%s' % (facebook_id, access_token)
	h = httplib2.Http()
	result = h.request(url, 'DELETE')[1]
	return "you have been logged out"


def createUser(login_session):
	newUser = User(name=login_session['username'], 
					email=login_session['email'], 
					picture=login_session['picture'])
	session.add(newUser)
	session.commit()
	user = session.query(User).filter_by(email=login_session['email']).one()
	return user.id


def getUserInfo(user_id):
	user = session.query(User).filter_by(id=user_id).one()
	return user


def getUserId(email):
	try:
		if session.query(User).filter_by(email=email).one():
			print ('in if')
			user = session.query(User).filter_by(email=email).one()
			return user.id
		else:
			print ("in else")
			return None
	except:
		return None


if __name__ == '__main__':
	app.secret_key = 'super_secret_key'
	app.debug = True
	app.run(host='0.0.0.0', port=5000)
