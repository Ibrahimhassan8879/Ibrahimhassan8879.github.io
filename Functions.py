import os
import requests
import urllib.parse

from flask import redirect, render_template, request, session
from functools import wraps
import sqlite3
import os

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

# Configure CS50 Library to use SQLite database
db = SQL("sqlite:///Database.db")

def Get_file_location():
    # Connect to the SQLite database
    conn = sqlite3.connect('Database.db')
    cursor = conn.cursor()

    # Execute the query to retrieve the file location
    cursor.execute("SELECT Files_Location_path FROM Web_Deployment WHERE System_id = ?", ("Id",))
    result = cursor.fetchone()

    # Close the database connection
    cursor.close()
    conn.close()

    return result[0]

def check_variable_if_exists(Variable,Variable_name,number_start,number_finished,page_rendered):
    for i in range(number_start, number_finished, 1):
        if Variable[i] == '':
            error_message = f"{Variable_name[i]} field cannot be empty !"
            template_variable = f"message_{i+1}"
            return render_template(page_rendered, **{template_variable: error_message})

    return None

def Check_existing_variable_on_table(Variable, Variable_name,number_start,number_finished,Variable_name_table, Table_name, page_rendered):
    for i in range(number_start, number_finished, 1):
        Variable_name_table[i] = db.execute(f"SELECT * FROM {Table_name} WHERE `{Variable_name[i]}` = ?",(Variable[i],))
        if len(Variable_name_table[i]) == 1:
            error_message = f"{Variable_name[i]} is already exists !"
            template_variable = f"message_{i+1}"
            return render_template(page_rendered, **{template_variable: error_message})

def Check_password_identically(Variable_1,Variable_2,Variable_name,number,page_rendered):
    if Variable_1 != Variable_2:
        error_message = f"{Variable_name}s is not identical !"
        template_variable = f"message_{number}"
        return render_template(page_rendered, **{template_variable: error_message})

def Get_account_id_from_admin_by_Type(TYPE):
    Quota_loaded = sqlite3.connect('Database.db').execute("SELECT Quota_staff_number FROM Quota WHERE Quota_loaded = ?",("Loaded",)).fetchall()[0]
    rows = sqlite3.connect('Database.db').execute(f"SELECT id FROM users WHERE TYPE = ? LIMIT {Quota_loaded[0]}",(TYPE,)).fetchall()
    output = [ row[0] for row in rows]
    return output

def Get_account_id_from_staff_by_Type(TYPE):

    # Check Quota Validation
    Quota_date = sqlite3.connect('Database.db').execute("SELECT Quota_date FROM Quota WHERE Quota_loaded = ?", ("Loaded",)).fetchall()[0][0]
    timestamp = datetime.now().date().strftime("%Y-%m-%d")
    if timestamp > str(Quota_date):
        rows = sqlite3.connect('Database.db').execute(f"SELECT id FROM users WHERE TYPE = ? LIMIT 0",(TYPE,)).fetchall()
        sqlite3.connect('Database.db').execute("UPDATE Quota SET Quota_log = ? WHERE Quota_loaded = ?", timestamp, ("Loaded",))
        output = [ row[0] for row in rows]
        return output

    Quota_loaded = sqlite3.connect('Database.db').execute("SELECT Quota_staff_number FROM Quota WHERE Quota_loaded = ?",("Loaded",)).fetchall()[0]
    rows = sqlite3.connect('Database.db').execute(f"SELECT id FROM users WHERE TYPE = ? LIMIT {Quota_loaded[0]}",(TYPE,)).fetchall()
    output = [ row[0] for row in rows]
    return output

def Get_account_id_from_users_by_Type(TYPE):

    # Check Quota Validation
    timestamp = datetime.now().date().strftime("%Y-%m-%d")
    Quota_date = sqlite3.connect('Database.db').execute("SELECT Quota_date FROM Quota WHERE Quota_loaded = ?", ("Loaded",)).fetchall()[0][0]

    if timestamp > str(Quota_date):
        rows = sqlite3.connect('Database.db').execute(f"SELECT id FROM users WHERE TYPE = ? LIMIT 0",(TYPE,)).fetchall()

        output = [ row[0] for row in rows]
        return output

    # Get Quota Type
    Quota_loaded = sqlite3.connect('Database.db').execute("SELECT Quota_users_number FROM Quota WHERE Quota_loaded = ?",("Loaded",)).fetchall()[0]
    rows = sqlite3.connect('Database.db').execute(f"SELECT id FROM users WHERE TYPE = ? LIMIT {Quota_loaded[0]}",(TYPE,)).fetchall()
    output = [ row[0] for row in rows]
    return output

def update_accounts_data():
    Admin_accounts = Get_account_id_from_admin_by_Type("Admin")
    Receptionist_accounts = Get_account_id_from_staff_by_Type("Receptionist")
    Nurse_accounts = Get_account_id_from_staff_by_Type("Nurse")
    Accountant_accounts = Get_account_id_from_staff_by_Type("Accountant")
    Patient_accounts = Get_account_id_from_users_by_Type("Patient")
    return Admin_accounts, Receptionist_accounts, Nurse_accounts, Accountant_accounts, Patient_accounts