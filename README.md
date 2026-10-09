# Meeting Recorder

Records the whole meeting conversation (your mic plus Zoom, Teams or Meet call audio) into one MP3, in the browser, without the meeting app's own recording.

## Use it
Open the GitHub Pages link in Chrome or Edge on a computer.

- **Online call, Windows:** share "Entire screen" and turn on "Also share system audio".
- **Online call, Mac:** join the meeting in a Chrome tab and share that tab with "Also share tab audio".
- **In a room:** choose "In a room" to record just the microphone.

Ask everyone to say their name at the start. **Stop and save** puts `<meeting>.mp3` and `<meeting>_notes.txt` (attendees, speaker marks) in your Downloads. Nothing is uploaded anywhere.

## Files
- `index.html` is the whole recorder.
- `vendor/lame.min.js` is the MP3 encoder (lamejs, LGPL; see `vendor/lamejs-LICENSE.txt`).
- `tools/transcribe_meeting.py` cleans the audio, separates speakers and transcribes (sherpa-onnx + Whisper). It is used to produce the transcript and minutes from an uploaded recording.
