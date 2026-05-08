// # Limit switch dirtection and Pin
// Door - 1/2(Com/Up) - Pin D2
// Chair - 1/3(Com/Down) - Pin D3

// Interaction button Pin - Pin D4
// Button LED - D5

// Relay switch - D6

const int buttonCount = 3;
const int button[buttonCount] = {2,3,4};

const int ledCount = 1;
const int led[ledCount] = {5};

const int relaySwitch = 6;
bool buttonState[buttonCount];
bool lastButtonState[buttonCount];
unsigned long lastDebounceTime[buttonCount];
unsigned long debounceDelay = 50;

String msg;

bool isBlinking = false;
long previousBlinkTime = 0;
const long blinkInterval = 500;

void setup() {
  Serial.begin(115200);
  delay(500);
  pinMode(LED_BUILTIN, OUTPUT);
  pinMode(relaySwitch, OUTPUT);
  digitalWrite(relaySwitch, HIGH);
  for (int i = 0; i < buttonCount; i++) {
    pinMode(button[i], INPUT_PULLUP);
    buttonState[i] = HIGH;
    lastButtonState[i] = HIGH;
    lastDebounceTime[i] = 0;
    
    if (i < ledCount) {
      pinMode(led[i], OUTPUT);
    }
  }
}

void loop() {
  readSerial();
  readButton();
  ledBlink();
}

void ledBlink(){
  if(isBlinking){
    long currentMillis = millis();
    if(currentMillis - previousBlinkTime >= blinkInterval){
      previousBlinkTime = currentMillis;

      int currentLedState = digitalRead(led[0]);
      digitalWrite(led[0],!currentLedState);
    }
  }
}

void readSerial(){
  while (Serial.available() > 0){
    char  c = (char)Serial.read();

    if( c == '\n' || c == '\r'){
      if (msg.length() > 0){
        // Below for 'int' trigger
        // int cmd = msg.toInt()

        String text = msg;
        text.toLowerCase();

        msg = "";

        if(text == "msg"){
          Serial.println("RESPOND");
        }

        if(text == "leddefault"){
          ledControl(0, true);
          isBlinking = false;
        }
        if(text == "ledblink"){
          isBlinking = true;
          // Serial.println("LEDBLINK");

        }
        if(text == "ledoff"){
          ledControl(0, false);
          isBlinking = false;          
        }
        // if(text == "ledron"){
        //   ledControl(1, true);
          
        // }
        // if(text == "ledroff"){
        //   ledControl(1, false);
          
        // }
        if(text == "lighton"){
          digitalWrite(relaySwitch, HIGH);          
        }
        if(text == "lightoff"){
          digitalWrite(relaySwitch, LOW);          
        }
      }
    }else{
      msg += c;
    }
  } 
}

void readButton() {
  for (int i = 0; i < buttonCount; i++) {
    bool currentState = digitalRead(button[i]);

    if(currentState != lastButtonState[i]){
      lastDebounceTime[i] = millis();
      lastButtonState[i] = currentState;
    }

    if((millis() - lastDebounceTime[i]) > debounceDelay){
      if(currentState != buttonState[i]){
        buttonState[i] = currentState;
        
        if(buttonState[i] == LOW){
          sendSerial(true, i);
          // Serial.print(i);
          // Serial.println(" Pressed");
        }else if(buttonState[i] == HIGH){
          sendSerial(false,i);
          // Serial.print(i);
          // Serial.println(" Released");
        }
      }
    }
  }
}

void sendSerial(bool active, int index){
  // if (index == 0) Serial.println(active ? "DoorClose" : "DoorOpen");
  if (index == 0) Serial.println(active ? "DoorOpen" : "DoorClose");
  else if (index == 1) Serial.println(active ? "Sit" : "Stand");

  if (index == 2){
    if(active){
      Serial.println("InterOne");
      // ledControl(0, true);
    }else{
      // ledControl(0, false);
    }
  }

}

void ledControl(int index, bool activate){
  if(activate){
    digitalWrite(led[index], HIGH);
  }else{
    digitalWrite(led[index], LOW);
  }
}