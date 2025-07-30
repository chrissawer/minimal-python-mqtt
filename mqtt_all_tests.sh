#!/bin/sh

PYDIR=$(dirname $0)
python3 $PYDIR/mqtt_tests.py
python3 $PYDIR/mqtt_message_tests.py
