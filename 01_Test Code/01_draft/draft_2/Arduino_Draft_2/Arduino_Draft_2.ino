// Interaction button Pin
// Button No.1(Record Confess) - Pin D2
// Button No.2(Hear Confess) - Pin D3

// Limit switch dirtection and Pin
// Door - 1/2(Com/Up) - Pin D4
// Chair - 1/3(Com/Down) - Pin D5

// Button LED - 6,7
// Relay switch - 8

const int ledCount = 2;
const int led[ledCount] = {6,7};

const int buttonCount = 4;
const int button[buttonCount] = {2,3,4,5};
const int relaySwitch = 8;
bool buttonState[buttonCount];
bool lastButtonState[buttonCount];
unsigned long lastDebounceTime[buttonCount];
unsigned long debounceDelay = 50;

String msg;

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
    pinMode(led[i], OUTPUT);
  }
}

void loop() {
  readSerial();
  readButton();
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
        if(text == "ledlon"){
          ledControl(0, true);
          
        }
        if(text == "ledloff"){
          ledControl(0, false);
          
        }
        if(text == "ledron"){
          ledControl(1, true);
          
        }
        if(text == "ledroff"){
          ledControl(1, false);
          
        }
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
  if(active){
    if (index == 0) Serial.println("InterOne");
    else if (index == 1) Serial.println("InterTwo");
    ledControl(index, true);
  }else{
    if(index < 2){
      ledControl(index, false);
    }
  }


  // if (index == 2) Serial.println(active ? "DoorClose" : "DoorOpen");
  if (index == 2) Serial.println(active ? "DoorOpen" : "DoorClose");
  else if (index == 3) Serial.println(active ? "Sit" : "Stand");
}

void ledControl(int index, bool activate){
  if(activate){
    digitalWrite(led[index], HIGH);
  }else{
    digitalWrite(led[index], LOW);
  }
}

