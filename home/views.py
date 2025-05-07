import os
from django.shortcuts import render
from django.http import JsonResponse
import serial
import time
from datetime import datetime
import csv
import pandas as pd
import plotly.express as px
from django.http import JsonResponse
 

def index(request):
    return render(request,'index.html')

 
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from datetime import datetime

@csrf_exempt
def send_command_view(request):
    if request.method == "POST" or request.method == "GET":
        from_date = request.GET.get('from_date') or request.POST.get('from_date')
        to_date = request.GET.get('to_date') or request.POST.get('to_date')
    
        from_date_obj = datetime.strptime(from_date, "%Y-%m-%d")
        to_date_obj = datetime.strptime(to_date, "%Y-%m-%d")

        if from_date_obj > to_date_obj:
            from_date, to_date = to_date, from_date

        year1, month1, day1 = map(int, from_date.split('-'))
        year2, month2, day2 = map(int, to_date.split('-'))

        # command_send = f"{day1:02d}/{month1:02d}/{year1}-{day2:02d}/{month2:02d}/{year2}"

        command_send = f"{day1:02d}/{month1:02d}/{year1}-{day2:02d}/{month2:02d}/{year2}"

        # command_send = f"{day1}/{month1}/{year1}-{day2}/{month2}/{year2}"
        # command_send='19/03/2025-20/04/2025'

        # For now, just return dummy response
 
    
    # Connect to Bluetooth device
        bt = connect_bluetooth(BLUETOOTH_PORT, BAUD_RATE)
        if not bt:
            print("Failed to connect. Exiting.")
            return render(request, 'index.html', {'response': 'Bluetooth Connection Failed.'})

    
        try:
        # Create a test date string (today's date)
            today = datetime.now().strftime("%d-%m-%Y")
            #command = f"DATE:{today}"  # More descriptive command format
        
        # Send command
            if not send_command(bt,command_send):
                print("Failed to send command")
                return render(request, 'index.html', {'response': 'Bluetooth Send Command Connection Failed.'})

        
        # Receive response
            response = receive_data(bt)
            if response:
                append_to_csv(response)
                return render(request, 'index.html', {'response': f"Date: {from_date_obj} to {to_date_obj}\n{response}"})
            else:
                return render(request, 'index.html', {'response': 'None response recived'})
            
        except KeyboardInterrupt:
                return render(request, 'index.html', {'response': 'User Interupted the program.'})
        finally:
        # Ensure connection is always closed
            if bt and bt.is_open:
                bt.close()
                print("Bluetooth connection closed")
         
         
    else:
        return render(request, 'index.html', {'response': 'Invalid request method.'})

# Configuration
BLUETOOTH_PORT = 'COM8'  # Replace with your Bluetooth port
BAUD_RATE = 9600
CONNECTION_TIMEOUT = 5  # seconds
COMMAND_TIMEOUT = 20    # seconds to wait for response

def connect_bluetooth(port, baud_rate, retries=3, delay=1):
    """Establish Bluetooth connection with retry mechanism."""
    for attempt in range(retries):
        try:
            bt = serial.Serial(port, baud_rate, timeout=1)
            print(f"Successfully connected to {port} at {baud_rate} baud rate.")
            return bt
        except serial.SerialException as e:
            print(f"Attempt {attempt + 1} failed: {e}")
            if attempt < retries - 1:
                time.sleep(delay)
    print("Failed to establish Bluetooth connection after multiple attempts.")
    return None

def send_command(bt, command):
    """Send a command to Arduino with verification."""
    if not bt or not bt.is_open:
        print("Error: Bluetooth connection not established")
        return False
    
    try:
        print(f"Sending command: {command}")
        bt.write((command + '\n').encode())
        bt.flush()  # Ensure data is sent immediately
        return True
    except Exception as e:
        print(f"Error sending command: {e}")
        return False

