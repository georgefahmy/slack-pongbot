from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone
from history.models import Game, Season
from datetime import datetime, date
from pytz import timezone as tzone
from collections import Counter
from elo import rate_1vs1
from django.conf import settings
from django.db.models import Q
from time import sleep

default_start = date(2019, 7, 1)
trend_size = 30

class Command(BaseCommand):
    help = 'Runs slackbot'

    def handle(self, *args, **options):
        from slackbot.bot import respond_to, listen_to, Bot
        import sys, re, logging, logging.config

        begin_elo_at = 1000
        def current_time():
            tz1 = tzone("America/Los_Angeles")
            now1 = datetime.now()
            now2 = tz1.localize(now1)
            return now1

        def _get_elo(start_date):
            #get games from ORM
            games = Game.objects.filter(created_on__gt=start_date).order_by('created_on')

            #instantiate rankings object
            rankings = {}
            for game in games:
                rankings[game.winner] = begin_elo_at
                rankings[game.loser] = begin_elo_at

            #build actual rankings
            for game in games:
                new_rankings = rate_1vs1(rankings[game.winner],rankings[game.loser])
                rankings[game.winner] = new_rankings[0]
                rankings[game.loser] = new_rankings[1]

            for player in rankings:
                rankings[player] = int(round(rankings[player],0))

            return rankings

        def _get_elo_graph(start_date):
            #setup plotly
            import random
            import plotly.plotly as py
            import plotly.graph_objs as go
            py.sign_in('geofahm', 'B1WfY9zkbIPB819acKzg')

            #get games from ORM
            games = Game.objects.filter(created_on__gt=start_date).order_by('created_on')

            #instantiate rankings object
            rankings = {}
            tracing = {}
            for game in games:
                tracing[game.winner] = begin_elo_at
                tracing[game.loser] = begin_elo_at
                rankings[game.winner] = begin_elo_at
                rankings[game.loser] = begin_elo_at

            x_axis = [game.created_on for game in games] + [ timezone.now() + timezone.timedelta(hours=24) ]

            #setup history object
            rankings_history = rankings.copy()
            for player in rankings_history.keys():
                rankings_history[player] = []

            #build traces
            for game in games:
                new_rankings = rate_1vs1(rankings[game.winner],rankings[game.loser])
                rankings[game.winner] = new_rankings[0]
                rankings[game.loser] = new_rankings[1]
                for player in tracing.keys():
                    rankings_history[player] =  rankings_history[player] + [rankings[player]]

            #add todays ranking
            for player in tracing.keys():
                rankings_history[player] =  rankings_history[player] + [rankings_history[player][-1]]

            traces = []
            # Create traces
            for player in tracing.keys():
                traces = traces + [ go.Scatter(
                    x = x_axis,
                    y = rankings_history[player],
                    mode = 'lines',
                    name = player
                ) ]

            # Plot!
            url = ""
            try:
                url = py.plot(traces, filename='python-datetime',auto_open=False,xTitle='Dates',yTitle='ELO Rankings',title='Leaderboard history') + ".png?" + str(random.random())
            except Exception:
                pass

            return url

        def _get_user_username(message,opponentname):
            if opponentname.find('>') > 0:
                logging.debug("DEBUG found > in name, using opp_userid")
                opp_userid = opponentname.replace('@','').replace('<','').replace('>','').strip()
                display_name = str(message.channel._client.users[opp_userid]['profile']['display_name'])
                if not display_name:
                    opponentname = '@' + str(message.channel._client.users[opp_userid]['profile']['real_name'])
                else:
                    opponentname = '@' + str(message.channel._client.users[opp_userid]['profile']['display_name'])
                logging.debug("DEBUG opponent: {}".format(opponentname))
            else:
                logging.debug("found no > in name, not using opp_user_id")
                opponentname = opponentname if opponentname.find('@') != -1 else '@' + opponentname
                logging.debug("DEBUG opponent: {}".format(opponentname))
            return opponentname.lower()

        def get_gif(type):
            if type == 'challenge':
                gifs = ['http://media0.giphy.com/media/DaNgLGo1xefu0/200.gif','http://media2.giphy.com/media/HbkT5F5CiRD3O/200.gif','http://media4.giphy.com/media/10mRi3yn0TVjGw/200.gif','http://media0.giphy.com/media/lcezaVyxCMMqQ/200.gif','http://media2.giphy.com/media/zp0nsdaiKMP4s/200.gif','http://media1.giphy.com/media/QDMBetxJ8YDvy/200.gif','http://media1.giphy.com/media/ozhDtzrmemc0w/200.gif','http://media1.giphy.com/media/rhV4HrtcNkgW4/200.gif','http://media0.giphy.com/media/dW073LLVqyUH6/200.gif','http://media2.giphy.com/media/peM7G1oWYgahW/200.gif','http://media2.giphy.com/media/E8GWazqt84V1u/200.gif','http://media2.giphy.com/media/qX3CivVQbEwo/200.gif','http://media1.giphy.com/media/Xmhz0vejtVhp6/200.gif','http://media4.giphy.com/media/CTeW3X1txg556/200.gif','http://media3.giphy.com/media/T6wZ2b32ZRORW/200.gif','http://media3.giphy.com/media/R7IYpzLLMBomk/200.gif','http://media3.giphy.com/media/DeoY3iC6VLBHG/200.gif','https://media1.giphy.com/media/l0NwKRRtGFjT9k6Q0/200.gif','https://media4.giphy.com/media/q7dp7xY7sHGCs/200.gif','https://media4.giphy.com/media/T6cP9jEs04fbW/200.gif','https://media3.giphy.com/media/xTcnT1NyU61Fpk75WU/200.gif','https://media0.giphy.com/media/Z6gwIJr7CPoqI/200.gif','https://media3.giphy.com/media/Z0Umc2aJY64XS/200.gif','https://media2.giphy.com/media/Ndy3hL4v1miMo/200.gif','https://media1.giphy.com/media/14dspyNocVyBwI/200.gif','https://media2.giphy.com/media/26tPoKcKX13IejXt6/200.gif','https://media4.giphy.com/media/lD08EuqQjc1K8/200.gif','https://media0.giphy.com/media/xTiTnCdwS6XsosHHyM/200.gif','https://media4.giphy.com/media/vdLRwjtIZ7g3K/200.gif','https://media0.giphy.com/media/VNGBU36a1vhwA/200.gif','https://media0.giphy.com/media/xTiTnin6Dlh2VGMbo4/200.gif','https://media2.giphy.com/media/phuTWDjfoXYcw/200.gif','https://media1.giphy.com/media/12TZCBBU3tFPY4/200.gif','https://media4.giphy.com/media/l7IwVljx8wgSc/200.gif','https://media0.giphy.com/media/3o85xJm1Rh6pISHhks/200.gif','https://media1.giphy.com/media/3oEdv73lmCG5GGiWxa/200.gif','https://media2.giphy.com/media/3oEdv3V0pwSlsKkKGs/200.gif','https://media3.giphy.com/media/gw3zMXiPDkOyVBsc/200.gif','https://media2.giphy.com/media/3o85xHHfQ1NiRfocCc/200.gif','https://media4.giphy.com/media/3o85xLA0jpUO3LlIc0/200.gif','https://media1.giphy.com/media/Ux15Wjv9kDRFm/200.gif','https://media1.giphy.com/media/1391lvKWNyuc9i/200.gif']
            elif type == 'taunt':
                gifs = ['https://media1.giphy.com/media/l0GRkpk8mcWhekrVC/200.gif' ,'https://media4.giphy.com/media/l41lKvLqu2xcYX8ly/200.gif' ,'https://media1.giphy.com/media/3o85xvq7HFBjnX3VBK/200.gif' ,'https://media2.giphy.com/media/tG4q5t4gdepjy/200.gif' ,'https://media4.giphy.com/media/YE5RrQAC1g7xm/200.gif' ,'https://media0.giphy.com/media/BFw86Be9MSWNa/200.gif' ,'https://media3.giphy.com/media/wp8DE7gpQKre0/200.gif' ,'https://media4.giphy.com/media/14wAFFW4x09qgw/200.gif' ,'https://media3.giphy.com/media/7Q8wiXGmhbXO0/200.gif' ,'https://media2.giphy.com/media/tvC9faYbQrHlS/200.gif' ,'https://media4.giphy.com/media/fCOYq0wyKeWZy/200.gif' ,'https://media0.giphy.com/media/136ttE0X1uWmsM/200.gif' ,'https://media0.giphy.com/media/86VV3ZYT1owDu/200.gif' ,'https://media0.giphy.com/media/rg22G4omR08lW/200.gif' ,'https://media0.giphy.com/media/u1hqtTKoTWVHi/200.gif' ,'https://media3.giphy.com/media/ETKSOS0KOgljO/200.gif' ,'https://media1.giphy.com/media/N4iJYIkzuIn6g/200.gif' ,'https://media4.giphy.com/media/pK1xYb8ftQZdm/200.gif' ,'https://media2.giphy.com/media/qGgu8qGWbPMkg/200.gif' ,'https://media3.giphy.com/media/FenUXhxrhGLle/200.gif' ,'https://media1.giphy.com/media/LByI6Ze8GWZKo/200.gif' ,'https://media1.giphy.com/media/uLHj9dmluha8M/200.gif' ,'https://media0.giphy.com/media/SpdOR2xwYzvYk/200.gif' ,'https://media3.giphy.com/media/kOlwMOrqkBQ6A/200.gif' ,'https://media3.giphy.com/media/WgvO9zb96dVx6/200.gif','https://media1.giphy.com/media/cnczob1SfXevK/200.gif','https://media1.giphy.com/media/HgRlGFapLl92U/200.gif','https://media3.giphy.com/media/ZOW5uliTiHwLS/200.gif','https://media0.giphy.com/media/jXAfNZqbmaEb6/200.gif','https://media2.giphy.com/media/LOpsoo3yRDHbi/200.gif','https://media1.giphy.com/media/11UV14XPbGFyCc/200.gif','https://media4.giphy.com/media/KqFsOCQZweNhK/200.gif','https://media4.giphy.com/media/qN7NZR3Q5R2mY/200.gif','https://media3.giphy.com/media/qraiyjvXXP2oM/200.gif','https://media4.giphy.com/media/VzbN9gupkkXp6/200.gif','https://media2.giphy.com/media/Qr4JSl1M86qLC/200.gif','https://media3.giphy.com/media/h38BLEj9QOx0I/200.gif','https://media0.giphy.com/media/BJMIzBe8OZyWQ/200.gif','https://media3.giphy.com/media/RSzvGBuoQRlp6/200.gif']
            elif type == 'winorloss':
                gifs = ['https://media1.giphy.com/media/Vs6ASalhnbomk/200.gif','https://media4.giphy.com/media/k4dmtQafDuhDG/200.gif','https://media4.giphy.com/media/6gyuq0k9zIcBG/200.gif','https://media1.giphy.com/media/11IPXDbYmRRNwk/200.gif','https://media1.giphy.com/media/13t2Pa6WECl8je/200.gif','https://media3.giphy.com/media/aHJ6uCT5aMcPS/200.gif','https://media0.giphy.com/media/s2pfpFIc6CDlu/200.gif','https://media1.giphy.com/media/11IPXDbYmRRNwk/200.gif','https://media4.giphy.com/media/M0yDGzfdQQOcg/200.gif','https://media3.giphy.com/media/YJ6TmsrR4rjOg/200.gif','https://media3.giphy.com/media/Mp19UE9GMARKE/200.gif','https://media1.giphy.com/media/fdgOAnZS81CRq/200.gif','https://media3.giphy.com/media/OetNQSs0jO7Kw/200.gif']
            else:
                gifs = ['http://media.tumblr.com/0e07ec60ce9b5f8019e7e98510e3e86e/tumblr_inline_mvq3ol2lHr1qahu1s.gif','http://38.media.tumblr.com/tumblr_ls933rtrAa1r3v6f2o1_500.gif','http://media.tumblr.com/ee3d490720837f2728e8de52094e1413/tumblr_inline_mknw21r56j1qz4rgp.gif','http://25.media.tumblr.com/ec131b67c3a55dcb99fa5e4ef5f3599b/tumblr_mmst60zClN1rhhrvto1_500.gif','http://31.media.tumblr.com/eb9e90aff682182d613737b9072f8e41/tumblr_mgo892vhpu1rk6n1go1_500.gif','http://media.tumblr.com/tumblr_mdicgvDPim1qh8ujs.gif','http://31.media.tumblr.com/f86af9c670404254ae22ab900a4c51f1/tumblr_mypy1toyaL1sgrpsuo1_500.gif','http://33.media.tumblr.com/aebeb686a640493b512c8999881d1fb5/tumblr_njzrzaICmG1s3h43ko1_500.gif','http://24.media.tumblr.com/209fafb786577f6556c8b49c1c8112e4/tumblr_mlqov0OsUf1rch0b8o1_500.gif','https://media2.giphy.com/media/l0NwIoO8LN6Pr3Ety/200.gif','https://media1.giphy.com/media/sNWGEbc5Jzp4c/200.gif','https://media3.giphy.com/media/l41m5FCBtcRpH4Djq/200.gif','https://media4.giphy.com/media/A4HCrFVdbxZpS/200.gif','https://media3.giphy.com/media/14g4EHIdeENmda/200.gif','https://media0.giphy.com/media/SF7kg7hOePkkg/200.gif','https://media3.giphy.com/media/e2wFIvRQ71MaI/200.gif','https://media2.giphy.com/media/iMlzhPDCJ7bQA/200.gif','https://media3.giphy.com/media/DTdI3KKdS8TBK/200.gif','https://media4.giphy.com/media/10h8kjAyPnGRsA/200.gif','https://media2.giphy.com/media/XKcxxxW2e075e/200.gif','https://media0.giphy.com/media/80QhlBqHx1DMs/200.gif','https://media3.giphy.com/media/14unPQFbyCdq2A/200.gif','https://media4.giphy.com/media/jgelsNvS6tYFG/200.gif','https://media1.giphy.com/media/PentDub5eQnu0/200.gif','https://media4.giphy.com/media/rCciDdJY8aTvO/200.gif','https://media2.giphy.com/media/JVC7ZSJEEpYgU/200.gif','https://media4.giphy.com/media/ef0ZKzcEPOBhK/200.gif','https://media0.giphy.com/media/kaDYxHzwxVlBK/200.gif','https://media2.giphy.com/media/MsC2pXWAPUqru/200.gif','https://media3.giphy.com/media/11nI3aybdZ9EA0/200.gif','https://media1.giphy.com/media/iGMQJxHoi9iDK/200.gif','https://media3.giphy.com/media/OYlmWQVEuM6yc/200.gif','https://media4.giphy.com/media/U90QBiNwIuV0c/200.gif']

            import random
            gifurl = random.choice (gifs)
            return gifurl

        @listen_to('^pongbot help', re.IGNORECASE)
        @listen_to('^pb help', re.IGNORECASE)
        def help(message):
            help_message="Hello! I'm pongbot, I'll track your Table-Tennis statistics.  Here's how to use me: \n\n"+\
                " _Play_: \n" +\
                "    `pb challenge <@opponent>` -- challenges @opponent to a friendly game of table-tennis \n" +\
                "    `pb taunt <@opponent> ` -- taunt @opponent \n" +\
                "    `pb accept <@opponent>` -- accepts a challenge \n" +\
                "    `pb result <@opponent> <wins> - <losses>` -- records the results against a single opponent (e.g. `pb result @johndoe 3-2`) \n" +\
                "    `pb predict <@opponent>` -- predict the outcome of a game between you and @opponent \n" +\
                "    `pb who next` -- randomly selects someone for you to play \n" +\
                " _Stats_: \n\n" +\
                "    `pb leaderboard` -- displays this seasons leaderboard for table-tennis\n" +\
                "    `pb <@user> history` -- shows the last 10 games for that user \n" +\
                "    `pb season` -- displays season information for table-tennis\n\n" +\
                "    `pb history` -- displays history for table-tennis\n\n" +\
                " _About_: \n" +\
                "    `pb help` -- displays help menu (this thing)\n" +\
                " You may also call me by my full name: `pongbot <command>`." +\
                " "
                # "    `pb alltime leaderboard table-tennis` -- displays the all time leaderboard for table-tennis\n" +\
                # "    `pb version` -- displays my software version\n\n" +\
                # "    `pb won <@opponent>` -- records a win for you against @opponent \n" +\
                # "    `pb lost <@opponent>` -- records a loss for you against @opponent \n" +\

            message.send(help_message)


        @listen_to('^pongbot version', re.IGNORECASE)
        @listen_to('^pb version', re.IGNORECASE)
        def version(message):
            help_message="Version 1.2 \n\n"+\
                " Version history \n" +\
                " * `1.2` -- deprecated `pb won <@opponent>` and `pb loss <@opponent>` in favor of `pb result...` \n" +\
                " * `1.1` -- added `pb result <@opponent> <wins> <losses>` for recording results quicker \n" +\
                " * `1.0` -- added `who next`, added `pb @user history` -- specific user history \n" +\
                ""
            message.reply(help_message)

        def get_active_season(seasoned):
            range_start_date = default_start

            try:
                active_season = Season.objects.get(active=True)
            except Exception as e:
                active_season = Season.objects.create(start_on = range_start_date,active = True)
                active_season.save()

            if seasoned:
                range_start_date = active_season.start_on
            else:
                active_season = None

            return active_season, range_start_date

        @listen_to('^pongbot alltime leaderboard',re.IGNORECASE)
        @listen_to('^pb alltime leaderboard', re.IGNORECASE)
        def unseasoned_leaderboard(message):
            return _leaderboard(message,False)

        @listen_to('^pongbot leaderboard',re.IGNORECASE)
        @listen_to('^pb leaderboard', re.IGNORECASE)
        def seasoned_leaderboard(message):
            return _leaderboard(message,True)

        def _leaderboard(message,seasoned=False):


            STATS_SIZE_LIMIT = 1000

            active_season , range_start_date = get_active_season(seasoned)

            games = Game.objects.filter(created_on__gt=range_start_date)
            if not games.count():
                message.reply("No stats found for this game type {}.".format( "this season" if active_season is not None else "" ),in_thread=True)

            players = list(set(list(games.values_list('winner',flat=True).distinct()) + list(games.values_list('loser',flat=True).distinct())))
            stats_by_user = {}
            elo_rankings = _get_elo(range_start_date)

            for player in players:
                stats_by_user[player] = { 'name': player, 'elo': elo_rankings[player], 'wins' : 0, 'losses': 0, 'total': 0 }

            for game in games.order_by('-created_on')[:STATS_SIZE_LIMIT]:
                stats_by_user[game.winner]['wins']+=1
                stats_by_user[game.winner]['total']+=1
                stats_by_user[game.loser]['losses']+=1
                stats_by_user[game.loser]['total']+=1

            for player in stats_by_user:
                stats_by_user[player]['win_pct'] =  round(stats_by_user[player]['wins'] * 1.0 / stats_by_user[player]['total'],2)*100

            stats_by_user = sorted(stats_by_user.items(), key=lambda x: -1 * x[1]['elo'])

            season_str = "All time" if active_season is None else active_season
            stats_str = "\n ".join([  " * {}({}): {}/{} ({}%)".format(stats[1]['name'],stats[1]['elo'],stats[1]['wins'],stats[1]['losses'],stats[1]['win_pct'])  for stats in stats_by_user ])
            stats_str = "{} leaderboard: \n\n{}\n{}".format(season_str, stats_str,_get_elo_graph(range_start_date))
            message.reply(stats_str,in_thread=True)

        @listen_to('^pongbot season',re.IGNORECASE)
        @listen_to('^pb season',re.IGNORECASE)
        def season(message):
            #close current season
            active_season, start_on = get_active_season(True)

            #msg back to users
            msg_str = "{} is active. \nUse `pongbot end season` to end this season.".format(active_season)
            message.send(msg_str)

        @listen_to('^pongbot end season',re.IGNORECASE)
        @listen_to('^pb end season',re.IGNORECASE)
        def end_season(message):

            #close current season
            active_season, start_on = get_active_season(True)
            active_season.end_on = datetime.now()
            active_season.active = False
            active_season.save()

            #start new season
            new_season = Season.objects.create(start_on = datetime.now(),active=True)
            num_seasons_before = Season.objects.filter(pk__lt=new_season.pk).count()
            new_season.season_number = num_seasons_before + 1
            new_season.save()

            #msg back to users
            msg_str = "{} ended.\n\n {} opened".format(active_season,new_season)
            message.send(msg_str)

        @listen_to('^pongbot history',re.IGNORECASE)
        @listen_to('^pb history',re.IGNORECASE)
        def history(message):

            HISTORY_SIZE_LIMIT = 10
            history_str = "\n".join(list( [ "* " + str(game) for game in Game.objects.order_by('-created_on')[:HISTORY_SIZE_LIMIT] ]  ))
            if history_str:
                history_str = "History for last {} games: \n\n{}".format(str(HISTORY_SIZE_LIMIT),history_str)
                message.reply(history_str, in_thread=True)
            else:
                message.send('No history found.')

        @listen_to('^pongbot (<@.*) history',re.IGNORECASE)
        @listen_to('^pb (<@.*) history',re.IGNORECASE)
        def individual_history(message,user):
            #input sanitization
            user = _get_user_username(message,user)
            logging.debug(user)
            HISTORY_SIZE_LIMIT = 10
            history_str = "\n".join(list( [ "* " + str(game) for game in Game.objects.filter(Q(winner=user) | Q(loser=user)).order_by('-created_on')[:HISTORY_SIZE_LIMIT] ]  ))

            games = (Game.objects.filter(Q(winner=user) | Q(loser=user)))
            games = games.order_by('-created_on')

            trend = [ "W" if game.winner == user else "L" for game in games[0:trend_size] ]
            trend.reverse()
            trend = "".join(trend)
            # highlight streaks in trends
            streak_sizes = list(range(3,10))
            streak_sizes.reverse()
            longest_streak = None
            for streak_size in streak_sizes:
                for streak_char in ["W","L"]:
                    streak_string = "".join([ streak_char for i in range(0,streak_size) ] )
                    if streak_string in trend:
                        if longest_streak is None:
                            longest_streak = "{}:{}".format(streak_char,streak_size)
            this_message = "\n\nTrend: " + trend + ( ". Longest streak: {}".format(longest_streak) if longest_streak else "" )

            active_season , range_start_date = get_active_season(seasoned=False)

            elo_rankings = _get_elo(range_start_date)
            player_elo = elo_rankings[user]

            elo_message="\n\n{}'s elo ranking is {}.".format(user,player_elo)

            if history_str:
                history_str = "History for {}'s last {} games: \n\n{}".format(user,str(HISTORY_SIZE_LIMIT),history_str)
                full_message = history_str+this_message+elo_message
                message.reply(full_message, in_thread=True)
            else:
                message.send('No history found')

            # message.reply(this_message, in_thread=True)
            #
            # message.reply("{}'s elo ranking is {}.".format(user,player_elo),in_thread=True)

        @listen_to('^pb challenge (.*)',re.IGNORECASE)
        @listen_to('^pongbot challenge (.*)',re.IGNORECASE)
        def challenge(message,opponentname):
            #setup
            sender = "@" + str(message.channel._client.users[message.body['user']]['profile']['display_name'])
            if not sender:
                sender = "@" + str(message.channel._client.users[message.body['user']]['profile']['real_name'])
            else:
                sender = "@" + str(message.channel._client.users[message.body['user']]['profile']['display_name'])
            sender = sender.lower()
            opponentname = _get_user_username(message,opponentname)

            #body
            accept_message = "gb accept {}".format(sender)
            gifurl = get_gif('challenge')

            #send response
            this_message = "{}, {} challenged you to a game!. Accept like this: `{}` \n\n{}".format(opponentname,sender,accept_message,gifurl)
            message.send(this_message)

        @listen_to('^pb taunt (.*)',re.IGNORECASE)
        @listen_to('^pongbot taunt (.*)',re.IGNORECASE)
        def taunt(message,opponentname):

            #setup
            sender = "@" + str(message.channel._client.users[message.body['user']]['profile']['display_name'])
            if not sender:
                sender = "@" + str(message.channel._client.users[message.body['user']]['profile']['real_name'])
            else:
                sender = "@" + str(message.channel._client.users[message.body['user']]['profile']['display_name'])
            sender = sender.lower()
            opponentname = _get_user_username(message,opponentname)
            #body
            gifurl = get_gif('taunt')

            #send response
            this_message = "{}, {} taunted you {}".format(opponentname,sender,gifurl)
            message.send(this_message)

        @listen_to('^pb predict (.*)',re.IGNORECASE)
        @listen_to('^pongbot predict (.*)',re.IGNORECASE)
        def predict(message,opponentname,seasoned=False):
            _predict(message,opponentname,True,False)
            _predict(message,opponentname,False,True)

        def _predict(message,opponentname,seasoned=False,show_trend=False):
            #setup
            sender = "@" + str(message.channel._client.users[message.body['user']]['profile']['display_name'])
            if not sender:
                sender = "@" + str(message.channel._client.users[message.body['user']]['profile']['real_name'])
            else:
                sender = "@" + str(message.channel._client.users[message.body['user']]['profile']['display_name'])
            sender = sender.lower()
            opponentname = _get_user_username(message,opponentname)
            active_season , range_start_date = get_active_season(seasoned)

            #body
            games = (Game.objects.filter(created_on__gt=range_start_date,winner=sender,loser=opponentname)) | (Game.objects.filter(created_on__gt=range_start_date,winner=opponentname,loser=sender))
            games = games.order_by('-created_on')
            if not games:
                message.send("No games found between {} and {}".format(sender,opponentname))
                return;

            stats_by_user = {}

            #todo: this could all be done in django querysets
            stats_for_sender = { 'wins' : 0, 'losses': 0, 'total': 0 }

            for game in games:

                if game.winner == sender:
                    stats_for_sender['wins'] = stats_for_sender['wins'] + 1
                    stats_for_sender['total'] = stats_for_sender['total'] + 1
                else:
                    stats_for_sender['losses'] = stats_for_sender['losses'] + 1
                    stats_for_sender['total'] = stats_for_sender['total'] + 1

            win_pct = round(stats_for_sender['wins'] * 1.0 / stats_for_sender['total'],2)*100
            season_str = "*all time*" if active_season is None else "*"+str(active_season)+"*"

            this_message = "{} total games played between {} and {} {}. \n{} is {}% likely to win next game"\
                            .format(stats_for_sender['total'],sender,opponentname,season_str,sender,win_pct)

            if show_trend:
                trend = [ "W" if game.winner == sender else "L" for game in games[0:trend_size] ]
                trend.reverse()
                trend = "".join(trend)
                # highlight streaks in trends
                streak_sizes = list(range(3,10))
                streak_sizes.reverse()
                longest_streak = None
                for streak_size in streak_sizes:
                    for streak_char in ["W","L"]:
                        streak_string = "".join([ streak_char for i in range(0,streak_size) ] )
                        if streak_string in trend:
                            if longest_streak is None:
                                longest_streak = "{}:{}".format(streak_char,streak_size)
                this_message = this_message + "\nTrend: " + trend + ( ". Longest streak: {}".format(longest_streak) if longest_streak else "" )

            message.send(this_message)


        @listen_to('^pb accept (.*)',re.IGNORECASE)
        @listen_to('^pongbot accept (.*)',re.IGNORECASE)
        def accepted(message,opponentname):
            #setup
            sender = "@" + str(message.channel._client.users[message.body['user']]['profile']['display_name'])
            if not sender:
                sender = "@" + str(message.channel._client.users[message.body['user']]['profile']['real_name'])
            else:
                sender = "@" + str(message.channel._client.users[message.body['user']]['profile']['display_name'])
            sender = sender.lower()
            opponentname = _get_user_username(message,opponentname)

            gifurl = get_gif('accepted')

            #send response
            this_message = "{}, {} accepted your challenge! \n\n{}".format(opponentname,sender,gifurl)
            message.send(this_message)

        @listen_to('pb highfive (.*)',re.IGNORECASE)
        def highfive(message,user):
            message.send('https://media.giphy.com/media/3o7TKTeL57EJdYFKBW/giphy.gif')

