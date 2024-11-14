# Import the dependencies.
from flask import Flask, jsonify
import datetime as dt
import pandas as pd
from sqlalchemy import create_engine, func
from sqlalchemy.orm import Session
from sqlalchemy.ext.automap import automap_base


#################################################
# Database Setup
#################################################


# reflect an existing database into a new model
engine = create_engine("sqlite:///Resources/hawaii.sqlite")
Base = automap_base()
Base.prepare(engine, reflect=True)
# reflect the tables


# Save references to each table
Measurement = Base.classes.measurement
Station = Base.classes.station

# Create our session (link) from Python to the DB


#################################################
# Flask Setup
#################################################
app = Flask(__name__)



#################################################
# Flask Routes
#################################################


# Homepage route
@app.route("/")
def welcome():
    return (
        f"Welcome to the Hawaii Climate API!<br/><br/>"
        f"Available Routes:<br/>"
        f"/api/v1.0/precipitation - Last 12 months of precipitation data<br/>"
        f"/api/v1.0/stations - List of weather stations<br/>"
        f"/api/v1.0/tobs - Temperature observations for the most active station over the last year<br/>"
        f"/api/v1.0/temp/<start> - Min, Max, and Avg temperature from a start date (YYYY-MM-DD)<br/>"
        f"/api/v1.0/temp/<start>/<end> - Min, Max, and Avg temperature between start and end dates (YYYY-MM-DD)<br/>"
    )

# Route for last 12 months of precipitation data
@app.route("/api/v1.0/precipitation")
def precipitation():
    session = Session(engine)
    most_recent_date = session.query(func.max(Measurement.date)).scalar()
    one_year_ago = pd.to_datetime(most_recent_date) - pd.DateOffset(years=1)
    results = session.query(Measurement.date, Measurement.prcp)\
        .filter(Measurement.date >= one_year_ago.strftime('%Y-%m-%d')).all()
    session.close()
    
    precipitation_data = {date: prcp for date, prcp in results}
    return jsonify(precipitation_data)

# Route for list of stations
@app.route("/api/v1.0/stations")
def stations():
    session = Session(engine)
    results = session.query(Station.station).all()
    session.close()
    
    stations = [station[0] for station in results]
    return jsonify(stations)

# Route for temperature observations of the most active station for the last year
@app.route("/api/v1.0/tobs")
def tobs():
    session = Session(engine)
    most_active_station = session.query(Measurement.station)\
        .group_by(Measurement.station)\
        .order_by(func.count(Measurement.station).desc()).first()[0]
    
    most_recent_date = session.query(func.max(Measurement.date)).scalar()
    one_year_ago = pd.to_datetime(most_recent_date) - pd.DateOffset(years=1)
    results = session.query(Measurement.date, Measurement.tobs)\
        .filter(Measurement.station == most_active_station)\
        .filter(Measurement.date >= one_year_ago.strftime('%Y-%m-%d')).all()
    session.close()
    
    tobs_data = [{"date": date, "temperature": tobs} for date, tobs in results]
    return jsonify(tobs_data)

# Route for temperature stats from a start date
@app.route("/api/v1.0/temp/<start>")
@app.route("/api/v1.0/temp/<start>/<end>")
def temp_stats(start, end=None):
    session = Session(engine)
    sel = [func.min(Measurement.tobs), func.avg(Measurement.tobs), func.max(Measurement.tobs)]
    
    if end:
        results = session.query(*sel).filter(Measurement.date >= start).filter(Measurement.date <= end).all()
    else:
        results = session.query(*sel).filter(Measurement.date >= start).all()
    session.close()
    
    temp_data = list(results[0])
    return jsonify(temp_data)

# Run the app
if __name__ == "__main__":
    app.run(debug=True)