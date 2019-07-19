from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone
from history.models import Game, Season, Rankings
from datetime import datetime, date
from pytz import timezone as tzone
from collections import Counter
from elo import rate_1vs1, setup
from django.conf import settings
from django.db.models import Q
from time import sleep


default_start = date(2019, 6, 1)
trend_size = 30
setup(k_factor=30)

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

        def _get_user_username(message,opponentname):
            if opponentname.find('>') > 0:
                opp_userid = opponentname.replace('@','').replace('<','').replace('>','').strip()
                display_name = str(message.channel._client.users[opp_userid]['profile']['display_name'])
                if not display_name:
                    opponentname = '@' + str(message.channel._client.users[opp_userid]['profile']['real_name'])
                    logging.debug("DEBUG real_name: {}".format(opponentname))
                else:
                    opponentname = '@' + str(message.channel._client.users[opp_userid]['profile']['display_name'])
                    logging.debug("DEBUG display_name: {}".format(opponentname))
            else:
                opponentname = opponentname if opponentname.find('@') != -1 else '@' + opponentname
                logging.debug("DEBUG: not using opp_user_id, opponent: {}".format(opponentname))

            return opponentname.lower()

        def _get_sender_username(message):
            display_name = str(message.channel._client.users[message.body['user']]['profile']['display_name'])
            if not display_name:
                sender = "@" + str(message.channel._client.users[message.body['user']]['profile']['real_name'])
                logging.debug("DEBUG real_name: {}".format(sender))
            else:
                sender = "@" + str(message.channel._client.users[message.body['user']]['profile']['display_name'])
                logging.debug("DEBUG display_name: {}".format(sender))

            return sender.lower()

        def get_gif(type):
            if type == 'challenge':
                gifs = ['http://media0.giphy.com/media/DaNgLGo1xefu0/200.gif','http://media2.giphy.com/media/HbkT5F5CiRD3O/200.gif','http://media4.giphy.com/media/10mRi3yn0TVjGw/200.gif','http://media0.giphy.com/media/lcezaVyxCMMqQ/200.gif','http://media2.giphy.com/media/zp0nsdaiKMP4s/200.gif','http://media1.giphy.com/media/QDMBetxJ8YDvy/200.gif','http://media1.giphy.com/media/ozhDtzrmemc0w/200.gif','http://media1.giphy.com/media/rhV4HrtcNkgW4/200.gif','http://media0.giphy.com/media/dW073LLVqyUH6/200.gif','http://media2.giphy.com/media/peM7G1oWYgahW/200.gif','http://media2.giphy.com/media/E8GWazqt84V1u/200.gif','http://media2.giphy.com/media/qX3CivVQbEwo/200.gif','http://media1.giphy.com/media/Xmhz0vejtVhp6/200.gif','http://media4.giphy.com/media/CTeW3X1txg556/200.gif','http://media3.giphy.com/media/T6wZ2b32ZRORW/200.gif','http://media3.giphy.com/media/R7IYpzLLMBomk/200.gif','http://media3.giphy.com/media/DeoY3iC6VLBHG/200.gif','https://media1.giphy.com/media/l0NwKRRtGFjT9k6Q0/200.gif','https://media4.giphy.com/media/q7dp7xY7sHGCs/200.gif','https://media4.giphy.com/media/T6cP9jEs04fbW/200.gif','https://media3.giphy.com/media/xTcnT1NyU61Fpk75WU/200.gif','https://media0.giphy.com/media/Z6gwIJr7CPoqI/200.gif','https://media3.giphy.com/media/Z0Umc2aJY64XS/200.gif','https://media2.giphy.com/media/Ndy3hL4v1miMo/200.gif','https://media1.giphy.com/media/14dspyNocVyBwI/200.gif','https://media2.giphy.com/media/26tPoKcKX13IejXt6/200.gif','https://media4.giphy.com/media/lD08EuqQjc1K8/200.gif','https://media0.giphy.com/media/xTiTnCdwS6XsosHHyM/200.gif','https://media4.giphy.com/media/vdLRwjtIZ7g3K/200.gif','https://media0.giphy.com/media/VNGBU36a1vhwA/200.gif','https://media0.giphy.com/media/xTiTnin6Dlh2VGMbo4/200.gif','https://media2.giphy.com/media/phuTWDjfoXYcw/200.gif','https://media1.giphy.com/media/12TZCBBU3tFPY4/200.gif','https://media4.giphy.com/media/l7IwVljx8wgSc/200.gif','https://media0.giphy.com/media/3o85xJm1Rh6pISHhks/200.gif','https://media1.giphy.com/media/3oEdv73lmCG5GGiWxa/200.gif','https://media2.giphy.com/media/3oEdv3V0pwSlsKkKGs/200.gif','https://media3.giphy.com/media/gw3zMXiPDkOyVBsc/200.gif','https://media2.giphy.com/media/3o85xHHfQ1NiRfocCc/200.gif','https://media4.giphy.com/media/3o85xLA0jpUO3LlIc0/200.gif','https://media1.giphy.com/media/Ux15Wjv9kDRFm/200.gif','https://media1.giphy.com/media/1391lvKWNyuc9i/200.gif']
            else:
                gifs = ['https://media1.giphy.com/media/l0GRkpk8mcWhekrVC/200.gif' ,'https://media4.giphy.com/media/l41lKvLqu2xcYX8ly/200.gif' ,'https://media1.giphy.com/media/3o85xvq7HFBjnX3VBK/200.gif' ,'https://media2.giphy.com/media/tG4q5t4gdepjy/200.gif' ,'https://media4.giphy.com/media/YE5RrQAC1g7xm/200.gif' ,'https://media0.giphy.com/media/BFw86Be9MSWNa/200.gif' ,'https://media3.giphy.com/media/wp8DE7gpQKre0/200.gif' ,'https://media4.giphy.com/media/14wAFFW4x09qgw/200.gif' ,'https://media3.giphy.com/media/7Q8wiXGmhbXO0/200.gif' ,'https://media2.giphy.com/media/tvC9faYbQrHlS/200.gif' ,'https://media4.giphy.com/media/fCOYq0wyKeWZy/200.gif' ,'https://media0.giphy.com/media/136ttE0X1uWmsM/200.gif' ,'https://media0.giphy.com/media/86VV3ZYT1owDu/200.gif' ,'https://media0.giphy.com/media/rg22G4omR08lW/200.gif' ,'https://media0.giphy.com/media/u1hqtTKoTWVHi/200.gif' ,'https://media3.giphy.com/media/ETKSOS0KOgljO/200.gif' ,'https://media1.giphy.com/media/N4iJYIkzuIn6g/200.gif' ,'https://media4.giphy.com/media/pK1xYb8ftQZdm/200.gif' ,'https://media2.giphy.com/media/qGgu8qGWbPMkg/200.gif' ,'https://media3.giphy.com/media/FenUXhxrhGLle/200.gif' ,'https://media1.giphy.com/media/LByI6Ze8GWZKo/200.gif' ,'https://media1.giphy.com/media/uLHj9dmluha8M/200.gif' ,'https://media0.giphy.com/media/SpdOR2xwYzvYk/200.gif' ,'https://media3.giphy.com/media/kOlwMOrqkBQ6A/200.gif' ,'https://media3.giphy.com/media/WgvO9zb96dVx6/200.gif','https://media1.giphy.com/media/cnczob1SfXevK/200.gif','https://media1.giphy.com/media/HgRlGFapLl92U/200.gif','https://media3.giphy.com/media/ZOW5uliTiHwLS/200.gif','https://media0.giphy.com/media/jXAfNZqbmaEb6/200.gif','https://media2.giphy.com/media/LOpsoo3yRDHbi/200.gif','https://media1.giphy.com/media/11UV14XPbGFyCc/200.gif','https://media4.giphy.com/media/KqFsOCQZweNhK/200.gif','https://media4.giphy.com/media/qN7NZR3Q5R2mY/200.gif','https://media3.giphy.com/media/qraiyjvXXP2oM/200.gif','https://media4.giphy.com/media/VzbN9gupkkXp6/200.gif','https://media2.giphy.com/media/Qr4JSl1M86qLC/200.gif','https://media3.giphy.com/media/h38BLEj9QOx0I/200.gif','https://media0.giphy.com/media/BJMIzBe8OZyWQ/200.gif','https://media3.giphy.com/media/RSzvGBuoQRlp6/200.gif']

            import random
            gifurl = random.choice (gifs)
            return gifurl

        @listen_to('^gamebot help', re.IGNORECASE)
        @listen_to('^gb help', re.IGNORECASE)
        def help(message):
            help_message="Hello! I'm Gamebot, I'll track your Ping-pong statistics.  Here's how to use me: \n\n"+\
                " _Play_: \n" +\
                "    `gb challenge <@opponent>` -- challenges @opponent to a friendly game of Ping-pong \n" +\
                "    `gb taunt <@opponent> ` -- taunt @opponent \n" +\
                "    `gb accept <@opponent>` -- accepts a challenge \n" +\
                "    `gb result <@opponent> <wins> - <losses>` -- records the results against a single opponent (e.g. `gb result @johndoe 3-2`) \n" +\
                "    `gb predict <@opponent>` -- predict the outcome of a game between you and @opponent \n" +\
                "    `gb who next` -- randomly selects someone for you to play \n\n" +\
                " _Stats_: \n\n" +\
                "    `gb leaderboard` -- displays this seasons leaderboard for table-tennis\n" +\
                "    `gb <@player> history` -- shows up to the last 30 games for that player \n" +\
                "    `gb <@player> elo` -- shows the player's elo ranking \n" +\
                "    `gb global history` -- displays history for table-tennis\n" +\
                "    `gb season` -- displays season information for table-tennis\n\n" +\
                " _About_: \n" +\
                "    `gb help` -- displays help menu (this thing)\n" +\
                " You may also call me by my full name: `gamebot <command>`." +\
                " "
                # "    `gb alltime leaderboard table-tennis` -- displays the all time leaderboard for table-tennis\n" +\
                # "    `gb version` -- displays my software version\n\n" +\

            message.reply(help_message)


        @listen_to('^gamebot version', re.IGNORECASE)
        @listen_to('^gb version', re.IGNORECASE)
        def version(message):
            version_message="Version 1.4.1 \n\n"+\
                " Version history \n" +\
                " * `1.4.1` -- add individual elo ranking message. \n" +\
                " * `1.4` -- gamebot first release for use. \n" +\
                " * `1.3` -- updated the database to track stats instead of calculating them live. \n" +\
                " * `1.2` -- deprecated `gb won <@opponent>` and `gb loss <@opponent>` in favor of `gb result...` \n" +\
                " * `1.1` -- added `gb result <@opponent> <wins> <losses>` for recording results quicker \n" +\
                " * `1.0` -- added `who next`, added `gb @user history` -- specific user history \n" +\
                ""
            message.reply(version_message)

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

        @listen_to('^gamebot alltime leaderboard',re.IGNORECASE)
        @listen_to('^gb alltime leaderboard', re.IGNORECASE)
        def unseasoned_leaderboard(message):
            return _leaderboard(message,False)

        @listen_to('^gamebot leaderboard',re.IGNORECASE)
        @listen_to('^gb leaderboard', re.IGNORECASE)
        def seasoned_leaderboard(message):
            return _leaderboard(message,True)

        def _leaderboard(message,seasoned=False):
            stats_str = rankings_order()
            message.reply(stats_str,in_thread=True)

        @listen_to('^gamebot season',re.IGNORECASE)
        @listen_to('^gb season',re.IGNORECASE)
        def season(message):
            #close current season
            active_season, start_on = get_active_season(True)

            #msg back to users
            msg_str = "{} is active. \nUse `pongbot end season` to end this season.".format(active_season)
            message.send(msg_str)

        @listen_to('^gamebot end season',re.IGNORECASE)
        @listen_to('^gb end season',re.IGNORECASE)
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

        @listen_to('^gamebot global history',re.IGNORECASE)
        @listen_to('^gb global history',re.IGNORECASE)
        def history(message):

            HISTORY_SIZE_LIMIT = 30
            history_str = "\n".join(list( [ "* " + str(game) for game in Game.objects.order_by('-created_on')[:HISTORY_SIZE_LIMIT] ]  ))
            if history_str:
                history_str = "History for last {} games: \n\n{}".format(str(HISTORY_SIZE_LIMIT),history_str)
                message.reply(history_str, in_thread=True)
            else:
                message.send('No history found.')

        @listen_to('^gamebot (<@.*) history',re.IGNORECASE)
        @listen_to('^gb (<@.*) history',re.IGNORECASE)
        def individual_history(message,user):
            #input sanitization
            user = _get_user_username(message,user)
            # logging.debug(user)
            HISTORY_SIZE_LIMIT = 30
            history_str = "\n".join(list( [ "* " + str(game) for game in Game.objects.filter(Q(winner=user) | Q(loser=user)).order_by('-created_on')[:HISTORY_SIZE_LIMIT] ]  ))

            games = Game.objects.filter(Q(winner=user) | Q(loser=user))
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

            player_elo = get_stats(user).ranking

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

        @listen_to('^gb challenge (.*)',re.IGNORECASE)
        @listen_to('^gamebot challenge (.*)',re.IGNORECASE)
        def challenge(message,opponentname):
            #setup
            sender = _get_sender_username(message)
            opponentname = _get_user_username(message,opponentname)

            #body
            accept_message = "gb accept {}".format(sender)
            gifurl = get_gif('challenge')

            #send response
            this_message = "{}, {} challenged you to a game!. Accept like this: `{}` \n\n{}".format(opponentname,sender,accept_message,gifurl)
            message.send(this_message)

        @listen_to('^gb taunt (.*)',re.IGNORECASE)
        @listen_to('^gamebot taunt (.*)',re.IGNORECASE)
        def taunt(message,opponentname):

            #setup
            sender = _get_sender_username(message)
            opponentname = _get_user_username(message,opponentname)

            #body
            gifurl = get_gif('taunt')

            #send response
            this_message = "{}, {} taunted you {}".format(opponentname,sender,gifurl)
            message.send(this_message)

        @listen_to('^gb predict (.*)',re.IGNORECASE)
        @listen_to('^gamebot predict (.*)',re.IGNORECASE)
        def predict(message,opponentname,seasoned=False):
            _predict(message,opponentname,True,False)
            _predict(message,opponentname,False,True)

        def _predict(message,opponentname,seasoned=False,show_trend=False):
            #setup
            sender = _get_sender_username(message)
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


        @listen_to('^gb accept (.*)',re.IGNORECASE)
        @listen_to('^gamebot accept (.*)',re.IGNORECASE)
        def accepted(message,opponentname):
            #setup
            sender = _get_sender_username(message)
            opponentname = _get_user_username(message,opponentname)

            gifurl = get_gif('accepted')

            #send response
            this_message = "{}, {} accepted your challenge! \n\n{}".format(opponentname,sender,gifurl)
            message.send(this_message)


