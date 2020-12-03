import io
from flask import Flask, redirect, render_template, request, session, url_for, send_file
import os
import sqlite3 as sl
import pandas as pd
import statsmodels.api as sm
import numpy as np
from datetime import date
from matplotlib.figure import Figure

app = Flask(__name__)
db = "covidData.db"


@app.route("/")
def home():
    # root/home page
    if request.args.get("error") == "True":
        return render_template("root.html", error="That's not a valid country, try again.")
    return render_template("root.html")


@app.route("/api/coronavirus/confirmed/<country_name>")
def view_confirmed(country_name):
    # check for errors otherwise pull up confirmed page
    dict = db_get_confirmed(country_name)
    if dict is None:
        return redirect(url_for('home', error="True"))
    return render_template("visualConfirmed.html", country_name=country_name)


@app.route("/redirect/confirmed")
def redirection_conf():
    # deal with parameter passing issues from html
    country = request.args.get("country_name")
    return redirect(url_for('view_confirmed', country_name=country))


@app.route("/redirect/recovered")
def redirection_reco():
    # deal with parameter passing issues from html
    country = request.args.get("country_name")
    return redirect(url_for('view_recovered', country_name=country))


@app.route("/api/coronavirus/recovered/<country_name>")
def view_recovered(country_name):
    # pull data from db than display recovered page
    dict = db_get_recovered(country_name)
    if dict is None:
        return redirect(url_for('home', error="True"))
    return render_template("visualRecovered.html", country_name=country_name)


@app.route("/api/coronavirus/confirmed/projection/<country_name>")
def project_confirmed(country_name):
    # pull data from db then dispplay confirmed page
    date = request.args.get("date")
    pro = project_confirmed_date(date, country_name)
    return render_template("projectConfirmed.html", country_name=country_name, projection=round(pro[0]), prodate=date)


@app.route("/api/coronavirus/recovered/projection/<country_name>")
def project_recovered(country_name):
    # pull data and build model, display html
    date = request.args.get("date")
    pro = project_recover_date(date, country_name)
    return render_template("projectRecovered.html", country_name=country_name, projection=round(pro[0]), prodate=date)


@app.route("/proj/confirmed-<country_name>-<year>-<month>-<day>.png")
def proj_img_confirmed(country_name, year, month, day):
    # endpoint for image of confirmed projections
    prodate = year + "-" + month + "-" + day
    dict = projection_confirmed_dict(prodate, country_name)
    df = pd.DataFrame.from_dict(dict)
    fig = Figure()
    ax = fig.add_subplot(1, 1, 1)
    ax.bar(df["dates"], df["cases"])
    ax.set_xticklabels(df["dates"], fontsize=6)
    for index, label in enumerate(ax.xaxis.get_ticklabels()):
        if index % 28 != 0:
            label.set_visible(False)
    ax.set_xlabel("Dates")
    ax.set_ylabel("Confirmed Recovered cases")
    fig.suptitle("Confirmed Recovered Cases")
    img = io.BytesIO()
    fig.savefig(img, format='png')
    img.seek(0)
    return send_file(img, mimetype="image/png")


@app.route("/proj/recovered-<country_name>-<year>-<month>-<day>.png")
def proj_img_recovered(country_name, year, month, day):
    # endpoint for image of recovered projections
    prodate = year + "-" + month + "-" + day
    dict = projection_recover_dict(prodate, country_name)
    df = pd.DataFrame.from_dict(dict)
    fig = Figure()
    ax = fig.add_subplot(1, 1, 1)
    ax.bar(df["dates"], df["cases"])
    ax.set_xticklabels(df["dates"], fontsize=6)
    for index, label in enumerate(ax.xaxis.get_ticklabels()):
        if index % 28 != 0:
            label.set_visible(False)
    ax.set_xlabel("Dates")
    ax.set_ylabel("Projected Recovered cases")
    fig.suptitle("Projected Recovered Cases")
    img = io.BytesIO()
    fig.savefig(img, format='png')
    img.seek(0)
    return send_file(img, mimetype="image/png")


