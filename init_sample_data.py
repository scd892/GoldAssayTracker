import sqlite3
from datetime import datetime, timedelta
import random

# Initialize database with sample data for demonstration
def init_sample_data():
    print("Checking if sample data initialization is needed...")
    
    # Connect to the database
    conn = sqlite3.connect('gold_assay.db')
    cursor = conn.cursor()
    
    # Check if the database already has assayers
    cursor.execute("SELECT COUNT(*) FROM assayers WHERE is_active = 1")
    assayer_count = cursor.fetchone()[0]
    
    if assayer_count > 0:
        print(f"Database already contains {assayer_count} active assayers. Skipping sample data initialization.")
        conn.close()
        return
    
    print("Initializing database with sample data...")
    
    # Clear existing data (just to be safe)
    cursor.execute("DELETE FROM assay_results")
    cursor.execute("DELETE FROM benchmark_assayers")
    cursor.execute("DELETE FROM assayers")
    conn.commit()
    
    # Add sample assayers
    assayers = [
        ("John Smith", "JS001"),
        ("Maria Garcia", "MG002"),
        ("Robert Johnson", "RJ003"),
        ("Li Wei", "LW004"),
        ("Sarah Brown", "SB005"),
    ]
    
    assayer_ids = {}
    
    for name, employee_id in assayers:
        cursor.execute(
            "INSERT INTO assayers (name, employee_id, is_active) VALUES (?, ?, 1)",
            (name, employee_id)
        )
        assayer_ids[name] = cursor.lastrowid
    
    # Set benchmark assayer (John Smith)
    cursor.execute(
        "INSERT INTO benchmark_assayers (assayer_id, set_date, is_active) VALUES (?, ?, 1)",
        (assayer_ids["John Smith"], datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
    )
    
    # Generate sample IDs
    sample_ids = [f"G{i:04d}" for i in range(1, 31)]
    
    # Create sample gold content values for each assayer and sample
    # The benchmark assayer's values will be the reference
    today = datetime.now()
    
    # For the benchmark assayer (John Smith)
    benchmark_id = assayer_ids["John Smith"]
    benchmark_values = {}
    
    for sample_id in sample_ids:
        # Generate a random gold content between 800 and 999.9
        gold_content = round(random.uniform(800, 999.9), 1)
        benchmark_values[sample_id] = gold_content
        
        # Use a date within the last 30 days
        days_ago = random.randint(0, 29)
        test_date = (today - timedelta(days=days_ago)).strftime('%Y-%m-%d %H:%M:%S')
        
        cursor.execute(
            "INSERT INTO assay_results (assayer_id, sample_id, gold_content, test_date, notes) VALUES (?, ?, ?, ?, ?)",
            (benchmark_id, sample_id, gold_content, test_date, "Benchmark test")
        )
    
    # For other assayers
    for name, assayer_id in assayer_ids.items():
        if name == "John Smith":  # Skip the benchmark assayer
            continue
        
        # Each assayer tests a random subset of samples
        assayer_samples = random.sample(sample_ids, k=random.randint(15, len(sample_ids)))
        
        for sample_id in assayer_samples:
            benchmark_value = benchmark_values[sample_id]
            
            # Add a small random deviation from benchmark
            deviation = round(random.uniform(-5.0, 5.0), 1)
            gold_content = max(0, min(999.9, benchmark_value + deviation))
            
            # Use a date within the last 30 days
            days_ago = random.randint(0, 29)
            test_date = (today - timedelta(days=days_ago)).strftime('%Y-%m-%d %H:%M:%S')
            
            # Add a note based on the deviation
            if abs(deviation) < 1.0:
                note = "Close match to benchmark"
            elif deviation > 0:
                note = "Higher than benchmark"
            else:
                note = "Lower than benchmark"
            
            cursor.execute(
                "INSERT INTO assay_results (assayer_id, sample_id, gold_content, test_date, notes) VALUES (?, ?, ?, ?, ?)",
                (assayer_id, sample_id, gold_content, test_date, note)
            )
    
    conn.commit()
    conn.close()
    
    print("Sample data initialization complete!")
    print(f"Added {len(assayers)} assayers")
    print(f"Added {len(sample_ids)} unique samples")
    print(f"Set {assayers[0][0]} as the benchmark assayer")

if __name__ == "__main__":
    init_sample_data()