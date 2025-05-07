#include <EEPROM.h>
#include <LiquidCrystal_I2C.h>
#include <Keypad.h>
#include <Wire.h>
#include <RTClib.h>
#define CASH_AMOUNT_ADDR 0
#define ONLINE_AMOUNT_ADDR sizeof(int)
#define LOG_START_ADDR 100  // Logs start at EEPROM address 100
#define LOG_ENTRY_SIZE 10   // Each log occupies 10 bytes
#define MAX_LOGS 100        // Limit logs to avoid EEPROM overflow
#define CASH_LOG 0
#define ONLINE_LOG 1

RTC_DS3231 rtc;
const byte ROWS = 4;
const byte COLS = 4;
char keys[ROWS][COLS] = {
  {'1', '2', '3', 'm'},
  {'4', '5', '6', '+'},
  {'7', '8', '9', '-'},
  {'*', '0', '/', 'e'}
};
byte rowPins[ROWS] = {9, 8, 7, 6};
byte colPins[COLS] = {5, 4, 3, 2};
Keypad keypad = Keypad(makeKeymap(keys), rowPins, colPins, ROWS, COLS);

int cashAmount;
int onlineAmount;
String buffer = "";
char operators[] = {'e', 'm'};

LiquidCrystal_I2C lcd(0x27, 16, 2);

void setup() {
  Serial.begin(9600);
  lcd.begin();
  EEPROM.get(CASH_AMOUNT_ADDR, cashAmount);
  EEPROM.get(ONLINE_AMOUNT_ADDR, onlineAmount);
  lcd.print("--SALES--");
  lcd.setCursor(0, 1);
  lcd.print("---TRACKER---");
  delay(500);
  lcd.clear();
  lcd.print("----Mentor----");
  lcd.setCursor(0,1);
  lcd.print("--Mrs.A Shinde--");
  delay(1300);
  lcd.clear();
  lcd.print("----Makers----");
  lcd.setCursor(0,1);
  lcd.print("---103_106---");
  delay(1000);
  lcd.clear();
  lcd.print("--SALES--");
  lcd.setCursor(0, 1);
  lcd.print("---TRACKER---");
  delay(500);
  
  
  
 
  
  
}

void loop() {
  
 if (Serial.available()) {
  String dateInput = Serial.readStringUntil('\n');
  if(dateInput.length()>1){  
  // Split the date range "20/03/2025-22/03/2025"
  lcd.clear();
  lcd.print("Transmitting");
  lcd.setCursor(0,1);
  lcd.print("Data...");
   
  int dashIndex = dateInput.indexOf('-');
  
  if (dashIndex != -1) {
    // Extract start and end dates
    String startDate = dateInput.substring(0, dashIndex);
    String endDate = dateInput.substring(dashIndex + 1);
    
    int startDay = startDate.substring(0, 2).toInt();
    int startMonth = startDate.substring(3, 5).toInt();
    int startYear = startDate.substring(6, 10).toInt();
    
    int endDay = endDate.substring(0, 2).toInt();
    int endMonth = endDate.substring(3, 5).toInt();
    int endYear = endDate.substring(6, 10).toInt();
    // Iterate through the date range and send logs
    DateTime startDateTime(startYear, startMonth, startDay, 0, 0, 0);
    DateTime endDateTime(endYear, endMonth, endDay, 23, 59, 59);

    while (startDateTime <= endDateTime) {
      dataTransmit(startDateTime.day(), startDateTime.month(), startDateTime.year());
      startDateTime = startDateTime + TimeSpan(1, 0, 0, 0);  // Move to next day
    }
    lcd.clear();
    lcd.print("Data Transmitted");
  } else {
    // If no range, process single date
    int day = dateInput.substring(0, 2).toInt();
    int month = dateInput.substring(3, 5).toInt();
    int year = dateInput.substring(6, 10).toInt();
    dataTransmit(day, month, year);
    lcd.clear();
    lcd.print("Data Transmitted");
  }
  dateInput="";
}
}


  char key = keypad.getKey();
  if (key) {  // Process key only when pressed
    
    bool isDelimiter = false;
    for (int i = 0; i < sizeof(operators); i++) {
      if (key == operators[i]) {
        isDelimiter = true;
        break;
      }
    }
    if (isDelimiter) {
      processInput(key);
    } else {
      buffer += key;
      lcd.clear();
      lcd.print(buffer);
    }
  }
}

