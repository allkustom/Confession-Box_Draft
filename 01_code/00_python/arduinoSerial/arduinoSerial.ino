// String msg;

void setup() {
  Serial.begin(115200);
  pinMode(LED_BUILTIN, OUTPUT);

}

void loop() {
  readSerial();
}

void readSerial(){
  if(Serial.available()>0){
    String msg = Serial.readString();
    if(msg == "on"){
          digitalWrite(LED_BUILTIN, HIGH);
          delay(500);
          digitalWrite(LED_BUILTIN, LOW);
          delay(500); 
          digitalWrite(LED_BUILTIN, HIGH);
          delay(500);
          digitalWrite(LED_BUILTIN, LOW);
          delay(500); 

    }
  }

  // while (Serial.available() > 0){
  //   char  c = (char)Serial.read();

  //   if( c == '\n' || c == '\r'){
  //     if (msg.length() > 0){
  //       // Below for 'int' trigger
  //       // int cmd = msg.toInt()

  //       String text = msg;
  //       text.toLowerCase();

  //       msg = "";

  //       if(text == "on"){
  //         //Blink built-in LED
  //         digitalWrite(LED_BUILTIN, HIGH);
  //         delay(500);
  //         digitalWrite(LED_BUILTIN, LOW);
  //         delay(500); 
  //         digitalWrite(LED_BUILTIN, HIGH);
  //         delay(500);
  //         digitalWrite(LED_BUILTIN, LOW);
  //         delay(500); 
  //         digitalWrite(LED_BUILTIN, HIGH);
  //         delay(500);
  //         digitalWrite(LED_BUILTIN, LOW);
  //         delay(500); 
  //       }
  //     }
  //   }else{
  //     msg += c;
  //   }
  // } 
}

