import csv
import io
import json

from flask import Flask
from sqlalchemy import asc, and_

from configuration import Configuration
from redis import Redis
from flask_jwt_extended import JWTManager

from models import *

application = Flask ( __name__ )
application.config.from_object ( Configuration )
jwt = JWTManager ( application )

def daemon():

    while True:

        with Redis(host=Configuration.REDIS_HOST) as redis:
            bytes = redis.lpop(Configuration.REDIS_PRODUCT_LIST)

        if not bytes:
            continue

        line = bytes.decode("utf-8")
        elements = line.split(",")
        categories = elements[0].split("|")
        name = elements[1]
        quantity = int(elements[2])
        price = float(elements[3])

        with application.app_context():

            product = Product.query.filter(Product.name == name).first()

            newOrder = Order()

            if product:
                existing_categories = ProductCategory.query.join(Category).with_entities(Category.name).filter(ProductCategory.productId == product.id).all()

                if set(categories) != set([x[0] for x in existing_categories]):
                    continue

                product.price = (quantity * price + product.quantity * product.price) / (quantity + product.quantity)
                product.quantity += quantity

            # new Product
            else:
                product = Product(name=name, price=price, quantity=quantity)
                database.session.add(product)
                database.session.commit()

                for categoryName in categories:
                    category = Category.query.filter(Category.name == categoryName).first()
                    if not category:
                        category = Category(name = categoryName)
                        database.session.add(category)
                        database.session.commit()
                    productCategory = ProductCategory(productId=product.id, categoryId=category.id)
                    database.session.add(productCategory)
            database.session.commit()

            # database.session.commit()

            # Check if there are some orders waithing for this product

            waitingProducts = ProductFromOrder.query.filter(and_(
                            ProductFromOrder.product == product.id,
                            ProductFromOrder.received < ProductFromOrder.requested
                        )).order_by(asc(ProductFromOrder.order)).all()

            if waitingProducts is not None and len(waitingProducts) > 0:
                i = 0

                myProductOrder = waitingProducts[i]

                while myProductOrder.received < myProductOrder.requested and product.quantity > 0:
                    left = myProductOrder.requested - myProductOrder.received

                    if left <= product.quantity:
                        myProductOrder.received = myProductOrder.requested
                        product.quantity -= left

                        # if that was the last one, order is no longer PENDING
                        unfinishedOrders = Order.query.join(ProductFromOrder, ProductFromOrder.order == Order.id)\
                            .filter(and_(ProductFromOrder.id == myProductOrder.id,
                                    ProductFromOrder.received < ProductFromOrder.requested)).all()

                        if not unfinishedOrders:
                            singleOrder = Order.query.filter(Order.id == myProductOrder.order).first()
                            singleOrder.status = "COMPLETE"
                            database.session.commit()

                    else:
                        myProductOrder.received += product.quantity
                        product.quantity = 0
                        database.session.commit()
                        break

                    database.session.commit()

                    i += 1
                    if i >= len(waitingProducts):
                        break
                    myProductOrder = waitingProducts[i]


if __name__ == "__main__":
    database.init_app ( application )
    daemon()