##########
        @listen_to('^pb result (<@.*) ([0-9])-([0-9])',re.IGNORECASE)
        @listen_to('^pb results (<@.*) ([0-9])-([0-9])',re.IGNORECASE)
        @listen_to('^pb result (<@.*) ([0-9]) ([0-9])',re.IGNORECASE)
        @listen_to('^pb results (<@.*) ([0-9]) ([0-9])',re.IGNORECASE)
        def results(message, opponentname, wins, losses ):
            def won2(message, opponentname):
                time = current_time()

                #setup
                sender = "@" + str(message.channel._client.users[message.body['user']]['profile']['display_name'])
                if not sender:
                    sender = "@" + str(message.channel._client.users[message.body['user']]['profile']['real_name'])
                else:
                    sender = "@" + str(message.channel._client.users[message.body['user']]['profile']['display_name'])
                sender = sender.lower()
                opponentname = _get_user_username(message,opponentname)
                if sender == opponentname:
                    raise Exception("You can't beat to yourself, please specify correct opponent.")

                active_season , range_start_date = get_active_season(True)

                winner_old_elo = 1000
                loser_old_elo = 1000

                elo_rankings = _get_elo(range_start_date)
                if sender in elo_rankings:
                    winner_old_elo = elo_rankings[sender]
                if opponentname in elo_rankings:
                    loser_old_elo = elo_rankings[opponentname]

                newgame = Game.objects.create(winner=sender,loser=opponentname,created_on=time,modified_on=time)

                elo_rankings = _get_elo(range_start_date)
                winner_elo_diff = elo_rankings[sender] - winner_old_elo
                loser_elo_diff = elo_rankings[opponentname] - loser_old_elo

            ##########
            def loss2(message, opponentname):
                time = current_time()
                #setup
                sender = "@" + str(message.channel._client.users[message.body['user']]['profile']['display_name'])
                if not sender:
                    sender = "@" + str(message.channel._client.users[message.body['user']]['profile']['real_name'])
                else:
                    sender = "@" + str(message.channel._client.users[message.body['user']]['profile']['display_name'])
                sender = sender.lower()
                opponentname = _get_user_username(message,opponentname)
                if sender == opponentname:
                    raise Exception("You can't beat to yourself, please specify correct opponent.")

                active_season , range_start_date = get_active_season(True)

                newgame = Game.objects.create(winner=opponentname,loser=sender,created_on=time,modified_on=time)
                winner_old_elo = 1000
                loser_old_elo = 1000

                elo_rankings = _get_elo(range_start_date)
                if sender in elo_rankings:
                    loser_old_elo = elo_rankings[sender]
                if opponentname in elo_rankings:
                    winner_old_elo = elo_rankings[opponentname]
                elo_rankings = _get_elo(range_start_date)
                winner_elo_diff = elo_rankings[opponentname] - winner_old_elo
                loser_elo_diff = elo_rankings[sender] - loser_old_elo
            ##########

            logging.debug("DEBUG: {} {} {}".format(opponentname,wins,losses))
            wins = int(wins)
            losses = int(losses)
            message.react("white_check_mark")
            if wins == 1 and losses != 1:
                message.reply("Recorded {} win and {} losses against {}".format(wins,losses,opponentname),in_thread=True)
            elif wins != 1 and losses == 1:
                message.reply("Recorded {} wins and {} loss against {}".format(wins,losses,opponentname),in_thread=True)
            elif wins == 1 and losses == 1:
                message.reply("Recorded {} win and {} loss against {}".format(wins,losses,opponentname),in_thread=True)
            else:
                message.reply("Recorded {} wins and {} losses against {}".format(wins,losses,opponentname),in_thread=True)
            for i in range(wins):
                won2(message,opponentname)
            for i in range(losses):
                loss2(message,opponentname)

