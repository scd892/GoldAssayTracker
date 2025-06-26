import sqlite3
import pandas as pd
from datetime import datetime

def _check_column_exists(cursor, table, column):
    """Check if a column exists in a SQLite table"""
    cursor.execute(f"PRAGMA table_info({table})")
    columns = [row[1] for row in cursor.fetchall()]
    return column in columns

def init_interlab_db():
    """Initialize the tables for inter-laboratory comparisons in the existing database"""
    conn = sqlite3.connect('gold_assay.db')
    cursor = conn.cursor()
    
    # Check if external_labs table exists
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='external_labs'")
    table_exists = cursor.fetchone() is not None
    
    if not table_exists:
        # Create external_labs table if it doesn't exist
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS external_labs (
            lab_id INTEGER PRIMARY KEY AUTOINCREMENT,
            lab_name TEXT NOT NULL,
            accreditation TEXT,
            industry_sector TEXT,
            is_active INTEGER DEFAULT 1,
            is_benchmark INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            notes TEXT
        )
        ''')
    else:
        # Check and add new columns if they don't exist
        if not _check_column_exists(cursor, "external_labs", "accreditation"):
            cursor.execute("ALTER TABLE external_labs ADD COLUMN accreditation TEXT")
        
        if not _check_column_exists(cursor, "external_labs", "industry_sector"):
            cursor.execute("ALTER TABLE external_labs ADD COLUMN industry_sector TEXT")
            
        if not _check_column_exists(cursor, "external_labs", "is_benchmark"):
            cursor.execute("ALTER TABLE external_labs ADD COLUMN is_benchmark INTEGER DEFAULT 0")
    
    
    # Check if interlab_results table exists
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='interlab_results'")
    table_exists = cursor.fetchone() is not None
    
    if not table_exists:
        # Create interlab_results table if it doesn't exist
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS interlab_results (
            result_id INTEGER PRIMARY KEY AUTOINCREMENT,
            lab_id INTEGER NOT NULL,
            sample_id TEXT NOT NULL,
            gold_content REAL NOT NULL,
            assayer_id INTEGER,
            internal_gold_content REAL,
            test_date TIMESTAMP NOT NULL,
            method_used TEXT,
            uncertainty REAL,
            notes TEXT,
            FOREIGN KEY (lab_id) REFERENCES external_labs (lab_id),
            FOREIGN KEY (assayer_id) REFERENCES assayers (assayer_id),
            UNIQUE(lab_id, sample_id)
        )
        ''')
    else:
        # Check and add new columns if they don't exist
        if not _check_column_exists(cursor, "interlab_results", "assayer_id"):
            cursor.execute("ALTER TABLE interlab_results ADD COLUMN assayer_id INTEGER")
            
        if not _check_column_exists(cursor, "interlab_results", "internal_gold_content"):
            cursor.execute("ALTER TABLE interlab_results ADD COLUMN internal_gold_content REAL")
    
    # Create interlab_comparisons table for matching external samples with internal ones
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS interlab_comparisons (
        comparison_id INTEGER PRIMARY KEY AUTOINCREMENT,
        internal_sample_id TEXT NOT NULL,
        external_sample_id TEXT NOT NULL,
        reference_value REAL,
        comparison_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        notes TEXT,
        UNIQUE(internal_sample_id, external_sample_id)
    )
    ''')
    
    conn.commit()
    conn.close()
    return True

def add_external_lab(lab_name, accreditation="", industry_sector="", notes=""):
    """Add a new external laboratory to the database"""
    conn = sqlite3.connect('gold_assay.db')
    cursor = conn.cursor()
    
    try:
        cursor.execute('''
        INSERT INTO external_labs (lab_name, accreditation, industry_sector, notes)
        VALUES (?, ?, ?, ?)
        ''', (lab_name, accreditation, industry_sector, notes))
        
        conn.commit()
        success = True
    except sqlite3.Error as e:
        print(f"Database error: {e}")
        conn.rollback()
        success = False
    finally:
        conn.close()
    
    return success

def get_external_labs():
    """Get list of all active external laboratories"""
    conn = sqlite3.connect('gold_assay.db')
    cursor = conn.cursor()
    
    # Check which columns exist
    cursor.execute("PRAGMA table_info(external_labs)")
    columns = [row[1] for row in cursor.fetchall()]
    
    # Build a query based on available columns
    select_columns = ["lab_id", "lab_name"]
    if "accreditation" in columns:
        select_columns.append("accreditation")
    if "industry_sector" in columns:
        select_columns.append("industry_sector")
    if "is_benchmark" in columns:
        select_columns.append("is_benchmark")
    select_columns.extend(["notes", "created_at"])
    
    query = f"""
    SELECT 
        {', '.join(select_columns)}
    FROM external_labs
    WHERE is_active = 1
    ORDER BY lab_name
    """
    
    labs_df = pd.read_sql(query, conn)
    
    # Add missing columns if they don't exist
    if "accreditation" not in labs_df.columns:
        labs_df["accreditation"] = ""
    if "industry_sector" not in labs_df.columns:
        labs_df["industry_sector"] = ""
    if "is_benchmark" not in labs_df.columns:
        labs_df["is_benchmark"] = 0
    
    conn.close()
    
    return labs_df

def update_external_lab(lab_id, lab_name, accreditation="", industry_sector="", notes=""):
    """Update an existing external laboratory"""
    conn = sqlite3.connect('gold_assay.db')
    cursor = conn.cursor()
    
    try:
        # Check which columns exist
        cursor.execute("PRAGMA table_info(external_labs)")
        columns = [row[1] for row in cursor.fetchall()]
        
        # Ensure the columns exist before updating
        if "accreditation" not in columns:
            cursor.execute("ALTER TABLE external_labs ADD COLUMN accreditation TEXT")
        
        if "industry_sector" not in columns:
            cursor.execute("ALTER TABLE external_labs ADD COLUMN industry_sector TEXT")
        
        # Now do the update with all fields
        cursor.execute('''
        UPDATE external_labs
        SET lab_name = ?, accreditation = ?, industry_sector = ?, notes = ?
        WHERE lab_id = ?
        ''', (lab_name, accreditation, industry_sector, notes, lab_id))
        
        conn.commit()
        success = True
    except sqlite3.Error as e:
        print(f"Database error: {e}")
        conn.rollback()
        success = False
    finally:
        conn.close()
    
    return success

def delete_external_lab(lab_id):
    """Delete (deactivate) an external laboratory by setting is_active to 0"""
    conn = sqlite3.connect('gold_assay.db')
    cursor = conn.cursor()
    
    try:
        # Check if any interlab results exist for this lab
        cursor.execute("SELECT COUNT(*) FROM interlab_results WHERE lab_id = ?", (lab_id,))
        count = cursor.fetchone()[0]
        
        if count > 0:
            message = f"Cannot delete lab with ID {lab_id} because it has {count} results. Consider deactivating instead."
            return False, message
        
        # Deactivate the lab instead of deleting
        cursor.execute("UPDATE external_labs SET is_active = 0 WHERE lab_id = ?", (lab_id,))
        
        conn.commit()
        return True, "Laboratory deactivated successfully"
    except sqlite3.Error as e:
        conn.rollback()
        return False, f"Database error: {e}"
    finally:
        conn.close()

def add_interlab_result(lab_id, sample_id, gold_content, assayer_id=None, internal_gold_content=None, test_date=None, method_used="", uncertainty=None, notes=""):
    """Add a new inter-laboratory result to the database"""
    conn = sqlite3.connect('gold_assay.db')
    cursor = conn.cursor()
    
    # Set default test_date to now if not provided
    if test_date is None:
        test_date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    try:
        # Check if columns exist
        cursor.execute("PRAGMA table_info(interlab_results)")
        columns = [row[1] for row in cursor.fetchall()]
        
        if "assayer_id" not in columns:
            cursor.execute("ALTER TABLE interlab_results ADD COLUMN assayer_id INTEGER")
            
        if "internal_gold_content" not in columns:
            cursor.execute("ALTER TABLE interlab_results ADD COLUMN internal_gold_content REAL")
        
        # Insert with new fields
        cursor.execute('''
        INSERT INTO interlab_results 
        (lab_id, sample_id, gold_content, assayer_id, internal_gold_content, test_date, method_used, uncertainty, notes)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (lab_id, sample_id, gold_content, assayer_id, internal_gold_content, test_date, method_used, uncertainty, notes))
        
        conn.commit()
        success = True
    except sqlite3.IntegrityError:
        # Duplicate entry
        conn.rollback()
        success = False
    except sqlite3.Error as e:
        print(f"Database error: {e}")
        conn.rollback()
        success = False
    finally:
        conn.close()
    
    return success