##########
        def get_stats(user):

            user_stats = Rankings.objects.get_or_create(user=user)[0]
            return user_stats
##########
        def update_stats(winner, loser):

            old_winner_elo = winner.ranking
            old_winner_wins = winner.wins
            old_winner_total = winner.total

            old_loser_elo = loser.ranking
            old_loser_losses = loser.losses
            old_loser_total = loser.total

            ranking_results = rate_1vs1(old_winner_elo,old_loser_elo)

            new_winner_elo = int(round(ranking_results[0],0))
            new_loser_elo = int(round(ranking_results[1],0))

            winner_wins = old_winner_wins+1
            winner_total = old_winner_total+1

            loser_losses = old_loser_losses+1
            loser_total = old_loser_total+1

            winner.ranking = new_winner_elo
            winner.wins = winner_wins
            winner.total = winner_total

            loser.ranking = new_loser_elo
            loser.losses = loser_losses
            loser.total = loser_total

            winner.save()
            loser.save()

            winner_diff = new_winner_elo - old_winner_elo
            loser_diff = new_loser_elo - old_loser_elo

            return new_winner_elo, new_loser_elo, winner_diff, loser_diff, winner_wins, winner_total, loser_losses, loser_total
##########
        def rankings_order():
            list_of_users = list(Rankings.objects.values_list('user',flat=True).order_by('-ranking'))
            rankings = {}
            for player in list_of_users:
                user_stats = get_stats(player)
                win_pct = round(user_stats.wins*1.0/user_stats.total,2)*100
                rankings[player] = { 'name': user_stats.user, 'ranking': user_stats.ranking, 'wins' : user_stats.wins, 'losses': user_stats.losses, 'total': user_stats.total ,'win_pct': win_pct}

            rankings = sorted(rankings.items(), key=lambda x: -1 * x[1]['ranking'])
            stats_str = "\n ".join([  " * {}({}): {}/{} ({}%)".format(player[1]['name'],player[1]['ranking'],player[1]['wins'],player[1]['losses'],player[1]['win_pct'])  for player in rankings ])

            return stats_str