@app.route("/confirmed-<country_name>.png")
def img_confirmed(country_name):
    # endpoint for confirmed data plot
    dict = db_get_confirmed(country_name)
    df = pd.DataFrame.from_dict(dict)
    fig = Figure()
    ax = fig.add_subplot(1, 1, 1)
    ax.bar(df["dates"], df["cases"])
    ax.set_xticklabels(df["dates"], fontsize=6)
    for index, label in enumerate(ax.xaxis.get_ticklabels()):
        if index % 28 != 0:
            label.set_visible(False)
    ax.set_xlabel("Dates")
    ax.set_ylabel("Confirmed cases")
    fig.suptitle("Confirmed Cases")
    img = io.BytesIO()
    fig.savefig(img, format='png')
    img.seek(0)
    return send_file(img, mimetype="image/png")


@app.route("/recovered-<country_name>.png")
def img_recovered(country_name):
    # endpoint for recovered data plot
    dict = db_get_recovered(country_name)
    df = pd.DataFrame.from_dict(dict)
    fig = Figure()
    ax = fig.add_subplot(1, 1, 1)
    ax.bar(df["dates"], df["cases"])
    ax.set_xticklabels(df["dates"], fontsize=6)
    for index, label in enumerate(ax.xaxis.get_ticklabels()):
        if index % 28 != 0:
            label.set_visible(False)
    ax.set_xlabel("Dates")
    ax.set_ylabel("Recovered cases")
    fig.suptitle("Recovered Cases")
    img = io.BytesIO()
    fig.savefig(img, format='png')
    img.seek(0)
    return send_file(img, mimetype="image/png")


def db_get_confirmed(country):
    # get the data from db, then return a dictionary of dates and case numbers for plotting in another function
    conn = sl.connect(db)
    curs = conn.cursor()
    stmt = "SELECT * FROM time_series_confirmed"
    data = curs.execute(stmt)
    # print(type(data))
    cases = []
    length = 0

    for thing in data:
        length = len(thing)
        break

    for i in range(4, length):
        cases.append(0)

    dates = pd.date_range(start="2020-01-22", end="2020-10-27").to_pydatetime().tolist()
    for i in range(0, len(dates)):
        dates[i] = dates[i].strftime("%M/%D/%Y")
        dates[i] = dates[i][3:]
        dates[i] = dates[i][:8]

    count = 0
    for thing in data:
        if thing[1] == country:
            count += 1
            for i in range(4, len(thing)):
                cases[i-4] += thing[i]

    if count == 0:
        return None

    dict = {"dates": [], "cases": []}
    for i in range(0, len(cases)):
        dict["dates"].append(dates[i])
        dict["cases"].append(cases[i])

    conn.close()
    return dict


def db_get_recovered(country):
    # get the data from db, then return a dictionary of dates and case numbers for plotting in another function
    conn = sl.connect(db)
    curs = conn.cursor()
    stmt = "SELECT * FROM time_series_recovered"
    data = curs.execute(stmt)
    # print(type(data))
    cases = []
    length = 0

    for thing in data:
        length = len(thing)
        break

    for i in range(4, length):
        cases.append(0)

    dates = pd.date_range(start="2020-01-22", end="2020-10-27").to_pydatetime().tolist()
    for i in range(0, len(dates)):
        dates[i] = dates[i].strftime("%M/%D/%Y")
        dates[i] = dates[i][3:]
        dates[i] = dates[i][:8]

    count = 0
    for thing in data:
        if thing[1] == country:
            count += 1
            for i in range(4, len(thing)):
                cases[i-4] += thing[i]

    if count == 0:
        return None

    dict = {"dates": [], "cases": []}
    for i in range(0, len(cases)):
        dict["dates"].append(dates[i])
        dict["cases"].append(cases[i])

    conn.close()
    return dict


