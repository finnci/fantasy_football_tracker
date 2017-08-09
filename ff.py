import requests
import socket
import time
import datetime

hg_key = 'fofofof'
drop_list = ['code', 'id', 'team_code', 'squad_number',
             'team', 'ep_next', 'element_type', 'bps']


def get_all_data():
    url = 'https://fantasy.premierleague.com/drf/bootstrap-static'
    resp = requests.get(url)
    return resp


def parse_players(players, team_map):
    m_list = []
    for player in players:
        team = team_map[player['team']]
        name = "%s_%s" % (player['first_name'], player['second_name'])
        name = name.replace(' ', '_')
        prefix = "%s.%s" % (team, name)
        for p, v in player.iteritems():
            if p in drop_list:
                continue
            try:
                v = float(v)
            except (ValueError, TypeError):
                continue
            if v == float(0):
                # not going to bother with 0s
                continue
            metric_str = "%s.%s %s" % (prefix, p, v)
            m_list.append(metric_str)
    return m_list


def get_team_mappings(teams):
    team_map = {}
    for team in teams:
        n = team['name'].replace(' ', '_')
        team_map[team['id']] = n
    return team_map


def alive():
    to_send = "%s.ff.script_alive 1\n"
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.sendto(to_send, ("carbon.hostedgraphite.com", 2003))
        return True
    except:
        return False


def send_to_hosted_graphite(p):
    send_count = 0
    metric_prefix = "%s.%s" % (hg_key, 'fantasy_football')
    for metric in p:
        to_send = "%s.%s\n" % (metric_prefix, metric)
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.sendto(to_send, ("carbon.hostedgraphite.com", 2003))
            send_count += 1
        except:
            pass
        time.sleep(1)
    print "Sent %s" % send_count


def main():
    updated = False
    run = True
    last_run = time.time() - 432000
    while True:
        d = datetime.datetime.now()
        if d.isoweekday() is 5 and (time.time() - last_run) > 432000:
            run = True
        if run:
            print "running"
            last_run = time.time()
            res = get_all_data().json()
            teams = get_team_mappings(res['teams'])
            p = parse_players(res['elements'], teams)
            send_to_hosted_graphite(p)
            run = False
        if (time.time() - last_measure) > 3600 and updated:
            updated = alive()


if __name__ == '__main__':
    main() 
