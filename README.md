# Meeting Recorder

Records the whole meeting conversation (your mic plus Zoom, Teams or Meet call audio) into one MP3, in the browser, without the meeting app's own recording. It shows a live transcript while you record and can also save a screen video.

## Use it
Open the GitHub Pages link in Chrome or Edge on a computer.

- **Online call, Windows:** share "Entire screen" and turn on "Also share system audio".
- **Online call, Mac:** join the meeting in a Chrome tab and share that tab with "Also share tab audio".
- **In a room:** choose "In a room" to record just the microphone.
- **Live transcript:** appears under the timer while you record (Chrome or Edge, needs internet). Pick the language next to it. Tap a name under "Who is speaking?" to label the lines.
- **Screen video:** tick "Also save a screen video" (online calls only).

Ask everyone to say their name at the start. **Stop and save** puts `<meeting>.mp3`, `<meeting>_notes.txt` (attendees, speaker marks) and, if chosen, `<meeting>_video.mp4` in your Downloads. The recording is never uploaded; only the live transcript uses the browser's online speech service. The rough live transcript is also saved at the end of the notes file.

## Files (all in this one folder)
- `index.html` is the whole recorder, with the MP3 encoder (lamejs, LGPL, see `lamejs-LICENSE.txt`) built in.
- `transcribe_meeting.py` cleans the audio, separates speakers and transcribes (sherpa-onnx + Whisper). It is used to produce the transcript and minutes from an uploaded recording.
