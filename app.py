import os
import sqlite3
from cs50 import SQL
from flask import Flask, flash, redirect, render_template, request, session , url_for
from flask_session import Session
from tempfile import mkdtemp
from werkzeug.security import check_password_hash, generate_password_hash
from datetime import datetime , timedelta
from pytz import timezone
from helpers import apology, login_required
import qrcode
import io
import base64
from PIL import Image, ImageDraw, ImageFont
from flask import send_file
from Functions import check_variable_if_exists, Check_existing_variable_on_table, Check_password_identically, Get_account_id_from_staff_by_Type, Get_account_id_from_users_by_Type, Get_account_id_from_admin_by_Type
import subprocess
import matplotlib.pyplot as plt
import numpy as np
import csv


# Configure application
app = Flask(__name__)



# Configure session to use filesystem (instead of signed cookies)
app.config['SESSION_COOKIE_NAME'] = 'your_cookie_name'
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Configure CS50 Library to use SQLite database
db = SQL("sqlite:///Database.db")



@app.after_request
def after_request(response):
    """Ensure responses aren't cached"""
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response

#Workers Accounts
Developer_account = {0}
Admin_accounts = Get_account_id_from_admin_by_Type("Admin")
Receptionist_accounts = Get_account_id_from_staff_by_Type("Receptionist")
Nurse_accounts = Get_account_id_from_staff_by_Type("Nurse")
Accountant_accounts = Get_account_id_from_staff_by_Type("Accountant")
Patient_accounts = Get_account_id_from_users_by_Type("Patient")

# Qeries for Qouta
# Admin SELECT id FROM users WHERE TYPE = "Admin";
# Receptionist SELECT id FROM users WHERE TYPE = "Receptionist";
# Nurse SELECT id FROM users WHERE TYPE = "Nurse";
# Accountant SELECT id FROM users WHERE TYPE = "Accountant";

@app.context_processor
def sessions():
    session['user_developer'] = Developer_account
    session['user_admin'] = Admin_accounts
    session['user_receptionist'] = Receptionist_accounts
    session['user_nurse'] = Nurse_accounts
    session['user_accountant'] = Accountant_accounts
    session['user_patient'] = Patient_accounts
    return dict()


@app.route("/", methods=["GET"])
def index():

    # Getting Quota validation date
    Quota_valid_date = db.execute("SELECT Quota_date FROM Quota WHERE Quota_loaded = ?", ("Loaded",))[0]['Quota_date']
    timestamp = datetime.now().date().strftime("%Y-%m-%d")
    if timestamp > str(Quota_valid_date):
        message_1 = "Your website is down !\n" "Your Quota has expired"
        return render_template("/index.html", message_1 = message_1)
    else:
        message_2 = "Your website is on !\n" f"Your Quota is valid until:  {Quota_valid_date}"
        return render_template("/index.html", message_2 = message_2)

#Developer pages
@app.route("/Developer_access",methods=["GET","POST"])
@login_required
def developer_access():
    if session['user_id'] not in Developer_account:
        return render_template("/")

    if request.method == "GET":
        return render_template("Developer_access.html")

    username = request.form.get("username")
    password = request.form.get("password")
    password_check = 'HemaCodingLLC'

    if username == "HemaCodingLLC" and password == password_check:
        return redirect("/Developer_page")
    else:
        return render_template("Developer_access.html", message = "Username or password Invalid")

@app.route("/Developer_page",methods=["GET","POST"])
@login_required
def developer_page():
    if session['user_id'] not in Developer_account:
        return render_template("/")

    if request.method == "GET":
        return render_template("Developer_page.html")

    terminal = request.form.get("Terminal")
    if terminal != None:
        conn = sqlite3.connect('Database.db')
        cursor = conn.cursor()
        cursor.execute(terminal)
        query_results = cursor.fetchall()
        column_names = [description[0] for description in cursor.description]
        conn.close()

        return render_template("Developer_page.html", output=query_results, columns=column_names)

    Quota_changed = request.form.get("New_Quota")
    db.execute("UPDATE Quota SET Quota_name = ? WHERE Quota_loaded = ?",Quota_changed,"Loaded")
    Active_Quota = db.execute("SELECT * FROM Quota WHERE Quota_loaded = ?","Loaded")[0]['Quota_name']
    return render_template("Developer_page.html", output=query_results, columns=column_names, Active_Quota = Active_Quota)

@app.route("/Quota",methods=["GET","POST"])
@login_required
def Quota():
    if session['user_id'] not in Developer_account:
        return render_template("/")

    Active_Quota = db.execute("SELECT * FROM Quota WHERE Quota_loaded = ?","Loaded")[0]['Quota_name']
    Quota_valid_date_old = db.execute("SELECT * FROM Quota WHERE Quota_loaded = ?", "Loaded")[0]['Quota_date']
    time = datetime.now().date().strftime("%Y-%m-%d")
    if time < Quota_valid_date_old:
        if request.method == "GET":
            return render_template("Quota.html", Active_Quota = Active_Quota, Quota_valid_date_old = Quota_valid_date_old)
    else:
        if request.method == "GET":
            return render_template("Quota.html", Active_Quota = Active_Quota, Quota_valid_date_old_2 = Quota_valid_date_old)

    # Developer change Quota Type & date
    Quota_changed = request.form.get("New_Quota")
    Quota_valid_date = request.form.get("Quota_valid_date")

    if Quota_changed == None and Quota_valid_date == None:
        return render_template("Quota.html", message_1 = "Invalid Input",Active_Quota = Active_Quota, Quota_valid_date_old = Quota_valid_date_old)

    if Quota_changed == None and Quota_valid_date == None:
        return render_template("Quota.html", message_1 = "Invalid Input",Active_Quota = Active_Quota, Quota_valid_date_old = Quota_valid_date_old)

    if Quota_changed != None and Quota_valid_date == None:
        db.execute("UPDATE Quota SET Quota_name = ? WHERE Quota_loaded = ?",Quota_changed, "Loaded")
        Active_Quota = db.execute("SELECT * FROM Quota WHERE Quota_loaded = ?","Loaded")[0]['Quota_name']
        return render_template("Quota.html", message_2 = "Successfully Changed Quota",Active_Quota = Active_Quota, Quota_valid_date_old = Quota_valid_date_old)

    if Quota_changed == None and Quota_valid_date != None:
        db.execute("UPDATE Quota SET Quota_date = ? WHERE Quota_loaded = ?", Quota_valid_date, "Loaded")
        Quota_valid_date = db.execute("SELECT * FROM Quota WHERE Quota_loaded = ?", "Loaded")[0]['Quota_date']
        return render_template("Quota.html", message_2 = "Successfully Renewed Quota",Active_Quota = Active_Quota, Quota_valid_date = Quota_valid_date)

