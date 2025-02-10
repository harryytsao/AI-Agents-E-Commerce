from typing import Optional, Dict, Any
import os
import logging
import psycopg2
import psycopg2.extras
from datetime import datetime

logger = logging.getLogger(__name__)

def load_product_data(product_id: str) -> Optional[Dict[str, Any]]:
    """Load product data from PostgreSQL database"""
    try:
        # Create connection using environment variables
        conn = psycopg2.connect(
            os.getenv('DATABASE_URL')
        )
        cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        
        # Try both UUID and string matching
        cursor.execute("""
            SELECT product_id,
                   name,
                   category,
                   price,
                   attributes,
                   history
            FROM products
            WHERE product_id::text = %s
               OR name ILIKE %s
               OR product_id = %s
        """, (product_id, f"%{product_id}%", product_id))
        
        product = cursor.fetchone()
        
        if not product:
            logger.warning(f"Product not found: {product_id}")
            return None
            
        # Convert to dictionary and ensure JSONB fields are parsed
        result = dict(product)
        # Parse JSONB fields if they're not None
        if result['attributes']:
            result['attributes'] = dict(result['attributes'])
        if result['history']:
            result['history'] = list(result['history'])
            
        return result
        
    except Exception as e:
        logger.error(f"Error loading product data: {e}")
        return None
        
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close() 