def receive_data(bt, timeout=10):
    """Receive all data lines from Arduino within the timeout period."""
    if not bt or not bt.is_open:
        print("Error: Bluetooth connection not established")
        return None

    start_time = time.time()
    received_lines = []  # List to store multiple lines of response

    while time.time() - start_time < timeout:
        if bt.in_waiting:
            try:
                data = bt.readline().decode().strip()  # Read a line
                if data:  
                    received_lines.append(data)  # Store in list
                    print(f"Received: {data}")  # Print each line
            except Exception as e:
                print(f"Error reading data: {e}")
                return None
        time.sleep(0.1)  # Prevents busy waiting

    if received_lines:
        return "\n".join(received_lines)  # Return all lines as a single string
    else:
        print("Timeout reached while waiting for response")
        return None


from datetime import datetime

@csrf_exempt
def manual_edit(request):
    if request.method == 'POST':
        raw_date = request.POST.get('date')  # '2025-01-01'
        amount = request.POST.get('amount')
        amount_type = request.POST.get('amount_type')

        # Convert 'YYYY-MM-DD' → 'DD/MM/YYYY'
        date_obj = datetime.strptime(raw_date, "%Y-%m-%d")
        formatted_date = date_obj.strftime("%d/%m/%Y")
        day_name = date_obj.strftime("%A")

        # Call function to append manual data
        file_path = os.path.join(r"C:/Users/Dell/Documents/DJAngo/Track/hello/zdatabase/transaction.csv")
        manual_edit_transaction(file_path, [(formatted_date, day_name, amount, amount_type)])
        context = {}
        # response_message = f"✅ Data submitted: {formatted_date}, ₹{amount}, {amount_type}"
        context['edit_response'] = f"Edit successful for {raw_date} - {amount_type}{amount}"
        return render(request, 'index.html',context)

    return render(request, 'index.html')
 
def manual_edit_transaction(file_path, manual_entries):
    from datetime import datetime
    import csv

    with open(file_path, 'a', newline='') as file:
        writer = csv.writer(file)

        for date_str, day_name, amount, typ in manual_entries:
            # Get day of the week
            date_obj = datetime.strptime(date_str, "%d/%m/%Y")
            day = date_obj.strftime("%A")

            # Use 00:00:00 time for manual edits
            time = "00:00:00"

            # Quote the type explicitly
            quoted_type = f'"{typ}"'

            writer.writerow([date_str, day, time, amount, typ])











 

CSV_FILE_PATH = "C:/Users/Dell/Documents/DJAngo/Track/hello/zdatabase/transaction.csv"

def visualize_data(request):
    error_message = None  # Store error messages for frontend display

    try:
        # Load CSV
        df = pd.read_csv(CSV_FILE_PATH)

        # Convert Date column to proper datetime format
        df["Date"] = pd.to_datetime(df["Date"], format="%d/%m/%Y", errors="coerce")

        # Get dates from request
        from_date = request.GET.get("from_date", "")
        to_date = request.GET.get("to_date", "")

        # If dates are provided, validate them
        if from_date and to_date:
            try:
                from_date = datetime.strptime(from_date, "%Y-%m-%d")  # Convert input to datetime
                to_date = datetime.strptime(to_date, "%Y-%m-%d")  
                if from_date > to_date:
                     from_date, to_date = to_date, from_date  # Swap the dates

                if from_date > to_date:
                    error_message = "Invalid date range: From Date must be before To Date."
                else:
                    # Filter data within the selected range
                    df = df[(df["Date"] >= from_date) & (df["Date"] <= to_date)]
            except ValueError:
                error_message = "Invalid date format. Please select valid dates."

        # If no valid data remains, return an error
        if df.empty:
            error_message = "No data available for the selected date range."

        if error_message:
            return render(request, "graphs.html", {"error": error_message})

        # Generate graphs
 # Calculate total sales
        total_sales = df[df["Amount"] > 0]["Amount"].sum()


# Create the pie chart
#         fig1 = px.pie(df, names="Type", values="Amount", title=f"Total Sales: Cash vs Online (Total: {total_sales}Rs.)",
#               color="Type", hole=0.3)

# # Show values instead of percentages
#         fig1.update_traces(textinfo='label+value')

        df["Date"] = pd.to_datetime(df["Date"], format="%d/%m/%Y")  # Ensure Date is in datetime format
        df = df.sort_values(by="Date")  # Sort by date for a proper curve
        df["Date"] = pd.to_datetime(df["Date"], format="%d/%m/%Y")  
        df = df.sort_values(by="Date")  
        df["Moving_Avg"] = df["Amount"].rolling(window=7, min_periods=1).mean()  
        df_positive = df[df["Amount"] > 0]