def build_confirmed_model(country):
    # build model to use for confirmed projections
    # grab recovered data from database
    conn = sl.connect(db)
    curs = conn.cursor()
    stmt = "SELECT * FROM time_series_confirmed"
    data = curs.execute(stmt)
    cases = []
    length = 0

    for thing in data:
        length = len(thing)
        break

    for i in range(4, length):
        cases.append(0)

    for thing in data:
        if thing[1] == country:
            for i in range(4, len(thing)):
                cases[i-4] += thing[i]

    # generate array for indexing
    index = []
    for i in range(0, 280):
        index.append(i)
    # make linear regression model
    index, cases = np.array(index), np.array(cases)
    model = sm.OLS(cases, index)
    results = model.fit();
    conn.close()
    return results


def project_confirmed_date(proDate, country):
    # project to a specific date for confirmed cases
    results = build_confirmed_model(country)
    d0 = date(2020, 1, 22)
    d1 = date(int(proDate[:4]), int(proDate[5:7]), int(proDate[8:]))
    delta = d1 - d0
    proIndex = delta.days
    return results.predict(proIndex)


def projection_confirmed_dict(proDate, country):
    # return a dictionary of dates and projections for plotting in another function
    results = build_confirmed_model(country)
    dates = pd.date_range(start="2020-01-22", end=proDate).to_pydatetime().tolist()
    for i in range(0, len(dates)):
        dates[i] = dates[i].strftime("%M/%D/%Y")
        dates[i] = dates[i][3:]
        dates[i] = dates[i][:8]
    proCases = []
    for i in range(0, len(dates)):
        r = results.predict(i)
        proCases.append(r[0])
    dict = {"dates": [], "cases": []}
    for i in range(0, len(proCases)):
        dict["dates"].append(dates[i])
        dict["cases"].append(proCases[i])
    return dict


def build_recover_model(country):
    # build model to project from for recovered cases
    # grab recovered data from database
    conn = sl.connect(db)
    curs = conn.cursor()
    stmt = "SELECT * FROM time_series_recovered"
    data = curs.execute(stmt)
    # print(type(data))
    cases = []
    length = 0

    for thing in data:
        length = len(thing)
        break

    for i in range(4, length):
        cases.append(0)

    for thing in data:
        if thing[1] == country:
            for i in range(4, len(thing)):
                cases[i-4] += thing[i]

    # generate array for indexing
    index = []
    for i in range(0, 280):
        index.append(i)
    # make linear regression model
    index, cases = np.array(index), np.array(cases)
    model = sm.OLS(cases, index)
    results = model.fit();
    conn.close()
    return results


def project_recover_date(proDate, country):
    # project to a specific date for recovered cases
    results = build_recover_model(country)
    d0 = date(2020, 1, 22)
    d1 = date(int(proDate[:4]), int(proDate[5:7]), int(proDate[8:]))
    delta = d1 - d0
    proIndex = delta.days
    return results.predict(proIndex)


def projection_recover_dict(proDate, country):
    # return a dictionary with recovered cases and dates to use for plotting in a different function
    results = build_recover_model(country)
    dates = pd.date_range(start="2020-01-22", end=proDate).to_pydatetime().tolist()
    for i in range(0, len(dates)):
        dates[i] = dates[i].strftime("%M/%D/%Y")
        dates[i] = dates[i][3:]
        dates[i] = dates[i][:8]
    proCases = []
    for i in range(0, len(dates)):
        r = results.predict(i)
        proCases.append(r[0])
    dict = {"dates": [], "cases": []}
    for i in range(0, len(proCases)):
        dict["dates"].append(dates[i])
        dict["cases"].append(proCases[i])
    return dict


if __name__ == "__main__":
    app.secret_key = os.urandom(12)
    app.run(debug=True)
