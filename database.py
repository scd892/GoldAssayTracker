import sqlite3
import pandas as pd
from datetime import datetime

def _check_column_exists(cursor, table, column):
    """Check if a column exists in a SQLite table"""
    cursor.execute(f"PRAGMA table_info({table})")
    columns = cursor.fetchall()
    return any(col[1] == column for col in columns)

def init_db():
    """Initialize the SQLite database and create necessary tables if they don't exist"""
    conn = sqlite3.connect('gold_assay.db')
    cursor = conn.cursor()
    
    # Create table for assayers
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS assayers (
        assayer_id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        employee_id TEXT UNIQUE,
        is_active INTEGER DEFAULT 1,
        joining_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        profile_picture TEXT DEFAULT '',
        work_experience TEXT DEFAULT ''
    )
    ''')
    
    # Create table for assay results
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS assay_results (
        result_id INTEGER PRIMARY KEY AUTOINCREMENT,
        assayer_id INTEGER NOT NULL,
        sample_id TEXT NOT NULL,
        gold_content REAL NOT NULL,
        test_date TIMESTAMP NOT NULL,
        notes TEXT,
        FOREIGN KEY (assayer_id) REFERENCES assayers (assayer_id),
        UNIQUE(assayer_id, sample_id)
    )
    ''')
    
    # Add gold_type column if it doesn't exist
    if not _check_column_exists(cursor, "assay_results", "gold_type"):
        cursor.execute("ALTER TABLE assay_results ADD COLUMN gold_type TEXT DEFAULT 'Unknown'")
        conn.commit()
        print("Added gold_type column to assay_results table")
        
    # Add bar_weight_grams column if it doesn't exist
    if not _check_column_exists(cursor, "assay_results", "bar_weight_grams"):
        cursor.execute("ALTER TABLE assay_results ADD COLUMN bar_weight_grams REAL DEFAULT 0")
        conn.commit()
        print("Added bar_weight_grams column to assay_results table")
    
    # Create table for benchmark assayers
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS benchmark_assayers (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        assayer_id INTEGER NOT NULL,
        set_date TIMESTAMP NOT NULL,
        is_active INTEGER DEFAULT 1,
        FOREIGN KEY (assayer_id) REFERENCES assayers (assayer_id)
    )
    ''')
    
    conn.commit()
    conn.close()

def add_assayer(name, employee_id, joining_date=None, profile_picture="", work_experience=""):
    """Add a new assayer to the database with optional profile information"""
    conn = sqlite3.connect('gold_assay.db')
    cursor = conn.cursor()
    
    if joining_date is None:
        joining_date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    try:
        cursor.execute(
            """INSERT INTO assayers 
               (name, employee_id, joining_date, profile_picture, work_experience) 
               VALUES (?, ?, ?, ?, ?)""",
            (name, employee_id, joining_date, profile_picture, work_experience)
        )
        conn.commit()
        success = True
    except sqlite3.IntegrityError:
        success = False
    
    conn.close()
    return success

def get_assayers():
    """Get list of all active assayers"""
    conn = sqlite3.connect('gold_assay.db')
    assayers_df = pd.read_sql("SELECT * FROM assayers WHERE is_active = 1", conn)
    conn.close()
    return assayers_df

def update_assayer(assayer_id, name, employee_id, joining_date=None, profile_picture=None, work_experience=None):
    """Update an existing assayer's information including profile data"""
    conn = sqlite3.connect('gold_assay.db')
    cursor = conn.cursor()
    
    try:
        # First, build the update query based on which parameters were provided
        update_parts = ["name = ?", "employee_id = ?"]
        params = [name, employee_id]
        
        if joining_date is not None:
            update_parts.append("joining_date = ?")
            params.append(joining_date)
        
        if profile_picture is not None:
            update_parts.append("profile_picture = ?")
            params.append(profile_picture)
            
        if work_experience is not None:
            update_parts.append("work_experience = ?")
            params.append(work_experience)
            
        # Add the assayer_id to the params
        params.append(assayer_id)
        
        # Construct and execute the query
        query = f"""
        UPDATE assayers
        SET {", ".join(update_parts)}
        WHERE assayer_id = ?
        """
        
        cursor.execute(query, params)
        conn.commit()
        success = True
    except sqlite3.IntegrityError:
        # This happens if the employee_id already exists for another assayer
        conn.rollback()
        success = False
    finally:
        conn.close()
        
    return success

def delete_assayer(assayer_id):
    """Delete (deactivate) an assayer by setting is_active to 0"""
    conn = sqlite3.connect('gold_assay.db')
    cursor = conn.cursor()
    
    # Check if this is a benchmark assayer
    cursor.execute('SELECT id FROM benchmark_assayers WHERE assayer_id = ? AND is_active = 1', (assayer_id,))
    is_benchmark = cursor.fetchone() is not None
    
    if is_benchmark:
        conn.close()
        return False, "Cannot delete the current benchmark assayer"
    
    try:
        # Set the assayer as inactive instead of actually deleting
        cursor.execute('UPDATE assayers SET is_active = 0 WHERE assayer_id = ?', (assayer_id,))
        conn.commit()
        success = True
        message = "Assayer deactivated successfully"
    except Exception as e:
        conn.rollback()
        success = False
        message = str(e)
    finally:
        conn.close()
        
    return success, message

def add_assay_result(assayer_id, sample_id, gold_content, test_date=None, notes="", gold_type="Unknown", bar_weight_grams=0):
    """Add a new assay result to the database"""
    if test_date is None:
        test_date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    conn = sqlite3.connect('gold_assay.db')
    cursor = conn.cursor()
    
    try:
        # Check if gold_type column exists, add it if it doesn't
        if not _check_column_exists(cursor, "assay_results", "gold_type"):
            cursor.execute("ALTER TABLE assay_results ADD COLUMN gold_type TEXT DEFAULT 'Unknown'")
            conn.commit()
            print("Added gold_type column to assay_results table")
            
        # Check if bar_weight_grams column exists, add it if it doesn't
        if not _check_column_exists(cursor, "assay_results", "bar_weight_grams"):
            cursor.execute("ALTER TABLE assay_results ADD COLUMN bar_weight_grams REAL DEFAULT 0")
            conn.commit()
            print("Added bar_weight_grams column to assay_results table")
        
        cursor.execute(
            "INSERT OR REPLACE INTO assay_results (assayer_id, sample_id, gold_content, test_date, notes, gold_type, bar_weight_grams) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (assayer_id, sample_id, gold_content, test_date, notes, gold_type, bar_weight_grams)
        )
        conn.commit()
        success = True
    except Exception as e:
        print(f"Error adding assay result: {e}")
        success = False
    
    conn.close()
    return success

def update_assay_result(result_id, gold_content, notes="", gold_type=None, bar_weight_grams=None):
    """Update an existing assay result"""
    conn = sqlite3.connect('gold_assay.db')
    cursor = conn.cursor()
    
    try:
        # Check if gold_type column exists, add it if it doesn't
        if not _check_column_exists(cursor, "assay_results", "gold_type"):
            cursor.execute("ALTER TABLE assay_results ADD COLUMN gold_type TEXT DEFAULT 'Unknown'")
            conn.commit()
            print("Added gold_type column to assay_results table")
            
        # Check if bar_weight_grams column exists, add it if it doesn't
        if not _check_column_exists(cursor, "assay_results", "bar_weight_grams"):
            cursor.execute("ALTER TABLE assay_results ADD COLUMN bar_weight_grams REAL DEFAULT 0")
            conn.commit()
            print("Added bar_weight_grams column to assay_results table")
        
        # Build dynamic SQL based on provided parameters
        update_parts = ["gold_content = ?", "notes = ?"]
        params = [gold_content, notes]
        
        if gold_type is not None:
            update_parts.append("gold_type = ?")
            params.append(gold_type)
            
        if bar_weight_grams is not None:
            update_parts.append("bar_weight_grams = ?")
            params.append(bar_weight_grams)
            
        # Add the result_id to the params
        params.append(result_id)
        
        # Construct and execute the query
        query = f"""
        UPDATE assay_results
        SET {", ".join(update_parts)}
        WHERE result_id = ?
        """
        
        cursor.execute(query, params)
        conn.commit()
        success = True
        message = "Assay result updated successfully"
    except Exception as e:
        conn.rollback()
        success = False
        message = str(e)
    finally:
        conn.close()
        
    return success, message

def delete_assay_result(result_id):
    """Delete an assay result"""
    conn = sqlite3.connect('gold_assay.db')
    cursor = conn.cursor()
    
    # Check if this result is from a benchmark assayer
    cursor.execute('''
    SELECT a.assayer_id FROM assay_results r
    JOIN benchmark_assayers a ON r.assayer_id = a.assayer_id 
    WHERE r.result_id = ? AND a.is_active = 1
    ''', (result_id,))
    
    is_benchmark = cursor.fetchone() is not None
    
    if is_benchmark:
        conn.close()
        return False, "Cannot delete results from the benchmark assayer"
    
    try:
        cursor.execute('DELETE FROM assay_results WHERE result_id = ?', (result_id,))
        conn.commit()
        success = True
        message = "Assay result deleted successfully"
    except Exception as e:
        conn.rollback()
        success = False
        message = str(e)
    finally:
        conn.close()
        
    return success, message

def get_assay_result(result_id):
    """Get details of a specific assay result"""
    conn = sqlite3.connect('gold_assay.db')
    # Use parameterized query to prevent SQL injection
    query = """
        SELECT r.*, a.name as assayer_name
        FROM assay_results r
        JOIN assayers a ON r.assayer_id = a.assayer_id
        WHERE r.result_id = ?
    """
    # Pass parameters as a tuple
    result_df = pd.read_sql(query, conn, params=(result_id,))
    conn.close()
    
    if result_df.empty:
        return None
    else:
        return result_df.iloc[0]

def set_benchmark_assayer(assayer_id):
    """Set an assayer as the benchmark"""
    conn = sqlite3.connect('gold_assay.db')
    cursor = conn.cursor()
    
    # First, deactivate all current benchmark assayers
    cursor.execute("UPDATE benchmark_assayers SET is_active = 0")
    
    # Then, add the new benchmark assayer
    cursor.execute(
        "INSERT INTO benchmark_assayers (assayer_id, set_date, is_active) VALUES (?, ?, 1)",
        (assayer_id, datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
    )
    
    conn.commit()
    conn.close()
    return True

def get_current_benchmark():
    """Get the current benchmark assayer"""
    conn = sqlite3.connect('gold_assay.db')
    benchmark_df = pd.read_sql("""
        SELECT b.assayer_id, a.name, b.set_date
        FROM benchmark_assayers b
        JOIN assayers a ON b.assayer_id = a.assayer_id
        WHERE b.is_active = 1
        ORDER BY b.set_date DESC
        LIMIT 1
    """, conn)
    conn.close()
    
    if benchmark_df.empty:
        return None
    else:
        return benchmark_df.iloc[0]

def get_assay_results(days=30):
    """Get assay results for the specified number of days"""
    conn = sqlite3.connect('gold_assay.db')
    query = f"""
        SELECT r.*, a.name as assayer_name
        FROM assay_results r
        JOIN assayers a ON r.assayer_id = a.assayer_id
        WHERE date(r.test_date) >= date('now', '-{days} days')
        ORDER BY r.test_date DESC
    """
    results_df = pd.read_sql(query, conn)
    conn.close()
    return results_df

def search_assay_results(search_term=None, sample_id=None, assayer_id=None, date_from=None, date_to=None, limit=100):
    """Search for assay results with various filters"""
    conn = sqlite3.connect('gold_assay.db')
    
    conditions = []
    params = []
    
    # Build the WHERE clause based on provided parameters
    if search_term:
        conditions.append("(r.sample_id LIKE ? OR a.name LIKE ? OR r.notes LIKE ?)")
        search_pattern = f"%{search_term}%"
        params.extend([search_pattern, search_pattern, search_pattern])
    
    if sample_id:
        conditions.append("r.sample_id = ?")
        params.append(sample_id)
    
    if assayer_id:
        conditions.append("r.assayer_id = ?")
        params.append(assayer_id)
    
    if date_from:
        conditions.append("date(r.test_date) >= date(?)")
        # If it's a datetime object, convert to string
        if hasattr(date_from, 'strftime'):
            date_from = date_from.strftime('%Y-%m-%d')
        params.append(date_from)
    
    if date_to:
        conditions.append("date(r.test_date) <= date(?)")
        # If it's a datetime object, convert to string
        if hasattr(date_to, 'strftime'):
            date_to = date_to.strftime('%Y-%m-%d')
        params.append(date_to)
    
    # Combine conditions with AND
    where_clause = " AND ".join(conditions) if conditions else "1=1"
    
    query = f"""
        SELECT r.*, a.name as assayer_name
        FROM assay_results r
        JOIN assayers a ON r.assayer_id = a.assayer_id
        WHERE {where_clause}
        ORDER BY r.test_date DESC
        LIMIT {limit}
    """
    
    results_df = pd.read_sql(query, conn, params=params)
    conn.close()
    return results_df

def get_deviations_from_benchmark(days=365):
    """Calculate deviations from the benchmark assayer for each sample
    
    Args:
        days: Number of days to look back for data (default: 365 to get plenty of data)
        
    Returns:
        DataFrame with deviation calculations or None if no benchmark is set
    """
    conn = sqlite3.connect('gold_assay.db')
    
    # Add debug statements to print to console
    
    
    # Check if there's a benchmark assayer
    benchmark_df = pd.read_sql("SELECT assayer_id FROM benchmark_assayers WHERE is_active = 1 LIMIT 1", conn)
    if benchmark_df.empty:
        
        conn.close()
        return None
    
    benchmark_id = benchmark_df.iloc[0]['assayer_id']
    
    
    # TEMPORARY: Remove gold_type from query and add some debugging
    
    
    # Get all samples tested by the benchmark assayer
    # Fixed query with direct string formatting for date to avoid SQLite parameter binding issues
    query = f"""
        SELECT r.*, a.name as assayer_name,
               b.gold_content as benchmark_value,
               (r.gold_content - b.gold_content) as deviation,
               ABS(r.gold_content - b.gold_content) as absolute_deviation,
               (r.gold_content - b.gold_content) / b.gold_content * 100 as percentage_deviation
        FROM assay_results r
        JOIN assayers a ON r.assayer_id = a.assayer_id
        JOIN assay_results b ON r.sample_id = b.sample_id AND b.assayer_id = {benchmark_id}
        WHERE r.assayer_id != {benchmark_id}
        ORDER BY r.test_date DESC, r.sample_id
    """
    
    deviations_df = pd.read_sql(query, conn)
    
    # Clean up and close connection
    conn.close()
    
    # Check results
    if deviations_df.empty:
        return pd.DataFrame()
    
    # Convert timestamp to datetime
    deviations_df['test_date'] = pd.to_datetime(deviations_df['test_date'])
    
    return deviations_df

def get_samples_for_date_range(start_date, end_date):
    """Get all samples for a specific date range"""
    conn = sqlite3.connect('gold_assay.db')
    query = """
        SELECT r.*, a.name as assayer_name
        FROM assay_results r
        JOIN assayers a ON r.assayer_id = a.assayer_id
        WHERE date(r.test_date) BETWEEN ? AND ?
        ORDER BY r.test_date DESC, r.sample_id
    """
    results_df = pd.read_sql(query, conn, params=(start_date, end_date))
    conn.close()
    
    if not results_df.empty:
        results_df['test_date'] = pd.to_datetime(results_df['test_date'])
    
    return results_df

def get_assayer_profile(assayer_id):
    """Get detailed profile information for a specific assayer"""
    conn = sqlite3.connect('gold_assay.db')
    query = """
        SELECT * FROM assayers WHERE assayer_id = ? AND is_active = 1
    """
    assayer_df = pd.read_sql(query, conn, params=(assayer_id,))
    conn.close()
    
    if assayer_df.empty:
        return None
    else:
        # Handle possible missing columns
        for col in ['joining_date', 'profile_picture', 'work_experience']:
            if col not in assayer_df.columns:
                assayer_df[col] = None
        
        # Convert joining_date to datetime
        if 'joining_date' in assayer_df.columns:
            assayer_df['joining_date'] = pd.to_datetime(assayer_df['joining_date'], errors='coerce')
        
        # Handle missing work experience
        for index, row in assayer_df.iterrows():
            if pd.isna(row['work_experience']) or row['work_experience'] == '':
                assayer_df.at[index, 'work_experience'] = 'No work experience information available.'
            
        # Convert NaT values to None
        for index, row in assayer_df.iterrows():
            if pd.isna(row['joining_date']):
                assayer_df.at[index, 'joining_date'] = None
                
        result = assayer_df.iloc[0].to_dict()
        
        # Ensure work_experience is never None
        if result.get('work_experience') is None or result.get('work_experience') == '':
            result['work_experience'] = 'No work experience information available.'
            
        return result

def get_assayer_profile_with_stats(assayer_id, days=30):
    """Get detailed profile information with performance statistics for a specific assayer"""
    # Get the basic profile
    profile = get_assayer_profile(assayer_id)
    
    if profile is None:
        return None
        
    # Initialize deviation metrics with default values
    profile['avg_deviation'] = 0.0
    profile['avg_percentage_deviation'] = 0.0
    
    # Calculate years of experience based on joining date
    if profile['joining_date'] is not None and not pd.isna(profile['joining_date']):
        try:
            today = datetime.now()
            years_experience = (today - profile['joining_date']).days / 365.25
            profile['years_experience'] = round(max(0, years_experience), 1)
        except (TypeError, ValueError):
            profile['years_experience'] = 0
    else:
        profile['years_experience'] = 0
    
    # Add performance stats if possible
    conn = sqlite3.connect('gold_assay.db')
    try:
        # Get count of samples tested
        samples_query = f"""
            SELECT COUNT(*) as sample_count
            FROM assay_results
            WHERE assayer_id = {assayer_id}
        """
        
        samples_df = pd.read_sql(samples_query, conn)
        if not samples_df.empty:
            profile['sample_count'] = samples_df.iloc[0]['sample_count']
        else:
            profile['sample_count'] = 0
            
        # Calculate average deviation if benchmark exists
        benchmark_df = pd.read_sql("SELECT assayer_id FROM benchmark_assayers WHERE is_active = 1 LIMIT 1", conn)
        if not benchmark_df.empty:
            benchmark_id = benchmark_df.iloc[0]['assayer_id']
            
            
            # Skip if this is the benchmark assayer (and set flag that this is the benchmark)
            if assayer_id == benchmark_id:
                profile['is_benchmark'] = True
                profile['avg_deviation'] = 0.0  # Benchmark has zero deviation by definition
                profile['avg_absolute_deviation'] = 0.0  # Benchmark has zero absolute deviation by definition
                profile['avg_percentage_deviation'] = 0.0
            else:
                profile['is_benchmark'] = False
                deviation_query = f"""
                    SELECT AVG(r.gold_content - b.gold_content) as avg_deviation,
                           AVG(ABS(r.gold_content - b.gold_content)) as avg_absolute_deviation,
                           AVG(ABS(r.gold_content - b.gold_content) / b.gold_content * 100) as avg_percentage_deviation
                    FROM assay_results r
                    JOIN assay_results b ON r.sample_id = b.sample_id AND b.assayer_id = {benchmark_id}
                    WHERE r.assayer_id = {assayer_id}
                """
                
                deviation_df = pd.read_sql(deviation_query, conn)
                
                if not deviation_df.empty and pd.notna(deviation_df.iloc[0]['avg_deviation']):
                    profile['avg_deviation'] = deviation_df.iloc[0]['avg_deviation']
                    profile['avg_absolute_deviation'] = deviation_df.iloc[0]['avg_absolute_deviation']
                    profile['avg_percentage_deviation'] = deviation_df.iloc[0]['avg_percentage_deviation']
                    
                else:
                    
                    # Set default values instead of leaving them as None (which displays as N/A)
                    profile['avg_deviation'] = 0.0
                    profile['avg_absolute_deviation'] = 0.0
                    profile['avg_percentage_deviation'] = 0.0
    finally:
        conn.close()
    
    return profile
        
def get_all_assayer_profiles():
    """Get all assayer profiles with basic statistics"""
    conn = sqlite3.connect('gold_assay.db')
    assayers_df = pd.read_sql("SELECT * FROM assayers WHERE is_active = 1", conn)
    conn.close()
    
    if assayers_df.empty:
        return pd.DataFrame()
    
    # Handle possible missing columns
    for col in ['joining_date', 'profile_picture', 'work_experience']:
        if col not in assayers_df.columns:
            assayers_df[col] = None
    
    # Convert joining_date to datetime where it's not None
    if 'joining_date' in assayers_df.columns:
        assayers_df['joining_date'] = pd.to_datetime(assayers_df['joining_date'], errors='coerce')
    
    # Calculate years of experience only for valid dates
    today = datetime.now()
    assayers_df['years_experience'] = assayers_df['joining_date'].apply(
        lambda x: round((today - x).days / 365.25, 1) if pd.notna(x) else None
    )
    
    return assayers_df

def get_assayer_performance(days=30, start_date=None, end_date=None):
    """
    Get performance metrics for all assayers compared to benchmark
    
    Args:
        days: Number of days to look back for data (default: 30)
        start_date: Optional start date for filtering (format: 'YYYY-MM-DD')
        end_date: Optional end date for filtering (format: 'YYYY-MM-DD')
        
    Returns:
        DataFrame with performance metrics for all assayers
    """
    conn = sqlite3.connect('gold_assay.db')
    
    # Check if there's a benchmark assayer
    benchmark_df = pd.read_sql("SELECT assayer_id FROM benchmark_assayers WHERE is_active = 1 LIMIT 1", conn)
    if benchmark_df.empty:
        conn.close()
        return None
    
    benchmark_id = benchmark_df.iloc[0]['assayer_id']
    
    # Prepare date filtering condition
    date_condition = ""
    if start_date and end_date:
        date_condition = f"AND date(r.test_date) BETWEEN '{start_date}' AND '{end_date}'"
    elif days:
        date_condition = f"AND date(r.test_date) >= date('now', '-{days} days')"
    
    # Get performance metrics with appropriate date filtering
    query = f"""
        SELECT 
            a.assayer_id,
            a.name as assayer_name,
            COUNT(r.sample_id) as sample_count,
            AVG(r.gold_content - b.gold_content) as avg_deviation,
            AVG(ABS(r.gold_content - b.gold_content)) as avg_absolute_deviation,
            AVG(ABS(r.gold_content - b.gold_content) / b.gold_content * 100) as avg_percentage_deviation,
            MIN(r.test_date) as first_test,
            MAX(r.test_date) as last_test
        FROM assay_results r
        JOIN assayers a ON r.assayer_id = a.assayer_id
        JOIN assay_results b ON r.sample_id = b.sample_id AND b.assayer_id = {benchmark_id}
        WHERE r.assayer_id != {benchmark_id}
        {date_condition}
        GROUP BY a.assayer_id, a.name
        ORDER BY avg_deviation
    """
    performance_df = pd.read_sql(query, conn)
    conn.close()
    
    return performance_df

def get_gold_type_analysis(days=365):
    """
    Analyze consistency across different gold types
    
    Args:
        days: Number of days to look back for data (default: 365)
        
    Returns:
        DataFrame with gold type analysis including mean, std, count, min, max deviation per gold type
    """
    conn = sqlite3.connect('gold_assay.db')
    
    # Check if there's a benchmark assayer
    benchmark_df = pd.read_sql("SELECT assayer_id FROM benchmark_assayers WHERE is_active = 1 LIMIT 1", conn)
    if benchmark_df.empty:
        conn.close()
        return None
    
    benchmark_id = benchmark_df.iloc[0]['assayer_id']
    
    # Check if gold_type column exists
    cursor = conn.cursor()
    if not _check_column_exists(cursor, "assay_results", "gold_type"):
        cursor.execute("ALTER TABLE assay_results ADD COLUMN gold_type TEXT DEFAULT 'Unknown'")
        conn.commit()
        print("Added gold_type column to assay_results table")
    
    # Get gold type metrics - exclude 'Unknown' gold types
    query = f"""
        SELECT 
            r.gold_type,
            COUNT(r.sample_id) as sample_count,
            AVG(ABS(r.gold_content - b.gold_content)) as avg_deviation,
            SUM((r.gold_content - b.gold_content) * (r.gold_content - b.gold_content)) / COUNT(r.sample_id) as variance,
            MIN(ABS(r.gold_content - b.gold_content)) as min_deviation,
            MAX(ABS(r.gold_content - b.gold_content)) as max_deviation
        FROM assay_results r
        JOIN assay_results b ON r.sample_id = b.sample_id AND b.assayer_id = {benchmark_id}
        WHERE r.assayer_id != {benchmark_id}
        AND r.gold_type IS NOT NULL 
        AND r.gold_type != '' 
        AND r.gold_type != 'Unknown'
        GROUP BY r.gold_type
        ORDER BY variance
    """
    
    
    gold_type_df = pd.read_sql(query, conn)
    conn.close()
    
    if not gold_type_df.empty:
        # Calculate standard deviation from variance
        gold_type_df['std_deviation'] = gold_type_df['variance'].apply(lambda x: round(x ** 0.5, 3))
        
        # Add consistency rank (lower standard deviation = higher consistency)
        gold_type_df = gold_type_df.sort_values('std_deviation')
        gold_type_df['consistency_rank'] = range(1, len(gold_type_df) + 1)
        
        # Add variability rank (higher standard deviation = higher variability)
        gold_type_df = gold_type_df.sort_values('std_deviation', ascending=False)
        gold_type_df['variability_rank'] = range(1, len(gold_type_df) + 1)
        
        # Sort by gold_type for display
        gold_type_df = gold_type_df.sort_values('gold_type')
        
        # Clean up - drop the variance column which we used for calculation
        gold_type_df = gold_type_df.drop(columns=['variance'])
        
    return gold_type_df

def get_assayer_gold_type_performance(assayer_id=None, days=365):
    """
    Get performance metrics for assayers by gold type
    
    Args:
        assayer_id: Optional assayer ID to filter results (default: None - all assayers)
        days: Number of days to look back for data (default: 365)
        
    Returns:
        DataFrame with assayer performance by gold type
    """
    conn = sqlite3.connect('gold_assay.db')
    
    # Check if there's a benchmark assayer
    benchmark_df = pd.read_sql("SELECT assayer_id FROM benchmark_assayers WHERE is_active = 1 LIMIT 1", conn)
    if benchmark_df.empty:
        conn.close()
        return None
    
    benchmark_id = benchmark_df.iloc[0]['assayer_id']
    
    # Check if gold_type column exists
    cursor = conn.cursor()
    if not _check_column_exists(cursor, "assay_results", "gold_type"):
        cursor.execute("ALTER TABLE assay_results ADD COLUMN gold_type TEXT DEFAULT 'Unknown'")
        conn.commit()
        print("Added gold_type column to assay_results table")
    
    # Build the assayer filter condition
    assayer_filter = f"AND r.assayer_id = {assayer_id}" if assayer_id is not None else ""
    
    # Get assayer performance by gold type - exclude 'Unknown' gold types
    query = f"""
        SELECT 
            a.assayer_id,
            a.name as assayer_name,
            r.gold_type,
            COUNT(r.sample_id) as sample_count,
            AVG(ABS(r.gold_content - b.gold_content)) as avg_deviation,
            SUM((r.gold_content - b.gold_content) * (r.gold_content - b.gold_content)) / COUNT(r.sample_id) as variance,
            MIN(ABS(r.gold_content - b.gold_content)) as min_deviation,
            MAX(ABS(r.gold_content - b.gold_content)) as max_deviation
        FROM assay_results r
        JOIN assayers a ON r.assayer_id = a.assayer_id
        JOIN assay_results b ON r.sample_id = b.sample_id AND b.assayer_id = {benchmark_id}
        WHERE r.assayer_id != {benchmark_id}
        AND r.gold_type IS NOT NULL 
        AND r.gold_type != '' 
        AND r.gold_type != 'Unknown'
        {assayer_filter}
        GROUP BY a.assayer_id, a.name, r.gold_type
        ORDER BY a.name, r.gold_type
    """
    
    
    performance_df = pd.read_sql(query, conn)
    conn.close()
    
    if not performance_df.empty:
        # Calculate standard deviation from variance
        performance_df['std_deviation'] = performance_df['variance'].apply(lambda x: round(x ** 0.5, 3))
        
        # Remove the variance column which we used for calculation
        performance_df = performance_df.drop(columns=['variance'])
    
    return performance_df
    
def get_weighted_mass_impact(days=365, min_gold_content=0, start_date=None, end_date=None):
    """
    Calculate the net mass gain/loss from assay deviations weighted by actual bar mass.
    
    This function calculates the physical impact of deviations by considering:
    1. The actual deviation in purity (ppt)
    2. The actual physical mass of each bar (in grams)
    
    Args:
        days: Number of days to look back for data (default: 365)
        min_gold_content: Minimum gold content to consider (in ppt, default: 0)
        start_date: Optional start date for filtering (format: 'YYYY-MM-DD')
        end_date: Optional end date for filtering (format: 'YYYY-MM-DD')
        
    Returns:
        DataFrame with detailed analysis of mass impact per assayer, including:
        - Net mass gain/loss
        - Positive and negative deviations
        - Mass-impact calculations
    """
    conn = sqlite3.connect('gold_assay.db')
    
    # Check if there's a benchmark assayer
    benchmark_df = pd.read_sql("SELECT assayer_id FROM benchmark_assayers WHERE is_active = 1 LIMIT 1", conn)
    if benchmark_df.empty:
        
        conn.close()
        return None
    
    benchmark_id = benchmark_df.iloc[0]['assayer_id']
    
    
    # Determine date filtering approach
    if start_date and end_date:
        # Use specific date range
        date_filter = f"AND date(r.test_date) BETWEEN '{start_date}' AND '{end_date}'"
        
    elif days is not None:
        # Use relative days from now
        date_filter = f"AND date(r.test_date) >= date('now', '-{days} days')"
        
    else:
        # No date filter - default to last 365 days if no filtering option is provided
        date_filter = f"AND date(r.test_date) >= date('now', '-365 days')"
        
    
    # Get individual sample data with detailed information including bar weight
    # Only include samples that have recorded bar weights (exclude samples with missing or zero bar weights)
    query = f"""
        SELECT 
            r.result_id,
            r.assayer_id,
            a.name as assayer_name,
            r.sample_id,
            r.gold_content,
            b.gold_content as benchmark_gold_content,
            (r.gold_content - b.gold_content) as deviation_ppt,
            r.bar_weight_grams,
            r.test_date,
            r.gold_type
        FROM assay_results r
        JOIN assayers a ON r.assayer_id = a.assayer_id
        JOIN assay_results b ON r.sample_id = b.sample_id AND b.assayer_id = {benchmark_id}
        WHERE 
            r.assayer_id != {benchmark_id}
            {date_filter}
            AND r.gold_content >= {min_gold_content}
            AND r.bar_weight_grams IS NOT NULL 
            AND r.bar_weight_grams > 0
        ORDER BY r.assayer_id, r.test_date DESC
    """
    
    
    samples_df = pd.read_sql(query, conn)
    conn.close()
    
    if samples_df.empty:
        
        return pd.DataFrame()
    
    # Convert test_date to datetime
    samples_df['test_date'] = pd.to_datetime(samples_df['test_date'])
    
    # Handle missing bar weights (set to 1000g by default if not specified)
    samples_df['bar_weight_grams'] = samples_df['bar_weight_grams'].fillna(1000).replace(0, 1000)
    
    # Calculate the actual gold mass in each bar (in grams)
    samples_df['actual_gold_mass_g'] = samples_df['bar_weight_grams'] * (samples_df['gold_content'] / 1000)
    samples_df['benchmark_gold_mass_g'] = samples_df['bar_weight_grams'] * (samples_df['benchmark_gold_content'] / 1000)
    
    # Calculate the mass deviation (+ for gain, - for loss)
    samples_df['mass_deviation_g'] = samples_df['actual_gold_mass_g'] - samples_df['benchmark_gold_mass_g']
    
    # Create separate columns for positive and negative deviations
    samples_df['positive_deviation_g'] = samples_df['mass_deviation_g'].apply(lambda x: max(0, x))
    samples_df['negative_deviation_g'] = samples_df['mass_deviation_g'].apply(lambda x: min(0, x)).abs()
    
    # Calculate additional metrics for each sample
    samples_df['deviation_per_kg'] = (samples_df['mass_deviation_g'] / (samples_df['bar_weight_grams'] / 1000))
    samples_df['abs_mass_deviation_g'] = samples_df['mass_deviation_g'].abs()
    samples_df['mass_deviation_percentage'] = (samples_df['mass_deviation_g'] / 
                                         (samples_df['bar_weight_grams'] * (samples_df['benchmark_gold_content'] / 1000))) * 100
    
    # Group by assayer to get summary statistics
    summary_df = samples_df.groupby(['assayer_id', 'assayer_name']).agg(
        sample_count=('sample_id', 'count'),
        avg_deviation_ppt=('deviation_ppt', 'mean'),
        std_deviation_ppt=('deviation_ppt', 'std'),
        median_deviation_ppt=('deviation_ppt', 'median'),
        total_bar_mass_kg=('bar_weight_grams', lambda x: sum(x) / 1000),  # Convert to kg
        avg_bar_mass_g=('bar_weight_grams', 'mean'),  # Average bar size
        max_bar_mass_g=('bar_weight_grams', 'max'),  # Largest bar measured
        avg_gold_content=('gold_content', 'mean'),
        total_mass_deviation_g=('mass_deviation_g', 'sum'),
        total_positive_deviation_g=('positive_deviation_g', 'sum'),
        total_negative_deviation_g=('negative_deviation_g', 'sum'),
        avg_mass_deviation_g=('mass_deviation_g', 'mean'),
        median_mass_deviation_g=('mass_deviation_g', 'median'),
        max_mass_deviation_g=('mass_deviation_g', 'max'),
        min_mass_deviation_g=('mass_deviation_g', 'min'),
        avg_deviation_per_kg=('deviation_per_kg', 'mean'),  # Deviation normalized by kg
        total_abs_mass_deviation_g=('abs_mass_deviation_g', 'sum'),  # Total absolute deviation (magnitude)
        avg_mass_deviation_percentage=('mass_deviation_percentage', 'mean')  # Average deviation as % of gold content
    ).reset_index()
    
    if not summary_df.empty:
        # Add deviation direction column
        summary_df['deviation_direction'] = summary_df['total_mass_deviation_g'].apply(
            lambda x: "Over" if x > 0 else "Under" if x < 0 else "Neutral"
        )
        
        # Calculate deviation as percentage of total gold mass
        summary_df['deviation_percentage'] = (summary_df['total_mass_deviation_g'] / 
                                             (summary_df['total_bar_mass_kg'] * 1000 * 
                                              (summary_df['avg_gold_content'] / 1000)) * 100)
        
        # Round values for display
        # List of columns that should be rounded to 2 decimal places
        columns_to_round = [
            'avg_deviation_ppt', 'std_deviation_ppt', 'median_deviation_ppt',
            'total_bar_mass_kg', 'avg_bar_mass_g', 'avg_gold_content',
            'total_mass_deviation_g', 'total_positive_deviation_g', 'total_negative_deviation_g',
            'avg_mass_deviation_g', 'median_mass_deviation_g', 'max_mass_deviation_g', 'min_mass_deviation_g',
            'avg_deviation_per_kg', 'total_abs_mass_deviation_g', 'avg_mass_deviation_percentage',
            'deviation_percentage'
        ]
        
        # Apply rounding to all numeric columns in the list
        for col in columns_to_round:
            if col in summary_df.columns:
                summary_df[col] = summary_df[col].round(2)
    
    # Store the detailed sample data as well for drilldown analysis if needed
    summary_df.attrs['detailed_samples'] = samples_df
    
    return summary_df