void processInput(char input) {
  if (input == 'e') {
    evaluateExpression();
  } else if (input == 'm') {
    char lastChar = buffer.charAt(buffer.length() - 1);
    buffer.remove(buffer.length() - 1);

    if (lastChar == '+') {
      //addToCash();
      int amount = buffer.toInt();
      storeLog(amount,CASH_LOG);
    } else if (lastChar == '*') {
      //addToOnline();
      int amount = buffer.toInt();
      storeLog(amount,ONLINE_LOG);
    } else if (lastChar == '-') {
      //reduceFromCash();
      int amount = buffer.toInt();
      storeLog(-amount,CASH_LOG);
    } else if (lastChar == '/') {
      //printAmount();
       enterDateAndDisplay();
      
    } else {
      lcd.clear();
      lcd.print("Syntax Error!");
      buffer="";
    }
  } else {
    lcd.clear();
    lcd.print("Syntax Error!");
  }
 
}

void evaluateExpression() {
  int result = parseAndEvaluateExpression(buffer);
  lcd.clear();
  lcd.print(buffer);
  lcd.print("=");
  lcd.print(result);
  buffer = "";
}

int parseAndEvaluateExpression(String expression) {
  int operand1 = 0;
  int operand2 = 0;
  char op;
  sscanf(expression.c_str(), "%d%c%d", &operand1, &op, &operand2);
  switch (op) {
    case '+': return operand1 + operand2;
    case '-': return operand1 - operand2;
    case '*': return operand1 * operand2;
    case '/': return operand2 != 0 ? operand1 / operand2 : 0;
    default: return 0;
  }
}

 

 
 




//updated functions

 


void storeLog(int amount, int amountType) {
  // Read the current log index (stored at LOG_START_ADDR)
    if (!rtc.begin()) {
    lcd.print("Couldn't find RTC");
    return;
  }
  int logIndex;
  EEPROM.get(LOG_START_ADDR, logIndex);

  // Prevent overflow
  if (logIndex >= MAX_LOGS) {
    lcd.clear();
    lcd.print("Log Full!");
    return;
  }

  // Calculate address for the new log
  int logAddr = LOG_START_ADDR + 1 + (logIndex * LOG_ENTRY_SIZE);

  // Get current date and time from RTC
  DateTime now = rtc.now();
  // Store date, time, amountType, and amount in EEPROM
  EEPROM.put(logAddr, now.year());
  EEPROM.write(logAddr + 2, now.month());
  EEPROM.write(logAddr + 3, now.day());
  EEPROM.write(logAddr + 4, now.hour());
  EEPROM.write(logAddr + 5, now.minute());
  EEPROM.write(logAddr + 6, amountType);
  EEPROM.put(logAddr + 7, amount);
  
  // Increment log index and update in EEPROM
  logIndex++;
  EEPROM.put(LOG_START_ADDR, logIndex);

  // Show on LCD
  lcd.clear();
    if(amountType==CASH_LOG){
    if(amount<0){lcd.print("Cash Reduced");amount=-amount;}
    else{lcd.print("Cash Added");}
  }
  else{lcd.print("Online Added");}
  lcd.setCursor(0,1);
  lcd.print(amount);
  lcd.print(" Rs ");
  buffer="";
 
}
void displayAmountsForDate(int day, int month, int year) {
  cashAmount = 0;
  onlineAmount = 0;
  
  // Read total log count
  int logIndex;
  EEPROM.get(LOG_START_ADDR, logIndex);
  if (logIndex > MAX_LOGS) logIndex = MAX_LOGS;  // Prevent overflow
  
  // Iterate over each log
  for (int i = 0; i < logIndex; i++) {
    int logAddr = LOG_START_ADDR + 1 + (i * LOG_ENTRY_SIZE);
    // Read date from EEPROM
    int logYear;
    EEPROM.get(logAddr, logYear);
    int logMonth = EEPROM.read(logAddr + 2);
    int logDay = EEPROM.read(logAddr + 3);

    // Check if the log matches the given date
    if (logYear == year && logMonth == month && logDay == day) {
      int logAmountType = EEPROM.read(logAddr + 6);
      int logAmount;
      EEPROM.get(logAddr + 7, logAmount);

      // Add to respective amounts
      if (logAmountType == CASH_LOG) {
        cashAmount += logAmount;
      } else if (logAmountType == ONLINE_LOG) {
        onlineAmount += logAmount;
      }
    }
  }

  // Display the results on the LCD
  lcd.clear(); 
  lcd.print(day);
  lcd.print("/");
  lcd.print(month);
  lcd.print("/");
  lcd.print(year);
  lcd.setCursor(0,1);
  lcd.print("C:");
  lcd.print(cashAmount);
  lcd.print(" O:");
  lcd.print(onlineAmount);
 buffer="";
}


