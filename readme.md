# FGMS Reporter

A simple time-tracking utility for FlightGear multiplayer.
This can pull from any fgms server.

Time will be tracked for each listed pilot if that pilot is
moving over 5 knots in speed.

# Usage

Edit the file config.ini and change or add the callsigns, aircraft models 
and servers you want to track.

```
[general]
# put all callsigns you want to track, each seperated by a |
callsigns=cs1|cs2|cs3
# put all plane models that you want to track, each seperated by a |
aircraft=737-300|F-15C|A-10-model|SpaceShuttle
# a list of every server you'd like to pull from.
# the server needs to have telnet enabled on port 5001.
# you only need to pull from one server on each server network
# i.e. only pull from mpserver01, not mpserver01 and mpserver03.
# it will report wrong if you do this.
servers = mpserver01.flightgear.org
```

It will put all output into a csv file imaginatively called
output.csv, with the headers: callsign, model, eft. 
eft is effective flight time, and is time that callsign spend
travelling over 5 knots.
