import csv
import io
import json

from flask import Flask, request, Response
from configuration import Configuration
from redis import Redis
from flask_jwt_extended import JWTManager, jwt_required

from roleChechDecorator import roleCheck

application = Flask ( __name__ )
application.config.from_object ( Configuration )
jwt = JWTManager ( application )

@application.route ( "/update", methods = ["POST"] )
@jwt_required(refresh=False)
@roleCheck (role = "manager")
def update():
    try:
        file = request.files["file"]
        # process the file
    except KeyError:
        return Response(response=json.dumps({"message":"Field file is missing."}), status=400)

    if file is None:
        return Response(response=json.dumps({"message":"Field file is missing."}), status=400)

    content = file.stream.read().decode("utf-8");
    stream = io.StringIO(content);
    reader = csv.reader(stream);

    line = 0
    elements = []
    for row in reader:
        if len(row) < 4:
            return Response(response=json.dumps({"message": "Incorrect number of values on line " + str(line) + "."}), status=400)

        quantity = row[2]
        if not (quantity.isdigit() and int(quantity) >= 0):
            return Response(response=json.dumps({"message": "Incorrect quantity on line " + str(line) + "."}), status=400)

        price = row[3]
        check = True
        try:
            number = float(price)
        except ValueError:
            check = False

        if not (check and float(price) >= 0):
            return Response(response=json.dumps({"message": "Incorrect price on line " + str(line) + "."}), status=400)

        elem = row[0] + "," + row[1] + "," + row[2] + "," + row[3]
        elements.append(elem)
        line += 1

    with Redis(host=Configuration.REDIS_HOST) as redis:
        for elem in elements:
            redis.rpush (Configuration.REDIS_PRODUCT_LIST, elem)
            print(elem)

    print("end")
    return Response(status=200)


if __name__ == "__main__":
    application.run ( debug = True, host="0.0.0.0", port = 6001 )
