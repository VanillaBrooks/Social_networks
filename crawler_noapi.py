import selenium
import time
from pprint import pprint
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
import pymysql

browser = webdriver.Firefox()

def utfcon():
    conn = pymysql.connect(host='localhost', user='root', password='pass', db='nodes2', charset='utf8')
    cursor = conn.cursor()
    return conn, cursor

def main():
    conn, cursor = utfcon()
    # initialize login infomation for twitter
    browser.get('https://twitter.com/ohh_marcy/followers')
    x = browser.find_element_by_tag_name("body")

    time.sleep(2)
    x.send_keys('sublimedhippo')
    x.send_keys(Keys.TAB)
    x.send_keys('Whomper12')
    x.send_keys(Keys.RETURN)
    time.sleep(5)

    network_base_user = 'ohh_marcy'
    cursor.execute('select user_follower_id from edges where user_id = %s', network_base_user)
    followers_1 = [i[0] for i in cursor.fetchall()]

    # if no data is recorded for the base case then lets record some base data
    if len(followers_1) == 0:
        print('getting some base data for user %s' %(network_base_user))
        write(get_followers(network_base_user), network_base_user, network_base_user)

    # find the previous people in the database
    cursor.execute('SELECT `user_id` FROM `edges`')
    already_recorded = [i[0] for i in cursor.fetchall()]
    previous = list(set(already_recorded))
    try:
        previous.remove(already_recorded[-1])
    except IndexError:
        pass
    # remove people from the queue that are already in the database
    for user in previous:
        if user in followers_1:
            followers_1.remove(user)
            print('data for %s was already recorded so it is being removed from queue' % (user))

    for user in followers_1:
        print('now working on %s'% (user))

        user_followers = get_followers(user)
        write(user_followers, user, network_base_user)

        print('%s has %s followers' % (user, len(user_followers)))

# writes the collected data to mysql
def write(list_of_followers, user_being_followed, base_user):
    conn, cursor = utfcon()
    if len(list_of_followers) < 12:
        cursor.execute('INSERT INTO `edges` (`user_id`, `user_follower_id`, `original_user`) VALUES (%s, %s, %s)',
                       (user_being_followed, 'No_Followers', base_user))
        conn.commit()
        return True
    for follower in list_of_followers:
        if len(follower) == 0:
            continue
        cursor.execute('INSERT INTO `edges` (`user_id`, `user_follower_id`, `original_user`) VALUES (%s, %s, %s)', (user_being_followed, follower, base_user))
    conn.commit()

    return True

# get all of the followers for a particular user
def get_followers(user):
    url = 'https://twitter.com/' + user + '/followers'
    browser.get(url)
    elem = browser.find_element_by_tag_name("body")

    condition = True
    usernames = []

    while condition == True:
        previous_usernames_length = len(usernames)
        usernames = browser.find_elements_by_class_name('u-linkComplex-target')
        if len(usernames) > 1800 or len(usernames) == previous_usernames_length:
            condition = False
        elif len(usernames) > previous_usernames_length:
            # print('sending more page down')
            for i in range(15):
                elem.send_keys(Keys.PAGE_DOWN)
                elem.send_keys(Keys.PAGE_DOWN)
                time.sleep(2)
        else:
            condition = False
    try:
        usernames = usernames[12:]
        usernames = [user.text for user in usernames]
    except IndexError:
        usernames = []
    print(usernames)
    return usernames

if __name__ == '__main__':
    main()