import tweepy, pymysql, time, os
from pprint import pprint
def authenticate():
    cons_key = 'tAltgJSN7bY60HelfaAZuRQTv'
    cons_sec = '9TlXEwO4XTunxCAjXHrQbpE0xasoTonRjIghEpQS6EVqMvJUmR'
    access_token = '143535005-G0YOesJnUFmeMosrlnokA35F0yS4yPn9FgDg13I6'
    access_secret = 'GXCTXBPwxF7ixu8eaRyABoH2uxQNVBrQNsEEXJgXAxp4X'

    auth = tweepy.OAuthHandler(cons_key, cons_sec)
    auth.set_access_token(access_token, access_secret)
    api = tweepy.API(auth)
    api.wait_on_rate_limit = True

    return api
def utfcon():
    conn = pymysql.connect(host='localhost', user='root', password='pass', db='nodes2', charset='utf8')
    cursor = conn.cursor()
    return conn, cursor

def recursive_cycle(list_of_screen_names, base_user):
    print('in recursive')
    backup = list_of_screen_names[:]

    for user in list_of_screen_names:
        try:
            print('///// new user: %s' % (user))
            find_all_followers(user, 1, base_user)
            backup.remove(user)

        except Exception as e:
            if 'authorized' in str(e):
                conn, cursor = utfcon()
                print('probably not auth error cont', e)
                cursor.execute('INSERT INTO `edges` (`user_id`, `user_follower_id`, `original_user`) VALUES (%s, %s, %s)', (user, 'User_Not_Found', base_user))
                conn.commit()
                conn.close()
                backup.remove(user)
                continue
            # the person changed their name and no longer exists
            # remove them from the database to avoid future errors
            if 'not exist' in str(e):
                conn, cursor = utfcon()
                print('page does not exist removing')
                cursor.execute('delete from edges where `user_follower_id` = %s', user)
                conn.commit()
                conn.close()
                backup.remove(user)
            print('there was an error in recursive_cycle: %s'% (e))
            conn, cursor = utfcon()

            cursor.execute('delete from `edges` where `user_id` = %s', user)
            conn.commit()
            conn.close()

            time.sleep(30)
            recursive_cycle(backup,base_user)
            return False


def find_all_followers(twitter_username, depth, base_user):
    # conn, cursor = utfcon()
    api = authenticate()

    # 15 calls per 15 minutes for api.followers
    followers = []
    changed = False
    for page in tweepy.Cursor(api.followers_ids, user_id=twitter_username).pages():
        shallow_followers = []
        for user in page:
            followers.append(user)
            changed = True
            shallow_followers.append(user)
            try:
                cursor.execute('INSERT INTO `edges` (`user_id`, `user_follower_id`, `original_user`) VALUES (%s, %s, %s)', (twitter_username, user, base_user))
                conn.commit()
            except Exception as e:
               print(e)
        print(shallow_followers)
        if len(followers) > 5000*10:
            return followers
    if changed == False:
        cursor.execute('INSERT INTO `edges` (`user_id`, `user_follower_id`,`original_user`) VALUES (%s, %s, %s)', (twitter_username, 'No_Followers', base_user))
        conn.commit()

    return followers


if __name__ == '__main__':
    conn, cursor = utfcon()

	# 2451959148 julzkang
    base_user_id = '3282581912'
    base_user = 'UNLVGammaPhi'


    cursor.execute('SELECT `user_follower_id` FROM edges where original_user=%s and user_id=%s', (base_user,base_user_id))
    followers = [i[0] for i in cursor.fetchall()]
    pprint(followers)

    if len(followers) == 0:
        followers = find_all_followers(base_user_id,0, base_user)

    followers = list(set(followers))
    cursor.execute('SELECT `user_id` FROM `edges` where `user_id` != %s', base_user)
    already_recorded = [i[0] for i in cursor.fetchall()]

    # if there is already data for user_id
    if len(already_recorded) > 0:
        # drops all entires for the most recent username in the first column
        # this prevents overwriting or incomplete data
        delete = already_recorded[-1]
        print('user checking to delete is: %s' % delete)

        # find all the users that were recorded for the last user id
        cursor.execute('select user_follower_id from edges where user_id = %s',delete)
        x = cursor.fetchall()
        occurances = [i[0] for i in x]

        occurances = len(list(set(occurances)))
        api = authenticate()

        follower_count = min(api.get_user(delete).followers_count, 5000*10)
        print('occurances: %s\nFollower_count: %s' % (occurances, follower_count))
        if occurances*1.1 < min(follower_count, 1200):
            print('!!!!!!!!!!!!!!!!!!!!!!!!!')

            cursor.execute('delete from `edges` where `user_id` = %s', delete)
            conn.commit()
            print('removed data for %s because it was the last entry and had %s entries' % (delete, occurances))
            print('already_recorded before pop: ', already_recorded)
            already_recorded.pop()
        else:
            delete = ''
        previous = list(set(already_recorded))

        try:
            previous.remove(delete)
        except Exception as e:
            pass
        print('value removed was %s and previous is now %s ' % (delete, previous))

        for user in previous:
            if user in followers:
                followers.remove(user)
                print('data for %s was already recorded so it is being removed from queue' % (user))
    print(len(followers))
    recursive_cycle(list_of_screen_names=followers,base_user=base_user)