##########
        @listen_to('^gamebot (<@.*) elo',re.IGNORECASE)
        @listen_to('^gb (<@.*) elo',re.IGNORECASE)
        def player_elo(message,user):
            player = _get_user_username(message,user)

            elo = get_stats(player).ranking
            message.reply("{}'s elo ranking is {}".format(player,elo),in_thread=True)

##########
        @listen_to('^gb update rankings')
        def create_rankings(message):
            time = current_time()
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
            STATS_SIZE_LIMIT = 1000
            games = Game.objects.filter(created_on__gt=default_start)

            players = list(set(list(games.values_list('winner',flat=True).distinct()) + list(games.values_list('loser',flat=True).distinct())))
            stats_by_user = {}
            elo_rankings = _get_elo(default_start)

            for player in players:
                stats_by_user[player] = { 'name': player, 'elo': elo_rankings[player], 'wins' : 0, 'losses': 0, 'total': 0 }

            for game in games.order_by('-created_on')[:STATS_SIZE_LIMIT]:
                stats_by_user[game.winner]['wins']+=1
                stats_by_user[game.winner]['total']+=1
                stats_by_user[game.loser]['losses']+=1
                stats_by_user[game.loser]['total']+=1

            for player in stats_by_user:
                stats_by_user[player]['win_pct'] =  round(stats_by_user[player]['wins'] * 1.0 / stats_by_user[player]['total'],2)*100

            #delete all entries before recreating them
            Rankings.objects.all().delete()

            for player in stats_by_user:
                stats = Rankings.objects.create(user=stats_by_user[player]['name'],ranking=stats_by_user[player]['elo'],wins=stats_by_user[player]['wins'],losses=stats_by_user[player]['losses'],total=stats_by_user[player]['total'])

            from pprint import pprint
            pprint(stats_by_user)