def get_interlab_results(lab_id=None, days=365):
    """Get inter-laboratory results with optional lab filtering"""
    conn = sqlite3.connect('gold_assay.db')
    cursor = conn.cursor()
    
    # Check which columns exist in interlab_results
    cursor.execute("PRAGMA table_info(interlab_results)")
    columns = [row[1] for row in cursor.fetchall()]
    
    # Start building the query
    where_clause = "WHERE 1=1"
    params = []
    
    if lab_id is not None:
        where_clause += " AND r.lab_id = ?"
        params.append(lab_id)
    
    if days > 0:
        # For date functions, we need to directly format the string
        lookback_date = f"date('now', '-{days} days')"
        where_clause += f" AND date(r.test_date) >= {lookback_date}"
    
    # Define the left join for assayers if the assayer_id column exists
    assayer_join = ""
    assayer_fields = ""
    if "assayer_id" in columns:
        assayer_join = "LEFT JOIN assayers a ON r.assayer_id = a.assayer_id"
        assayer_fields = ", a.name as assayer_name"
    
    query = f"""
    SELECT 
        r.*, l.lab_name{assayer_fields}
    FROM interlab_results r
    JOIN external_labs l ON r.lab_id = l.lab_id
    {assayer_join}
    {where_clause}
    ORDER BY r.test_date DESC
    """
    
    results_df = pd.read_sql(query, conn, params=params if params else None)
    
    # Add empty assayer_name column if it doesn't exist
    if "assayer_name" not in results_df.columns and "assayer_id" in columns:
        results_df["assayer_name"] = ""
    
    conn.close()
    
    return results_df

