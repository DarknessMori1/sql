from fastapi import FastAPI, HTTPException, Depends 
from fastapi.middleware.cors import CORSMiddleware 
from pydantic import BaseModel 
from typing import List, Optional 
import psycopg2 
from psycopg2.extras import RealDictCursor 
import os 
from datetime import datetime 
import time
import logging
from fastapi import Query, Path, Request
from fastapi.responses import JSONResponse
from dataclasses import dataclass
from typing import Dict

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('app.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

app = FastAPI(title="TechStore API", version="1.0.0") 

app.start_time = time.time()

app.add_middleware( 
    CORSMiddleware, 
    allow_origins=["*"], 
    allow_credentials=True, 
    allow_methods=["*"],  
    allow_headers=["*"], 
) 

@dataclass
class Metrics:
    request_count: int = 0
    error_count: int = 0
    response_times: List[float] = None
    
    def __post_init__(self):
        if self.response_times is None:
            self.response_times = []

metrics = Metrics()

# Модели Pydantic
class ProductUpdate(BaseModel):
    name: Optional[str] = None
    price: Optional[float] = None
    category: Optional[str] = None
    description: Optional[str] = None 

class ProductBase(BaseModel): 
    name: str 
    price: float 
    category: str 
    description: Optional[str] = None 

class ProductCreate(ProductBase): 
    pass 

class Product(ProductBase): 
    id: int 
    created_at: datetime 

    class Config: 
        from_attributes = True 

def get_user():
    return {"user_id": 1, "username": "admin"}

def check_admin(user: dict = Depends(get_user)):
    if user.get("username") != "admin":
        logger.warning("user not admin")
        raise HTTPException(status_code=403, detail="NOT admin")
    return True
    
# Зависимость для получения соединения с БД 
def get_db_connection(): 
    for attempt in range(3):
        try:
            conn = psycopg2.connect(
                host=os.getenv("DB_HOST", "localhost"),
                database=os.getenv("DB_NAME", "techstore"),
                user=os.getenv("DB_USER", "postgres"),
                password=os.getenv("DB_PASSWORD", "password"),
                cursor_factory=RealDictCursor
            )
            return conn
        except Exception as e:
            if attempt < 2:
                logger.info("Retrying connection")
                time.sleep(1)
            else:
                logger.error("connection failed")
                raise HTTPException(
                    status_code=500, 
                    detail="connection failed"
                )

@app.middleware("http")
async def metrics_middleware(request: Request, call_next):
    start_time = time.time()
    metrics.request_count += 1
    
    try:
        response = await call_next(request)
        processing_time = time.time() - start_time
        metrics.response_times.append(processing_time)
        
        return response
        
    except Exception as e:
        metrics.error_count += 1
        raise e

@app.get("/metrics")
async def get_metrics():
    avg_response_time = sum(metrics.response_times) / len(metrics.response_times) if metrics.response_times else 0
    return {
        "request_count": metrics.request_count,
        "error_count": metrics.error_count,
        "avg_response_time": round(avg_response_time, 3),
        "total_response_time": round(sum(metrics.response_times), 3),
        "requests_per_second": round(metrics.request_count / (time.time() - app.start_time), 2)
    }

# Ручки CRUD операций 
@app.get("/") 
async def root(): 
    return {"message": "TechStore API", "version": "1.0.0"} 

@app.get("/products/", response_model=List[Product]) 
async def get_products(
    sort_by: str = "id",
    category: Optional[str] = None,
    limit: int = 100,  
    offset: int = 0,   
    conn = Depends(get_db_connection)
):
    """ 
    Получить список товаров с возможностью сортировки 
    """ 
    logger.info(f"Getting products")

    allowed_fields = ["id", "name", "price", "category", "created_at"]
    if sort_by not in allowed_fields:
        logger.warning(f"Invalid sort: {sort_by}")
        raise HTTPException(
            status_code=400, 
            detail="Invalid sort "
        )

    try:
        with conn.cursor() as cur:
            stmt = "SELECT id, name, price, category, description, created_at FROM products"
            params = []

            if category:
                stmt += " WHERE category = %s"
                params.append(category)

            stmt += f" ORDER BY {sort_by} ASC"

            stmt += " LIMIT %s OFFSET %s"
            params.extend([limit, offset])

            cur.execute(stmt, params)
            products = cur.fetchall()

        logger.info(f"Retrieved {len(products)} products")
        return products

    except Exception as e:
        logger.error(f"Error retrieving products: {e}")
        raise HTTPException(status_code=500, detail="server error")

@app.post("/products/", response_model=Product)
async def create_product(
    product: ProductCreate,  
    conn = Depends(get_db_connection),
    is_admin: bool = Depends(check_admin)
):
    """
    Создать новый товар
    """

    if len(product.name.strip()) == 0:
        logger.warning("empty name")
        raise HTTPException(status_code=400, detail="Product empty")
    
    if product.price <= 0:
        logger.warning("invalid price")
        raise HTTPException(status_code=400, detail="err price")
    
    if len(product.category.strip()) == 0:
        logger.warning("empty category")
        raise HTTPException(status_code=400, detail="Category empty")
    
    if len(product.name) > 255:
        logger.warning("Product name too long")
        raise HTTPException(status_code=400, detail="Product name too long")

    try:
        with conn.cursor() as cur:
            cur.execute("INSERT INTO products (name, price, category, description) VALUES (%s, %s, %s, %s) RETURNING id, name, price, category, description, created_at", 
            (product.name, product.price, product.category, product.description))
            
            new_product = cur.fetchone()
            conn.commit()
        logger.info("Product created")
        return new_product
            
    except psycopg2.IntegrityError:
        conn.rollback()
        logger.error("error creating product")
        raise HTTPException(status_code=400, detail="Double")
        
    except Exception as e:
        conn.rollback()
        logger.error("error creating product")
        raise HTTPException(status_code=500, detail="server error")

product_cache = {}

@app.get("/products/{product_id}", response_model=Product)   
async def get_product( 
    product_id: int,
    conn = Depends(get_db_connection)
): 
    """ 
    Получить товар по ID 
    """ 
    if product_id in product_cache:
        logger.debug(f"Product {product_id} found in cache")
        return product_cache[product_id]

    try:
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM products WHERE id = %s", (product_id,)) 
            product = cur.fetchone() 

        if not product: 
            logger.warning("Product not found")
            raise HTTPException(status_code=404, detail="Product not found")

        product_cache[product_id] = product
        return product

    except Exception as e:
        logger.error("Error retrieving product")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.put("/products/{product_id}", response_model=Product)
async def update_product(
    product_id: int,
    product: ProductCreate,  
    conn = Depends(get_db_connection),
    is_admin: bool = Depends(check_admin)
):
    """ 
    Обновить товар 
    """ 
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM products WHERE id = %s FOR UPDATE", (product_id,))
            current_product = cur.fetchone()
                    
            if not current_product:
                logger.warning("Product not found")
                raise HTTPException(status_code=404, detail="Product not found")
                        
            cur.execute(""" 
                UPDATE products  
                SET name = %s, price = %s, category = %s, description = %s 
                WHERE id = %s 
                RETURNING id, name, price, category, description, created_at 
            """, (product.name, product.price, product.category, product.description, product_id))
                        
            updated_product = cur.fetchone()
            conn.commit()
            
            return updated_product

    except Exception as e:
        conn.rollback()
        logger.error("Error updating product")
        raise HTTPException(status_code=500, detail="server error")

@app.patch("/products/{product_id}", response_model=Product)
async def partial_update_product(
    product_id: int,
    product: ProductUpdate,  
    conn = Depends(get_db_connection),
    is_admin: bool = Depends(check_admin)
):
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM products WHERE id = %s FOR UPDATE", (product_id,))
            current_product = cur.fetchone()
                    
            if not current_product:
                logger.warning("Product not found")
                raise HTTPException(status_code=404, detail="Product not found")
                    
            cur.execute("""
                UPDATE products 
                SET name = COALESCE(%s, name),
                price = COALESCE(%s, price),
                category = COALESCE(%s, category),
                description = COALESCE(%s, description)
                WHERE id = %s 
                RETURNING id, name, price, category, description, created_at
            """, (product.name, product.price, product.category, product.description, product_id))
                    
            updated_product = cur.fetchone()
            conn.commit()
            
            return updated_product

    except Exception as e:
        conn.rollback()
        logger.error("Error update product")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.delete("/products/{product_id}")
async def delete_product(
    product_id: int,
    confirm: bool = Query(..., description="Confirmation of deletion"),
    conn = Depends(get_db_connection),
    is_admin: bool = Depends(check_admin)
): 
    """ 
    Удалить товар   
    """ 
    if not confirm:
        logger.warning("Deletion cancelled")
        raise HTTPException(status_code=400, detail="Canceling a deletion")
    
    try:
        with conn.cursor() as cur:
            cur.execute("""
                UPDATE products 
                SET name = '[DELETE] ' || name, is_deleted = TRUE, deleted_at = CURRENT_TIMESTAMP
                WHERE id = %s AND is_deleted = FALSE
            """, (product_id,))
            conn.commit()
            
            if cur.rowcount == 0:
                logger.warning("Product not found")
                raise HTTPException(status_code=404, detail="Product not found")
            return {"message": "Product deleted successfully"} 
            
    except Exception as e:
        conn.rollback()
        logger.error("Error deleting product")
        raise HTTPException(status_code=500, detail="server err")

# Ручки для сортировки 
@app.get("/products/sort/{sort_type}", response_model=List[Product])
async def get_sorted_products(
    sort_type: str, 
    conn = Depends(get_db_connection)
): 
    """ 
    Получить товары с различными вариантами сортировки 
    """ 
    sort_mapping = {
        "name": "name ASC", 
        "name_desc": "name DESC",  
        "price": "price ASC", 
        "price_desc": "price DESC", 
        "category": "category ASC", 
        "id": "id ASC",
        "id_desc": "id DESC",
        "created_at": "created_at ASC",
        "created_at_desc": "created_at DESC",
        "price_name": "price ASC, name ASC",
        "category_price": "category ASC, price DESC",
        "name_price_desc": "name ASC, price DESC"
    }
    if sort_type not in sort_mapping:
        logger.warning("Invalid sort")
        raise HTTPException(
            status_code=400, 
            detail=f"Invalid sort type. Allowed: {list(sort_mapping.keys())}"
        )
    
    sort_expression = sort_mapping[sort_type]

    try:
        with conn.cursor() as cur: 
            stmt = f""" 
                SELECT id, name, price, category, description, created_at 
                FROM products  
                ORDER BY {sort_expression} 
            """
            logger.debug("Executing sorted")
            cur.execute(stmt)
            products = cur.fetchall()
        
        logger.info(f"Retrieved {len(products)} products with sort type: {sort_type}")
        return products

    except Exception as e:
        logger.error("Error sorted products")
        raise HTTPException(status_code=500, detail="server error")

request_times = {}

async def rate_limit_middleware(request: Request, call_next):
    client_ip = request.client.host
    current_time = time.time()
    
    if client_ip in request_times:
        time_window = [t for t in request_times[client_ip] if current_time - t < 60]
        if len(time_window) >= 10:
            logger.warning("Rate limit")
            return JSONResponse(
                status_code=429, 
                content={"detail": "Too many requests"}
            )
        time_window.append(current_time)
        request_times[client_ip] = time_window
    else:
        request_times[client_ip] = [current_time]
    
    response = await call_next(request)
    return response

app.middleware("http")(rate_limit_middleware)

if __name__ == "__main__":
    logger.info("Starting server")
    import uvicorn 
    uvicorn.run(app, host="0.0.0.0", port=8000)

