# Delivery Order Analyzer

A secure web application for analyzing delivery order data from Excel files. This tool processes food delivery orders, extracts item quantities, and generates detailed reports for business analysis.

## Features

- **Secure Access**: Password-protected application with configurable authentication
- **Excel File Upload**: Process delivery order data from Excel (.xlsx/.xls) files
- **Intelligent Parsing**: Automatically extracts food items and quantities from order text
- **Interactive Analysis**: Select specific orders for targeted analysis
- **Comprehensive Reporting**: Generate detailed reports with item quantities and totals
- **Data Export**: Download analysis results as CSV files or text reports
- **Real-time Processing**: Instant analysis and visualization of delivery data

## Installation

### Prerequisites

- Python 3.7 or higher
- pip package manager

### Setup

1. Clone the repository:
```bash
git clone <repository-url>
cd delivery-analyzer
```

2. Install required dependencies:
```bash
pip install -r requirements.txt
```

3. Configure authentication:

   **For local development:**
   Create a `config.json` file in the project root:
   ```json
   {
     "password": "your_secure_password"
   }
   ```

   **For Streamlit Cloud deployment:**
   Add the password to your app's secrets in the Streamlit Cloud dashboard:
   ```toml
   password = "your_secure_password"
   ```

4. Ensure you have the food items reference file:
   - The `food_items.csv` file should contain the list of available food items
   - This file is used for matching and parsing order data

## Usage

### Running Locally

1. Start the Streamlit application:
```bash
streamlit run delivery_analyzer_secure_enhanced.py
```

2. Open your web browser and navigate to the displayed URL (typically `http://localhost:8501`)

3. Enter the configured password to access the application

### Processing Orders

1. **Upload Excel File**: Use the sidebar to upload your delivery order Excel file
2. **Process Data**: Click "Process Excel File" to convert and load the data
3. **Select Orders**: Choose specific delivery orders for analysis using checkboxes
4. **Analyze**: Click "Analyze Selected Orders" to generate reports
5. **Export Results**: Download CSV files or detailed text reports

## Data Format

### Excel File Structure

The application expects Excel files with the following columns (starting from row 4):
- Column 1: Delivery identifier
- Column 2: Customer name
- Column 3: Phone number
- Column 4: Address
- Column 5: City
- Column 6: ZIP code
- Column 7: Items ordered (text format)

### Items Format

Items should be formatted as: `[Item Name] x[Quantity], [Item Name] x[Quantity], Total: $[Amount]`

Example: `肉末香茹胡罗卜糯米烧卖 15个/份x3， 荠菜鲜肉馄饨 50/份x2， 总价：$100.00`

## Configuration

### Food Items List

Update the `food_items.csv` file to include all available food items. Each item should be on a separate line under the `food_items` column header.

### Authentication

The application supports two authentication modes:

1. **Local Development**: Uses `config.json` file
2. **Cloud Deployment**: Uses Streamlit secrets management

## Deployment

### Streamlit Cloud

1. Push your code to a GitHub repository
2. Connect the repository to Streamlit Cloud
3. Configure the password in the app's secrets
4. The app will automatically deploy and update when you push changes

### Other Platforms

The application can be deployed on any platform that supports Streamlit applications. Ensure the password is properly configured through environment variables or the platform's secrets management system.

## Technical Details

### Dependencies

- **Streamlit**: Web application framework
- **Pandas**: Data processing and analysis
- **OpenPyXL**: Excel file reading
- **Regular Expressions**: Text parsing and pattern matching

### Architecture

- **Frontend**: Streamlit web interface
- **Backend**: Python data processing
- **Authentication**: Password-based access control
- **Data Storage**: CSV file output for processed data

## Troubleshooting

### Common Issues

1. **Excel File Not Processing**: Ensure the file follows the expected format and starts data from row 4
2. **Items Not Matching**: Check that food items in `food_items.csv` match the naming in your Excel file
3. **Authentication Error**: Verify password configuration in config.json or Streamlit secrets
4. **Missing Dependencies**: Run `pip install -r requirements.txt` to install all required packages

### Error Messages

- **"food_items.csv not found"**: Ensure the food items reference file exists in the project directory
- **"Password not configured"**: Set up authentication using config.json or Streamlit secrets
- **"Error processing Excel file"**: Check file format and data structure

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## Security

- All data processing happens locally or in your deployed environment
- No data is sent to external services
- Password protection prevents unauthorized access
