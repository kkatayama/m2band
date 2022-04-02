from random import randint
import requests
import random

# Wrapper Functions ###########################################################
def g(url, api='http://192.168.1.95:8080'):
    url = f'{api}{url}'
    print(url)
    r = requests.get(url)
    res = r.json() if r.status_code == 200 else r.text
    print(res)
    return(res)

def p(url, api='http://192.168.1.95:8080'):
    url = f'{api}{url}'
    print(url)
    r = requests.post(url)
    res = r.json() if r.status_code == 200 else r.text
    print(res)
    return(res)

###############################################################################
#                          Basic Functions - Tests                            #
###############################################################################
# -- test /index/
def testIndex():
    print(g('/')["message"] == "available commands")
    print(g('')["message"] == "available commands")

###############################################################################
#                           TEST CORE FUNCTION: /add                          #
###############################################################################
def testAddInit():
    g('/add')
    g('/add/')
    g('/add/usage')
    g('/add/usage/')
    g('/add/users')
    g('/add/users/')
    g('/add/oximeter')
    g('/add/oximeter/')

def testAddErrors():
    g('/add/users/username/luke/')
def testAddUsers
    # -- create some users
    luke_id     = g('/add/users/username/luke/password/luke')
    angelina_id = g('/add/users/')
    matt_id     = g('/add/users/')
    mike_id     = g('/add/users/')
    drew_id     = gt'/add/users/')


###############################################################################
#                               Users Table Tests                             #
###############################################################################
usernames = ["luke", "angelina", "matt", "mike", "drew"]




# -- multiple edits -- #
g("/edit/users?username=username||'@udel.edu'&filter=user_id=0")

for i in range(1, 6):
    path = f"/edit/users?username=REPLACE(username,'{i-1}','{i}')&filter=user_id={i}"
    g(path)


g("/edit/oximeter?temperature=round(temperature,2)&filter=user_id>0")

# 20 /add/oximeter
for i in range(20):
    # -- user_id
    user_id = randint(1, 5)
    # -= heart_rate
    heart_rate = randint(99, 166)
    # -- blood_o2
    blood_o2 = randint(95, 100)
    # -- temperature
    temperature = random.uniform(97, 99)

    path = f"/add/oximeter/user_id/{user_id}/heart_rate/{heart_rate}/blood_o2/{blood_o2}/temperature/{temperature}"
    g(path)



inotifywait -q -m -e CLOSE_WRITE --format="git commit -m 'auto commit db' %w && git push origin main" m2band.db | bash
