/*
System state header file
*/

#ifndef my_sys_state_h
#define my_sys_state_h
#include <Arduino.h>


// ------ circular arrays:

template<typename tData, int maxLen> class tCircularArray {
  tData list[maxLen];
  int caInd = 0;
  bool full = false;

public:

  int numberOfElements() {
    if (full)
      return maxLen;
    else
      return caInd;
  };

  void put(tData x) {
    memcpy(&list[caInd], &x, sizeof(tData));
    caInd += 1;
    if (caInd >= maxLen) {
      caInd = 0;
      full = true;
    }
  };

  void get(int n, tData &y) {
    // for (int i=0; i<nElems; i++) get(i, sensVals);
    if (n < 0 || n >= maxLen) return;
    int ix = caInd - n - 1;
    if (ix < 0) ix += maxLen;
    memcpy(&y, &list[ix], sizeof(tData));
  };

  void get(tData &y) {
    get(0, y);
  };  // get the most recent data
};


// ------ System info, centralize data:

typedef struct {
  unsigned long eventTime = 0;
  int eventId;
} tEvent;


// length of data saving (circular) buffers
#define BUFF_LEN 200

// the main class doing the storage & show job
class MySysState {
public:
  MySysState() = default;
  ~MySysState();

  // events data
  tCircularArray<tEvent, BUFF_LEN> buff1;
  tEvent oneEvent;

  void eventStore(int eventId) {
    oneEvent.eventId = eventId;
    oneEvent.eventTime = millis();
    buff1.put(oneEvent);
  };
  
  String event2str() {
    String str = "id=" + String(oneEvent.eventId) + " t=" + String(oneEvent.eventTime);
    return str;
  };

  // show one event
  void showEvent() {
    Serial.println(event2str());
  }

  // show all events
  void showAllEvents() {
    // see what is in the buffers (they should start empty)
    int nElems = buff1.numberOfElements();
    for (int j = nElems-1; j >= 0; j--) {
      buff1.get(j, oneEvent);
      showEvent();
    }
  }

};

// declare one object to use everywhere
extern MySysState ss;

// testing functions implemented in the .cpp :
void ss_loop_demo_2();

#endif  // my_sys_state_h