# Admin pages
@app.route("/modify_doctors",methods=["GET","POST"])
@login_required
def modify():

    if session['user_id'] not in Admin_accounts:
        return render_template("/")
    else:
        #Getting all doctors name
        Doctors_available = db.execute("SELECT * FROM Doctors")
        Doctors_specialty = db.execute("SELECT * FROM Doctors_specialty")
        if request.method == "GET":
            return render_template("modify_doctors.html",Doctors_available = Doctors_available,Doctors_specialty=Doctors_specialty)

        #Getting admin input
        new_doctor_name = request.form.get("Doctor_name")
        new_doctor_specialty = request.form.get("Doctor_specialty")
        Days_available = request.form.get("Days_available")
        removed_doctor_name = request.form.get("Doctor_removed")
        new_doctor_price = request.form.get("Doctor_price")
        Doctor_day_modified = request.form.get("Doctor_day_modified")
        Doctor_new_days = request.form.get("Doctor_new_days")
        Doctor_price_modified = request.form.get("Doctor_price_modified")
        Doctor_new_price = request.form.get("Doctor_new_price")

        #check if admin no inputs
        if new_doctor_name == None and new_doctor_specialty == None and Days_available == None and new_doctor_price == None and removed_doctor_name == None  and Doctor_day_modified == None and Doctor_new_days == None and Doctor_price_modified == None and Doctor_new_price == None:
            return render_template("modify_doctors.html",message_2= "Invalid Input",Doctors_available = Doctors_available,Doctors_specialty=Doctors_specialty)

        #Remove Doctor
        if new_doctor_name == None and new_doctor_specialty == None and Days_available == None and new_doctor_price == None and removed_doctor_name != None and Doctor_day_modified == None and Doctor_new_days == None and Doctor_price_modified == None and Doctor_new_price == None:

            #removing Doctor and it's appointments
            db.execute("DELETE FROM Doctors WHERE Doctor_name = ?",removed_doctor_name)
            db.execute("DELETE FROM patient_reservation WHERE patient_doctor_reservation =?",removed_doctor_name)
            db.execute("DELETE FROM Doctor_query WHERE Doctor_name = ?",removed_doctor_name)
            New_doctors = db.execute("SELECT * FROM Doctors")
            return render_template("modify_doctors.html",message_3="Doctor Removed Successfully",Doctors_available = New_doctors,Doctors_specialty=Doctors_specialty)

        #Modify Doctor days
        if new_doctor_name == None and new_doctor_specialty == None and Days_available == None and removed_doctor_name == None and new_doctor_price == None and Doctor_new_days != None and Doctor_price_modified == None and Doctor_new_price == None:

            # Check if doctor didn't selected
            if Doctor_day_modified == None:
                return render_template("modify_doctors.html",message_5="you must select doctor",Doctors_available = Doctors_available,Doctors_specialty=Doctors_specialty)

            #check new days is valid
            days_entered = Doctor_new_days.split()
            for i in range(0 , len(days_entered) , 1):
                day_check = db.execute("SELECT * FROM Week_date WHERE Week_days LIKE '%' || ? || '%'",days_entered[i])
                if len(day_check) == 0 or Doctor_new_days == '':
                    return render_template("modify_doctors.html",message_6="you must add Valid days",Doctors_available = Doctors_available,Doctors_specialty=Doctors_specialty)

            # Update doctor days
            db.execute("UPDATE Doctors SET Days_available = ? WHERE Doctor_name = ?",Doctor_new_days, Doctor_day_modified)
            New_doctors = db.execute("SELECT * FROM Doctors")
            return render_template("modify_doctors.html",message_5=f"Doctor {Doctor_day_modified} Days Modified Successfully",Doctors_available = New_doctors,Doctors_specialty=Doctors_specialty)

        # Modify Doctor price
        if new_doctor_name == None and new_doctor_specialty == None and Days_available == None and removed_doctor_name == None and new_doctor_price == None and Doctor_day_modified == None and Doctor_new_days == None and Doctor_new_price != None:

            # Check if doctor isn't selected
            if Doctor_price_modified == None:
                return render_template("modify_doctors.html",message_8="you must select doctor",Doctors_available = Doctors_available,Doctors_specialty=Doctors_specialty)

            #check price is valid
            if Doctor_new_price.isnumeric() == False:
                return render_template("modify_doctors.html",message_8="Invalid Price",Doctors_available = Doctors_available,Doctors_specialty=Doctors_specialty)

            # Update Doctor price
            db.execute("UPDATE Doctors SET Doctor_price = ? WHERE Doctor_name = ?",Doctor_new_price,Doctor_price_modified)
            New_doctors = db.execute("SELECT * FROM Doctors")
            return render_template("modify_doctors.html",message_7=f"Doctor {Doctor_price_modified} Price Modified Successfully",Doctors_available = New_doctors,Doctors_specialty=Doctors_specialty)

        # ADD New Doctor
        if new_doctor_name != None and Days_available != None and new_doctor_price != None and removed_doctor_name == None  and Doctor_day_modified == None and Doctor_new_days == None and Doctor_price_modified == None and Doctor_new_price == None:

            # Check if Doctor specialy
            if new_doctor_specialty == None:
                return render_template("modify_doctors.html",message_2 = "you must select doctor specialty",Doctors_available = Doctors_available,Doctors_specialty=Doctors_specialty)

            #check Doctor_name if it's numeric
            if new_doctor_name.isdigit() == True:
                return render_template("modify_doctors.html",message_2 = "the doctor name cannot have numbers",Doctors_available = Doctors_available,Doctors_specialty=Doctors_specialty)

            #check Doctor_name if exists
            Doctor_name_check = db.execute("SELECT * FROM Doctors WHERE Doctor_name = ?",new_doctor_name)
            if len(Doctor_name_check) == 1:
                return render_template("modify_doctors.html",message_2="the doctor name has been already taken",Doctors_available = Doctors_available,Doctors_specialty=Doctors_specialty)

            #check if the specialty is founded
            specialty = db.execute("SELECT * FROM Doctors_specialty WHERE Doctors_specialty = ?",new_doctor_specialty)
            if len(specialty) != 1:
                return render_template("modify_doctors.html",message_2="you must add the doctor specialty first",Doctors_available = Doctors_available,Doctors_specialty=Doctors_specialty)

            #check if the days is invalid
            days_entered = Days_available.split()
            for i in range(0 , len(days_entered) , 1):
                day_check = db.execute("SELECT * FROM Week_date WHERE Week_days LIKE '%' || ? || '%'",days_entered[i])
                if len(day_check) == 0 or Days_available == '':
                    return render_template("modify_doctors.html",message_2="you must add Valid days",Doctors_available = Doctors_available,Doctors_specialty=Doctors_specialty)

            #check if price is non-numeric
            if new_doctor_price.isnumeric() == False:
                return render_template("modify_doctors.html",message_2="Invalid Price",Doctors_available = Doctors_available,Doctors_specialty=Doctors_specialty)

            #Add new doctor
            db.execute("INSERT INTO Doctors (Doctor_name, Doctor_specialty , Days_available, doctor_price) VALUES (?,?,?,?)",new_doctor_name,new_doctor_specialty,Days_available,new_doctor_price)
            db.execute("INSERT INTO Doctor_query (Doctor_name) VALUES(?)",new_doctor_name)
            New_doctors_available = db.execute("SELECT * FROM Doctors")
            return render_template("modify_doctors.html",message_1="Doctor Added Successfully",Doctors_available = New_doctors_available,Doctors_specialty=Doctors_specialty)


@app.route("/modify_staff_accounts",methods=["GET","POST"])
@login_required
def modify_staff_accounts():


    if session['user_id'] not in Admin_accounts:
        return render_template("/")

    Quota = db.execute("SELECT * FROM Quota")[0]
    staff_users_name = db.execute("SELECT * FROM users WHERE TYPE NOT IN (?,?) ORDER BY TYPE",("Patient",),("HemaCodingLLC",))
    staff_users_name_deleted = db.execute("SELECT * FROM users WHERE TYPE NOT IN (?,?,?) ORDER BY TYPE",("Patient",),("HemaCodingLLC",),("Admin",))
    staff_account_type = {"Admin","Receptionist","Nurse","Accountant"}

    # Getting page
    if request.method == "GET":
        return render_template("modify_staff_accounts.html",staff_users_name = staff_users_name, staff_account_type = staff_account_type, Quota = Quota, staff_users_name_deleted = staff_users_name_deleted)

    # Getting admin inputs
    staff_account_modified = request.form.get("account_modified")
    staff_account_type = request.form.get("account_type")
    new_username = request.form.get("new_username")
    new_email = request.form.get("new_email")
    new_phonenumber = request.form.get("new_phonenumber")
    new_address = request.form.get("new_address")
    new_age = request.form.get("new_age")
    password = request.form.get("password")
    password_confirmation = request.form.get("confirmation")
    deleted_staff_account = request.form.get("account_deleted")

    if staff_account_modified == None and staff_account_type == None and deleted_staff_account == None:
        return render_template("modify_staff_accounts.html",message = "Invalid inputs !",staff_users_name = staff_users_name, staff_account_type = staff_account_type, Quota = Quota, staff_users_name_deleted = staff_users_name_deleted)

    if staff_account_modified != None and staff_account_type != None and deleted_staff_account != None:
        return render_template("modify_staff_accounts.html",message = "You cannot edit and create accounts at the same time !",staff_users_name = staff_users_name, staff_account_type = staff_account_type, Quota = Quota, staff_users_name_deleted = staff_users_name_deleted)

    if deleted_staff_account != None:

        # Admin Delete staff account
        db.execute("DELETE FROM users WHERE username = ? AND TYPE NOT IN (?,?,?)",deleted_staff_account,("Patient",),("HemaCodingLLC",),("Admin",))
        staff_users_name = db.execute("SELECT * FROM users WHERE TYPE NOT IN (?,?) ORDER BY TYPE",("Patient",),("HemaCodingLLC",))
        return render_template("modify_staff_accounts.html",staff_users_name = staff_users_name, staff_account_type = staff_account_type, Quota = Quota, staff_users_name_deleted = staff_users_name_deleted)

    if staff_account_modified != None:

        #Admin modify staff account
        Variables_list = [staff_account_modified ,new_username, new_email, new_phonenumber, new_address, new_age]
        Variables_name = ["staff_account_modified" ,"username" , "Email" , "Phone_number" , "Address" , "Age"]

        # Blank Inputs
        if check_variable_if_exists(Variables_list,Variables_name,0,5,"/modify_staff_accounts.html"):
            return check_variable_if_exists(Variables_list,Variables_name,0,5,"/modify_staff_accounts.html")

        # Get user_id
        user_id = db.execute("SELECT * FROM users WHERE username = ?",staff_account_modified)

        # Update account data
        db.execute("UPDATE users SET username = ?, Email = ?, Phone_number = ?, ADRESS = ?, Age = ? WHERE username = ?", new_username, new_email, new_phonenumber, new_address, new_age, staff_account_modified)

        # Getting all staff usersname
        staff_users_name = db.execute("SELECT * FROM users WHERE TYPE NOT IN (?,?) ORDER BY TYPE",("Patient",),("HemaCodingLLC",))

        return render_template("modify_staff_accounts.html",staff_users_name = staff_users_name, Quota = Quota, staff_users_name_deleted = staff_users_name_deleted)

    if staff_account_type != None:

        # Admin create staff account
        account_type = request.form.get("account_type")

        #Admin modify staff account
        Variables_list = [account_type ,new_username, new_email, new_phonenumber, new_address, new_age, password, password_confirmation]
        Variables_name = ["account_type" ,"username" , "Email" , "Phone_number" , "Address" , "Age" , "password" , "password_confirmation"]
        Variables_name_Table = ["account_type" ,"username" , "Email" , "Phone_number" , "Address" , "Age" , "password" , "password_confirmation"]

        # Blank Inputs
        if check_variable_if_exists(Variables_list,Variables_name,0,8,"/modify_staff_accounts.html"):
            return check_variable_if_exists(Variables_list,Variables_name,0,8,"/modify_staff_accounts.html")

        # Check Password & it's confirmation not the same
        if Check_password_identically(password,password_confirmation,"Password",7,"/modify_staff_accounts.html"):
            return Check_password_identically(password,password_confirmation,"Password",7,"/modify_staff_accounts.html")

        # Check if data already exists
        if Check_existing_variable_on_table(Variables_list,Variables_name,1,4,Variables_name_Table,"users","/modify_staff_accounts.html"):
            return Check_existing_variable_on_table(Variables_list,Variables_name,1,4,Variables_name_Table,"users","/modify_staff_accounts.html")

        # Password hashing
        password = generate_password_hash(password)

        # Account Data insertion
        db.execute("INSERT INTO users (username,hash,Phone_number,AGE,ADRESS,Email,TYPE) VALUES (?)", (new_username, password,new_phonenumber,new_age,new_address,new_email,account_type))
        staff_users_name = db.execute("SELECT * FROM users WHERE TYPE NOT IN (?,?) ORDER BY TYPE",("Patient",),("HemaCodingLLC",))
        return render_template("modify_staff_accounts.html", message_10 = "Staff Account Added Successfully",staff_users_name = staff_users_name, staff_account_type = staff_account_type, Quota = Quota, staff_users_name_deleted = staff_users_name_deleted)

