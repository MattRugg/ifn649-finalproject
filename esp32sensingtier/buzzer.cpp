#include <Arduino.h>
#include "elapsedMillis.h"

#define NOTE_MUTE (note_t)-1
#define NOTE_END (note_t)-2
#define NOTE_LOOP (note_t)-3

// Pin mapping
const int buzzerPin = 5;
const int buzzerCh = 0;

typedef struct {
  note_t note;
  uint8_t octave;
  int duration;
} Track;

int currentTrack = 0;
int trackNoteCounter = 0;

Track accessGranted[] = { 
  {NOTE_C, 5, 250},
  {NOTE_D, 5, 250},
  {NOTE_E, 5, 250},
  {NOTE_END, 5, 0}
};

Track accessDenied[] = { 
  {NOTE_D, 4, 290},
  {NOTE_MUTE, 4, 10},
  {NOTE_D, 4, 290},
  {NOTE_END, 5, 0}
};

Track emergency[] = { 
  {NOTE_E, 5, 30},
  {NOTE_MUTE, 4, 1000},
  {NOTE_LOOP, 4, 10}
};

void buzzerSetup()
{  
  // initialize the digital pin as an output.
  ledcAttachPin(buzzerPin, 0);
}

void playNote(note_t Note, int octave)
{
  if (Note == NOTE_MUTE)
  {
    Serial.println("Mute note");
    ledcWriteTone(buzzerCh, 0);
    return;
  }

  ledcWriteNote(buzzerCh, Note, octave);
}

void buzzerTrackStop()
{
  currentTrack = 0;
  trackNoteCounter = 0;
  ledcDetachPin(buzzerPin);
}

void buzzerLoop()
{
  static elapsedMillis sinceLastNote;
  Track* track = NULL;

  if (currentTrack == 1)
    track = accessGranted;
  else if (currentTrack == 2)
    track = accessDenied;
  else if (currentTrack == 3)
    track = emergency;
  else 
    return;
  
  if (trackNoteCounter) {
    Track previousNote =  track[trackNoteCounter-1];
    if (sinceLastNote >= previousNote.duration) {
      sinceLastNote = 0;

      if (track[trackNoteCounter].note == NOTE_LOOP)
      {
        trackNoteCounter = 0;
      }
      else if (track[trackNoteCounter].note == NOTE_END)
      {
        Serial.println("End of Tune note");
        currentTrack = 0;
        trackNoteCounter = 0;
        ledcDetachPin(buzzerPin);
        return;
      }

      playNote(track[trackNoteCounter].note, track[trackNoteCounter].octave);
      trackNoteCounter++;
    }
  } else {
    ledcAttachPin(buzzerPin, buzzerCh);
    sinceLastNote = 0;
    playNote(track[trackNoteCounter].note, track[trackNoteCounter].octave);
    trackNoteCounter++;
  }
}

void buzzerPlayTrack(int iTrack)
{
  currentTrack = iTrack;
  trackNoteCounter = 0;
  return;
  
  if (iTrack == 0)
  {
    ledcAttachPin(buzzerPin, buzzerCh);
    ledcWriteNote(buzzerCh, NOTE_D, 4);
    delay(300);
    ledcWriteNote(buzzerCh, NOTE_D, 4);
    delay(300);
    ledcDetachPin(buzzerPin);
  }
  else if (iTrack == 1)
  {
    ledcAttachPin(buzzerPin, buzzerCh);
    ledcWriteNote(buzzerCh, NOTE_A, 5);
    delay(150);
    ledcWriteNote(buzzerCh, NOTE_C, 5);
    delay(150);
    ledcWriteNote(buzzerCh, NOTE_D, 5);
    delay(150);
    ledcDetachPin(buzzerPin);
  }
}
