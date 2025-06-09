import mysql.connector
from mysql.connector import Error
import threading
from decimal import Decimal

class Database:
    _instance = None
    _pool = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(Database, cls).__new__(cls)
            cls._instance._initialize_pool()
        return cls._instance
    
    def _initialize_pool(self):
        if self._pool is None:
            try:
                self._pool = mysql.connector.pooling.MySQLConnectionPool(
                    pool_name="mypool",
                    pool_size=5,
                    host="localhost",
                    user="root",
                    password="H4ckm3!_",
                    database="boarding_house"
                )
                print("Database connection established successfully")
            except Error as e:
                print(f"Error connecting to database: {e}")
                raise
    
    def get_connection(self):
        return self._pool.get_connection()
    
    def execute(self, query, params=None):
        """Execute a query that doesn't return results"""
        conn = None
        cursor = None
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            cursor.execute(query, params or ())
            conn.commit()
        except Error as e:
            if conn:
                conn.rollback()
            print(f"Error executing query: {e}")
            raise
        finally:
            if cursor:
                cursor.close()
            if conn:
                conn.close()
    
    def create_tables(self):
        """Create all necessary tables if they don't exist"""
        try:
            # Create tenants table
            self.execute("""
                CREATE TABLE IF NOT EXISTS tenants (
                    tenant_id INT AUTO_INCREMENT PRIMARY KEY,
                    first_name VARCHAR(50) NOT NULL,
                    last_name VARCHAR(50) NOT NULL,
                    email VARCHAR(100) UNIQUE,
                    phone VARCHAR(20),
                    room_id INT,
                    check_in_date DATE,
                    check_out_date DATE,
                    profile_image VARCHAR(255),
                    monthly_rate DECIMAL(10,2) DEFAULT 0.00,
                    total_amount DECIMAL(10,2) DEFAULT 0.00,
                    balance DECIMAL(10,2) DEFAULT 0.00,
                    FOREIGN KEY (room_id) REFERENCES rooms(room_id)
                )
            """)
            
            # Create rooms table
            self.execute("""
                CREATE TABLE IF NOT EXISTS rooms (
                    room_id INT AUTO_INCREMENT PRIMARY KEY,
                    room_number VARCHAR(10) NOT NULL UNIQUE,
                    capacity INT NOT NULL,
                    price DECIMAL(10,2) NOT NULL,
                    status ENUM('Available', 'Occupied', 'Maintenance') DEFAULT 'Available'
                )
            """)
            
            # Create payments table
            self.execute("""
                CREATE TABLE IF NOT EXISTS payments (
                    payment_id INT AUTO_INCREMENT PRIMARY KEY,
                    tenant_id INT,
                    amount_rent DECIMAL(10,2) NOT NULL,
                    amount_paid DECIMAL(10,2) DEFAULT 0.00,
                    balance DECIMAL(10,2) NOT NULL,
                    payment_date DATE,
                    payment_method VARCHAR(32),
                    status VARCHAR(32) DEFAULT 'Pending',
                    description TEXT,
                    FOREIGN KEY (tenant_id) REFERENCES tenants(tenant_id)
                )
            """)
            
            # Create maintenance table
            self.execute("""
                CREATE TABLE IF NOT EXISTS maintenance (
                    maintenance_id INT AUTO_INCREMENT PRIMARY KEY,
                    room_id INT,
                    issue_description TEXT NOT NULL,
                    status ENUM('Pending', 'In Progress', 'Completed') DEFAULT 'Pending',
                    reported_date DATE NOT NULL,
                    completed_date DATE,
                    cost DECIMAL(10,2) DEFAULT 0.00,
                    FOREIGN KEY (room_id) REFERENCES rooms(room_id)
                )
            """)
            
            print("All tables created successfully")
        except Exception as e:
            print(f"Error creating tables: {e}")
            raise
    
    def execute_query(self, query, params=None):
        """Execute a query and return all results"""
        conn = None
        cursor = None
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            cursor.execute(query, params or ())
            return cursor.fetchall()
        except Error as e:
            print(f"Error executing query: {e}")
            raise
        finally:
            if cursor:
                cursor.close()
            if conn:
                conn.close()
    
    def fetch_one(self, query, params=None):
        """Execute a query and return one result"""
        conn = None
        cursor = None
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            cursor.execute(query, params or ())
            return cursor.fetchone()
        except Error as e:
            print(f"Error executing query: {e}")
            raise
        finally:
            if cursor:
                cursor.close()
            if conn:
                conn.close()
    
    def fetch_all(self, query, params=None):
        """Execute a query and return all results"""
        return self.execute_query(query, params)
    
    def insert(self, query, params=None):
        """Execute an insert query and return the last insert ID"""
        conn = None
        cursor = None
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            cursor.execute(query, params or ())
            conn.commit()
            return cursor.lastrowid
        except Error as e:
            if conn:
                conn.rollback()
            print(f"Error executing insert: {e}")
            raise
        finally:
            if cursor:
                cursor.close()
            if conn:
                conn.close()
    
    def update(self, query, params=None):
        """Execute an update query and return the number of affected rows"""
        conn = None
        cursor = None
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            cursor.execute(query, params or ())
            conn.commit()
            return cursor.rowcount
        except Error as e:
            if conn:
                conn.rollback()
            print(f"Error executing update: {e}")
            raise
        finally:
            if cursor:
                cursor.close()
            if conn:
                conn.close()
    
    def delete(self, query, params=None):
        """Execute a delete query and return the number of affected rows"""
        return self.update(query, params)
    
    def close(self):
        """Close all connections in the pool"""
        if self._pool:
            try:
                for conn in self._pool._cnx_queue:
                    conn.close()
                print("Database connections closed successfully")
            except Exception as e:
                print(f"Error closing database connections: {e}")
    
    def __del__(self):
        """Destructor to ensure connections are closed"""
        self.close() 