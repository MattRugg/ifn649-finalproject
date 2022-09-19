typedef void (*errorCB)(String);

class TagUtils
{
  private:
    typedef enum {
      STATE_BEGIN = 0,
      STATE_TAG_ID = 1,
      STATE_END = 2
    } TAG_READ_STATE_MACHINE;
  
    // State machine variables
    TAG_READ_STATE_MACHINE state;
    char cTagID[13];
    int countTagBytes;

    byte ascii2byte(char ascii_nibble)
    {
      if (ascii_nibble >= '0' && ascii_nibble <= '9')
        return ascii_nibble - '0';

      if (ascii_nibble >= 'A' && ascii_nibble <= 'F')
        return ascii_nibble - 'A' + 10;
    }

    errorCB errorCallback = NULL;
  
  public:

    TagUtils() {
      state = STATE_BEGIN;
      countTagBytes = 0;
    }

    TagUtils(errorCB userErrorCallback):TagUtils() {
      errorCallback = userErrorCallback;
    }

    char* checkCRC(char *cTagID)
    {
      byte bTagID[6];
      byte crc = 0;
      
      // we have to convert ASCII to bytes
      // before and accumulate bytes at the
      // same time

      //Serial.println(cTagID);

      for (int i = 0; i < sizeof(bTagID); i++){

        // Convert ascii-represented nibbles to bytes
        int idx = i*2;
        bTagID[i] = ascii2byte(cTagID[idx]) << 4;
        bTagID[i] += ascii2byte(cTagID[idx+1]);

        // XOR every byte except for the CRC itself
        if (i < sizeof(bTagID)-1)
          crc ^= bTagID[i];

        // Serial.printf("%d %c%c = %d, acc = %d\n", i, cTagID[idx], cTagID[idx+1], bTagID[i], crc);
      }

      // Serial.printf("acc %d crc %d\n", crc, bTagID[5]);
      
      if (crc == bTagID[5])
      {
        return cTagID;
      }

      return NULL;
      
    }
    
    char* readTagByte(byte A)
    {
      if (state == STATE_BEGIN && A == 0x02)
      {
        state = STATE_TAG_ID;
        return NULL;
      }
    
      if (state == STATE_TAG_ID)
      {
        if (countTagBytes < sizeof(cTagID)-1)
        {
          cTagID[countTagBytes] = A;
          countTagBytes++;
        }
    
        if (countTagBytes == sizeof(cTagID)-1)
        {
          state = STATE_END;
          cTagID[countTagBytes++] = 0; // Add null termination
        }
        
        return NULL;
      }
    
      if (state == STATE_END && A == 0x03)
      {
        countTagBytes = 0;   // reset byte counter for next tag
        state = STATE_BEGIN; // rewind state machine
        
        if (A == 0x03){
          char * retTag = checkCRC(cTagID);
          if (retTag != NULL){
            return retTag;
          } else {
            // failed checksum
            if (errorCallback != NULL)
              errorCallback("Failed checksum");
            return NULL;
          }
        } else {
          // Could not find the control character 0x03:
          // It's likely the RFID tag wasn't properly read

          if (errorCallback != NULL)
              errorCallback("Unexpected end control character");

          return NULL;
        }
      }  
    }
};