@app.route("/modify_specialties",methods = ["GET","POST"])
@login_required
def modify_specialties():
    if session['user_id'] not in Admin_accounts:
        return render_template("/")

    #Getting specialties information
    specialties = db.execute("SELECT * FROM Doctors_specialty")

    #admin gets page by "GET"
    if request.method == "GET":
        return render_template("modify_specialties.html", specialties=specialties)

    #Getting user inputs
    specialty_removed = request.form.get("specialty_removed")
    specialty_add = request.form.get("specialty_add")

    #check if input is blank
    if specialty_removed == None and specialty_add == None:
        return render_template("modify_specialties.html",message = "No input data", specialties=specialties)

    elif specialty_removed != None and specialty_add != None:
        return render_template("modify_specialties.html",message = "You cannot add & remove at the same time", specialties=specialties)

    #Admin remove specialty
    elif specialty_removed != None and specialty_add == None:

        #specialty deletion
        db.execute("DELETE FROM Doctors_specialty WHERE Doctors_specialty = ?",specialty_removed)

        #getting the new list of specialties
        specialties = db.execute("SELECT * FROM Doctors_specialty")
        return render_template("modify_specialties.html",message = "Specialty Removed successfully", specialties=specialties)

    #Admin add specialty
    else:

        #check if specialty added blank or multiple times
        if specialty_add.isalpha() == False:
            return render_template("modify_specialties.html",message = "Invalid specialty input", specialties=specialties)

        #check if specialty added multiple times
        specialty_check = db.execute("SELECT * FROM Doctors_specialty WHERE Doctors_specialty = ?",specialty_add)[0]['Doctors_specialty']
        if len(specialty_check) != 0:
            return render_template("modify_specialties.html",message = "This specialty already exists", specialties=specialties)

        #specialty add
        db.execute("INSERT INTO Doctors_specialty(Doctors_specialty) VALUES(?)",specialty_add)

        #getting the new list of specialties
        specialties = db.execute("SELECT * FROM Doctors_specialty")
        return render_template("modify_specialties.html",message = "Specialty Added successfully", specialties=specialties)


@app.route("/delete_patient", methods=["GET","POST"])
@login_required
def delete_patient():
    if session['user_id'] not in Admin_accounts:
        return render_template("/")

    #Getting patients accounts
    patient_information = db.execute("SELECT * FROM users  WHERE TYPE = ?","Patient")

    if request.method == "GET":
        return render_template("delete_patient.html",patient_information = patient_information)

    account_name_delete = request.form.get("account_name_delete")

    #check if admin blank input
    if account_name_delete == None :
        return render_template("delete_patient.html",message = "Enter Account username to Delete",patient_information = patient_information)

    #search account result
    db.execute("DELETE FROM users WHERE username = ?",account_name_delete)
    db.execute("DELETE FROM Patients WHERE patient_name = ?",account_name_delete)
    db.execute("DELETE FROM patient_reservation WHERE patient_name = ?",account_name_delete)
    patient_information = db.execute("SELECT * FROM users WHERE TYPE = ?","Patient")
    return render_template("delete_patient.html",message = "Account deleted succussfully" ,patient_information = patient_information)


@app.route("/Search_Refund", methods = ["GET", "POST"])
@login_required
def search_refund():
    if session['user_id'] not in Admin_accounts:
        return redirect("/")

    Accountants_name = db.execute("SELECT username FROM users WHERE TYPE = ?", "Accountant")
    if request.method == "GET":

        # GETTING PAGE
        return render_template("Search_refund.html", Accountants_name = Accountants_name)

    # Getting user inputs
    Date_from = request.form.get("Date_from")
    Date_to = request.form.get("Date_to")
    Accountant_name = request.form.get("Accountant_name")

    return redirect(url_for("Refund"), Date_from, Date_to, Accountant_name)

@app.route("/Refund", methods = ["GET", "POST"])
@login_required
def refund():
    if session['user_id'] not in Admin_accounts:
        return redirect("/")

    if request.method == "GET":
        Accountant_name = request.args.get("Accountant_name")
        Date_from = request.args.get("Date_from")
        Date_to = request.args.get("Date_to")
        reservations_reviewed = db.execute("SELECT * FROM patient_reservation_reviewed WHERE Time_stamp > ? AND Time_stamp < ? AND accountant_name = ?", Date_from, Date_to, Accountant_name)
        return render_template("Refund.html", reservations_reviewed = reservations_reviewed, Accountant_name = Accountant_name, Date_from = Date_from, Date_to= Date_to)

    # Getting user reservation selection to refund
    Refunded_reservation_id = request.form.get("Refunded_reservation")

    # Getting user reservations
    Accountant_name = request.form.get("Accountant_name")
    Date_from = request.form.get("Date_from")
    Date_to = request.form.get("Date_to")

    # Remove from patient_reservation_reviewed & Update patient_reservation_checked & patient_reservation status
    db.execute("DELETE FROM patient_reservation_reviewed WHERE reservation_id = ?", Refunded_reservation_id)
    db.execute("UPDATE patient_reservation_checked SET reservation_status = ? WHERE reservation_id = ?", "Checked", Refunded_reservation_id)
    db.execute("UPDATE patient_reservation SET reservation_status = ? WHERE reservation_id = ?", "Checked", Refunded_reservation_id)
    reservations_reviewed = db.execute("SELECT * FROM patient_reservation_reviewed WHERE Time_stamp > ? AND Time_stamp < ? AND accountant_name = ?", Date_from, Date_to, Accountant_name)

    return render_template("Refund.html", reservations_reviewed = reservations_reviewed, Accountant_name = Accountant_name, Date_from = Date_from, Date_to= Date_to)


# Receptionist pages
@app.route("/reservation_patient",methods=["GET","POST"])
@login_required
def reservation_patient():
    if session['user_id'] not in Receptionist_accounts:
        return redirect("/")

    #getting all specialties available
    Doctors_specialty = db.execute("SELECT Doctors_specialty FROM doctors_specialty")
    if request.method == "GET":

        return render_template("reservation_patient.html",Doctors=Doctors_specialty)

    #getting data from user
    specialty = request.form.get("doctor_specialty")
    if specialty == None:
        return render_template("reservation_patient.html",message = "Cannot search with select Doctor specialty",Doctors=Doctors_specialty)
    day = request.form.get("doctor_day")
    return redirect(url_for('reservated_patient', specialty = specialty, day = day))

@app.route("/reservated_patient", methods=["GET","POST"])
@login_required
def reservated_patient():
    """Get stock quote."""
    if session['user_id'] not in Receptionist_accounts:
        return redirect("/")

    patients_name = db.execute("SELECT patient_name FROM patients")
    specialty = request.args.get("specialty")
    day = request.args.get("day")
    # If user gets page by get
    if request.method == "GET":
        if day == None:
            Doctor_searched = db.execute("SELECT * FROM Doctors WHERE Doctor_specialty = ?",specialty)
            return render_template("our_doctors_patient.html",Doctors = Doctor_searched, patients=patients_name)

        Doctor_searched = db.execute("SELECT * FROM Doctors WHERE Doctor_specialty = ? AND Days_available LIKE '%' || ? || '%'",specialty,day)
        return render_template("our_doctors_patient.html",Doctors = Doctor_searched, patients = patients_name)


