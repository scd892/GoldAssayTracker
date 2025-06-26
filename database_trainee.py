import sqlite3
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

def init_trainee_db():
    """Initialize the trainee evaluation database tables"""
    conn = sqlite3.connect('gold_assay.db')
    cursor = conn.cursor()
    
    # Create a table for trainees if it doesn't exist
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS trainees (
        trainee_id INTEGER PRIMARY KEY AUTOINCREMENT,
        assayer_id INTEGER NOT NULL,
        start_date TEXT NOT NULL,
        certification_date TEXT,
        status TEXT DEFAULT 'Pending',
        target_tolerance REAL DEFAULT 0.3,
        min_samples_required INTEGER DEFAULT 20,
        min_accuracy_percentage REAL DEFAULT 85.0,
        notes TEXT,
        is_active INTEGER DEFAULT 1,
        FOREIGN KEY (assayer_id) REFERENCES assayers (assayer_id)
    )
    ''')
    
    # Create a table for certified reference materials
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS reference_materials (
        reference_id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        gold_content REAL NOT NULL,
        uncertainty REAL DEFAULT 0.1,
        material_type TEXT,
        source TEXT,
        notes TEXT,
        is_active INTEGER DEFAULT 1
    )
    ''')
    
    # Create a table for trainee evaluations against reference materials
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS trainee_evaluations (
        evaluation_id INTEGER PRIMARY KEY AUTOINCREMENT,
        trainee_id INTEGER NOT NULL,
        reference_id INTEGER NOT NULL,
        test_date TEXT NOT NULL,
        measured_gold_content REAL NOT NULL,
        deviation_ppt REAL,
        is_within_tolerance INTEGER DEFAULT 0,
        sample_id TEXT,
        notes TEXT,
        evaluation_type TEXT DEFAULT 'accuracy',
        FOREIGN KEY (trainee_id) REFERENCES trainees (trainee_id),
        FOREIGN KEY (reference_id) REFERENCES reference_materials (reference_id)
    )
    ''')
    
    # Create table for certification thresholds
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS certification_thresholds (
        threshold_id INTEGER PRIMARY KEY AUTOINCREMENT,
        min_samples INTEGER DEFAULT 20,
        min_accuracy_percentage REAL DEFAULT 85.0,
        max_std_deviation REAL DEFAULT 0.5,
        max_avg_deviation REAL DEFAULT 0.2,
        is_active INTEGER DEFAULT 1
    )
    ''')
    
    # Check if we need to insert default certification thresholds
    cursor.execute("SELECT COUNT(*) FROM certification_thresholds")
    if cursor.fetchone()[0] == 0:
        cursor.execute('''
        INSERT INTO certification_thresholds (min_samples, min_accuracy_percentage, max_std_deviation, max_avg_deviation, is_active)
        VALUES (20, 85.0, 0.5, 0.2, 1)
        ''')
    
    conn.commit()
    conn.close()
    print("Trainee evaluation database tables created successfully")

def add_trainee(assayer_id, start_date=None, target_tolerance=0.3, min_samples_required=20, min_accuracy_percentage=85.0, notes=""):
    """
    Register an assayer as a trainee for certification tracking
    
    Args:
        assayer_id: ID of the existing assayer
        start_date: Start date of training period (defaults to today)
        target_tolerance: Target tolerance in ppt for passing evaluations (default 0.3 ppt)
        min_samples_required: Minimum samples required for certification eligibility (default 20)
        min_accuracy_percentage: Minimum percentage of samples within tolerance required (default 85%)
        notes: Additional notes about the trainee
        
    Returns:
        trainee_id: ID of the newly created trainee record
    """
    if start_date is None:
        start_date = datetime.now().strftime('%Y-%m-%d')
    
    conn = sqlite3.connect('gold_assay.db')
    cursor = conn.cursor()
    
    # Check if assayer exists
    cursor.execute("SELECT assayer_id FROM assayers WHERE assayer_id = ?", (assayer_id,))
    if not cursor.fetchone():
        conn.close()
        raise ValueError(f"Assayer with ID {assayer_id} does not exist")
    
    # Check if assayer is already registered as a trainee
    cursor.execute("SELECT trainee_id FROM trainees WHERE assayer_id = ? AND is_active = 1", (assayer_id,))
    existing = cursor.fetchone()
    if existing:
        conn.close()
        return existing[0]  # Return existing trainee ID
    
    # Insert new trainee
    cursor.execute('''
    INSERT INTO trainees 
    (assayer_id, start_date, status, target_tolerance, min_samples_required, min_accuracy_percentage, notes, is_active)
    VALUES (?, ?, ?, ?, ?, ?, ?, 1)
    ''', (assayer_id, start_date, 'Pending', target_tolerance, min_samples_required, min_accuracy_percentage, notes))
    
    trainee_id = cursor.lastrowid
    conn.commit()
    conn.close()
    
    return trainee_id