##########

        # Who should I play next
        @listen_to('^pb who next', re.IGNORECASE)
        def opponent_select(message):
            from random import choice
            #setup_sender
            sender = "@" + str(message.channel._client.users[message.body['user']]['profile']['display_name'])
            if not sender:
                sender = "@" + str(message.channel._client.users[message.body['user']]['profile']['real_name'])
            else:
                sender = "@" + str(message.channel._client.users[message.body['user']]['profile']['display_name'])
            sender = sender.lower()
            #identify users available
            users = message.channel._body['members']
            user_list = []

            for index in range(len(users)):
                user = users[index]
                username = '@' + str(message._client.users[user]['profile']['display_name'])
                if not username:
                    username = "@" + str(message._client.users[user]['profile']['real_name'])
                else:
                    username = "@" + str(message._client.users[user]['profile']['display_name'])
                username = sender.lower()
                user_list.append(username)

            user_list.remove("@")
            user_list.remove(sender)

            opponent = choice(user_list)

            message.send("{}, you should play {} next! \n Do you want to challenge them? Type `pb challenge {}`".format(sender,opponent,opponent))

#########
        @listen_to('^pb challenge$',re.IGNORECASE)
        @listen_to('^pb accept$',re.IGNORECASE)
        @listen_to('^pb win$',re.IGNORECASE)
        @listen_to('^pb won$',re.IGNORECASE)
        @listen_to('^pb lost$',re.IGNORECASE)
        @listen_to('^pb loss$',re.IGNORECASE)
        @listen_to('^pongbot challenge$',re.IGNORECASE)
        @listen_to('^pongbot accept$',re.IGNORECASE)
        @listen_to('^pongbot win$',re.IGNORECASE)
        @listen_to('^pongbot won$',re.IGNORECASE)
        @listen_to('^pongbot lost$',re.IGNORECASE)
        @listen_to('^pongbot loss$',re.IGNORECASE)
        def error_history_2(message):
            message.reply('Please specify an opponent handle.')

        @listen_to('^pb challenge (.*)$',re.IGNORECASE)
        @listen_to('^pb accept (.*)$',re.IGNORECASE)
        @listen_to('^pb win (.*)$',re.IGNORECASE)
        @listen_to('^pb won (.*)$',re.IGNORECASE)
        @listen_to('^pb lost (.*)$',re.IGNORECASE)
        @listen_to('^pb loss (.*)$',re.IGNORECASE)
        @listen_to('^pongbot challenge (.*)$',re.IGNORECASE)
        @listen_to('^pongbot accept (.*)$',re.IGNORECASE)
        @listen_to('^pongbot win (.*)$',re.IGNORECASE)
        @listen_to('^pongbot won (.*)$',re.IGNORECASE)
        @listen_to('^pongbot lost (.*)$',re.IGNORECASE)
        @listen_to('^pongbot loss (.*)$',re.IGNORECASE)
        def error_history_3(message,next_arg):
            #message.reply('Please specify both a gametype and an opponent handle.')
            pass
        @listen_to('^pb result (<@.*)$',re.IGNORECASE)
        def error_results_1(message, arg1):
            raise Exception("No valid results posted, please include <wins> - <losses> after <@opponent>")

        def main():
            kw = {
                'format': '[%(asctime)s] %(message)s',
                'datefmt': '%m/%d/%Y %H:%M:%S',
                'level': logging.DEBUG if settings.DEBUG else logging.DEBUG,
                'stream': sys.stdout,
            }
            logging.basicConfig(**kw)
            logging.getLogger('requests.packages.urllib3.connectionpool').setLevel(logging.DEBUG)

            bot = Bot()
            bot.run()

        main()
