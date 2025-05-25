from models import *

session = get_db_session()
comment = session.query(Comment).filter_by(comment_id='UgyZvkzQvPwQ9y55tFZ4AaABAg').first()
print(f'Комментарий найден: {comment is not None}')
if comment:
    print(f'Video ID: {comment.video_id}')
    print(f'Author: {comment.author}')
    print(f'Text: {comment.text[:50]}...')
session.close() 