def get_trainees():
    """
    Get list of all active trainees with their associated assayer information
    
    Returns:
        DataFrame with trainee information
    """
    conn = sqlite3.connect('gold_assay.db')
    
    query = """
    SELECT 
        t.trainee_id, 
        t.assayer_id, 
        a.name as assayer_name,
        a.employee_id,
        t.start_date, 
        t.certification_date, 
        t.status, 
        t.target_tolerance,
        t.min_samples_required,
        t.min_accuracy_percentage,
        t.notes
    FROM trainees t
    JOIN assayers a ON t.assayer_id = a.assayer_id
    WHERE t.is_active = 1
    ORDER BY t.status, t.start_date DESC
    """
    
    trainees_df = pd.read_sql(query, conn)
    conn.close()
    return trainees_df

def add_reference_material(name, gold_content, uncertainty=0.1, material_type="Standard", source="", notes=""):
    """
    Add a certified reference material to the database
    
    Args:
        name: Name or identifier of the reference material
        gold_content: Certified gold content in ppt
        uncertainty: Uncertainty of the certified value (default 0.1 ppt)
        material_type: Type of material (Standard, CRM, In-house, etc.)
        source: Source or provider of the reference material
        notes: Additional information
        
    Returns:
        reference_id: ID of the newly created reference material
    """
    conn = sqlite3.connect('gold_assay.db')
    cursor = conn.cursor()
    
    cursor.execute('''
    INSERT INTO reference_materials 
    (name, gold_content, uncertainty, material_type, source, notes, is_active)
    VALUES (?, ?, ?, ?, ?, ?, 1)
    ''', (name, gold_content, uncertainty, material_type, source, notes))
    
    reference_id = cursor.lastrowid
    conn.commit()
    conn.close()
    
    return reference_id

def get_reference_materials():
    """
    Get list of all active reference materials
    
    Returns:
        DataFrame with reference material information
    """
    conn = sqlite3.connect('gold_assay.db')
    
    query = """
    SELECT 
        reference_id, 
        name, 
        gold_content, 
        uncertainty, 
        material_type, 
        source, 
        notes
    FROM reference_materials
    WHERE is_active = 1
    ORDER BY name
    """
    
    materials_df = pd.read_sql(query, conn)
    conn.close()
    return materials_df