void enterDateAndDisplay() {
  lcd.clear();
  lcd.print("Date: ");
  lcd.setCursor(0, 1);
  String temp = "";
  
  while (true) {
    char c = keypad.getKey();
    if (c) {
      // '+' pressed → Show today's amounts immediately
      // Collect date input
      temp += c;
      if(temp=="+"){
       if (!rtc.begin()) {
       lcd.print("Couldn't find RTC");
       return;
       }
       DateTime now=rtc.now();
       displayAmountsForDate(now.day(),now.month(),now.year());
      return;
     }
      lcd.clear();
      lcd.print("Date: ");
      lcd.print(temp);

      // Check if full date is entered (10 chars: DD/MM/YYYY)
      if (temp.length() == 10) {
        int day = temp.substring(0, 2).toInt();
        int month = temp.substring(3, 5).toInt();
        int year = temp.substring(6, 10).toInt();
        displayAmountsForDate(day, month, year);
        return;
      }
    }
  }
}

 

void dataTransmit(int day, int month, int year) {
  // Read total log count
  int logIndex;
  EEPROM.get(LOG_START_ADDR, logIndex);
  if (logIndex > MAX_LOGS) logIndex = MAX_LOGS;  // Prevent overflow
  
  // Flag to check if data is found
  bool dataFound = false;

  // Iterate over each log
  for (int i = 0; i < logIndex; i++) {
    int logAddr = LOG_START_ADDR + 1 + (i * LOG_ENTRY_SIZE);
    
    // Read date from EEPROM
    int logYear;
    EEPROM.get(logAddr, logYear);
    int logMonth = EEPROM.read(logAddr + 2);
    int logDay = EEPROM.read(logAddr + 3);

    // Check if the log matches the given date
    if (logYear == year && logMonth == month && logDay == day) {
      int logHour = EEPROM.read(logAddr + 4);
      int logMinute = EEPROM.read(logAddr + 5);
      int logAmountType = EEPROM.read(logAddr + 6);
      int logAmount;
      EEPROM.get(logAddr + 7, logAmount);

      // Determine amount type string
      String typeStr = (logAmountType == CASH_LOG) ? "Cash" : "Online";

      // Format and transmit data
      Serial.print(day < 10 ? "0" : "");
      Serial.print(day);
      Serial.print("/");
      Serial.print(month < 10 ? "0" : "");
      Serial.print(month);
      Serial.print("/");
      Serial.print(year);
      Serial.print(", ");
      Serial.print(logHour < 10 ? "0" : "");
      Serial.print(logHour);
      Serial.print(":");
      Serial.print(logMinute < 10 ? "0" : "");
      Serial.print(logMinute);
      Serial.print(", ");
      Serial.print(logAmount);
      Serial.print(", ");
      Serial.print(typeStr);
      Serial.println(", ");
      dataFound = true;
    }
  }

  // If no data found, send "No Data" message
  if (!dataFound) {
      Serial.print(day < 10 ? "0" : "");
      Serial.print(day);
      Serial.print("/");
      Serial.print(month < 10 ? "0" : "");
      Serial.print(month);
      Serial.print("/");
      Serial.print(year);
      Serial.print(", ");
      Serial.print("00");
      Serial.print(":");
      Serial.print("00");
      Serial.print(":");
      Serial.print("00");
      Serial.print(", ");
      Serial.print("00");
      Serial.print(", ");
      Serial.print("No Logs");
      Serial.println(", ");
     
  }
}