def create_interlab_comparison(internal_sample_id, external_sample_id, reference_value=None, notes=""):
    """Create a comparison between internal and external samples"""
    conn = sqlite3.connect('gold_assay.db')
    cursor = conn.cursor()
    
    try:
        cursor.execute('''
        INSERT INTO interlab_comparisons 
        (internal_sample_id, external_sample_id, reference_value, notes)
        VALUES (?, ?, ?, ?)
        ''', (internal_sample_id, external_sample_id, reference_value, notes))
        
        conn.commit()
        success = True
    except sqlite3.IntegrityError:
        # Duplicate entry
        conn.rollback()
        success = False
    except sqlite3.Error as e:
        print(f"Database error: {e}")
        conn.rollback()
        success = False
    finally:
        conn.close()
    
    return success

def set_external_lab_benchmark(lab_id):
    """Set an external laboratory as the benchmark"""
    conn = sqlite3.connect('gold_assay.db')
    cursor = conn.cursor()
    
    try:
        # First, ensure the column exists
        cursor.execute("PRAGMA table_info(external_labs)")
        columns = [row[1] for row in cursor.fetchall()]
        
        if "is_benchmark" not in columns:
            cursor.execute("ALTER TABLE external_labs ADD COLUMN is_benchmark INTEGER DEFAULT 0")
        
        # Clear any existing benchmark
        cursor.execute("UPDATE external_labs SET is_benchmark = 0")
        
        # Set the new benchmark
        cursor.execute("UPDATE external_labs SET is_benchmark = 1 WHERE lab_id = ?", (lab_id,))
        
        conn.commit()
        return True, "Benchmark laboratory set successfully"
    except sqlite3.Error as e:
        conn.rollback()
        return False, f"Database error: {e}"
    finally:
        conn.close()

