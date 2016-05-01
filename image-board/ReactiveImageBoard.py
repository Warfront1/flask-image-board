import os
import uuid

from collections import OrderedDict
from flask import Flask, render_template, request, Response
import pprint
import MySQLdb
import MySQLdb.cursors
from werkzeug.utils import secure_filename

app = Flask(__name__)
static_folder_path = os.path.join(os.path.dirname(os.path.abspath(__file__)),'static', 'images')
ALLOWED_EXTENSIONS = set(['.png', '.jpg', '.jpeg', '.gif', '.webm'])


db = MySQLdb.connect(host="localhost",    # your host, usually localhost
                     user="root",         # your username
                     passwd="",  # your password
                     db="image_board",
                     cursorclass=MySQLdb.cursors.DictCursor)        # name of the data base

def get_latest_threads():
# fetches a list of the most recent(last posted on threads)
    cur = db.cursor()
    cur.execute("""select p.thread_id
                    from posts p
                    where insert_timestamp = (select max(p1.insert_timestamp)
                                                        from posts p1 where p1.thread_id = p.thread_id)
                    order by insert_timestamp desc
                    limit 4""")
    latest_threads = []
    for result in cur.fetchall():
        latest_threads.append(int(result['thread_id']))
    return latest_threads

@app.route('/')
def hello_world():
    return_list = []
    for latest_thread in get_latest_threads():
        cur = db.cursor()
        cur.execute("""select thread_id, comment, insert_timestamp, id, post_image, cast(image_size / 1000 as int) 'image_size'
                        from posts
                        where thread_id = '%s'
                        order by insert_timestamp asc
                        limit 10""",(latest_thread))
        return_list.append(cur.fetchall())
    return render_template('main.html', threads=return_list)

@app.route('/post', methods=['POST'])
def post():
    if request.method == 'POST':
        post_uuid = uuid.uuid4()
        storage_location = None
        print post_uuid
        pprint.pprint(request.form)
        print request.form['comment']

        file = request.files['pic']
        if file:
            safe_filename = secure_filename(file.filename)
            extension = os.path.splitext(safe_filename)[1]
            print safe_filename, extension
            if extension in ALLOWED_EXTENSIONS:
                storage_location = str(post_uuid)+extension
                print storage_location
                if not os.path.exists(static_folder_path):
                    os.makedirs(static_folder_path)
                final_storage_location = os.path.join(static_folder_path, storage_location)
                file.save(final_storage_location)
            else:
                print "File not in valid list of extensions!"
        print final_storage_location
        size = os.path.getsize(final_storage_location)
        print size
        print "file upload success"
        cur = db.cursor()
        print "reply to id: {0}".format(request.form['reply_to_id'])
        if int(request.form['reply_to_id']) == -1:
            # new thread
            cur.execute("""Insert into thread (category_id) values (%s);""",
                (1))
            thread_id =  db.insert_id()
        else:
            #reply
            cur.execute("Select thread_id from posts where id=%s", (request.form['reply_to_id']))
            thread_id =  int(cur.fetchone()['thread_id'])
        cur.execute("""Insert into posts (thread_id, comment, ip_address, post_uuid, post_image, image_size) values (%s, %s, %s, %s, %s, %s);""",
                    (thread_id, request.form['comment'], request.remote_addr, str(post_uuid), storage_location, str(size)))
        db.commit()
    # return Response(status=204)
    return hello_world()

if __name__ == '__main__':
    # app.debug = True
    app.run(host='0.0.0.0')