def add_trainee_evaluation(trainee_id, reference_id, measured_gold_content, test_date=None, sample_id="", notes="", evaluation_type="accuracy"):
    """
    Add a trainee evaluation against a reference material
    
    Args:
        trainee_id: ID of the trainee 
        reference_id: ID of the reference material being tested
        measured_gold_content: The gold content measured by the trainee in ppt
        test_date: Date of the test (defaults to today)
        sample_id: Optional sample identifier
        notes: Additional notes
        evaluation_type: Type of evaluation ('accuracy' or 'consistency')
        
    Returns:
        evaluation_id: ID of the newly created evaluation record
    """
    if test_date is None:
        test_date = datetime.now().strftime('%Y-%m-%d')
    
    conn = sqlite3.connect('gold_assay.db')
    cursor = conn.cursor()
    
    # Get reference material certified value
    cursor.execute("SELECT gold_content, uncertainty FROM reference_materials WHERE reference_id = ?", (reference_id,))
    ref_result = cursor.fetchone()
    if not ref_result:
        conn.close()
        raise ValueError(f"Reference material with ID {reference_id} does not exist")
    
    certified_value, uncertainty = ref_result
    
    # Get trainee's target tolerance
    cursor.execute("SELECT target_tolerance FROM trainees WHERE trainee_id = ?", (trainee_id,))
    trainee_result = cursor.fetchone()
    if not trainee_result:
        conn.close()
        raise ValueError(f"Trainee with ID {trainee_id} does not exist")
    
    target_tolerance = trainee_result[0]
    
    # Calculate deviation and whether it's within tolerance
    deviation_ppt = measured_gold_content - certified_value
    is_within_tolerance = 1 if abs(deviation_ppt) <= target_tolerance else 0
    
    # Insert evaluation
    cursor.execute('''
    INSERT INTO trainee_evaluations 
    (trainee_id, reference_id, test_date, measured_gold_content, deviation_ppt, is_within_tolerance, sample_id, notes, evaluation_type)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (trainee_id, reference_id, test_date, measured_gold_content, deviation_ppt, is_within_tolerance, sample_id, notes, evaluation_type))
    
    evaluation_id = cursor.lastrowid
    conn.commit()
    
    # Update trainee certification status
    update_trainee_certification_status(trainee_id, conn)
    
    conn.close()
    return evaluation_id

def update_trainee_certification_status(trainee_id, conn=None):
    """
    Update a trainee's certification status based on their evaluation history
    
    Args:
        trainee_id: ID of the trainee
        conn: Optional existing database connection
    
    Returns:
        status: The updated certification status
    """
    close_conn = False
    if conn is None:
        conn = sqlite3.connect('gold_assay.db')
        close_conn = True
    
    cursor = conn.cursor()
    
    # Get certification thresholds
    cursor.execute("SELECT min_samples, min_accuracy_percentage, max_std_deviation, max_avg_deviation FROM certification_thresholds WHERE is_active = 1 LIMIT 1")
    threshold_result = cursor.fetchone()
    if not threshold_result:
        if close_conn:
            conn.close()
        return "Pending"
    
    min_samples, min_accuracy_percentage, max_std_deviation, max_avg_deviation = threshold_result
    
    # Get trainee requirements (which may override global settings)
    cursor.execute("SELECT min_samples_required, min_accuracy_percentage FROM trainees WHERE trainee_id = ?", (trainee_id,))
    trainee_result = cursor.fetchone()
    if not trainee_result:
        if close_conn:
            conn.close()
        return "Pending"
    
    trainee_min_samples, trainee_min_accuracy = trainee_result
    
    # Use trainee-specific thresholds if available
    min_samples = trainee_min_samples or min_samples
    min_accuracy_percentage = trainee_min_accuracy or min_accuracy_percentage
    
    # Get all evaluations to process by type
    cursor.execute("""
    SELECT 
        evaluation_id,
        deviation_ppt,
        is_within_tolerance,
        evaluation_type
    FROM trainee_evaluations
    WHERE trainee_id = ?
    """, (trainee_id,))
    
    evaluations = cursor.fetchall()
    if not evaluations:  # No evaluations yet
        if close_conn:
            conn.close()
        return "Pending"
    
    # Separate evaluations by type
    accuracy_evals = []
    consistency_evals = []
    
    for eval in evaluations:
        eval_id, deviation, is_within_tolerance, eval_type = eval
        if eval_type == 'accuracy':
            accuracy_evals.append((deviation, is_within_tolerance))
        elif eval_type == 'consistency':
            consistency_evals.append((deviation, is_within_tolerance))
    
    # Calculate statistics for both types
    accuracy_stats = {
        'count': len(accuracy_evals),
        'within_tolerance': sum(e[1] for e in accuracy_evals) if accuracy_evals else 0,
        'deviations': [e[0] for e in accuracy_evals]
    }
    
    consistency_stats = {
        'count': len(consistency_evals),
        'within_tolerance': sum(e[1] for e in consistency_evals) if consistency_evals else 0,
        'deviations': [e[0] for e in consistency_evals]
    }
    
    # Calculate derived statistics for accuracy evaluations
    if accuracy_stats['count'] > 0:
        accuracy_stats['accuracy_percentage'] = (accuracy_stats['within_tolerance'] / accuracy_stats['count']) * 100
        accuracy_stats['avg_deviation'] = sum(accuracy_stats['deviations']) / accuracy_stats['count']
        
        import numpy as np
        if len(accuracy_stats['deviations']) > 1:
            accuracy_stats['std_deviation'] = np.std(accuracy_stats['deviations'], ddof=1)
        else:
            accuracy_stats['std_deviation'] = 0.0
    
    # Calculate derived statistics for consistency evaluations
    if consistency_stats['count'] > 0:
        consistency_stats['accuracy_percentage'] = (consistency_stats['within_tolerance'] / consistency_stats['count']) * 100
        consistency_stats['avg_deviation'] = sum(consistency_stats['deviations']) / consistency_stats['count']
        
        import numpy as np
        if len(consistency_stats['deviations']) > 1:
            consistency_stats['std_deviation'] = np.std(consistency_stats['deviations'], ddof=1)
        else:
            consistency_stats['std_deviation'] = 0.0
    
    # Determine certification status - need to meet criteria for both types if both have samples
    new_status = "Pending"
    
    # Must have sufficient samples of accuracy evaluations
    if accuracy_stats['count'] >= min_samples:
        accuracy_passed = (
            accuracy_stats.get('accuracy_percentage', 0) >= min_accuracy_percentage and
            abs(accuracy_stats.get('avg_deviation', 999)) <= max_avg_deviation and
            accuracy_stats.get('std_deviation', 999) <= max_std_deviation
        )
        
        # Check if consistency evaluations exist and they meet criteria
        if consistency_stats['count'] > 0:
            consistency_passed = (
                consistency_stats.get('accuracy_percentage', 0) >= min_accuracy_percentage and
                abs(consistency_stats.get('avg_deviation', 999)) <= max_avg_deviation and
                consistency_stats.get('std_deviation', 999) <= max_std_deviation
            )
            
            # Both must pass to be certified
            if accuracy_passed and consistency_passed:
                new_status = "Certified"
            else:
                new_status = "Needs More Training"
        else:
            # No consistency evaluations - only require accuracy to pass
            if accuracy_passed:
                new_status = "Certified"
            else:
                new_status = "Needs More Training"
    else:
        if accuracy_stats['count'] > 0:
            # Has some evaluations but not enough
            new_status = "Pending"
        else:
            # No accuracy evaluations at all
            new_status = "Pending"
    
    # Update trainee status
    cursor.execute("UPDATE trainees SET status = ? WHERE trainee_id = ?", (new_status, trainee_id))
    
    # If newly certified, set certification date
    if new_status == "Certified":
        cursor.execute("""
        UPDATE trainees 
        SET certification_date = ? 
        WHERE trainee_id = ? AND (certification_date IS NULL OR certification_date = '')
        """, (datetime.now().strftime('%Y-%m-%d'), trainee_id))
    
    conn.commit()
    
    if close_conn:
        conn.close()
    
    return new_status

def get_trainee_evaluations(trainee_id=None, days=90):
    """
    Get evaluation records for trainees
    
    Args:
        trainee_id: Optional trainee ID to filter results
        days: Number of days to look back
        
    Returns:
        DataFrame with evaluation records
    """
    conn = sqlite3.connect('gold_assay.db')
    
    where_clause = "WHERE e.test_date >= date('now', '-{} days')".format(days)
    if trainee_id is not None:
        where_clause += f" AND e.trainee_id = {trainee_id}"
    
    query = f"""
    SELECT 
        e.evaluation_id,
        e.trainee_id,
        t.assayer_id,
        a.name as assayer_name,
        a.employee_id,
        e.reference_id,
        r.name as reference_name,
        r.gold_content as certified_gold_content,
        r.uncertainty,
        e.measured_gold_content,
        e.deviation_ppt,
        e.is_within_tolerance,
        t.target_tolerance,
        e.test_date,
        e.sample_id,
        e.notes,
        t.status as certification_status,
        e.evaluation_type
    FROM trainee_evaluations e
    JOIN trainees t ON e.trainee_id = t.trainee_id
    JOIN assayers a ON t.assayer_id = a.assayer_id
    JOIN reference_materials r ON e.reference_id = r.reference_id
    {where_clause}
    ORDER BY e.test_date DESC
    """
    
    evaluations_df = pd.read_sql(query, conn)
    conn.close()
    return evaluations_df

def get_trainee_summary(trainee_id=None):
    """
    Get summary performance statistics for trainees
    
    Args:
        trainee_id: Optional trainee ID to filter results
        
    Returns:
        DataFrame with trainee performance summaries
    """
    conn = sqlite3.connect('gold_assay.db')
    
    # First get the trainees
    where_clause = "WHERE t.is_active = 1"
    if trainee_id is not None:
        where_clause += f" AND t.trainee_id = {trainee_id}"
    
    # Get the basic trainee info
    query = f"""
    SELECT 
        t.trainee_id,
        t.assayer_id,
        a.name as assayer_name,
        a.employee_id,
        t.start_date,
        t.certification_date,
        t.status as certification_status,
        t.target_tolerance,
        t.min_samples_required,
        t.min_accuracy_percentage,
        t.notes
    FROM trainees t
    JOIN assayers a ON t.assayer_id = a.assayer_id
    {where_clause}
    ORDER BY t.status, a.name
    """
    
    trainees_df = pd.read_sql(query, conn)
    
    # If no trainees, return empty dataframe
    if trainees_df.empty:
        conn.close()
        return trainees_df
    
    # Get all evaluations for these trainees
    trainee_ids = tuple(trainees_df['trainee_id'].tolist())
    # Handle the case when there's only one trainee (SQLite requires special syntax)
    if len(trainee_ids) == 1:
        trainee_filter = f"e.trainee_id = {trainee_ids[0]}"
    else:
        trainee_filter = f"e.trainee_id IN {trainee_ids}"
    
    eval_query = f"""
    SELECT 
        e.trainee_id,
        e.evaluation_id,
        e.deviation_ppt,
        e.is_within_tolerance,
        e.test_date,
        e.evaluation_type
    FROM trainee_evaluations e
    WHERE {trainee_filter}
    """
    
    evals_df = pd.read_sql(eval_query, conn)
    conn.close()
    
    # Calculate stats using pandas
    result_df = trainees_df.copy()
    
    # Initialize default columns - overall stats
    result_df['total_samples_evaluated'] = 0
    result_df['average_deviation'] = 0.0
    result_df['standard_deviation'] = 0.0
    result_df['percent_within_tolerance'] = 0.0
    result_df['first_evaluation'] = None
    result_df['last_evaluation'] = None
    
    # Initialize separate stats for accuracy and consistency
    result_df['accuracy_samples'] = 0
    result_df['accuracy_avg_deviation'] = 0.0
    result_df['accuracy_std_deviation'] = 0.0 
    result_df['accuracy_within_tolerance'] = 0.0
    
    result_df['consistency_samples'] = 0
    result_df['consistency_avg_deviation'] = 0.0
    result_df['consistency_std_deviation'] = 0.0
    result_df['consistency_within_tolerance'] = 0.0
    
    # If there are evaluations, calculate stats per trainee
    if not evals_df.empty:
        # Overall statistics across all evaluation types
        stats = evals_df.groupby('trainee_id').agg(
            total_samples=('evaluation_id', 'count'),
            avg_deviation=('deviation_ppt', 'mean'),
            std_deviation=('deviation_ppt', 'std'),
            within_tolerance=('is_within_tolerance', 'sum'),
            first_eval=('test_date', 'min'),
            last_eval=('test_date', 'max')
        ).reset_index()
        
        # Calculate percentage within tolerance
        stats['percent_within_tolerance'] = (stats['within_tolerance'] / stats['total_samples']) * 100
        
        # Fill NaN values in std_deviation (happens when only 1 sample)
        stats['std_deviation'] = stats['std_deviation'].fillna(0.0)
        
        # Merge overall stats into result
        stats_cols = {
            'total_samples': 'total_samples_evaluated',
            'avg_deviation': 'average_deviation',
            'std_deviation': 'standard_deviation',
            'percent_within_tolerance': 'percent_within_tolerance',
            'first_eval': 'first_evaluation',
            'last_eval': 'last_evaluation'
        }
        stats = stats.rename(columns=stats_cols)
        
        # Get only the needed columns for the merge
        merge_cols = ['trainee_id'] + list(stats_cols.values())
        stats = stats[merge_cols]
        
        # Merge with result
        result_df = pd.merge(
            result_df, 
            stats, 
            on='trainee_id', 
            how='left'
        )
        
        # Instead of referring to stats_cols, check if the columns exist in result_df
        for col in result_df.columns:
            if col in ['first_evaluation', 'last_evaluation']:
                continue
            # Check if the column is numeric and has NaN values
            if col in result_df.select_dtypes(include=['number']).columns and result_df[col].isna().any():
                result_df[col] = result_df[col].fillna(0.0)
        
        # Calculate separate stats for accuracy evaluations
        if 'accuracy' in evals_df['evaluation_type'].values:
            accuracy_evals = evals_df[evals_df['evaluation_type'] == 'accuracy']
            
            acc_stats = accuracy_evals.groupby('trainee_id').agg(
                accuracy_samples=('evaluation_id', 'count'),
                accuracy_avg_deviation=('deviation_ppt', 'mean'),
                accuracy_std_deviation=('deviation_ppt', 'std'),
                accuracy_within_tol=('is_within_tolerance', 'sum')
            ).reset_index()
            
            # Calculate percentage within tolerance for accuracy
            acc_stats['accuracy_within_tolerance'] = (acc_stats['accuracy_within_tol'] / acc_stats['accuracy_samples']) * 100
            acc_stats = acc_stats.drop(columns=['accuracy_within_tol'])
            
            # Fill NaN values
            acc_stats['accuracy_std_deviation'] = acc_stats['accuracy_std_deviation'].fillna(0.0)
            
            # Merge with result
            result_df = pd.merge(
                result_df,
                acc_stats,
                on='trainee_id',
                how='left'
            )
            
            # Fill NaN values for accuracy columns
            for col in ['accuracy_samples', 'accuracy_avg_deviation', 'accuracy_std_deviation', 'accuracy_within_tolerance']:
                if col in result_df.columns:
                    result_df[col] = result_df[col].fillna(0.0)
        
        # Calculate separate stats for consistency evaluations
        if 'consistency' in evals_df['evaluation_type'].values:
            consistency_evals = evals_df[evals_df['evaluation_type'] == 'consistency']
            
            cons_stats = consistency_evals.groupby('trainee_id').agg(
                consistency_samples=('evaluation_id', 'count'),
                consistency_avg_deviation=('deviation_ppt', 'mean'),
                consistency_std_deviation=('deviation_ppt', 'std'),
                consistency_within_tol=('is_within_tolerance', 'sum')
            ).reset_index()
            
            # Calculate percentage within tolerance for consistency
            cons_stats['consistency_within_tolerance'] = (cons_stats['consistency_within_tol'] / cons_stats['consistency_samples']) * 100
            cons_stats = cons_stats.drop(columns=['consistency_within_tol'])
            
            # Fill NaN values
            cons_stats['consistency_std_deviation'] = cons_stats['consistency_std_deviation'].fillna(0.0)
            
            # Merge with result
            result_df = pd.merge(
                result_df,
                cons_stats,
                on='trainee_id',
                how='left'
            )
            
            # Fill NaN values for consistency columns
            for col in ['consistency_samples', 'consistency_avg_deviation', 'consistency_std_deviation', 'consistency_within_tolerance']:
                if col in result_df.columns:
                    result_df[col] = result_df[col].fillna(0.0)
    
    return result_df

def get_certification_thresholds():
    """Get the current certification thresholds"""
    conn = sqlite3.connect('gold_assay.db')
    query = "SELECT * FROM certification_thresholds WHERE is_active = 1 LIMIT 1"
    thresholds_df = pd.read_sql(query, conn)
    conn.close()
    return thresholds_df

def update_certification_thresholds(min_samples, min_accuracy_percentage, max_std_deviation, max_avg_deviation):
    """Update certification thresholds"""
    conn = sqlite3.connect('gold_assay.db')
    cursor = conn.cursor()
    
    # Deactivate current thresholds
    cursor.execute("UPDATE certification_thresholds SET is_active = 0")
    
    # Insert new thresholds
    cursor.execute("""
    INSERT INTO certification_thresholds 
    (min_samples, min_accuracy_percentage, max_std_deviation, max_avg_deviation, is_active)
    VALUES (?, ?, ?, ?, 1)
    """, (min_samples, min_accuracy_percentage, max_std_deviation, max_avg_deviation))
    
    conn.commit()
    conn.close()
    
    # Recalculate status for all trainees
    update_all_trainee_statuses()
    
    return True

def update_all_trainee_statuses():
    """Update certification status for all trainees"""
    conn = sqlite3.connect('gold_assay.db')
    cursor = conn.cursor()
    
    cursor.execute("SELECT trainee_id FROM trainees WHERE is_active = 1")
    trainees = cursor.fetchall()
    
    for trainee in trainees:
        update_trainee_certification_status(trainee[0], conn)
    
    conn.close()
    return True

def get_trainee_performance_history(trainee_id, days=90, evaluation_type=None):
    """
    Get historical performance for a specific trainee
    
    Args:
        trainee_id: ID of the trainee
        days: Number of days of history to retrieve
        evaluation_type: Optional filter for evaluation type ('accuracy' or 'consistency')
        
    Returns:
        DataFrame with daily performance metrics
    """
    conn = sqlite3.connect('gold_assay.db')
    
    # Build the where clause with evaluation type filter if provided
    where_clause = f"""
        e.trainee_id = {trainee_id}
        AND e.test_date >= date('now', '-{days} days')
    """
    
    if evaluation_type:
        where_clause += f" AND e.evaluation_type = '{evaluation_type}'"
    
    # Get raw evaluation data
    query = f"""
    SELECT 
        e.evaluation_id,
        e.deviation_ppt,
        e.is_within_tolerance,
        e.test_date,
        e.evaluation_type
    FROM trainee_evaluations e
    WHERE {where_clause}
    ORDER BY e.test_date
    """
    
    raw_data = pd.read_sql(query, conn)
    conn.close()
    
    # If no data, return empty dataframe
    if raw_data.empty:
        return pd.DataFrame(columns=[
            'test_date', 'daily_samples', 'avg_deviation', 
            'std_deviation', 'daily_accuracy_percentage', 'evaluation_type'
        ])
    
    # Convert to datetime for grouping
    raw_data['test_date'] = pd.to_datetime(raw_data['test_date'])
    
    # Group by date and evaluation_type, and calculate metrics
    if evaluation_type:
        # If filtered by type, just group by date
        group_cols = [raw_data['test_date'].dt.date]
    else:
        # Otherwise group by date and type
        group_cols = [raw_data['test_date'].dt.date, 'evaluation_type']
    
    history_df = raw_data.groupby(group_cols).agg(
        daily_samples=('evaluation_id', 'count'),
        avg_deviation=('deviation_ppt', 'mean'),
        std_deviation=('deviation_ppt', 'std'),
        within_tolerance=('is_within_tolerance', 'sum')
    ).reset_index()
    
    # Calculate accuracy percentage
    history_df['daily_accuracy_percentage'] = (history_df['within_tolerance'] / history_df['daily_samples']) * 100
    
    # Fill NaN values in std_deviation
    history_df['std_deviation'] = history_df['std_deviation'].fillna(0.0)
    
    # Convert test_date back to datetime for plotting
    if evaluation_type:
        # If filtered by type, add the evaluation type column for consistency
        history_df['evaluation_type'] = evaluation_type
    
    if 'test_date' in history_df.columns:
        history_df['test_date'] = pd.to_datetime(history_df['test_date'])
    
    # Sort by date (and type if present)
    sort_cols = ['test_date']
    if 'evaluation_type' in history_df.columns:
        sort_cols.append('evaluation_type')
    
    history_df = history_df.sort_values(sort_cols)
    
    return history_df