def get_external_lab_benchmark():
    """Get the current benchmark external laboratory"""
    conn = sqlite3.connect('gold_assay.db')
    cursor = conn.cursor()
    
    try:
        # Check if the is_benchmark column exists
        cursor.execute("PRAGMA table_info(external_labs)")
        columns = [row[1] for row in cursor.fetchall()]
        
        if "is_benchmark" not in columns:
            return None
        
        # Get the benchmark lab
        cursor.execute("""
        SELECT lab_id, lab_name 
        FROM external_labs 
        WHERE is_benchmark = 1 AND is_active = 1
        LIMIT 1
        """)
        
        result = cursor.fetchone()
        
        if result:
            return {"lab_id": result[0], "lab_name": result[1]}
        else:
            return None
    finally:
        conn.close()

def get_interlab_comparisons(days=365):
    """Get inter-laboratory comparison data"""
    conn = sqlite3.connect('gold_assay.db')
    
    # Create a safer version using direct string formatting for the date condition
    # This avoids parameter binding issues with SQLite's date functions
    lookback_date = f"date('now', '-{days} days')"
    
    query = f"""
    WITH internal_results AS (
        SELECT 
            ar.sample_id as internal_sample_id,
            ar.gold_content as internal_gold_content,
            a.name as assayer_name,
            ar.test_date as internal_test_date
        FROM assay_results ar
        JOIN assayers a ON ar.assayer_id = a.assayer_id
        WHERE date(ar.test_date) >= {lookback_date}
    ),
    
    external_results AS (
        SELECT 
            ir.sample_id as external_sample_id,
            ir.gold_content as external_gold_content,
            el.lab_name,
            ir.test_date as external_test_date,
            ir.method_used,
            ir.uncertainty
        FROM interlab_results ir
        JOIN external_labs el ON ir.lab_id = el.lab_id
        WHERE date(ir.test_date) >= {lookback_date}
    )
    
    SELECT 
        ic.comparison_id,
        ic.internal_sample_id,
        ic.external_sample_id,
        COALESCE(ic.reference_value, ir.internal_gold_content) as reference_value,
        ir.internal_gold_content,
        er.external_gold_content,
        ir.assayer_name,
        er.lab_name,
        ir.internal_test_date,
        er.external_test_date,
        er.method_used,
        er.uncertainty,
        (er.external_gold_content - ir.internal_gold_content) as absolute_deviation,
        ((er.external_gold_content - ir.internal_gold_content) / ir.internal_gold_content * 100) as percentage_deviation,
        ic.comparison_date,
        ic.notes
    FROM interlab_comparisons ic
    JOIN internal_results ir ON ic.internal_sample_id = ir.internal_sample_id
    JOIN external_results er ON ic.external_sample_id = er.external_sample_id
    WHERE date(ic.comparison_date) >= {lookback_date}
    ORDER BY ic.comparison_date DESC
    """
    
    # No parameters needed as the date is now directly in the query
    comparisons_df = pd.read_sql(query, conn)
    conn.close()
    
    # If no data is found, return an empty DataFrame with the expected columns
    if comparisons_df.empty:
        # Create a minimal empty DataFrame with expected columns
        columns = [
            'comparison_id', 'internal_sample_id', 'external_sample_id', 
            'reference_value', 'internal_gold_content', 'external_gold_content', 
            'assayer_name', 'lab_name', 'absolute_deviation'
        ]
        return pd.DataFrame(columns=columns)
    
    return comparisons_df