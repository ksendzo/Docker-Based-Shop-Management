from flask import Flask, request, Response, jsonify
from configuration import Configuration
from email.utils import parseaddr
from models import database, User, UserRole, Role
from sqlalchemy import and_
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, create_refresh_token, get_jwt, \
    get_jwt_identity, verify_jwt_in_request;
import re
import json

application = Flask(__name__)
application.config.from_object(Configuration)

@application.route("/check", methods=["GET"])
def check():
    return Response(status=200)

def is_valid_email(email):
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    match = re.match(pattern, email)
    return match is not None

def is_valid_password(password):
    if len(password) < 8:
        return False
    if not any(char.isdigit() for char in password):
        return False
    if not any(char.isupper() for char in password):
        return False
    if not any(char.islower() for char in password):
        return False
    return True

@application.route("/register", methods=["POST"])
def register():

    forename = request.json.get("forename", "")
    surname = request.json.get("surname", "")
    email = request.json.get("email", "")
    password = request.json.get("password", "")
    isCustomer = request.json.get("isCustomer", None)

    missingField = ""
    if not forename or len(forename) == 0:
        missingField = "forename"
    elif not surname or len(surname) == 0:
        missingField = "surname"
    elif not email or len(email) == 0:
        missingField = "email"
    elif not password or len(password) == 0:
        missingField = "password"
    elif isCustomer is None:
        missingField = "isCustomer"

    if len(missingField) > 0:
        return Response(response=json.dumps({"message":f"Field {missingField} is missing."}), status=400)

    #check forename
    if len(forename) > 256:
        return Response(response=json.dumps({"message":"Too long forname."}), status=400)

    if len(surname) > 256:
        return Response(response=json.dumps({"message":"Too long surname."}), status=400)

    #check email
    if len(email) > 256:
        return Response(response=json.dumps({"message":"Too long email."}), status=400)

    if not is_valid_email(email):
        return Response(response=json.dumps({"message":"Invalid email."}), status=400)

    #check password
    if len(email) > 256:
        return Response(response=json.dumps({"message":"Too long password."}), status=400)

    if not is_valid_password(password):
        return Response(response=json.dumps({"message":"Invalid password."}), status=400)

    #check if email is already in the db
    isUser = User.query.filter(User.email == email).first()

    if isUser:
        return Response(response=json.dumps({"message":"Email already exists."}), status=400)

    user = User (forename=forename, surname=surname, email=email, password=password)
    database.session.add(user)
    database.session.commit()

    role = "user" if isCustomer else "warehouseman"
    rr = Role.query.filter(Role.name == role).one()
    userRole = UserRole(userId = user.id, roleId = rr.id)

    database.session.add(userRole)
    database.session.commit()

    return Response(status=200)

jwt = JWTManager(application)

@application.route("/login", methods=["POST"])
def login():
    email = request.json.get("email", "")
    password = request.json.get("password", "")

    if not email or len(email) == 0:
        return Response(response=json.dumps({"message":"Field email is missing."}), status=400)
    if not password or len(password) == 0:
        return Response(response=json.dumps({"message":"Field password is missing."}), status=400)

    if len(email) > 256:
        return Response(response=json.dumps({"message":"Field email is too long."}), status=400)
    if len(password) > 256:
        return Response(response=json.dumps({"message":"Field password is too long."}), status=400)

    if not is_valid_email(email):
        return Response(response=json.dumps({"message":"Invalid email."}), status=400)

    user = User.query.filter(and_(User.email == email, User.password == password)).first()

    if not user:
        return Response(response=json.dumps({"message":"Invalid credentials."}), status=400)

    role = Role.query.join(UserRole).filter(UserRole.userId == user.id).with_entities(Role.name).first()

    if role.name == "admin":
        role = "administrator"
    elif role.name == "user":
        role = "customer"
    else:
        role = "manager"

    additionalClaims = {
        "forename": user.forename,
        "surname": user.surname,
        "roles": [role]
    }

    accessToken = create_access_token ( identity = user.email, additional_claims = additionalClaims, expires_delta=Configuration.JWT_ACCESS_TOKEN_EXPIRESS)
    refreshToken = create_refresh_token ( identity = user.email, additional_claims = additionalClaims, expires_delta=Configuration.JWT_REFRESH_TOKEN_EXPIRESS)

    return jsonify ( accessToken = accessToken, refreshToken = refreshToken ), 200


@application.route ( "/refresh", methods = ["POST"] )
@jwt_required ( refresh = True )
def refresh ( ):
    identity = get_jwt_identity ( )
    refreshClaims = get_jwt ( )

    additionalClaims = {
        "forename": refreshClaims["forename"],
        "surname": refreshClaims["surname"],
        "roles": refreshClaims["roles"]
    }

    accessToken = create_access_token ( identity = identity, additional_claims = additionalClaims, expires_delta=Configuration.JWT_ACCESS_TOKEN_EXPIRESS)

    return jsonify ( accessToken = accessToken), 200


@application.route("/delete", methods=["POST"])
@jwt_required(refresh=False)
def delete():
    verify_jwt_in_request()
    claims = get_jwt()
    if (not (("roles" in claims) and ("administrator" in claims["roles"]))):
        return Response(response=json.dumps({"msg": "Missing Authorization Header"}), status=401)

    email = request.json.get("email", "")

    if not email or len(email) == 0:
        return Response(response=json.dumps({"message":"Field email is missing."}), status=400)

    if len(email) > 256:
        return Response(response=json.dumps({"message": "Field email is too long."}), status=400)

    if not is_valid_email(email):
        return Response(response=json.dumps({"message":"Invalid email."}), status=400)

    user = User.query.filter(User.email == email).first()

    if user is None:
        return Response(response=json.dumps({"message":"Unknown user."}), status=400)

    userRole = UserRole.query.filter(UserRole.userId == user.id).first()

    database.session.delete(userRole)
    database.session.commit()

    database.session.delete(user)
    database.session.commit()

    return Response(status=200)


@application.route("/", methods=["GET"])
def index():
    return "Hello World!"

if __name__ == '__main__':
    database.init_app(application)
    application.run(debug=True, host="0.0.0.0", port=5002)



