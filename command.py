import os
import pika
import uvicorn
from fastapi import FastAPI, UploadFile, BackgroundTasks

app = FastAPI()


def convert_to_webm(input_path, output_path):
    command = f'ffmpeg -i {input_path} -c:v libvpx-vp9 -b:v 1M -c:a libopus {output_path}'
    os.system(command)


def convert_to_mp4(input_path, output_path):
    command = f'ffmpeg -i {input_path} -c:v libx264 -crf 23 -c:a aac -b:a 128k {output_path}'
    os.system(command)


def send_message_to_broker():
    connection = pika.BlockingConnection(pika.ConnectionParameters('localhost', 2233))
    channel = connection.channel()

    channel.queue_declare(queue='task_queue', durable=True)

    channel.basic_publish(
        exchange='',
        routing_key='task_queue',
        body='finished',
        properties=pika.BasicProperties(
            delivery_mode=2  # Make message persistent
        )
    )

    connection.close()


@app.post("/convert")
async def convert_file(background_tasks: BackgroundTasks, file: UploadFile):
    file_path = f"uploads/output/{file.filename}"
    base_filename, file_extension = os.path.splitext(file_path)
    output_path = f"{base_filename}.webm" if file_extension == ".mp4" else f"{base_filename}.mp4"

    with open(file_path, "wb") as f:
        f.write(await file.read())

    if file_extension == ".mp4":
        background_tasks.add_task(convert_to_webm, file_path, output_path)
    elif file_extension == ".webm":
        background_tasks.add_task(convert_to_mp4, file_path, output_path)

    background_tasks.add_task(send_message_to_broker)

    return {"message": "Conversion started. Check back later for the output file."}


if __name__ == "__main__":
    uvicorn.run("ffmpeg_microservice:app", host="0.0.0.0", port=5000)