#         Create histogram
      

# Aggregate data by 'Type' (Cash vs Online) to calculate total amount
        df_aggregated = df_positive.groupby("Type")["Amount"].sum().reset_index()
        total_sales = df_aggregated["Amount"].sum()

        # Create a bar chart for total amounts (sum of sales)
        fig1 = px.bar(
            df_aggregated,
            x="Type",  # Payment type (Cash or Online)
            y="Amount",  # Total amount for each payment type
            title=f"Total Cash vs Online Sales Amounts: ₹{total_sales:,.2f}", 
            labels={"Type": "Payment Type", "Amount": "Total Amount (Rs.)"},
            color="Type",  # Color bars based on Type (Cash or Online)
            text="Amount",  # Display amount on top of the bars
        )
        
        fig1.update_layout(
            xaxis_title="Payment Type",
            yaxis_title="Total Amount (Rs.)",
        )

        df_expense = df[df["Amount"] < 0]

# Convert negative amounts to positive for graphing
        df_expense["Amount"] = df_expense["Amount"].abs()

# Aggregate data by 'Type' (Cash vs Online) to calculate total expense
        df_expense_aggregated = df_expense.groupby("Type")["Amount"].sum().reset_index()

# Calculate total expenses from the positive values (expenses are negative, but plotted as positive)
        total_expense = df_expense_aggregated["Amount"].sum()

# Create a bar chart for total expenses (sum of expenses)
        fig11 = px.bar(
            df_expense_aggregated,
            x="Type",  # Payment type (Cash or Online)
            y="Amount",  # Total expense for each payment type
            title=f"Total Cash vs Online Expenses: ₹{total_expense:,.2f}",  # Adding total expense to the title
            labels={"Type": "Payment Type", "Amount": "Total Expense (Rs.)"},
            color="Type",  # Color bars based on Type (Cash or Online)
            text="Amount",  # Display amount on top of the bars
        )
        
        fig11.update_layout(
            xaxis_title="Payment Type",
            yaxis_title="Total Expense (Rs.)",
        )





        fig2 = px.line(df, x="Date", y="Moving_Avg", title="Date vs Sales (7-day Moving Average)",
               markers=True, line_shape="spline", color_discrete_sequence=["#FF5733"])
        fig2.update_layout(xaxis_title="Date", yaxis_title="Sales Amount", xaxis=dict(showgrid=True), yaxis=dict(showgrid=True))

        # fig3 = px.bar(df, x=df["Date"].dt.day_name(), y="Amount", title="Days vs Sales")
        # fig3.update_layout(xaxis_title="Day", yaxis_title="Sales Amount", xaxis=dict(showgrid=True), yaxis=dict(showgrid=True))
        # Filter out rows with negative sales amounts
        filtered_df = df[df["Amount"] >= 0]

# Create bar chart: Days vs Sales (only non-negative)
        fig3 = px.bar(filtered_df, x=filtered_df["Date"].dt.day_name(), y="Amount",         
              title="Days vs Sales")
        
        fig3.update_layout(        
            xaxis_title="Day", 
         yaxis_title="Sales Amount", 
         xaxis=dict(showgrid=True), 
         yaxis=dict(showgrid=True)
        )
        
 
        # Convert "Hour" to int if it's not already
         # Extract hour and convert to integer
        df["Hour"] = df["Time"].str[:2].astype(int)
        
        # Plot histogram using Hour and Amount
        fig4 = px.histogram(df, x="Hour", y="Amount", histfunc="sum", nbins=24,
                            title="Hourly Sales Histogram",
                            labels={"Amount": "Total Sales", "Hour": "Hour of Day"})

        fig4.update_layout(xaxis=dict(dtick=1), xaxis_title="Hour", yaxis_title="Total Sales")


        # Amount range bins
        bins = [0, 50, 100, 200, 500, 1000]
        labels = ["0-50", "50-100", "100-200", "200-500", "500+"]
        df["Amount Range"] = pd.cut(df["Amount"], bins=bins, labels=labels)
        filtered_df1 = df[df["Amount"] >= 0]
        fig5 = px.bar(filtered_df1, x="Amount Range", y="Amount", title="Amount Range vs Sales",color_discrete_sequence=px.colors.qualitative.Set2)

        fig5.update_layout(xaxis_title="Amount Range", yaxis_title="Sales Amount", xaxis=dict(showgrid=True), yaxis=dict(showgrid=True))


       # Monthly Sales Histogram (Simplified)