@app.route("/our_doctors_patient", methods=["GET","POST"])
@login_required
def our_doctors_patient():
    if session['user_id'] not in Receptionist_accounts:
        return redirect("/")

    #query all of doctors
    Doctors = db.execute("SELECT * FROM Doctors")
    patients_name = db.execute("SELECT patient_name FROM patients")
    # If user gets page by get
    if request.method == "GET":
        return render_template("our_doctors_patient.html",Doctors = Doctors,patients=patients_name)


    Reserved_Doctor = request.form.get("doctor_name")
    if Reserved_Doctor == None:
        return render_template("our_doctors_patient.html",message = "Cannot make a reservation without select Doctor",Doctors = Doctors,patients=patients_name)
    Patient_name = request.form.get("patient_name")
    if Patient_name == None:
        return render_template("our_doctors_patient.html",message = "Cannot make a reservation without select Patient",Doctors = Doctors,patients=patients_name)

    Patient_id = db.execute("SELECT patient_id FROM patients WHERE patient_name = ?",Patient_name)[0]['patient_id']
    Reserved_Doctor_specialty = db.execute("SELECT * FROM Doctors WHERE doctor_name = ?",Reserved_Doctor)[0]['Doctor_specialty']
    day = request.form.get("doctor_day")
    if day == None:
        return render_template("our_doctors_patient.html",message = "Cannot make a reservation without select Day",Doctors = Doctors,patients=patients_name)
    #check if the doctor has already reserved
    Doctor_name = db.execute("SELECT * FROM patient_reservation WHERE patient_doctor_reservation = ? AND patient_id = ?",Reserved_Doctor,Patient_id)
    if len(Doctor_name) != 0:
        return render_template("our_doctors_patient.html",message = "cannot reserve the same doctor multiple times",Doctors = Doctors,patients=patients_name)
    #check if the day is not in the list of doctor
    Doctor_day = db.execute("SELECT * FROM Doctors WHERE Doctor_name = ? AND Days_available LIKE '%' || ? || '%'",Reserved_Doctor,day)
    if len(Doctor_day) == 0:
        return render_template("our_doctors_patient.html",message = "cannot reserve this doctor at that day",Doctors = Doctors,patients=patients_name)
    #reserve a doctor
    else:
        receptionist_name = db.execute("SELECT username FROM users WHERE id = ?",session['user_id'])[0]['username']
        db.execute("INSERT INTO patient_reservation (patient_id,patient_name, patient_doctor_reservation,patient_doctor_specialty,patient_doctor_date_time,receptionist_name,reservation_status) VALUES (?)",(Patient_id,Patient_name,Reserved_Doctor,Reserved_Doctor_specialty,day,receptionist_name,"Unchecked"))
        db.execute("UPDATE patient_reservation SET patient_query = ( SELECT CASE patient_doctor_date_time WHEN 'Saturday' THEN Doctor_Saturday_queue WHEN 'Sunday' THEN Doctor_Sunday_queue WHEN 'Monday' THEN Doctor_Monday_queue WHEN 'Tuesday' THEN Doctor_Tuesday_queue WHEN 'Wednesday' THEN Doctor_Wednesday_queue WHEN 'Thursday' THEN Doctor_Thursday_queue WHEN 'Friday' THEN Doctor_Friday_queue  ELSE patient_query END FROM Doctor_query WHERE patient_reservation.patient_doctor_reservation = Doctor_query.Doctor_name ) WHERE patient_name = ?",Patient_name)
        Doctors = db.execute("SELECT Doctors.Doctor_name, Doctors.Doctor_specialty,patient_reservation.patient_query, patient_reservation.patient_doctor_date_time, patient_reservation.reservation_id, patient_reservation.Time_stamp FROM Doctors JOIN patient_reservation ON Doctors.Doctor_name == patient_reservation.patient_doctor_reservation WHERE patient_reservation.patient_id = ?",Patient_id)
        return render_template("myappointments.html",Doctors=Doctors)

@app.route("/patientinformation", methods=["GET","POST"])
@login_required
def patientinformation():
    if session['user_id'] not in Receptionist_accounts:
        return redirect("/")

    #query all patients names
    patients_name = db.execute("SELECT patient_name FROM Patients")


    if request.method == "GET":
        return render_template("patientinformation.html")

    #getting search information
    patient_name = request.form.get("patient_name")
    patient_phonenumber = request.form.get("patient_phonenumber")
    patient_age = request.form.get("patient_age")
    appoint_cancellation = request.form.get("cancel_appointment")

    #check if user wants to cancel appointment patient
    if patient_name == None and patient_phonenumber == None and patient_age == None:

        #check if user didn't select doctor to remove appointment
        if appoint_cancellation == None:
            return render_template("patientinformation.html",message = "you must input data")



    #getting information from database
    patient_data = db.execute("SELECT * FROM Patients WHERE patient_name LIKE '%' || ? || '%' AND patient_phonenumber LIKE '%' || ? || '%' AND patient_age LIKE '%' || ? || '%'",patient_name,patient_phonenumber,patient_age)


    #cancel appointment
    if appoint_cancellation != None:
        if patient_name == None and patient_phonenumber == None and patient_age == None:
            return render_template("patientinformation.html",message="you must input patient_name")

        else:

            db.execute("DELETE FROM patient_reservation WHERE patient_doctor_reservation = ? AND patient_name = ?",appoint_cancellation,patient_name)
            return render_template("patientinformation.html")

    #check if name not exists
    if len(patient_data) == 0:
        return render_template("patientinformation.html",message = "There is no patient information")

    #Getting information from data base
    patient_name_data = patient_data[0]['patient_name']
    patient_appointments = db.execute("SELECT * FROM patient_reservation WHERE patient_name = ? AND reservation_status = ?","Unchecked",patient_name_data)
    Doctors_appointed = db.execute("SELECT patient_doctor_reservation FROM patient_reservation WHERE patient_name = ?",patient_name_data)
    return render_template("patientinformation.html",patient_data = patient_data,patient_appointments = patient_appointments)

@app.route("/view_patients_reservation",methods=["GET","POST"])
@login_required
def view_patients_reservation():
    if session['user_id'] not in Receptionist_accounts:
        return redirect("/")
    Reservation_data = db.execute("SELECT * FROM patient_reservation")

    if request.method == "GET":
        return render_template("view_patients_reservation.html",Reservation_data=Reservation_data)
    else:
        #query patients reservations
        return render_template("view_patients_reservation.html")

@app.route("/Review_reservated", methods = ["GET", "POST"])
@login_required
def Review_reservated():
    if session['user_id'] not in Receptionist_accounts:
        return redirect("/")

    if request.method == "GET":
        timestamp = 8
        Late_Reservations = db.execute("SELECT * FROM patient_reservation WHERE patient_reservation.reservation_status = ? AND DATE(patient_reservation.Time_stamp) <= DATE('now', '-8 day')", ("Reserved",) )
        Late_Reservations = db.execute("SELECT * FROM Patients JOIN patient_reservation WHERE patient_reservation.reservation_status = ? AND Patients.patient_name = patient_reservation.patient_name AND DATE(patient_reservation.Time_stamp) <= DATE('now', '-8 day')", ("Reservated",))
        return render_template("Review_reservated.html", Late_Reservations = Late_Reservations)



#Nurse pages
@app.route("/Doctor_clinc",methods=["GET","POST"])
@login_required
def Doctor_clinc():
    if session['user_id'] not in Nurse_accounts:
        return redirect("/")

    # Getting doctor name & doctor day
    Doctors = db.execute("SELECT * FROM Doctors")


    # Getting page by "GET"
    if request.method == "GET":
        return render_template("Doctor_clinc.html",Doctors_name = Doctors)


    Doctor_clinc = request.form.get("Doctor_clinc")
    day = request.form.get("doctor_day")

    if Doctor_clinc == None or day == None:
        return render_template("Doctor_clinc.html",Doctors_name = Doctors)

    return redirect(url_for('Doctor_clinc_reservations', Doctor_clinc = Doctor_clinc , day = day))

@app.route("/Doctor_clinc_reservations",methods=["GET","POST"])
@login_required
def Doctor_clinc_reservations():
    if session['user_id'] not in Nurse_accounts:
        return redirect("/")


    Doctor_clinc = request.args.get("Doctor_clinc")
    day = request.args.get("day")
    # Getting Doctor reservations at specific day
    Doctors = db.execute("SELECT * FROM patient_reservation WHERE reservation_status = ? AND patient_doctor_reservation = ? AND patient_doctor_date_time = ?","Unchecked",Doctor_clinc,day)


    # Getting doctor reservations from past page
    if request.method == "GET":
        return render_template("Doctor_clinc_reservations.html",Doctors = Doctors,Doctor_clinc = Doctor_clinc, day = day)


    patient_query = request.form.get("patient_query")
    Doctor_clinc = request.form.get("Doctor_clinc")
    day = request.form.get("day")

    # Getting Doctor reservations at specific day
    Doctors = db.execute("SELECT * FROM patient_reservation WHERE reservation_status = ? AND patient_doctor_reservation = ? AND patient_doctor_date_time = ?","Unchecked",Doctor_clinc,day)
    db.execute("UPDATE patient_reservation SET reservation_status = ? WHERE patient_query = ? AND patient_doctor_reservation = ? AND patient_doctor_date_time = ?","Checked",patient_query,Doctor_clinc,day)
    Doctors = db.execute("SELECT * FROM patient_reservation WHERE reservation_status = ? AND patient_doctor_reservation = ? AND patient_doctor_date_time = ?","Unchecked",Doctor_clinc,day)
    Doctor_price = db.execute("SELECT Doctor_price FROM Doctors WHERE Doctor_name = ?",Doctor_clinc)[0]['Doctor_price']
    Nurse_name = db.execute("SELECT username FROM users WHERE id = ?",session['user_id'])[0]['username']
    db.execute("INSERT INTO patient_reservation_checked (patient_id, patient_name, patient_doctor_reservation, patient_doctor_date_time, patient_doctor_specialty, doctor_price, reservation_id, patient_query, patient_reserved, receptionist_name, nurse_name) SELECT patient_id, patient_name, ?, ?, patient_doctor_specialty, ?, reservation_id, ?, patient_reserved, receptionist_name, ? FROM patient_reservation WHERE patient_query = ? AND patient_doctor_reservation = ? AND patient_doctor_date_time = ?",Doctor_clinc,day,Doctor_price,patient_query,Nurse_name,patient_query,Doctor_clinc,day)
    return render_template("Doctor_clinc_reservations.html",Doctors = Doctors,Doctor_clinc = Doctor_clinc, day = day)


