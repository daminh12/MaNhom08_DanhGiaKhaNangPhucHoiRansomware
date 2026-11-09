"""Synthetic orders lab. Database writes are limited to inserting fake orders."""

from contextlib import contextmanager
from datetime import timezone
import os
from pathlib import Path
import re
from urllib.parse import urlsplit

from flask import Flask, jsonify, render_template, request
import pymysql
from werkzeug.exceptions import BadRequest, RequestEntityTooLarge


PRODUCTS = ("Notebook", "Pen", "Folder")
ORDER_FIELDS = {"customer_alias", "product_name", "quantity", "unit_price_vnd"}
ORDER_COLUMNS = "id, customer_alias, product_name, quantity, unit_price_vnd, created_at_utc"


def create_app(config=None):
    app = Flask(__name__)
    app.config.from_mapping(
        DB_HOST=os.environ.get("DB_HOST", "db"),
        DB_NAME=os.environ.get("DB_NAME", "lab_config"),
        DB_USER=os.environ.get("DB_USER", "group08_app"),
        DB_PASSWORD_FILE=os.environ.get("DB_PASSWORD_FILE", "/run/secrets/db_app_password"),
        DB_CONNECTOR=None,
        MAX_CONTENT_LENGTH=8192,
        TRUSTED_HOSTS=["localhost", "127.0.0.1"],
    )
    if config:
        app.config.update(config)

    @contextmanager
    def database():
        connector = app.config["DB_CONNECTOR"]
        if connector is None:
            password = Path(app.config["DB_PASSWORD_FILE"]).read_text(encoding="utf-8").strip()
            if not password:
                raise ValueError("Missing database credential")
            connection = pymysql.connect(
                host=app.config["DB_HOST"],
                user=app.config["DB_USER"],
                password=password,
                database=app.config["DB_NAME"],
                charset="utf8mb4",
                cursorclass=pymysql.cursors.DictCursor,
                autocommit=False,
                connect_timeout=3,
                read_timeout=3,
                write_timeout=3,
                init_command="SET time_zone = '+00:00'",
            )
        else:
            connection = connector()
        try:
            yield connection
        finally:
            connection.close()

    def db_error():
        # Do not return/log connection details, SQL, or password-file contents.
        app.logger.warning("Database operation unavailable")
        return jsonify(error="Cơ sở dữ liệu chưa sẵn sàng. Vui lòng thử lại."), 503

    def serialize(row):
        result = dict(row)
        stamp = result["created_at_utc"]
        result["created_at_utc"] = stamp.replace(tzinfo=timezone.utc).isoformat().replace("+00:00", "Z")
        return result

    @app.after_request
    def response_headers(response):
        response.headers["Cache-Control"] = "no-store"
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["Referrer-Policy"] = "no-referrer"
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; script-src 'self'; style-src 'self'; "
            "img-src 'self'; connect-src 'self'; frame-ancestors 'none'; "
            "base-uri 'none'; form-action 'self'"
        )
        return response

    @app.errorhandler(RequestEntityTooLarge)
    def too_large(_error):
        return jsonify(error="Yêu cầu vượt quá giới hạn 8 KiB."), 413

    @app.get("/")
    def index():
        return render_template("index.html", products=PRODUCTS)

    @app.get("/health")
    def health():
        try:
            with database() as connection, connection.cursor() as cursor:
                cursor.execute("SELECT COUNT(*) AS total FROM orders")
                count = cursor.fetchone()["total"]
            return jsonify(status="ok", database="ok", orders_count=count)
        except (pymysql.MySQLError, OSError, ValueError):
            return jsonify(status="unavailable", database="unavailable"), 503

    @app.get("/api/orders")
    def orders():
        try:
            with database() as connection, connection.cursor() as cursor:
                cursor.execute("SELECT COUNT(*) AS total FROM orders")
                total = cursor.fetchone()["total"]
                cursor.execute(f"SELECT {ORDER_COLUMNS} FROM orders ORDER BY id DESC LIMIT 100")
                rows = cursor.fetchall()
            return jsonify(orders=[serialize(row) for row in rows], total=total)
        except (pymysql.MySQLError, OSError, ValueError):
            return db_error()

    @app.post("/api/orders")
    def add_order():
        # No browser cross-origin mutation; non-browser JSON clients are allowed.
        origin = request.headers.get("Origin")
        expected_origin = urlsplit(request.host_url)
        if (origin is not None and origin.rstrip("/") != f"{expected_origin.scheme}://{expected_origin.netloc}") or request.headers.get("Sec-Fetch-Site") == "cross-site":
            return jsonify(error="Chỉ chấp nhận yêu cầu từ trang lab này."), 403
        if not request.is_json:
            return jsonify(error="Yêu cầu phải dùng Content-Type: application/json."), 415
        try:
            payload = request.get_json()
        except BadRequest:
            return jsonify(error="JSON không hợp lệ."), 400
        if not isinstance(payload, dict) or set(payload) != ORDER_FIELDS:
            return jsonify(error="Cần đủ bốn trường: customer_alias, product_name, quantity, unit_price_vnd."), 400
        alias, product = payload["customer_alias"], payload["product_name"]
        quantity, price = payload["quantity"], payload["unit_price_vnd"]
        if not isinstance(alias, str) or re.fullmatch(r"LAB-[A-Z0-9-]{1,32}", alias) is None:
            return jsonify(error="Mã khách giả phải có dạng LAB-001, chỉ dùng chữ hoa, số và dấu gạch ngang."), 400
        if not isinstance(product, str) or product not in PRODUCTS:
            return jsonify(error="Sản phẩm phải là Notebook, Pen hoặc Folder."), 400
        if type(quantity) is not int or not 1 <= quantity <= 100:
            return jsonify(error="Số lượng phải là số nguyên từ 1 đến 100."), 400
        if type(price) is not int or not 1 <= price <= 100_000_000:
            return jsonify(error="Đơn giá phải là số nguyên từ 1 đến 100.000.000 VND."), 400
        try:
            with database() as connection, connection.cursor() as cursor:
                cursor.execute(
                    "INSERT INTO orders (customer_alias, product_name, quantity, unit_price_vnd) VALUES (%s, %s, %s, %s)",
                    (alias, product, quantity, price),
                )
                cursor.execute(f"SELECT {ORDER_COLUMNS} FROM orders WHERE id = %s", (cursor.lastrowid,))
                row = cursor.fetchone()
                connection.commit()
            return jsonify(order=serialize(row)), 201
        except (pymysql.MySQLError, OSError, ValueError):
            return db_error()

    return app


app = create_app()