#         Extract month and year
        df['Month'] = df['Date'].dt.strftime('%B')  # Full month name
        df['Year'] = df['Date'].dt.year

#         Calculate total sales per month (sum of all amounts)
        monthly_sales = df.groupby(['Year', 'Month'])['Amount'].sum().reset_index()
        # Calculate total revenue
        total_revenue6 = monthly_sales['Amount'].sum()
#         Define month order for proper sorting
        month_order = ['January', 'February', 'March', 'April', 'May', 'June',
                       'July', 'August', 'September', 'October', 'November', 'December']
        
# C        reate the histogram
        fig6 = px.bar(monthly_sales,
                     x='Month',
                     y='Amount',
                     title=f'Total Profits: ₹{total_revenue6:,.2f}',
                     color='Amount',
                     color_continuous_scale=px.colors.sequential.Viridis,
                     category_orders={'Month': month_order})
        
        fig6.update_layout(
            xaxis_title='Month',
            yaxis_title='Total Sales',
            xaxis={'categoryorder': 'array', 'categoryarray': month_order}
        ) 
        return render(request, "graphs.html", {
            "graph1": fig1.to_html(full_html=False),
            "graph2": fig2.to_html(full_html=False),
            "graph3": fig3.to_html(full_html=False),
            "graph4": fig4.to_html(full_html=False),
            "graph5": fig5.to_html(full_html=False),
            "graph6": fig6.to_html(full_html=False),
            "graph11": fig11.to_html(full_html=False),
            "error": None
        })
    
    except Exception as e:
        return render(request, "graphs.html", {"error": f"Unexpected error: {str(e)}"})

 
 
CSV_FILE_PATH = r"C:/Users/Dell/Documents/DJAngo/Track/hello/zdatabase/transaction.csv"

def initialize_csv():
    """Create a CSV file with headers if it doesn't exist."""
    if not os.path.exists(CSV_FILE_PATH):
        with open(CSV_FILE_PATH, mode='w', newline='') as file:
            writer = csv.writer(file)
            writer.writerow(["Date", "Day", "Time", "Amount", "Type"])  # Headers
def append_to_csv(response_data):
    """Replace existing records for received dates and append new data."""
    initialize_csv()  # Ensure CSV exists

    transactions = response_data.strip().split('\n')  # Split by new lines
    new_data = []
    received_dates = set()

    for transaction in transactions:
        parts = transaction.split(', ')
        if len(parts) != 4:
            continue  # Skip invalid rows
        
        date_str, time_str, amount, trans_type = parts

        # Ignore invalid data (e.g., 'No Logs' entries)
        if trans_type.strip().lower() == "no logs":
            continue

        try:
            date_obj = datetime.strptime(date_str, "%d/%m/%Y")
            day_of_week = date_obj.strftime("%A")

            new_data.append([date_str, day_of_week, time_str, amount, trans_type])
            received_dates.add(date_str)
        except ValueError as e:
            print(f"Skipping invalid entry: {transaction} | Error: {e}")

    if not new_data:
        return  # No valid transactions

    # Load existing CSV data
    if os.path.exists(CSV_FILE_PATH) and os.stat(CSV_FILE_PATH).st_size > 0:
        df = pd.read_csv(CSV_FILE_PATH)

        # Remove existing records for received dates
        if "Date" in df.columns:
            df = df[~df["Date"].isin(received_dates)]
        else:
            df = pd.DataFrame(columns=["Date", "Day", "Time", "Amount", "Type"])  # Handle empty file
    else:
        df = pd.DataFrame(columns=["Date", "Day", "Time", "Amount", "Type"])  # Handle missing file

    # Append new transactions
    new_df = pd.DataFrame(new_data, columns=["Date", "Day", "Time", "Amount", "Type"])
    df = pd.concat([df, new_df], ignore_index=True)

    # Save updated CSV
    df.to_csv(CSV_FILE_PATH, index=False)
 