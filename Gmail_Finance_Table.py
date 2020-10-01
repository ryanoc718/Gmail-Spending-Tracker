from httplib2 import Http
from googleapiclient.discovery import build
from oauth2client import file, client, tools
import base64
from bs4 import BeautifulSoup
import pandas as pd
from datetime import datetime 
from datetime import timedelta


class gmailFinTable():
    def __init__(self):
        self.gmailClient = self.get_gmail_client()
    
    def get_gmail_client(self):
        
        # getting credentials for cleint creation
        scopes = "https://www.googleapis.com/auth/gmail.readonly"
        
        store = file.Storage('client_secret.json')
        creds = store.get()
        if not creds or creds.invalid:
            flow = client.flow_from_clientsecrets('credentials.json', scopes)
            creds = tools.run_flow(flow, store)
        service = build('gmail', 'v1', http=creds.authorize(Http()))
        
        # Call the Gmail API to fetch INBOX
        results = service.users().messages().list(userId='me',labelIds = ['INBOX']).execute()
        messages = results.get('messages', [])

        if messages:
            #print("Transactions are:")
            cnt = 0
            yesterday = datetime.today() - timedelta(days=1)
            yesterday = (yesterday - datetime(1970,1,1)).total_seconds() * 1000
            #print(yesterday)
            for message in messages:
                cnt += 1
                msg = service.users().messages().get(userId='me', id=message['id']).execute()
                curr = int(msg['internalDate'])
                #print(curr)
                if curr < yesterday:
                    #print('broke at', cnt)
                    break
                payloadInfo = msg['payload']
                headr = payloadInfo['headers']
                # get sender
                for sendr in headr:
                    if sendr['name'] == 'Subject':
                        santander = 'Alert: Debit transaction'
                        if sendr['value'].find(santander) != -1: #or sendr['value'].find('paid you $') != -1:
                            #print(sendr['value'])
                            for d in headr:
                                if d['name'] == 'Date':
                                    #print(d['value'])
                                    mssg_parts = payloadInfo['parts']
                                    part_one = mssg_parts[0]
                                    part_body = part_one['body']  
                                    part_data = part_body['data']
                                    clean_one = part_data.replace("-","+")
                                    clean_one = clean_one.replace("_","/")
                                    clean_two = base64.b64decode (bytes(clean_one, 'UTF-8')) 
                                    # cleaned html to be able to parse
                                    soup = BeautifulSoup(clean_two , "html.parser" )
                                    blacklist = ['style', 'script']
                                    texts = [t for t in soup.find_all(text=True) if t.parent.name not in blacklist]
                                    # search list of strings for one with value
                                    for i in range(len(texts)):
                                        if texts[i][0] == '$':
                                            self.toFile(texts[i+2], texts[i][1:])
                                    #print("---------------------")
    def toFile(self, date, val):
        #print("$%s: was bought on: %s" % (val, date))
        # create dataframe with vals
        df2 = pd.DataFrame({'Date': date, 'Amount': float(val)}, index= [0])
        # open file and add new dataframe to the columns
        with open('gmail_fin_log.csv', 'a') as f:
             (df2).to_csv(f, index=False, header=False)
        #self.totalSpending()
            # only run totalspending() when testing in cmd
    
    def totalSpending(self):
        df = pd.read_csv('gmail_fin_log.csv')
        print(df['Amount'].sum())

if __name__ == '__main__':
    email = gmailFinTable()
