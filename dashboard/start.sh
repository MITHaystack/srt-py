#!/bin/sh
gunicorn app:server -b :8000 -w 4 
