from twilio.rest import Client
from twilio.twiml.messaging_response import Message, MessagingResponse
import datetime, threading, time
from api import authToken, accountSID


client = Client(accountSID, authToken)


# next_call = time.time()

def send_sms(phonenumber, aqi):
    # global next_call
    # print datetime.datetime.now()
    # next_call = next_call+(1*60*60*24)
    # threading.Timer( next_call - time.time(), foo ).start()
    message = client.messages.create(
                                body='Hi there! The AQI for your zip code is {}'.format(aqi),
                                from_='+12162385494',
                                to = phonenumber
                            )
    print(message.sid)
