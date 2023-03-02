import csv
import io
import json

from flask import Flask, request, Response, jsonify
from sqlalchemy import and_, func, desc
from sqlalchemy.sql.functions import coalesce

from configuration import Configuration
from redis import Redis
from flask_jwt_extended import JWTManager, jwt_required

from models import *
from roleChechDecorator import roleCheck

application = Flask ( __name__ )
application.config.from_object ( Configuration )
jwt = JWTManager ( application )

@application.route ( "/productStatistics", methods = ["GET"] )
@jwt_required(refresh=False)
@roleCheck (role = "administrator")
def productStatistics():

    prods = Product.query.join(ProductFromOrder)\
        .with_entities(Product.name, coalesce(func.sum(ProductFromOrder.received), 0), coalesce(func.sum(ProductFromOrder.requested),0)).\
        group_by(Product.id, Product.name).all()

    results = []

    for prod in prods:
        results.append({
            "name": prod[0],
            "sold": int(str((prod[2]))),
            "waiting": int(str((prod[2] - prod[1])))
        })

    return Response(response=json.dumps({"statistics": results}), status=200)


@application.route ( "/categoryStatistics", methods = ["GET"] )
@jwt_required(refresh=False)
@roleCheck (role = "administrator")
def categoryStatistics():

    prods = Category.query.join(ProductCategory, isouter=True).join(ProductFromOrder, ProductCategory.productId == ProductFromOrder.product, isouter=True)\
        .order_by(desc(coalesce(func.sum(ProductFromOrder.requested), 0)))\
        .order_by(Category.name)\
        .with_entities(Category.name).\
        group_by(Category.id).all()

    prods = [row[0] for row in prods]

    return Response(response=json.dumps({"statistics": prods}), status=200)



if __name__ == "__main__":
    database.init_app ( application )
    application.run ( debug = True, host = "0.0.0.0", port = 6003 )