# Accountant Pages
@app.route("/check_reservations_date", methods=["GET","POST"])
@login_required
def check_reservations():
    if session['user_id'] not in Accountant_accounts:
        return render_template("/")

    # Accountant gets page by GET
    if request.method == "GET":
        Doctors_name = db.execute("SELECT * FROM Doctors")
        Receptionists_name = db.execute("SELECT username FROM users WHERE TYPE = ?","Receptionist")
        Nurses_name = db.execute("SELECT username FROM users WHERE TYPE = ?","Nurse")
        return render_template("check_reservations.html", Doctors_name = Doctors_name, Receptionists_name = Receptionists_name, Nurses_name = Nurses_name)

    Date_from = request.form.get("Date_from")
    Date_to = request.form.get("Date_to")
    Doctor_name = request.form.get("Doctor_name")
    Receptionist_name = request.form.get("Receptionist_name")
    Nurse_name = request.form.get("Nurse_name")

    return redirect("/review_reservations", Date_from, Date_to, Doctor_name, Receptionist_name, Nurse_name)

@app.route("/review_reservations", methods=["GET","POST"])
@login_required
def review_reservations():
    if session['user_id'] not in Accountant_accounts:
        return render_template("/")

    if request.method == "GET":
        Date_from = request.args.get("Date_from")
        Date_to = request.args.get("Date_to")
        Doctors_name = request.args.get("Doctor_name")
        Receptionists_name = request.args.get("Receptionist_name")
        Nurses_name = request.args.get("Nurse_name")

        reservations_checked = db.execute("SELECT * FROM patient_reservation_checked WHERE reservation_status = ? AND Time_stamp >= ? AND Time_stamp <= ? OR patient_doctor_reservation = ? OR receptionist_name = ? OR nurse_name = ?", "Checked", Date_from, Date_to, Doctors_name, Receptionists_name, Nurses_name)

        if len(reservations_checked) == 0:
            Doctors_name = db.execute("SELECT * FROM Doctors")
            Receptionists_name = db.execute("SELECT username FROM users WHERE TYPE = ?","Receptionist")
            Nurses_name = db.execute("SELECT username FROM users WHERE TYPE = ?","Nurse")
            return render_template("check_reservations.html",message = "Invalid input or not found reservations at that time", Doctors_name = Doctors_name, Receptionists_name = Receptionists_name, Nurses_name = Nurses_name)

        return render_template("reservation_id_review.html",reservations_checked = reservations_checked)

    if request.method == "POST":
        Date_from = request.form.get("Date_from")
        Date_to = request.form.get("Date_to")
        reservation_id_reviewed = request.form.get("reservation_id_reviewed")
        accountant_name = db.execute("SELECT username FROM users WHERE id = ?",session['user_id'])[0]['username']

        # Update the checked table & insert into new table
        db.execute("UPDATE patient_reservation_checked SET reservation_status = ? WHERE reservation_id = ?","Reviewed",reservation_id_reviewed)
        db.execute("UPDATE patient_reservation SET reservation_status = ? WHERE reservation_id = ?","Reviewed",reservation_id_reviewed)
        db.execute("INSERT INTO patient_reservation_reviewed (patient_id, patient_name, patient_doctor_reservation, patient_doctor_date_time, patient_doctor_specialty, doctor_price, nurse_name, receptionist_name, accountant_name, reservation_id, patient_query) SELECT patient_id, patient_name, patient_doctor_reservation, patient_doctor_date_time, patient_doctor_specialty, doctor_price, nurse_name, receptionist_name, ?, reservation_id, patient_query FROM patient_reservation_checked WHERE reservation_id = ?", accountant_name, reservation_id_reviewed)
        reservations_checked = db.execute("SELECT * FROM patient_reservation_checked WHERE reservation_status = ?", "Checked")
        return render_template("reservation_id_review.html",reservations_checked = reservations_checked)

