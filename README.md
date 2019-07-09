install the requirements from the requirements.txt file
setup your slackbot_settings.py
setup your slackbot


Start by getting your bot's API Token:

    * go to https://your_teamname.slack.com/apps/manage/custom-integrations
    * Click *bots*
    * Click *Add Configuration*.
    * Choose a username.  Press "Add Bot Integration"
    * Copy your bot's API key

replace `<API-KEY>` with your bot's API-key

```
git clone
cd pongbot
pip install --ignore-installed -r requirements.txt
echo 'API_TOKEN = "<API-KEY>"' > slackbot_settings.py
./manage.py migrate
./manage.py run_bot
```
- Invite pongbot to a channel.
- Start interacting with commands like `pb help`.
