import os
import uuid

from flask import Flask, render_template, request, Response
import pprint
import MySQLdb
import MySQLdb.cursors
from werkzeug.utils import secure_filename

app = Flask(__name__)
static_folder_path = os.path.join(os.path.dirname(os.path.abspath(__file__)),'static', 'images')
ALLOWED_EXTENSIONS = set(['.png', '.jpg', '.jpeg', '.gif', '.webm'])

@app.route('/')
def hello_world():
    db = MySQLdb.connect(host="localhost",    # your host, usually localhost
                     user="root",         # your username
                     passwd="",  # your password
                     db="image_board",
                     cursorclass=MySQLdb.cursors.DictCursor)        # name of the data base
    cur = db.cursor()
    cur.execute("""select comment, insert_timestamp, id, post_image, cast(image_size / 1000 as int) 'image_size'
                    from posts
                    order by insert_timestamp desc
                    limit 10""")
    return render_template('main.html', posts=cur.fetchall())

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
                final_storage_location = os.path.join(static_folder_path, storage_location)
                file.save(final_storage_location)
            else:
                print "File not in valid list of extensions!"
        print final_storage_location
        size = os.path.getsize(final_storage_location)
        print size
        print "file upload success"
        db = MySQLdb.connect(host="localhost",    # your host, usually localhost
                             user="root",         # your username
                             passwd="",  # your password
                             db="image_board")        # name of the data base
        cur = db.cursor()
        cur.execute("""Insert into posts (comment, ip_address, post_uuid, post_image, image_size) values (%s, %s, %s, %s, %s);""",
                    (request.form['comment'], request.remote_addr, str(post_uuid), storage_location, str(size)))
        db.commit()
    # return Response(status=204)
    return hello_world()

if __name__ == '__main__':
    app.run(host='0.0.0.0')
