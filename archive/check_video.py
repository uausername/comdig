from models import *

session = get_db_session()
video = session.query(Video).filter_by(id=11).first()
if video:
    print(f'Видео найдено:')
    print(f'ID: {video.id}')
    print(f'video_id: {video.video_id}')
    print(f'URL: {video.youtube_url}')
    print(f'Title: {video.title}')
else:
    print('Видео с ID 11 не найдено')

# Также проверим, есть ли видео с video_id = rQYMTcppl98
video2 = session.query(Video).filter_by(video_id='rQYMTcppl98').first()
if video2:
    print(f'\nВидео с video_id rQYMTcppl98 найдено:')
    print(f'ID: {video2.id}')
    print(f'URL: {video2.youtube_url}')
else:
    print('\nВидео с video_id rQYMTcppl98 не найдено')

session.close() 