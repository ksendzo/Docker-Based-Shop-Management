import csv
import io
import json

from flask import Flask, request, Response, jsonify
from sqlalchemy import and_

from configuration import Configuration
from redis import Redis
from flask_jwt_extended import JWTManager, jwt_required

from models import *
from roleChechDecorator import roleCheck

application = Flask ( __name__ )
application.config.from_object ( Configuration )
jwt = JWTManager ( application )

@application.route ( "/search", methods = ["GET"] )
@jwt_required(refresh=False)
@roleCheck (role = "customer")
def search():

    name = request.args.get('name')
    category = request.args.get('category')

    if name is None:
        name = ""
    if category is None:
        category = ""

    categories = Category.query.join(ProductCategory).join(Product)\
        .filter(and_(Category.name.like(f'%{category}%'), Product.name.like(f'%{name}%'))).group_by(Category.name).with_entities(Category.name).all()

    categories = [row[0] for row in categories]

    products_query = Product.query.join(ProductCategory).join(Category)\
        .filter(and_(Category.name.like(f'%{category}%'), Product.name.like(f'%{name}%')))\
        .group_by(Product.id)\
        .with_entities(Product.id, Product.name, Product.price, Product.quantity).all()

    products = []
    for product in products_query:
        my_categories =  Category.query.join(ProductCategory).filter(ProductCategory.productId == product.id).with_entities(Category.name).all()
        my_categories = [row[0] for row in my_categories]
        products.append({
            "categories": my_categories,
            "id": product.id,
            "name": product.name,
            "price": product.price,
            "quantity": product.quantity
        })

    return jsonify ( categories = categories, products = products), 200


@application.route ( "/order", methods = ["POST"] )
@jwt_required(refresh=False)
@roleCheck (role = "customer")
def order():

    email = "john@mail.com"

    requests = request.json.get("requests")

    if not requests or not isinstance(requests, list) or len(requests) == 0:
        return Response(response=json.dumps({"message":"Field requests is missing."}), status=400)

    sum_price = 0
    original_prices = {}

    for i in range(len(requests)):
        req = requests[i]

        if not req or req.get('id') is None:
            return Response(response=json.dumps({"message": f'Product id is missing for request number {i}.'}), status=400)

        if req.get('quantity') is None:
            return Response(response=json.dumps({"message": f'Product quantity is missing for request number {i}.'}), status=400)

        if not isinstance(req.get('id'), int) or req.get('id') <= 0:
            return Response(response=json.dumps({"message": f'Invalid product id for request number {i}.'}), status=400)

        if not isinstance(req.get('quantity'), int) or req.get('quantity') <= 0:
            return Response(response=json.dumps({"message": f'Invalid product quantity for request number {i}.'}), status=400)

        product = Product.query.filter(Product.id == req['id']).all()

        if len(product) == 0:
            return Response(response=json.dumps({"message": f'Invalid product for request number {i}.'}), status=400)

        product = product[0]

        sum_price += product.price * req["quantity"]
        original_prices[int(product.id)] = float(product.price)

    new_order = Order(status="PENDING", price=sum_price, customer=email)
    database.session.add(new_order)
    database.session.commit()

    status = "COMPLETE"

    for req in requests:
        product = Product.query.filter(Product.id == req["id"]).with_for_update().all()[0]

        if product.quantity >= req["quantity"]:
            received = req["quantity"]
            product.quantity -= req["quantity"]
        else:
            received = product.quantity
            product.quantity = 0
            status = "PENDING"

        pfo = ProductFromOrder(product=int(product.id), order=int(new_order.id), requested=int(req["quantity"]), received=int(received), price=original_prices[int(product.id)])

        database.session.add(pfo)
        database.session.commit()

    if status == "COMPLETE":
        new_order.status = status
        database.session.commit()

    return Response(response=json.dumps({"id": new_order.id}), status=200)


@application.route ( "/status", methods = ["GET"] )
@jwt_required(refresh=False)
@roleCheck (role = "customer")
def status():
    email = "john@mail.com"

    orders = Order.query.filter(Order.customer == email).all()

    results = []

    for order in orders:
        single_order = {}
        single_order["products"] = []
        single_order["price"] = order.price
        single_order["status"] = order.status
        single_order["timestamp"] = order.timestamp.isoformat()

        productsFromOrder = ProductFromOrder.query.filter(ProductFromOrder.order == order.id).all()

        for productFO in productsFromOrder:
            product = Product.query.filter(Product.id == productFO.product).all()[0]
            prod = {}
            prod["name"] = product.name
            prod["price"] = productFO.price
            prod["received"] = productFO.received
            prod["requested"] = productFO.requested

            categs = Category.query.join(ProductCategory).filter(ProductCategory.productId == product.id)\
                .with_entities(Category.name).all()

            prod["categories"] = [row[0] for row in categs]

            single_order["products"].append(prod)

        results.append(single_order)


    print(results)

    return Response(response=json.dumps({"orders": results}), status=200)


if __name__ == "__main__":
    database.init_app ( application )
    application.run ( debug = True, host="0.0.0.0", port = 6002 )