@app.route("/reviewed_reservations", methods=["GET","POST"])
@login_required
def reviewed_reservations():
    if session['user_id'] not in Accountant_accounts:
        return render_template("/")

    # Getting date range from user
    if request.method == "GET":

        return render_template("reviewed_reservations.html")

    # Getting user inputs
    Date_from = request.form.get("Date_from")
    Date_to = request.form.get("Date_to")

    # Getting reservations_reviewed
    reservations_reviewed = db.execute("SELECT * FROM patient_reservation_reviewed WHERE Time_stamp >= ? AND Time_stamp <= ?",Date_from,Date_to)

    # Excel data
    rows = reservations_reviewed
    Reservation_id = [row['reservation_id'] for row in rows]
    Receptionist_name = [row['receptionist_name'] for row in rows]
    Nurse_Name = [row['nurse_name'] for row in rows]
    patient_doctor_reservation = [row['patient_doctor_reservation'] for row in rows]
    doctor_price = [row['doctor_price'] for row in rows]
    Time_stamp = [row['Time_stamp'] for row in rows]

    # Calculate sum of reservations
    Sum_of_reservations_total = db.execute("SELECT SUM(Doctor_price) FROM patient_reservation_reviewed WHERE Time_stamp >= ? AND Time_stamp <= ?",Date_from,Date_to)[0]['SUM(Doctor_price)']

    # Making csv
    header = ["Reservation ID" , "Receptionist Name", "Nurse Name" , "Doctor Name" , "Doctor Price" , "Time Stamp"]

    List = [None] * len(Reservation_id)
    for i in range(0, len(Reservation_id), 1):
        List[i] = [Reservation_id[i], Receptionist_name[i],Nurse_Name[i], patient_doctor_reservation[i], doctor_price[i], Time_stamp[i]]

    footers = ["Total Cash" , "","","", Sum_of_reservations_total]

    # Getting current time for the file name
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")

    # Getting account name
    Accountant_name = db.execute("SELECT * FROM users WHERE id = ?",session['user_id'])[0]['username']

    # Making csv file
    csv_file_save_location = f'/workspaces/104943996/Problem_sets/Final_Project/hospital/csv_files/ Reviewed Reservations Accountant name {Accountant_name} Date-{timestamp}.csv'
    with open(csv_file_save_location, 'w', encoding='UTF8', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(header)
        writer.writerows(List)
        writer.writerow(footers)

    # Check no reservations
    if len(reservations_reviewed) == 0:
        return render_template("reviewed_reservations.html",message = "There is no reservations to be checked in this period", reservations_reviewed = reservations_reviewed)
    return render_template("reviewed_reservations.html", reservations_reviewed = reservations_reviewed, Sum_of_reservations_total = Sum_of_reservations_total)


@app.route("/Doctors_evaluation", methods=["GET","POST"])
@login_required
def Doctors_evaluation():
    if session['user_id'] not in Accountant_accounts:
        return render_template("/")

    # Getting date range from user
    if request.method == "GET":

        return render_template("Doctors_evaluation.html")

    # Getting user inputs
    Date_from = request.form.get("Date_from")
    Date_to = request.form.get("Date_to")

    # Getting reservations_reviewed
    reservations_reviewed = db.execute("SELECT * FROM patient_reservation_reviewed WHERE Time_stamp >= ? AND Time_stamp <= ?",Date_from,Date_to)

    # Calculate sum of reservations
    Sum_of_reservations_total = db.execute("SELECT SUM(Doctor_price) FROM patient_reservation_reviewed WHERE Time_stamp >= ? AND Time_stamp <= ?",Date_from,Date_to)[0]['SUM(Doctor_price)']

    # Calculate sum of reservations per doctor
    rows = db.execute("SELECT DISTINCT(patient_doctor_reservation) AS Doctor_name, SUM(Doctor_price) AS Doctor_price, COUNT(reservation_id) AS Doctor_reservations FROM patient_reservation_reviewed WHERE Time_stamp >= ? AND Time_stamp <= ? GROUP BY patient_doctor_reservation ORDER BY patient_doctor_reservation", Date_from, Date_to)

    # Prepare the data for the graph
    doctor_names = [row['Doctor_name'] for row in rows]
    doctor_reservations = [row['Doctor_reservations'] for row in rows]
    doctor_prices = [row['Doctor_price'] for row in rows]
    header = ["Doctor name", "Doctor Reservations", "Doctor Price"]
    List = [None] * len(doctor_names)
    for i in range(0, len(doctor_names), 1):
        List[i] = [doctor_names[i], doctor_reservations[i], doctor_prices[i]]

    # Generate a timestamp for the current time
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")

    # Getting accountant name
    Accountant_name = db.execute("SELECT username FROM users WHERE id = ?",session['user_id'])[0]['username']

    # Define location of new csv
    csv_save_location = f'/workspaces/104943996/Problem_sets/Final_Project/hospital/csv_files/ Doctors Evaluation Accountant name {Accountant_name} Date-{timestamp}.csv'

    # Make csv file for the Evaluation table
    with open(csv_save_location, 'w', encoding='UTF8', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(header)
        writer.writerows(List)

    # Create the bar graph
    fig, ax = plt.subplots()
    ax.bar(doctor_names, doctor_prices, label='Doctor Prices')

    # Set labels and title
    ax.set_xlabel('Doctor Name')
    ax.set_ylabel('Doctor Share')
    ax.set_title('Doctor Reservations and Prices')

    # Add legend
    ax.legend()

    # Define the save location for the graphs
    save_location = '/workspaces/104943996/Problem_sets/Final_Project/hospital/Graphs/'

    # Save the bar graph to a file
    bar_graph_file = 'bar_graph.png'
    plt.savefig(bar_graph_file, format='png')

    # Encode the bar graph image in base64
    with open(bar_graph_file, 'rb') as file:
        bar_graph_data = file.read()
    bar_graph_url = base64.b64encode(bar_graph_data).decode()

    # Specify the save location and filename for the bar graph
    bar_graph_save_location = f"{save_location}bar_graph_{timestamp}.png"
    plt.savefig(bar_graph_save_location, format='png')

    # Create the pie graph
    fig, ax = plt.subplots()
    y = np.array(doctor_reservations)
    labels = [row['Doctor_name'] for row in rows]
    ax.pie(y, labels=labels, shadow=True)
    ax.set_title('Doctor Reservations')

    # Add legend
    ax.legend(title='Doctor Share')

    # Save the pie graph to a file
    pie_graph_file = 'pie_graph.png'
    plt.savefig(pie_graph_file, format='png')

    # Encode the pie graph image in base64
    with open(pie_graph_file, 'rb') as file:
        pie_graph_data = file.read()
    pie_graph_url = base64.b64encode(pie_graph_data).decode()

    # Specify the save location and filename for the pie graph
    pie_graph_save_location = f"{save_location}pie_graph_{timestamp}.png"
    plt.savefig(pie_graph_save_location, format='png')

    # Check no reservations
    if len(reservations_reviewed) == 0:
        return render_template("Doctors_evaluation.html",message = "There is no reservations to be checked in this period", reservations_reviewed = reservations_reviewed)

    return render_template("Doctors_evaluation.html", reservations_reviewed = reservations_reviewed,Sum_of_reservations_total = Sum_of_reservations_total, List = rows, graph_url=bar_graph_url , graph_url_2 = pie_graph_url)

@app.route("/Unchecked_nurse", methods = ["GET","POST"])
@login_required
def Unchecked_nurse():
    if session['user_id'] not in Accountant_accounts:
        return render_template("/")

    # Getting table FROM patient_reservation_checked
    if request.method == "GET":
        Nurses_name = db.execute("SELECT * FROM users WHERE TYPE = ?","Nurse")
        return render_template("Unchecked_nurse.html", Nurses_name = Nurses_name)

    # Getting Date_from Date_to
    Date_from = request.form.get("Date_from")
    Date_to = request.form.get("Date_to")
    Nurse_name = request.form.get("Nurse_name")



    return redirect(url_for("checked_nurse"), Date_from, Date_to, Nurse_name)

@app.route("/checked_nurse", methods = ["GET", "POST"])
@login_required
def checked_nurse():
    if session['user_id'] not in Accountant_accounts:
        return render_template("/")

    if request.method == "GET":

        # Getting from last page
        Date_from = request.args.get("Date_from")
        Date_to = request.args.get("Date_to")
        Nurse_name = request.args.get("Nurse_name")

        # Search table
        Reservations = db.execute("SELECT * FROM patient_reservation_checked WHERE nurse_name = ? AND Time_stamp >= ? AND Time_stamp <= ?", Nurse_name, Date_from, Date_to)
        return render_template("checked_nurse.html", Reservations = Reservations, Nurse_name = Nurse_name, Date_from = Date_from, Date_to = Date_to)


    Reservation_id = request.form.get("Reservation_id")
    Nurse_name = request.form.get("Nurse_name")
    Date_from = request.form.get("Date_from")
    Date_to = request.form.get("Date_to")
    # Search table
    Reservations = db.execute("SELECT * FROM patient_reservation_checked WHERE nurse_name = ? AND Time_stamp >= ? AND Time_stamp <= ?", Nurse_name, Date_from, Date_to)

    if Reservation_id == None:
        return render_template("checked_nurse.html", message = "Invalid Input", Reservations = Reservations)

    # Check if this reservation already reviewed
    Review_check = db.execute("SELECT * FROM patient_reservation_reviewed WHERE reservation_id = ?", Reservation_id)
    if len(Review_check) != 0:
        return render_template("checked_nurse.html", message = "This Reservation has been reviewed contact administrator to refund it first", Reservations = Reservations, Nurse_name = Nurse_name, Date_from = Date_from, Date_to = Date_to)

    # Delete From checked reservations & update patient_reservation status "Unchecked"
    db.execute("DELETE FROM patient_reservation_checked WHERE reservation_id = ?", Reservation_id)
    db.execute("UPDATE patient_reservation SET reservation_status = ? WHERE reservation_id = ?", "Unchecked", Reservation_id)
    return render_template("checked_nurse.html", message = "Successfully Unchecked Reservation", Reservations = Reservations)


#Client pages
@app.route("/reservation",methods=["GET","POST"])
@login_required
def reservation():

    if session['user_id'] not in Patient_accounts:
        return render_template("/")

    Doctors_specialty = db.execute("SELECT Doctors_specialty FROM doctors_specialty")
    if request.method == "GET":
        return render_template("reservation.html",Doctors=Doctors_specialty)

    #getting data from user
    specialty = request.form.get("doctor_specialty")
    if specialty == None:
        return render_template("reservation.html",message = "Cannot make a reservation without select Doctor specialty",Doctors=Doctors_specialty)
    day = request.form.get("doctor_day")
    return redirect(url_for('reservated', specialty = specialty, day = day))

@app.route("/reservated", methods=["GET","POST"])
def reservated():
    """Get stock quote."""

    specialty = request.args.get("specialty")
    day = request.args.get("day")
    # If user gets page by get
    if request.method == "GET":
        if day == None:
            Doctor_searched = db.execute("SELECT * FROM Doctors WHERE Doctor_specialty = ?",specialty)
            return render_template("our_doctors.html",Doctors = Doctor_searched)

        Doctor_searched = db.execute("SELECT * FROM Doctors WHERE Doctor_specialty = ? AND Days_available LIKE '%' || ? || '%'",specialty,day)
        return render_template("our_doctors.html",Doctors = Doctor_searched)

@app.route("/myappointments", methods=["GET"])
@login_required
def myappointments():

    if session['user_id'] not in Patient_accounts:
        return render_template("/")

    #query the patient appointments
    Patient_id = db.execute("SELECT * FROM Patients WHERE user_id = ?",session['user_id'])

    #check if patient new account
    if len(Patient_id) == 0:
        return render_template("myappointments.html")
    Patient_id = Patient_id[0]['patient_id']
    Doctors = db.execute("SELECT * FROM Doctors JOIN patient_reservation ON Doctors.Doctor_name == patient_reservation.patient_doctor_reservation WHERE patient_reservation.patient_id = ?",Patient_id)
    return render_template("myappointments.html",Doctors=Doctors)

#All Access pages
@app.route("/our_doctors", methods=["GET","POST"])
def our_doctors():


    #query all of doctors
    Doctors = db.execute("SELECT * FROM Doctors")

    if 'user_id' in session:
        #query patient data
        Patient_DATA = db.execute("SELECT * FROM Patients WHERE user_id = ?",session['user_id'])
        Patient_id = Patient_DATA[0]['patient_id']
        Patient_name = Patient_DATA[0]['patient_name']

    # If user gets page by get
    if request.method == "GET":
        return render_template("our_doctors.html",Doctors = Doctors)


    Reserved_Doctor = request.form.get("doctor_name")
    if Reserved_Doctor == None:
        return render_template("our_doctors.html",message = "Cannot make a reservation without select Doctor",Doctors = Doctors)
    Reserved_Doctor_specialty = db.execute("SELECT * FROM Doctors WHERE doctor_name = ?",Reserved_Doctor)[0]['Doctor_specialty']
    day = request.form.get("doctor_day")
    if day == None:
        return render_template("our_doctors.html",message = "Cannot make a reservation without selecting Day",Doctors = Doctors)
    #check if the doctor has already reserved
    Doctor_name = db.execute("SELECT * FROM patient_reservation WHERE patient_doctor_reservation = ? AND patient_id = ?",Reserved_Doctor,Patient_id)
    if len(Doctor_name) != 0:
        return render_template("our_doctors.html",message = "cannot reserve the same doctor multiple times",Doctors = Doctors)
    #check if the day is not in the list of doctor
    Doctor_day = db.execute("SELECT * FROM Doctors WHERE Doctor_name = ? AND Days_available LIKE '%' || ? || '%'",Reserved_Doctor,day)
    if len(Doctor_day) == 0:
        return render_template("our_doctors.html",message = "cannot reserve this doctor at that day",Doctors = Doctors)
    #reserve a doctor
    else:
        patient_reserved = db.execute("SELECT username FROM users WHERE id = ?",session['user_id'])[0]['username']
        db.execute("INSERT INTO patient_reservation (patient_id,patient_name, patient_doctor_reservation,patient_doctor_specialty,patient_doctor_date_time,patient_reserved) VALUES (?)",(Patient_id,Patient_name,Reserved_Doctor,Reserved_Doctor_specialty,day,patient_reserved))
        db.execute("UPDATE patient_reservation SET patient_query = ( SELECT CASE patient_doctor_date_time WHEN 'Saturday' THEN Doctor_Saturday_queue WHEN 'Sunday' THEN Doctor_Sunday_queue WHEN 'Monday' THEN Doctor_Monday_queue WHEN 'Tuesday' THEN Doctor_Tuesday_queue WHEN 'Wednesday' THEN Doctor_Wednesday_queue WHEN 'Thursday' THEN Doctor_Thursday_queue WHEN 'Friday' THEN Doctor_Friday_queue  ELSE patient_query END FROM Doctor_query WHERE patient_reservation.patient_doctor_reservation = Doctor_query.Doctor_name ) WHERE patient_name = ?",Patient_name)
        Doctors = db.execute("SELECT Doctors.Doctor_name, Doctors.Doctor_specialty,patient_reservation.patient_query, patient_reservation.patient_doctor_date_time, patient_reservation.reservation_id, patient_reservation.Time_stamp FROM Doctors JOIN patient_reservation ON Doctors.Doctor_name == patient_reservation.patient_doctor_reservation WHERE patient_reservation.patient_id = ?",Patient_id)
        return render_template("myappointments.html",Doctors=Doctors)


@app.route("/get_your_ticket",methods=["GET","POST"])
@login_required
def get_ticket():

    #For the users
    if session['user_id'] not in Receptionist_accounts and session['user_id'] in Patient_accounts:
        #getting user doctors_reservated
        #query the patient appointments
        Patient_id = db.execute("SELECT * FROM Patients WHERE user_id = ?",session['user_id'])[0]['patient_id']
        Patient_name = db.execute("SELECT * FROM Patients WHERE user_id = ?",session['user_id'])[0]['patient_name']
        doctors_reservated = db.execute("SELECT patient_doctor_reservation FROM patient_reservation WHERE patient_id = ? AND reservation_status = ?",Patient_id,"Reservated")
        patient_age = db.execute("SELECT patient_age FROM Patients WHERE patient_id = ?",Patient_id)
        if request.method == "GET":
            return render_template("ticket.html",doctors_reservated = doctors_reservated)

        #getting doctor name
        doctor_reservation = request.form.get("doctor_reservation")
        reservation_data = db.execute("SELECT * FROM patient_reservation WHERE patient_doctor_reservation = ? AND patient_name = ?",doctor_reservation, Patient_name)
        reservation_price = db.execute("SELECT Doctor_price FROM Doctors WHERE Doctor_name = ?",doctor_reservation)

        # Check invalid Inputs
        if len(reservation_data) == 0 :
            return render_template("ticket.html",message = "Invalid Input",doctors_reservated = doctors_reservated)

    #for the receptionistists
    elif session['user_id'] in Receptionist_accounts:
        patients_name = db.execute("SELECT * FROM Patients")
        doctors_reservated = db.execute("SELECT * FROM Doctors")

        if request.method == "GET":
            return render_template("ticket.html",doctors_reservated = doctors_reservated,patient_name=patients_name)

        #getting doctor name
        patient_name_get = request.form.get("patient_name")
        doctor_reservation = request.form.get("doctor_reservation")
        Variables_list = [patient_name_get , doctor_reservation]
        Variables_name = ["Patient name","Doctor name"]
        reservation_data = db.execute("SELECT * FROM patient_reservation WHERE patient_doctor_reservation = ? AND patient_name = ?",doctor_reservation,patient_name_get)
        patient_age = db.execute("SELECT patient_age FROM Patients WHERE patient_name = ?",patient_name_get)
        reservation_price = db.execute("SELECT Doctor_price FROM Doctors WHERE Doctor_name = ?",doctor_reservation)

        # Check reservation Data invalid
        if len(reservation_data) == 0:
            return render_template("ticket.html",message = "Invalid Data or This patient didn't reserved the doctor you have entered !",doctors_reservated = doctors_reservated,patient_name=patients_name)

        reservation_status = reservation_data[0]['reservation_status']

        # Check reservations for online users tickets
        if reservation_status == "Reservated":

            # Update to Unchecked & input receptionist name
            receptionist_name = db.execute("SELECT username FROM users WHERE id = ?",session['user_id'])[0]['username']
            db.execute("UPDATE patient_reservation SET reservation_status = ?, receptionist_name = ? WHERE patient_doctor_reservation = ? AND patient_name = ?", "Unchecked", receptionist_name, doctor_reservation, patient_name_get)
            reservation_data = db.execute("SELECT * FROM patient_reservation WHERE patient_doctor_reservation = ? AND patient_name = ?",doctor_reservation,patient_name_get)

        #check if the patient didn't reservated the doctor
        if len(reservation_data) == 0:
            return render_template("ticket.html",message = "This patient didn't reserved the doctor you have entered !",doctors_reservated = doctors_reservated,patient_name=patients_name)

        #check if the patient already checked doctor
        if reservation_status == "Checked":
            return render_template("ticket.html",message = "This patient has been Checked already !",doctors_reservated = doctors_reservated,patient_name=patients_name)

        # Blank Inputs
        if check_variable_if_exists(Variables_list,Variables_name,0,2,"/ticket.html"):
            return check_variable_if_exists(Variables_list,Variables_name,0,2,"/ticket.html")

    # Extract the relevant fields from the reservation_data
    patient_id = reservation_data[0]['patient_id']
    patient_name = reservation_data[0]['patient_name']
    patient_age = patient_age[0]['patient_age']
    patient_doctor_reservation = reservation_data[0]['patient_doctor_reservation']
    patient_doctor_date_time = reservation_data[0]['patient_doctor_date_time']
    patient_doctor_specialty = reservation_data[0]['patient_doctor_specialty']
    reservation_price = reservation_price[0]['Doctor_price']
    patient_query = reservation_data[0]['patient_query']
    patient_reservation_timestamp = reservation_data[0]['Time_stamp']
    patient_reservation_id = reservation_data[0]['reservation_id']
    receptionist_name = reservation_data[0]['receptionist_name']

    # Concatenate the reservation information as a string
    reservation_info =   f"Doctor Name:          {patient_doctor_reservation}\n" \
                         f"Doctor Specialty:     {patient_doctor_specialty}\n" \
                         f"Reservation Day:     {patient_doctor_date_time}\n" \
                         f"Reservation Price:   {reservation_price}.00 $\n" \
                         f"\n" \
                         f"Patient ID:               {patient_id}\n" \
                         f"Patient Name:         {patient_name}\n" \
                         f"Patient Age:            {patient_age}\n" \
                         f"\n" \
                         f"Your Queue:             {patient_query}\n" \
                         f"Time Reservated:     {patient_reservation_timestamp}\n" \
                         f"Reservation ID:         {patient_reservation_id}\n" \
                         f"Receptionist Name:   {receptionist_name}\n"

    # Concatenate the reservation information as a string
    reservation_info_1 = f"Doctor Name:          {patient_doctor_reservation}\n" \
                         f"Doctor Specialty:     {patient_doctor_specialty}\n" \
                         f"Reservation Day:     {patient_doctor_date_time}\n" \
                         f"Reservation Price:   {reservation_price}.00 $\n" \
                         f"\n" \
                         f"Patient ID:               {patient_id}\n" \
                         f"Patient Name:         {patient_name}\n" \
                         f"Patient Age:            {patient_age}\n"

    reservation_info_2 = f"Your Queue:             {patient_query}\n" \
                         f"Time Reservated:     {patient_reservation_timestamp}\n" \
                         f"Reservation ID:         {patient_reservation_id}\n" \
                         f"Receptionist Name:   {receptionist_name}\n"

    reservation_info_3 = f"Note: The ticket will not be considered\n""unless it have the hospital name stamp on\n""the same day of reservation & receptionist name"

    # Generate the QR code
    qr = qrcode.QRCode(version=1, box_size=10, border=5)
    qr.add_data(reservation_info)
    qr.make(fit=True)
    qr_image = qr.make_image(fill='black', back_color='white')

    # Resize the QR code image
    qr_size = (120, 120)  # Set the desired size of the QR code image
    qr_image = qr_image.resize(qr_size)

    # Create a new image with the reservation data and the QR code
    ticket_size = (400, 800)  # Set the desired size of the ticket image
    ticket_image = Image.new('RGB', ticket_size, 'white')
    draw = ImageDraw.Draw(ticket_image)

    # Draw a solid border
    border_color = 'black'
    border_width = 2
    draw.rectangle([(0, 0), (ticket_size[0] - 1, ticket_size[1] - 1)], outline=border_color, width=border_width)

    # Load the source image
    source_image = Image.open('/workspaces/104943996/Problem_sets/Final_Project/hospital/static/Logo-final_300-200.png')
    x = 50
    y = 5

    #paste logo
    ticket_image.paste(source_image , (x,y))


    # Set the desired font and text size
    font_size = 16
    font = ImageFont.truetype("/workspaces/104943996/Problem_sets/Final_Project/hospital/static/arial.ttf", font_size)

    # Draw the reservation data 1 on the image
    text_y = 225
    for line in reservation_info_1.split('\n'):
        draw.text((50, text_y), line, fill='black', font=font)
        text_y += font_size + 4

    # Calculate the position to paste the QR code in the ticket image
    qr_x = 140
    qr_y = text_y - 12

    # Paste the resized QR code image on the ticket image
    ticket_image.paste(qr_image, (qr_x, qr_y))

    # Draw the reservation data 2 on the image
    text_y = 520
    for line in reservation_info_2.split('\n'):
        draw.text((50, text_y), line, fill='black', font=font)
        text_y += font_size + 4

    # Draw the reservation data 2 on the image
    text_y = 720
    for line in reservation_info_3.split('\n'):
        draw.text((50, text_y), line, fill='black', font=font)
        text_y += font_size + 4

    # Save the image to a byte stream
    image_byte_arr = io.BytesIO()
    ticket_image.save(image_byte_arr, format='PNG')
    image_byte_arr.seek(0)

    # Check if receptionist save
    if session['user_id'] in Receptionist_accounts:


        #save the image to a file folder receptionist tickets
        image_path = f"/workspaces/104943996/Problem_sets/Final_Project/hospital/Tickets/Tickets_receptionist/reservation_ticket Receptionist_name {receptionist_name} Reservation_ID {patient_reservation_id} Time stamp {patient_reservation_timestamp}.png"
        ticket_image.save(image_path, format='PNG')

    else:
        # Save the image to a file for users in tickets
        image_path = f"/workspaces/104943996/Problem_sets/Final_Project/hospital/Tickets/Users/reservation_ticket Reservation_ID {patient_reservation_id} Time stamp {patient_reservation_timestamp}.png"
        ticket_image.save(image_path, format='PNG')

        # Convert the image to a base64-encoded string
        base64_image = base64.b64encode(image_byte_arr.getvalue()).decode('utf-8')

        # Render the template with the reservation ticket image
        return render_template('ticket.html', base64_image=base64_image, reservation_data=reservation_data[0], doctors_reservated = doctors_reservated)

    # Convert the image to a base64-encoded string
    base64_image = base64.b64encode(image_byte_arr.getvalue()).decode('utf-8')

    # Render the template with the reservation ticket image
    return render_template('ticket.html', base64_image=base64_image, reservation_data=reservation_data[0], doctors_reservated = doctors_reservated, patient_name=patients_name)

@app.route("/Messages", methods = ["GET","POST"])
@login_required
def messages_system():
    if session['user_id'] in Patient_accounts:
        return render_template("/")

    # Getting staff name
    staff_accounts_name = db.execute("SELECT username FROM users WHERE TYPE != ?",("Patient",))

    # Getting user message from
    Your_messages = db.execute("SELECT * FROM Messages JOIN users ON Messages.Message_to = users.username WHERE users.id = ?", session['user_id'])

    # Getting user sended messages
    sended_messages = db.execute("SELECT * FROM Messages JOIN users ON Messages.Message_from = users.username WHERE users.id = ?", session['user_id'])

    if request.method == "GET":
        return render_template("Messages.html", staff_accounts_name = staff_accounts_name, Your_messages = Your_messages, sended_messages = sended_messages)

    if request.method == "POST":

        # Sending message
        Message_to = request.form.get("Message_to")
        Message_from = db.execute("SELECT username FROM users WHERE id = ?",session['user_id'])[0]['username']
        Message_contect = request.form.get("Message_content")

        # Save to table
        db.execute("INSERT INTO Messages (Message_from, Message_to, Message_content) VALUES(?,?,?)", Message_from, Message_to, Message_contect)
        return render_template("Messages.html", staff_accounts_name = staff_accounts_name, Your_messages = Your_messages)

@app.route("/contact_us",methods=["GET"])
def contact_us():


    return render_template("contact_us.html")

#Accounts pages
@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""

    # Forget any user_id
    session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Ensure username was submitted
        if not request.form.get("username"):
            return render_template("login.html", message = "You must provide username")

        # Ensure password was submitted
        elif not request.form.get("password"):
            return render_template("login.html", message ="You must provide password")

        # Query database for username
        rows = db.execute("SELECT * FROM users WHERE username = ?", request.form.get("username"))

        # Ensure username exists and password is correct
        if len(rows) != 1 or not check_password_hash(rows[0]["hash"], request.form.get("password")):
            return render_template("login.html", message = "invalid username and/or password")

        # Remember which user has logged in
        session["user_id"] = rows[0]["id"]

        # Redirect user to home page
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("login.html")


@app.route("/resetpassword", methods=["GET", "POST"])
def resetpassword():

    # If user gets page by get
    if request.method == "GET":
        return render_template("resetpassword.html")

    # If user gets page by post
    else:

        # Checking the username in database for valid account
        username_check = request.form.get("username")
        username = db.execute("SELECT * from users WHERE username = ?", username_check)
        if len(username) != 1:
            return render_template("resetpassword.html", message ="Username you've entered doesn't exist")
        else:

            # Checking if the entry two passwords is not the same
            new_password = request.form.get("resetpassword")
            passwordconfirmation = request.form.get("passwordconfirmation")
            if new_password != passwordconfirmation:
                return render_template("resetpassword.html", message ="Passwords must be the same")

            # Checking if the old password is the same as the new one
            old_password = db.execute("SELECT hash FROM users WHERE username = ?", username_check)[0]['hash']
            same_password = check_password_hash(old_password, new_password)
            if same_password != 0:
                return render_template("resetpassword.html", message ="Password can't be the same as the old one !")

            # Implementing the new password hash to database
            hash_pass = generate_password_hash(new_password)
            db.execute("UPDATE users SET hash = ? WHERE username = ?", hash_pass, request.form.get("username"))
            return redirect("/")


@app.route("/logout")
def logout():
    """Log user out"""

    # Forget any user_id
    session.clear()

    # Redirect user to login form
    return redirect("/")


#Register for only for Admin & Receptionists
@app.route("/register_log", methods=["GET", "POST"])
@login_required
def register_log():

    if session['user_id'] in Admin_accounts or session['user_id'] in Receptionist_accounts:
        if request.method == "GET":
            render_template("/register_log.html")
    else:
        return redirect("/")

    if request.method == "POST":

        # New username entry
        username = request.form.get("username")
        Email = request.form.get("Email")
        Phone_number = request.form.get("Phone_number")
        ADRESS = request.form.get("Address")
        AGE = request.form.get("AGE")
        password = request.form.get("password")
        password_confirmation = request.form.get("confirmation")


        Variables = [username , Email , Phone_number , ADRESS , AGE , password , password_confirmation]
        Variables_name = ["username" , "Email" , "Phone_number" , "Address" , "Age" , "password" , "Password confirmation"]
        Variables_name_Table = ["username" , "Email" , "Phone_number" , "Address" , "Age" , "password", "Password confirmation"]

        # Blank Inputs
        if check_variable_if_exists(Variables,Variables_name,0,7,"/register_log.html"):
            return check_variable_if_exists(Variables,Variables_name,0,7,"/register_log.html")

        # Check if data already exists
        if Check_existing_variable_on_table(Variables,Variables_name,0,3,Variables_name_Table,"users","/register_log.html"):
            return Check_existing_variable_on_table(Variables,Variables_name,0,3,Variables_name_Table,"users","/register_log.html")

        # Password & it's confirmation not the same
        if Check_password_identically(password,password_confirmation,"Password",7,"/register_log.html"):
            return Check_password_identically(password,password_confirmation,"Password",7,"/register_log.html")

        # Password hashing
        password = generate_password_hash(request.form.get("password"))

        # Account Data insertion
        db.execute("INSERT INTO users (username,hash,Phone_number,AGE,ADRESS,Email) VALUES (?)", (username, password,Phone_number,AGE,ADRESS,Email))

        # Aquiring session
        return redirect("/")

    # Rendering page
    return render_template("/register_log.html")


#Register for users
@app.route("/register", methods=["GET", "POST"])
def register():

    # Forget any user_id
    session.clear()

    if request.method == "GET":
        render_template("/register.html")

    if request.method == "POST":

        # New username entry
        username = request.form.get("username")
        Email = request.form.get("Email")
        Phone_number = request.form.get("Phone_number")
        ADRESS = request.form.get("Address")
        AGE = request.form.get("AGE")
        password = request.form.get("password")
        password_confirmation = request.form.get("confirmation")

        # Making variables into list
        Variables = [username , Email , Phone_number , ADRESS , AGE , password , password_confirmation]
        Variables_name = ["username" , "Email" , "Phone_number" , "Address" , "Age" , "password" , "Password confirmation"]
        Variables_name_Table = ["username" , "Email" , "Phone_number" , "Address" , "Age" , "password", "Password confirmation"]

        # Check Blank Inputs
        if check_variable_if_exists(Variables,Variables_name,0,7,"/register.html"):
            return check_variable_if_exists(Variables,Variables_name,0,7,"/register.html")

        # Check Variables if already exists
        if Check_existing_variable_on_table(Variables,Variables_name,0,3,Variables_name_Table,"users","/register.html"):
            return Check_existing_variable_on_table(Variables,Variables_name,0,3,Variables_name_Table,"users","/register.html")

        # Check Password & it's confirmation not the same
        if Check_password_identically(password,password_confirmation,"Password",7,"/register.html"):
            return Check_password_identically(password,password_confirmation,"Password",7,"/register.html")

        # Password hashing
        password = generate_password_hash(request.form.get("password"))

        # Account Data insertion
        db.execute("INSERT INTO users (username,hash,Phone_number,AGE,ADRESS,Email) VALUES (?)", (username, password,Phone_number,AGE,ADRESS,Email))

        # Aquiring session
        return redirect("/")

    # Rendering page
    return render_template("/register.html")


