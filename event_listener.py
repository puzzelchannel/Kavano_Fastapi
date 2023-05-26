import time
import pika

connection = pika.BlockingConnection(pika.ConnectionParameters('localhost', 2233))
channel = connection.channel()

channel.queue_declare(queue='task_queue', durable=True)


def callback(ch, method, properties, body):
    print("Received message:", body.decode())

    time.sleep(5)
    print("Work finished!")

    ch.basic_ack(delivery_tag=method.delivery_tag)


channel.basic_qos(prefetch_count=1)

channel.basic_consume(queue='task_queue', on_message_callback=callback)

channel.start_consuming()
