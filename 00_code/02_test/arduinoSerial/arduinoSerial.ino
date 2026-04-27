const int buttonCount = 2;
const int button[buttonCount] = {2,3};
bool buttonState[buttonCount];
bool lastButtonState[buttonCount];
unsigned long lastDebounceTime[buttonCount];
unsigned long debounceDelay = 50;

String msg;

void setup() {
  Serial.begin(115200);
  delay(500);
  pinMode(LED_BUILTIN, OUTPUT);
  for (int i = 0; i < buttonCount; i++) {
    pinMode(button[i], INPUT_PULLUP);
    buttonState[i] = HIGH;
    lastButtonState[i] = HIGH;
    lastDebounceTime[i] = 0;
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

        if(text == "LED"){
          for(int i =0; i < 5; i ++){
            digitalWrite(LED_BUILTIN, HIGH);
            delay(500);
            digitalWrite(LED_BUILTIN, LOW);
            delay(500); 
          }
        }
        if(text == "msg"){
          delay(2000);
          Serial.println("RESPOND");
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
          Serial.print(i);
          Serial.println(" Pressed");
        }else if(buttonState[i] == HIGH){
          sendSerial(false,i);
          Serial.print(i);
          Serial.println(" Released");
        }
      }
    }
  }
}

void sendSerial(bool active, int index){
  if (index == 0) Serial.println(active ? "DoorOpen" : "DoorClose");
  else if (index == 1) Serial.println(active ? "Sit" : "Stand");
}
