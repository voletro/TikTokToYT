# TikTok to YT
By voletro.

Downloads a trending TikTok video and uploads it to YouTube. This will happen every half an hour (30 mins).
## Requirements:

Firefox - https://www.mozilla.org/en-US/firefox/new/

GeckoDriver - https://github.com/mozilla/geckodriver/releases

EditThisCookie - https://addons.mozilla.org/en-US/firefox/addon/etc2/

## Setup:

1. Extract downloaded zip file to a folder. Go to that folder in a terminal.

2. Run "pip install -r requirements.txt" inside the downloaded folder.

3. Sign into YouTube on Firefox with the account you want to upload the videos to.

4. Install the EditThisCookie extension on Firefox, open it, and click the export button to export login cookies to clipboard.

5. Open the file called login.json in a text editor. Paste the exported login cookies into the file and save.

6. Run the main.py script!

## Special thanks to these people for making this project possible:

davidteather - TikTokApi - https://github.com/davidteather/TikTok-Api

SeleniumHQ - selenium - https://github.com/SeleniumHQ/selenium


