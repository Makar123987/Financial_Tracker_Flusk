from os import environ
from flask import Flask, request, render_template, session, redirect, abort, flash
from sqlalchemy import select, insert
from database import db_session, init_db
import models
from datetime import datetime
from werkzeug.security import check_password_hash, generate_password_hash
from sqlalchemy import exc

INCOME = 1
SPEND = 2
