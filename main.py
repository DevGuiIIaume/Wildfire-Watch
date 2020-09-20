from flask import Flask, render_template, request, redirect, jsonify, session
from flask_simple_geoip import SimpleGeoIP
import json
import urllib.request
from flask_sqlalchemy import SQLAlchemy
import hashlib
import os
from flask_session import Session
from send_sms import send_sms
from api import API_KEY

app = Flask(__name__)
app.secret_key = os.urandom(24)
base = os.path.abspath(os.path.dirname(__file__))
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///" + os.path.join(base, 'app.db')
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db = SQLAlchemy(app)
# Session(app)


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), nullable=False)
    password = db.Column(db.String(255), nullable=False)
    zipCode1 = db.Column(db.Integer, nullable=False)
    zipCode2 = db.Column(db.Integer)
    zipCode3 = db.Column(db.Integer)
    phone = db.Column(db.String(25))

db.create_all()

# Get AQI at specified zip code
def getAqi(zip, distance="25"):
    try:
        url = "http://www.airnowapi.org/aq/observation/zipCode/current/?format=application/json&zipCode=" + str(zip) + "&distance=" + distance + "&API_KEY=" + API_KEY
        response = urllib.request.urlopen(url)
        data = response.read()
        response.close()
        text = data.decode(encoding='utf-8')
        data = json.loads(text)
        aqi = data[1]['AQI']
        return aqi
    except:
        return 0

def getGeo(zip, distance = "25"):
    try:
        url = "http://www.airnowapi.org/aq/observation/zipCode/current/?format=application/json&zipCode=" + str(zip) + "&distance=" + distance + "&API_KEY=" + API_KEY
        response = urllib.request.urlopen(url)
        data = response.read()
        response.close()
        text = data.decode(encoding='utf-8')
        data = json.loads(text)
        aqi = data[1]['ReportingArea']
        return aqi
    except:
        return 0

@app.route('/set/')
def set():
    session['uid'] = None
    return 'ok'

@app.route("/")
def home():
    # Get AQI of current location
    currAqi = getAqi("94122")

    # If logged in, show APIs for user's zip codes
    loggedIn = False
    if "uid" in session:
        loggedIn = True
    userAqis = {}
    if loggedIn:
        print("got here")
        #user = User.query.get(0)
        user = User.query.filter_by(username=session['uname']).first()
        if not user:
            print("no user")
        #zipCodes = [user.zipCode1, user.zipCode2, user.zipCode3]
        zipCodes = [session['zipCode1'], session['zipCode2'], session['zipCode3']]
        for zipCode in zipCodes:
            userAqis[zipCode] = getAqi(zipCode)
    return render_template("home.html", currAqi=currAqi, loggedIn=loggedIn, userAqis=userAqis)

@app.route("/signup", methods=["GET"])
def loadSignUp():
    return render_template("signUp.html")

@app.route("/signup", methods=["POST"])
def createUser():
    if request.method == "POST":
        try:
            userData = request.form.to_dict(flat=False)

            print(userData["zipCode1"][0])

            # Hash password
            salt = "5gz"
            password = userData["password"][0] + salt
            hashedPassword = hashlib.md5(password.encode()).hexdigest()

            newUser = User(username=userData["username"][0],
                            password=hashedPassword,
                            zipCode1=int(userData["zipCode1"][0]),
                            zipCode2=int(userData["zipCode2"][0]),
                            zipCode3=int(userData["zipCode3"][0]),
                            phone=userData["phone"][0])

            session['zipCode1'], session['zipCode2'], session['zipCode3'] = userData["zipCode1"][0], userData["zipCode2"][0], userData["zipCode3"][0]

            db.session.add(newUser)
            session['uid'] = User.query.filter_by(username=userData["username"][0]).first().id
            session['uname'] = userData["zipCode1"][0]
            #uid = newUser.id

            send_sms(userData["phone"][0], getAqi(userData["zipCode1"][0]))
        except Exception as e:
            pass
    return redirect("/")

@app.route("/login", methods=["GET"])
def loadLogin():
    return render_template("login.html", error="")

@app.route("/login", methods=["POST"])
def login():
    global uid
    if request.method == "POST":
        userData = request.form.to_dict(flat=False)

        # Hash password
        salt = "5gz"
        password = userData["password"][0] + salt
        hashedPassword = hashlib.md5(password.encode()).hexdigest()

        user = User.query.filter_by(username=userData["username"][0]).first()
        if user:
            if user.password == hashedPassword:
                session['uid'] = user.id
                return redirect("/")

    return render_template("login.html", error="Incorrect username/password")


@app.route("/", methods=["POST"])
def getNewZip():
    zipC = request.form["searchboxzip"]
    newZip = getAqi(zipC)
    p = getGeo(zipC)
    return render_template("home.html", z=newZip, pos=p)

@app.route("/logout")
def logout():
    session.pop('uid')
    return redirect("/")

@app.route("/aboutus")
def aboutUs():
    return render_template("aboutUs.html")

if __name__ == "__main__":
    app.run(debug=True)
