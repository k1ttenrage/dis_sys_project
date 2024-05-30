import sys, os
from pika import BlockingConnection, ConnectionParameters

def main():
    connection = BlockingConnection(ConnectionParameters(host='localhost'))
    channel = connection.channel()

    channel.queue_declare(queue='hello')

    method_frame, header_frame, body = channel.basic_get(queue='hello', auto_ack=True)
    
    if method_frame:
        print(f" [x] Received {body}")
    else:
        print("No message returned")

    connection.close()

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print('Interrupted')
        try:
            sys.exit(0)
        except SystemExit:
            os._exit(0)
