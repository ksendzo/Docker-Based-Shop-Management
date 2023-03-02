from flask_sqlalchemy import SQLAlchemy
import datetime

database = SQLAlchemy()

class ProductCategory ( database.Model ):
    __tablename__ = "ProductCategory"
    id = database.Column ( database.Integer, primary_key = True, autoincrement=True )
    productId = database.Column ( database.Integer, database.ForeignKey ( "Product.id" ), nullable = False )
    categoryId = database.Column ( database.Integer, database.ForeignKey ( "Category.id" ), nullable = False )


class Product(database.Model):
    __tablename__ = "Product"

    id = database.Column(database.Integer, primary_key=True, autoincrement=True)
    name = database.Column(database.String(256), nullable=False)
    price = database.Column(database.Float, nullable=False)
    quantity = database.Column(database.Integer, nullable=False, default=0)


class Category(database.Model):
    __tablename__ = "Category"

    id = database.Column(database.Integer, nullable=False, primary_key=True, autoincrement=True)
    name = database.Column(database.String(256), nullable=False, unique=True)

    def __repr__(self):
        return self.name


class ProductFromOrder(database.Model):
    __tablename__ = "ProductFromOrder"

    id = database.Column(database.Integer, primary_key=True, autoincrement=True)
    product = database.Column(database.Integer, database.ForeignKey("Product.id"), nullable=False)
    order = database.Column(database.Integer, database.ForeignKey("Order.id"), nullable=False)
    received = database.Column(database.Integer, nullable=False)
    requested = database.Column(database.Integer, nullable=False)
    price = database.Column(database.Float, nullable=False)


class Order(database.Model):
    __tablename__ = "Order"

    id = database.Column(database.Integer, primary_key=True, autoincrement=True)
    timestamp = database.Column(database.DateTime, default=datetime.datetime.utcnow)
    status = database.Column(database.String(256), nullable=False)
    price = database.Column(database.Float, nullable=False)
    customer = database.Column(database.String(256), nullable=False)