##########
        @listen_to('^gb result (<@.*) ([0-9]+)-([0-9]+)',re.IGNORECASE)
        @listen_to('^gb results (<@.*) ([0-9]+)-([0-9]+)',re.IGNORECASE)
        @listen_to('^gb result (<@.*) ([0-9]+) ([0-9]+)',re.IGNORECASE)
        @listen_to('^gb results (<@.*) ([0-9]+) ([0-9]+)',re.IGNORECASE)
        def results(message, opponentname, wins, losses ):
            def won2(message, opponentname):
                time = current_time()

                #setup
                sender = _get_sender_username(message)
                opponentname = _get_user_username(message,opponentname)
                if sender == opponentname:
                    raise Exception("You can't beat to yourself, please specify correct opponent.")

                active_season , range_start_date = get_active_season(True)

                newgame = Game.objects.create(winner=sender,loser=opponentname,created_on=time,modified_on=time)
                winner = get_stats(sender)
                loser = get_stats(opponentname)
                new_winner_elo, new_loser_elo, winner_diff, loser_diff, winner_wins, winner_total, loser_losses, loser_total = update_stats(winner, loser)
                logging.debug("DEBUG: winner: {}, loser: {}, winner_elo_diff: +{},({}), loser_elo_diff: {},({}), winner_wins: {}, loser_losses: {}".format(sender,opponentname,winner_diff,new_winner_elo,loser_diff,new_loser_elo,winner_wins,loser_losses))
                rankings_order()

            ##########
            def loss2(message, opponentname):
                time = current_time()
                #setup
                sender = _get_sender_username(message)
                opponentname = _get_user_username(message,opponentname)
                if sender == opponentname:
                    raise Exception("You can't beat to yourself, please specify correct opponent.")

                active_season , range_start_date = get_active_season(True)

                newgame = Game.objects.create(winner=opponentname,loser=sender,created_on=time,modified_on=time)
                winner = get_stats(opponentname)
                loser = get_stats(sender)
                new_winner_elo, new_loser_elo, winner_diff, loser_diff, winner_wins, winner_total, loser_losses, loser_total = update_stats(winner, loser)
                logging.debug("DEBUG: winner: {}, loser: {}, winner_elo_diff: +{},({}), loser_elo_diff: {},({}), winner_wins: {}, loser_losses: {}".format(opponentname,sender,winner_diff,new_winner_elo,loser_diff,new_loser_elo,winner_wins,loser_losses))
                rankings_order()

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
        @listen_to('^gb who next', re.IGNORECASE)
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
        @listen_to('^gb challenge$',re.IGNORECASE)
        @listen_to('^gb accept$',re.IGNORECASE)
        @listen_to('^gamebot challenge$',re.IGNORECASE)
        @listen_to('^gamebot accept$',re.IGNORECASE)
        def error_history_2(message):
            message.reply('Please specify an opponent handle.')

        @listen_to('^gb challenge (.*)$',re.IGNORECASE)
        @listen_to('^gb accept (.*)$',re.IGNORECASE)
        @listen_to('^gamebot challenge (.*)$',re.IGNORECASE)
        @listen_to('^gamebot accept (.*)$',re.IGNORECASE)
        def error_history_3(message,next_arg):
            #message.reply('Please specify both a gametype and an opponent handle.')
            pass

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
