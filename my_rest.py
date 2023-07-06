import requests
import datetime
import os

# Fill in login details here
url = "https://mattermost.tudelft.nl/api"
token = "" #enter your token here permanantly at your own risk



def execute_get(extension,my_headers,params = None):
    if params == None:
        res = requests.get(url + extension, headers=my_headers)
    else:
        res = requests.get(url + extension, headers=my_headers,params=params)

    if res.status_code != 200:
        print('GET failed')
        print(res.text)
        assert False, 'Something was wrong with the GET command'

    #ret_dict = json.loads(res.text)
    ret_dict = res.json()
    return ret_dict

def execute_get_file(extension,my_headers,params = None):
    if params == None:
        res = requests.get(url + extension, headers=my_headers)
    else:
        res = requests.get(url + extension, headers=my_headers,params=params)

    if res.status_code != 200:
        print('GET failed')
        assert False, 'Something wrong with GET command'
    return res

def execute_post(extenstion,params = None):
    res = requests.post(url+extenstion,headers=my_headers,params = params)

    if res.status_code != 200:
        print('Getting files failed with response code {}'.format(res.status_code))
        print(res.text)
        assert False, 'Something wrong with POST command'
    ret_dict = res.json()
    return ret_dict

if __name__ == '__main__':

    if token == '':
        token = input('Enter your personal access token:')

    # Add the token to the http headers 
    my_headers = requests.utils.default_headers()
    my_headers.update({"Authorization": "Bearer "+token})

    # Get a user with 'me' = checking if we login okay
    myself = execute_get('/v4/users/me',my_headers)
    my_user_id = myself["id"]

    print('Authentication successful as: {}'.format(myself['email']))

    # lets try to get a team from name 
    team_name = ''
    if team_name == '':
        team_name = input('Enter the team name: (example - use "suss" for SSL team) :')
    team_from_name = execute_get("/v4/teams/name/"+team_name,my_headers)
    print('Working with team: ',team_from_name['display_name'])

    # Get users in team
    users_in_SSL = execute_get('/v4/users',my_headers,params={"in_team":team_from_name['id']})

    # Get channels for user
    channels = execute_get('/v4/users/'+my_user_id+'/teams/'+team_from_name['id']+'/channels',my_headers)

    print('These are all the channels for team:{}'.format(team_name))
    for ind,chan in enumerate(channels):
        chan_name = 'unknown'
        if chan['display_name'] == '':
            chan_name = 'Direct message: '
            for user in users_in_SSL:
                if user['id'] in chan['name']:
                    chan_name = chan_name + user['first_name']+' '+user['last_name']+ ' '
        else:
            chan_name = chan['display_name']

        print('{} : {}'.format(ind,chan_name))
    try:
        selected_index = int(input('Enter index of channel you want to save:'))
        selected_channel = channels[selected_index]
    except:
        print('Issue with the choice of index')

    # now we have extracted the channel we want 

    parent_folder = input('Enter a folder name of your choice:')

    try:
        os.mkdir(parent_folder)
        os.mkdir(os.path.join(parent_folder,'chats'))
        os.mkdir(os.path.join(parent_folder,'files'))
    except OSError as error:
        print(error)  
        quit()

    filename = '{}/chats/{}_{}.txt'.format(parent_folder,team_name,selected_channel['id'])
    with open(filename,'w') as f:
        print('Saving to:{}'.format(filename))

    # accumulate file ids
    file_ids_extracted = []

    # Next we will extract posts
    # Get posts for a channel
    get_posts = True
    if get_posts:
        page = 0

        while True:
            posts = execute_get('/v4/channels/'+selected_channel['id']+'/posts',my_headers,params={"page":str(page)})

            orders = posts['order']
            if orders == []:
                break
            page += 1
            posts_extracted = posts['posts']

            with open(filename,'a',encoding='utf-8') as f:
                for order in orders:
                    if 'file_ids' in posts_extracted[order].keys():
                        file_ids = posts_extracted[order]['file_ids']
                        for file_id in file_ids:
                            file_ids_extracted.append(file_id)
                    msg = posts_extracted[order]['message']
                    user_id = posts_extracted[order]['user_id']
                    create_time = posts_extracted[order]['create_at']/1000
                    timestamp = datetime.datetime.fromtimestamp(create_time).strftime("%d/%m/%Y %H:%M:%S")
                    name = 'unknown'
                    for user in users_in_SSL:
                        if user['id'] == user_id:
                            name = user['first_name'] + ' ' + user['last_name']
                    line_to_print = '{} {}: {}\n'.format(timestamp,name,msg)
                    f.write(line_to_print)

    # We will try to get files
    get_files = True

    if get_files:

        for file_id in file_ids_extracted:
            file_get = execute_get_file('/v4/files/'+file_id,my_headers)
            file_metadata = execute_get('/v4/files/'+file_id+'/info',my_headers)

            filename = '{}/files/{}_{}'.format(parent_folder,file_id,file_metadata['name'])
            with open(filename,'wb') as f:
                f.write(file_get.content)
            print(filename)

    print('Thank you for using this wonderful service')


