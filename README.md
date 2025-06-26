# AEG labsync Monitor

A sophisticated Streamlit application for gold testing laboratory performance monitoring with advanced batch data entry capabilities and multi-AI integration for comprehensive trainee evaluation.

## Features

### Authentication System
- **Role-based access control** with 5 user account types
- **Persistent login sessions** - stay logged in until manual logout
- **Secure user management** for administrators

### User Roles & Access Levels
- **Administrator** - Full system access including user management
- **Management** - All operational features except user management
- **HR** - Monitoring, analytics, profiles, and evaluation features
- **Monitoring** - Data entry, monitoring, analytics, and profiles
- **Laboratory** - Basic access to data entry and profiles

### Core Functionality
- **Advanced Data Entry** - Batch processing with intelligent validation
- **Daily Monitoring** - Real-time performance tracking and alerts
- **Analytics Dashboard** - Comprehensive statistical analysis and visualizations
- **AI Assistant** - Multi-provider integration (OpenAI, DeepSeek, Anthropic Claude)
- **Trainee Evaluation** - Automated assessment and progress tracking
- **Inter-Laboratory Comparisons** - Cross-lab performance benchmarking
- **Gold Type Analysis** - Specialized analysis for different gold compositions
- **Mass Impact Analysis** - Physical impact calculations of assay deviations

### Technical Features
- **Interactive Visualizations** - Plotly-based charts and heatmaps
- **Database Integration** - SQLite with comprehensive data models
- **Export Capabilities** - Multiple format support for reports
- **Responsive Design** - Optimized for laboratory environments

## Technology Stack

- **Frontend**: Streamlit
- **Backend**: Python 3.11
- **Database**: SQLite
- **AI Integration**: OpenAI, DeepSeek, Anthropic Claude
- **Visualization**: Plotly, Matplotlib
- **Data Processing**: Pandas, NumPy

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/aeg-labsync-monitor.git
cd aeg-labsync-monitor
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Set up environment variables:
```bash
cp .env.example .env
# Edit .env with your API keys
```

4. Initialize the database:
```bash
python init_sample_data.py
```

5. Run the application:
```bash
streamlit run app.py --server.port 5000
```

## Usage

### Default User Accounts

The system comes with 5 pre-configured accounts for different access levels:

| Role | Username | Password | Access Level |
|------|----------|----------|--------------|
| Administrator | admin | @Algol025 | Full system access |
| Management | management | aegold995 | All features except user management |
| HR | hr | aeghr025 | Monitoring, analytics, profiles, evaluation |
| Monitoring | monitoring | aeglab3210 | Data entry, monitoring, analytics, profiles |
| Laboratory | laboratory | 17025 | Basic access to data entry and profiles |

### Key Workflows

1. **Data Entry**: Input assay results with automatic validation
2. **Performance Monitoring**: Track deviation patterns and trends
3. **AI Analysis**: Get intelligent insights on laboratory performance
4. **Report Generation**: Export comprehensive performance reports
5. **User Management**: Manage access levels and permissions (Admin only)

## Configuration

### Streamlit Configuration
The application uses custom Streamlit configuration in `.streamlit/config.toml`:
```toml
[server]
headless = true
address = "0.0.0.0"
port = 5000
```

### Environment Variables
Required environment variables in `.env`:
- `OPENAI_API_KEY` - For OpenAI integration
- `DEEPSEEK_API_KEY` - For DeepSeek integration  
- `ANTHROPIC_API_KEY` - For Claude integration

## Project Structure

```
├── app.py                  # Main Streamlit application
├── auth.py                 # Authentication and access control
├── database.py             # Core database operations
├── database_interlab.py    # Inter-laboratory comparison data
├── database_trainee.py     # Trainee evaluation data
├── user_management.py      # User management interface
├── utils.py               # Utility functions and visualizations
├── pages/                 # Individual page modules
│   ├── 01_Data_Entry.py
│   ├── 02_Daily_Monitoring.py
│   ├── 03_Analytics.py
│   ├── 04_Data_Export.py
│   ├── 05_AI_Assistant.py
│   ├── 06_Settings.py
│   ├── 07_Assayer_Profiles.py
│   ├── 08_Interlab_Comparisons.py
│   ├── 09_Gold_Type_Analysis.py
│   ├── 10_Mass_Impact_Analysis.py
│   └── 11_Trainee_Evaluation.py
├── ai_assistant.py        # Multi-provider AI integration
├── anthropic_assistant.py # Claude-specific functions
├── openai_assistant.py    # OpenAI-specific functions
├── deepseek_assistant.py  # DeepSeek-specific functions
└── assets/               # Static assets and icons
```

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/new-feature`)
3. Commit your changes (`git commit -am 'Add new feature'`)
4. Push to the branch (`git push origin feature/new-feature`)
5. Create a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For technical support or questions about laboratory implementation, please create an issue in the GitHub repository.

## Acknowledgments

- Built for AEG laboratory monitoring requirements
- Integrates industry-standard assaying practices
- Designed for compliance with laboratory quality standards