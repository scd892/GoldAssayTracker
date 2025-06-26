from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional

@dataclass
class Assayer:
    """Class representing an assayer (lab technician)"""
    assayer_id: Optional[int] = None
    name: str = ""
    employee_id: str = ""
    is_active: bool = True
    joining_date: datetime = datetime.now()
    profile_picture: str = ""  # Base64 encoded or file path to image
    work_experience: str = ""  # Text describing work experience

@dataclass
class AssayResult:
    """Class representing a single assay result"""
    result_id: Optional[int] = None
    assayer_id: int = 0
    sample_id: str = ""
    gold_content: float = 0.0
    test_date: datetime = datetime.now()
    notes: str = ""

@dataclass
class Benchmark:
    """Class representing a benchmark assayer"""
    id: Optional[int] = None
    assayer_id: int = 0
    set_date: datetime = datetime.now()
    is_active: bool = True

@dataclass
class Deviation:
    """Class representing a deviation calculation"""
    sample_id: str = ""
    assayer_name: str = ""
    gold_content: float = 0.0
    benchmark_value: float = 0.0
    absolute_deviation: float = 0.0
    percentage_deviation: float = 0.0
    test_date: datetime = datetime.now()
