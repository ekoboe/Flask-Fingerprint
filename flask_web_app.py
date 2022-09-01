import time
import board
import busio
from digitalio import DigitalInOut, Direction
import adafruit_fingerprint
import random

import serial
uart = serial.Serial("/dev/ttyUSB0", baudrate=57600, timeout=1)

finger = adafruit_fingerprint.Adafruit_Fingerprint(uart)

##################################################
from flask import Flask, request, flash, session, url_for, redirect, render_template, jsonify
from flask_sqlalchemy import SQLAlchemy
import datetime
import RPi.GPIO as GPIO

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///user.sqlite3'
app.config['SECRET_KEY'] = "random string"
db = SQLAlchemy(app)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True)
    
db.create_all()

@app.route('/')
def login():
    return render_template('login.html')

@app.route('/loginProses', methods=['POST'])
def proses_login():
    name = request.form.get('name')
    user = User.query.filter_by(name=name).first()
    if not user:
        flash('This name does not exist')
        return redirect(url_for('login'))
        
    session['username'] = user.name

    return redirect(url_for('verifikasi'))

@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect(url_for('login'))

@app.route('/veriflogin1')
def get_fingerprint():
    """Get a finger print image, template it, and see if it matches!"""
    while finger.get_image() != adafruit_fingerprint.OK:
        pass
    if finger.image_2_tz(1) != adafruit_fingerprint.OK:
        return False
    if finger.finger_fast_search() != adafruit_fingerprint.OK:
        return False
    return True

@app.route('/veriflogin2')
def verifikasi():
    if get_fingerprint():
        return redirect(url_for('user'))
    else:
        flash('Failed, try again')
        return redirect(url_for('login'))

@app.route('/register')
def register():
    return render_template('register.html')

@app.route('/registerProses', methods=['POST'])
def proses_register():
    name = request.form.get('name')
   
    user = User.query.filter_by(name=name).first() 

    if user: 
        flash('Name already exist')
        return redirect(url_for('register'))

    new_user = User(name=name)

    
    db.session.add(new_user)
    db.session.commit()

    return redirect(url_for('tambah'))

@app.route('/enroll')
def enroll():
    return redirect(url_for('tambah'))
    
@app.route('/fungsienr')
def enroll_finger():
    location = random.randint(5, 127)
    for fingerimg in range(1, 3):
        if fingerimg == 1:
            pass
        else:
            pass

        while True:
            i = finger.get_image()
            if i == adafruit_fingerprint.OK:
                break
            elif i == adafruit_fingerprint.NOFINGER:
                pass
            elif i == adafruit_fingerprint.IMAGEFAIL:
                flash("Imaging error")
                return False
            else:
                flash("Other error")
                return False

        
        i = finger.image_2_tz(fingerimg)
        if i == adafruit_fingerprint.OK:
            pass
        else:
            if i == adafruit_fingerprint.IMAGEMESS:
                flash("Image too messy")
            elif i == adafruit_fingerprint.FEATUREFAIL:
                flash("Could not identify features")
            elif i == adafruit_fingerprint.INVALIDIMAGE:
                flash("Image invalid")
            else:
                flash("Other error")
            return False

        if fingerimg == 1:
            time.sleep(1)
            while i != adafruit_fingerprint.NOFINGER:
                i = finger.get_image()

    
    i = finger.create_model()
    if i == adafruit_fingerprint.OK:
        pass
    else:
        if i == adafruit_fingerprint.ENROLLMISMATCH:
            flash("Prints did not match")
        else:
            flash("Other error")
        return False

    
    i = finger.store_model(location)
    if i == adafruit_fingerprint.OK:
        flash("Stored in template %i" % location)
    else:
        if i == adafruit_fingerprint.BADLOCATION:
            flash("Bad storage location")
        elif i == adafruit_fingerprint.FLASHERR:
            flash("Flash storage error")
        else:
            flash("Other error")
        return False

    return True
    
@app.route('/tambah')
def tambah():
    if enroll_finger():
        return redirect(url_for('login'))
    else:
        flash('Failed, try again')
        return redirect(url_for('register'))
    
###############################################################
GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)

GPIO.setup(2, GPIO.OUT)
GPIO.output(2, GPIO.LOW)
##################################################################

@app.route('/index')
def user():
    return render_template('user.html', user = User.query.all())


@app.route('/find')
def find():
    if get_fingerprint():
        flash("Detected, template number %i" % finger.finger_id)
        return render_template('find.html', user = User.query.all())
    else:
        flash('Finger not found')
        return render_template('find.html', user = User.query.all())
    
@app.route('/enrollf')
def enrollf():
    if enroll_finger():
        return render_template('enroll.html', user = User.query.all())
    else:
        flash('Failed, try again')
        return render_template('enroll.html', user = User.query.all())
    
@app.route('/del')
def yyy():
    return render_template('delete.html', user = User.query.all())
    
@app.route('/delete', methods=['POST'])
def delete():
    if finger.delete_model(int(request.form.get('template'))) == adafruit_fingerprint.OK:
        flash("Deleted!")
    else:
        flash("Failed to delete")
    
    return render_template('delete.html', user = User.query.all())


@app.route('/door')
def door():
    return render_template('door.html', door = GPIO.input(2))

@app.route('/nyala')
def nyala():
    if get_fingerprint():
        GPIO.output(2, GPIO.HIGH)
        flash("Pintu dibuka oleh nomor %i" % finger.finger_id)
        return render_template('door.html', door = GPIO.input(2))
    else:
        flash("Sidik jari tidak sesuai, tidak dapat membuka pintu")
        return render_template('door.html', door = GPIO.input(2))

if __name__ == "__main__":
    app.run(debug=True, host='192.168.101.149', port=5000)